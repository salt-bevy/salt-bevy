---
# salt state file for suspending Vagrant VMs

reboot_all:
  vagrant.rebooted:
    - name: 'x_?'
...
