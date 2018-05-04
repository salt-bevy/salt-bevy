#!/usr/bin/env python3
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4

# (C) COPYRIGHT © Preston Landers 2010
# Released under the same license as Python 2.6.5
#
# Python3 update by: Vernon Cole 2018

import sys, os, traceback, time


def isUserAdmin():
    if os.name == 'nt':
        import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            traceback.print_exc()
            print("Admin check failed, assuming not an admin.")
            return False
    elif os.name == 'posix':
        # Check for root on Posix
        return os.getuid() == 0
    else:
        raise RuntimeError("Unsupported operating system for this module: {}".format(os.name))


def runAsAdmin(cmdLine=None, wait=True):
    if cmdLine is None:
        python_exe = sys.executable
        cmdLine = [python_exe] + sys.argv  # run the present Python command with elevation.
    else:
        if not isinstance(cmdLine, (tuple, list)):
            raise ValueError("cmdLine is not a sequence.")

    cmd = '"{}"'.format(cmdLine[0])

    params = " ".join(['"{}"'.format(x) for x in cmdLine[1:]])

    if os.name == 'posix':
        import subprocess
        cmd = 'sudo {} {}'.format(cmd, params)
        print('Running command-->', cmd)
        rc = subprocess.call(cmd, shell=True)

    elif os.name == 'nt':
        try:
            import win32con, win32event, win32process
        except ImportError:
            raise ImportError('PyWin32 module has not been installed.')
        # noinspection PyUnresolvedReferences
        from win32com.shell.shell import ShellExecuteEx
        # noinspection PyUnresolvedReferences
        from win32com.shell import shellcon

        showCmd = win32con.SW_SHOWNORMAL

        lpVerb = 'runas'  # causes UAC elevation prompt.
        print()
        print("This window is waiting while a child window is run as an Administrator...")
        print("Running command-->{} {}...".format(cmd, params))
        procInfo = ShellExecuteEx(nShow=showCmd,
                                  fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                  lpVerb=lpVerb,
                                  lpFile=cmd,
                                  lpParameters=params)
        if wait:
            procHandle = procInfo['hProcess']
            if procHandle is None:
                print("Windows Process Handle is Null. RunAsAdmin did not create a child process.")
                rc = None
            else:
                win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
                rc = win32process.GetExitCodeProcess(procHandle)
                # print("Process handle %s returned code %s" % (procHandle, rc))
                procHandle.Close()
        else:
            rc = None
    else:
        raise RuntimeError("Unsupported operating system for this module: {}".format(os.name))
    return rc


def run_elevated(command=None):
    if not isUserAdmin():
        rc = runAsAdmin(command)
        time.sleep(3)
        sys.exit(rc)


def test(command=None):
    if not isUserAdmin():
        print("You're not an admin. You are running PID={} with command-->{}".format(os.getpid(), command))
        rc = runAsAdmin(command)
    else:
        sys.argv.remove("--test")
        print("You ARE an admin. You are running PID={} with command-->{}".format(os.getpid(), command))
        if len(sys.argv) > 1:
            import subprocess
            rc = subprocess.call(sys.argv[1:], shell=True)
        else:
            rc = 0
        time.sleep(2)
        input('Press Enter to exit.')
    return rc


if __name__ == "__main__":
    if "--test" in sys.argv:
        print('......testing with no arguments.......')
        test()
        if not isUserAdmin():
            print('....... NEXT, a real useful example ...........')
            if os.name == 'nt':
                call = ["c:\\Windows\\notepad.exe", "C:\Windows\System32\drivers\etc\hosts"]
            else:
                call = ['nano', '/etc/hosts']
            test(call)
    elif len(sys.argv) == 1:
        print('usage: sudo <command> <arguments>  # will run with elevated priviledges')
    else:
        run_elevated(sys.argv[1:])
