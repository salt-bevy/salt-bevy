---
# Salt state for installing Visual Studio C++ non-GUI compiler
#
include:
  - windows.install_chocolatey

visualstudio2019buildtools:
  chocolatey.upgraded:
    - require:
      - install_chocolatey

visualstudio2019-workload-python:
  chocolatey.upgraded:
    - name: visualstudio2019-workload-python
    - require:
      - visualstudio2019buildtools

visualstudio2019-workload-nativedesktop:
  chocolatey.upgraded:
    - name: visualstudio2019-workload-nativedesktop
    - require:
      - visualstudio2019buildtools
...
