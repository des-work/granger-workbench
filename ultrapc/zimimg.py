"""Index the images *inside* your Kiwix ZIM archives for CLIP image search.

The Knowledge Vault's ZIM files (Wikipedia, Stack Exchange, …) hold millions of
images.  This extracts them directly from the archive with libzim — no dumping
the 124 GB ZIM to disk — CLIP-embeds each on the GPU, and writes an index in the
exact same format as `imgsearch`, so you search them with the ordinary command:

    ultra img index-zim wikipedia_en_simple      # build (resumable)
    ultra img search "the moon"                  # then search like any collection

Opening a result launches the image in your browser via the local kiwix server.

Scale: full English Wikipedia has ~8.2M images (a multi-day, ~8 GB-of-vectors
job); Simple Wikipedia ~325k (a few hours).  Indexing is resumable — it
checkpoints, and a re-run skips what's done — so a long build survives
interruption.  A minimum-size filter drops icons / formula strips / sprites.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

from . import core, imgsearch, knowledge

# image entry types worth indexing (raster photos). SVG needs rasterizing and is
# mostly logos/diagrams; GIF is usually animated UI — both skipped by default.
_KEEP_MIME = {"image/webp", "image/jpeg", "image/png", "image/apng"}
_MIN_BYTES = 1500          # cheap pre-filter: skip tiny icons before decoding
_DEFAULT_MIN_SHORT = 80    # after decode, skip if the SHORT side < this — drops
                           # banners/formula-strips/icons while keeping real photos
_BATCH = 64
_CHECKPOINT_EVERY = 8000   # flush a resumable checkpoint this often (images)

MUTED = imgsearch.MUTED
PAPER = imgsearch.PAPER
AMBER = imgsearch.AMBER
RED = imgsearch.RED
GREENH = "#96cd6e"


def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


# --------------------------------------------------------------------------- #
#  Resolving a ZIM + its server book name
# --------------------------------------------------------------------------- #

def resolve_zim(name_or_path: str) -> Path | None:
    """Accept a full path, a filename, or a stem fragment (e.g. 'simple',
    'wikipedia_en_simple') and return the matching local .zim, or None."""
    p = Path(name_or_path)
    if p.is_file() and p.suffix.lower() == ".zim":
        return p
    zims = knowledge.local_zims()
    frag = name_or_path.lower().replace(".zim", "")
    exact = [z for z in zims if z.stem.lower() == frag]
    if exact:
        return exact[0]
    partial = [z for z in zims if frag in z.stem.lower()]
    return partial[0] if len(partial) == 1 else (partial[0] if partial else None)


def _book_name(zim: Path) -> str:
    """The book id kiwix-serve uses in /content/<book>/ URLs — the ZIM filename
    STEM.  NOT the library.xml `name` attribute: that's a catalog-only alias,
    and building URLs from it 404s every link (the entries are all fine)."""
    return zim.stem


def _content_url(book: str, path: str) -> str:
    return f"{knowledge.BASE}/content/{book}/{urllib.parse.quote(path)}"


def _label(path: str) -> str:
    """Human-readable caption from an image entry path."""
    base = path.rsplit("/", 1)[-1]
    base = urllib.parse.unquote(base).lstrip("!")
    if "." in base:
        base = base.rsplit(".", 1)[0]
    return base.replace("_", " ").strip() or path


# --------------------------------------------------------------------------- #
#  Enumerate image entries
# --------------------------------------------------------------------------- #

def scan_images(archive, min_bytes: int = _MIN_BYTES) -> list[tuple[str, int]]:
    """Return [(path, size)] for every keep-worthy image entry in the archive.
    Fast (libzim iterates in C++); the size pre-filter skips obvious chrome."""
    out = []
    getter = archive._get_entry_by_id
    for i in range(archive.all_entry_count):
        e = getter(i)
        if e.is_redirect:
            continue
        it = e.get_item()
        mt = it.mimetype.split(";")[0]
        if mt in _KEEP_MIME:
            sz = it.size
            if sz >= min_bytes:
                out.append((e.path, sz))
    return out


def _decode(archive, path: str, min_short: int):
    """ZIM bytes -> RGB PIL image, or None if unreadable / too small.  Filtering
    on the SHORT side drops banners and formula strips (e.g. 487×52) that a
    long-side filter would keep."""
    try:
        import io
        from PIL import Image
        data = bytes(archive.get_entry_by_path(path).get_item().content)
        img = Image.open(io.BytesIO(data))
        img.load()
        if min(img.size) < min_short:
            return None
        return img.convert("RGB")
    except Exception:
        return None


# --------------------------------------------------------------------------- #
#  Build
# --------------------------------------------------------------------------- #

def _write_info(d: Path, info: dict) -> None:
    core.write_atomic(d / "info.json", json.dumps(info, indent=2))


def build_from_zim(zim: Path, name: str | None = None, limit: int | None = None,
                   min_short: int = _DEFAULT_MIN_SHORT, model: str | None = None,
                   progress=None) -> dict:
    """Stream every image in `zim` through CLIP into a resumable on-disk index.

    Vectors append to vectors.f16 (raw float16) and metadata to meta.jsonl — so
    memory stays flat no matter how many millions of images there are.  Progress
    is checkpointed by a cursor into the (deterministic) image list; a re-run
    truncates any half-written tail back to the last checkpoint and resumes."""
    import numpy as np
    from libzim.reader import Archive

    model = model or imgsearch._configured_model()
    clip = imgsearch._get_clip(model)
    if clip is None:
        raise RuntimeError("CLIP model not available — install transformers/Pillow")

    book = _book_name(zim)
    name = name or zim.stem
    d = imgsearch._dir(name)
    d.mkdir(parents=True, exist_ok=True)
    imgsearch._INDEX_CACHE.pop(name, None)

    vec_path = d / "vectors.f16"
    meta_path = d / "meta.jsonl"
    info_path = d / "info.json"
    off_path = d / "meta_offsets.npy"

    archive = Archive(zim)
    todo = scan_images(archive)          # deterministic order (entry-id sorted)
    if limit:
        todo = todo[:limit]
    if not todo:
        raise RuntimeError(f"No indexable images found in {zim.name}")

    # ---- resume if a matching partial build exists ------------------------- #
    cursor = 0        # how many todo items consumed (incl. skips)
    count = 0         # rows actually written
    dim = 0
    skipped = 0
    if info_path.exists() and vec_path.exists() and meta_path.exists():
        try:
            prev = json.loads(info_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
        if (prev.get("source") == f"zim:{zim.name}"
                and prev.get("model") == model and prev.get("dim")):
            cursor = int(prev.get("cursor", 0))
            count = int(prev.get("count", 0))
            dim = int(prev["dim"])
            skipped = int(prev.get("skipped", 0))
            # drop any bytes/lines written past the last good checkpoint
            with open(vec_path, "r+b") as vf:
                vf.truncate(count * dim * 2)
            _truncate_lines(meta_path, count)
            off_path.unlink(missing_ok=True)
    if cursor == 0:                      # fresh build — start clean
        vec_path.write_bytes(b"")
        meta_path.write_text("", encoding="utf-8")
        off_path.unlink(missing_ok=True)
        count = 0

    total = len(todo)
    t0 = time.time()
    since_ckpt = 0
    vf = open(vec_path, "ab")
    mf = open(meta_path, "a", encoding="utf-8")

    def _info(partial: bool) -> dict:
        return {"name": name, "source": f"zim:{zim.name}", "book": book,
                "model": model, "dim": dim, "count": count, "total": total,
                "cursor": cursor, "skipped": skipped, "partial": partial,
                "min_short": min_short,
                "built": datetime.now().isoformat(timespec="seconds"),
                "seconds": round(time.time() - t0, 1)}

    def _flush_checkpoint():
        vf.flush(); os.fsync(vf.fileno())
        mf.flush(); os.fsync(mf.fileno())
        _write_info(d, _info(True))

    try:
        for i in range(cursor, total, _BATCH):
            batch = todo[i:i + _BATCH]
            imgs, metas = [], []
            for path, sz in batch:
                img = _decode(archive, path, min_short)
                if img is None:
                    skipped += 1
                    continue
                imgs.append(img)
                metas.append({"file": _label(path),
                              "abs": _content_url(book, path),
                              "hash": f"{book}/{path}"})
            if imgs:
                vecs, kept_m, enc_skipped = imgsearch._embed_images_resilient(
                    clip, imgs, metas)
                skipped += enc_skipped
                if vecs is not None:
                    if dim == 0:
                        dim = int(vecs.shape[1])
                    rows = np.ascontiguousarray(vecs, dtype=np.float16)
                    vf.write(rows.tobytes())
                    for m in kept_m:
                        mf.write(json.dumps(m, ensure_ascii=False) + "\n")
                    count += len(kept_m)
                    since_ckpt += len(kept_m)
            cursor = min(i + _BATCH, total)
            if progress:
                progress(cursor, total)
            if since_ckpt >= _CHECKPOINT_EVERY:
                _flush_checkpoint()
                since_ckpt = 0
    finally:
        vf.close(); mf.close()

    if count == 0:
        raise RuntimeError("No images could be decoded")

    # finalize: byte-offset index for lazy meta lookup + non-partial info
    _write_offsets(meta_path, off_path)
    info = _info(False)
    _write_info(d, info)
    imgsearch._INDEX_CACHE.pop(name, None)
    core.log("zimimg", f"indexed '{name}' from {zim.name}: {count} images "
                       f"({skipped} skipped) in {info['seconds']}s", "SUCCESS")
    return info


def _truncate_lines(path: Path, keep: int) -> None:
    """Truncate a text file to its first `keep` lines (drops a partial tail)."""
    if keep <= 0:
        path.write_text("", encoding="utf-8")
        return
    seen = 0
    with open(path, "rb") as f:
        while seen < keep:
            line = f.readline()
            if not line:
                break
            seen += 1
        cut = f.tell()
    with open(path, "r+b") as f:
        f.truncate(cut)


def _write_offsets(meta_path: Path, off_path: Path) -> None:
    """Record the byte offset of each JSONL line so search can seek to any
    row's metadata without loading the whole file."""
    import numpy as np
    offs, pos = [], 0
    with open(meta_path, "rb") as f:
        for line in f:
            offs.append(pos)
            pos += len(line)
    imgsearch._save_npy_atomic(off_path, np.asarray(offs, dtype=np.int64))


