#!/usr/bin/env python3
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4

# (C) COPYRIGHT © Preston Landers 2010
# Released under the same license as Python 2.6.5
#
# Python3 update and extensive changes by: Vernon Cole 2018, 2019

import sys, os, traceback, time, json, subprocess

ELEVATION_FLAG = "--_context"  # internal use only. Should never be passed on a user command line


def has_context():  # we-were-here flag has been set
    '''
    Do command line arguments include one beginning with "--_context"?
    :return: bool, context flag was present in argv
    '''
    return any(arg.startswith(ELEVATION_FLAG) for arg in sys.argv)


def isUserAdmin():
    '''
    Checks for "--_context" argument or OS opinion of whether current process is elevated
    :return: bool, process has administrator privileges.
    '''
    if has_context():
        return True
    if os.name == 'nt':
        from win32com.shell import shell
        try:
            return shell.IsUserAnAdmin()
        except Exception as e:
            traceback.print_exc()
            print("Admin check failed, assuming not an admin.")
            return False
    elif os.name == 'posix':
        # Check for root on Posix
        return os.getuid() == 0
    else:
        raise RuntimeError("Unsupported operating system for this module: {}".format(os.name))


def runAsAdmin(commandLine=None, context=None, python_shell=False, wait=True):
    '''
    Run a command with elevated system privileges.

    :param commandLine: str . a string, or sequence of strings, of the command line
    :param context: dic or bool. additional context to pass to the elevated program. Adds CLI argument "--_context={}"
    :param python_shell: bool, the command is a Python script.
    :param wait: bool, wait for command completion. If False, will run the command asynchronously.
    :return: int, the return code from the execution. Will be None for async, 89 for some Windows error conditions.
    '''
    try:
        # noinspection PyUnresolvedReferences
        from helpers.argv_quote import quote
    except (ModuleNotFoundError, ImportError):
        from argv_quote import quote

    if commandLine is None:
        cmdLine = []
    elif isinstance(commandLine, str):
        cmdLine = commandLine.split()
    else:
        if not isinstance(commandLine, (tuple, list)):
            raise ValueError("commandLine must be a sequence or a string.")
        cmdLine = list(commandLine)  # make a local copy

    if python_shell:
        python_exe = sys.executable  # the path to the running Python image file
        cmdLine.insert(0, python_exe)  # run the Python command with elevation.

    if isinstance(context, dict):
        ctx = json.dumps(context)
        cmdLine.append(ELEVATION_FLAG + "=" + ctx)
    elif context:
        cmdLine.append(ELEVATION_FLAG)

    if os.name == 'posix':
        cmdLine.insert(0, "sudo")  # make a call using the system's "sudo"
        cmd = quote(*cmdLine)
        print('(Running command-->', cmd, ')')
        return_code = subprocess.call(cmd, shell=True)

    elif os.name == 'nt':  # running Windows -- must use pywin32 to ask for elevation
        try:
            # noinspection PyUnresolvedReferences
            import win32con, win32event, win32process
        except ImportError:
            raise ImportError('PyWin32 module has not been installed.')
        # noinspection PyUnresolvedReferences
        from win32com.shell.shell import ShellExecuteEx
        # noinspection PyUnresolvedReferences
        from win32com.shell import shellcon

        showCmd = win32con.SW_SHOWNORMAL
        try:
            params = quote(*cmdLine[1:])
        except IndexError:
            params = ""
        try:
            cmd = quote(cmdLine[0])
        except IndexError:
            cmd = "_No_command_was_supplied_"
        lpVerb = 'runas'  # causes UAC elevation prompt.
        print()
        print("This window will be waiting while a child window is run as an Administrator...")
        print("(Running command-->{} {})".format(cmd, params))
        procInfo = ShellExecuteEx(nShow=showCmd,
                                  fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                  lpVerb=lpVerb,
                                  lpParameters=params,
                                  lpFile=cmd)
        if wait:
            procHandle = procInfo['hProcess']
            if procHandle is None:
                print("Windows Process Handle is Null. RunAsAdmin did not create a child process.")
                return_code = 89
            else:
                win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
                return_code = win32process.GetExitCodeProcess(procHandle)
                # print("Process handle %s returned code %s" % (procHandle, return_code))
                procHandle.Close()
        else:
            return_code = None  # asked not to wait for completion
    else:
        raise RuntimeError("Unsupported operating system for this module: {}".format(os.name))
    return return_code

