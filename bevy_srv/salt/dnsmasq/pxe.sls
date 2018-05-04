---
# salt state file for making a PXE boot server

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
