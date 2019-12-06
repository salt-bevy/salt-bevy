# SaltStack state to enable KEEPALIVE settings in the configuration.
# https://docs.saltstack.com/en/latest/ref/configuration/minion.html#keepalive-settings
#
{% set salt_root = salt['file.dirname'](salt['config.get']('conf_file')) %}
#
{{salt_root}}/minion.d/keepalive.conf:
  file.managed:
    - replace: false
    - contents: |
        tcp_keepalive: true
        tcp_keepalive_idle: 300
