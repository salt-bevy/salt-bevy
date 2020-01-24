---
# salt state file for installing the SaltStack netAPI server components
#    https://docs.saltstack.com/en/latest/ref/netapi/all/salt.netapi.rest_cherrypy.html
{% set salt_root = salt['file.dirname'](salt['config.get']('conf_file')) %}
include:
  - test_not_a_workstation
  - bevy_master
  - .pepper

salt-api:
  pkg.installed:
    - unless:
      - salt-api --version

cherrypy:
  pip.installed:
    - names:
      - CherryPy
      - pyOpenSSL
      - ws4py

tls.create_self_signed_cert:
  module.run:
      - kwargs:
          O: {{ salt['pillar.get']('salt-api:tls_organization', 'Dummy Organization') }}
          L: {{ salt['pillar.get']('salt-api:tls_location', 'supply in manual_bevy_settings.sls') }}
          emailAddress: {{ salt['pillar.get']('salt-api:tls_emailAddress', 'nobody@nowhere.test') }}

{{ salt_root }}/master.d/api.conf:
  file.managed:
    - makedirs: True
    - source: salt://bevy_master/files/api.conf
    - template: jinja

salt-api-service:
  service.running:
    - name: salt-api
    - enable: True
    - watch:
      - pkg: salt-api
      - file: {{ salt_root }}/master.d/api.conf
    - require:
      - delay_master_restart
...