def repair_urls(name: str) -> dict | None:
    """Rewrite a ZIM collection's stored URLs to the server's real book id.

    Early builds baked the library.xml `name` into every `abs` URL; kiwix-serve
    actually serves content under the ZIM filename stem, so those links 404'd
    even though every entry is present.  This streams meta.jsonl through a
    temp file swapping the book prefix, rebuilds the byte-offset index, and
    updates info.json — metadata only, the 7 GB of vectors are untouched.

    Returns the updated info dict if a rewrite happened, None if the
    collection isn't ZIM-backed or already uses the correct book id."""
    d = imgsearch._dir(name)
    info_path, meta_path = d / "info.json", d / "meta.jsonl"
    if not (info_path.exists() and meta_path.exists()):
        return None
    info = json.loads(info_path.read_text(encoding="utf-8"))
    src = str(info.get("source", ""))
    if not src.startswith("zim:"):
        return None
    correct = Path(src[4:]).stem
    old = str(info.get("book", ""))
    if not old or old == correct:
        return None

    # drop any cached reader first — its open meta.jsonl handle would block
    # the os.replace on Windows
    cached = imgsearch._INDEX_CACHE.pop(name, None)
    if cached is not None and hasattr(cached[1], "close"):
        cached[1].close()

    old_abs, new_abs = f"/content/{old}/", f"/content/{correct}/"
    old_hash = f"{old}/"
    tmp = d / "meta.jsonl.tmp"
    with open(meta_path, "r", encoding="utf-8") as fin, \
         open(tmp, "w", encoding="utf-8") as fout:
        for line in fin:
            m = json.loads(line)
            a = m.get("abs")
            if isinstance(a, str):
                m["abs"] = a.replace(old_abs, new_abs, 1)
            h = m.get("hash")
            if isinstance(h, str) and h.startswith(old_hash):
                m["hash"] = f"{correct}/" + h[len(old_hash):]
            fout.write(json.dumps(m, ensure_ascii=False) + "\n")
        fout.flush(); os.fsync(fout.fileno())
    os.replace(tmp, meta_path)
    _write_offsets(meta_path, d / "meta_offsets.npy")
    info["book"] = correct
    _write_info(d, info)
    core.log("zimimg", f"repaired '{name}' URLs: book {old} -> {correct}",
             "SUCCESS")
    return info


