#!/bin/bash
SCRIPTPATH="$( cd "$(dirname "$0")/../salt-bevy" ; pwd -P )"
set -x
if [ ! -d $SCRIPTPATH ]; then
  pushd ..
  git clone https://github.com/salt-bevy/salt-bevy.git
  popd
fi
/usr/bin/env python3 $SCRIPTPATH/configure_machine/bootstrap_bevy_member_here.py "$@"
cp -n $SCRIPTPATH/vgr .
