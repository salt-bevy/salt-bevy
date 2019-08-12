---
# Salt state for preventing local user account passwords from expiring
#
#
{% if grains['os'] == 'Windows' %}
disable_passsword_expiration:
  cmd.run:
    - name: 'wmic UserAccount set PasswordExpires=False
{% endif %}
...
