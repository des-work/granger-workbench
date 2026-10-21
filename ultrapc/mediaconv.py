"""Safe media conversion for the toolkit.

Design rule #1: NEVER corrupt or lose the source. Every conversion:
  * reads the source read-only (ffmpeg never writes to the input path),
  * writes to a temporary ".partial" file in the output folder,
  * verifies the result actually decodes (ffprobe streams + duration sanity),
  * only then atomically moves it into place, and
  * never overwrites an existing file (auto-suffixes " (1)", " (2)", ...).
On any failure the temp file is removed and the source is left untouched.

Audio/video needs ffmpeg; a portable copy can be fetched into tools/ffmpeg.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import core, ui

FF_DIR = core.ROOT / "tools" / "ffmpeg"
# Self-contained static Windows build (no admin install needed).
FFMPEG_URL = ("https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/"
              "ffmpeg-master-latest-win64-gpl.zip")


# --------------------------------------------------------------------------- #
#  ffmpeg / ffprobe location & bootstrap
# --------------------------------------------------------------------------- #

def _bin(name: str) -> str | None:
    exe = name + (".exe" if core.IS_WINDOWS else "")
    local = FF_DIR / exe
    if local.exists():
        return str(local)
    return shutil.which(name)


def ffmpeg_bin() -> str | None:
    return _bin("ffmpeg")


def ffprobe_bin() -> str | None:
    return _bin("ffprobe")


def have_ffmpeg() -> bool:
    return bool(ffmpeg_bin() and ffprobe_bin())


def ensure_ffmpeg(interactive: bool = True) -> bool:
    """Return True if ffmpeg+ffprobe are usable, fetching a portable copy if not."""
    if have_ffmpeg():
        return True
    if not core.IS_WINDOWS:
        if interactive:
            ui.popup_error("ffmpeg not found. Install it via your package manager "
                           "(e.g. apt install ffmpeg).")
        return False
    if interactive and not ui.ask_yesno(
            "Audio/video conversion needs ffmpeg, which isn't installed.\n\n"
            "Download a portable copy (~100 MB) into the toolkit now?\n"
            "(One-time; no admin required.)", "Get ffmpeg"):
        return False
    FF_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = FF_DIR / "ffmpeg.zip"
    ui.info("Downloading portable ffmpeg (~100 MB)...")
    rc = subprocess.call(["curl", "-L", "--ssl-no-revoke", "-o", str(zip_path),
                          FFMPEG_URL])
    if rc != 0 or not zip_path.exists():
        ui.err("ffmpeg download failed."); return False
    ui.info("Extracting...")
    try:
        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(FF_DIR)
        # copy ffmpeg.exe / ffprobe.exe out of the nested bin/ folder
        for exe in ("ffmpeg.exe", "ffprobe.exe"):
            found = next(FF_DIR.rglob(exe), None)
            if found and found.parent != FF_DIR:
                shutil.copy2(found, FF_DIR / exe)
        zip_path.unlink(missing_ok=True)
    except Exception as exc:
        ui.err(f"Extraction failed: {exc}"); return False
    if have_ffmpeg():
        core.log("mediaconv", "portable ffmpeg installed", "SUCCESS")
        ui.ok("ffmpeg ready.")
        return True
    ui.err("ffmpeg still not found after extraction.")
    return False


# --------------------------------------------------------------------------- #
#  Format presets
# --------------------------------------------------------------------------- #

AUDIO_PRESETS = {
    "mp3":  ["-c:a", "libmp3lame", "-q:a", "2"],
    "wav":  ["-c:a", "pcm_s16le"],
    "flac": ["-c:a", "flac"],
    "m4a":  ["-c:a", "aac", "-b:a", "192k"],
    "ogg":  ["-c:a", "libvorbis", "-q:a", "5"],
    "opus": ["-c:a", "libopus", "-b:a", "128k"],
}

VIDEO_PRESETS = {
    "mp4":  ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"],
    "mkv":  ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-c:a", "aac", "-b:a", "192k"],
    "webm": ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
             "-c:a", "libopus"],
    "mov":  ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-c:a", "aac", "-b:a", "192k"],
}

AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".wmv", ".flv", ".m4v"}


# --------------------------------------------------------------------------- #
#  Probe & verify
# --------------------------------------------------------------------------- #

def probe(path: str | Path) -> dict | None:
    out = core.run([ffprobe_bin(), "-v", "error", "-show_format",
                    "-show_streams", "-of", "json", str(path)], timeout=120)
    try:
        return json.loads(out)
    except Exception:
        return None


def _duration(info: dict | None) -> float | None:
    if not info:
        return None
    try:
        return float(info.get("format", {}).get("duration"))
    except (TypeError, ValueError):
        return None


def verify_output(path: Path, kind: str, src_duration: float | None,
                  verify_duration: bool = True) -> tuple[bool, str]:
    """Confirm the converted file decodes and (optionally) wasn't truncated.

    verify_duration=False is used by operations that intentionally change the
    length (silence-trim, speed change); the decode + stream checks still run.
    """
    if not path.exists() or path.stat().st_size == 0:
        return False, "output missing or empty"
    info = probe(path)
    if not info:
        return False, "output not decodable (ffprobe failed)"
    streams = info.get("streams", [])
    kinds = {s.get("codec_type") for s in streams}
    if kind == "audio" and "audio" not in kinds:
        return False, "no audio stream in output"
    if kind == "video" and "video" not in kinds:
        return False, "no video stream in output"
    out_dur = _duration(info)
    if verify_duration and src_duration and out_dur:
        # allow small container/encoder differences; flag real truncation
        if abs(out_dur - src_duration) > max(1.0, 0.05 * src_duration):
            return False, (f"duration mismatch (src {src_duration:.1f}s vs "
                           f"out {out_dur:.1f}s) — possible truncation")
    return True, f"verified ({out_dur:.1f}s)" if out_dur else "verified"


# --------------------------------------------------------------------------- #
#  Safe conversion
# --------------------------------------------------------------------------- #

def _unique(path: Path) -> Path:
    """Return a non-existing path, auto-suffixing ' (n)' to avoid overwrite."""
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    n = 1
    while True:
        cand = parent / f"{stem} ({n}){suffix}"
        if not cand.exists():
            return cand
        n += 1


def convert_one(src: str | Path, out_dir: str | Path, target_ext: str,
                kind: str, args: list[str], pre_args: list[str] | None = None,
                expected_duration: float | None = None,
                out_stem_suffix: str = "", verify_duration: bool = True) -> dict:
    """Safely convert one file. Returns {ok, src, out, detail}.

    pre_args           : ffmpeg args placed BEFORE -i (e.g. input -ss seek).
    expected_duration  : verify against this instead of the source duration
                         (used by trim, where the output is intentionally shorter).
    out_stem_suffix    : appended to the output name (e.g. " (trimmed)").
    """
    src = Path(src)
    out_dir = Path(out_dir)
    target_ext = target_ext.lower().lstrip(".")
    result = {"ok": False, "src": str(src), "out": "", "detail": ""}

    if not src.exists():
        result["detail"] = "source not found"
        return result
    out_dir.mkdir(parents=True, exist_ok=True)

    final = _unique(out_dir / f"{src.stem}{out_stem_suffix}.{target_ext}")
    # extra guard: never let output resolve to the source path
    try:
        if final.resolve() == src.resolve():
            final = _unique(out_dir / f"{src.stem}{out_stem_suffix} (converted).{target_ext}")
    except Exception:
        pass
    # Keep the REAL extension so ffmpeg can infer the output container;
    # a mid-name marker keeps it distinct from the final file.
    tmp = final.with_name(f"{final.stem}.ultrapart{final.suffix}")

    cmd = [ffmpeg_bin(), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
           *(pre_args or []), "-i", str(src), *args, str(tmp)]
    try:
        rc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600).returncode
    except subprocess.TimeoutExpired:
        tmp.unlink(missing_ok=True)
        result["detail"] = "conversion timed out"
        return result
    if rc != 0:
        tmp.unlink(missing_ok=True)
        result["detail"] = f"ffmpeg exit {rc}"
        return result

    check_dur = expected_duration if expected_duration is not None else _duration(probe(src))
    ok, detail = verify_output(tmp, kind, check_dur, verify_duration)
    if not ok:
        tmp.unlink(missing_ok=True)          # discard bad output; source safe
        result["detail"] = f"rejected: {detail}"
        return result

    os.replace(tmp, final)                    # atomic within the same folder
    result.update(ok=True, out=str(final), detail=detail)
    return result


# --------------------------------------------------------------------------- #
#  Interactive tools
# --------------------------------------------------------------------------- #

def _run_batch(files: list[str], out_dir: str, target_ext: str, kind: str,
               args: list[str], title: str, slug: str) -> None:
    r = core.Report(title)
    r.section(f"{len(files)} file(s) -> {out_dir}  (format: {target_ext})")
    r.line("  Source files are never modified. Failed items leave the original intact.")
    ok = 0
    for i, f in enumerate(files, 1):
        name = Path(f).name
        print(f"\r  converting {i}/{len(files)}: {name[:40]:<40}", end="", flush=True)
        res = convert_one(f, out_dir, target_ext, kind, args)
        if res["ok"]:
            ok += 1
            r.finding("PASS", f"{name} -> {Path(res['out']).name}  [{res['detail']}]")
        else:
            r.finding("FAIL", f"{name}: {res['detail']}", "MEDIUM",
                      "Some files failed to convert (originals untouched)")
    print()
    r.line(f"\n  Succeeded: {ok}/{len(files)}. Originals left unchanged.")
    ui.deliver_report(r, slug)


def _pick_format(kind: str) -> str | None:
    presets = AUDIO_PRESETS if kind == "audio" else VIDEO_PRESETS
    items = [(str(i + 1), fmt.upper()) for i, fmt in enumerate(presets)]
    items.append((str(len(presets) + 1), "Remux only — change container, NO re-encode "
                                          "(lossless, fastest)"))
    choice = ui.menu(f"Target {kind} format", "pick an output format", items, "Cancel")
    if choice == "0" or not choice or not choice.isdigit():
        return None
    idx = int(choice) - 1
    keys = list(presets)
    if idx == len(keys):
        return "__remux__"
    if 0 <= idx < len(keys):
        return keys[idx]
    return None


def audio_args(fmt: str, quality: str | None = None) -> list[str]:
    """Build audio codec args. quality is a bitrate like '192k', or 'vbr'/None."""
    if fmt == "wav":
        return ["-c:a", "pcm_s16le"]
    if fmt == "flac":
        return ["-c:a", "flac"]
    if fmt == "mp3":
        if quality in (None, "vbr"):
            return ["-c:a", "libmp3lame", "-q:a", "2"]       # ~190 kbps VBR
        return ["-c:a", "libmp3lame", "-b:a", quality]
    if fmt == "m4a":
        return ["-c:a", "aac", "-b:a", quality or "192k"]
    if fmt == "ogg":
        return ["-c:a", "libvorbis", "-b:a", quality or "192k"]
    if fmt == "opus":
        return ["-c:a", "libopus", "-b:a", quality or "128k"]
    return AUDIO_PRESETS.get(fmt, [])


def _pick_audio_quality(fmt: str) -> str | None:
    """Return a bitrate ('192k'), 'vbr', or None if cancelled. Lossless -> 'vbr'."""
    if fmt in ("wav", "flac"):
        return "vbr"      # ignored for lossless
    items = [("1", "128 kbps — small"), ("2", "192 kbps — good (default)"),
             ("3", "256 kbps — high"), ("4", "320 kbps — maximum")]
    if fmt == "mp3":
        items.append(("5", "VBR ~190 kbps — recommended"))
    choice = ui.menu(f"Audio quality ({fmt.upper()})", "pick a bitrate", items, "Cancel")
    return {"1": "128k", "2": "192k", "3": "256k", "4": "320k",
            "5": "vbr"}.get(choice)


def audio_convert(ctx=None) -> None:
    ui.clear(); ui.title_bar("Audio Conversion", "safe — originals never modified")
    if not ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose audio files to convert",
                              [("Audio", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus *.wma"),
                               ("All files", "*.*")])
    if not files:
        return
    fmt = _pick_format("audio")
    if not fmt:
        return
    if fmt == "__remux__":
        target = Path(files[0]).suffix.lstrip(".") or "mkv"
        args, target_ext = ["-c", "copy"], target
    else:
        quality = _pick_audio_quality(fmt)
        if quality is None:
            return
        args, target_ext = audio_args(fmt, quality), fmt
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return
    _run_batch(files, out_dir, target_ext, "audio", args,
               "Audio Conversion", "Audio_Convert")


def video_convert(ctx=None) -> None:
    ui.clear(); ui.title_bar("Video Conversion", "safe — originals never modified")
    if not ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose video files to convert",
                              [("Video", "*.mp4 *.mkv *.webm *.mov *.avi *.wmv *.flv *.m4v"),
                               ("All files", "*.*")])
    if not files:
        return
    fmt = _pick_format("video")
    if not fmt:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return
    if fmt == "__remux__":
        target = Path(files[0]).suffix.lstrip(".") or "mkv"
        args, target_ext = ["-c", "copy"], target
        ui.dim("Remux keeps the exact streams — only the container changes.")
    else:
        args, target_ext = VIDEO_PRESETS[fmt], fmt
        ui.warn("Re-encoding video can take a while; this taxes the CPU/GPU.")
    _run_batch(files, out_dir, target_ext, "video", args,
               "Video Conversion", "Video_Convert")


def extract_audio(ctx=None) -> None:
    ui.clear(); ui.title_bar("Extract Audio from Video", "safe — originals untouched")
    if not ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose video files",
                              [("Video", "*.mp4 *.mkv *.webm *.mov *.avi *.wmv *.flv *.m4v"),
                               ("All files", "*.*")])
    if not files:
        return
    fmt = _pick_format("audio")
    if not fmt or fmt == "__remux__":
        if fmt == "__remux__":
            ui.warn("Remux isn't applicable when extracting; pick a real format.")
            ui.pause()
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return
    args = ["-vn", *AUDIO_PRESETS[fmt]]        # -vn drops the video stream
    _run_batch(files, out_dir, fmt, "audio", args,
               "Extract Audio", "Extract_Audio")


# --------------------------------------------------------------------------- #
#  Loudness normalization (two-pass EBU R128 loudnorm)
# --------------------------------------------------------------------------- #

def _measure_loudnorm(src: Path, tgt_i: float, tp: float = -1.5,
                      lra: float = 11.0) -> dict | None:
    """First pass: measure loudness so the second pass can normalize linearly."""
    cmd = [ffmpeg_bin(), "-hide_banner", "-nostdin", "-i", str(src),
           "-af", f"loudnorm=I={tgt_i}:TP={tp}:LRA={lra}:print_format=json",
           "-f", "null", "-"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return None
    m = re.search(r"\{[^{}]*\"input_i\"[\s\S]*?\}", p.stderr or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def normalize_audio(ctx=None) -> None:
    ui.clear(); ui.title_bar("Normalize Audio Loudness", "EBU R128 — originals kept")
    if not ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose audio files to normalize",
                              [("Audio", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus *.wma"),
                               ("All files", "*.*")])
    if not files:
        return
    tgt_items = [("1", "-16 LUFS — general / podcasts (default)"),
                 ("2", "-14 LUFS — streaming (Spotify/YouTube)"),
                 ("3", "-23 LUFS — broadcast (EBU R128)")]
    tchoice = ui.menu("Target loudness", "how loud should the result be?",
                      tgt_items, "Cancel")
    target = {"1": -16.0, "2": -14.0, "3": -23.0}.get(tchoice)
    if target is None:
        return
    fmt_items = [(str(i + 1), f.upper()) for i, f in enumerate(AUDIO_PRESETS)]
    fchoice = ui.menu("Output format", "normalization re-encodes the audio",
                      fmt_items, "Cancel")
    if fchoice == "0" or not fchoice or not fchoice.isdigit():
        return
    keys = list(AUDIO_PRESETS)
    if not (1 <= int(fchoice) <= len(keys)):
        return
    fmt = keys[int(fchoice) - 1]
    quality = _pick_audio_quality(fmt)
    if quality is None:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return

    r = core.Report("Audio Normalization")
    r.section(f"{len(files)} file(s) -> {out_dir}  (target {target} LUFS, {fmt})")
    r.line("  Two-pass loudnorm. Sources are never modified.")
    ok = 0
    for i, f in enumerate(files, 1):
        name = Path(f).name
        print(f"\r  normalizing {i}/{len(files)}: measuring {name[:34]:<34}",
              end="", flush=True)
        meas = _measure_loudnorm(Path(f), target)
        if meas:
            af = (f"loudnorm=I={target}:TP=-1.5:LRA=11:"
                  f"measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:"
                  f"measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}:"
                  f"offset={meas['target_offset']}:linear=true")
            pass_note = "2-pass"
        else:
            af = f"loudnorm=I={target}:TP=-1.5:LRA=11"     # single-pass fallback
            pass_note = "1-pass"
        print(f"\r  normalizing {i}/{len(files)}: encoding  {name[:34]:<34}",
              end="", flush=True)
        args = ["-af", af, *audio_args(fmt, quality)]
        res = convert_one(f, out_dir, fmt, "audio", args,
                          out_stem_suffix=" (normalized)")
        if res["ok"]:
            ok += 1
            r.finding("PASS", f"{name} -> {Path(res['out']).name}  "
                              f"[{pass_note}, {res['detail']}]")
        else:
            r.finding("FAIL", f"{name}: {res['detail']}", "MEDIUM",
                      "Some files failed to normalize (originals untouched)")
    print()
    r.line(f"\n  Succeeded: {ok}/{len(files)}. Originals left unchanged.")
    ui.deliver_report(r, "Audio_Normalize")


# --------------------------------------------------------------------------- #
#  Trim / cut
# --------------------------------------------------------------------------- #

def parse_time(s: str) -> float | None:
    """Parse 'HH:MM:SS(.ms)', 'MM:SS', or plain seconds -> seconds."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        if ":" in s:
            total = 0.0
            for part in s.split(":"):
                total = total * 60 + float(part)
            return total
        return float(s)
    except ValueError:
        return None


