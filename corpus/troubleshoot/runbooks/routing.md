# Routing troubleshooting decision tree

Tags: routing, gateway, static route, ospf, bgp, traceroute, asymmetric, rp_filter, ecmp

## Step 0 — localize with the halving test

```
ping <default-gw>        # my own L2/L3 config?
ping <far-router>        # path through the core?
ping <destination>       # end to end?
traceroute -n <dest>     # Linux (UDP by default; -I for ICMP, -T -p 443 for TCP)
tracert -d <dest>        # Windows (ICMP)
traceroute <dest>        # IOS
```
The first silent hop marks the failure zone. `!H`/`!N` (unreachable) beats `* * *` (filtered/ratelimited) for information. Remember: routers deprioritize ICMP *to themselves* — mid-path `* * *` with a working final hop is normal.

## Step 1 — what route is actually being used?

| OS | Command |
|---|---|
| Linux | `ip route get <dest>` ← answers "which route/iface/src IP for THIS packet" |
| Linux table | `ip route show` (+ `ip rule show` for policy routing!) |
| Windows | `Find-NetRoute -RemoteIPAddress <dest>` · `route print` |
| IOS | `show ip route <dest>` · `show ip cef <dest>` (what's actually programmed) |

Checks, in order:
1. **Is there a route at all?** No default (`0.0.0.0/0`) and no specific → local host problem.
2. **Longest prefix match surprise**: a stale /32 or /24 beats the default. `ip route get` / `show ip route <dest>` reveals it.
3. **Two defaults / wrong metric**: `ip route show default` — VPN clients often inject a second default. Windows: `Get-NetRoute -DestinationPrefix 0.0.0.0/0` + InterfaceMetric.
4. **Policy routing (Linux)**: `ip rule show` — a rule can send traffic to another table entirely (`ip route show table <n>`). WireGuard/VPNs use this heavily.
5. **Source address matters**: `ip route get <dest> from <src>` — replies use the *reply* route. See asymmetry §3.

## Step 2 — next hop resolvable?

Route exists but next hop dead:
- `ip neigh show <gw>` — `FAILED`/`INCOMPLETE` = ARP failing = L2 problem (VLAN/cable), not routing.
- IOS: `show arp | include <gw>`; recursive routes: `show ip route <next-hop>` must itself resolve.

## Step 3 — asymmetric / return-path problems (the classic "ping works one way")

Forward path fine; replies leave via a different interface/provider and get dropped:
- Linux `rp_filter` drops packets whose reply route differs from the arrival interface: `sysctl net.ipv4.conf.all.rp_filter` — set to `2` (loose) or `0` on multi-homed boxes.
- Firewalls drop the reply because they never saw the SYN (state missing). Evidence: `tcpdump` on both interfaces of the middle box; conntrack: `conntrack -L | grep <ip>`.
- Fix pattern (Linux, two uplinks): policy routing — mark or `from <ip>` rules so replies leave the interface they arrived on:
```
ip rule add from 203.0.113.5 table 100
ip route add default via 203.0.113.1 dev eth1 table 100
```

## Step 4 — dynamic routing protocol issues

### OSPF (IOS)
```
show ip ospf neighbor          # want FULL (or 2WAY on DROTHER pairs)
show ip ospf interface brief   # right interfaces in right areas?
show ip route ospf
```
Neighbor stuck in:
- (nothing listed): hello not arriving — L2, ACL blocking proto 89, `passive-interface`, area/subnet mismatch.
- `INIT`: your hellos not received back — one-way (ACL/unicast filter).
- `EXSTART/EXCHANGE`: **MTU mismatch** — `show run interface`, fix or `ip ospf mtu-ignore`.
- `2WAY` on point-to-point: DR election confusion — set `ip ospf network point-to-point` both ends.
Must match on both sides: area id, hello/dead timers, subnet/mask, authentication, stub flags. Check fast: `debug ip ospf adj` (careful in prod).

### BGP (IOS)
```
show ip bgp summary            # neighbor state; want Established
show ip bgp neighbors <ip>     # last error notification
show ip bgp <prefix>           # do we have the route? why not best?
```
- `Idle` — no route to neighbor or config error.
- `Active` — TCP/179 not connecting: reachability, ACL, wrong `update-source`/neighbor IP, TTL (eBGP default 1 hop: need `ebgp-multihop` for loopback peering).
- Established but no routes: filters (`show ip bgp neighbors <ip> received-routes` needs soft-reconfig), missing `network` statement, or next-hop unreachable (`show ip bgp` — next hop must resolve; iBGP often needs `next-hop-self`).

### FRR (Linux) equivalents
`vtysh -c 'show ip ospf neighbor'`, `show bgp summary`, config in `/etc/frr/frr.conf`, daemons in `/etc/frr/daemons`. Kernel gets routes via zebra: confirm with `ip route show proto ospf|bgp`.

## Step 5 — forwarding through a Linux box fails

Box receives but won't forward:
```
sysctl net.ipv4.ip_forward          # must be 1
nft list ruleset | grep -i forward  # FORWARD chain policy drop?
```
Both directions must be allowed in FORWARD, plus NAT if crossing to a public net (see nat-firewall runbook).

## Step 6 — intermittent / weird

- **ECMP flapping**: two equal routes, per-flow hashing — some flows work, others don't (one path broken). `ip route show` multiple nexthops; IOS `show ip cef <dest> detail` shows both paths.
- **Route flapping**: `show ip route <dest>` age keeps resetting; check interface flaps (`show interface | include line protocol|flapped`) and protocol logs (`show logging | include OSPF|BGP`).
- **TTL exceeded loops**: traceroute shows the same pair of hops repeating = routing loop — usually a static default pointing back at the other router.
- **New subnet unreachable from elsewhere**: the *return* route is missing on the remote/core router — routes must exist in BOTH directions; redistribute or add the static on the far side.
