---
# Salt state to install https://brew.sh/ on MacOS
  {% set my_user = salt['config.get']('my_windows_user', salt['cmd.run']("python -c \"import os; print(os.getenv(\'SUDO_USER\', 'vagrant'))\"")) %}

brew_install:
  cmd.run:
    - name: yes | ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    - runas: {{ my_user }}
    - unless: brew --version