def trim_media(ctx=None) -> None:
    ui.clear(); ui.title_bar("Trim / Cut Clip", "extract a section — originals kept")
    if not ensure_ffmpeg():
        ui.pause(); return
    src = ui.ask_open_file("Choose an audio/video file to trim",
                           [("Media", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus "
                                      "*.mp4 *.mkv *.webm *.mov *.avi *.wmv *.flv *.m4v"),
                            ("All files", "*.*")])
    if not src:
        return
    total = _duration(probe(src))
    if total:
        ui.info(f"Clip length: {total:.1f}s")
    start = parse_time(ui.ask_string("Start time (HH:MM:SS or seconds; blank = 0):",
                                     initial="0") or "0")
    end = parse_time(ui.ask_string("End time (HH:MM:SS or seconds):") or "")
    if start is None or end is None or end <= start:
        ui.popup_error("Need a valid start and end, with end after start.")
        ui.pause(); return
    if total and end > total + 0.5:
        ui.warn(f"End {end:.1f}s is past the clip length ({total:.1f}s); "
                "it will stop at the real end.")
        end = total
    dur = end - start

    ext = Path(src).suffix.lstrip(".").lower()
    kind = "video" if f".{ext}" in VIDEO_EXTS else "audio"
    mode_items = [("1", "Fast — stream copy, no re-encode (keyframe-accurate, lossless)"),
                  ("2", "Precise — re-encode (frame-accurate)")]
    mode = ui.menu("Trim mode", "how should I cut it?", mode_items, "Cancel")
    if mode == "0" or not mode:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return

    if mode == "1":       # fast: input-seek + stream copy
        pre_args = ["-ss", f"{start}"]
        args = ["-t", f"{dur}", "-c", "copy"]
        target_ext = ext
    else:                 # precise: output-seek + re-encode
        pre_args = None
        if kind == "video":
            args = ["-ss", f"{start}", "-t", f"{dur}",
                    *VIDEO_PRESETS.get(ext, VIDEO_PRESETS["mp4"])]
            target_ext = ext if ext in VIDEO_PRESETS else "mp4"
        else:
            target_ext = ext if ext in AUDIO_PRESETS else "mp3"
            args = ["-ss", f"{start}", "-t", f"{dur}", *audio_args(target_ext)]

    ui.info(f"Cutting {start:.1f}s → {end:.1f}s ({dur:.1f}s)...")
    res = convert_one(src, out_dir, target_ext, kind, args, pre_args=pre_args,
                      expected_duration=dur, out_stem_suffix=" (trimmed)")
    r = core.Report("Trim / Cut")
    r.section(f"{Path(src).name}  →  {start:.1f}s to {end:.1f}s")
    r.line("  Source file is never modified.")
    if res["ok"]:
        r.finding("PASS", f"Saved {Path(res['out']).name}  [{res['detail']}]")
    else:
        r.finding("FAIL", res["detail"], "MEDIUM", "Trim failed (original untouched)")
    ui.deliver_report(r, "Trim_Cut")


def convert_status(ctx=None) -> None:
    ui.clear(); ui.title_bar("Media Conversion — Status", "engine & tooling")
    print()
    ui.info(f"ffmpeg:  {ffmpeg_bin() or 'NOT INSTALLED'}")
    ui.info(f"ffprobe: {ffprobe_bin() or 'NOT INSTALLED'}")
    ui.info(f"Safety:  temp-write + decode-verify + no-overwrite; sources read-only")
    print()
    if not have_ffmpeg() and ui.ask_yesno("Install portable ffmpeg now?", "ffmpeg"):
        ensure_ffmpeg(interactive=False) if have_ffmpeg() else ensure_ffmpeg()
    ui.pause()