def get_context():
    '''
    parse and return json dictionary from the --_context argument.
    :return: dic
    '''
    for arg in sys.argv:
        if arg.startswith(ELEVATION_FLAG):
            try:
                ret = json.loads(arg.split('=')[1])
                return ret
            except (IndexError, json.JSONDecodeError) as e:
                print("Decode Error in Context=>{}".format(e))
                print("sys.argv-->", sys.argv)
                return {}
    return {}


def set_env_variables_permanently_win(key_value_pairs, whole_machine = False):
    """
    Similar to os.environ[var_name] = var_value for all pairs provided, but instead of setting the variables in the
    current process, sets the environment variables permanently at the os MACHINE level.
    NOTE:  process must be "elevated" before making this call.  Use "sudo" first.

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

    # noinspection PyUnresolvedReferences
    import winreg, win32gui, win32con

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

    # tell all the world that a change has been made
    win32gui.SendMessageTimeout(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment',
                                win32con.SMTO_ABORTIFHUNG, 1000)


def test(command=None):
    try:
        if isinstance(command, str):
            command = command.split()
        if "--test" in command:
            command.remove("--test")
    except TypeError:
        pass
    if not isUserAdmin():
        print("You're not an admin. You are running PID={} with command-->{}".format(os.getpid(), command))
        if command is not None:
            return_code = runAsAdmin(command[1:])
    else:
        print("You ARE an admin. You are running PID={} with command-->{}".format(os.getpid(), command))
        if command is not None and len(command) > 1:
            import subprocess
            import argv_quote
            return_code = subprocess.call(argv_quote.quote(*command[1:]), shell=True)
        else:
            return_code = 0
        time.sleep(2)
        input('Press Enter to exit.')
    return return_code


if __name__ == "__main__":
    if '--pause' in sys.argv:
        if isUserAdmin():
            input('. . . This window is running "sudo --pause". . . Press <enter> to exit:')
    elif "--test" in sys.argv:
        print('......testing.......')
        test(sys.argv)
        if not isUserAdmin():
            print('....... NEXT, a real useful example ... editing the "etc/hosts" file ........')
            if os.name == 'nt':
                call = ["c:\\Windows\\notepad.exe", r"C:\Windows\System32\drivers\etc\hosts"]
            else:
                call = ['nano', '/etc/hosts']
            test(call)
    elif "--install-sudo-command" in sys.argv and os.name == 'nt':
        print('Installing "sudo" command...')
        if isUserAdmin():
            import shutil
            shutil.copy2(__file__, r'C:\Windows\sudo.py')
            shutil.copy2(os.path.dirname(os.path.abspath(__file__)) + r'\argv_quote.py',
                                         r'C:\Windows\argv_quote.py')
            set_env_variables_permanently_win({'PATHEXT': r'.PY'}, whole_machine=True)
        else:
            runAsAdmin([os.path.abspath(__file__), '--install-sudo-command'], python_shell=True)
    elif "--set-environment" in sys.argv and os.name == 'nt':
        ctx = get_context()
        set_env_variables_permanently_win(ctx, whole_machine=True)
    elif "--set-user-environment" in sys.argv and os.name == 'nt':
        ctx = get_context()
        set_env_variables_permanently_win(ctx, whole_machine=False)
    elif len(sys.argv) == 1:
        print('usage: sudo <command> <arguments>  # will run with elevated priviledges')
    else:
        runAsAdmin(sys.argv[1:])
