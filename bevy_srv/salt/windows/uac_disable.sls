---
# Salt state for preventing Windows 10 Cortana from running
#
#see PCWorld article
#
{% if grains['os'] == 'Windows' %}
'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System':
  reg.present:
    - vname: EnableLUA
    - vdata: 0
    - vtype: REG_DWORD
{% endif %}
...

