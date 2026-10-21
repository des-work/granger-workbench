"""vindex — a persistent, GPU-searched semantic index over your documents.

The KB chat embeds candidates on the fly from BM25 hits, so its recall is capped
by keyword search. vindex is the opposite: embed a whole document collection
ONCE, keep the vectors, and search them by meaning on the GPU — so a query finds
the right passage even when it shares no keywords with it.

Vectors live in `C:\\Ultra-PC-Knowledge\\vindex\\<name>\\` (float16, compact) and
are searched through `vmath.Index`, which runs on CUDA when a GPU build of torch
is present (a million vectors in ~25 ms on the 4080) and falls back to numpy.

    ultra vindex build <folder> --name notes     # embed a folder of docs
    ultra vindex search notes "how do I rotate the signing key"
    ultra vindex list

Whole-Wikipedia semantic search would need libzim to iterate a ZIM's articles
plus hours of embedding (~58 GB of vectors for 19M articles); the machinery here
is ready for it, but the shipped scope is document folders and text corpora.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from . import ai, core, knowledge

MUTED = "#8fb8cf"
PAPER = "#eaf6ff"
AMBER = "#febc2e"
RED = "#ff5f57"

TEXT_EXTS = {".md", ".txt", ".rst", ".log", ".csv", ".json", ".py", ".markdown"}
DOC_EXTS = {".pdf", ".docx", ".pptx"}       # via reader, if available


def _root() -> Path:
    return knowledge.knowledge_dir() / "vindex"


def _dir(name: str) -> Path:
    return _root() / name


def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


# --------------------------------------------------------------------------- #
#  Chunking + text extraction
# --------------------------------------------------------------------------- #

def _chunk(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


def _extract(path: Path) -> str:
    if path.suffix.lower() in TEXT_EXTS:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""
    if path.suffix.lower() in DOC_EXTS:
        try:
            from . import reader
            return reader.extract(str(path)) or ""
        except Exception:
            return ""
    return ""


def _iter_files(folder: Path):
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.suffix.lower() in (TEXT_EXTS | DOC_EXTS):
            yield p


# --------------------------------------------------------------------------- #
#  Build
# --------------------------------------------------------------------------- #

def build(source: str, name: str | None = None, limit: int | None = None,
          progress=None) -> dict:
    """Embed every document under `source` into a searchable index. Returns info."""
    import numpy as np

    folder = Path(source)
    if not folder.exists():
        raise FileNotFoundError(source)
    if not ai.available():
        raise RuntimeError("Ollama isn't running — start it to embed.")
    em = ai.embed_model()
    if not em:
        raise RuntimeError("No embedding model (ollama pull nomic-embed-text).")
    name = name or folder.name

    metas: list[dict] = []
    texts: list[str] = []
    for f in _iter_files(folder):
        raw = _extract(f)
        if not raw.strip():
            continue
        rel = str(f.relative_to(folder))
        for ci, ch in enumerate(_chunk(raw)):
            metas.append({"file": rel, "chunk": ci, "text": ch[:400]})
            texts.append(ch)
            if limit and len(texts) >= limit:
                break
        if limit and len(texts) >= limit:
            break
    if not texts:
        raise RuntimeError(f"No indexable text found under {folder}")

    # embed in batches (Ollama runs nomic on the GPU); report progress
    vecs: list[list[float]] = []
    B = 64
    t0 = time.time()
    for i in range(0, len(texts), B):
        batch = [f"search_document: {t}" for t in texts[i:i + B]]
        got = ai.embed(batch, model=em)
        if len(got) != len(batch):
            raise RuntimeError("Embedding failed part-way; index not written.")
        vecs.extend(got)
        if progress:
            progress(min(i + B, len(texts)), len(texts))

    arr = np.asarray(vecs, dtype=np.float16)      # half precision -> half the disk
    d = _dir(name)
    d.mkdir(parents=True, exist_ok=True)
    np.save(d / "vectors.npy", arr)
    (d / "meta.json").write_text(json.dumps(metas), encoding="utf-8")
    info = {"name": name, "source": str(folder), "embed_model": em,
            "dim": int(arr.shape[1]), "count": int(arr.shape[0]),
            "built": datetime.now().isoformat(timespec="seconds"),
            "seconds": round(time.time() - t0, 1)}
    core.write_atomic(d / "info.json", json.dumps(info, indent=2))
    core.log("vindex", f"built '{name}': {info['count']} chunks in "
                       f"{info['seconds']}s ({em})", "SUCCESS")
    return info


# --------------------------------------------------------------------------- #
#  Search
# --------------------------------------------------------------------------- #

_CACHE: dict[str, tuple] = {}      # name -> (vmath.Index, metas, info)


def _load(name: str):
    if name in _CACHE:
        return _CACHE[name]
    import numpy as np
    from . import vmath
    d = _dir(name)
    if not (d / "vectors.npy").exists():
        return None
    arr = np.load(d / "vectors.npy").astype(np.float32)
    metas = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    info = json.loads((d / "info.json").read_text(encoding="utf-8"))
    entry = (vmath.Index(arr), metas, info)
    _CACHE[name] = entry
    return entry


def search(name: str, query: str, k: int = 8) -> list[dict]:
    entry = _load(name)
    if entry is None or not ai.available():
        return []
    index, metas, info = entry
    qv = ai.embed([f"search_query: {query}"], model=info.get("embed_model"))
    if not qv:
        return []
    hits = []
    for i, score in index.search(qv[0], k):
        m = metas[i]
        hits.append({"score": round(float(score), 3), "file": m["file"],
                     "chunk": m["chunk"], "text": m["text"]})
    return hits


def list_indexes() -> list[dict]:
    root = _root()
    if not root.exists():
        return []
    out = []
    for d in sorted(root.iterdir()):
        info = d / "info.json"
        if info.is_file():
            try:
                out.append(json.loads(info.read_text(encoding="utf-8")))
            except Exception:
                continue
    return out


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() != "vindex":
        return None
    ca, blue, green = _theme()
    rest = argv[1:]
    sub = rest[0].lower() if rest else "list"

    if sub == "build":
        args = rest[1:]
        source, name, limit = None, None, None
        i = 0
        while i < len(args):
            if args[i] == "--name" and i + 1 < len(args):
                name = args[i + 1]; i += 2
            elif args[i] == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1]); i += 2
            else:
                source = args[i]; i += 1
        if not source:
            print("usage: ultra vindex build <folder> [--name N] [--limit K]")
            return 2

        def _prog(done, total):
            if done % 256 == 0 or done == total:
                ca.loadbar(f"  embedding {done}/{total}", seconds=0.01,
                           c1=blue, c2=green)
        try:
            with ca.Spinner("  scanning + embedding on the GPU", style="dots",
                            c=blue):
                info = build(source, name, limit)
        except Exception as exc:
            print(ca.color(f"  ✕ {exc}", RED)); return 1
        print(ca.color(f"  ✓ indexed {info['count']} chunks from "
                       f"{Path(info['source']).name} in {info['seconds']}s", green))
        print(ca.color(f"    search it:  ultra vindex search {info['name']} "
                       '"<query>"', MUTED))
        return 0

    if sub == "search":
        if len(rest) < 3:
            print('usage: ultra vindex search <name> "<query>"'); return 2
        name, query = rest[1], " ".join(rest[2:])
        from . import vmath
        print()
        print(ca.color(f"  ▸ vindex[{name}] ", green) + ca.color(query, "#ffffff")
              + ca.color(f"   ({vmath.backend()})", MUTED))
        print(ca.gradient("  " + "─" * 66, blue, green))
        hits = search(name, query, 8)
        if not hits:
            print(ca.color("  (no index by that name, or Ollama is down — "
                           "`ultra vindex list`)", AMBER)); return 1
        for h in hits:
            print("   " + ca.color(f"{h['score']:.2f}", green)
                  + ca.color(f"  {h['file']} #{h['chunk']}", "#4fc3f7"))
            print("         " + ca.color(h["text"][:110].replace("\n", " "), MUTED))
        return 0

    # list
    idxs = list_indexes()
    print()
    print(ca.gradient(f"  ╭─ Semantic indexes · {len(idxs)} " + "─" * 40 + "╮",
                      blue, green))
    if not idxs:
        print("  " + ca.color("│", blue) + ca.color(
            "  none yet — ultra vindex build <folder> --name X", MUTED)
            + " " * 17 + ca.color("│", green))
    for it in idxs:
        line = f"  {it['name'][:24]:<24} {it['count']:>7} chunks · {it['embed_model'][:18]}"
        print("  " + ca.color("│", blue) + ca.color(line, PAPER)
              + " " * max(1, 64 - len(line)) + ca.color("│", green))
    print(ca.gradient("  ╰" + "─" * 66 + "╯", green, blue))
    return 0
