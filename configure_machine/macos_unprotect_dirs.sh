#!/usr/bin/env bash -x
chflags nohidden /etc
chflags nohidden /var
chflags nohidden /tmp
mkdir -p /etc/salt/minion.d
chown -R vagrant:staff /etc/salt
chmod 775 /etc/salt/minion.d
mkdir -p /srv/pillar
chown -R vagrant:staff /srv/pillar
chmod 775 /srv/pillar
mkdir -p /srv/salt
chown -R vagrant:staff /srv/salt
chmod 775 /srv/salt
