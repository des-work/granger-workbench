# Interface / link-layer (L1-L2) troubleshooting

Tags: interface down, link, ethernet, vlan, trunk, speed duplex, arp, mac, spanning-tree, err-disable

## Step 0 — interface state

| OS | Command | Healthy looks like |
|---|---|---|
| Linux | `ip -br link` · `ethtool eth0` | `UP` · `Link detected: yes`, right `Speed/Duplex` |
| Windows | `Get-NetAdapter` | Status `Up`, expected LinkSpeed |
| IOS | `show interfaces status` · `show interfaces Gi0/1` | `connected` · `GigabitEthernet0/1 is up, line protocol is up` |

IOS state decode:
- `down/down` — physical: cable, SFP, far end off, wrong port.
- `up/down` — L1 ok, L2 not: protocol/encap mismatch (trunk vs access, keepalive), or err-disable on far side.
- `administratively down` — `no shutdown` it.
- Linux `NO-CARRIER` = cable/far-end; `state DOWN` without NO-CARRIER = `ip link set eth0 up`.

## §1 err-disabled ports (IOS)

```
show interfaces status err-disabled
show errdisable recovery
```
Causes: port-security violation, BPDU guard (someone plugged a switch), link-flap. Fix cause, then `shutdown` / `no shutdown` the port. Auto-recovery: `errdisable recovery cause <x>`, `errdisable recovery interval 300`.
Port security state: `show port-security interface Gi0/1` (violation count, sticky MAC that moved?).

## §2 Speed/duplex mismatch (slow + errory, not down)

Symptom: link up but throughput terrible, late collisions/CRC errors climbing.
```
# Linux
ethtool eth0                       # Speed: 100Mb/s Half = red flag on gig gear
ip -s link show eth0               # errors/dropped counters
# IOS
show interfaces Gi0/1 | include duplex|errors|collisions
```
Rule: **auto both ends or hard-set both ends** — one side auto + one side forced = duplex mismatch (the auto side falls back to half). Fix: `ethtool -s eth0 speed 1000 duplex full autoneg on` / IOS `speed auto`, `duplex auto`. CRC errors with correct duplex = bad cable/SFP/patch panel — swap components to isolate.

## §3 VLAN problems (right cable, wrong network)

Host gets no DHCP / wrong subnet / can't reach gateway but link is up → suspect VLAN.
```
# IOS — what VLAN is the port in?
show vlan brief
show interfaces Gi0/1 switchport      # mode access/trunk, access vlan, native vlan
show interfaces trunk                 # allowed + forwarding VLANs per trunk
```
Checklist:
1. Access port in the intended VLAN? `switchport access vlan 20`.
2. VLAN actually exists and is active? `show vlan brief` (a port in a nonexistent VLAN goes nowhere).
3. Trunk between switches **allows** that VLAN? `switchport trunk allowed vlan` list — the classic miss after adding a VLAN.
4. **Native VLAN mismatch** on a trunk (CDP warns: `%CDP-4-NATIVE_VLAN_MISMATCH`) — untagged traffic crosses VLANs.
5. Linux tagged interface: `ip -d link show eth0.20` (or `vlan20`); create: `ip link add link eth0 name eth0.20 type vlan id 20`. Host tagging must match the switch port mode (access port ⇒ NO tag on host; trunk ⇒ tag).
6. Windows: tag set in NIC driver properties ("VLAN ID") or `Set-NetAdapterAdvancedProperty`.

## §4 ARP / "same subnet but can't reach"

```
ip neigh show                  # Linux: INCOMPLETE/FAILED = no ARP reply
arp -a                         # Windows
show arp                       # IOS
```
No ARP reply while both up, same VLAN:
- Host firewall dropping (rare for ARP but check MAC filtering / port-security).
- Actually different subnets/masks (`ip -br addr` both sides — a /24 vs /25 mismatch splits the "same" network).
- Private VLAN / client isolation (common on WLAN guest SSIDs).
- Find where a MAC lives: `show mac address-table address <mac>` hop by hop.
- Duplicate IP: see DHCP runbook §5.
- Gratuitous-ARP test: `arping -I eth0 <peer-ip>` — works below IP-level filters.

## §5 Spanning tree — 30-50s delays and loops

- Port takes ~30s to pass traffic after link-up (classic STP listening/learning): enable `spanning-tree portfast` on host-facing access ports (NEVER on switch-switch links) or use RSTP (`spanning-tree mode rapid-pvst`).
- Network-wide meltdown, all lights blinking hard, MACs flapping between ports (`%SW_MATM-4-MACFLAP_NOTIF`) = **loop**: someone bridged two ports / plugged a hub twice. `show spanning-tree` root and blocked ports; BPDU guard on access ports prevents this: `spanning-tree bpduguard enable`.

## §6 Counters that tell stories

```
ip -s link show eth0           # Linux
show interfaces Gi0/1 | begin input rate     # IOS
```
| Counter climbing | Meaning |
|---|---|
| CRC / input errors | Bad cable/SFP/duplex — physical |
| Late collisions | Duplex mismatch (or >100m cable) |
| Output drops | Congestion/QoS — link oversubscribed |
| Giants | MTU/tagging mismatch (VLAN tag adds 4 bytes: need `system mtu` / baby giants ok) |
| Runts | Collisions/bad NIC |
Clear + watch on IOS: `clear counters Gi0/1`, recheck after 5 min.

## §7 Bonding/teaming quirks

- Linux: `cat /proc/net/bonding/bond0` — slave states, LACP partner. One slave down = degraded not dead; LACP mismatch (802.3ad vs static) = flapping.
- IOS: `show etherchannel summary` — want `P` (bundled). `w`/`s`/`i` flags = mode mismatch (`channel-group N mode active` both ends for LACP).
