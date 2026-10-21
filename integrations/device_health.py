#!/usr/bin/env python3
"""Local, read-only device-health tool for Hermes over MCP stdio.

Real readings only. Each section shells out to one already-installed tool
(sensors, nvidia-smi, upower, df, /proc) and reports "unavailable" for that
section alone on failure, rather than fabricating a number or failing the
whole snapshot. No network calls.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


class HealthError(Exception):
    pass


def _run(cmd, timeout=5):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def cpu():
    try:
        load1, load5, load15 = Path("/proc/loadavg").read_text().split()[:3]
    except OSError:
        return {"error": "unavailable"}
    reading = {"load_1m": float(load1), "load_5m": float(load5), "load_15m": float(load15)}
    nproc = _run(["nproc"])
    if nproc:
        try:
            reading["cores"] = int(nproc.strip())
        except ValueError:
            pass
    sensors_out = _run(["sensors"])
    if sensors_out:
        match = re.search(r"Package id 0:\s*\+?(-?[\d.]+)", sensors_out)
        if match:
            reading["package_temp_c"] = float(match.group(1))
    return reading


def memory():
    try:
        text = Path("/proc/meminfo").read_text()
    except OSError:
        return {"error": "unavailable"}
    fields = {}
    for line in text.splitlines():
        match = re.match(r"(\w+):\s+(\d+) kB", line)
        if match:
            fields[match.group(1)] = int(match.group(2))
    total = fields.get("MemTotal", 0)
    available = fields.get("MemAvailable", 0)
    swap_total = fields.get("SwapTotal", 0)
    swap_free = fields.get("SwapFree", 0)
    reading = {
        "total_gb": round(total / 1_048_576, 1),
        "available_gb": round(available / 1_048_576, 1),
        "swap_total_gb": round(swap_total / 1_048_576, 1),
        "swap_used_gb": round((swap_total - swap_free) / 1_048_576, 1),
    }
    if total:
        reading["used_percent"] = round((1 - available / total) * 100, 1)
    return reading


def gpu():
    out = _run(["nvidia-smi",
                "--query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu,power.draw",
                "--format=csv,noheader,nounits"])
    if not out:
        return {"error": "unavailable"}
    parts = [p.strip() for p in out.strip().split(",")]
    if len(parts) != 6:
        return {"error": "unexpected nvidia-smi output"}
    name, temp, mem_used, mem_total, util, power = parts
    try:
        return {"name": name, "temperature_c": float(temp), "memory_used_mb": float(mem_used),
                "memory_total_mb": float(mem_total), "utilization_percent": float(util),
                "power_draw_w": float(power)}
    except ValueError:
        return {"error": "unexpected nvidia-smi output"}


def battery():
    devices = _run(["upower", "-e"])
    bat = next((line.strip() for line in (devices or "").splitlines() if "BAT" in line), None)
    if not bat:
        return {"present": False}
    out = _run(["upower", "-i", bat])
    if not out:
        return {"present": True, "error": "unavailable"}
    reading = {"present": True}
    patterns = {
        "state": r"state:\s*(\S+)",
        "percentage": r"percentage:\s*(\d+)%",
        # "capacity" is upower's health metric: full-charge capacity vs the
        # design capacity when new - the actual wear indicator, not charge %.
        "capacity_health_percent": r"^\s*capacity:\s*([\d.]+)%",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, out, re.M)
        if match:
            reading[key] = match.group(1) if key == "state" else float(match.group(1))
    return reading


def disks():
    out = _run(["df", "-h", "--output=target,size,used,avail,pcent",
                "-x", "tmpfs", "-x", "devtmpfs", "-x", "overlay", "-x", "squashfs",
                "-x", "efivarfs"])
    if not out:
        return {"error": "unavailable"}
    rows = []
    for line in out.strip().splitlines()[1:]:
        parts = line.split()
        if len(parts) == 5:
            rows.append({"mount": parts[0], "size": parts[1], "used": parts[2],
                        "available": parts[3], "used_percent": parts[4]})
    return {"mounts": rows}


def uptime():
    out = _run(["uptime", "-p"])
    return out.strip() if out else "unavailable"


def snapshot():
    return {"cpu": cpu(), "memory": memory(), "gpu": gpu(), "battery": battery(),
            "disks": disks(), "uptime": uptime()}


TOOLS = [
    {"name": "device_health",
     "description": ("Read this machine's actual current health: CPU load and package "
                      "temperature, RAM and swap usage, GPU temperature/utilization/memory, "
                      "battery charge and wear (capacity_health_percent - full-charge capacity "
                      "versus design capacity, the real wear indicator, distinct from the "
                      "charge percentage), and disk space per mount. Every field is a live "
                      "reading taken just now, not an estimate. Call this instead of guessing "
                      "or making up numbers for any question about device/system/battery/disk "
                      "health or status. A section reporting an error means that one reading "
                      "is unavailable on this machine right now - say so, don't invent a value."),
     "inputSchema": {"type": "object", "properties": {}}},
]


def rpc(message):
    method, params = message.get("method"), message.get("params") or {}
    if method == "initialize":
        return {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                "serverInfo": {"name": "device-health", "version": "1.0"}}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        try:
            if params.get("name") != "device_health":
                raise HealthError("Unknown tool")
            result = snapshot()
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        except Exception as exc:
            return {"isError": True, "content": [{"type": "text", "text": str(exc)}]}
    return None


def main():
    if "--check" in sys.argv:
        print(json.dumps(snapshot(), indent=2))
        return
    for line in sys.stdin:
        try:
            request_obj = json.loads(line)
            result = rpc(request_obj)
            if "id" in request_obj:
                reply = {"jsonrpc": "2.0", "id": request_obj["id"]}
                if result is None:
                    reply["error"] = {"code": -32601, "message": "Method not found"}
                else:
                    reply["result"] = result
                print(json.dumps(reply), flush=True)
        except Exception as exc:
            print(f"MCP request error: {exc}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
