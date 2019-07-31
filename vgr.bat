rem running Vagrant using salt-bevy definitions
@set VAGRANT_CWD=..\salt-bevy
set VAGRANT_PWD=%CD%
set arg2=%2
if [%arg2%] == [generic_no_salt] (set arg2=generic) else (set VAGRANT_SALT=t)
if [%arg2%] NEQ [generic] goto normal
set GENERIC=t
if not %1==up goto not_up
if not "%4"=="" (set NODE_ADDRESS=%4)
if not "%5"=="" (set NODE_MEMORY=%5)
if not "%6"=="" (set NODE_BOX=%6)
:not_up
vagrant.exe %1 %3
@set NODE_ADDRESS=
@set NODE_MEMORY=
@set NODE_BOX=
@set VAGRANT_SALT=
@goto exit
:normal
@set GENERIC=
vagrant.exe %1 %2
:exit
@set VAGRANT_CWD=
@set VAGRANT_PWD=
