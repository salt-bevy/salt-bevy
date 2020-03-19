net session >nul 2>&1
if NOT ERRORLEVEL 1 GOTO OKAY
@echo SORRY: This script must be run from an Administrator command (cmd) prompt.
@GOTO END
:OKAY
@echo Bootstrapping chocolatey now.  Please be patient.
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
choco install -y python3
py -3 -m pip install pyyaml ifaddr passlib pywin32
:END
