#!/usr/bin/env bash -x
if ! command -v python3 >/dev/null 2>&1; then
  curl -sLo /srv/salt/python3.pkg https://www.python.org/ftp/python/3.6.8/python-3.6.8-macosx10.9.pkg
  installer -pkg /srv/salt/python3.pkg -target /
fi
# thanks to gtmanfred for this automatic Salt installation script.
if ! command -v salt-call >/dev/null 2>&1; then
  export SALT_VERSION="$(curl -sL https://pypi.python.org/pypi/salt/json | python -c "import sys, json; print('.'.join(sorted([x.split('.') for x in list(json.load(sys.stdin)['releases'])])[-1]))")"
  curl -sLo /srv/salt/salt.pkg "https://repo.saltstack.com/osx/salt-$SALT_VERSION-py3-x86_64.pkg"
  installer -pkg /srv/salt/salt.pkg -target /
fi
