# {{ pillar['salt_created_message'] }}
# {# This is the top for the initial creation of the bevy master #}
{# it will not be used in normal operation #}
base:
  '*':
    - common

  bevyma
    - bevy_master.define_interactive_user
    - bevy_master
    - bevy_master.local_windows_repository
    - playready_configure_master
