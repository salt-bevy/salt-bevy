#!/usr/bin/env bash -x

if ! command -v salt-call >/dev/null 2>&1; then
  ./macos_install_P3_and_salt.sh
fi
brew cask install vagrant;
brew cask install virtualbox;
