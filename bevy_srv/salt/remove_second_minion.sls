---
# salt state file for removing a second minion

{% set other_minion = salt['config.get']('additional_minion_tag') or '' %}

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
