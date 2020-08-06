rem running Vagrant using salt-bevy definitions
@setlocal
@set VAGRANT_CWD=..\salt-bevy
@set VAGRANT_PWD=%CD%
@set arg1=%1
@set VAGRANT_SALT=
@if [%arg1%] EQU [--no-salt] (SHIFT) else (set VAGRANT_SALT=true)
@set arg2=%2
@if [%arg2%] NEQ [generic] goto normal
set GENERIC=true
@if not %1==up goto not_up
if not "%~4"=="" (set NODE_ADDRESS=%4)
if not "%~5"=="" (set NODE_MEMORY=%5)
if not "%~6"=="" (set NODE_BOX=%6)
vagrant.exe %1 %3 %7 %8 %9
@goto exit
:not_up
vagrant.exe %1 %3 %4 %5 %6 %7 %8 %9
@goto exit
:normal
vagrant.exe %1 %2 %3 %4 %5 %6 %7 %8 %9
:exit
