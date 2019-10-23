#fs.inotify.max_user_watches:
#  sysctl.present:
#    - value: 1048576

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
