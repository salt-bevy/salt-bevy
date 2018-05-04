---
# salt state file for (re)starting a group of Vagrant VMs

start_all_x:
  vagrant.running:
    - name: 'x_?'
...
