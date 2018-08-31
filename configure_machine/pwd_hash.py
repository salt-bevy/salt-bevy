#!/usr/bin/env python3
import os, getpass, sys
from pathlib import Path

try:
    import passlib.hash as ph  # must use passlib module on Mac OS or Windows systems.
    sha = ph.sha512_crypt
    import random
except ImportError:
    sha = None  # flag that passlib is not present
    import crypt  # will use built-in crypt (works okay on Linux)

HASHFILE_NAME = 'bevy_linux_password.hash'  # Salt scripts will expect this name

try:
    hashdir = Path.home() / '.ssh'  # only works on Python 3.5+
except AttributeError:  # older Python3
    hashdir = Path('/home/') / getpass.getuser() / '.ssh'
hashpath = hashdir / HASHFILE_NAME

def make_file():
    dashline = 78 * '-'
    print(dashline)
    print()
    print('This program will request a password, and send its Linux "Hash" to...')
    print(' {}'.format(hashpath))
    print()

    while True:
        pw1 = getpass.getpass()
        pw2 = getpass.getpass("And again: ")

        if pw1 != pw2:
            print("Passwords didn't match")
            continue
        else:
            if sha:  # is it installed?
                pwhash = sha.hash(pw1,
                                  salt=hex(random.getrandbits(64))[2:],
                                  rounds=5000)  # 5000 is magic, do not change
            else:  # no passlib module, use crypt
                pwhash = crypt.crypt(pw1)
            print('the hash is...')
            print(pwhash)
        if 0 < len(pwhash) < 32:
            print('Sorry: the crypt module is fully implemented only on Linux Python3.')
            print('  Your hash is too small to be SHA-2, meaning it will not work for a SaltStack user definition.')
            print('  You need to "pip3 install passlib" and rerun this program')
            sys.exit(1)
        if (input("Use this password hash? [Y/n]:") or 'y').lower().startswith('y'):
            break

    os.makedirs(str(hashdir), exist_ok=True)
    with hashpath.open('w') as pf:
        pf.write(pwhash + '\n')
    print('File {} written.'.format(hashpath))
    print(dashline)

if __name__ == "__main__":
    make_file()
