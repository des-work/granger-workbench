# Cisco IOS/IOS-XE command quick reference (troubleshooting-first)

Tags: cisco, ios, show commands, debug, vlan, ospf, bgp, nat, acl, syntax

## Orientation on an unfamiliar device

```
show version                     # platform, IOS version, uptime, reload reason
show running-config              # (or: show run | section <feature>)
show ip interface brief          # every L3 interface + state in one screen
show interfaces status           # switchports: connected/notconnect/err-disabled, VLAN, speed
show cdp neighbors detail        # what's physically attached (LLDP: show lldp neighbors)
show inventory                   # serials/SFPs
show logging                     # the device's own story
show processes cpu sorted | exclude 0.00   # is it melting?
```

## Filtering output (essential on long configs)

```
show run | include ^interface|ip address     # regex include
show run | section ospf                      # whole config blocks
show run | begin line vty                    # from first match onward
show ip route | exclude connected
```

## L2 switching

```
show mac address-table [address <mac>|interface Gi0/1]
show vlan brief
show interfaces trunk
show interfaces Gi0/1 switchport
show spanning-tree [vlan 10]
show port-security interface Gi0/1
show etherchannel summary
show ip dhcp snooping binding
clear mac address-table dynamic
```
Config bits: `switchport mode access|trunk`, `switchport access vlan N`, `switchport trunk allowed vlan add N` (**never forget `add`** — without it you REPLACE the list and drop every other VLAN), `spanning-tree portfast`, `spanning-tree bpduguard enable`.

## L3 / routing

```
show ip route [<dest>]           # RIB
show ip cef <dest> [detail]      # FIB — what's actually forwarding
show ip protocols                # what's running, timers, networks
show ip arp
ping <ip> source <iface>         # test from a specific source (return-path check!)
ping <ip> size 1500 df-bit       # MTU probe
traceroute <ip> numeric
show ip ospf neighbor | show ip ospf interface brief | show ip ospf database
show ip bgp summary | show ip bgp neighbors <ip> | show ip bgp <prefix>
show standby brief               # HSRP state (Active/Standby)
show ip nat translations | statistics
show access-lists                # with per-line hit counters
```

## Debug — safely

```
show debugging                 # what's already on
undebug all                    # the panic button (or: u all)
terminal monitor               # see debugs over SSH (no = stop)
debug ip icmp | debug ip ospf adj | debug ip bgp | debug ip dhcp server events
```
Rules: never `debug all`; never debug packet-level on a busy box; consider `logging buffered 64000 debugging` + `no logging console` first, read with `show logging`. Conditional debug limits blast radius: `debug condition interface Gi0/1`.

## Config hygiene

```
configure terminal ... end
show archive config differences   # if archive configured
copy running-config startup-config     # SAVE (or: write memory / wr)
reload in 10                      # safety net before risky remote change — cancel with: reload cancel
```
`reload in N` then make the change; if you lock yourself out the box reboots to the old startup-config. Confirm change works → `reload cancel` + save.

## Interface repair one-liners

```
interface Gi0/1
 shutdown / no shutdown          # bounce
 speed auto / duplex auto
 no switchport                   # make it routed (L3 switch)
 ip address 10.1.1.1 255.255.255.0
```

## Management plane

```
line vty 0 4
 transport input ssh
 login local
ip ssh version 2
crypto key generate rsa modulus 2048     # needs hostname + ip domain-name first
show users                                # who's on
show ip ssh
ntp server <ip>  /  show ntp status      # wrong clock breaks certs+DNSSEC+logs
```

## Password recovery / config register (physical access)

Break during boot → ROMMON → `confreg 0x2142` (ignore startup) → boot → copy startup to running, change secret, `config-register 0x2102`, save. `show version` last line reveals a 0x2142 left behind (symptom: config "vanishes" every reboot).

## IOS vs IOS-XE differences that bite

- IOS-XE: `show platform`, software install via `install add file ... activate commit`.
- Some IOS-XE boxes: `show ip interface brief | exclude unassigned` lists many internal interfaces — filter aggressively.