# --------------------------------------------------------------------------- #
#  CLI (invoked via `ultra img index-zim ...`)
# --------------------------------------------------------------------------- #

def cli_index(args: list[str]) -> int:
    ca, blue, green = _theme()
    target, name, limit = None, None, None
    min_short, model = _DEFAULT_MIN_SHORT, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--name" and i + 1 < len(args):
            name = args[i + 1]; i += 2
        elif a == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        elif a == "--min-size" and i + 1 < len(args):
            min_short = int(args[i + 1]); i += 2
        elif a == "--model" and i + 1 < len(args):
            model = args[i + 1]; i += 2
        else:
            target = a; i += 1

    if not target:
        print("usage: ultra img index-zim <zim-name> [--name N] [--limit K] "
              "[--min-size PX]")
        print("  e.g. ultra img index-zim wikipedia_en_simple")
        zims = knowledge.local_zims()
        if zims:
            print("\n  available ZIMs:")
            for z in zims:
                print(f"    {z.stem}")
        return 2

    zim = resolve_zim(target)
    if zim is None:
        print(ca.color(f"  ✕ no ZIM matching '{target}' "
                       "(try `ultra kb-status`)", RED))
        return 1

    try:
        from libzim.reader import Archive  # noqa: F401
    except ImportError:
        print(ca.color("  ✕ libzim not installed — run:", RED))
        print(ca.color("     python -m pip install libzim", MUTED))
        return 1

    from . import vmath
    print()
    print(ca.color(f"  ▸ ZIM image indexer · {zim.stem}", green)
          + ca.color(f"   ({vmath.backend()})", MUTED))
    print(ca.gradient("  " + "─" * 66, blue, green))

    def _prog(done, total):
        pct = done * 100 // total if total else 100
        print(f"\r  embedding {done}/{total} images ({pct}%)  ", end="",
              flush=True)

    try:
        info = build_from_zim(zim, name=name, limit=limit, min_short=min_short,
                              model=model, progress=_prog)
    except KeyboardInterrupt:
        print(ca.color("\n  ⏸ interrupted — progress was checkpointed; re-run to "
                       "resume", AMBER)); return 130
    except Exception as exc:
        print(ca.color(f"\n  ✕ {exc}", RED)); return 1

    print()
    print(ca.color(f"  ✓ {info['count']:,} images indexed "
                   f"({info['skipped']:,} skipped) in "
                   f"{info['seconds']:,.0f}s", green))
    print(ca.color(f"    search it:  ultra img search "
                   '"<description>"', MUTED))
    return 0
