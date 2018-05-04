#!/usr/bin/env python3
"""
Execute a shell script after a delay time.
  arg[1] is delay time in seconds
  all following arguments are a command and its arguments.
  if " ; " appears as an argument, the command line will be split at that point and
  run as two (or more) separate commands.
  If a command is "echo", it will not be printed out (echoed) before being executed.
"""
#
from __future__ import print_function  # used to make PyCharm Python2 compatibility happy

import sys, subprocess, time
CHEAP_LOG_FILE = '/tmp/run_command_later.log'

args = sys.argv
if not sys.stdout.isatty():
    try:
        sys.stdout = open(CHEAP_LOG_FILE, 'w')  # cheap log output
        sys.stderr = sys.stdout
    except:
        pass
cmd = args.pop(0)
try:
    delay = float(args.pop(0))
    if not args:  # only an empty list remaining?
        raise ValueError
except (ValueError, IndexError):
    print('Usage: {} seconds_to_delay command and args to run'.format(cmd))
    sys.exit(1)
print('{} sleeping {} seconds...'.format(__file__, delay))
time.sleep(delay)

raw_command = ' '.join(args)
commands = raw_command.split(';')

print()
print('v - v - v - v - v - v - v - v - v - v - v - v - v - v - v - v')
print(time.asctime())
retcd = 0  # default to success indication
for command in commands:
    command = command.strip()
    if not command.startswith('echo'):
        print('{} is now running command-> "{}"'.format(__file__, command))
    sys.stdout.flush()
    try:
        # 3.5 sp = subprocess.run(command, shell=True, check=True, stdout=sys.stdout, stderr=subprocess.STDOUT)
        # 3.5 retcd = sp.returncode
        retcd = subprocess.call(command, shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT) # 3.4
        if retcd != 0:  #3.4
            print('ERROR: '
                'Command "{}" returned non-zero exit status "{}"'.format(command, retcd))  # 3.4
    except subprocess.CalledProcessError as e:
        print('* * * ERROR running command . . .')
        print('(try checking {} for details)'.format(CHEAP_LOG_FILE))
        print(e)
        retcd = e.returncode
        break  # stop running other commands, if a list
print('^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^ - ^')
print(' $ ', end='')  # a phony prompt for the user
sys.stdout.flush()
sys.exit(retcd)  # send the return code (from the called subprocess) to the shell
