powershell wget -outfile bootstrap-salt.ps1 http://raw.githubusercontent.com/saltstack/salt-bootstrap/develop/bootstrap-salt.ps1
powershell .\bootstrap-salt.ps1 -pythonversion 3 -runservice false -master localhost
copy .\masterless_minion.conf \salt\conf\minion.d
rem del bootstrap-salt.ps1
call C:\salt\salt-call.bat --version
