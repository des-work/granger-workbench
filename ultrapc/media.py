"""[2] Media Tools.

Image inspection (dimensions, mode, EXIF), integrity check, batch
convert/resize, and duplicate detection. Audio/video metadata uses ffprobe
when present; the app tells you clearly if it is missing.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from . import core, ui

try:
    from PIL import Image, ExifTags
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".ico"}


def _need_pil() -> bool:
    if not HAVE_PIL:
        ui.popup_error("Pillow (PIL) is not available.\nInstall with:  pip install Pillow")
        return False
    return True


# --------------------------------------------------------------------------- #
#  Image inspector
# --------------------------------------------------------------------------- #

def image_inspector(ctx=None) -> None:
    ui.clear(); ui.title_bar("Image Inspector", "dimensions, mode, EXIF metadata")
    if not _need_pil():
        return
    path = ui.ask_open_file("Choose an image",
                            [("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                             ("All files", "*.*")])
    if not path:
        return
    r = core.Report("Image Inspector")
    r.section(path)
    try:
        with Image.open(path) as im:
            r.line(f"  format     {im.format}")
            r.line(f"  size       {im.width} x {im.height} px")
            r.line(f"  mode       {im.mode}")
            r.line(f"  megapixels {im.width * im.height / 1e6:.2f} MP")
            r.line(f"  file size  {os.path.getsize(path):,} bytes")

            exif = getattr(im, "_getexif", lambda: None)()
            if exif:
                r.section("EXIF")
                names = {v: k for k, v in ExifTags.TAGS.items()}  # noqa: F841
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag in ("MakerNote", "UserComment") or isinstance(value, bytes):
                        continue
                    r.line(f"  {str(tag):<24} {value}")
            else:
                r.section("EXIF")
                r.line("  (none embedded)")
    except Exception as exc:
        ui.popup_error(f"Could not open image:\n{exc}"); return
    ui.show_text(r.text(), "Ultra-PC — Image Inspector")
    ui.pause()


# --------------------------------------------------------------------------- #
#  Image integrity check (batch)
# --------------------------------------------------------------------------- #

def integrity_check(ctx=None) -> None:
    ui.clear(); ui.title_bar("Image Integrity Check", "scan a folder for corrupt images")
    if not _need_pil():
        return
    folder = ui.ask_directory("Choose a folder of images")
    if not folder:
        return
    r = core.Report("Image Integrity Check")
    r.section(folder)
    files = [p for p in Path(folder).rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    ui.info(f"Scanning {len(files)} image(s)...")
    bad = 0
    for i, p in enumerate(files, 1):
        print(f"\r  checking {i}/{len(files)}", end="", flush=True)
        try:
            with Image.open(p) as im:
                im.verify()
        except Exception as exc:
            bad += 1
            r.finding("FAIL", f"{p.name}: {exc}", "MEDIUM", "Corrupt image files found")
    print()
    if bad == 0:
        r.finding("PASS", f"all {len(files)} images verified OK")
    ui.deliver_report(r, "Image_Integrity")


# --------------------------------------------------------------------------- #
#  Batch convert / resize
# --------------------------------------------------------------------------- #

def batch_convert(ctx=None) -> None:
    ui.clear(); ui.title_bar("Batch Convert / Resize", "uses this PC's horsepower")
    if not _need_pil():
        return
    files = ui.ask_open_files("Choose images to process",
                              [("Images", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                               ("All files", "*.*")])
    if not files:
        return
    fmt = (ui.ask_string("Output format? (jpg / png / webp / keep)", initial="keep")
           or "keep").lower().lstrip(".")
    max_dim = ui.ask_string("Max width/height in px? (blank = no resize)") or ""
    outdir = ui.ask_directory("Choose an output folder")
    if not outdir:
        return
    max_px = int(max_dim) if max_dim.strip().isdigit() else None

    r = core.Report("Batch Convert / Resize")
    r.section(f"{len(files)} file(s) -> {outdir}")
    done = 0
    for i, f in enumerate(files, 1):
        print(f"\r  processing {i}/{len(files)}", end="", flush=True)
        try:
            with Image.open(f) as im:
                if max_px:
                    im.thumbnail((max_px, max_px))
                src = Path(f)
                ext = src.suffix.lstrip(".") if fmt == "keep" else fmt
                if ext.lower() in ("jpg", "jpeg") and im.mode in ("RGBA", "P"):
                    im = im.convert("RGB")
                out = Path(outdir) / f"{src.stem}.{ext}"
                im.save(out)
                done += 1
        except Exception as exc:
            r.finding("WARN", f"{Path(f).name}: {exc}")
    print()
    r.finding("PASS", f"{done}/{len(files)} images written to {outdir}")
    ui.deliver_report(r, "Batch_Convert")


# --------------------------------------------------------------------------- #
#  Duplicate finder (content hash)
# --------------------------------------------------------------------------- #

def find_duplicates(ctx=None) -> None:
    ui.clear(); ui.title_bar("Duplicate Finder", "find identical files by content hash")
    folder = ui.ask_directory("Choose a folder to scan (recursive)")
    if not folder:
        return
    seen: dict[str, list[str]] = {}
    files = [p for p in Path(folder).rglob("*") if p.is_file()]
    ui.info(f"Hashing {len(files)} file(s)...")
    for i, p in enumerate(files, 1):
        print(f"\r  {i}/{len(files)}", end="", flush=True)
        try:
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                while chunk := fh.read(1024 * 1024):
                    h.update(chunk)
            seen.setdefault(h.hexdigest(), []).append(str(p))
        except Exception:
            continue
    print()
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    r = core.Report("Duplicate Finder")
    r.section(folder)
    if not dupes:
        r.finding("PASS", "no duplicate files found")
    else:
        wasted = 0
        for digest, paths in dupes.items():
            r.line(f"\n  {len(paths)} copies (sha256 {digest[:12]}...):")
            for pth in paths:
                r.line(f"    {pth}")
            try:
                wasted += os.path.getsize(paths[0]) * (len(paths) - 1)
            except Exception:
                pass
        r.finding("WARN", f"{len(dupes)} duplicate set(s); "
                  f"~{wasted / 1024 / 1024:.1f} MB reclaimable", "MEDIUM",
                  "Duplicate files wasting space")
    ui.deliver_report(r, "Duplicate_Finder")


# --------------------------------------------------------------------------- #
#  Media metadata (ffprobe)
# --------------------------------------------------------------------------- #

def media_metadata(ctx=None) -> None:
    ui.clear(); ui.title_bar("Audio/Video Metadata", "codecs, duration, bitrate")
    if not core.have("ffprobe"):
        ui.popup_info(
            "ffprobe (part of ffmpeg) is not installed.\n\n"
            "Install it once with:\n    winget install Gyan.FFmpeg\n\n"
            "Then this tool reads codecs, duration, bitrate, resolution for any "
            "audio/video file. Image tools work without it.", "ffmpeg needed")
        ui.pause(); return
    path = ui.ask_open_file("Choose an audio/video file")
    if not path:
        return
    out = core.run(["ffprobe", "-hide_banner", "-v", "error", "-show_format",
                    "-show_streams", path], timeout=60)
    ui.show_text(out or "(no output)", "Ultra-PC — Media Metadata")
    ui.pause()


# --------------------------------------------------------------------------- #
#  Registration
# --------------------------------------------------------------------------- #

def register() -> core.Category:
    from . import mediaconv
    cat = core.Category("media", "Media Tools")
    cat.add("inspect", "Image inspector (EXIF / dimensions)", image_inspector)
    cat.add("integ", "Image integrity check (folder scan)", integrity_check)
    cat.add("conv", "Batch convert / resize images", batch_convert)
    cat.add("aconv", "Convert audio  (safe, originals kept)", mediaconv.audio_convert)
    cat.add("vconv", "Convert video  (safe, originals kept)", mediaconv.video_convert)
    cat.add("aextract", "Extract audio from video", mediaconv.extract_audio)
    cat.add("anorm", "Normalize audio loudness (safe)", mediaconv.normalize_audio)
    cat.add("trim", "Trim / cut a clip (safe)", mediaconv.trim_media)
    cat.add("dupe", "Duplicate file finder", find_duplicates)
    cat.add("meta", "Audio/Video metadata (ffprobe)", media_metadata)
    cat.add("cvstatus", "Conversion engine status / install ffmpeg", mediaconv.convert_status)
    return cat
