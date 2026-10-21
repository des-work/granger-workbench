# SSH troubleshooting decision tree

Tags: ssh, openssh, connection refused, timeout, permission denied, host key, sshd

## Step 0 — classify the failure by its exact message

| Symptom | Meaning | Go to |
|---|---|---|
| `Connection refused` | Packet reached the host; nothing listening on that port (or RST from firewall) | §1 |
| `Connection timed out` / hangs before banner | Packets never reach sshd: routing, filtering, host down | §2 |
| Hangs *after* `SSH-2.0-...` banner exchange | MTU/PMTUD blackhole or DNS reverse-lookup stall on server | §3 |
| `Permission denied (publickey)` | Transport fine; auth failing | §4 |
| `Permission denied` (password) | Wrong password, account locked, or PasswordAuthentication off | §4 |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Host key mismatch (reinstall, IP reuse, or MITM) | §5 |
| `no matching key exchange method` / `no matching host key type` | Old client/server algorithm mismatch | §6 |
| Works then drops after idle | Keepalive/NAT timeout | §7 |
| Slow login (10-30s pause) then works | DNS reverse lookup or GSSAPI stall on server | §8 |

Always retry with maximum verbosity and read where it stops: `ssh -vvv user@host`.

## §1 Connection refused

Server side:
```
ss -tlnp | grep :22          # is sshd listening? on which address?
systemctl status sshd         # (Debian/Ubuntu: ssh) running? crashed?
journalctl -u sshd -e         # why it exited, bad config line?
sshd -t                       # validate config; prints the broken line
```
- Listening on `127.0.0.1:22` only → set `ListenAddress 0.0.0.0` (or correct addr) in `/etc/ssh/sshd_config`, restart.
- Non-standard port? `grep -E '^Port' /etc/ssh/sshd_config` and connect with `ssh -p <port>`.
- sshd up + still refused → a firewall is sending RST or the DNAT/port-forward targets the wrong inside host. Check `nft list ruleset` / `iptables -L -n -v`; on the edge router check the port-forward rule.
- Windows server: `Get-Service sshd`, `Get-NetTCPConnection -LocalPort 22 -State Listen`, `Get-NetFirewallRule -DisplayName *ssh*`.

## §2 Timeout / no banner

Client side, in order:
```
ping <host>                        # L3 reachable at all?
traceroute -n <host>               # where does the path die?
nc -zv -w4 <host> 22               # TCP probe to the port
```
- Ping ok, port 22 filtered → firewall between you and host, or host firewall DROPs (vs REJECT=refused). Server: `nft list ruleset | grep -i drop`, cloud security group / ACL on the path.
- Ping fails too → generic L3 problem: wrong route, host down, ACL. Use the routing runbook.
- Confirm on the server whether SYNs even arrive: `tcpdump -ni any port 22 and host <client-ip>` while retrying. Arriving but unanswered → host firewall. Not arriving → upstream.
- IOS device in path: `show access-lists` (look for implicit deny hits), `show ip nat translations | include 22`.

## §3 Hangs after banner / during key exchange

Classic MTU blackhole (VPN/tunnel in path). The banner is small; key exchange sends big packets.
```
ping -M do -s 1372 <host>     # if this fails but -s 1200 works => MTU issue
```
Fixes: correct MTU on tunnel iface (`ip link set dev tun0 mtu 1400`), or MSS clamp on the router: IOS `ip tcp adjust-mss 1360` on the tunnel/LAN interface; nftables `tcp flags syn tcp option maxseg size set rt mtu`.
Also possible: server-side DNS stall — see §8.

## §4 Auth failures (publickey / password)

Client: `ssh -vvv` shows which keys were *offered* and what the server *accepted*.
Server: watch live while the client retries:
```
journalctl -u sshd -f       # or: tail -f /var/log/auth.log (Debian) /var/log/secure (RHEL)
```
Most common causes, in order:
1. **Permissions.** sshd silently ignores keys if too open. Server side: `~` not group-writable, `chmod 700 ~/.ssh`, `chmod 600 ~/.ssh/authorized_keys`, owner = the login user. Log line: `Authentication refused: bad ownership or modes`.
2. Wrong user (`ssh ubuntu@` vs `root@`) or key not in *that* user's authorized_keys.
3. `PubkeyAuthentication no` / `PasswordAuthentication no` / `AllowUsers`/`AllowGroups`/`Match` blocks in sshd_config. Check what applies: `sshd -T | grep -Ei 'pubkey|password|allow|match'`.
4. SELinux (RHEL): wrong context after restoring home dirs → `restorecon -R -v ~/.ssh`.
5. Client offering too many keys → `Too many authentication failures`: `ssh -o IdentitiesOnly=yes -i ~/.ssh/right_key`.
6. root login: `PermitRootLogin prohibit-password|no`.
7. Account locked/expired: `passwd -S user`; `chage -l user`.
8. Windows OpenSSH server quirk: administrators' keys go in `C:\ProgramData\ssh\administrators_authorized_keys` (NOT ~/.ssh), ACL restricted to Administrators+SYSTEM.

## §5 Host key changed

`ssh-keygen -R <host>` removes the old key, then reconnect and verify the new fingerprint out-of-band (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server console). If the host was NOT reinstalled/re-imaged and the IP wasn't reused, treat as possible MITM — verify before accepting.

## §6 Algorithm mismatch (legacy gear)

Old network devices (IOS, old appliances) often need legacy algos enabled client-side per-host in `~/.ssh/config`:
```
Host old-switch
  KexAlgorithms +diffie-hellman-group14-sha1,diffie-hellman-group-exchange-sha1
  HostKeyAlgorithms +ssh-rsa
  PubkeyAcceptedAlgorithms +ssh-rsa
  Ciphers +aes256-cbc
```
Error text names the missing algorithm — add exactly that one. On IOS side: `ip ssh server algorithm ...`, `show ip ssh`.

## §7 Session drops after idle

NAT/firewall state timeout. Client `~/.ssh/config`:
```
Host *
  ServerAliveInterval 30
  ServerAliveCountMax 4
```
or server `ClientAliveInterval 30`.

## §8 Slow login (long pause, then normal)

- Server does reverse-DNS on your IP and its DNS is broken: set `UseDNS no` in sshd_config (default in modern OpenSSH).
- GSSAPI stall: client `ssh -o GSSAPIAuthentication=no`.
- Server-side `systemd-logind`/pam slowness: check `journalctl -e` around login time.

## Cisco IOS as the SSH *server*

```
show ip ssh                    # SSH enabled? version?
show run | include ip ssh|line vty
```
Requirements: hostname + `ip domain-name x`, `crypto key generate rsa modulus 2048`, `line vty 0 4; transport input ssh; login local`, a local user. `%SSH-3-NO_MATCH` in logs = client/server algorithm mismatch (§6).
