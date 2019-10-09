#!/usr/bin/env bash
set -x
pushd ..
if [ -d training/ ]; then
pushd training
git pull
popd
else
git clone https://github.com/salt-bevy/training.git
fi
popd
