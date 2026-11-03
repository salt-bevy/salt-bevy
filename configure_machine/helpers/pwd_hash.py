#!/usr/bin/env python3
import getpass, sys

try:
    import passlib.hash as ph  # use passlib wherever it is installed
    sha = ph.sha512_crypt.using(rounds=5000)  # 5000 is magic, do not change
except ImportError:
    sha = None  # flag that passlib is not present
    try:
        import crypt  # built in on Linux, but removed in Python 3.13
    except ImportError:
        raise ImportError('Password hashing needs the passlib module. Try "pip3 install passlib".')


def make_hash():
    dashline = 78 * '-'
    print(dashline)
    print()
    print('This program will request a password, and return its hash string.')
    print()

    while True:
        pw1 = getpass.getpass()
        pw2 = getpass.getpass("And again: ")

        if pw1 != pw2:
            print("Passwords didn't match")
            continue
        else:
            if sha:  # is passlib installed?
                pwhash = sha.hash(pw1)  # passlib generates the salt
            else:  # no passlib module, use crypt
                pwhash = crypt.crypt(pw1)
            print('the hash is...')
            print(pwhash)
        if 0 < len(pwhash) < 32:
            print('Sorry: the crypt module is fully implemented only on Linux Python 3.')
            print('  This hash is too small to be SHA-2, meaning it will not work for a SaltStack user definition.')
            print('  You need to "pip3 install passlib" and/or rerun this program using Python 3.')
            sys.exit(1)
        if (input("Use this password hash? [Y/n]:") or 'y').lower().startswith('y'):
            break
    print(dashline)
    return pwhash

if __name__ == "__main__":
    print('{"hash": "%s"}' % make_hash())  # output JSON, just in case we may want that someday.
