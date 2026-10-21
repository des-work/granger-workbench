# Windows networking quick reference (troubleshooting-first)

Tags: windows, netsh, powershell, ipconfig, winrm, rdp, smb, firewall, dns client

## The modern PowerShell set (prefer these)

```powershell
Get-NetIPConfiguration               # ipconfig /all, structured
Get-NetAdapter                       # link state, speed
Get-NetRoute -DestinationPrefix 0.0.0.0/0    # default routes + metrics
Find-NetRoute -RemoteIPAddress 8.8.8.8       # which route/interface THIS dest uses
Get-NetNeighbor                      # ARP table
Get-DnsClientServerAddress           # DNS per adapter
Resolve-DnsName name [-Server ip] [-Type A|AAAA|MX|TXT|SRV]
Test-NetConnection host -Port 443    # ping + TCP probe + route diagnosis in one
Test-NetConnection -TraceRoute host
Get-NetTCPConnection -State Listen   # netstat -ano equivalent
Get-NetConnectionProfile             # Public vs Private (firewall profile!)
Get-NetFirewallProfile | Select Name,Enabled
Get-SmbConnection / Get-SmbShare
Get-DnsClientCache                   # + Clear-DnsClientCache
```

## Classic commands still worth knowing

```
ipconfig /all | /release | /renew | /flushdns | /displaydns | /registerdns
route print                          # -4 for IPv4 only
route add 10.2.0.0 mask 255.255.0.0 10.1.1.254 -p      # -p = persistent
netstat -ano | findstr :443          # PID owning a port  → tasklist /fi "PID eq <pid>"
arp -a  ·  nslookup name server  ·  tracert -d host  ·  pathping host
netsh interface ip show config
netsh wlan show wlanreport           # HTML Wi-Fi diagnosis report
netsh trace start capture=yes ...    # built-in packet capture (etl) — or use pktmon:
pktmon start --capture --comp nics ; pktmon stop ; pktmon etl2pcap log.etl   # → wireshark
```

## Reset hammers (order: least → most destructive)

```
ipconfig /flushdns
netsh winsock reset            # after malware/VPN-client damage; reboot
netsh int ip reset             # rebuild TCP/IP stack; reboot
Restart-NetAdapter -Name Ethernet
Get-NetAdapter | Restart-NetAdapter   # everything
```

## Firewall (see also nat-firewall runbook)

```powershell
Set-NetConnectionProfile -InterfaceAlias Ethernet -NetworkCategory Private
New-NetFirewallRule -DisplayName 'Allow ICMPv4-In' -Protocol ICMPv4 -IcmpType 8 -Direction Inbound -Action Allow
Get-NetFirewallRule -Enabled True -Direction Inbound | Sort DisplayName | Select DisplayName,Profile,Action
Set-NetFirewallProfile -LogBlocked True      # log: %systemroot%\system32\LogFiles\Firewall\pfirewall.log
```

## Remote management

```powershell
# WinRM / PowerShell remoting
Enable-PSRemoting -Force
Test-WSMan <host>
Enter-PSSession <host> [-Credential (Get-Credential)]
# workgroup (non-domain) client needs: Set-Item WSMan:\localhost\Client\TrustedHosts '<host>'
# RDP
Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 0
Enable-NetFirewallRule -DisplayGroup 'Remote Desktop'
qwinsta /server:<host>              # who's logged on
# OpenSSH server (optional feature)
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd ; Set-Service sshd -StartupType Automatic
# admins' keys: C:\ProgramData\ssh\administrators_authorized_keys (strict ACL!)
```

## SMB / shares

```powershell
Test-NetConnection <host> -Port 445
Get-SmbServerConfiguration | Select EnableSMB1Protocol,EnableSMB2Protocol
net use * \\host\share /user:DOMAIN\user      # classic map
Get-SmbMapping ; Get-SmbOpenFile
# access denied vs not found: check both NTFS ACL (icacls path) AND share perms (Get-SmbShareAccess share)
```
Guest/anonymous share access is blocked by default on modern Windows — "0x80070035 network path not found" against a NAS often = SMB1-only device or guest-auth policy, not networking.

## AD-joined boxes: the usual suspects

```powershell
Test-ComputerSecureChannel [-Repair -Credential ...]   # broken trust ("machine account password")
w32tm /query /status                                   # Kerberos needs <5 min clock skew
nltest /dsgetdc:domain.local                           # which DC am I using?
gpupdate /force ; gpresult /h out.html                 # policy actually applied?
klist                                                  # Kerberos tickets
```
DNS on a domain machine should point ONLY at AD DNS servers (public resolver as secondary breaks logons intermittently).

## Event logs that matter for networking

```powershell
Get-WinEvent -LogName 'Microsoft-Windows-Dhcp-Client/Admin' -MaxEvents 20
Get-WinEvent -LogName 'Microsoft-Windows-DNS-Client Events/Operational' -MaxEvents 20
Get-WinEvent -LogName System -MaxEvents 50 | where ProviderName -match 'Tcpip|Dhcp|DNS'
```
