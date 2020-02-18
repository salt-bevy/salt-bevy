Accept Microsoft Eula:
  environ.setenv:
    - name: ACCEPT_EULA
    - value: Y

{% if salt['grains.get']('os_family') == 'Debian' -%}
microsoft_repo:
  pkgrepo.managed:
    - humanname: Microsoft repository
    - name: deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-{{ salt['grains.get']('os')|lower }}-{{ salt['grains.get']('oscodename')|lower }}-prod {{ salt['grains.get']('oscodename')|lower }} main
    - file: /etc/apt/sources.list.d/microsoft.list
    - key_url: https://packages.microsoft.com/keys/microsoft.asc
    - architectures: amd64
    - clean_file: True
{% endif -%}

msodbcsql17:
  pkg.installed:
    - require:
      - pkgrepo: microsoft_repo
      - environ: Accept Microsoft Eula
