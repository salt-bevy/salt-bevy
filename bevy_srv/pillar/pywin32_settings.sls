---
# salt pillar file for settings related to building pywin32
#
{% set target_root = salt['config.get']('projects_root', 'none')  %}
{% set target_root = '/opt' if target_root|lower == 'none' else target_root %}
{% set target_root = 'C:\\'~target_root[1:] if grains['os'] == 'Windows' and target_root.startswith('/') else target_root %}
pywin32:
  source_directory_parent: {{ target_root }}

  git_branch: 'develop' # use "none" to inhibit loading the source using "git"
{% if grains['osrelease_info'][0] == 2012 %}  {# this has never been tested. It may actually work. #}
  visual_studio_version: 'visualstudio2012professional'
  visual_studio_vcinstalldir: 'C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC\'
  visual_studio_vscommntools: 'C:\Program Files (x86)\Microsoft Visual Studio 11.0\Common7\Tools\'
  visual_studio_vscommntools_name: 'VS110COMNTOOLS'
  visual_studio_settings_bat: '%VS110COMNTOOLS%\vsvars32.bat'
{% else %}  {# supported Windows versions are expected to use Visual Studio 2017 (or parts thereof). #}
  visual_studio_year: '2017'
  visual_studio_version: '15.0'
  visual_studio_vcinstalldir: 'C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\'
  visual_studio_vscommntools_name: 'VS150COMNTOOLS'
  visual_studio_vscommntools: 'C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\'
  visual_studio_settings_bat: 'C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat'
{% endif %}
...
