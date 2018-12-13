---
# Salt state for installing https://www.mono-project.com/
#
{% if grains['os'] == 'Windows' %}
include:
  - windows.install_chocolatey

monodevelop:
  chocolatey.upgraded:
    - require:
      - install_chocolatey

{% else %}
mono:
  pkgrepo.managed:
    - humanname: mono-project
  {% if grains['os_family'] == 'Debian' %}
    {% if grains['os'] == 'Ubuntu' and grains['osrelease'] == '16.04' %}
    - name: "deb https://download.mono-project.com/repo/ubuntu stable-xenial main"
    {% elif grains['os'] == 'Ubuntu' %}  {# Ubuntu 18.04 and later #}
    - name: "deb https://download.mono-project.com/repo/ubuntu stable-bionic main"
    {% elif grains['os'] == 'Raspbain' %}  {# presume Raspbain 9 #}
    - name: "deb https://download.mono-project.com/repo/debian stable-raspbianstretch main"
    {% else %}  {# presume Debian 9 #}
    - name: "deb https://download.mono-project.com/repo/debian stable-stretch main"
    {% endif %}
    - keyserver: hkp://keyserver.ubuntu.com:80
    - keyid: 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
    - require_in:
      - monodevelop
  {% else %}  {# RPM based -- code not tested by VDC #}
    - baseurl: https://download.mono-project.com/repo/centos7-stable.repo
    - gpgkey: https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
  {% endif %}  {# Debian family ... else ... #}

monodevelop:
  pkg.installed:
    - name: mono-complete
{% endif %}  {# Windows ... else ... #}
...
