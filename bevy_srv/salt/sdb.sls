---
# salt state file for setting up Salt's Small DataBase

{{ salt['config.get']('salt_config_directory') }}/master.d/sdb.conf:
  file.managed:
    - source: salt://files/sdb.conf
    - template: jinja
    - onlyif:
      - test -d {{ salt['config.get']('salt_config_directory') }}/master.d

{{ salt['config.get']('salt_config_directory') }}/minion.d/sdb.conf:
  file.managed:
    - makedirs: True
    - source: salt://files/sdb.conf
    - template: jinja
...
