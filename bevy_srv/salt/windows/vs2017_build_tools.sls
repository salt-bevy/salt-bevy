---
# Salt state for installing Visual Studio C++ non-GUI compiler
#
vs_2017_choc_bt:
  module.run:
    - name: chocolatey.bootstrap
    - require_in:
      - visualstudio2017buildtools

visualstudio2017buildtools:
  chocolatey.installed

visualstudio2017-workload-vctools:
  chocolatey.installed
...
