#!/usr/bin/env python
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4

# (C) COPYRIGHT © Preston Landers 2010
# Released under the same license as Python 2.6.5
#
# Python3 update and extensive changes by: Vernon Cole 2018, 2019, 2020

import sys, os, traceback, time, subprocess, shutil

if os.name == 'nt':
    try:
        # noinspection PyUnresolvedReferences
        import winreg, win32gui, win32con, win32event, win32process
        # noinspection PyUnresolvedReferences
        from win32com.shell import shell, shellcon
        # noinspection PyUnresolvedReferences
        from win32com.shell.shell import ShellExecuteEx
    except ImportError:
        raise ImportError('PyWin32 module import failure.  Try "py -m pip install pywin32 pyyaml".')

try:
    # noinspection PyUnresolvedReferences
    from helpers.argv_quote import quote
except (ModuleNotFoundError, ImportError):
    # noinspection PyUnresolvedReferences
    from argv_quote import quote

try:
    # noinspection PyUnresolvedReferences
    import yaml as decoder
    def loader(s):
        return decoder.load(s, decoder.Loader)
    encoder = decoder.dump
    decodeError = decoder.YAMLError
except (ModuleNotFoundError, ImportError):
    # noinspection PyUnresolvedReferences
    import json as decoder
    loader = decoder.loads
    encoder = decoder.dumps
    decodeError = decoder.JSONDecodeError
    print('NOTE: no YAML module found, falling back to JSON. Try "pip install pyyaml".')

VERSION = 1.6

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
        ctx = encoder(context)
        cmdLine.append(ELEVATION_FLAG + "=" + ctx)
    elif context:
        cmdLine.append(ELEVATION_FLAG)

    if os.name == 'posix':
        cmdLine.insert(0, "sudo")  # make a call using the system's "sudo"
        cmd = quote(*cmdLine)
        print('(Running command-->', cmd, ')')
        return_code = subprocess.call(cmd, shell=True)

    elif os.name == 'nt':  # running Windows -- must use pywin32 to ask for elevation
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
        if wait:
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
                return_code = 89  # Windows ERROR_NO_PROC_SLOTS
            else:
                win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
                return_code = win32process.GetExitCodeProcess(procHandle)
                # print("Process handle %s returned code %s" % (procHandle, return_code))
                procHandle.Close()
                print("(Now Returned from waiting...)")
        else:
            return_code = None  # asked not to wait for completion
    else:
        raise RuntimeError("Unsupported operating system for this module: {}".format(os.name))
    return return_code


