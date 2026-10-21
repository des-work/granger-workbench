# Linux networking quick reference (troubleshooting-first)

Tags: linux, iproute2, ss, tcpdump, nftables, systemd-networkd, networkmanager, journalctl

## iproute2 — the modern set (ifconfig/netstat are dead)

```
ip -br addr                     # all interfaces + IPs, one line each
ip -br link                     # link state (UP / NO-CARRIER)
ip -s link show eth0            # error/drop counters
ip route show ; ip -6 route show
ip route get 8.8.8.8            # THE command: which route/iface/src for this dest
ip rule show                    # policy routing tables (VPNs live here)
ip neigh show                   # ARP/ND cache (REACHABLE/STALE ok, FAILED bad)
ip addr add 10.1.1.5/24 dev eth0 ; ip link set eth0 up
ip link set eth0 mtu 1400
ip link add link eth0 name eth0.20 type vlan id 20     # tagged VLAN
```

## Sockets & processes

```
ss -tlnp                        # TCP listeners + owning process
ss -ulnp                        # UDP
ss -tnp state established '( dport = :443 or sport = :443 )'
ss -s                           # socket summary
fuser 80/tcp                    # PID on a port (alt: lsof -i :80)
```
Bound to `127.0.0.1:port` = local-only — the #1 "works on the box, refused remotely" cause.

## Live packet proof

```
tcpdump -ni eth0 host 10.1.1.9 and port 443        # the ground truth
tcpdump -ni any icmp                                # watch pings arrive
tcpdump -ni eth0 -w cap.pcap -c 500                 # save for wireshark
tcpdump -ni eth0 'tcp[tcpflags] & (tcp-syn|tcp-rst) != 0'   # handshake problems only
```

## Name resolution

```
resolvectl status               # per-link DNS (systemd-resolved)
resolvectl query name ; resolvectl flush-caches
dig name @server +short ; dig +trace name ; dig -x <ip>
getent hosts name               # what apps actually get (nsswitch: files+dns)
```

## Firewall

```
nft list ruleset
iptables -L -n -v --line-numbers ; iptables -t nat -L -n -v    # -v = hit counters
firewall-cmd --list-all         # RHEL/firewalld
ufw status verbose              # Ubuntu
conntrack -L | grep <ip>        # connection tracking state
sysctl net.ipv4.ip_forward      # =1 required to route/forward
```

## Which network manager owns this box? (config edits go different places)

```
systemctl is-active NetworkManager systemd-networkd
networkctl list                              # networkd view
nmcli device status ; nmcli connection show  # NetworkManager view
```
| Stack | Config lives in | Apply |
|---|---|---|
| NetworkManager (desktops, RHEL) | `nmcli con mod` / `/etc/NetworkManager/system-connections/` | `nmcli con up <name>` |
| systemd-networkd (servers, Arch) | `/etc/systemd/network/*.network` | `networkctl reload` |
| netplan (Ubuntu) | `/etc/netplan/*.yaml` (renders to one of the above) | `netplan apply` (try: `netplan try`) |
| ifupdown (old Debian) | `/etc/network/interfaces` | `ifdown eth0 && ifup eth0` |

Static IP via nmcli:
```
nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addresses 10.1.1.5/24 ipv4.gateway 10.1.1.1 ipv4.dns 10.1.1.53
nmcli con up "Wired connection 1"
```

## Logs & services

```
journalctl -u sshd -e           # service log, jump to end
journalctl -f                   # follow everything
journalctl -b -p err            # this boot, errors only
dmesg -T | grep -i eth          # kernel: link up/down, driver, firmware
systemctl status <svc> ; systemctl restart <svc>
```

## DHCP client

```
dhclient -v eth0                # verbose DORA
networkctl renew eth0           # networkd
nmcli device reapply eth0       # NM
```

## Wi-Fi

```
iw dev wlan0 link               # connected? signal? bitrate
iw dev wlan0 scan | grep -E 'SSID|signal'
nmcli device wifi list ; nmcli device wifi connect <ssid> password <pw>
rfkill list                     # soft/hard blocked?
```

## Performance triage

```
mtr -rwzbc 50 <host>            # traceroute+loss statistics in one report
iperf3 -s (server) / iperf3 -c <server> [-R]      # raw throughput both directions
ethtool eth0 | grep -E 'Speed|Duplex'
ping -M do -s 1472 <host>       # MTU probe (1472+28=1500)
tc qdisc show dev eth0          # shaping applied?
```

## Namespaces & containers (why "it works on the host but not in the container")

```
ip netns list ; ip netns exec <ns> ip -br addr
docker network ls ; docker inspect <ctr> --format '{{json .NetworkSettings.Networks}}'
nsenter -t <pid> -n ss -tlnp    # inspect a container's sockets from the host
```
Container can't be reached: published port (`-p 8080:80`) vs exposed; iptables DOCKER chain; container listening on 127.0.0.1 inside the container (must bind 0.0.0.0).
