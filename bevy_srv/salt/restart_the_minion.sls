---
# salt state file to restart the minion
{% set other_minion = salt['config.get']('additional_minion_tag') or '' %}

{% if grains['os'] == 'Windows' %}
  {% set tmpdir = 'C:\\tmp' %}
win_tmp_dir:
  file.directory:
    - name: {{ tmpdir }}
{% else %}
  {% set tmpdir = '/tmp' %}
{% endif %}

{# restart-the-minion_setup:
  file.managed:
    - name: {{ tmpdir }}/run_command_later.py
    - source: salt://run_command_later.py
    {% if grains['os'] != 'Windows' %}- mode: 775{% endif %}
    - show_changes: false
    - makedirs: true #}

restart-the-minion:
  cmd.run:
    - bg: true  # do not wait for completion of this command
    - order: last
    {% if  grains['os_family'] == 'Windows' %}
    - name: 'C:\salt\salt-call.bat service.restart salt-minion'
    {# elif grains['os_family'] == 'MacOS' %}
    - name: '{{ tmpdir }}/run_command_later.py 10 "pkill -f salt-minion"'  # this command seems to work for any installed Salt
    - shell: /bin/bash
    - require:
      - file: restart-the-minion_setup     #}
    {% elif grains['os_family'] == 'MacOS' %}
    - name: "salt-call service.restart com.saltstack.salt.minion"
    {% else %}
    - name: "salt-call service.restart salt{{ other_minion }}-minion"
    - shell: /bin/bash
    {% endif %}
...
