# {# This is the top for the initial creation of the bevy master #}
{# it will not be used in normal operation except for masterless minions #}
base:
  '*':
    - common
    - administrator_user
    - interactive_user
    - cleanup_vagrant
    - ensure_user_privs

  bevymaster:
    - bevy_master.define_interactive_user
    - bevy_master
    - bevy_master.local_windows_repository

  local:
    - bevy_master.define_interactive_user
    - bevy_master
    - bevy_master.local_windows_repository