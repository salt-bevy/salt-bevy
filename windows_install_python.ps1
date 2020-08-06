#Requires -RunAsAdministrator
#
# You must do "set-executionpolicy bypass" or "set-executionpolicy allsigned" to run this script.
#
write-host "Bootstrapping chocolatey now.  Please be patient."
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
#
write-host "choco install -y python3"
choco install -y python3
write-host "py -3 -m pip install pyyaml ifaddr passlib pywin32"
py -3 -m pip install pyyaml ifaddr passlib pywin32
