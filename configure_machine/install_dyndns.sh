#!/bin/bash
# Dynamic DNS through RFC 2136 updates to fremont.2txt.us's PowerDNS, for a
# salt-bevy VM whose DHCP address changes. It replaces install_ddclient.sh,
# whose HE.net dyndns2 updates stopped working when 2tst.xyz moved to
# PowerDNS on fremont.
#
# Usage (as root): install_dyndns.sh <name> <zone> <key-name> <secret> [iface]
#   e.g. install_dyndns.sh salt24.7c.2tst.xyz 7c.2tst.xyz salt24.7c "$SECRET" eth0
#
# The key comes from `pdnsutil generate-tsig-key <host>.7c hmac-sha256` on
# fremont. fremont's update policy (7c-salt pillar dns:update_policy, subnets)
# lets it change only <host>.7c.2tst.xyz, so a leaked key can't touch other
# names. A friendlier name can CNAME to it (salt24.2tst.xyz -> salt24.7c...).
#
# It publishes one A record: the interface's IPv4 address (a lab address,
# meant for machines on the same networks). Updates go out at boot and every
# 15 minutes, but are only sent when the address changed or a day has passed.
# It is the same design as 7c-salt's dyndns-client state (which does IPv6 AAAA
# for oldpi). Safe to re-run: it rewrites its files and publishes right away.
set -euo pipefail

name=${1:?name}; zone=${2:?zone}; key_name=${3:?key name}; secret=${4:?secret}
iface=${5:-eth0}
server=fremont.2txt.us
ttl=300

if ! command -v nsupdate >/dev/null; then
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq bind9-dnsutils >/dev/null
fi

install -d -m 0700 /etc/dyndns
umask 077
cat > /etc/dyndns/tsig.key <<EOF
key "$key_name" {
    algorithm hmac-sha256;
    secret "$secret";
};
EOF
umask 022

cat > /usr/local/sbin/dyndns-update <<EOF
#!/bin/bash
# Written by salt-bevy configure_machine/install_dyndns.sh. Publishes this
# host's $iface IPv4 address as the A record of $name. --force always sends.
set -eu
state=/var/lib/dyndns/last
mkdir -p /var/lib/dyndns
addr=\$(ip -4 -o addr show dev $iface scope global 2>/dev/null | awk '{split(\$4, a, "/"); print a[1]}' | head -1 || true)
want=\${addr:-none}
if [ "\${1:-}" != --force ] && [ -n "\$(find "\$state" -mmin -1440 2>/dev/null)" ] \\
    && [ "\$(cat "\$state")" = "\$want" ]; then
    exit 0
fi
{
    echo "server $server"
    echo "zone $zone"
    echo "update delete $name. A"
    [ -n "\$addr" ] && echo "update add $name. $ttl A \$addr"
    echo "send"
} | nsupdate -4 -k /etc/dyndns/tsig.key
echo "\$want" > "\$state"
logger -t dyndns "$name A set to \$want"
EOF
chmod 0755 /usr/local/sbin/dyndns-update

cat > /etc/systemd/system/dyndns-update.service <<EOF
[Unit]
Description=Publish this host's IPv4 address as $name
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/dyndns-update
EOF

cat > /etc/systemd/system/dyndns-update.timer <<EOF
[Unit]
Description=Check this host's IPv4 address for $name every 15 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable -q --now dyndns-update.timer
/usr/local/sbin/dyndns-update --force
echo "dyndns: $name -> $(cat /var/lib/dyndns/last)"
