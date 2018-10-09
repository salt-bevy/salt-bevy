---
# /srv/salt/add_bevymaster_to_hosts.sls
# salt state file to add /etc/hosts entry for bevymaster

add_bevymaster_to_hosts:
  host.present:
    - ip: {{ pillar['master_external_ip'] }}
    - names:
      - bevymaster
...
