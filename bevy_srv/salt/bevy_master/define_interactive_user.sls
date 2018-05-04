---
# salt state file for putting the interactive user's info into the master data scripts.

{% set my_linux_user = salt['config.get']('my_linux_user') %}

# salt state file to place creator's public key on bevy master server
# assumes a Linux file layout.
{% if grains['os_family'] == 'Windows' %}
  {% set my_home = salt['environ.get']('USERPROFILE') %}
{% else %}
  {% set my_home = salt['environ.get']('HOME') %}
{% endif %}
establish_my_pub_key:
  file.managed:
    - replace: false
    - name: /srv/salt/ssh_keys/{{ my_linux_user }}.pub
    - source: /home/{{ my_home }}/.ssh/id_rsa.pub
    - makedirs: true
    - order: 3
    - onlyif:
      - test -e /home/{{ my_home }}/.ssh/id_rsa.pub
...
