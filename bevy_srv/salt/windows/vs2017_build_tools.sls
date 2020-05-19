---
# Salt state for installing Visual Studio C++ non-GUI compiler
#
include:
  - windows.install_chocolatey

{# NOTE: there is a bug in old Salt-Minions. You may need to hand install 2018.3.0 for chocolatey to work.  #}
#dotnet4.0:
#  chocolatey.installed:
#    - name: dotnet4.0

visualstudio2017buildtools:
  chocolatey.upgraded:
    - require:
      - install_chocolatey

visualstudio2017-workload-vctools_bt:
  chocolatey.upgraded:
    - name: visualstudio2017-workload-vctools
    - require:
      - visualstudio2017buildtools

visualstudio2017-workload-netweb_bt:
  chocolatey.upgraded:
    - name: visualstudio2017-workload-netweb
    - require:
      - visualstudio2017buildtools
...
