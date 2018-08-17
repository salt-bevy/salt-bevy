---
# salt state file for starting cloud instances in Azurre

azure_prerequisites:
  pkg.installed:
    - names:
      {% if grains['os_family'] == 'Debian' %}
      - build-essential
      - libssl-dev
      - libffi-dev
      - python-dev
      {% else %} {# assume RedHat #}
      - gcc
      - libffi-devel
      - python-devel
      - openssl-devel
      {% endif %}
  pip.installed:
    - 'azure-cli>=2.0.12'


...
