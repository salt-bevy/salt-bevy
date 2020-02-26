---
# salt state file for all systems
{# this is an example of things you may always want installed. #}

{% if grains['os_family'] == 'Windows' %}
{% set install_git_using_traditional_tools = False %}
{% if install_git_using_traditional_tools %}
pkg.refresh_db:
  module.run:
  - require_in:
    - pkg: windows_packages
windows_packages:
{# Assumes that you ran salt_master.local_windows_repository on the Master #}
  pkg.installed:
    - pkgs:
      - npp
      - git
{% endif %}

choco_boot:
  cmd.run:
    - name: salt-call chocolatey.bootstrap
    - require_in:
      - windows_py3
    - unless:
      - choco --version

windows_py3:
  chocolatey.installed:
    - name:
      - python3
    - unless:
      - py -3 --version

{% if not install_git_using_traditional_tools %}
notepadplusplus.install:
  chocolatey.installed:
    - unless:
      - where notepad++
git.install:
  chocolatey.installed:
    - unless:
      - git --version
    - package_args: "/GitAndUnixToolsOnPath"
{% endif %}

windows_pygit2_failure_workaround:
   cmd.run:
     - name: c:\salt\bin\python -m pip install pygit2

{# Note: .sls files are interpreted on the Minion, so the environment variables are local to it #}
{{ salt['environ.get']('SystemRoot') }}/edit.bat:  {# very dirty way to create an "edit" command for all users #}
  file.managed:
    - contents:
      - '"{{ salt['environ.get']('ProgramFiles(x86)') }}\Notepad++\Notepad++.exe" %*'
    - unless:  {# do not install this if there is an existing "edit" command #}
      - where edit
{{ salt['environ.get']('SystemRoot') }}/tail.bat:  {# very dirty way to create a "tail -f" command for all users #}
  file.managed:
    - contents: |
        @ECHO OFF
        IF "%1"=="-f" (
        powershell get-content "%2" -tail 20 -wait
        ) ELSE (
        start /b powershell get-content "%1" -tail 20
        )
    - unless:  {# do not install this if there is an existing "tail" command #}
      - where tail
include:
  - restart_the_minion

{% else %}  {# Not Windows #}

{% if grains['mem_total'] < 2000 %}  {# NOTE: k8s will demand NO swap #}
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
      - nano
      {% if grains['pythonversion'][0] == 2 %}
      - python-pip
      {% endif %}
      - python3
      - python3-pip
      - tree
{% endif %}

{% if salt['grains.get']('os') == 'Ubuntu' %}
ubuntu_packages:
  pkg.installed:
    - pkgs:
      {% if grains['osrelease'] < '18.04' %}
      - python-software-properties
      {% endif %}
      - vim-tiny
      - virt-what
      {% if grains['osrelease'] < '16.04' %}
      - python-git  # fallback package if pygit2 is not found.
      {% elif grains['pythonversion'][0] == 3 %}
      - python3-pygit2
      {% else %}
      - python-pygit2
      {% endif %}
      {% if grains['locale_info']['defaultlanguage'] != 'en_US' %}
      - 'language-pack-en'
      {% endif %}
{% endif %}

{% if grains['os_family'] == 'MacOS' %}
MacOS_common:
  test.nop:
    - name: 'successful operation on MacOS complete'
{% endif %}

{% endif %}
...
