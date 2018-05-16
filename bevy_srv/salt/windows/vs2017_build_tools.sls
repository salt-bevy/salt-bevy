---
# Salt state for installing Visual Studio C++ non-GUI compiler
#
vs_2017_choc_bt:
  module.run:
    - name: chocolatey.bootstrap
    - require_in:
      - visualstudio2017buildtools

{# NOTE: there is a bug in old Salt-Minions. You may need to hand install 2018.3.0 for chocolatey to work.  #}
dotnet4.0:
  chocolatey.installed:
    - name: dotnet4.0

visualstudio2017buildtools:
  chocolatey.installed:
    - name: visualstudio2017buildtools

visualstudio2017-workload-vctools_bt:
  chocolatey.installed:
    - name: visualstudio2017-workload-vctools
    - require:
      - visualstudio2017buildtools

visualstudio2017-workload-netweb_bt:
  chocolatey.installed:
    - name: visualstudio2017-workload-netweb
    - require:
      - visualstudio2017buildtools
...
