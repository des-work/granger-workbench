"""Media & asset ingest — a clean intake pipeline for creative work.

The problem this kills: camera dumps, Blender exports, downloaded textures and
UE assets landing in random folders "to organize later". Instead there is ONE
process: point `ultra ingest` at any source (SD card, download dir, phone
dump) and every file is classified, renamed consistently, deduplicated by
hash, and filed into a stable library layout — with a manifest of exactly
what went where.

    ultra ingest run <source>                # copy (source untouched)
    ultra ingest run <source> --move         # verified move (hash-checked)
    ultra ingest run <source> --dry          # show the plan, touch nothing
    ultra ingest run <source> --project bee  # file under Projects/bee/...
    ultra ingest run <source> --index        # + CLIP-index photos afterward
    ultra ingest status                      # library overview
    ultra ingest root [path]                 # show / set the library root

Library layout (root default C:\\Ultra-Media, config key `media_root`):

    Photos/YYYY/YYYY-MM-DD/     camera photos + RAW, timestamp-prefixed
    Photos/Screenshots/YYYY-MM/ screen captures kept out of the photo stream
    Pictures/YYYY-MM/           non-camera images (downloads) — timeline stays clean
    Video/YYYY/YYYY-MM-DD/      probed (duration/res) when ffprobe exists
    Audio/YYYY-MM/
    Textures/<set>/             PBR sets grouped (albedo/normal/rough/…)
    Textures/loose/             HDRIs/          Models/<fmt>/
    Blender/    Unreal/    Archives/    _Unsorted/   (nothing is ever lost)
    _ingest/hashes.json         library-wide dedup index
    _ingest/logs/…json          one manifest per run

Safety follows the project's file rules: copies are hash-verified in a single
source read (stream-hash while copying, re-hash the copy); --move deletes the
source only after the verified copy exists; duplicates are skipped (and
logged), never overwritten. Robustness contract: one unreadable file (cloud
placeholder, permission error) costs one manifest line, never the run; the
library can never ingest itself; the dedup ledger + manifest are checkpointed
every 100 files and persisted even on a crash.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from . import core

MUTED, PAPER, AMBER, RED = "#8fb8cf", "#eaf6ff", "#febc2e", "#ff6159"

DEFAULT_ROOT = r"C:\Ultra-Media"

# --------------------------------------------------------------------------- #
#  Classification rules
# --------------------------------------------------------------------------- #

RAW_EXT = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".mts", ".m2ts", ".webm",
             ".wmv", ".3gp"}
AUDIO_EXT = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aif", ".aiff"}
MODEL_EXT = {".fbx", ".obj", ".gltf", ".glb", ".usd", ".usda", ".usdc",
             ".usdz", ".abc", ".stl", ".dae", ".ply", ".3ds"}
TEX_EXT = {".tga", ".tif", ".tiff", ".bmp", ".dds", ".ktx", ".ktx2", ".psd"}
HDR_EXT = {".hdr", ".exr"}
BLEND_EXT = {".blend"}
UNREAL_EXT = {".uasset", ".umap", ".uproject", ".pak"}
ARCHIVE_EXT = {".zip", ".rar", ".7z", ".tar", ".gz"}
JUNK_EXT = {".blend1", ".blend2", ".tmp", ".ds_store", ".tmp~"}

_PBR_SUFFIXES = (
    # naming used by AmbientCG / PolyHaven / Substance / textures.com exports
    "albedo", "basecolor", "base_color", "diffuse", "diff", "color",
    "normal", "nrm", "nor", "nor_gl", "nor_dx", "normalgl", "normaldx",
    "bump", "roughness", "rough", "rgh", "metallic", "metalness", "metal",
    "ao", "ambientocclusion", "occlusion", "height", "disp",
    "displacement", "emissive", "emission", "opacity", "alpha",
    "specular", "gloss", "arm", "orm",
)
_PBR_RE = re.compile(
    r"^(.*?)[_\-. ](?:" + "|".join(_PBR_SUFFIXES) + r")(?:[_\-. ]?\d+k)?$",
    re.IGNORECASE)

_CAMERA_NAME = re.compile(r"^(img|dsc[fn]?|dscf|pxl|dji|gopr|mvi|p\d{4}|"
                          r"\d{8}_\d{6})", re.IGNORECASE)
_SCREENSHOT_NAME = re.compile(r"screen\s?shot|screencap|capture|snip",
                              re.IGNORECASE)


def pbr_set(stem: str) -> str | None:
    """'RustyMetal_04_roughness' -> 'RustyMetal_04' (None if not a PBR map)."""
    m = _PBR_RE.match(stem)
    return m.group(1) if m and m.group(1) else None


def _exif_datetime(path: Path):
    """Camera capture time from EXIF (jpg/tiff via PIL), else None."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            exif = im.getexif()
        for tag in (36867, 306):          # DateTimeOriginal, DateTime
            v = exif.get(tag)
            if v:
                return datetime.strptime(str(v)[:19], "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def _has_camera_exif(path: Path) -> bool:
    try:
        from PIL import Image
        with Image.open(path) as im:
            exif = im.getexif()
        return bool(exif.get(271) or exif.get(272))    # Make / Model
    except Exception:
        return False


def classify(path: Path) -> str:
    """One file -> category id. Pure-ish (reads EXIF for image disambiguation)."""
    ext = path.suffix.lower()
    stem = path.stem
    if ext in JUNK_EXT:
        return "junk"
    if ext in BLEND_EXT:
        return "blender"
    if ext in UNREAL_EXT:
        return "unreal"
    if ext in MODEL_EXT:
        return "model"
    if ext in RAW_EXT:
        return "photo_raw"
    if ext in HDR_EXT:
        low = stem.lower()
        # Blender render outputs are often huge EXRs — a size-only rule would
        # misfile them as HDRIs, so render-ish names outrank size
        if any(h in low for h in ("render", "pass", "comp", "beauty")):
            return "texture"
        if any(h in low for h in ("hdri", "pano", "sky", "env")) \
                or path.stat().st_size > 20 * 1024 * 1024:
            return "hdri"
        return "texture"
    if ext in TEX_EXT:
        return "texture"
    if ext in PHOTO_EXT:
        if pbr_set(stem):
            return "texture"
        if _SCREENSHOT_NAME.search(stem):
            return "screenshot"
        if _CAMERA_NAME.match(stem) or _has_camera_exif(path):
            return "photo"
        # No camera signal at all: JPG/HEIC still lean photo (cameras and
        # photo exports emit them), but PNG/WebP without EXIF or a camera
        # name are almost never photographs — keep them out of the photo
        # timeline instead of polluting it with downloaded images
        if ext in (".jpg", ".jpeg", ".heic", ".heif"):
            return "photo"
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in ARCHIVE_EXT:
        return "archive"
    return "unsorted"


def _file_dt(path: Path, cat: str) -> datetime:
    # EXIF only helps where PIL can actually read it (JPEG/TIFF/PNG); RAW and
    # video would just raise inside Image.open, so skip straight to mtime
    if cat == "photo" and path.suffix.lower() in (".jpg", ".jpeg", ".tif",
                                                  ".tiff", ".png"):
        dt = _exif_datetime(path)
        if dt:
            return dt
    return datetime.fromtimestamp(path.stat().st_mtime)


def destination(root: Path, path: Path, cat: str, dt: datetime,
                project: str = "") -> Path | None:
    """Where a classified file belongs. Returns None for junk (skipped)."""
    stamp = dt.strftime("%Y%m%d_%H%M%S")
    name = path.name
    if cat in ("photo", "photo_raw", "video") \
            and not re.match(r"^\d{8}_\d{6}_", name):
        name = f"{stamp}_{name}"
    sub = {
        "photo":      Path("Photos") / f"{dt:%Y}" / f"{dt:%Y-%m-%d}",
        "photo_raw":  Path("Photos") / f"{dt:%Y}" / f"{dt:%Y-%m-%d}",
        "screenshot": Path("Photos") / "Screenshots" / f"{dt:%Y-%m}",
        "image":      Path("Pictures") / f"{dt:%Y-%m}",
        "video":      Path("Video") / f"{dt:%Y}" / f"{dt:%Y-%m-%d}",
        "audio":      Path("Audio") / f"{dt:%Y-%m}",
        "model":      Path("Models") / path.suffix.lower().lstrip("."),
        "blender":    Path("Blender"),
        "unreal":     Path("Unreal"),
        "archive":    Path("Archives"),
        "unsorted":   Path("_Unsorted"),
        "junk":       None,
    }.get(cat)
    if cat == "texture":
        s = pbr_set(path.stem)
        sub = Path("Textures") / (s if s else "loose")
    elif cat == "hdri":
        sub = Path("HDRIs")
    if sub is None:
        return None
    base = root / (Path("Projects") / project if project else Path()) / sub
    return base / name


# --------------------------------------------------------------------------- #
#  Hashing, dedup, verified transfer
# --------------------------------------------------------------------------- #

def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _root() -> Path:
    cfg = core.load_config()
    return Path(cfg.get("media_root") or DEFAULT_ROOT)


def _hash_index_path(root: Path) -> Path:
    return root / "_ingest" / "hashes.json"


def _load_hashes(root: Path) -> dict:
    try:
        return json.loads(_hash_index_path(root).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_hashes(root: Path, hashes: dict) -> None:
    p = _hash_index_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    core.write_atomic(p, json.dumps(hashes))


def _unique(dest: Path) -> Path:
    if not dest.exists():
        return dest
    i = 2
    while True:
        cand = dest.with_stem(f"{dest.stem}_{i}")
        if not cand.exists():
            return cand
        i += 1


def _transfer(src: Path, dest: Path, move: bool, src_hash: str) -> None:
    """Copy src -> dest, hashing the copy stream as it's written and
    verifying it against the source hash we already computed — one read of
    the source total (matters for multi-GB video). The source is deleted
    (move) only after the verified copy exists."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".ultrapart")
    h = hashlib.sha256()
    try:
        with open(src, "rb") as fin, open(tmp, "wb") as fout:
            while True:
                b = fin.read(1 << 20)
                if not b:
                    break
                h.update(b)
                fout.write(b)
            fout.flush()
        if h.hexdigest() != src_hash:
            raise IOError(f"source changed while copying: {src.name}")
        if _sha256(tmp) != src_hash:
            raise IOError(f"copy verification failed: {src.name}")
        shutil.copystat(src, tmp)          # keep mtime etc. like copy2
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    if move:
        src.unlink()


def _probe_video(path: Path) -> dict:
    try:
        from . import mediaconv
        import subprocess
        fp = mediaconv.ffprobe_bin()
        if not fp:
            return {}
        out = subprocess.run(
            [fp, "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height:format=duration", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=30).stdout
        j = json.loads(out or "{}")
        st = (j.get("streams") or [{}])[0]
        return {"w": st.get("width"), "h": st.get("height"),
                "sec": round(float(j.get("format", {}).get("duration", 0)), 1)}
    except Exception:
        return {}


# --------------------------------------------------------------------------- #
#  The run
# --------------------------------------------------------------------------- #

def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


_CHECKPOINT_EVERY = 100     # persist the dedup ledger this often mid-run


def run(source: str | Path, move: bool = False, dry: bool = False,
        project: str = "", progress=None) -> dict:
    """Ingest everything under `source`. Returns the manifest dict.

    Robustness contract: one unreadable file (cloud placeholder, permission
    error, vanished mid-run) is logged and skipped — it never aborts the run;
    the library can never ingest itself; the dedup ledger and manifest are
    checkpointed during the run and always persisted, crash or not."""
    src_root = Path(source).expanduser()
    if not src_root.exists():
        raise FileNotFoundError(f"source not found: {src_root}")
    root = _root()
    if _is_under(src_root, root):
        raise ValueError(f"source {src_root} is inside the library {root} — "
                         "that would re-ingest the library into itself")

    hashes = _load_hashes(root) if not dry else {}
    if src_root.is_dir():
        # skip the library itself if it happens to live under the source
        # (e.g. `ingest run C:\` with the library on C:)
        files = [p for p in sorted(src_root.rglob("*"))
                 if p.is_file() and not _is_under(p, root)]
    else:
        files = [src_root]

    manifest = {"source": str(src_root), "root": str(root), "move": move,
                "dry": dry, "project": project,
                "started": datetime.now().isoformat(timespec="seconds"),
                "items": [], "counts": {}, "filed": 0, "bytes": 0}
    counts: dict[str, int] = {}
    logdir = root / "_ingest" / "logs"
    logname = f"ingest-{time.strftime('%Y%m%d-%H%M%S')}.json"

    def _persist():
        _save_hashes(root, hashes)
        logdir.mkdir(parents=True, exist_ok=True)
        core.write_atomic(logdir / logname, json.dumps(manifest, indent=1))

    since_ckpt = 0
    try:
        for i, f in enumerate(files):
            if progress:
                progress(i + 1, len(files), f.name)
            item = {"src": str(f)}
            manifest["items"].append(item)
            # everything per-file is fallible (cloud placeholders raise on
            # read; files vanish; EXIF parsing hits corrupt headers) — one
            # bad file must cost one line in the manifest, not the run
            try:
                cat = classify(f)
                counts[cat] = counts.get(cat, 0) + 1
                if cat == "junk":
                    item["action"] = "junk-skip"
                    continue
                dt = _file_dt(f, cat)
                dest = destination(root, f, cat, dt, project)
                item.update(cat=cat, dest=str(dest))
                if dry:
                    item["action"] = "plan"
                    continue
                h = _sha256(f)
                if h in hashes:
                    item.update(action="duplicate-skip", of=hashes[h])
                    counts["duplicate"] = counts.get("duplicate", 0) + 1
                    continue
                dest = _unique(dest)
                item["dest"] = str(dest)
                _transfer(f, dest, move, h)
                hashes[h] = str(dest.relative_to(root))
                manifest["filed"] += 1
                manifest["bytes"] += dest.stat().st_size
                since_ckpt += 1
                if cat == "video":
                    info = _probe_video(dest)
                    if info:
                        item["probe"] = info
                item["action"] = "moved" if move else "copied"
            except Exception as exc:
                item.update(action="ERROR", error=str(exc))
                counts["error"] = counts.get("error", 0) + 1
            if not dry and since_ckpt >= _CHECKPOINT_EVERY:
                _persist()
                since_ckpt = 0
    finally:
        manifest["counts"] = counts
        manifest["finished"] = datetime.now().isoformat(timespec="seconds")
        if not dry:
            _persist()
            core.log("ingest", f"{len(files)} files from {src_root} -> "
                               f"{root} ({counts})", "SUCCESS")
    return manifest


def status() -> dict:
    root = _root()
    out = {"root": str(root), "exists": root.exists(), "areas": {}}
    if root.exists():
        for area in ("Photos", "Video", "Audio", "Textures", "HDRIs",
                     "Models", "Blender", "Unreal", "Archives", "_Unsorted",
                     "Projects"):
            d = root / area
            if d.exists():
                n = sum(1 for p in d.rglob("*") if p.is_file())
                out["areas"][area] = n
        out["hashes"] = len(_load_hashes(root))
    return out


# --------------------------------------------------------------------------- #
#  CLI — `ultra ingest ...`
# --------------------------------------------------------------------------- #

def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() not in ("ingest", "intake", "import"):
        return None
    ca, blue, green = _theme()
    rest = argv[1:]
    sub = rest[0].lower() if rest else "help"

    if sub == "root":
        cfg = core.load_config()
        if len(rest) > 1:
            cfg["media_root"] = rest[1]
            core.save_config(cfg)
            print(ca.color(f"  ✓ media library root set to {rest[1]}", green))
        else:
            print(ca.color(f"  media library root: {_root()}"
                           f"   (set: ultra ingest root <path>)", PAPER))
        return 0

    if sub == "status":
        st = status()
        print()
        print(ca.color(f"  ▸ media library · {st['root']}", green))
        if not st["exists"]:
            print(ca.color("    (not created yet — first ingest run builds "
                           "it)", MUTED))
            return 0
        for area, n in st["areas"].items():
            print(ca.color(f"    {area:<12} {n:>7,} files", PAPER))
        print(ca.color(f"    tracked hashes: {st.get('hashes', 0):,} "
                       "(library-wide dedup)", MUTED))
        return 0

    if sub in ("run", "from"):
        args = rest[1:]
        source, move, dry, project, index = None, False, False, "", False
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--move":
                move = True; i += 1
            elif a in ("--dry", "--dry-run", "-n"):
                dry = True; i += 1
            elif a == "--index":
                index = True; i += 1
            elif a == "--project" and i + 1 < len(args):
                project = args[i + 1]; i += 2
            else:
                source = a if source is None else source; i += 1
        if not source:
            print("usage: ultra ingest run <source> [--move] [--dry] "
                  "[--project <name>] [--index]")
            return 2

        print()
        print(ca.color(f"  ▸ ingest · {source} → {_root()}"
                       + ("  (DRY RUN)" if dry else "")
                       + ("  (verified move)" if move else "  (copy)"), green))
        print(ca.gradient("  " + "─" * 66, blue, green))

        # in-place progress only on a real terminal (project rule: gate
        # ANIMATION on TTY so piped runs stay one clean line per event)
        _prog = None
        if getattr(ca, "TTY", False):
            def _prog(done, total, name):
                print(f"\r  {done}/{total}  {name[:46]:<46}", end="",
                      flush=True)

        try:
            m = run(source, move=move, dry=dry, project=project,
                    progress=_prog)
        except (FileNotFoundError, ValueError) as exc:
            print(ca.color(f"\n  ✕ {exc}", RED)); return 1
        if _prog:
            print("\r" + " " * 70)
        for cat, n in sorted(m["counts"].items()):
            mark = "⚠" if cat in ("error", "unsorted") else "·"
            print(ca.color(f"    {mark} {cat:<12} {n:>5}", PAPER))
        if dry:
            print(ca.color("\n  dry run — nothing was written. Re-run "
                           "without --dry to file these.", AMBER))
        else:
            mb = m["bytes"] / 1e6
            skipped = m["counts"].get("duplicate", 0)
            print(ca.color(f"\n  ✓ filed {m['filed']} file(s), {mb:,.0f} MB "
                           f"into {m['root']}"
                           + (f" · {skipped} duplicate(s) skipped"
                              if skipped else "")
                           + " · manifest in _ingest/logs", green))
            if m["counts"].get("error"):
                print(ca.color(f"  ⚠ {m['counts']['error']} file(s) failed — "
                               "their sources were NOT deleted; see the "
                               "manifest", RED))
        if index and not dry:
            photos = _root() / "Photos"
            if photos.exists():
                print(ca.color("\n  ▸ CLIP-indexing the photo library…",
                               green))
                from . import imgsearch
                imgsearch.handle(["img", "index", str(photos),
                                  "--name", "media-photos"])
        return 0

    print("usage: ultra ingest run <source> [--move] [--dry] [--project N] "
          "[--index]   ·   ingest status   ·   ingest root [path]")
    return 0
