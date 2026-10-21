"""`ultra prime "<task>"` — the session primer. One command that bundles
everything an AI coding session needs to START WORKING on a task, so it skips
the expensive exploration phase entirely.

The economics: a cold session spends ~20-30K tokens opening the README, listing
folders, and reading 3-5 files just to orient. A primer delivers the same
orientation — but task-focused and pre-digested — in ~3-6K tokens, and it does
it by COMPOSING tools that already exist:

    context.build     project capsule (readme + tree + recent commits)
    coderag.search    semantic 'where in the code is this task?' → file:line
    context.code_map  signatures of the files that matter (structure, not source)
    devkit.SNIPPETS   reusable code already on hand (don't regenerate it)
    git               what's been happening + what's dirty right now

    ultra prime "add rate limiting to the API"      # print the primer
    ultra prime "fix the ingest dedup" --out p.md    # also write a file
    ultra prime "<task>" --code 8 --snips 8          # widen the pulls

Works in ANY repo (point code-search at it first with `ultra code-index <dir>`).
House conventions come from `.ultra/conventions.md` if present, else a baked
Ultra-PC default — so the session matches your style without re-deriving it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import core

MUTED, PAPER, GREEN = "#8fb8cf", "#eaf6ff", "#96cd6e"

# Baked house conventions used when a repo has no .ultra/conventions.md.
# Tuned for Ultra-PC; other repos should drop in their own file.
_DEFAULT_CONVENTIONS = """\
- Python 3.11 is the runtime — run tests/scripts with `py -3.11`, never bare `python`.
- Important state files are written with `core.write_atomic` (temp→fsync→replace), never plain write_text.
- Animation (spinners, in-place progress) is gated on `cliart.TTY`; piped runs print one clean line.
- Every feature ships with a smoke test; run `py -3.11 tests/smoke.py` before committing.
- CLI output is themed via `cliart` (gradient/color); reuse the existing helpers, don't hand-roll ANSI.
- Reuse before regenerate: check `ultra snip`, `ultra code-search`, and the design vault first.
- Graceful degradation: optional deps (numpy/PIL/torch/ollama) may be absent — never hard-crash on import."""


def _run_git(root: Path, *args: str) -> str:
    try:
        # git emits UTF-8 (commit messages have em-dashes); decode it as such
        # rather than the Windows locale codepage, which mojibakes them
        return subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=10).stdout.strip()
    except Exception:
        return ""


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2}


_STOP = {"the", "and", "for", "add", "fix", "make", "with", "into", "that",
         "this", "from", "use", "using", "how", "why", "what", "when", "get",
         "set", "new", "our", "can", "should", "want", "need", "code"}


def _match_snippets(task: str, limit: int) -> list[tuple[str, dict]]:
    """Rank the snippet library by keyword overlap with the task."""
    from . import devkit
    keys = _tokens(task) - _STOP
    scored = []
    for sid, s in devkit.SNIPPETS.items():
        hay = _tokens(f"{sid} {s.get('lang','')} {' '.join(s.get('tags',[]))} "
                      f"{s.get('desc','')}")
        overlap = len(keys & hay)
        if overlap:
            scored.append((overlap, sid, s))
    scored.sort(key=lambda x: -x[0])
    return [(sid, s) for _, sid, s in scored[:limit]]


def _match_stacks(task: str) -> list[tuple[str, dict]]:
    from . import devkit
    keys = _tokens(task) - _STOP
    out = []
    for sid, s in getattr(devkit, "STACKS", {}).items():
        hay = _tokens(f"{sid} {' '.join(s.get('tags', []))} {s.get('desc','')}")
        if keys & hay:
            out.append((sid, s))
    return out[:4]


def _code_hits(task: str, top: int) -> tuple[str, list, str | None]:
    """(indexed-root, [(score, record)…], warning) from the code-RAG index."""
    from . import coderag
    res = coderag.search(task, top=top)
    if "error" in res:
        return "", [], res["error"]
    return res.get("root", ""), res.get("hits", []), res.get("warn")


def _first_signature(text: str) -> str:
    """The most identifying line of a code chunk — a def/class if present."""
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        if re.match(r"\s*(def |class |async def |function |export |const |"
                    r"public |private |type |interface )", ln):
            return ln.strip()[:100]
    return (lines[0].strip()[:100] if lines else "")


def build_primer(task: str, cwd: str | Path = ".", top_code: int = 6,
                 top_snips: int = 6) -> str:
    root = Path(cwd).resolve()
    L: list[str] = []
    L.append(f"# Session primer — {root.name}")
    L.append(f"\n**Task:** {task}\n")

    # -- orientation (compact) ------------------------------------------- #
    from . import context
    readme = context._readme(root, cap=900).strip()
    L.append("## Orientation")
    if readme:
        L.append(readme.split("\n\n")[0][:600])
    entry = next((f for f in ("ultra.py", "main.py", "app.py", "index.js",
                              "src/index.ts", "manage.py", "Cargo.toml",
                              "pyproject.toml", "package.json")
                  if (root / f).exists()), None)
    if entry:
        L.append(f"\n- Entry / manifest: `{entry}`")

    # -- where the work is (the killer section) -------------------------- #
    ir, hits, warn = _code_hits(task, top_code)
    L.append("\n## Where the work likely is")
    if warn and not hits:
        L.append(f"_(code-search unavailable: {warn})_\n"
                 "Fall back to `ultra code-search` after `ultra code-index "
                 f"{root}`.")
    elif not hits:
        L.append("_(no code index yet — run `ultra code-index "
                 f"{root}` once to unlock this section)_")
    else:
        if warn:
            L.append(f"> ⚠ {warn}\n")
        if ir and Path(ir).resolve() != root:
            L.append(f"> note: code index covers `{ir}`, not this folder.\n")
        seen_files: list[str] = []
        for score, r in hits:
            loc = f"{r['path']}:{r['start']}-{r['end']}"
            L.append(f"- `{loc}` — {_first_signature(r['text'])}  "
                     f"_(rel {score:.2f})_")
            if r["path"] not in seen_files:
                seen_files.append(r["path"])

        # -- structure of the top files (signatures, not source) --------- #
        L.append("\n## Structure of the files that matter")
        base = Path(ir) if ir else root
        for rel in seen_files[:4]:
            fp = base / rel
            try:
                cm = context.code_map(str(fp))
            except Exception:
                cm = ""
            if cm:
                L.append(f"\n### {rel}\n```\n{cm.strip()[:1400]}\n```")

    # -- reusable assets on hand ----------------------------------------- #
    snips = _match_snippets(task, top_snips)
    stacks = _match_stacks(task)
    if snips or stacks:
        L.append("\n## Reusable assets — don't regenerate these")
        for sid, s in snips:
            L.append(f"- snippet `{sid}` [{s.get('lang','')}] — "
                     f"{s.get('desc','')}  → `ultra snip show {sid}`")
        for sid, s in stacks:
            L.append(f"- scaffold `{sid}` — {s.get('desc','')}  → "
                     f"`ultra stacks new {sid} <dir>`")

    # -- recent activity ------------------------------------------------- #
    if (root / ".git").exists():
        log = _run_git(root, "log", "--oneline", "-6")
        branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
        dirty = _run_git(root, "status", "--porcelain")
        L.append("\n## Recent activity")
        if branch:
            L.append(f"- branch: `{branch}`")
        if log:
            L.append("- last commits:\n```\n" + log + "\n```")
        if dirty:
            # porcelain lines are 'XY path' (or 'R  old -> new'); take the
            # path robustly rather than a fixed slice
            files = []
            for ln in dirty.splitlines()[:12]:
                p = ln[2:].strip()
                if " -> " in p:
                    p = p.split(" -> ", 1)[1]
                files.append(p)
            L.append("- uncommitted: " + ", ".join(f"`{f}`" for f in files))

    # -- conventions ----------------------------------------------------- #
    conv_file = root / ".ultra" / "conventions.md"
    conv = (conv_file.read_text(encoding="utf-8").strip()
            if conv_file.is_file() else _DEFAULT_CONVENTIONS)
    L.append("\n## House conventions\n" + conv)

    # -- verify ---------------------------------------------------------- #
    test_cmd = ("py -3.11 tests/smoke.py" if (root / "tests" / "smoke.py").exists()
                else "pytest" if (root / "tests").exists()
                else "npm test" if (root / "package.json").exists() else None)
    if test_cmd:
        L.append(f"\n## Verify\nRun before committing: `{test_cmd}`")

    return "\n".join(L) + "\n"


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() not in ("prime", "primer", "session"):
        return None
    from . import cliart as ca
    args = argv[1:]
    task_parts, out, top_code, top_snips, cwd = [], "", 6, 6, "."
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out" and i + 1 < len(args):
            out = args[i + 1]; i += 2
        elif a == "--code" and i + 1 < len(args):
            top_code = int(args[i + 1]); i += 2
        elif a in ("--snips", "--snippets") and i + 1 < len(args):
            top_snips = int(args[i + 1]); i += 2
        elif a in ("--cwd", "--dir") and i + 1 < len(args):
            cwd = args[i + 1]; i += 2
        else:
            task_parts.append(a); i += 1
    task = " ".join(task_parts).strip()
    if not task:
        print('usage: ultra prime "<task>" [--out file.md] [--code N] '
              "[--snips N] [--cwd dir]")
        return 2

    primer = build_primer(task, cwd, top_code, top_snips)
    print(primer)
    approx = len(primer) // 4
    if out:
        core.write_atomic(Path(out).expanduser(), primer)
    tail = ca.color(f"\n[primer ≈ {approx:,} tokens — paste this to start a "
                    "session hot instead of exploring cold]", MUTED)
    if out:
        tail += ca.color(f"\n[written to {out}]", GREEN)
    print(tail)
    return 0
