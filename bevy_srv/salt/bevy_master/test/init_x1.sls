---
# salt state file to initialize, but not start, a VM

init_x1:
  vagrant.initialized:
    - name: x_1
    - cwd: {{ pillar['cwd'] }}
    - vagrant_runas: {{ pillar['my_linux_user'] }}
    - machine: quail1
    - vagrant_provider: virtualbox
...

