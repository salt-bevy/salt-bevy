---
# install a Microsoft SQL server
#
{% if grains['os'] == 'Windows' %}
include:
  - windows.install_chocolatey

sql-server-2019:
  chocolatey.upgraded:
    - require:
      - install_chocolatey

{% else %}
sql-server-repo:
  pkgrepo.managed:
    - humanname: ms-sql-server
  {% if grains['os_family'] == 'Debian' %}
    - name: "deb https://packages.microsoft.com/ubuntu/{{ grains['osrelease'] }}/mssql-server-2019 {{ grains['oscodename'] }} main"
    - key_url: https://packages.microsoft.com/keys/microsoft.asc
  {% else %}  {# RPM based -- code not tested by VDC #}
    - baseurl: https://packages.microsoft.com/config/rhel/8/mssql-server-2019.repo
  {% endif %}  {# Debian family ... else ... #}

mssql-server:
  pkg.installed:
    - names:
        - mssql-server
        - mssql-tools
        - unixodbc-dev
    - require: sql-server-repo

need-to-configure-manually:
  test.nop:
    - name 'NOTICE --> You must run the following command manually: "sudo /opt/mssql/bin/mssql-conf setup"'
    - order: last
{% endif %}  {# Windows ... else ... #}
...
