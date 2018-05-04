---
# salt state file for defining a generic administrator username
{% if salt['grains.get']('virtual', 'physical') != 'physical' or salt['config.get']('create_administrator') %}
{% set users = 'Users' if grains['os'] == "Windows" else 'users' %}

staff_group:
  group:
    - present
    - name: staff
    - require_in:
      - user: vagrant

vagrant:
  {% if grains['os'] != "Windows" %}
  group:
    - present
  {% endif %}
  user:
    - present
    - groups:
      - {{ users }}
    - optional_groups:
      - staff
      - www-data
      - dialout
  {% if grains['os'] == "Windows" %}
      - Administrators
  {% else %}
      - sudo
    - password: $6$cIiKCbvKbLcXR7FL$N08PF11jBzcRpCKNvwboW/ErEMzJ1l899LDEAbn2frCuS7mzCRDrRwgOAD4iIb9nPw9vxfLHeKxOcl2JDVx3L0
    # the default password is "vagrant"
    - enforce_password: false
  {% endif %}
{% endif %}
...
