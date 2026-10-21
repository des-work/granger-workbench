"""[5] Thumbdrive Scripts — auto-detect the portable USB kit and launch it.

Scans removable/local drives for the \\Scripts folder that contains
0_START_HERE.bat, lists every numbered .bat, and launches the chosen one in
its own console so it runs exactly as it does off the stick (its %~d0 drive
reference is preserved).
"""

from __future__ import annotations

import re
import string
import subprocess
from pathlib import Path

from . import core, ui

MARKER = "0_START_HERE.bat"


def _candidate_roots() -> list[Path]:
    roots = []
    if core.IS_WINDOWS:
        for letter in string.ascii_uppercase:
            p = Path(f"{letter}:\\")
            if p.exists():
                roots.append(p)
    else:
        roots.append(Path("/"))
    return roots


def find_scripts_dir() -> Path | None:
    # 1. cached path
    cfg = core.load_config()
    cached = cfg.get("usb_scripts_path")
    if cached and (Path(cached) / MARKER).exists():
        return Path(cached)
    # 2. scan drives for <drive>\Scripts\0_START_HERE.bat
    for root in _candidate_roots():
        cand = root / "Scripts"
        if (cand / MARKER).exists():
            cfg["usb_scripts_path"] = str(cand)
            core.save_config(cfg)
            return cand
    return None


def _pretty(name: str) -> tuple[int, str]:
    """('33_PC_Slow_Triage.bat') -> (33, 'PC Slow Triage')."""
    stem = Path(name).stem
    m = re.match(r"^(\d+)[_\-\s]*(.*)$", stem)
    if m:
        return int(m.group(1)), m.group(2).replace("_", " ").strip() or stem
    return 9999, stem.replace("_", " ")


def _list_scripts(scripts_dir: Path) -> list[Path]:
    bats = [p for p in scripts_dir.glob("*.bat")
            if not p.name.startswith("_")
            and not p.name.lower().endswith((".old", ".backup"))
            and ".v2_old" not in p.name.lower()]
    return sorted(bats, key=lambda p: _pretty(p.name)[0])


def _launch(bat: Path) -> None:
    """Launch a .bat in its own console rooted at its drive."""
    drive_root = Path(bat.drive + "\\") if bat.drive else bat.parent
    try:
        if core.IS_WINDOWS:
            # start in a new window; keep working dir at the drive root so the
            # script's %~d0 / relative paths resolve like they do off the USB.
            subprocess.Popen(f'start "Ultra-PC: {bat.name}" cmd /c "{bat}"',
                             shell=True, cwd=str(drive_root))
        else:
            core.open_in_os(bat)
        core.log("scripts", f"launched {bat.name}", "INFO")
        ui.ok(f"Launched {bat.name} in a new window.")
    except Exception as exc:
        ui.err(f"Could not launch: {exc}")


def script_launcher(ctx=None) -> None:
    ui.clear(); ui.title_bar("Thumbdrive Scripts", "your portable .bat rescue kit")
    scripts_dir = find_scripts_dir()
    if not scripts_dir:
        ui.err("Could not find the USB Scripts folder (looking for "
               f"...\\Scripts\\{MARKER}).")
        ui.dim("Plug in the thumbdrive, or point me at the folder manually.")
        if ui.ask_yesno("Locate the Scripts folder manually?", "Thumbdrive"):
            chosen = ui.ask_directory("Select the folder containing 0_START_HERE.bat")
            if chosen and (Path(chosen) / MARKER).exists():
                cfg = core.load_config()
                cfg["usb_scripts_path"] = chosen
                core.save_config(cfg)
                scripts_dir = Path(chosen)
            else:
                ui.err("That folder doesn't contain the kit."); ui.pause(); return
        else:
            ui.pause(); return

    while True:
        bats = _list_scripts(scripts_dir)
        ui.clear()
        ui.title_bar("Thumbdrive Scripts", str(scripts_dir))
        print()
        for p in bats:
            num, label = _pretty(p.name)
            tag = f"{num:>2}" if num != 9999 else " *"
            print("  " + ui._c(f"[{tag}]", ui.C.BOLD + ui.C.CYN) + f"  {label}")
        print("  " + ui._c("[0]", ui.C.BOLD + ui.C.CYN) + "  Back")
        print()
        ui.dim("Enter a script number to launch it in a new window.")
        choice = ui.prompt("Select number: ")
        if choice == "0" or not choice:
            return
        if not choice.isdigit():
            continue
        target = next((p for p in bats if _pretty(p.name)[0] == int(choice)), None)
        if not target:
            ui.err("No script with that number."); ui.pause(); continue
        _launch(target)
        ui.pause()


def register() -> core.Category:
    cat = core.Category("scripts", "Thumbdrive Scripts")
    cat.add("launch", "Browse & launch the USB .bat kit", script_launcher)
    return cat
