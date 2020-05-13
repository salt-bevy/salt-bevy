powershell wget -outfile bootstrap-salt.ps1 http://raw.githubusercontent.com/saltstack/salt-bootstrap/develop/bootstrap-salt.ps1
powershell .\bootstrap-salt.ps1 -pythonversion 3 -runservice false -master localhost
py -3 helpers\sudo.py icacls c:\salt\conf /grant %USERDOMAIN%\%USERNAME%:(F) /T /C /L
powershell new-item C:\\salt\\conf\\minion.d -itemtype directory -ErrorAction silentlycontinue
powershell Copy-Item masterless_minion.conf -Destination C:\salt\conf\minion.d\00_masterless_default.conf
del bootstrap-salt.ps1
call C:\salt\salt-call.bat --version
