#!/usr/bin/env bash -x
# -- MacOS will not, in its infinite wisdom, allow me to install the xcode tools as "root"
# -- by running "xcode-select --install" without clicking on a GUI window,
# -- but the HomeBrew bootstrapper _can_ install them.
# -- so we will install brew, which will do what we actually need as a side-effect.
# -- vernondcole
#
if ! type "brew" > /dev/null; then
  ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)";
fi
