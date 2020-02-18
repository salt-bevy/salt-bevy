---
# salt state file for setting up Salt's Small DataBase

{% set salt_root = salt['file.dirname'](salt['config.get']('conf_file')) %}

{{ salt_root }}/master.d/sdb.conf:
  file.managed:
    - source: salt://files/sdb.conf
    - template: jinja
    - onlyif:
      - test -d {{ salt_root }}/master.d

{{ salt_root }}/minion.d/sdb.conf:
  file.managed:
    - makedirs: True
    - source: salt://files/sdb.conf
    - template: jinja
...
