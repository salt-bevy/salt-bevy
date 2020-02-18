---
# load a small kurbernetes installation
# see https://microk8s.io/docs/
#
  {% if grains['os_family'] == 'Debian' %}
snapd:
  pkg.installed

install_microk8s:
  cmd.run:
    - name: snap install microk8s --classic --channel=1.17/stable
    - require:
        - snapd

{% set my_user = salt['config.get']('my_linux_user', '') %}
  {% if my_user %}
include:
  interactive_user:

microk8s_group:
  group.present:
    - name: microk8s
    - addusers:
      - {{ my_user }}
    - require:
      - install_microk8s

short_k8s_command:
  file.append:
    - name: /home/{{ my_user }}/.bash_aliases
    - text: alias kubectl='microk8s.kubectl'
    - unless: which kubectl
  {% endif %}

{% else %}

microk8s_oops:
  test.fail_without_changes:
    - name: "Sorry. No script available to install microk8s on your {{ grains['os_family'] }} system."
{% endif %}
