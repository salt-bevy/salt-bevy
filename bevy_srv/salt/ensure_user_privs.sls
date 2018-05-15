---
# salt state file to ensure user's priviledges on a virtual machine

{% set my_user = salt['pillar.get']('my_linux_user', 'None') %}
{% set my_windows_user = salt['pillar.get']('my_windows_user', 'None') %}

include:
  - interactive_user

{% if grains['os'] == "Windows" %}
  {% if my_windows_user != 'None' %}  {# suppress copy if windows user is not defined #}
ssh_public_key:
  file.managed:
    - name: 'C:/Users/{{ my_windows_user }}/.ssh/id_rsa.pub'
    - user: {{ my_windows_user }}
    - source: salt://ssh_keys/{{ my_user }}.pub
    - onlyif:  # do not attemt to create a directory if user is not yet initialized by Windows
      - {{ salt['file.directory_exists']('C:/Users/{{ my_windows_user }}/.ssh/id_rsa.pub') }}
    - replace: False
  {% endif %}
{% else %}  {# not Windows #}
 {% if my_user != 'None' %}
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
 {% endif %}  {# my_user defined #}
{% endif %} {# Windows not #}
...
