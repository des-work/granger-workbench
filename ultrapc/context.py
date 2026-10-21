"""Context capsule — one file that packages a project's essence so a fresh
Claude session skips 15+ minutes of exploration.

Contents (in one .md file):
  - Project name + when generated
  - README extract (first ~2500 chars)
  - File tree (relative, non-huge, non-vendored)
  - Code map (files + function/class signatures, ~34× smaller than raw source)
  - Recent commits (if it's a git repo)
  - Task-relevant snippets from YOUR OWN codebase (via coderag)

    python ultra.py context                        # ./context.md for the CWD
    python ultra.py context "add jwt auth"         # + task-relevant snippets
    python ultra.py context --dir C:\\proj\\x       # a different project
    python ultra.py context --out here.md          # custom output path
"""

from __future__ import annotations

import time
from pathlib import Path

from . import core

try:
    from .reader import code_map, CODE_EXTS, SKIP_DIRS, DOC_EXTS
except Exception:
    CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".sh", ".sql"}
    SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "dist", "build",
                 "__pycache__", ".next", "target", ".cache"}
    DOC_EXTS = {".md", ".txt", ".rst"}
    def code_map(path):        # pragma: no cover
        return "(code_map unavailable)\n"


def _readme(root: Path, cap: int = 2500) -> str:
    for name in ("README.md", "README.rst", "README.txt", "README"):
        p = root / name
        if p.exists():
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                return text[:cap] + ("\n…(truncated)" if len(text) > cap else "")
            except OSError:
                pass
    return "(no README found)"


def _tree(root: Path, cap: int = 100) -> list[str]:
    """List files worth mentioning: not in vendored/cache dirs, not huge."""
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            if p.stat().st_size > 500_000:
                continue
        except OSError:
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        files.append(rel)
        if len(files) >= cap:
            files.append(f"…(+{sum(1 for _ in root.rglob('*'))-cap} more)")
            break
    return files


def _git_log(root: Path, n: int = 10) -> str:
    if not (root / ".git").exists():
        return ""
    out = core.run(["git", "-C", str(root), "log", f"-{n}", "--oneline",
                    "--decorate=short"], timeout=15)
    return out or ""


def _git_status(root: Path) -> str:
    if not (root / ".git").exists():
        return ""
    out = core.run(["git", "-C", str(root), "status", "--short"], timeout=10)
    return out or ""


def _task_slice(task: str, root: Path) -> str:
    """Run coderag search for the task; return top-5 excerpts. Silent on failure."""
    if not task:
        return ""
    try:
        from . import coderag, ai
    except Exception:
        return ""
    if not coderag.available():
        return ("(codebase RAG unavailable — start Ollama + `ollama pull "
                "nomic-embed-text` to enable task-relevant snippets)")
    # index this project if we haven't yet (or if the index is for another repo)
    from .coderag import _load
    idx = _load()
    if not idx or Path(idx.get("root", "")) != root:
        try:
            print(f"  indexing {root.name} for task-relevant lookup…")
            coderag.index(str(root))
        except Exception as exc:
            return f"(could not index: {exc})"
    r = coderag.search(task, top=5)
    if "error" in r or not r.get("hits"):
        return ""
    out = [f"### For task: {task!r} — most relevant existing code"]
    for score, rec in r["hits"]:
        out.append(f"\n**{rec['path']}:{rec['start']}**  _(score {score:.2f})_")
        out.append("```\n" + rec["text"][:900] + "\n```")
    return "\n".join(out)


def build(cwd: str | Path = ".", task: str = "") -> str:
    root = Path(cwd).expanduser().resolve()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"# {root.name} — context capsule",
             f"_generated {now} · use this instead of exploring the whole repo_",
             "",
             "## What this is",
             _readme(root),
             "",
             "## File tree",
             "```", *_tree(root), "```", ""]

    # code map (structural — signatures only)
    has_code = any((root / f).exists() for f in ["ultra.py", "src", "app.py"]) \
               or any(root.rglob("*.py")) or any(root.rglob("*.ts")) \
               or any(root.rglob("*.js"))
    if has_code:
        parts += ["## Code map (files + signatures, no bodies)",
                  code_map(str(root)), ""]

    # git activity
    log = _git_log(root)
    if log:
        parts += ["## Recent commits", "```", log, "```", ""]
    stat = _git_status(root)
    if stat.strip():
        parts += ["## Working tree", "```", stat, "```", ""]

    # task-relevant existing code
    if task:
        slice_txt = _task_slice(task, root)
        if slice_txt:
            parts += ["## Task context", slice_txt, ""]

    parts += ["---",
              f"_Ultra-PC context capsule · paste this at the start of a chat "
              f"so the assistant skips exploration._"]
    return "\n".join(parts)


def cmd_context(cwd: str = ".", task: str = "", out: str = "") -> int:
    text = build(cwd, task)
    dest = Path(out or "context.md").expanduser()
    dest.write_text(text, encoding="utf-8")
    chars = len(text)
    print(f"Wrote context capsule -> {dest}")
    print(f"  {chars:,} chars  (~{chars // 4:,} tokens)")
    print(f"  Paste this file at the start of a Claude session to skip "
          f"exploration.")
    return 0


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() != "context":
        return None
    rest = argv[1:]
    cwd, out, task_parts = ".", "", []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--dir" and i + 1 < len(rest):
            cwd = rest[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(rest):
            out = rest[i + 1]; i += 2
        else:
            task_parts.append(a); i += 1
    return cmd_context(cwd, " ".join(task_parts), out)
