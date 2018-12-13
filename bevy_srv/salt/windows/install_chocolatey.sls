---
# Salt state for installing the chocolatey installation tool
#
install_chocolatey:
  module.run:
    - name: chocolatey.bootstrap

{# NOTE: there is a bug in old Salt-Minions. You may need to hand install 2018.3.0 for chocolatey to work.  #}

