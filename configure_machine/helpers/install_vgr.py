#!/usr/bin/env python3
"""
Installs a global "vgr" command, so that Vagrant commands can control this salt-bevy
checkout's VMs from any directory -- not just from a sibling "projects" folder.

Re-uses the windows-sudo package's directory-of-truth / elevation logic (a per-user
Python install already puts its own "Scripts" directory on PATH and is writable
without elevation; an "all users" install needs C:\\Windows and admin rights).
"""
import os, sys
from pathlib import Path

try:
    from windows_sudo import sudo
except ImportError:
    print('ERROR: this requires the "windows-sudo" package. Try "py -3 -m pip install windows-sudo".')
    sys.exit(10)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # .../configure_machine/helpers/install_vgr.py -> repo root
VGR_TEMPLATE = REPO_ROOT / 'vgr.bat'
RELATIVE_CWD_LINE = '@set VAGRANT_CWD=..\\salt-bevy'


def build_vgr_bat():
    template = VGR_TEMPLATE.read_text()
    if RELATIVE_CWD_LINE not in template:
        raise RuntimeError('"{}" has changed -- expected to find "{}" in it.'.format(
            VGR_TEMPLATE, RELATIVE_CWD_LINE))
    return template.replace(RELATIVE_CWD_LINE, '@set "VAGRANT_CWD={}"'.format(REPO_ROOT))


def main():
    if os.name != 'nt':
        print('This installer is for Windows only.')
        print('On other platforms, just put a copy of "vgr" on your PATH.')
        sys.exit(1)

    install_dir = sudo.user_python_scripts_dir() or r'C:\Windows'
    whole_machine = (install_dir == r'C:\Windows')
    if whole_machine and not sudo.isUserAdmin():
        print('Elevation is required to install into "{}" -- requesting it now...'.format(install_dir))
        sudo.runAsAdmin([os.path.abspath(__file__)], python_shell=True)
        return

    dest = Path(install_dir) / 'vgr.bat'
    dest.write_text(build_vgr_bat())
    print('Installed "vgr" into "{}"'.format(install_dir))
    print('It points at this checkout: "{}"'.format(REPO_ROOT))
    print()
    print('Open a NEW command window and type "vgr status" to try it from any directory.')
    print('(Re-run this installer if you move or re-clone this checkout.)')
    try:
        input('Hit <Enter> to continue . . .')
    except EOFError:
        pass


if __name__ == '__main__':
    main()
