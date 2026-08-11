#!/bin/bash -x
# Vagrant's file provisioner (run just before this) drops the host's /srv/pillar
# tree at /tmp/host_pillar, owned by the ssh user. Move it into place as root.
mkdir -p /srv/pillar
cp -a /tmp/host_pillar/. /srv/pillar/
chown -R vagrant:staff /srv/pillar
chmod -R 775 /srv/pillar
rm -rf /tmp/host_pillar
