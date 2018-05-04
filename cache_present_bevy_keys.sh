#!/usr/bin/env bash
# run on bevy_master to preserve the state of the bevy for future bevy masters
mkdir /vagrant/bevy_srv/salt/pki_cache
sudo cp -r -v /etc/salt/pki /vagrant/bevy_srv/salt/pki_cache
