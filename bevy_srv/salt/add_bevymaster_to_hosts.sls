---
# /srv/salt/add_bevymaster_to_hosts.sls
# salt state file to add /etc/hosts entry for bevymaster

add_bevymaster_to_hosts:
  host.present:
    {% if salt['grains.get']('virtual', 'physical') == 'VirtualBox' %}
    - ip: {{ pillar['bevymaster_url'] }}
    - ip: {{ pillar['bevymaster_url'] }}
    - names:
      - bevymaster
...