def get_context(flag=ELEVATION_FLAG):
    '''
    parse and return json dictionary from the --_context= argument.
    :return: dic
    '''
    for arg in sys.argv:
        if arg.startswith(flag):
            try:
                ctx = arg.split('=')[1]
                if not ctx.startswith('{'):
                    ctx = '{' + ctx
                if not ctx.endswith('}'):
                    ctx += '}'
                ret = loader(ctx)
                return ret
            except (IndexError, decodeError) as e:
                print("Decode Error in {}=>{}".format(flag, e))
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

    subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment' if whole_machine \
        else r'Environment'

    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE if whole_machine else winreg.HKEY_CURRENT_USER,
                          subkey, 0, winreg.KEY_ALL_ACCESS) as key:
        for name, value in key_value_pairs.items():
            try:
                if value.lower() == "none":
                    value = None
            except AttributeError:
                pass
            print('  setting environment variable -->', name, '=', value)
            try:
                present, value_type = winreg.QueryValueEx(key, name)
            except OSError:
                present = ''
                value_type = winreg.REG_SZ if isinstance(value, str) else \
                    winreg.REG_BINARY if isinstance(value, bool) else winreg.REG_DWORD
            print('old value was {} = {}'.format(name, present))
            if name.upper() in ['PATH', 'PATHEXT']:
                elements = present.upper().split(';')
                case_elements = present.split(';')
                if value.startswith('-'):  # remove a path element
                    value = value[1:]  # remove the '-'
                    try:
                        indx = elements.index(value.upper())
                        removed = case_elements.pop(indx)
                        print('Removing "{}" from {}'.format(removed, name))
                    except ValueError:
                        print('Element "{}" was not found in {}'.format(value, name))
                        continue
                else:  # adding a path element
                    if value.upper() in elements:
                        print('Value {} already in {}'.format(value, present))
                        continue
                    else:
                        print('"{}" will not be entirely changed. "{}" will be appended at the end.'.format(
                            name, value))
                        case_elements.append(value)
                value = ';'.join(case_elements)
            if value is not None:
                print("Setting ENVIRONMENT VARIABLE '{}' to '{}'".format(name, value))
                winreg.SetValueEx(key, name, 0, value_type, value)
            else:
                try:
                    winreg.DeleteValue(key, name)
                    print("Deleting ENV VARIABLE '{}'".format(name))
                except FileNotFoundError:
                    print("ENV VARIABLE '{}' was not present".format(name))

    # tell all the world that a change has been made
    win32gui.SendMessageTimeout(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment',
                                win32con.SMTO_ABORTIFHUNG, 1000)
    if has_context():
        input('Hit <Enter> to continue . . .')


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
            # noinspection PyUnresolvedReferences
            return_code = subprocess.call(quote(*command[1:]), shell=True)
        else:
            return_code = 0
        time.sleep(2)
        input('Press Enter to exit.')
    return return_code


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] in ["--help", "-h", "su", "/?", "/help"]:
        print('''usage:
         sudo <command> <arguments> # will run <command> with elevated priviledges
         sudo --pause <cmd> <args>  # will keep the command screen open until you hit a key
         sudo salt-xxx <cmd> . . .  # will call a command from C:\Salt\salt-xxx and then pause
         sudo --set-user-env="'arg1': 'val1','arg2': 'val2'" # adds values to the user's PERMANENT environment vars
         sudo --set-system-env="arg1: val1, arg2: val2" # adds values to the system's PERMANENT environment vars
         sudo --hosts  # will open your /etc/hosts file for editing (at the weird Windows location)
         sudo --install-sudo-command  # create a runnable copy of itself in C:\Windows
         sudo bash # starts an Administrator Linux-Subsystem-for-Windows window
         sudo cmd  # starts an Administrator command window
         ''')
    elif sys.argv[1] == "--version":
        print('sudo version', VERSION)
    elif sys.argv[1] == "--test":
        print('......testing.......')
        test(sys.argv)
    elif sys.argv[1] == "--hosts":
        print('....... NEXT, a useful example ... editing the "etc/hosts" file ........')
        if os.name == 'nt':
            call = ["notepad", r"C:\Windows\System32\drivers\etc\hosts"]
        else:
            call = ['nano', '/etc/hosts']
        runAsAdmin(call)
    elif sys.argv[1] == "--install-sudo-command" and os.name == 'nt':
        WINDOWS_PATH = r'C:\Windows\sudo.py'
        print('Installing "sudo" command...')
        if isUserAdmin():
            shutil.copy2(__file__, WINDOWS_PATH)
            shutil.copy2(os.path.dirname(os.path.abspath(__file__)) + r'\argv_quote.py',
                         os.path.dirname(WINDOWS_PATH) + r'\argv_quote.py')
            shutil.copy2(os.path.dirname(os.path.abspath(__file__)) + r'\sudo_pause.bat',
                         os.path.dirname(WINDOWS_PATH) + r'\sudo_pause.bat')
            shutil.copy2(os.path.dirname(os.path.abspath(__file__)) + r'\sudo_cd.bat',
                         os.path.dirname(WINDOWS_PATH) + r'\sudo_cd.bat')
            set_env_variables_permanently_win({'PATHEXT': '.PY'}, whole_machine=True)
            time.sleep(5)
        else:
            runAsAdmin([os.path.abspath(__file__), '--install-sudo-command'], python_shell=True)
    elif any([arg.startswith("--set-system-env") for arg in sys.argv]) and os.name == 'nt':
        if isUserAdmin():
            ctx = get_context("--set-system-env")
            set_env_variables_permanently_win(ctx, whole_machine=True)
            time.sleep(5)
        else:
            runAsAdmin([os.path.abspath(__file__)] + sys.argv[1:], None, python_shell=True)
    elif any([arg.startswith("--set-user-env") for arg in sys.argv]) and os.name == 'nt':
        ctx = get_context("--set-user-env")
        set_env_variables_permanently_win(ctx, whole_machine=False)
    else:  # normal operation
        if sys.argv[1].startswith('salt-'):  # make "sudo salt-call" automatically pause
            sys.argv.insert(1, '--pause')

        if sys.argv[1] == '--pause':
            sys.argv[1] = 'sudo_pause.bat'
        else:
            sys.argv.insert(1, 'sudo_cd.bat')
        cwd = os.getcwd()
        sys.argv.insert(2, cwd)
        runAsAdmin(sys.argv[1:])
