---
# Salt state for installing a development copy of Salt
#
{% set projects_root = salt['config.get']('projects_root', '/opt') %}

{{ projects_root }}/salt:
  git.latest:
    - name: https://github.com/saltstack/salt.git
    - target: {{ projects_root }}/salt
    - rev: develop
    - branch: develop
    - require_in:
      - git_add_remote

git_add_remote:
  cmd.run:
    - cwd: {{ projects_root }}/salt
    - names:
      - 'git remote add upstream https://github.com/saltstack/salt || exit /b 0'
      - 'git fetch --tags upstream'
    - hide_output: True

salt_dev_env:  # install the salt dependencies
{% if grains['os'] == 'Windows' %}
  cmd.run:
    - shell: powershell
    - name: './build_env_2.ps1'
    - cwd: {{ projects_root }}/salt/pkg/windows
    - require_in:
      - dev_env_salt

  {% set project_python = 'C:\\salt\\bin\\python.exe' %}
{% else %}  {# not Windows #}

  {# TODO: convert this to virtualenv.managed #}
  {% set project_python = '/usr/bin/python' %}
  pip.installed:
    - cwd: {{ projects_root }}/salt
    - editable: True
    - name: '.'
{% endif %} {# else not Windows #}

dev_env_salt:  # install the development copy of salt
  cmd.run:
    - name: '{{ project_python }} setup.py install'
    - cwd: {{ projects_root }}/salt
...
