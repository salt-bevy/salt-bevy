#!/usr/bin/env bash -x
chflags nohidden /etc
chflags nohidden /var
chflags nohidden /tmp
mkdir -p /etc/salt/minion.d
chown -R vagrant:staff /etc/salt
chmod 775 /etc/salt/minion.d
