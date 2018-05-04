---
# salt state file for all systems
{# this is an example of things you may always want installed. #}

{% if grains['os_family'] == 'Windows' %}

pkg.refresh_db:
  module.run:
  - require_in:
    - pkg: windows_packages

windows_packages:
{# Assumes that you ran bevy_master.local_windows_repository on the Master #}
  pkg.installed:
    - pkgs:
      - npp
      - git

windows_pygit2:
  pip.installed:
    - name: pygit2
    - cwd: 'c:\salt\bin\Scripts\'
    - bin_env: '.\pip.exe'
    - reload_modules: True
windows_pygit2_failure_workaround:
   cmd.run:
     - name: 'c:\salt\bin\python -m pip install pygit2'
     - onfail:
       - pip: windows_pygit2

{# Note: .sls files are interpreted on the Minion, so the environment variables are local to it #}
{{ salt['environ.get']('SystemRoot') }}/edit.bat:  {# very dirty way to create an "edit" command for all users #}
  file.managed:
    - contents:
      - '"{{ salt['environ.get']('ProgramFiles(x86)') }}\Notepad++\Notepad++.exe" %*'
    - unless:  {# do not install this if there is an existing "edit" command #}
      - where edit

{% else %}
{% if grains['mem_total'] < 2000 %}
swapspace:
  pkg.installed:
    - refresh: true
    - cache_valid_time: 600
    - order: 1
{% endif %}

{% if grains['os_family'] == 'Debian' %}
debian_packages:
  pkg.installed:
    - pkgs:
      - git
      - htop
      - mtr
      - nano
      - python-pip
      - tree
{% endif %}

{% if salt['grains.get']('os') == 'Ubuntu' %}
ubuntu_packages:
  pkg.installed:
    - pkgs:
      - jq
      - python-software-properties
      - silversearcher-ag
      - strace
      - vim-tiny
      - virt-what
      {% if grains['osrelease'] < '16.04' %}
      - python-git  # fallback package if pygit2 is not found.
      {% else %}
      - python-pygit2
      {% endif %}
      {% if grains['locale_info']['defaultlanguage'] != 'en_US' %}
      - 'language-pack-en'
      {% endif %}
{% endif %}
{% endif %}
...
