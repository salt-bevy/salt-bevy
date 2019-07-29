rem run Vagrant using salt-bevy definitions
set VAGRANT_CWD=..\salt-bevy
set VAGRANT_PWD=%CD%
vagrant.exe %*
set VAGRANT_CWD=
set VAGRANT_PWD=

