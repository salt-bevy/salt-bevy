---
# Salt state for installing Visual Studio 2017 Professional
#
include:
  - windows.install_chocolatey

visualstudio2019buildtools:
  chocolatey.installed

visualstudio2019-workload-python:
  chocolatey.installed
...
