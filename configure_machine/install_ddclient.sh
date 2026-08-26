#!/bin/bash -e
# Installs and configures ddclient to keep this host's A record at
# dns.he.net (HE's dyndns2 protocol) pointed at whatever address is
# currently on a given local interface -- these hosts publish their
# WireGuard-mesh address, not a public/WAN IP, since the "public_network"
# bridge in the salt-bevy Vagrantfile actually rides the WireGuard tunnel
# (see bevy pillar's vagrant_interface_guess: 'WireGuard Tunnel').
#
# No automatic Salt provisioning reaches quail1/quail22/salt22 (see the
# Vagrantfile comments on those machine blocks), so this is run by hand
# over ssh instead of as a state.
#
# Usage: sudo ./install_ddclient.sh <fqdn> <he-ddns-key> [iface]
if (( EUID != 0 )); then
  echo "run this with sudo" >&2
  exit 1
fi

FQDN="$1"
KEY="$2"
IFACE="${3:-eth0}"
if [ -z "$FQDN" ] || [ -z "$KEY" ]; then
  echo "usage: $0 <fqdn> <he-ddns-key> [iface]" >&2
  exit 1
fi

if ! dpkg -s ddclient >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y ddclient
fi

systemctl stop ddclient 2>/dev/null || true

cat > /etc/ddclient.conf <<EOF
daemon=300
syslog=yes
pid=/var/run/ddclient.pid
ssl=yes
use=if, if=$IFACE
protocol=dyndns2
server=dyn.dns.he.net
login=$FQDN
password='$KEY'
$FQDN
EOF
chmod 600 /etc/ddclient.conf

systemctl enable ddclient
systemctl restart ddclient
sleep 2
systemctl --no-pager --full status ddclient | head -20
