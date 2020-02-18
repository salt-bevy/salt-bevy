#fs.inotify.max_user_watches:
#  sysctl.present:
#    - value: 1048576
  {% set vagrant_prefix = salt['config.get']('vagrant_prefix', 'vagrant_prefix not defined so do not change route') %}
  {% set nets = salt['network.default_route']() %}
  {% for net in nets %}
    {% if net.gateway.startswith(vagrant_prefix) %}
kill_default_route_{{ net.interface }}:
  cmd.run:
      {% if grains['os'] == 'Windows' %}
    - names:
        - route delete 0.0.0.0 mask 0.0.0.0 {{ net.gateway }}
        - route add -p 0.0.0.0 mask 0.0.0.0 {{ net.gateway }} metric 9999  {# so that the other route is preferred #}
      {% else %}
    - name: ip route del default via {{ net.gateway }}
      {% endif %}
    {% endif %}
  {% endfor %}

remove_the_competition:  # these take a lot of virtual memory.
  {% if grains['os'] == 'Windows' %}
  chocolatey.uninstalled:
    - name: chef-client
    - order: last  {# wait for chocolatey to be installed #}
  {% elif grains['os'] == 'MacOS' %}
  test.nop
  {% else %}
  pkg.removed:
    - names:
      - puppet
      - chef
  {% endif %}

{% if grains['os_family'] == 'Debian' %}
autoremove:
  module.run:
    - name: pkg.autoremove
    - order: last

ensure-virt-what:
  pkg.installed:  # gets removed (with puppet) by autoremove
    - name: virt-what
    - require:
      - module: autoremove
{% endif %}
