# NAT & firewall troubleshooting

Tags: nat, firewall, nftables, iptables, port forward, conntrack, windows firewall, acl, asa

## Step 0 — is a firewall even the problem?

Refused (RST) vs timeout (silent drop): `nc -zv host port`. REJECT rules and closed ports both give "refused"; DROP gives timeout. Prove packets on the wire at each hop with `tcpdump` — that's the only ground truth.

## §1 Linux nftables / iptables

```
nft list ruleset                      # everything (nftables)
iptables -L -n -v --line-numbers      # legacy/compat; -v = HIT COUNTERS
iptables -t nat -L -n -v
```
**Use the hit counters**: reproduce the failure, re-run with `-v`, see which DROP counter increments. nftables equivalent: add `counter` to suspect rules or `nft monitor trace` + a rule with `meta nftrace set 1`.

Common gotchas:
- Rule order: first match wins — your ACCEPT sits *below* a broad DROP.
- INPUT vs FORWARD: traffic *through* the box needs FORWARD (+ `sysctl net.ipv4.ip_forward=1`); to the box = INPUT.
- Established-only ruleset without `ct state established,related accept` breaks replies.
- Docker/libvirt insert their own chains ahead of yours (`DOCKER-USER` is where your through-traffic rules must go).
- firewalld on RHEL wraps nftables: `firewall-cmd --list-all`, add with `--add-service`/`--add-port` not raw nft.
- ufw on Ubuntu: `ufw status verbose`.

## §2 Windows Firewall

```
Get-NetFirewallProfile | Select Name, Enabled          # which profile is active?
Get-NetConnectionProfile                               # is this NIC Public or Private?!
Test-NetConnection <host> -Port 445
Get-NetFirewallRule -Enabled True -Direction Inbound | where DisplayName -like '*<app>*'
```
Classic: NIC classified **Public** so all the Private-profile allow rules don't apply. Fix: `Set-NetConnectionProfile -InterfaceAlias Ethernet -NetworkCategory Private`.
Log drops: `Set-NetFirewallProfile -LogBlocked True` → `%systemroot%\system32\LogFiles\Firewall\pfirewall.log`.
Remote mgmt quickies: `Enable-PSRemoting`, `winrm quickconfig`, File+Print sharing rule group for ping/SMB.
Windows blocks **inbound ICMP echo by default** — "can't ping a Windows box" is usually policy not connectivity:
`New-NetFirewallRule -DisplayName 'Allow ICMPv4-In' -Protocol ICMPv4 -IcmpType 8 -Direction Inbound -Action Allow`

## §3 Cisco IOS ACLs

```
show access-lists                 # HIT COUNTS per line
show run | include access-group   # which ACL on which interface/direction
```
- Implicit `deny any` at the end of every ACL — no match = drop, and it's invisible.
- Direction matters: `in` = arriving at the interface; most mistakes are applying the right ACL in the wrong direction.
- Log a deny to see victims: `deny ip any any log` (last line, temporarily).
- ACL edits: named ACLs allow line numbers (`ip access-list extended X` → `15 permit ...`); numbered ACLs must be rebuilt.

## §4 NAT — outbound (masquerade/overload) broken

Symptom: LAN can't reach internet; router itself can.
```
# IOS
show ip nat translations
show ip nat statistics            # hits/misses, which interfaces are inside/outside
```
IOS checklist: `ip nat inside` on LAN iface, `ip nat outside` on WAN iface, ACL matching inside sources, `ip nat inside source list <acl> interface <wan> overload`. No translations appearing = ACL doesn't match or inside/outside marks missing.
```
# Linux (nftables)
nft list table nat                # masquerade rule present, right oifname?
conntrack -L | head               # live translations
```
Linux checklist: `ip_forward=1`, `masquerade` in postrouting chain for the WAN interface, FORWARD chain allows LAN→WAN + established back.

## §5 NAT — port forward (DNAT) not working

Test **from outside** (from inside, hairpin NAT usually isn't configured — that's expected, not broken!).
Trace the chain:
1. Does the WAN see the SYN? `tcpdump -ni <wan> port <p>`.
2. DNAT rule translating? IOS: `ip nat inside source static tcp <inside-ip> 80 interface <wan> 80`, verify in `show ip nat translations`. Linux: `dnat to <inside>:80` in prerouting; conntrack shows the mapped tuple.
3. Does the inside host see it? `tcpdump` on the target host.
4. Does the target host's OWN firewall allow it (source will be the outside IP, not the router).
5. **Return path**: target's default gateway must be the NAT router, or replies escape un-NATted and get RST.
6. Also FORWARD chain must permit WAN→inside for the DNATted flow (Linux).

## §6 Conntrack quirks

- Table full: `dmesg | grep conntrack` ("table full, dropping packet") → raise `net.netfilter.nf_conntrack_max`.
- Stale entry after changing NAT/routes: `conntrack -D -d <ip>` to flush that peer.
- Long-lived idle flows dropped: state timeout < app keepalive — enable app-level keepalives or raise `nf_conntrack_tcp_timeout_established`.

## §7 ASA one-liners (if one's in the path)

```
show conn address <ip>                 # is a connection built?
packet-tracer input inside tcp <src> 12345 <dst> 443    # SIMULATES the whole path: ACL, NAT, routes — says exactly what drops it
show logging | include <ip>
```
`packet-tracer` is the single best firewall-debug command Cisco ships — use it before anything else on ASA/FTD.

## §8 "It's slow, not blocked" — think inspection

IPS/UTM/proxy in path: TLS handshake completes but throughput dies, or specific sites break → try bypassing inspection for a test host; check firewall CPU (`show processes cpu` / device dashboard). Also see MTU (methodology runbook) — VPN + firewall + "some sites hang" ≈ PMTUD blackhole.
