"""[1] PC Diagnostics & Health.

Uses psutil where available and PowerShell/CIM for Windows-specific data.
Every tool produces a saved report with a synthesized verdict.
"""

from __future__ import annotations

from datetime import datetime

from . import core, ui

try:
    import psutil
    HAVE_PSUTIL = True
except Exception:
    HAVE_PSUTIL = False


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} EB"


# --------------------------------------------------------------------------- #
#  System overview
# --------------------------------------------------------------------------- #

def system_overview(ctx=None) -> None:
    ui.clear(); ui.title_bar("System Overview", "hardware & OS inventory")
    r = core.Report("System Overview")
    import platform

    r.section("Operating System")
    r.line(f"  OS:        {platform.platform()}")
    r.line(f"  Version:   {platform.version()}")
    r.line(f"  Machine:   {platform.machine()}")
    r.line(f"  Node:      {core.COMPUTER}")
    r.line(f"  Python:    {platform.python_version()}")

    r.section("CPU")
    r.line(f"  Processor: {platform.processor()}")
    if HAVE_PSUTIL:
        r.line(f"  Cores:     {psutil.cpu_count(logical=False)} physical / "
               f"{psutil.cpu_count(logical=True)} logical")
        freq = psutil.cpu_freq()
        if freq:
            r.line(f"  Frequency: {freq.current:.0f} MHz (max {freq.max:.0f})")
        r.line(f"  Load now:  {psutil.cpu_percent(interval=0.5):.0f}%")

    if HAVE_PSUTIL:
        vm = psutil.virtual_memory()
        r.section("Memory")
        r.line(f"  Total:     {_fmt_bytes(vm.total)}")
        r.line(f"  Available: {_fmt_bytes(vm.available)} ({100 - vm.percent:.0f}% free)")
        used_pct = vm.percent
        if used_pct > 90:
            r.finding("WARN", f"RAM {used_pct:.0f}% used — memory pressure", "MEDIUM",
                      "System low on RAM")
        else:
            r.finding("PASS", f"RAM {used_pct:.0f}% used")

        r.section("Disks")
        for part in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(part.mountpoint)
            except Exception:
                continue
            r.line(f"  {part.device:<8} {part.fstype:<6} "
                   f"{_fmt_bytes(u.used)}/{_fmt_bytes(u.total)} ({u.percent:.0f}% used)")

        boot = datetime.fromtimestamp(psutil.boot_time())
        up = datetime.now() - boot
        r.section("Uptime")
        r.line(f"  Booted:    {boot:%Y-%m-%d %H:%M:%S}")
        r.line(f"  Uptime:    {up.days}d {up.seconds // 3600}h {(up.seconds % 3600) // 60}m")

    if core.IS_WINDOWS:
        r.section("GPU")
        gpu = core.powershell(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,@{n='VRAM_GB';e={[math]::Round($_.AdapterRAM/1GB,1)}},"
            "DriverVersion | Format-Table -AutoSize | Out-String")
        r.line(gpu.strip() or "  (unavailable)")

    ui.deliver_report(r, "System_Overview")


# --------------------------------------------------------------------------- #
#  Disk / SMART health
# --------------------------------------------------------------------------- #

def disk_health(ctx=None) -> None:
    ui.clear(); ui.title_bar("Disk & SMART Health", "physical drive status")
    r = core.Report("Disk & SMART Health")

    if not core.IS_WINDOWS:
        r.finding("SKIP", "SMART query needs Windows PowerShell.")
        ui.deliver_report(r, "Disk_Health"); return

    r.section("Physical disks")
    table = core.powershell(
        "Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,"
        "OperationalStatus,@{n='Size_GB';e={[math]::Round($_.Size/1GB,1)}} | "
        "Format-Table -AutoSize | Out-String")
    r.line(table.strip() or "  (none reported)")

    unhealthy = core.ps_value(
        "(Get-PhysicalDisk | Where-Object HealthStatus -ne 'Healthy' | "
        "Measure-Object).Count")
    if unhealthy.isdigit() and int(unhealthy) > 0:
        r.finding("FAIL", f"{unhealthy} disk(s) report unhealthy SMART status", "HIGH",
                  "Drive failing — SMART unhealthy")
    else:
        r.finding("PASS", "All physical disks report Healthy")

    r.section("Volume free space")
    for line in core.powershell(
            "Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter,"
            "FileSystemLabel,@{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB,1)}},"
            "@{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}} | "
            "Format-Table -AutoSize | Out-String").strip().splitlines():
        r.line("  " + line)

    ui.deliver_report(r, "Disk_Health")


# --------------------------------------------------------------------------- #
#  Slow triage — Python port of 33_PC_Slow_Triage.bat
# --------------------------------------------------------------------------- #

