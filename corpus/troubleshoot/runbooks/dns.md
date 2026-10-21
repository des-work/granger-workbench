# DNS troubleshooting decision tree

Tags: dns, resolution, nslookup, dig, resolv.conf, systemd-resolved, bind, NXDOMAIN, SERVFAIL

## Step 0 — prove it's DNS

`ping 8.8.8.8` works but `ping google.com` fails → DNS. Both fail → routing problem, not DNS.

## Step 1 — what does the OS think its resolver is?

| OS | Command | Notes |
|---|---|---|
| Linux (systemd-resolved) | `resolvectl status` | per-link DNS servers + search domains; `/etc/resolv.conf` often points at 127.0.0.53 stub |
| Linux (classic) | `cat /etc/resolv.conf` | beware: NetworkManager/dhclient rewrite it |
| Windows | `ipconfig /all` (DNS Servers line) · `Get-DnsClientServerAddress` | per-adapter |
| Cisco IOS | `show run | include name-server|domain` · `show hosts` | `ip name-server x.x.x.x`, `ip domain lookup` must be on |

## Step 2 — bypass the OS: query servers directly

```
dig example.com @1.1.1.1          # public resolver
dig example.com @<your-dns-ip>    # your configured resolver
nslookup example.com 1.1.1.1      # Windows equivalent
Resolve-DnsName example.com -Server 1.1.1.1   # PowerShell, richer output
```

| Result pattern | Diagnosis |
|---|---|
| Works @1.1.1.1, fails @your-server | Your DNS server is broken/unreachable → §3 |
| Fails @1.1.1.1 too (timeout) | Port 53 blocked outbound, or no route — firewall/routing, not DNS config |
| NXDOMAIN everywhere | Name really doesn't exist — typo? wrong search domain appended? (`dig` shows the exact queried name) |
| SERVFAIL | Upstream/authoritative failure or DNSSEC validation failing → §4 |
| Works with dig, apps still fail | OS-level: stub/cache/hosts file/search domain → §5 |

## Step 3 — your DNS server is the problem

- Reachable at all? `nc -zvu <dns> 53` and `nc -zv <dns> 53` (TCP matters for big answers).
- On the server (BIND): `systemctl status named`, `named-checkconf`, `named-checkzone example.com zonefile`, `rndc status`, logs in `journalctl -u named -e`.
- Windows DNS role: `Get-Service DNS`, DNS Manager → check forwarders; `dnscmd /info`; Event Viewer DNS-Server log.
- dnsmasq: `systemctl status dnsmasq`, test with `dig @127.0.0.1`; config `/etc/dnsmasq.conf` (`server=`, `interface=`).
- Recursion: server answers its own zones but not internet names → forwarders dead or recursion disabled (`allow-recursion` in BIND; "Disable recursion" checkbox in Windows DNS).

## Step 4 — SERVFAIL specifics

```
dig example.com +cd @server    # +cd disables DNSSEC checking
```
Works with `+cd` but not without → DNSSEC validation failure (expired signatures upstream, or your server's trust anchor/clock is wrong — check system time!).
`dig +trace example.com` walks root→TLD→authoritative and shows exactly which delegation step breaks.

## Step 5 — OS layer weirdness (dig works, apps don't)

- **hosts file override**: `getent hosts <name>` (Linux) / `type C:\Windows\System32\drivers\etc\hosts` — a stale entry beats DNS.
- **systemd-resolved stub confusion**: `resolvectl query <name>` vs `dig <name>` differ → per-link DNS mismatch (VPN pushed different DNS to one link): `resolvectl status`, `resolvectl flush-caches`.
- **Windows cache**: `ipconfig /displaydns | findstr <name>` shows a cached (possibly negative) record → `ipconfig /flushdns`.
- **Search-domain surprise**: shortname resolves to `shortname.wrong.suffix`. Linux: `resolvectl status` search list; Windows: `Get-DnsClientGlobalSetting` suffix list. `dig` a fully-qualified name (trailing dot) to compare: `dig host.example.com.`
- **nsswitch order**: `grep hosts /etc/nsswitch.conf` — should generally be `files dns` (or resolved/myhostname variants). mDNS `.local` names need avahi and only work for `.local`.

## Step 6 — VPN/split-DNS problems

Symptom: on VPN, internal names fail (or external ones do).
- Linux: `resolvectl status` — internal domains must be listed as routing domains (`~corp.example`) on the VPN link. Fix: `resolvectl domain tun0 '~corp.example'; resolvectl dns tun0 10.x.x.x`.
- Windows: `Get-DnsClientNrptPolicy` (Name Resolution Policy Table) shows which suffixes go to which server.

## Records beyond A

```
dig -t AAAA name    # IPv6 (apps may prefer broken AAAA over working A!)
dig -t MX domain    # mail
dig -t CNAME name
dig -t SRV _service._tcp.domain
dig -x 10.1.2.3     # reverse (PTR)
```
"Website slow to start connecting" with working v4 → broken IPv6 AAAA + Happy Eyeballs timeout; test `curl -4` vs `curl -6`.

## New zone/record "not working" checklist (server admin side)

1. Did you bump the zone SERIAL and `rndc reload zone`? Secondaries won't transfer otherwise (`dig -t SOA zone @primary` vs `@secondary` — compare serials).
2. TTL: old value cached everywhere until TTL expires — that's not a fault.
3. Delegation: parent NS records must match the zone's NS records (`dig +trace`).
4. Answer >512 bytes over UDP needs EDNS/TCP — a firewall blocking TCP/53 breaks big answers and zone transfers.
