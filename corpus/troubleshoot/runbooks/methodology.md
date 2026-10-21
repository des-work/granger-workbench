# Network troubleshooting methodology (read me first)

Tags: methodology, approach, osi, escalation, evidence

## The layered walk (bottom-up)

Work up the stack; each layer's tools assume the layers below are healthy.

| Layer | Question | Linux | Cisco IOS | Windows |
|---|---|---|---|---|
| L1 physical | Link light? cable? | `ip -br link` (state UP?) · `ethtool eth0` | `show interfaces status` · `show interfaces GigabitEthernet0/1` | `Get-NetAdapter` (Status Up?) |
| L2 switching | Right VLAN? MAC learned? ARP? | `ip neigh` · `bridge fdb show` | `show mac address-table` · `show vlan brief` · `show arp` | `arp -a` · `Get-NetNeighbor` |
| L3 addressing | Right IP/mask/gateway? | `ip -br addr` · `ip route` | `show ip interface brief` · `show ip route` | `ipconfig /all` · `Get-NetIPConfiguration` · `route print` |
| L3 reachability | Can I reach next hop / far end? | `ping <gw>` then `ping 8.8.8.8` · `traceroute -n` | `ping`, `traceroute` | `ping`, `tracert`, `Test-NetConnection <ip>` |
| L4 transport | Is the port open/listening? | `ss -tlnp` (server side) · `nc -zv host 22` (client side) | `show tcp brief` · `telnet host 22` | `Get-NetTCPConnection` · `Test-NetConnection host -Port 22` |
| L5-7 service | Is the daemon healthy? auth? config? | `systemctl status <svc>` · `journalctl -u <svc> -e` | `show run | section <svc>` · `debug ...` (careful) | `Get-Service` · Event Viewer / `Get-WinEvent` |

**Name-vs-IP split test (do this early):** if `ping 8.8.8.8` works but `ping google.com` fails, it is a DNS problem — jump to the DNS runbook. If neither works, it's routing/L3 or below.

**Halve the path:** ping the default gateway, then the far router, then the destination. The first hop that fails localizes the fault.

**One change at a time.** Change → test → record. Revert what didn't help.

## Evidence to collect BEFORE asking for help (or generating a Claude prompt)

A good escalation contains all of these. This list drives `ultra.py fix` prompt generation.

1. **Symptom, precisely.** "SSH from A(10.0.1.5) to B(10.0.2.9) hangs after banner" beats "SSH broken".
2. **Scope.** One host or many? One direction or both? Started when? What changed?
3. **Topology sketch.** Source → switches/routers/firewalls → destination, with IPs/VLANs.
4. **Layer evidence** (paste raw output, don't paraphrase):
   - `ip -br addr; ip route; ip neigh` (or `ipconfig /all; route print`, or `show ip int brief; show ip route`)
   - The failing command with verbose flags (`ssh -vvv`, `dig +trace`, `curl -v`)
   - Server side: listener check (`ss -tlnp | grep <port>`) and the service log tail.
   - Packet proof if possible: `tcpdump -ni eth0 host <peer> and port <p>` while reproducing — do SYNs arrive? Do replies leave?
5. **What you already tried and its exact result.**

## Reading tcpdump/packet evidence quickly

- SYN sent, nothing back → filtered upstream or host down/off-path (or asymmetric return path).
- SYN sent, RST back → host reachable, port closed (service not listening / wrong port).
- SYN, SYN-ACK, then client sends nothing → local firewall/conntrack ate the SYN-ACK? MTU rarely bites here.
- Handshake completes, stalls on large transfer → MTU/PMTUD blackhole. Test: `ping -M do -s 1472 <peer>` (Linux) / `ping -f -l 1472 <peer>` (Windows). 1472+28=1500.
- Traffic arrives on the wire but the app never sees it → local firewall (`nft list ruleset` / `iptables -L -n -v`, Windows `Get-NetFirewallRule`), or wrong bind address.

## Common root-cause frequencies (check the cheap ones first)

1. Local firewall / security group rule (by far the most common for "connection refused/timeout").
2. Wrong IP/mask/VLAN (host is in the wrong L2 domain; gateway unreachable).
3. DNS pointing at the wrong/old address (check with `dig`/`nslookup` against a *specific* server).
4. Service not listening where you think (bound to 127.0.0.1 instead of 0.0.0.0; wrong port).
5. Return-path routing (packets arrive; replies leave via another interface with no route back / rp_filter drops).
6. MTU after a VPN/tunnel/overlay was introduced.
7. Duplicate IP (intermittent, ARP flapping: `ip neigh` shows changing MAC; IOS logs `%IP-4-DUPADDR`).
8. Expired DHCP scope / static-vs-DHCP conflict.
