# Passed by build_boxes.py for --providers virtualbox on arm64 hosts (Apple Silicon).
# The packer VirtualBox plugin always adds an x86 PIIX4 controller named "IDE", which an
# armv8 VM can't start with (VERR_MAIN_CONFIG_CONSTRUCTOR_COM_ERROR from
# i_configStorageCtrls in VBox.log). Bento's own aarch64 list
# (packer_templates/pkr-sources.pkr.hcl) tries to remove it as "IDE Controller", which
# fails with VBOX_E_OBJECT_NOT_FOUND. Same list otherwise; the disk and install ISO are
# on the VirtioSCSI controller, so nothing is lost with the IDE one.
vboxmanage = [
  ["modifyvm", "{{.Name}}", "--chipset", "armv8virtual"],
  ["modifyvm", "{{.Name}}", "--audio-enabled", "off"],
  ["modifyvm", "{{.Name}}", "--nat-localhostreachable1", "on"],
  ["modifyvm", "{{.Name}}", "--cableconnected1", "on"],
  ["modifyvm", "{{.Name}}", "--usb-xhci", "on"],
  ["modifyvm", "{{.Name}}", "--graphicscontroller", "qemuramfb"],
  ["modifyvm", "{{.Name}}", "--mouse", "usb"],
  ["modifyvm", "{{.Name}}", "--keyboard", "usb"],
  ["storagectl", "{{.Name}}", "--name", "IDE", "--remove"],
]
