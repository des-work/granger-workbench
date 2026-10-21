"""What Granger can actually operate on this machine, beyond answering.

Two jobs:
  * APPS - a registry of real programs with the spoken phrases that should
    reach them, so "open a spreadsheet" or "make a 2D animation of a forest"
    becomes a real command instead of the model claiming it did something.
  * terminal_context() - read what's on screen in the user's tmux panes, so
    "what's this error" / "is it done yet" can be answered from the actual
    output rather than guessed at.

Availability is always checked at call time. A tool that isn't installed
reports that plainly - it never silently does nothing.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

BLENDER = Path(__file__).resolve().parent.parent / ".build/blender-4.5.11-linux-x64/blender"


def _blender_path() -> str | None:
    if BLENDER.is_file():
        return str(BLENDER)
    return shutil.which("blender")


# kind: "gui" launches detached; "term" opens in a terminal window (the tool
# is interactive text); "arg" takes the rest of the sentence as its argument.
APPS: tuple[dict, ...] = (
    {"name": "LibreOffice Writer", "cmd": ["lowriter"], "kind": "gui",
     "phrases": (r"libre\s*office writer", r"\bwriter\b", r"word processor",
                 r"(open|start|new)\s+(a\s+)?document")},
    {"name": "LibreOffice Calc", "cmd": ["localc"], "kind": "gui",
     "phrases": (r"libre\s*office calc", r"\bcalc\b", r"spread ?sheet")},
    {"name": "LibreOffice Impress", "cmd": ["loimpress"], "kind": "gui",
     "phrases": (r"libre\s*office impress", r"\bimpress\b", r"slide ?deck",
                 r"presentation")},
    {"name": "LibreOffice", "cmd": ["libreoffice"], "kind": "gui",
     "phrases": (r"libre\s*office",)},
    # 3D before the 2D/termstage entry: "make a 3D animation of X" must not
    # fall through to terminal art.
    {"name": "3D model", "cmd": ["pc", "make"], "kind": "arg",
     "phrases": (r"(make|create|build|generate)\s+(me\s+)?(a|an|some)?\s*(3d\s+)?model\b",)},
    {"name": "3D animation", "cmd": ["pc", "animate"], "kind": "arg",
     "phrases": (r"(make|create|build|generate|render)\s+(me\s+)?(a|an|some)?\s*"
                 r"(3d|blender)\s+(animation|render|scene)\b",
                 r"(make|create|build|generate|render)\s+(me\s+)?(a|an|some)?\s*"
                 r"animation\s+in\s+blender\b")},
    {"name": "Blender", "cmd": None, "kind": "gui", "resolve": _blender_path,
     "phrases": (r"\bblender\b", r"3d editor")},
    # The "make me one" form has to be matched before the bare launcher,
    # or "generate some terminal art of X" just opens termstage's menu.
    {"name": "termstage scene", "cmd": ["termstage", "create"], "kind": "arg",
     "phrases": (r"(make|create|build|generate)\s+(me\s+)?(a|an|some)?\s*"
                 r"(2d\s+)?(terminal\s+)?(animation|scene|art)\b",)},
    {"name": "termstage", "cmd": ["termstage"], "kind": "term",
     "phrases": (r"\bterm ?stage\b", r"terminal (art|animation)")},
    {"name": "Wireshark", "cmd": ["wireshark"], "kind": "gui",
     "phrases": (r"wire ?shark",)},
    {"name": "VS Code", "cmd": ["code"], "kind": "gui",
     "phrases": (r"\bvs ?code\b", r"\bcode editor\b")},
    # libvirt is not installed on this box yet (no /etc/libvirt, no virsh).
    # Kept here deliberately: the moment it is installed this starts working,
    # and until then a VM request gets an honest "not installed" instead of
    # a model pretending it booted something.
    {"name": "virtual machines", "cmd": ["virt-manager"], "kind": "gui",
     "phrases": (r"\bvirt-?manager\b", r"\bvms?\b", r"virtual machines?")},
)


def _resolve(app: dict) -> list[str] | None:
    """The real command for an app, or None when it isn't installed."""
    if app.get("resolve"):
        found = app["resolve"]()
        return [found] if found else None
    cmd = app["cmd"]
    return cmd if shutil.which(cmd[0]) else None


