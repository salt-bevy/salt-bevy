# Hurricane Electric dynamic DNS (dyndns2) update key for quail1 (not currently wired up
# to any Vagrantfile provisioner -- quail1 was abandoned before ddclient was ever added).
#
# quail22/salt22/bevymaster's keys were removed 2026-10-04: the 2tst.xyz zone moved to
# PowerDNS-primary-on-fremont on 2026-09-16, which silently broke HE.net dyndns2 updates
# for this zone, and all three of those VMs are inactive. Their DNS records were deleted
# outright from fremont's PowerDNS rather than fixed. See the "Dynamic DNS setup" project
# memory. If DNS is ever needed again for a salt-bevy host, add a record directly via
# fremont's PowerDNS/PowerDNS-Admin instead of reviving dyndns2 for this zone.
#
# Tracked in git (deliberately, by user decision 2026-08-26 -- these keys only let
# someone repoint a *.2tst.xyz DDNS record, low blast radius for this project). If that
# changes, rotate in the dns.he.net panel and update here.
ddns_key_quail1="94EOZsHIyfGRB1ga"
