#!/bin/bash -x
# Salt (masterless) reads its states/pillar from /srv/salt and /srv/pillar
# (see minion file_roots/pillar_roots), but the palmtree/django app repo
# carries its own checked-in copy of the django.* states and pillar under
# /opt/palmtree/srv, which git.latest updates on every highstate. Without
# this copy, /srv/salt and /srv/pillar/django.sls stay frozen at whatever
# they were the first time this VM was bootstrapped, even though the repo
# (and /opt/palmtree) keeps moving. Refresh them from the repo's checked-in
# copy before Salt runs, so a new highstate sees this run's states/pillar,
# not last run's.
if [ -d /opt/palmtree/srv/salt ]; then
  cp -a /opt/palmtree/srv/salt/. /srv/salt/
fi
if [ -f /opt/palmtree/srv/pillar/django.sls ]; then
  cp -a /opt/palmtree/srv/pillar/django.sls /srv/pillar/django.sls
fi
