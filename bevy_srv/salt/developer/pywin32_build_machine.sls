---
# Salt state for provisioning a Windows machine to build pywin32
#
{% if grains['os'] != 'Windows' %}
sorry_Windows_only:
  test.fail_without_changes:
    - name: 'Sorry: pywin32 can only be built on a Windows operating system'
    - order: 1
    - failhard: True
{% endif %} {# Windows #}

include:
  - windows.vs2019_build_tools
  - windows.vc4python
...
