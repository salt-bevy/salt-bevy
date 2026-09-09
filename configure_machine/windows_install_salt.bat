powershell wget -outfile bootstrap-salt.ps1 http://raw.githubusercontent.com/saltstack/salt-bootstrap/develop/bootstrap-salt.ps1
powershell .\bootstrap-salt.ps1 -pythonversion 3 -runservice false -master localhost
py -3 -m windows_sudo.sudo icacls "%ProgramData%\Salt Project\Salt\conf" /grant %USERDOMAIN%\%USERNAME%:(F) /T /C /L
powershell new-item "%ProgramData%\Salt Project\Salt\conf\minion.d" -itemtype directory -ErrorAction silentlycontinue
powershell Copy-Item masterless_minion.conf -Destination "%ProgramData%\Salt Project\Salt\conf\minion.d\00_masterless_default.conf"
del bootstrap-salt.ps1
call "%ProgramFiles%\Salt Project\Salt\salt-call.bat" --version
