#!/usr/bin/env bash -x
chflags nohidden /etc
chflags nohidden /var
chflags nohidden /tmp
mkdir -p /etc/salt/minion.d
chown -R vagrant:staff /etc/salt
chmod 775 /etc/salt/minion.d
mkdir -p /opt/saltdata/pillar
chown -R vagrant:staff /opt/saltdata/pillar
chmod 775 /opt/saltdata/pillar
mkdir -p /opt/saltdata/salt
chown -R vagrant:staff /opt/saltdata/salt
chmod 775 /opt/saltdata/salt
