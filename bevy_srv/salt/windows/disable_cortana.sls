---
# Salt state for preventing Windows 10 Cortana from running
#
#see PCWorld article
#
{% if grains['os'] == 'Windows' and grains['osrelease'] == '10' %}
'HKLM\Software\Policies\Microsoft\Windows\Windows Search':
  reg.present:
    - vname: AllowCortana
    - vdata: 0
    - vtype: REG_DWORD
{% endif %}
...

