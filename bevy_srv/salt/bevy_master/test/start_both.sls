---
# salt state file to start two Vagrant VMs

x_1:
  vagrant.running:
    - cwd: {{ pillar['cwd'] }}
    - vagrant_runas: {{ pillar['runas'] }}
    # will use the default (quail1)

init_x2:
  vagrant.initialized:
    - name: x_2
    - vm:  # this is an embedded dict. Does it work?
        cwd: {{ pillar['cwd'] }}
        machine: quail16
        vagrant_runas: {{ pillar['runas'] }}

x_2:
  vagrant.running:
  - require:
    - init_x2
...

