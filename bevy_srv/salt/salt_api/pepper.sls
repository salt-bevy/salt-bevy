---
# salt state file for installing the "pepper" command on a workstation

salt-pepper:
  pip.installed

pepper_config_file:
  file.managed:
    - name: /home/{{ salt['config.get']('my_linux_user') }}/.pepperrc
    - contents: |
        {{ pillar['salt_managed_message'] }}
        [main]
        SALTAPI_URL=https://{{ salt['pillar.get']('salt-api:server_address') }}:{{ salt['pillar.get']('salt-api:port','8000') }}
        SALTAPI_USER={{ salt['pillar.get']('salt-api:username') }}
        SALTAPI_PASS={{ salt['pillar.get']('salt-api:password') }}
        SALTAPI_EAUTH={{ salt['pillar.get']('salt-api:eauth') }}
    - user: {{ salt['config.get']('my_linux_user') }}
    - group: staff
...
