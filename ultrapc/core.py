"""Core plumbing: paths, config, report writing, logging, and command runners.

Everything else in Ultra-PC builds on this. Kept dependency-free (stdlib only)
so the toolkit always starts, even if optional libraries are missing.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
#  Paths
# --------------------------------------------------------------------------- #

# Project root = the folder that contains ultra.py (parent of this package).
ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "Reports"
CONFIG_PATH = ROOT / "ultra_config.json"
LOG_PATH = REPORTS_DIR / "ultra_log.txt"

COMPUTER = socket.gethostname()


def ensure_dirs() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def timestamp() -> str:
    """Filesystem-safe timestamp, matching the thumbdrive convention."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def write_atomic(path, text: str, encoding: str = "utf-8") -> None:
    """Write a file corruption-safely: write to a temp sibling, flush+fsync,
    then os.replace() (atomic within a folder). A crash mid-write leaves the
    original intact instead of a half-written file — the project's file-write
    principle, applied to state like the search indexes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    try:
        with tmp.open("w", encoding=encoding) as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


# --------------------------------------------------------------------------- #
#  Config
# --------------------------------------------------------------------------- #

DEFAULT_CONFIG = {
    "usb_scripts_path": "",   # cached path to the thumbdrive \Scripts folder
    "media_root": "",         # asset-ingest library root; blank = C:\Ultra-Media
    "tracker_dir": "",        # notes → Work Tracker folder (holds tasks.json)
    "last_report": "",
    "auto_open_reports": False,
    # Local-AI / RAG settings — all model-agnostic so the app keeps working if
    # you swap Ollama models. Blank = auto-detect whatever is installed.
    "use_semantic": True,     # embed+rerank retrieval when an embed model exists
    "chat_model": "",         # pin a chat model, else auto (see ai.default_model)
    "embed_model": "",        # pin an embedding model, else auto-detect
    "num_ctx": 8192,          # context window; lowered automatically for the model
    # GPU cross-encoder reranker (precision boost after hybrid retrieval)
    "use_reranker": True,     # rerank top candidates with a cross-encoder
    "reranker_model": "",     # blank = cross-encoder/ms-marco-MiniLM-L-6-v2
    # CLIP image search (ultra img). Blank = openai/clip-vit-base-patch32 (fast).
    # Set openai/clip-vit-large-patch14 for sharper results (bigger download).
    "clip_model": "",
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            return merged
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    try:
        write_atomic(CONFIG_PATH, json.dumps(cfg, indent=2))
    except Exception:
        pass


# --------------------------------------------------------------------------- #
#  Logging (mirrors the spirit of _log.bat)
# --------------------------------------------------------------------------- #

def log(source: str, message: str, level: str = "INFO") -> None:
    ensure_dirs()
    line = f"[{datetime.now().isoformat(timespec='seconds')}] [{level:<7}] {source}: {message}\n"
    try:
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
#  Reports
# --------------------------------------------------------------------------- #

class Report:
    """Accumulates report text and PASS/WARN/FAIL findings, then synthesizes
    a verdict — the same pattern your triage .bat scripts use, in Python."""

    def __init__(self, title: str):
        self.title = title
        self.lines: list[str] = []
        self.fail = 0
        self.warn = 0
        self.primary_issue: str | None = None
        self.primary_conf = "LOW"
        self._header()

    def _header(self) -> None:
        self.lines += [
            "=" * 60,
            f"  {self.title.upper()}",
            f"  Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"  Computer:  {COMPUTER}",
            f"  User:      {os.getenv('USERNAME') or os.getenv('USER') or '?'}",
            "=" * 60,
            "",
        ]

    def section(self, name: str) -> None:
        self.lines += ["", f"--- {name} ---"]

    def line(self, text: str = "") -> None:
        self.lines.append(text)

    def finding(self, status: str, text: str, conf: str = "MEDIUM",
                issue: str | None = None) -> None:
        """status: PASS | WARN | FAIL | INFO | SKIP."""
        self.lines.append(f"  [{status}] {text}")
        if status == "FAIL":
            self.fail += 1
            if issue and self.primary_issue is None:
                self.primary_issue, self.primary_conf = issue, conf
        elif status == "WARN":
            self.warn += 1
            if issue and self.primary_issue is None and conf == "HIGH":
                self.primary_issue, self.primary_conf = issue, conf

    def verdict(self) -> str:
        self.lines += ["", "=" * 60, "  VERDICT", "=" * 60]
        if self.primary_issue:
            self.lines += [f"  Primary likely issue: {self.primary_issue}",
                           f"  Confidence:           {self.primary_conf}"]
        elif self.fail:
            self.lines.append("  Multiple FAILs found — see report above.")
        elif self.warn > 2:
            self.lines.append("  Multiple WARNs — cumulative factors, review above.")
        else:
            self.lines.append("  No serious issues found.")
        self.lines += [f"  Total FAILs: {self.fail}", f"  Total WARNs: {self.warn}"]
        return self.summary()

    def summary(self) -> str:
        if self.primary_issue:
            return f"{self.primary_issue}  (confidence {self.primary_conf})"
        if self.fail:
            return f"{self.fail} FAIL / {self.warn} WARN — see report."
        if self.warn:
            return f"No critical issues. {self.warn} WARN — see report."
        return "All checks passed."

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    def save(self, slug: str) -> Path:
        ensure_dirs()
        path = REPORTS_DIR / f"{slug}_{COMPUTER}_{timestamp()}.txt"
        path.write_text(self.text(), encoding="utf-8")
        cfg = load_config()
        cfg["last_report"] = str(path)
        save_config(cfg)
        log(slug, f"report saved -> {path.name}", "SUCCESS")
        return path


# --------------------------------------------------------------------------- #
#  Command runners
# --------------------------------------------------------------------------- #

IS_WINDOWS = platform.system() == "Windows"


def run(cmd: list[str], timeout: int = 60) -> str:
    """Run a command, return stdout (stderr appended on failure). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "").rstrip()
        if p.returncode != 0 and p.stderr:
            out = (out + "\n" + p.stderr.strip()).strip()
        return out
    except FileNotFoundError:
        return f"(command not found: {cmd[0]})"
    except subprocess.TimeoutExpired:
        return f"(timed out after {timeout}s)"
    except Exception as exc:  # pragma: no cover - defensive
        return f"(error: {exc})"


