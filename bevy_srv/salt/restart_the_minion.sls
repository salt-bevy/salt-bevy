---
# salt state file to restart the minion
{% set other_minion = salt['config.get']('additional_minion_tag', '') %}

restart-the-minion_setup:
  file.managed:
    - name: /tmp/run_command_later.py
    - source: salt://run_command_later.py
    {% if grains['os'] != 'Windows' %}- mode: 775{% endif %}
    - show_changes: false
restart-the-minion:
  cmd.run:
    - bg: true  # do not wait for completion of this command
    - require:
      - file: restart-the-minion_setup
    - order: last
    - shell: /bin/bash
    {% if grains['os_family'] == 'MacOS' %}
    - name: '/tmp/run_command_later.py 10 "pkill -f salt-minion"'  {# this command seems to work for any installed Salt #}
    {# - name: "/tmp/run_command_later.py 10 launchctl unload /Library/LaunchAgents/{{ salt_minion_service_name }}.plist; launchctl load /Library/LaunchAgents/{{ salt_minion_service_name }}.plist" #}
    {% elif grains['os_family'] == 'Windows' %}
    - name: 'py \tmp\run_command_later.py 10 net stop salt-minion; C:\salt\salt-minion-start-service"'
    {% else %}
    - name: "/tmp/run_command_later.py 10 systemctl restart salt{{ other_minion }}-minion"
    {% endif %}
...
