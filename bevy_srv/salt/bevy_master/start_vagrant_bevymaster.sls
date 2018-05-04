---
# salt state file to start a bevy master as a VM
# on your workstation.
#
# sudo salt-call --local state.apply bevy_master.start_vagrant_bevymaster
#

start_bevy_master:
  vagrant.running:
    - name: bevymaster
    - machine: bevymaster
    - cwd: {{ pillar['cwd'] }}
    - runas: {{ pillar['runas'] }}

include:
  - add_bevymaster_to_hosts
...
