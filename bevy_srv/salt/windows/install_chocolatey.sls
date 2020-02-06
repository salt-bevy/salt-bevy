---
# Salt state for installing the chocolatey installation tool
#
{# using cmd.run rather than module.run to get an extra layer of isolation #}
install_chocolatey:
  cmd.run:
    - name: c:\salt\salt-call.bat chocolatey.bootstrap
    - unless: choco --version
    #- runas:  {{ salt['config.get']('my_windows_user') }}
    #- password: {{ salt['config.get']('my_windows_password') }}

not_really_a_failure:
  test.nop:
    - name: 'A false failure message may have been given for chocolatey.bootstrap.'
    - onfail: [install_chocolatey]
...
