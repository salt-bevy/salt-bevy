#!/usr/bin/env python3
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4

# (C) COPYRIGHT © Preston Landers 2010
# Released under the same license as Python 2.6.5
#
# Python3 update by: Vernon Cole 2018

import sys, os, traceback, time, json
import warnings, subprocess

ELEVATION_FLAG = "--context"


def already_elevated():  # we-were-here flag has been set
    return any(arg.startswith(ELEVATION_FLAG) for arg in sys.argv)


def isUserAdmin():
    if already_elevated():
        return True
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


def runAsAdmin(commandLine=None, context=None, wait=True):
    if commandLine is None:
        python_exe = sys.executable
        cmdLine = [python_exe] + sys.argv  # run the present Python command with elevation.
    else:
        if not isinstance(commandLine, (tuple, list)):
            raise ValueError("commandLine is not a sequence.")
        cmdLine = list(commandLine)  # make a local copy

    if isinstance(context, dict):
        ctx = json.dumps(context)
        cmdLine.append("{}='{}'".format(ELEVATION_FLAG, ctx))
    elif context:
        cmdLine.append(ELEVATION_FLAG)

    if os.name == 'posix':
        cmd = "sudo " + ' '.join(cmdLine)
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
        cmd = '"{}"'.format(cmdLine[0])
        params = " ".join(['"{}"'.format(x) for x in cmdLine[1:]])
        lpVerb = 'runas'  # causes UAC elevation prompt.
        print()
        print("This window is waiting while a child window is run as an Administrator...")
        print("Running command-->{} {}".format(cmd, params))
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


def run_elevated(command=None, context=None):
    if not isUserAdmin():
        rc = runAsAdmin(command, context)
        time.sleep(3)
        sys.exit(rc)


def get_context():
    for arg in sys.argv:
        if arg.startswith(ELEVATION_FLAG):
            try:
                return json.loads(arg.split('=')[1])
            except (IndexError, json.JSONDecodeError) as e:
                print("Decode Error in Context=>{}".format(e))
                return {}
    return {}


def set_env_variables_permanently_win(key_value_pairs: dict, whole_machine: bool = False):
    """
    Similar to os.environ[var_name] = var_value for all pairs provided, but instead of setting the variables in the
    current process, sets the environment variables permanently at the os MACHINE level.

    Original Recipe from http://code.activestate.com/recipes/416087/
    :param key_value_pairs: a dictionary of variable name+value to set
    :param whole_machine: if True the env variables will be set at the MACHINE (HKLM) level.
           If False it will be done at USER level (HKCU)
    :return:
    """
    if not isinstance(key_value_pairs, dict):
        raise ValueError('{!r} must be {}'.format(key_value_pairs, dict))
    if os.name != 'nt':
        raise ModuleNotFoundError('Attempting Windows operation on non-Windows')

    import winreg
    import win32gui, win32con

    path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment' if whole_machine else r'Environment'

    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE if whole_machine else winreg.HKEY_CURRENT_USER,
                          path, 0,
                          #winreg.KEY_READ) as key:
                          winreg.KEY_ALL_ACCESS) as key:

        for name, value in key_value_pairs.items():
            print(name, '=', value)
            try:
                present, value_type = winreg.QueryValueEx(key, name)
            except OSError:
                present = NotImplemented
                value_type = winreg.REG_SZ
            print('{} = {}'.format(name, present))

            if name.upper() in ['PATH', 'PATHEXT']:
                if value.upper() in present.split(';'):  # these two keys will always be present and contain ";"
                    print('Value {} already in {}'.format(value, present))
                    continue
                else:
                    print('"{}" will not be entirely changed. "{}" will be appended at the end.'.format(
                        name, value))
                    value = '{};{}'.format(present, value)
            if value:
                print("Setting ENVIRONMENT VARIABLE '{}' to '{}'",format(name, value))
                winreg.SetValueEx(key, name, 0, value_type, value)
            else:
                print("Deleting ENV VARIABLE '{}'".format(name))
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass  # ignore if already deleted

    win32gui.SendMessageTimeout(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment',
                                win32con.SMTO_ABORTIFHUNG, 1000)


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
            print('....... NEXT, a real useful example ... editing the "etc/hosts" file ........')
            if os.name == 'nt':
                call = ["c:\\Windows\\notepad.exe", "C:\Windows\System32\drivers\etc\hosts"]
            else:
                call = ['nano', '/etc/hosts']
            test(call)
    elif "--install-sudo-command" in sys.argv and os.name == 'nt':
        print('Installing "sudo" command...')
        import shutil
        shutil.copy2(__file__, r'C:\Windows\sudo.py')
        set_env_variables_permanently_win({'PATHEXT': r'.PY'}, whole_machine=True)
    elif "--set-environment" in sys.argv and os.name == 'nt':
        ctx = get_context()
        set_env_variables_permanently_win(ctx, whole_machine=True)
    elif "--set-user-environment" in sys.argv and os.name == 'nt':
        ctx = get_context()
        set_env_variables_permanently_win(ctx, whole_machine=False)
    elif len(sys.argv) == 1:
        print('usage: sudo <command> <arguments>  # will run with elevated priviledges')
    else:
        run_elevated(sys.argv[1:])
