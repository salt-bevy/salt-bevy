#fs.inotify.max_user_watches:
#  sysctl.present:
#    - value: 1048576
  {% set vagrant_prefix = salt['config.get']('vagrant_prefix', 'vagrant_prefix not defined so do not change route') %}
  {% set nets = salt['network.default_route']() %}
  {% set seen = [] %}  {# an interface can show up more than once; its state ID must be unique #}
  {% for net in nets %}
    {% if net.gateway.startswith(vagrant_prefix) and net.interface not in seen %}
      {% do seen.append(net.interface) %}
kill_default_route_{{ net.interface }}:
  cmd.run:
      {% if grains['os'] == 'Windows' %}
    - names:
        - route delete 0.0.0.0 mask 0.0.0.0 {{ net.gateway }}
        - route add -p 0.0.0.0 mask 0.0.0.0 {{ net.gateway }} metric 9999  {# so that the other route is preferred #}
      {% else %}
      {# a high metric so that the other route is preferred. Linux allows only one IPv4
         default route per metric, so each interface gets its own, fixed by its ifindex;
         replace-then-prune keeps reruns from shuffling or losing routes. #}
      {% set metric = 9000 + salt['file.read']('/sys/class/net/' ~ net.interface ~ '/ifindex') | int %}
    - names:
        - ip route replace default via {{ net.gateway }} dev {{ net.interface }} metric {{ metric }}
        - ip -4 route show default via {{ net.gateway }} dev {{ net.interface }} | awk '{m=0; for (i=1; i<NF; i++) if ($i=="metric") m=$(i+1); print m}' | grep -vx {{ metric }} | xargs -r -n1 ip route del default via {{ net.gateway }} dev {{ net.interface }} metric
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
