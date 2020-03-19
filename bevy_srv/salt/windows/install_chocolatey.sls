---
# Salt state for installing the chocolatey installation tool
#
{# using cmd.run rather than module.run to get an extra layer of isolation #}
install_chocolatey:
  cmd.run:
    - name: salt-call chocolatey.bootstrap
    - unless: choco list --lo --noop
...
