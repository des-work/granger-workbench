"""Backup — snapshot the irreplaceable Ultra-PC data.

The 128 GB of ZIMs, the design vault, and the code are all re-downloadable or in
git. The data that is NOT recoverable if lost is small and personal:

  * your search feedback / ratings          (_ratings.jsonl)
  * saved AI chat sessions                  (_chat_sessions.jsonl)
  * runtime config                          (ultra_config.json)
  * Fix-It solved-cases corpus              (troubleshoot/solved/)  <- self-built
  * your locally-edited troubleshoot docs   (runbooks/cisco/windows/linux)
  * Claude escalation prompts               (Reports/fix-prompt-*.md)

`ultra backup [dest]` zips those into  ~/Ultra-PC-Backups  (or <dest>).

  python ultra.py backup            # -> ~/Ultra-PC-Backups/ultra-backup-<ts>.zip
  python ultra.py backup D:\safe    # custom destination
"""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

from . import core, knowledge

MUTED = "#8fb8cf"
PAPER = "#eaf6ff"
AMBER = "#febc2e"
TROUBLE = knowledge.knowledge_dir() / "troubleshoot"


def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


def _sources() -> list[tuple[Path, str]]:
    """(path, arcname) pairs for everything worth saving that exists."""
    kd = knowledge.knowledge_dir()
    items: list[tuple[Path, str]] = [
        (kd / "_ratings.jsonl", "knowledge/_ratings.jsonl"),
        (kd / "_chat_sessions.jsonl", "knowledge/_chat_sessions.jsonl"),
        (core.CONFIG_PATH, "config/ultra_config.json"),
    ]
    # quick notes (the tracker pipeline's local store — small and personal)
    notes_dir = kd / "notes"
    if notes_dir.exists():
        for f in notes_dir.rglob("*"):
            if f.is_file():
                items.append((f, f"knowledge/notes/{f.relative_to(notes_dir)}"))
    # gallery curation (topics + taste ratings — small, self-built)
    for name in ("gallery_topics.json", "gallery_taste.json"):
        items.append((kd / "imgsearch" / name, f"knowledge/{name}"))
    # Fix-It solved cases + locally-edited troubleshoot docs (may differ from git)
    for sub in ("solved", "runbooks", "cisco", "windows", "linux"):
        d = TROUBLE / sub
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file():
                    items.append((f, f"troubleshoot/{sub}/{f.relative_to(d)}"))
    # Claude escalation prompts
    if core.REPORTS_DIR.exists():
        for f in core.REPORTS_DIR.glob("fix-prompt-*.md"):
            items.append((f, f"reports/{f.name}"))
    return [(p, a) for p, a in items if p.exists()]


def run_backup(dest: str | None = None) -> Path | None:
    """Zip the irreplaceable data. Returns the archive path (None if nothing)."""
    ca, blue, green = _theme()
    out_dir = Path(dest) if dest else (Path.home() / "Ultra-PC-Backups")
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"ultra-backup-{datetime.now():%Y%m%d-%H%M%S}.zip"

    sources = _sources()
    print()
    print(ca.gradient("  ╭─ Ultra-PC backup " + "─" * 47 + "╮", blue, green))
    if not sources:
        print("  " + ca.color("│", blue)
              + ca.color("  nothing to back up yet (no personal data on disk)", AMBER)
              + " " * 14 + ca.color("│", green))
        print(ca.gradient("  ╰" + "─" * 66 + "╯", green, blue))
        return None

    total = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path, arc in sources:
            try:
                z.write(path, arc)
                sz = path.stat().st_size
                total += sz
                line = f"  {arc[:46]:<46} {_fmt(sz):>10}"
                print("  " + ca.color("│", blue) + ca.color(line, PAPER)
                      + " " * max(1, 66 - len(line)) + ca.color("│", green))
            except OSError:
                continue
    zsz = archive.stat().st_size
    print(ca.gradient("  ├" + "─" * 66 + "┤", blue, green))
    summ = f"  {len(sources)} items · {_fmt(total)} raw -> {_fmt(zsz)} zipped"
    print("  " + ca.color("│", blue) + ca.color(summ, green)
          + " " * max(1, 66 - len(summ)) + ca.color("│", green))
    print(ca.gradient("  ╰" + "─" * 66 + "╯", green, blue))
    print(ca.color(f"  ✓ {archive}", green))
    core.log("backup", f"{len(sources)} items -> {archive.name}", "SUCCESS")
    return archive


def _fmt(n: float) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def handle(argv: list[str]) -> int | None:
    """Dispatch `backup [dest]`; None if not ours."""
    if not argv or argv[0].lower() != "backup":
        return None
    dest = argv[1] if len(argv) > 1 else None
    return 0 if run_backup(dest) is not None else 1
