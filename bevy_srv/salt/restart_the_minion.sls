---
# salt state file to restart the minion
{% set other_minion = salt['config.get']('additional_minion_tag') or '' %}

restart-the-minion:
  cmd.run:
    - bg: true  # do not wait for completion of this command
    - order: last
    {% if  grains['os_family'] == 'Windows' %}
    - name: 'C:\salt\salt-call.bat service.restart salt-minion'
    {% elif grains['os_family'] == 'MacOS' %}
    - name: "salt-call service.restart com.saltstack.salt.minion"
    {% else %}
    - name: "salt-call service.restart salt{{ other_minion }}-minion"
    - shell: /bin/bash
    {% endif %}
...
