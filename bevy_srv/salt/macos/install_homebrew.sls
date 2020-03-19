---
# Salt state to install https://brew.sh/ on MacOS
  {% set my_user = salt['config.get']('my_windows_user', salt['cmd.run']("python -c \"import os; print(os.getenv(\'SUDO_USER\', 'vagrant'))\"")) %}

brew_install:
  {% if grains['os'] == 'MacOS' %}
  cmd.run:
    - name: yes | ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    - runas: {{ my_user }}
    - unless: brew --version
  {% else %}
  test.fail_without_changes:
    - name: You cannot install Homebrew on anything other than a Mac.
  {% endif %}
