# {# This is the top for the initial creation of the bevy master #}
{# it will not be used in normal operation except for masterless minions #}
base:
  '*':
    - common

  bevymaster:
    - bevy_master.define_interactive_user
    - bevy_master
    - bevy_master.local_windows_repository

  local:
    - bevy_master.define_interactive_user
    - bevy_master
    - bevy_master.local_windows_repository