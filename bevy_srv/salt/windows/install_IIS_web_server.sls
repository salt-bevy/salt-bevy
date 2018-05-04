---
# Salt state for installing Windows server features
#
# Install feature by name:
# Installs the IIS Web Server Role (Web-Server)
IIS-WebServerRole:
  win_servermanager.installed:
    - recurse: True
    - name: Web-Server
# add some tools
install_IIS_2:
  win_servermanager.installed:
    - recurse: True
    - name:  'Web-Net-Ext45,Web-Scripting-Tools'
...
