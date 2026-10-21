"""CLIP image search — find images by text description or visual similarity.

Uses OpenAI's CLIP model (via the ``transformers`` library, already installed
for the reranker) to encode images and text into the same vector space.  The
same GPU infrastructure that powers text retrieval (vmath.Index on CUDA) runs
the search, so a collection of 50 k images searches in single-digit ms.

    ultra img index ~/Pictures                  # embed all images (GPU)
    ultra img search photos "sunset"            # text → image
    ultra img similar photos photo.jpg          # image → image (reverse)
    ultra img list                              # show indexed collections

Vectors are float16 on disk (same as vindex) at
``C:\\Ultra-PC-Knowledge\\imgsearch\\<name>\\``.

Robustness (why this module is more careful than it looks):
  * **Crash-resumable** — indexing checkpoints atomically every N images, and
    the incremental hash (path+mtime+size) means a re-run skips finished files,
    so an interrupted 10 k-image build resumes instead of restarting.
  * **Atomic writes** — vectors, meta and info are all written temp-then-replace
    (`core.write_atomic` / `_save_npy_atomic`); a crash mid-write leaves the
    previous index intact (the project's file-write principle).
  * **Bad-image tolerant** — EXIF orientation is applied (phone photos embed
    right-side-up), truncated files still load, decompression bombs are capped,
    and a single unreadable image is skipped instead of failing the batch.
  * **Model-consistent** — the query is always encoded with the SAME model the
    images were, because search loads the model named in the index's info.json;
    dimension mismatch is impossible even if you change `clip_model` later.

Graceful degradation: if transformers or Pillow aren't installed, or the model
hasn't downloaded, the CLI says so and exits cleanly.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from . import core

IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
    ".webp", ".ico", ".avif", ".heic", ".heif",
}

MUTED = "#8fb8cf"
PAPER = "#eaf6ff"
AMBER = "#febc2e"
RED = "#ff5f57"
CYAN = "#4fc3f7"

_DEFAULT_MODEL = "openai/clip-vit-base-patch32"

_BATCH = 32
_CHECKPOINT_EVERY = 1000        # flush a resumable checkpoint this often
_MAX_PIXELS = 200_000_000       # decompression-bomb cap (200 MP)

# CLIP was trained on captions like "a photo of X"; averaging a small prompt
# ensemble (including the bare query) sharpens text→image retrieval without the
# variance of betting on one template.  This is what OpenAI did for zero-shot.
_PROMPT_TEMPLATES = ("{}", "a photo of {}", "a picture of {}", "an image of {}")


# --------------------------------------------------------------------------- #
#  Paths
# --------------------------------------------------------------------------- #

def _root() -> Path:
    from . import knowledge
    return knowledge.knowledge_dir() / "imgsearch"


def _dir(name: str) -> Path:
    return _root() / name


def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


def _configured_model() -> str:
    return core.load_config().get("clip_model") or _DEFAULT_MODEL


# --------------------------------------------------------------------------- #
#  Model loading — a per-model cache (keyed by model name) so search encodes
#  the query with the exact model the index was built with, and a lock so a
#  GUI calling from two threads can't double-load.  Uses transformers'
#  CLIPModel directly; the sentence-transformers wrapper has a path-parsing
#  bug with newer HF hub versions.
# --------------------------------------------------------------------------- #

_CLIP_CACHE: dict[str, object] = {}     # model_name -> (model, processor, device) | False
_LOAD_LOCK = threading.Lock()
_ENV_SET = False


def _quiet_hf() -> None:
    global _ENV_SET
    if _ENV_SET:
        return
    _ENV_SET = True
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
    for lg in ("huggingface_hub", "transformers", "sentence_transformers"):
        logging.getLogger(lg).setLevel(logging.ERROR)


def _get_clip(model_name: str | None = None):
    """Return (model, processor, device) for `model_name`, or None if it can't
    be loaded.  Cached per model name; failures are cached too so we don't retry
    a doomed download every call."""
    name = model_name or _configured_model()
    cached = _CLIP_CACHE.get(name)
    if cached is not None:
        return cached or None            # False -> None (known failure)

    with _LOAD_LOCK:
        cached = _CLIP_CACHE.get(name)   # double-checked under the lock
        if cached is not None:
            return cached or None

        try:
            from PIL import Image, ImageFile     # noqa: F401
            # tolerate slightly-truncated JPEGs and cap decompression bombs
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            Image.MAX_IMAGE_PIXELS = _MAX_PIXELS
        except ImportError:
            core.log("imgsearch", "Pillow not installed", "WARN")
            _CLIP_CACHE[name] = False
            return None

        try:
            from transformers import CLIPModel, CLIPProcessor
        except ImportError:
            core.log("imgsearch", "transformers not installed", "WARN")
            _CLIP_CACHE[name] = False
            return None

        from . import rerank
        rerank._patch_hf_insecure()      # this box MITMs TLS; same fix as pip
        _quiet_hf()

        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"

        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                proc = CLIPProcessor.from_pretrained(name)
                model = CLIPModel.from_pretrained(name).to(device).eval()
            entry = (model, proc, device)
            _CLIP_CACHE[name] = entry
            core.log("imgsearch", f"loaded {name} on {device}", "INFO")
            return entry
        except Exception as exc:
            core.log("imgsearch", f"CLIP load failed ({name}): {exc}", "WARN")
            _CLIP_CACHE[name] = False
            return None


# --------------------------------------------------------------------------- #
#  Encoding
# --------------------------------------------------------------------------- #

def _embed_images(clip, images):
    """Encode PIL Images -> normalized CLIP vectors (numpy, float32)."""
    import torch
    model, proc, device = clip
    inputs = proc(images=images, return_tensors="pt")
    pv = inputs["pixel_values"].to(device)
    with torch.no_grad():
        vo = model.vision_model(pixel_values=pv)
        emb = model.visual_projection(vo.pooler_output)
        emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().float().numpy()


def _embed_images_resilient(clip, images, metas):
    """Encode a batch; on ANY failure (GPU OOM, a bad tensor, etc.) fall back to
    one image at a time and skip only the offenders.  Returns
    (vectors|None, kept_metas, skipped_count) with vectors aligned to kept_metas."""
    import numpy as np
    try:
        return _embed_images(clip, images), list(metas), 0
    except Exception as exc:
        core.log("imgsearch", f"batch encode failed ({exc}); retrying per-image",
                 "WARN")
        with contextlib.suppress(Exception):
            import torch
            torch.cuda.empty_cache()

        vecs, kept, skipped = [], [], 0
        for img, m in zip(images, metas):
            try:
                vecs.append(_embed_images(clip, [img])[0])
                kept.append(m)
            except Exception:
                skipped += 1
                with contextlib.suppress(Exception):
                    import torch
                    torch.cuda.empty_cache()
        if not vecs:
            return None, [], skipped
        return np.asarray(vecs), kept, skipped


def _embed_query(clip, query: str):
    """Encode a text query with the prompt ensemble -> one normalized vector."""
    import numpy as np
    import torch
    model, proc, device = clip
    prompts = [t.format(query) for t in _PROMPT_TEMPLATES]
    inputs = proc(text=prompts, return_tensors="pt", padding=True,
                  truncation=True, max_length=77)
    ids = inputs["input_ids"].to(device)
    mask = inputs["attention_mask"].to(device)
    with torch.no_grad():
        to = model.text_model(input_ids=ids, attention_mask=mask)
        emb = model.text_projection(to.pooler_output)
        emb = emb / emb.norm(dim=-1, keepdim=True)
        mean = emb.mean(dim=0)
        mean = mean / mean.norm()
    return mean.cpu().float().numpy()


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def _file_hash(path: Path) -> str:
    st = path.stat()
    h = hashlib.md5()
    h.update(str(path).encode())
    h.update(str(st.st_mtime_ns).encode())
    h.update(str(st.st_size).encode())
    return h.hexdigest()


def _iter_images(folder: Path):
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            yield p


def _load_image(path: Path):
    """Load an image for CLIP: apply EXIF orientation, force RGB.  None on any
    failure (corrupt, unsupported, decompression bomb over the cap)."""
    try:
        from PIL import Image, ImageOps
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)      # phones store orientation in EXIF
        return img.convert("RGB")
    except Exception:
        return None


def _save_npy_atomic(path: Path, arr) -> None:
    """np.save is not atomic; a crash mid-write corrupts the index.  Write to a
    temp sibling via a file handle (so np.save doesn't re-append .npy) then
    os.replace — the same guarantee core.write_atomic gives text files."""
    import numpy as np
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    try:
        with tmp.open("wb") as fh:
            np.save(fh, arr)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            with contextlib.suppress(OSError):
                tmp.unlink()


def _write_index(d: Path, arr, metas: list[dict], info: dict) -> None:
    d.mkdir(parents=True, exist_ok=True)
    _save_npy_atomic(d / "vectors.npy", arr)
    core.write_atomic(d / "meta.json", json.dumps(metas, ensure_ascii=False))
    core.write_atomic(d / "info.json", json.dumps(info, indent=2))


# --------------------------------------------------------------------------- #
#  Build index
# --------------------------------------------------------------------------- #

def build(source: str, name: str | None = None, model: str | None = None,
          incremental: bool = True, progress=None) -> dict:
    import numpy as np

    model = model or _configured_model()
    clip = _get_clip(model)
    if clip is None:
        raise RuntimeError(
            "CLIP model not available — install transformers and Pillow")

    folder = Path(source).resolve()
    if not folder.exists():
        raise FileNotFoundError(source)
    name = name or folder.name
    d = _dir(name)
    _INDEX_CACHE.pop(name, None)         # a rebuild invalidates the search cache

    # Load the existing index for incremental reuse — but only if it was built
    # with the SAME model (otherwise its vectors live in a different space and
    # can't be mixed with new ones).
    existing_hashes: dict[str, int] = {}
    existing_vecs = None
    existing_metas: list[dict] = []
    if incremental and (d / "meta.json").exists() and (d / "vectors.npy").exists():
        try:
            prev_info = json.loads((d / "info.json").read_text(encoding="utf-8"))
            if prev_info.get("model", model) == model:
                existing_metas = json.loads(
                    (d / "meta.json").read_text(encoding="utf-8"))
                existing_vecs = np.load(d / "vectors.npy").astype(np.float32)
                existing_hashes = {m["hash"]: i
                                   for i, m in enumerate(existing_metas)}
        except Exception:
            existing_hashes, existing_vecs, existing_metas = {}, None, []

    all_paths = list(_iter_images(folder))
    if not all_paths:
        raise RuntimeError(f"No images found under {folder}")

    keep_idx: list[int] = []
    new_paths: list[Path] = []
    new_metas: list[dict] = []
    for p in all_paths:
        try:
            fh = _file_hash(p)
        except OSError:
            continue                     # file vanished between listing and now
        if fh in existing_hashes:
            keep_idx.append(existing_hashes[fh])
        else:
            new_paths.append(p)
            new_metas.append({"file": str(p.relative_to(folder)), "abs": str(p),
                              "hash": fh, "size": p.stat().st_size})

    # the unchanging "kept" portion (reused vectors + metas)
    kept_arr = existing_vecs[keep_idx] if (keep_idx and existing_vecs is not None) \
        else None
    kept_metas = [existing_metas[i] for i in keep_idx]

    def _info(count: int, dim: int, n_new: int, skipped: int, partial: bool,
              secs: float) -> dict:
        return {"name": name, "source": str(folder), "model": model,
                "dim": dim, "count": count, "new": n_new, "kept": len(keep_idx),
                "skipped": skipped, "partial": partial,
                "built": datetime.now().isoformat(timespec="seconds"),
                "seconds": round(secs, 1)}

    new_vec_parts: list = []
    done_metas: list[dict] = []
    skipped = 0
    since_ckpt = 0
    t0 = time.time()

    def _checkpoint():
        parts = ([kept_arr] if kept_arr is not None else []) + new_vec_parts
        if not parts:
            return
        arr = np.concatenate(parts, axis=0).astype(np.float16)
        metas = kept_metas + done_metas
        _write_index(d, arr, metas,
                     _info(len(metas), int(arr.shape[1]), len(done_metas),
                           skipped, True, time.time() - t0))

    for bi in range(0, len(new_paths), _BATCH):
        batch_paths = new_paths[bi:bi + _BATCH]
        imgs, metas_slice = [], []
        for j, p in enumerate(batch_paths):
            img = _load_image(p)
            if img is None:
                skipped += 1
            else:
                imgs.append(img)
                metas_slice.append(new_metas[bi + j])

        if imgs:
            vecs, kept_m, enc_skipped = _embed_images_resilient(
                clip, imgs, metas_slice)
            skipped += enc_skipped
            if vecs is not None:
                new_vec_parts.append(vecs)
                done_metas.extend(kept_m)
                since_ckpt += len(kept_m)

        if progress:
            progress(min(bi + _BATCH, len(new_paths)), len(new_paths))

        if since_ckpt >= _CHECKPOINT_EVERY:
            _checkpoint()
            since_ckpt = 0

    # final assembly
    parts = ([kept_arr] if kept_arr is not None else []) + new_vec_parts
    if not parts:
        raise RuntimeError("No images could be loaded (all corrupt/unreadable?)")
    final_arr = np.concatenate(parts, axis=0).astype(np.float16)
    final_metas = kept_metas + done_metas
    info = _info(int(final_arr.shape[0]), int(final_arr.shape[1]),
                 len(done_metas), skipped, False, time.time() - t0)
    _write_index(d, final_arr, final_metas, info)
    _INDEX_CACHE.pop(name, None)
    core.log("imgsearch", f"indexed '{name}': {info['count']} images "
                          f"({info['new']} new, {info['kept']} kept, "
                          f"{skipped} skipped) in {info['seconds']}s", "SUCCESS")
    return info


# --------------------------------------------------------------------------- #
#  Search
# --------------------------------------------------------------------------- #

_INDEX_CACHE: dict[str, tuple] = {}      # name -> (index, metas, info, mtime)


class _JsonlMeta:
    """Lazy row→metadata accessor for streamed (ZIM) indexes: seeks to a line
    by its precomputed byte offset instead of loading millions of dicts into
    RAM.  Only the handful of top-k results are ever read + parsed."""

    def __init__(self, path: Path, offsets):
        self._path = path
        self._off = offsets
        self._fh = None

    def __len__(self) -> int:
        return len(self._off)

    def __getitem__(self, i: int) -> dict:
        if self._fh is None:
            self._fh = open(self._path, "rb")
        self._fh.seek(int(self._off[i]))
        return json.loads(self._fh.readline())

    def close(self) -> None:
        if self._fh is not None:
            try:
                self._fh.close()
            finally:
                self._fh = None

    def __del__(self):
        self.close()


def _ensure_offsets(d: Path, count: int):
    """Return the row byte-offset array for a streamed index, (re)building it
    from meta.jsonl if missing or stale."""
    import numpy as np
    op, mp = d / "meta_offsets.npy", d / "meta.jsonl"
    if op.exists():
        off = np.load(op)
        if len(off) >= count:
            return off[:count]
    offs, pos = [], 0
    with open(mp, "rb") as f:
        for line in f:
            offs.append(pos)
            pos += len(line)
    arr = np.asarray(offs, dtype=np.int64)
    _save_npy_atomic(op, arr)
    return arr[:count]


def _load_index(name: str):
    import numpy as np
    from . import vmath
    d = _dir(name)
    f16, npy = d / "vectors.f16", d / "vectors.npy"

    # streamed (ZIM) format: memmapped float16, chunked GPU search, lazy meta
    if f16.exists():
        mtime = f16.stat().st_mtime_ns
        cached = _INDEX_CACHE.get(name)
        if cached and cached[3] == mtime:
            return cached[:3]
        try:
            info = json.loads((d / "info.json").read_text(encoding="utf-8"))
            count, dim = int(info["count"]), int(info["dim"])
            mm = np.memmap(f16, dtype=np.float16, mode="r", shape=(count, dim))
            metas = _JsonlMeta(d / "meta.jsonl", _ensure_offsets(d, count))
        except Exception as exc:
            core.log("imgsearch", f"index '{name}' unreadable: {exc}", "WARN")
            return None
        _INDEX_CACHE[name] = (vmath.MemmapIndex(mm), metas, info, mtime)
        return _INDEX_CACHE[name][:3]

    # in-memory (folder) format
    if not npy.exists():
        return None
    mtime = npy.stat().st_mtime_ns
    cached = _INDEX_CACHE.get(name)
    if cached and cached[3] == mtime:    # fresh cache hit (index unchanged)
        return cached[:3]
    try:
        arr = np.load(npy).astype(np.float32)
        metas = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        info = json.loads((d / "info.json").read_text(encoding="utf-8"))
    except Exception as exc:
        core.log("imgsearch", f"index '{name}' unreadable: {exc}", "WARN")
        return None
    _INDEX_CACHE[name] = (vmath.Index(arr), metas, info, mtime)
    return _INDEX_CACHE[name][:3]


def _hits(index, metas, results) -> list[dict]:
    out = []
    for i, score in results:
        m = metas[i]
        out.append({"score": round(float(score), 3), "file": m["file"],
                    "abs": m.get("abs", "")})
    return out


def search(name: str, query: str, k: int = 12) -> list[dict]:
    query = (query or "").strip()
    if not name or not query:      # no collection / empty query -> nothing
        return []
    entry = _load_index(name)
    if entry is None:
        return []
    index, metas, info = entry
    clip = _get_clip(info.get("model"))  # encode query with the index's model
    if clip is None:
        return []
    qv = _embed_query(clip, query)
    return _hits(index, metas, index.search(qv, k))


def similar(name: str, image_path: str, k: int = 12) -> list[dict]:
    if not name:
        return []
    entry = _load_index(name)
    if entry is None:
        return []
    img = _load_image(Path(image_path))
    if img is None:
        return []
    index, metas, info = entry
    clip = _get_clip(info.get("model"))
    if clip is None:
        return []
    qv = _embed_images(clip, [img])[0]
    return _hits(index, metas, index.search(qv, k))


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
#  Search-across-everything — so you can just describe an image without knowing
#  (or typing) which collection it lives in.
# --------------------------------------------------------------------------- #

def _resolve_target(args: list[str], names) -> tuple[str | None, str]:
    """Decide whether the first CLI arg is a collection name or part of the
    query.  A leading token counts as a collection only when it matches an
    existing index AND something follows it — so `img search "the moon"`
    searches everywhere, while `img search photos "the moon"` targets one."""
    if len(args) >= 2 and args[0] in names:
        return args[0], " ".join(args[1:])
    return None, " ".join(args)


def _dedup(hits: list[dict]) -> list[dict]:
    """Drop repeats of the same file — e.g. a photo indexed in two overlapping
    collections.  Callers pass score-sorted hits, so the first (highest) wins."""
    seen, out = set(), []
    for h in hits:
        key = h.get("abs") or h.get("file")
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def search_all(query: str, k: int = 12) -> list[dict]:
    """Text→image across every collection, merged by score.  Each hit is tagged
    with its 'collection'.  Note: scores are directly comparable only within one
    CLIP model; if collections use different models the merge is approximate."""
    query = (query or "").strip()
    if not query:
        return []
    out: list[dict] = []
    for it in list_indexes():
        for h in search(it["name"], query, k):
            h["collection"] = it["name"]
            out.append(h)
    out.sort(key=lambda h: -h["score"])
    return _dedup(out)[:k]


def similar_all(image_path: str, k: int = 12) -> list[dict]:
    """Image→image across every collection, merged by score."""
    if _load_image(Path(image_path)) is None:
        return []
    out: list[dict] = []
    for it in list_indexes():
        for h in similar(it["name"], image_path, k):
            h["collection"] = it["name"]
            out.append(h)
    out.sort(key=lambda h: -h["score"])
    return _dedup(out)[:k]


# --------------------------------------------------------------------------- #
#  Verify — probe stored links/files so dead results surface without manually
#  clicking each one (`ultra img verify`).  ZIM collections with a stale book
#  id are repaired automatically (metadata rewrite, vectors untouched).
# --------------------------------------------------------------------------- #

def _sample_metas(name: str, k: int) -> list[dict]:
    """Random sample of k metadata rows from a collection (either format),
    without loading vectors or the CLIP model."""
    import random
    d = _dir(name)
    try:
        info = json.loads((d / "info.json").read_text(encoding="utf-8"))
        count = int(info.get("count", 0))
    except Exception:
        return []
    if count <= 0:
        return []
    picks = sorted(random.sample(range(count), min(k, count)))
    if (d / "meta.jsonl").exists():
        store = _JsonlMeta(d / "meta.jsonl", _ensure_offsets(d, count))
        try:
            return [store[i] for i in picks]
        finally:
            store.close()
    try:
        metas = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    return [metas[i] for i in picks if i < len(metas)]


def _probe_target(target: str, timeout: float = 8.0) -> bool:
    """True if a stored result target is reachable — HTTP 200 for ZIM-served
    URLs, file-exists for folder collections."""
    if not target:
        return False
    if target.startswith("http"):
        import urllib.request
        try:
            with urllib.request.urlopen(target, timeout=timeout) as r:
                return r.status == 200
        except Exception:
            return False
    return Path(target).exists()


def _cli_verify(ca, blue, green, only: str | None, sample: int) -> int:
    items = [it for it in list_indexes()
             if not only or it.get("name") == only]
    if not items:
        print(ca.color(f"  (no collection named '{only}')" if only else
                       "  (nothing indexed yet)", AMBER))
        return 1
    served = False
    broken = 0
    for it in items:
        name = it.get("name", "?")
        metas = _sample_metas(name, sample)
        if not metas:
            print(ca.color(f"  ? {name}: no readable metadata", AMBER))
            broken += 1
            continue
        if not served and any(str(m.get("abs", "")).startswith("http")
                              for m in metas):
            with contextlib.suppress(Exception):
                from . import knowledge
                knowledge.serve_start()
            served = True
        ok = sum(1 for m in metas if _probe_target(m.get("abs", "")))
        if ok == len(metas):
            print(ca.color(f"  ✓ {name}: {ok}/{len(metas)} sampled links OK",
                           green))
            continue
        # ZIM collections often fail wholesale from a stale book id — fixable
        if str(it.get("source", "")).startswith("zim:"):
            from . import zimimg
            print(ca.color(f"  ⚠ {name}: {ok}/{len(metas)} OK — repairing "
                           "URLs…", AMBER))
            if zimimg.repair_urls(name) is not None:
                metas = _sample_metas(name, sample)
                ok = sum(1 for m in metas if _probe_target(m.get("abs", "")))
                if ok == len(metas):
                    print(ca.color(f"  ✓ {name}: repaired — {ok}/{len(metas)} "
                                   "OK", green))
                    continue
        broken += 1
        print(ca.color(f"  ✕ {name}: {len(metas) - ok}/{len(metas)} sampled "
                       "links dead", RED))
        src = str(it.get("source", ""))
        hint = ("re-run `ultra img index-zim` to rebuild" if
                src.startswith("zim:") else
                f"re-run `ultra img index {src} --name {name}` to refresh")
        print(ca.color(f"      {hint}", MUTED))
    return 1 if broken else 0


# --------------------------------------------------------------------------- #
#  Shared result rendering + open-by-number (used by both search and similar)
# --------------------------------------------------------------------------- #

def _render_hits(ca, green, hits: list[dict]) -> None:
    for n, h in enumerate(hits, 1):
        loc = f"{h['collection']}/{h['file']}" if h.get("collection") \
            else h["file"]
        print("   " + ca.color(f"{n:>2}.", MUTED) + " "
              + ca.color(f"{h['score']:.3f}", green)
              + ca.color(f"  {loc}", CYAN))


def _offer_open(ca, green, hits: list[dict]) -> None:
    """Let the user open results by number — supports multi-select (e.g. '1 3 5'
    or '1,3,5' or '1-4').  Enter skips."""
    prompt = ca.color("  open? [numbers, range, or Enter to skip] ", MUTED)
    try:
        ans = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print(); return
    if not ans:
        return
    indices = _parse_selection(ans, len(hits))
    if not indices:
        print(ca.color("  (no valid numbers in that selection)", AMBER)); return
    kiwix_started = False
    for i in indices:
        h = hits[i]
        target = h.get("abs", "")
        if target.startswith("http"):
            if not kiwix_started:
                try:
                    from . import knowledge
                    knowledge.serve_start()
                except Exception:
                    pass
                kiwix_started = True
            core.open_in_os(target)
            print(ca.color(f"  → opened {h['file']}", green))
        elif target and Path(target).exists():
            core.open_in_os(target)
            print(ca.color(f"  → opened {h['file']}", green))
        else:
            print(ca.color(f"  (can't open: {target or '?'})", AMBER))


def _parse_selection(text: str, count: int) -> list[int]:
    """Parse a multi-select string into 0-based indices.
    Accepts: '3', '1 3 5', '1,3,5', '1-4', '2, 5-7', or mixes."""
    indices: list[int] = []
    seen: set[int] = set()
    for tok in text.replace(",", " ").split():
        if "-" in tok and not tok.startswith("-"):
            parts = tok.split("-", 1)
            try:
                lo, hi = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            for n in range(lo, hi + 1):
                i = n - 1
                if 0 <= i < count and i not in seen:
                    seen.add(i); indices.append(i)
        else:
            try:
                n = int(tok)
            except ValueError:
                continue
            i = n - 1
            if 0 <= i < count and i not in seen:
                seen.add(i); indices.append(i)
    return indices


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
#  Interactive-menu category (the main `ultra` menu)
# --------------------------------------------------------------------------- #

def _tool_gallery(_ctx) -> None:
    from . import gallery
    gallery.open_gallery()


def _tool_search(_ctx) -> None:
    query = input("  describe the image you want: ").strip()
    if query:
        handle(["img", "search"] + query.split())


def _tool_verify(_ctx) -> None:
    handle(["img", "verify"])


def _tool_status(_ctx) -> None:
    handle(["img", "status"])


def register() -> "core.Category":
    cat = core.Category("img", "Image Search & Gallery")
    cat.add("gallery", "The Ultra Archive — space-museum photo hall",
            _tool_gallery)
    cat.add("search", "Find an image by describing it", _tool_search)
    cat.add("verify", "Health-check result links", _tool_verify)
    cat.add("status", "Collections + model info", _tool_status)
    return cat


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() not in ("img", "imgsearch", "image"):
        return None
    ca, blue, green = _theme()
    rest = argv[1:]
    sub = rest[0].lower() if rest else "list"

    if sub in ("index-zim", "zim", "index-wiki", "wiki"):
        from . import zimimg
        return zimimg.cli_index(rest[1:])

    if sub in ("gallery", "museum", "archive", "browse"):
        from . import gallery
        return gallery.cli(rest[1:])

    if sub in ("topics", "topic", "curate"):
        from . import gallery
        return gallery.cli_topics(rest[1:])

    if sub in ("verify", "check"):
        args = rest[1:]
        sample, only, i = 40, None, 0
        while i < len(args):
            if args[i] == "--sample" and i + 1 < len(args):
                try:
                    sample = max(1, int(args[i + 1]))
                except ValueError:
                    pass
                i += 2
            else:
                only = args[i]; i += 1
        print()
        print(ca.color("  ▸ img verify", green)
              + ca.color(f"   (sampling {sample} per collection)", MUTED))
        print(ca.gradient("  " + "─" * 66, blue, green))
        return _cli_verify(ca, blue, green, only, sample)

    if sub in ("index", "build"):
        args = rest[1:]
        source, name, model = None, None, None
        i = 0
        while i < len(args):
            if args[i] == "--name" and i + 1 < len(args):
                name = args[i + 1]; i += 2
            elif args[i] == "--model" and i + 1 < len(args):
                model = args[i + 1]; i += 2
            else:
                source = args[i]; i += 1
        if not source:
            print("usage: ultra img index <folder> [--name N] [--model M]")
            return 2

        from . import vmath
        print()
        print(ca.color("  ▸ CLIP image indexer", green)
              + ca.color(f"   ({vmath.backend()})", MUTED))
        print(ca.gradient("  " + "─" * 66, blue, green))

        def _prog(done, total):
            pct = done * 100 // total if total else 100
            print(f"\r  embedding {done}/{total} images ({pct}%)  ", end="",
                  flush=True)

        try:
            info = build(source, name, model=model, progress=_prog)
        except Exception as exc:
            print(ca.color(f"\n  ✕ {exc}", RED)); return 1

        print()
        print(ca.color(f"  ✓ {info['count']} images indexed "
                       f"({info['new']} new, {info['kept']} kept"
                       + (f", {info['skipped']} skipped" if info['skipped'] else "")
                       + f") in {info['seconds']}s", green))
        print(ca.color(f"    search:  ultra img search {info['name']} "
                       '"<description>"', MUTED))
        return 0

    if sub == "search":
        args = rest[1:]
        names = {it["name"] for it in list_indexes()}
        name, query = _resolve_target(args, names)
        if not query:
            print('usage: ultra img search "<description>"      (searches all)\n'
                  '   or: ultra img search <collection> "<description>"')
            return 2
        from . import vmath
        print()
        print(ca.color(f"  ▸ img[{name or 'all'}] ", green)
              + ca.color(query, "#ffffff")
              + ca.color(f"   ({vmath.backend()})", MUTED))
        print(ca.gradient("  " + "─" * 66, blue, green))
        hits = search(name, query, 12) if name else search_all(query, 12)
        if not hits:
            print(ca.color("  (nothing indexed yet — build a collection with "
                           "`ultra img index <folder> --name X`)", AMBER)); return 1
        _render_hits(ca, green, hits)
        print()
        _offer_open(ca, green, hits)
        return 0

    if sub == "similar":
        names = {it["name"] for it in list_indexes()}
        name, img_path = _resolve_target(rest[1:], names)
        if not img_path:
            print("usage: ultra img similar <image-path>       (searches all)\n"
                  "   or: ultra img similar <collection> <image-path>")
            return 2
        if not Path(img_path).exists():
            print(ca.color(f"  ✕ file not found: {img_path}", RED)); return 1
        from . import vmath
        print()
        print(ca.color(f"  ▸ img[{name or 'all'}] ", green)
              + ca.color(f"similar to {Path(img_path).name}", "#ffffff")
              + ca.color(f"   ({vmath.backend()})", MUTED))
        print(ca.gradient("  " + "─" * 66, blue, green))
        hits = similar(name, img_path, 12) if name else similar_all(img_path, 12)
        if not hits:
            print(ca.color("  (nothing indexed, unreadable image, or CLIP "
                           "model unavailable)", AMBER)); return 1
        _render_hits(ca, green, hits)
        print()
        _offer_open(ca, green, hits)
        return 0

    if sub == "status":
        from . import vmath
        print()
        model = _configured_model()
        clip = _get_clip(model)
        dev = clip[2] if clip else "—"
        print(ca.color("  CLIP image search", green))
        print(ca.color(f"    model:    {model}", PAPER))
        print(ca.color(f"    device:   {dev}", PAPER))
        print(ca.color(f"    backend:  {vmath.backend()}", PAPER))
        print(ca.color(f"    encoder:  {'loaded' if clip else 'unavailable'}",
                       green if clip else AMBER))
        idxs = list_indexes()
        total = sum(i.get("count", 0) for i in idxs)
        print(ca.color(f"    indexes:  {len(idxs)} ({total} images)", PAPER))
        return 0

    idxs = list_indexes()
    print()
    print(ca.gradient(f"  ╭─ Image indexes · {len(idxs)} " + "─" * 38 + "╮",
                      blue, green))
    if not idxs:
        print("  " + ca.color("│", blue) + ca.color(
            "  none yet — ultra img index <folder> --name X", MUTED)
            + " " * 17 + ca.color("│", green))
    for it in idxs:
        tag = " (partial)" if it.get("partial") else ""
        line = (f"  {it['name'][:22]:<22} {it['count']:>7} images · "
                f"{it.get('model', '?').split('/')[-1][:16]}{tag}")
        print("  " + ca.color("│", blue) + ca.color(line, PAPER)
              + " " * max(1, 64 - len(line)) + ca.color("│", green))
    print(ca.gradient("  ╰" + "─" * 66 + "╯", green, blue))
    return 0