def powershell(script: str, timeout: int = 60) -> str:
    """Run a PowerShell one-liner and return its trimmed output."""
    if not IS_WINDOWS:
        return "(PowerShell unavailable on this OS)"
    return run(["powershell", "-NoProfile", "-Command", script], timeout=timeout)


def ps_value(script: str, timeout: int = 30) -> str:
    """PowerShell call expected to yield a single scalar value (first line)."""
    out = powershell(script, timeout).strip()
    return out.splitlines()[0].strip() if out else ""


def have(tool: str) -> bool:
    """True if an executable is on PATH."""
    return shutil.which(tool) is not None


def open_in_os(path: str | Path) -> None:
    """Open a file/folder with the OS default handler."""
    path = str(path)
    try:
        if IS_WINDOWS:
            os.startfile(path)  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as exc:
        log("open_in_os", f"{path}: {exc}", "ERROR")


# --------------------------------------------------------------------------- #
#  Tool registry — modules register their tools here for the menu system
# --------------------------------------------------------------------------- #

@dataclass
class Tool:
    key: str            # short id, e.g. "sysinfo"
    label: str          # menu label
    func: object        # callable(ctx) -> None
    desc: str = ""      # one-line description


@dataclass
class Category:
    key: str
    label: str
    tools: list[Tool] = field(default_factory=list)

    def add(self, key, label, func, desc=""):
        self.tools.append(Tool(key, label, func, desc))
        return func
