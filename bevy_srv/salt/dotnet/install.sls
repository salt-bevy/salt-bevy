---
# Salt state for provisioning a server to run a dotnet_core program
#
{% if grains['os'] == 'Windows' %}

include:
  - windows.install_chocolatey

dotnetcore-sdk:
  chocolatey.installed

{% elif grains['os'] == 'MacOS' %}

include:
  - macos.install_homebrew

dotnet_core_mac:
  pkg.installed:
    - name: homebrew/cask/dotnet-sdk

  {% else %}

  {% if salt['grains.get']('os_family') == 'Debian' %}
microsoft_repo_dn:
  pkgrepo.managed:
    - humanname: Microsoft repository
    - name: deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-{{ salt['grains.get']('os')|lower }}-{{ salt['grains.get']('oscodename')|lower }}-prod {{ salt['grains.get']('oscodename')|lower }} main
    - file: /etc/apt/sources.list.d/microsoft.list
    - key_url: https://packages.microsoft.com/keys/microsoft.asc
    - architectures: amd64
    - clean_file: True
  {% endif %}
dotnetcore_install:
  pkg.installed:
    - names:
      - apt-transport-https
      - dotnet-sdk-3.1
      - aspnetcore-runtime-3.1
    - requires:
        - pkgrepo: microsoft_repo_dn

{% endif %} {# Windows else #}
...
