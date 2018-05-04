---
# salt state file for killing Vagrant VMs

destroy_all:
  vagrant.destroyed:
    - name: 'x_?'
...
