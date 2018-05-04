---
# salt state file for suspending Vagrant VMs

suspend_all:
  vagrant.paused:
    - name: 'x_?'
...
