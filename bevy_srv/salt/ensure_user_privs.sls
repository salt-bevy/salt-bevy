---
# salt state file to ensure user's priviledges on a virtual machine

{% set my_user = salt['pillar.get']('my_linux_user') %}

include:
  - interactive_user

{% if grains['os'] == "Windows" %}
ssh_public_key:
  file.managed:
    - name: 'C:\Users\{{ my_user }}\.ssh\id_rsa.pub'
    - user: {{ my_user }}
    - source: salt://ssh_keys/{{ my_user }}.pub
    - makedirs: True
    - replace: False
{% else %}  {# not Windows #}
{% set home = '/Users/' if grains['os'] == "MacOS" else '/home/' %}
{{ home }}{{ my_user }}/.ssh:
  file.directory:
    - user: {{ my_user }}
    - group: {{ my_user }}
    - dir_mode: 755
    - makedirs: True
ssh_public_key:
  ssh_auth.present:
    - user: {{ my_user }}
    - source: salt://ssh_keys/{{ my_user }}.pub
    - require:
      - file: {{ home }}{{ my_user }}/.ssh

/etc/sudoers:  # set the interactive linux user for passwordless sudo
  file.append:
    - text: |
        {{ my_user }} ALL=(ALL) NOPASSWD: ALL

/etc/defaults/login:
  file.append:
    - text: "UMASK=002  # create files as group-readable by default ## added by Salt"
    - makedirs: true
{% endif %} {# Windows not #}
...