def slow_triage(ctx=None) -> None:
    ui.clear(); ui.title_bar("PC Slow Triage", "why is this machine slow?")
    if not ui.ask_yesno("Run 8 performance checks now? (~1-2 min)", "Slow Triage"):
        return
    r = core.Report("PC Slow Triage")

    # 1. Disk health
    r.section("Disk SMART health")
    if core.IS_WINDOWS:
        bad = core.ps_value("(Get-PhysicalDisk | Where-Object HealthStatus -ne "
                            "'Healthy' | Measure-Object).Count")
        if bad.isdigit() and int(bad) > 0:
            r.finding("FAIL", f"{bad} disk(s) unhealthy", "HIGH",
                      "Drive failing — SMART unhealthy")
        else:
            r.finding("PASS", "All disks healthy")
    else:
        r.finding("SKIP", "needs Windows")

    if HAVE_PSUTIL:
        # 2. Free space on system drive
        r.section("System drive free space")
        sysdrive = "C:\\" if core.IS_WINDOWS else "/"
        try:
            u = psutil.disk_usage(sysdrive)
            free_pct = 100 - u.percent
            if free_pct < 10:
                r.finding("FAIL", f"only {free_pct:.0f}% free on {sysdrive}", "HIGH",
                          f"{sysdrive} critically low on space")
            elif free_pct < 15:
                r.finding("WARN", f"{free_pct:.0f}% free on {sysdrive}")
            else:
                r.finding("PASS", f"{free_pct:.0f}% free on {sysdrive}")
        except Exception:
            r.finding("SKIP", "could not read drive")

        # 3. RAM
        r.section("RAM usage")
        vm = psutil.virtual_memory()
        free_pct = 100 - vm.percent
        if free_pct < 10:
            r.finding("FAIL", f"only {free_pct:.0f}% RAM free — paging likely", "HIGH",
                      "Out of RAM — system paging heavily")
        elif free_pct < 20:
            r.finding("WARN", f"only {free_pct:.0f}% RAM free")
        else:
            r.finding("PASS", f"{free_pct:.0f}% RAM free")

        # 4. Top CPU processes — prime baselines on stable Process objects,
        #    sleep, then read the delta (per-process cpu_percent needs two reads).
        r.section("Top CPU processes")
        import time
        procs = list(psutil.process_iter(["name", "memory_info"]))
        for p in procs:
            try:
                p.cpu_percent(None)  # prime
            except Exception:
                pass
        time.sleep(0.6)
        rows = []
        for p in procs:
            try:
                cpu = p.cpu_percent(None)
                name = p.info.get("name") or "?"
                mem = p.info.get("memory_info")
                rows.append((cpu, name, mem.rss / 1024 / 1024 if mem else 0))
            except Exception:
                continue
        rows.sort(reverse=True)
        miners = {"xmrig", "cgminer", "coinminer", "minerd", "nbminer"}
        miner_hit = False
        for cpu, name, memmb in rows[:8]:
            r.line(f"  {name:<28} cpu {cpu:>5.1f}%  mem {memmb:>7.1f} MB")
            if name.lower().replace(".exe", "") in miners:
                miner_hit = True
        if miner_hit:
            r.finding("FAIL", "cryptominer process detected", "HIGH",
                      "Cryptominer malware running")
        else:
            r.finding("PASS", "no obvious cryptominers in top processes")

    # 5. Startup items
    if core.IS_WINDOWS:
        r.section("Startup items")
        cnt = core.ps_value("(Get-CimInstance Win32_StartupCommand | Measure-Object).Count")
        if cnt.isdigit():
            n = int(cnt)
            if n > 50:
                r.finding("WARN", f"{n} startup items — slows boot")
            elif n > 30:
                r.finding("WARN", f"{n} startup items — on the high side")
            else:
                r.finding("PASS", f"{n} startup items")

        # 6. Services
        r.section("Running services")
        run_cnt = core.ps_value("(Get-Service | Where-Object Status -eq Running | "
                                "Measure-Object).Count")
        if run_cnt.isdigit():
            n = int(run_cnt)
            r.finding("WARN" if n > 200 else "PASS", f"{n} services running")

    # 7. Uptime
    if HAVE_PSUTIL:
        r.section("Uptime")
        up_days = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).days
        if up_days > 30:
            r.finding("WARN", f"up {up_days} days — a reboot may help")
        else:
            r.finding("PASS", f"uptime {up_days} days")

    ui.deliver_report(r, "PC_Slow_Triage")


# --------------------------------------------------------------------------- #
#  Network diagnostics
# --------------------------------------------------------------------------- #

def network_diag(ctx=None) -> None:
    ui.clear(); ui.title_bar("Network Diagnostics", "connectivity & interfaces")
    r = core.Report("Network Diagnostics")

    if HAVE_PSUTIL:
        r.section("Interfaces (up)")
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        for name, st in stats.items():
            if not st.isup:
                continue
            ips = [a.address for a in addrs.get(name, []) if a.family.name == "AF_INET"]
            r.line(f"  {name:<24} {'up':<4} {st.speed} Mbps  {', '.join(ips) or '-'}")

    r.section("Connectivity")
    import subprocess
    ping_target = "8.8.8.8"
    count_flag = "-n" if core.IS_WINDOWS else "-c"
    out = core.run(["ping", count_flag, "3", ping_target], timeout=20)
    if "TTL=" in out or "ttl=" in out or "time=" in out:
        r.finding("PASS", f"internet reachable ({ping_target})")
    else:
        r.finding("FAIL", f"cannot reach {ping_target}", "HIGH", "No internet connectivity")
    r.line(out)

    r.section("DNS resolution")
    dns = core.run(["nslookup", "example.com"], timeout=15)
    if "Address" in dns or "addresses" in dns.lower():
        r.finding("PASS", "DNS resolving")
    else:
        r.finding("WARN", "DNS resolution unclear — see report")
    r.line(dns)

    ui.deliver_report(r, "Network_Diagnostics")


# --------------------------------------------------------------------------- #
#  Registration
# --------------------------------------------------------------------------- #

def register() -> core.Category:
    cat = core.Category("diag", "PC Diagnostics & Health")
    cat.add("sys", "System overview (hardware & OS inventory)", system_overview)
    cat.add("disk", "Disk & SMART health", disk_health)
    cat.add("slow", "Slow triage — 'why is this slow?'", slow_triage)
    cat.add("net", "Network diagnostics", network_diag)
    return cat
