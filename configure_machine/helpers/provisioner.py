"""
Help the user install a copy of Vagrant and Virtualbox
"""
def install_vagrant():

    import webbrowser, subprocess
    from pathlib import Path

    debian = False
    # noinspection PyBroadException
    try:
        if 'ID_LIKE=debian' in Path('/etc/os-release').read_text():
            debian = True
    except Exception:
        pass
    if debian:
        subprocess.call('apt install virtualbox', shell=True)
    else:
        webbrowser.open('https://www.virtualbox.org/wiki/Downloads')

    webbrowser.open("https://www.vagrantup.com/downloads.html")

    rtn = subprocess.call('vagrant -v', shell=True)
    vagrant_present = rtn == 0
    return vagrant_present

