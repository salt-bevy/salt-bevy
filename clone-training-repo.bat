echo on
pushd ..
if not exist training goto clone_it
pushd training
git pull
popd
exit /b
clone_it:
git clone https://github.com/salt-bevy/training.git
popd
