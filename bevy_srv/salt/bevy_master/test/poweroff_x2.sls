---
# salt state file to power off a Vagrant VM

{{ pillar['stop_node'] }}:
  vagrant.powered_off
...
