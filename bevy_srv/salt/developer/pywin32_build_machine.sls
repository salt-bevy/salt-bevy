---
# Salt state for provisioning a Windows (or Linux) server to build PlayReady
#
{% set NUnit_Console_version = '3.9.0' %}
{% set NUnit_Console_tag = 'v3.9' %}

{% if grains['os'] != 'Windows' %}
  {# set up an Ubuntu build machine #}
mono_install:
  pkgrepo.managed:
    - name: "deb https://download.mono-project.com/repo/ubuntu stable-{{ grains['oscodename'] }} main"
    - keyserver: hkp://keyserver.ubuntu.com:80
    - keyid: 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
  pkg.installed:
    - names:
      - mono-complete
      - nuget
    - require_in:
      - nuget_v3_config
{% set nuget_config = salt['environ.get']('HOME') ~ '/.nuget/NuGet/NuGet.Config' %}

{% else %} {# Windows #}

{% if grains['osrelease_info'][0] == 2012 %} {# this is for an obsolete version of Windows and therefore untested #}
{% set vs_version = salt['pillar.get']('playready:visual_studio_version') %}
dotnet3.5:  # needed only for wixtoolset
  chocolatey.installed:
    - name: dotnet3.5
{{ vs_version }}:
  chocolatey.installed:
    - name: {{ vs_version }}
wixtoolset:
  chocolatey.installed:
    - require:
      - dotnet3.5
      - {{ vs_version }}

{% else %}  {# Windows server more recent than 2012 #}

{% set vs_version = salt['pillar.get']('playready:visual_studio_year', '! ERROR: Missing Pillar playready:visual_studio_year !') %}
include:
  - windows.vs{{ vs_version }}_build_tools  # from https://github.com/salt-bevy, which also installs chocolatey

visualstudio{{ vs_version }}-workload-netweb:
  chocolatey.installed

{% endif %}

dotnet4.0:  # needed for PlayReady SDK 3.0?
  chocolatey.installed:
    - name: dotnet4.0

nuget:
  chocolatey.installed:
    - name: nuget.commandline
    - require_in:
      - nuget_v3_config
{% set nuget_config = salt['environ.get']('APPDATA') ~ '\\NuGet\\NuGet.Config' %}

NUnit_install:
  chocolatey.installed:
    - name: nunit-console-runner

windows-sdk-8.1:  # TODO: is this needed?
  chocolatey.installed:
    - name: windows-sdk-8.1
{% endif %} {# Windows #}

NUnit_console_install:
  file.directory:
    - name: /opt/NUnit
    - makedirs: True
    # - file_mode: 775
  archive.extracted:
    - name: /opt/NUnit
    - source: https://github.com/nunit/nunit-console/releases/download/{{ NUnit_Console_tag }}/NUnit.Console-{{ NUnit_Console_version }}.zip
    - skip_verify: True
    - enforce_toplevel: False
    - if_missing: /opt/NUnit/nunit3-console.exe

nuget_v3_config:
  cmd.run:
    - name: nuget sources remove -Name ArtifactoryNuGet
    - onlyif:
      - nuget sources list | grep ArtifactoryNuGet

nuget_v3_config_1:
  cmd.run:
    - name: nuget sources add -Name ArtifactoryNuGet -Source {{ salt['pillar.get']('playready:installer_nuget_url', '! ERROR: Missing Pillar playready:installer_nuget_url !') }}
    - require:
      - nuget_v3_config
...
