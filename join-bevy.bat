@ECHO ON
py -3 ..\salt-bevy\configure_machine\bootstrap_bevy_member_here.py %1 %2 %3 %4 %5
if NOT EXIST vgr.bat copy ..\salt-bevy\vgr.bat .
