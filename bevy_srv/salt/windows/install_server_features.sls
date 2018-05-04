---
# Salt state for installing Windows server features
#
# Install feature by name:
# Installs the IIS Web Server Role (Web-Server)
IIS-WebServerRole:
  win_servermanager.installed:
    - recurse: True
    - name: Web-Server

# Install multiple features, exclude the Web-Service
install_multiple_features:
  win_servermanager.installed:
    - recurse: True
    - features:
      - RemoteAccess
      - XPS-Viewer
      - SNMP-Service
    - exclude:
      - Web-Service
...
