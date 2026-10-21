# DHCP troubleshooting decision tree

Tags: dhcp, lease, apipa, 169.254, dhclient, dhcp relay, ip helper-address, kea, isc

## Step 0 — classify

| Symptom | Meaning | Go to |
|---|---|---|
| Client has 169.254.x.x (APIPA) / no lease | DISCOVER never answered | §1 |
| Client gets a lease but wrong subnet/options | Wrong scope matched / rogue server | §3 |
| Some clients get leases, new ones don't | Scope exhausted | §2 |
| Lease works, then breaks at renewal | Renewal (unicast) blocked or server changed | §4 |
| Two hosts fighting over one IP | Duplicate / conflicting static | §5 |

DHCP flow to keep in mind: **D**ISCOVER (bcast) → **O**FFER → **R**EQUEST → **A**CK ("DORA"). Broadcasts don't cross routers — remote subnets need a relay.

## §1 No lease at all

Client side — force and watch:
```
# Linux
sudo dhclient -v eth0             # verbose DORA on the console
# or: sudo networkctl renew eth0 ; journalctl -u systemd-networkd -e
# Windows
ipconfig /release ; ipconfig /renew
# then: Get-WinEvent -LogName 'Microsoft-Windows-Dhcp-Client/Admin' -MaxEvents 20
```
Watch the wire (server or client): `tcpdump -ni eth0 port 67 or port 68`

| What you see | Diagnosis |
|---|---|
| No DISCOVER leaves the client | Client iface down/wrong (check `ip -br link`), or client not set to DHCP |
| DISCOVER visible on client, never reaches server | L2 path: wrong VLAN, port isolated, **missing DHCP relay** on the client's gateway (§1a), DHCP snooping dropping it (§1b) |
| DISCOVER arrives, no OFFER | Server: service down, no scope for that subnet, scope full (§2), or server ignores unknown clients |
| OFFER sent, client keeps DISCOVERing | OFFER not reaching client (return path / snooping), or client rejects it |

Server health:
```
systemctl status kea-dhcp4-server   # or isc-dhcp-server / dhcpd
journalctl -u kea-dhcp4-server -e
# Windows DHCP role:
Get-Service DHCPServer ; Get-DhcpServerv4Scope ; Get-DhcpServerv4ScopeStatistics
```
Windows domain environments: the DHCP server must be **authorized** in AD (`Get-DhcpServerInDC`) or it silently won't serve.

### §1a Clients on a different subnet than the server → relay required

On the clients' gateway (IOS): `interface Vlan20` → `ip helper-address <dhcp-server-ip>`.
Verify: `show ip interface Vlan20 | include Helper`. Linux router: `dhcrelay` or Kea's relay. The server also needs a scope matching the *clients'* subnet (relay stamps giaddr with its interface IP — that's how the scope is selected).

### §1b DHCP snooping eating packets (switches)

`show ip dhcp snooping` / `show ip dhcp snooping binding`. The uplink toward the real server must be a **trusted** port: `ip dhcp snooping trust` on that interface. Untrusted ports drop OFFERs by design.

## §2 Scope exhausted

- IOS server: `show ip dhcp pool` (leased/total), `show ip dhcp binding`.
- Kea/ISC: count leases in `/var/lib/kea/kea-leases4.csv` / `dhcpd.leases` vs range size.
- Windows: `Get-DhcpServerv4ScopeStatistics` (PercentageInUse).
Fixes: widen range, shorten lease time for guest networks, purge stale bindings (`clear ip dhcp binding *` on IOS — careful).

## §3 Wrong address/options handed out

- **Rogue server**: two OFFERs race. Find it: `tcpdump -ni eth0 port 67 -e` and look at source MACs of OFFERs; or Windows `Get-WinEvent` DHCP-client log shows the server ID. A plugged-in home router is the classic culprit. Prevention = DHCP snooping (§1b).
- Wrong scope matched behind relay: the helper's giaddr decides — check the relay interface IP and the server's subnet declarations.
- Options: gateway = option 3, DNS = option 6, domain = option 15. Verify what the client actually received: Linux `networkctl status eth0`; Windows `ipconfig /all`.

## §4 Breaks at renewal (T1/T2)

Renewal at 50% of lease is **unicast** to the server (no relay involved) — a firewall that only allowed broadcast DHCP, or a server IP change, breaks renewals while fresh boots work. Confirm with `tcpdump port 67` at renewal time; allow UDP/67 unicast server-bound.

## §5 Duplicate IP conflict

Symptoms: intermittent connectivity, ARP flapping (`ip neigh show` MAC changes; IOS `%IP-4-DUPADDR` log).
```
arping -D -I eth0 <ip>       # duplicate-address probe (0 replies = free)
arp-scan --interface eth0 <subnet>/24   # who owns what
```
Find the offender's switch port by MAC: IOS `show mac address-table address <mac>`. Common cause: static assignment inside the DHCP range — exclude statics: IOS `ip dhcp excluded-address a.b.c.d`; Windows scope exclusion range; Kea `pools` that skip the static block.

## Cisco IOS as the DHCP *server* — quick reference

```
ip dhcp excluded-address 10.1.1.1 10.1.1.20
ip dhcp pool LAN
 network 10.1.1.0 255.255.255.0
 default-router 10.1.1.1
 dns-server 10.1.1.5
 lease 0 8
show ip dhcp binding | show ip dhcp pool | show ip dhcp conflict
debug ip dhcp server events        # watch DORA live (safe-ish)
```
`show ip dhcp conflict` non-empty = duplicate IPs detected via ping-before-offer.
