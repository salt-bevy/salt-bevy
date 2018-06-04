---
# salt state file for making a PXE boot server

check_private_network:
{# Your PXE private network should be have been set in pillar/manual_bevy_settings.sls for your situation #}
{#                                     the 192.0.2.0 network is IANA reserved for examples only #}
{% set pxe_network_cidr = salt['pillar.get']('pxe_network_cidr', '192.0.2.0/24')) %}
{% if salt['network.in_subnet'](pxe_network_cidr) %}
  test.nop:
    name: 'You DO have a network interface on the PXE network.'
{% else %}
  test.fail_without_changes:
    - name: 'Salt State selection ERROR: Your machine does not have an interface on the {{ pxe_network_cidr }} network.'
{% endif %}

pxe_packages:
  pkg.installed:
    - names:
      - dnsmasq
      - pxelinux
      - syslinux-common

tftp_dir:
  file.directory:
    - name: /srv/tftpboot
    - user: {{ salt['config.get']('my_linux_user') }}
    - group: staff
    - dir_mode: 775
    - file_mode: 644
    - makedirs: true

supply_memtest_bin:
  file.managed:
    - name: /srv/tftpboot/memtest86+  # NOTE: no ".bin"
    - source:
      - /boot/memtest86+.bin
      - salt://{{ slspath }}/files/memtest86+.bin
    - use: {file: tftp_dir}

/srv/tftpboot/pxelinux.cfg/default:
  file.managed:
    - makedirs: true
    - replace: false
    - source: salt://{{ slspath }}/files/default.cfg
    - template: jinja

/srv/tftpboot/pxelinux.0:
  file.managed:
     - source:
       - /srv/tftpboot/{{ pillar['pxe_netboot_subdir'] }}/pxelinux.0
       - /usr/lib/PXELINUX/pxelinux.0
       - salt://{{ slspath }}/files/pxelinux.0

/srv/tftpboot/ldlinux.c32:
  file.managed:
     - source:
       - /srv/tftpboot/{{ pillar['pxe_netboot_subdir'] }}/ldlinux.c32
       - /usr/lib/syslinux/modules/bios/ldlinux.c32
       - salt://{{ slspath }}/files/ldlinux.c32

/srv/tftpboot/menu.c32:
  file.managed:
     - source:
       - /srv/tftpboot/{{ pillar['pxe_netboot_subdir'] }}/menu.c32
       - /usr/lib/syslinux/modules/bios/menu.c32
       - salt://{{ slspath }}/files/menu.c32

/etc/dnsmasq.d/dnsmasq_pxe.conf:
  file.managed:
    - source: salt://{{ slspath }}/files/dnsmasq_pxe.conf
    - template: jinja
    - makedirs: true

/etc/default/dnsmasq:
  file.append:
    - text: "DNSMASQ_EXCEPT=lo  ## Added by Salt"

dnsmasq_service:
  service.running:
    - name: dnsmasq
    - enable: true
    - watch:
      - file: /etc/default/dnsmasq
      - file: /etc/dnsmasq.d/dnsmasq_pxe.conf
      - pkg: dnsmasq
...
