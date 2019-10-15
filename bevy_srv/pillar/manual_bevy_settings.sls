---
# salt pillar file for common values for a bevy

{% set master_vagrant_ip = salt['config.get']('master_external_ip', '192.168.88.9') %}  {# main IP address of bevy master #}
{% set master_external_ip = salt['config.get']('master_external_ip', '192.168.88.9') %}  {# main IP address of bevy master #}
{% set pxe_network_cidr = '192.168.88.0/24' %}  {# your private local network for PXE operation #}
pxe_network_cidr: '{{ pxe_network_cidr }}'
bevymaster_external_ip: {{ master_external_ip }}
bevymaster_vagrant_ip: {{ master_vagrant_ip }}  # vagrant host-only IP address of master

{# define module functions which will each minion will run periodically to send data to Salt Mine #}
mine_functions:
  network.ip_addrs: '[]'
  grains.item:
    - fqdn

#change to agree with your actual saltify test hardware machine
wol_test_machine_ip: 192.168.88.8  # the ip address of the minion machine
wol_test_mac: '00-1a-4b-7c-2a-b2'  # mac address of minion machine
wol_test_sender_id: bevymaster  # Salt node id of WoL transmitter

bevy_dir: {{ salt['config.get']('projects_root', '/projects') ~ '/salt-bevy' }}  # path to salt-bevy directory tree
#

# the minion ID's to be put in the master's AUTOSIGN_FILE
#  -- this is an insecure method for automatically accepting minions with known names.
autosign_minion_ids:
  - '# these id names are from pillar file "manual_bevy_settings.sls" entry "autosign_minion_ids".'
  - '# A minion (or wildcard) named in this list will be accepted automatically.  (Insecure!)'
  - 'win1[0269]' {# regular expression matches either win10, win12, win16 or win19 #}
  - 'quail2'

dhcp_pxe_range: {{ pxe_network_cidr.split('/')[0] }}  # network for dnsmasq PXE server replies
{% set pxe_server_ip_list = salt['network.ip_addrs']() %}
{%- if pxe_server_ip_list %}
{%- set pxe_server_ip = pxe_server_ip_list[0] %}
# the pxe boot server needs a Python program to run to keep auto installed machines from looping
# these are the controls for the pxe_clearing_daemon
pxe_clearing_daemon_life_minutes: 60
pxe_clearing_port: 4545  # TCP port to send html control to pxe_clearing_daemon

{% set default_ubuntu_version = 'xenial' %}  {# version name of Ubuntu to install on workstations by default #}

# download source of base operating system to be booted by PXE.
# each version of Ubuntu will have its own installer in a different subdirectory of the PXE boot server
default_ubuntu_version: {{ default_ubuntu_version }} # used for non-scripted PXE installs
pxe_netboot_subdir: '{{ default_ubuntu_version }}'  # name for PXE tftp server subdirectory
pxe_netboot_download_url: http://archive.ubuntu.com/ubuntu/dists/{{ default_ubuntu_version }}/main/installer-amd64/current/images

# This is a list of dicts of machines to be PXE booted.
#  each should have a "tag" matching the Netboot Tags below.
#  Salt state file dnsmasq/pxe_auto_install.sls will create a PXE configuration setting file for each entry in this list.
pxe_netboot_configs:
  - mac: '00-1a-4b-7c-2a-b2'  {# Note the "-", it means this line starts a list #}
    hostname: 'hplt.test'
    subdir: '{{ default_ubuntu_version }}/'  # include a trailing "/"
    tag: install
    kernel: ubuntu-installer/amd64/linux
    append: 'vga=788 initrd=ubuntu-installer/amd64/initrd.gz auto-install/enable=true preseed/url=tftp://{{ pxe_server_ip }}/preseed.files/'
    next_command: 'sleep 60;salt-cloud -p hw_demo x_hw'  {# pxe_clearing_deamon will send this command when install completes #}
# - mac: '01-02-03-04-05-06'
#   tag: something_else
#
# Netboot Tags...
#  This is a list of dnsmasq configuration commands,
#  configures the DHCP server using state file dnsmasq/pxe_auto_install.sls
#  Each entry is a pxe-service line to match one or more of the configs above.
#  The parameters are: tag, client system type, menu text, file to boot.
#  Client system type is one of: x86PC, IA32_EFI, X86-64_EFI, or others
# see http://www.thekelleys.org.uk/dnsmasq/docs/dnsmasq-man.html
pxe_netboot_tags:
  -  pxe-service=tag:install,x86PC,"Network install {{ default_ubuntu_version }}","{{ default_ubuntu_version }}/pxelinux"
  -  pxe-service=tag:!known,x86PC,"Default PXE menu","/pxelinux"
  # - pxe-service=tag:something_else,who,what,where
{% endif -%} {# end of pxe-server configuration #}

salt-api:  {# the api server is located using the "master" grain #}
  port: 4507  # other examples use port 8000
  eauth: pam
  username: vagrant
  password: vagrant

  tls_organization: 'My Company Name'
  tls_location: 'Somewhere, UT'
  tls_emailAddress: 'me@mycompany.test'
...
