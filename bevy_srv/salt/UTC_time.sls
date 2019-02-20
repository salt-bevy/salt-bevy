---
# Salt state for making a server run in UTC
#
# see https://superuser.com/questions/975717/does-windows-10-support-utc-as-bios-time
#
UTC:
  timezone.system:
    - name: Etc/GMT
{% if grains['os'] != 'Windows' %}
    - utc: True
{% else %}
    - utc: False  {# Salt will not set this, so we do it ourselves in the registry #}

'HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\TimeZoneInformation\RealTimeIsUniversal':
  reg.present:
    - vdata: 1
    - vtype: REG_DWORD

Z_24_Hour:
    cmd.run:
      - name: $culture = Get-Culture; $culture.DateTimeFormat.ShortTimePattern = 'HH:mm:ss'; $culture.DateTimeFormat.LongTimePattern = 'HH:mm:ss.ff'; Set-Culture $culture
      - shell: powershell
{% endif %}
...

