---
# salt state file for reconfiguring a hardware machine using PXE
# -- controlled by pillar data in bevy_settings_pillar.sls

include:
  - bevy_master  # set up the bevy master
  - dnsmasq.pxe_auto_install  # load and start the pxe_boot server

start_hw:
  module.run:  # wake the machine to start the install process
    - name: network.wol
      mac: {{ pillar['wol_test_mac'] }}
...
