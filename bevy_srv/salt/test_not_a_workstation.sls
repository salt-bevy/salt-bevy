{% if grains['virtual'] != 'physical' %}
checked_running_on_VM:
  test.nop:
    - name: Running on a {{ grains['virtual'] }} virtual machine. Okay.
{% elif grains['os'] == 'Windows' and 'Server' in salt['grains.get']('osfullname', '') %}
checked_running_on_Windows_server:
  test.nop:
    - name: Running on a server version of Windows. Okay.
{% else %}
  {% set home = salt['environ.get']('HOMEPATH') if grains['os'] == "Windows" else salt['environ.get']('HOME') if grains['os'] == 'MacOS' else salt['file.join']('/home', salt['environ.get']('SUDO_USER', salt['environ.get']('USER'))) %}

  {% if salt['file.directory_exists'](salt['file.join'](home, "Desktop")) %} {# do not do this on user's workstation #}
checked_but_is_a_workstation:
  test.fail_without_changes:
    - name: Desktop directory detected in {{ home }}. You probably should not do this on a workstation.
    - failhard: True
  {% else %}
checked_no_desktop_found:
  test.nop:
    - name: No Desktop found in {{ home }}. Probably running on server hardware.
  {% endif %}
{% endif %}
    - order: 2