def find_app(heard: str) -> dict | None:
    """Match a spoken request to an app. Returns the entry plus a resolved
    `command` (None when not installed) and, for "arg" apps, the `subject`
    pulled off the end of the sentence."""
    for app in APPS:
        for pattern in app["phrases"]:
            match = re.search(pattern, heard, re.I)
            if not match:
                continue
            entry = dict(app)
            entry["command"] = _resolve(app)
            if app["kind"] == "arg":
                # everything after the matched verb phrase is the subject:
                # "make a 2d animation of a forest at night" -> "a forest at night"
                rest = heard[match.end():].strip()
                entry["subject"] = re.sub(r"^(of|about|for|showing)\s+", "", rest, flags=re.I).strip()
            return entry
    return None


def launch(app: dict, *, terminal_runner=None) -> str:
    """Start an app. Returns a short line describing what happened - caller
    speaks it. `terminal_runner` opens a text tool in a terminal window
    (easy._launch_in_terminal); without it, "term" apps fall back to GUI-style
    detach."""
    command = app.get("command")
    if not command:
        return f"{app['name']} isn't installed on this machine, so I can't open it."
    if app["kind"] == "arg":
        subject = app.get("subject") or ""
        if not subject:
            return f"I can run {app['name']}, but I didn't catch what it should be of."
        from . import jobs
        kind = {"3D model": "model", "3D animation": "animation", "termstage scene": "terminal-animation"}.get(app["name"])
        if not kind:
            return f"No verified builder is registered for {app['name']}."
        report = jobs.start(kind, subject)
        if report["status"] == "failed":
            return "The build failed to start: " + report.get("error", "unknown error")
        return f"Local {app['name']} job {report['job_id']}: {report['status']}. Check the job before claiming completion."
    if app["kind"] == "term" and terminal_runner:
        terminal_runner(app["name"], command)
        return f"Opening {app['name']} in a terminal."
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    return f"Opening {app['name']}."


# --- what's on screen in the user's terminal -------------------------------

TERMINAL_RE = re.compile(
    r"\b(my terminal|the terminal|terminal output|what('s| is) (running|happening|going on)|"
    r"this (error|output|log)|that (error|output)|the (error|output|log) (above|there)|"
    r"is it (done|finished|running|still going)|did it (finish|work|pass|fail)|"
    r"what does (it|that|this) say|read (my|the) (screen|terminal|output)|"
    r"wireshark|tshark|the capture|my code|the build|the tests?)\b",
    re.I)


def tmux_panes() -> list[tuple[str, str]]:
    """[(pane label, visible text)] for every live tmux pane, newest first.
    Empty when tmux isn't running anything - which is the usual case unless
    the user works inside tmux."""
    if not shutil.which("tmux"):
        return []
    try:
        listed = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", "#{session_name}:#{window_index}.#{pane_index}"],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if listed.returncode != 0:
        return []
    panes = []
    for target in [p for p in listed.stdout.split() if p]:
        try:
            captured = subprocess.run(["tmux", "capture-pane", "-p", "-t", target],
                                      capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if captured.returncode == 0:
            text = captured.stdout.strip()
            if text:
                panes.append((target, text))
    return panes


def terminal_context(max_lines: int = 40) -> str | None:
    """Current terminal contents, trimmed for a prompt. None when there's
    nothing to read, so the caller can say so instead of inventing output."""
    panes = tmux_panes()
    if not panes:
        return None
    blocks = []
    for target, text in panes:
        lines = text.splitlines()[-max_lines:]
        blocks.append(f"[tmux pane {target}]\n" + "\n".join(lines))
    return "\n\n".join(blocks)
