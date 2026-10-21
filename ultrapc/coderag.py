"""Codebase RAG — semantic search over YOUR own repos so "reuse my existing X"
finds real code instead of regenerating it. Reuses the local Ollama embedding
model already wired up for the Knowledge Vault (ultrapc/ai.py). Fully offline.

    python ultra.py code-index "C:\\path\\to\\projects"   # build/update the index
    python ultra.py code-search "jwt auth middleware"     # find matching code
    python ultra.py code-status

Index is a JSON file of {path, start_line, end_line, text, vec}. Degrades
gracefully (clear message) if Ollama / an embedding model isn't available.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import ai, core, ui
from . import assets

RAG_DIR = assets.ASSETS_DIR / "code-rag"
INDEX = RAG_DIR / "index.json"

CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb",
             ".php", ".c", ".h", ".cpp", ".cs", ".swift", ".kt", ".sh", ".sql",
             ".css", ".scss", ".html", ".vue", ".svelte", ".lua", ".r", ".md"}
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "dist", "build", "__pycache__",
             ".next", ".nuxt", "target", "vendor", ".cache", "coverage", ".idea"}
MAX_FILE_BYTES = 400_000  # generous: includes hand-authored data modules like assets.py
MAX_CHUNKS = 8000            # safety ceiling for a single index run


def available() -> bool:
    return ai.available() and ai.embed_model() is not None


# --------------------------------------------------------------------------- #
#  Chunking + indexing
# --------------------------------------------------------------------------- #

def _chunk_file(text: str, window: int = 40, step: int = 30):
    """Yield (start_line, end_line, chunk_text) sliding windows over lines."""
    lines = text.splitlines()
    if not lines:
        return
    i = 0
    n = len(lines)
    while i < n:
        seg = lines[i:i + window]
        if any(ln.strip() for ln in seg):
            yield i + 1, min(i + window, n), "\n".join(seg)
        i += step


def _iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in CODE_EXTS:
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield p


def index(root_dir: str, batch: int = 64) -> dict:
    """Walk `root_dir`, embed code chunks, write the index. Returns a summary."""
    if not available():
        return {"error": "Ollama embedding model unavailable. Start Ollama and "
                         "pull nomic-embed-text (`ollama pull nomic-embed-text`)."}
    root = Path(root_dir).expanduser()
    if not root.exists():
        return {"error": f"path not found: {root}"}
    RAG_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    pending: list[dict] = []
    files = 0

    em = ai.embed_model()

    def flush():
        if not pending:
            return
        vecs = ai.embed([ai._prefixed(em, "search_document", r["text"]) for r in pending], em)
        if vecs and len(vecs) == len(pending):
            for r, v in zip(pending, vecs):
                r["vec"] = v
                records.append(r)
        pending.clear()

    for fp in _iter_files(root):
        files += 1
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(fp.relative_to(root))
        for start, end, chunk in _chunk_file(text):
            pending.append({"path": rel, "start": start, "end": end, "text": chunk})
            if len(pending) >= batch:
                flush()
            if len(records) >= MAX_CHUNKS:
                break
        if len(records) >= MAX_CHUNKS:
            break
    flush()

    data = {"root": str(root), "model": em, "prefixed": True,
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files": files, "chunks": len(records), "records": records}
    core.write_atomic(INDEX, json.dumps(data))
    core.log("coderag", f"indexed {len(records)} chunks from {files} files", "SUCCESS")
    return {"root": str(root), "files": files, "chunks": len(records)}


# --------------------------------------------------------------------------- #
#  Search
# --------------------------------------------------------------------------- #

def _load() -> dict | None:
    if not INDEX.exists():
        return None
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception:
        return None


def search(query: str, top: int = 6) -> dict:
    data = _load()
    if not data:
        return {"error": "No index yet. Run: code-index <dir>"}
    if not available():
        return {"error": "Ollama embedding model unavailable."}
    em = ai.embed_model()
    warn = None
    if data.get("model") and em and data["model"] != em:
        warn = (f"Index was built with '{data['model']}' but current embed model "
                f"is '{em}'. Results may be poor — re-run: code-index {data['root']}")
    q_in = ai._prefixed(em, "search_query", query) if data.get("prefixed") else query
    qv = ai.embed([q_in], em)
    if not qv:
        return {"error": "Failed to embed the query."}
    qv = qv[0]
    scored = [(ai._cosine(qv, r["vec"]), r) for r in data["records"] if r.get("vec")]
    # _cosine returns 0.0 for dimension mismatch, so a swapped model won't crash.
    scored.sort(key=lambda x: x[0], reverse=True)
    return {"root": data["root"], "hits": scored[:top], "warn": warn}


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def cmd_index(root_dir: str) -> int:
    print(f"Indexing {root_dir} (embedding locally, this can take a minute)...")
    r = index(root_dir)
    if "error" in r:
        print("  " + r["error"]); return 1
    print(f"Indexed {r['chunks']} chunks from {r['files']} files.")
    print(f"  index: {INDEX}")
    return 0


def cmd_search(query: str, top: int = 6) -> int:
    if not query:
        print("usage: code-search \"<query>\""); return 2
    r = search(query, top)
    if "error" in r:
        print("  " + r["error"]); return 1
    if r.get("warn"):
        print("  \x1b[93m[warn]\x1b[0m " + r["warn"] + "\n")
    if not r["hits"]:
        print("  no matches."); return 1
    print(f"Top matches in {r['root']}:\n")
    for score, rec in r["hits"]:
        loc = f"{rec['path']}:{rec['start']}"
        print(f"  \x1b[1m{loc}\x1b[0m  \x1b[2m(score {score:.2f})\x1b[0m")
        preview = [ln for ln in rec["text"].splitlines() if ln.strip()][:3]
        for ln in preview:
            print(f"      {ln[:96]}")
        print()
    return 0


def cmd_status() -> int:
    data = _load()
    print(f"Code-RAG index: {INDEX}")
    print(f"  Ollama embed model: {ai.embed_model() or '(none — start Ollama)'}")
    if data:
        print(f"  root: {data['root']}")
        print(f"  {data['chunks']} chunks from {data['files']} files "
              f"(built {data.get('generated','?')})")
    else:
        print("  no index yet — run: code-index <dir>")
    return 0


# --------------------------------------------------------------------------- #
#  Menu tools (registered by devkit) + dispatch
# --------------------------------------------------------------------------- #

def _tool_index(ctx=None) -> None:
    ui.title_bar("Code Search — Index a codebase")
    if not available():
        ui.warn("Ollama + an embedding model (nomic-embed-text) is required.")
        ui.dim("Start Ollama, then: ollama pull nomic-embed-text")
        ui.pause(); return
    d = ui.ask_directory("Choose your projects / repo folder")
    if not d:
        ui.pause(); return
    cmd_index(d)
    ui.pause()


def _tool_search(ctx=None) -> None:
    ui.title_bar("Code Search — Search your repos")
    q = ui.prompt("search your code for: ").strip()
    if q:
        print()
        cmd_search(q)
    ui.pause()


def handle(argv: list[str]) -> int | None:
    if not argv:
        return None
    cmd = argv[0].lower()
    rest = argv[1:]
    if cmd == "code-index":
        if not rest:
            print("usage: code-index <dir>"); return 2
        return cmd_index(rest[0])
    if cmd == "code-search":
        return cmd_search(" ".join(rest))
    if cmd == "code-status":
        return cmd_status()
    return None
