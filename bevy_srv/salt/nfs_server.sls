---
# salt state file for installing an nfs file server

{% if salt['grains.get']('os_family') == 'Debian' %}
# install nfs on Vagrant host #
install-nfs:
  pkg.installed:
    - name: nfs-kernel-server
nfs-kernel-server:
  service.running:
    - enable: true
  require:
    - pkg: install-nfs
{% else %}
install-nfs:
  test.fail_without_changes:
    - name: "Installation of NFS on non-Debian is not scripted."
{% endif %}

...
