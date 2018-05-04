---
# salt state file for removing a second minion

{% set run_second = salt['config.get']('run_second_minion', none) %}
{% set other_minion = '2' if run_second|int(-1) < 1 else run_second|string %}

systemctl_stop{{ other_minion }}:
  service.dead:
    - name: salt{{ other_minion }}-minion
    - enable: false
    - init_delay: 4

remove_salt{{ other_minion }}_call_command:
  file.blockreplace:
    - name: /etc/bash.bashrc
    - marker_start: '# v v v v v v  added by Salt  v v v v v v ( -- Do not edit or remove this line -- )'
    - marker_end:   '# ^ ^ ^ ^ ^ ^  added by Salt  ^ ^ ^ ^ ^ ^ ( -- Do not edit or remove this line -- )'
    - content: '# Working code here has been removed.'
...
