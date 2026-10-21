"""Audio Studio — restoration & processing built on the safe conversion engine.

Aimed at the analog-capture workflow (cassettes, vinyl, VHS audio via a USB
adapter): clean up hiss/hum, declick vinyl, fade, trim dead air, split a whole
album side into per-track files, adjust gain, and analyze levels.

Every tool that writes a file goes through mediaconv.convert_one, so the source
is never modified and outputs are decode-verified before they're kept.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import core, ui
from . import mediaconv as mc

AUDIO_FILTER = [("Audio", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus *.wma"),
                ("All files", "*.*")]


# --------------------------------------------------------------------------- #
#  Shared helpers
# --------------------------------------------------------------------------- #

def _pick_output(default_fmt: str = "flac"):
    """Ask output format + quality. Returns (fmt, quality) or (None, None)."""
    keys = list(mc.AUDIO_PRESETS)
    items = [(str(i + 1), f.upper() + ("  (lossless)" if f in ("wav", "flac") else ""))
             for i, f in enumerate(keys)]
    choice = ui.menu("Output format", "how to save the result", items, "Cancel")
    if choice == "0" or not choice or not choice.isdigit() or not (1 <= int(choice) <= len(keys)):
        return None, None
    fmt = keys[int(choice) - 1]
    quality = mc._pick_audio_quality(fmt)
    if quality is None:
        return None, None
    return fmt, quality


def _fx_batch(files, out_dir, fmt, quality, af, suffix, title, slug,
              verify_duration=True) -> None:
    r = core.Report(title)
    r.section(f"{len(files)} file(s) -> {out_dir}  (format {fmt})")
    r.line(f"  Filter: {af or '(none)'}")
    r.line("  Sources are never modified.")
    ok = 0
    for i, f in enumerate(files, 1):
        name = Path(f).name
        print(f"\r  processing {i}/{len(files)}: {name[:40]:<40}", end="", flush=True)
        args = (["-af", af] if af else []) + mc.audio_args(fmt, quality)
        res = mc.convert_one(f, out_dir, fmt, "audio", args, out_stem_suffix=suffix,
                             verify_duration=verify_duration)
        if res["ok"]:
            ok += 1
            r.finding("PASS", f"{name} -> {Path(res['out']).name}  [{res['detail']}]")
        else:
            r.finding("FAIL", f"{name}: {res['detail']}", "MEDIUM",
                      "Some files failed (originals untouched)")
    print()
    r.line(f"\n  Succeeded: {ok}/{len(files)}. Originals left unchanged.")
    ui.deliver_report(r, slug)


# --------------------------------------------------------------------------- #
#  Cleanup / restore  (denoise, de-hum, vinyl declick)
# --------------------------------------------------------------------------- #

RESTORE_PRESETS = {
    "1": ("Voice cleanup (mic/podcast)",
          "highpass=f=90,afftdn=nr=12"),
    "2": ("Tape hiss reduction",
          "afftdn=nr=24:nf=-30,lowpass=f=15000"),
    "3": ("Remove 50 Hz mains hum",
          "highpass=f=35,equalizer=f=50:t=q:w=8:g=-40,"
          "equalizer=f=100:t=q:w=8:g=-30,equalizer=f=150:t=q:w=8:g=-24"),
    "4": ("Remove 60 Hz mains hum",
          "highpass=f=35,equalizer=f=60:t=q:w=8:g=-40,"
          "equalizer=f=120:t=q:w=8:g=-30,equalizer=f=180:t=q:w=8:g=-24"),
    "5": ("Vinyl restore (declick + declip)",
          "highpass=f=30,adeclick,adeclip"),
    "6": ("Gentle broadband denoise",
          "afftdn=nr=10"),
}


def restore_audio(ctx=None) -> None:
    ui.clear(); ui.title_bar("Clean Up / Restore Audio", "denoise · de-hum · declick")
    if not mc.ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose audio files to clean up", AUDIO_FILTER)
    if not files:
        return
    items = [(k, v[0]) for k, v in RESTORE_PRESETS.items()]
    choice = ui.menu("Restoration preset", "pick a cleanup profile", items, "Cancel")
    if choice not in RESTORE_PRESETS:
        return
    label, af = RESTORE_PRESETS[choice]
    fmt, quality = _pick_output()
    if not fmt:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return
    ui.info(f"Applying: {label}")
    _fx_batch(files, out_dir, fmt, quality, af, " (cleaned)",
              f"Audio Restore — {label}", "Audio_Restore")


# --------------------------------------------------------------------------- #
#  Fade in / out
# --------------------------------------------------------------------------- #

def fade_audio(ctx=None) -> None:
    ui.clear(); ui.title_bar("Fade In / Out", "smooth starts and endings")
    if not mc.ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose audio files", AUDIO_FILTER)
    if not files:
        return
    fin = mc.parse_time(ui.ask_string("Fade-IN seconds (blank = 0):", initial="0") or "0") or 0
    fout = mc.parse_time(ui.ask_string("Fade-OUT seconds (blank = 0):", initial="0") or "0") or 0
    if fin <= 0 and fout <= 0:
        ui.popup_error("Enter a fade-in and/or fade-out length."); ui.pause(); return
    fmt, quality = _pick_output()
    if not fmt:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return
    r = core.Report("Audio Fade")
    r.section(f"{len(files)} file(s)  fade-in {fin}s / fade-out {fout}s -> {out_dir}")
    r.line("  Sources are never modified.")
    ok = 0
    for i, f in enumerate(files, 1):
        name = Path(f).name
        print(f"\r  processing {i}/{len(files)}: {name[:40]:<40}", end="", flush=True)
        total = mc._duration(mc.probe(f))
        parts = []
        if fin > 0:
            parts.append(f"afade=t=in:st=0:d={fin}")
        if fout > 0 and total:
            parts.append(f"afade=t=out:st={max(0, total - fout):.3f}:d={fout}")
        af = ",".join(parts)
        args = ["-af", af, *mc.audio_args(fmt, quality)]
        res = mc.convert_one(f, out_dir, fmt, "audio", args, out_stem_suffix=" (faded)")
        if res["ok"]:
            ok += 1; r.finding("PASS", f"{name} -> {Path(res['out']).name}")
        else:
            r.finding("FAIL", f"{name}: {res['detail']}", "MEDIUM",
                      "Some files failed (originals untouched)")
    print()
    r.line(f"\n  Succeeded: {ok}/{len(files)}.")
    ui.deliver_report(r, "Audio_Fade")


# --------------------------------------------------------------------------- #
#  Trim silence (dead air at start/end)
# --------------------------------------------------------------------------- #

def trim_silence(ctx=None) -> None:
    ui.clear(); ui.title_bar("Trim Silence", "remove dead air at start & end")
    if not mc.ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose audio files", AUDIO_FILTER)
    if not files:
        return
    thr = ui.ask_string("Silence threshold in dB (quieter = more aggressive; "
                        "default -50):", initial="-50") or "-50"
    try:
        thr = int(float(thr))
    except ValueError:
        thr = -50
    fmt, quality = _pick_output()
    if not fmt:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return
    af = (f"silenceremove=start_periods=1:start_duration=0.05:start_threshold={thr}dB:"
          f"detection=peak,areverse,"
          f"silenceremove=start_periods=1:start_duration=0.05:start_threshold={thr}dB:"
          f"detection=peak,areverse")
    _fx_batch(files, out_dir, fmt, quality, af, " (trimmed)",
              "Trim Silence", "Trim_Silence", verify_duration=False)


# --------------------------------------------------------------------------- #
#  Gain / amplify / peak-normalize
# --------------------------------------------------------------------------- #

def _max_volume(src: Path) -> float | None:
    cmd = [mc.ffmpeg_bin(), "-nostdin", "-hide_banner", "-i", str(src),
           "-af", "volumedetect", "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", p.stderr or "")
    return float(m.group(1)) if m else None


def gain_audio(ctx=None) -> None:
    ui.clear(); ui.title_bar("Gain / Amplify", "adjust volume safely")
    if not mc.ensure_ffmpeg():
        ui.pause(); return
    files = ui.ask_open_files("Choose audio files", AUDIO_FILTER)
    if not files:
        return
    mode = ui.menu("Gain mode", "how to change the level",
                   [("1", "Amplify / attenuate by a fixed dB"),
                    ("2", "Peak-normalize to -1 dBFS (per file)")], "Cancel")
    if mode == "0" or not mode:
        return
    fmt, quality = _pick_output()
    if not fmt:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return

    if mode == "1":
        db = ui.ask_string("Gain in dB (e.g. 3 to boost, -3 to reduce):", initial="3") or "0"
        try:
            db = float(db)
        except ValueError:
            db = 0.0
        _fx_batch(files, out_dir, fmt, quality, f"volume={db}dB", " (gain)",
                  "Audio Gain", "Audio_Gain")
        return

    # peak normalize: measure each file, apply the exact gain to hit -1 dBFS
    r = core.Report("Peak Normalize")
    r.section(f"{len(files)} file(s) -> {out_dir}  (target -1 dBFS)")
    r.line("  Sources are never modified.")
    ok = 0
    for i, f in enumerate(files, 1):
        name = Path(f).name
        print(f"\r  processing {i}/{len(files)}: {name[:40]:<40}", end="", flush=True)
        mv = _max_volume(Path(f))
        gain = (-1.0 - mv) if mv is not None else 0.0
        args = ["-af", f"volume={gain:.2f}dB", *mc.audio_args(fmt, quality)]
        res = mc.convert_one(f, out_dir, fmt, "audio", args, out_stem_suffix=" (normalized)")
        if res["ok"]:
            ok += 1
            r.finding("PASS", f"{name}: applied {gain:+.1f} dB -> {Path(res['out']).name}")
        else:
            r.finding("FAIL", f"{name}: {res['detail']}", "MEDIUM",
                      "Some files failed (originals untouched)")
    print()
    r.line(f"\n  Succeeded: {ok}/{len(files)}.")
    ui.deliver_report(r, "Peak_Normalize")


# --------------------------------------------------------------------------- #
#  Split a long recording into tracks by silence
# --------------------------------------------------------------------------- #

def _detect_silences(src: Path, thr_db: int, min_sil: float) -> list[tuple[float, float]]:
    cmd = [mc.ffmpeg_bin(), "-nostdin", "-hide_banner", "-i", str(src),
           "-af", f"silencedetect=noise={thr_db}dB:d={min_sil}", "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    txt = p.stderr or ""
    starts = [float(m) for m in re.findall(r"silence_start:\s*(-?[\d.]+)", txt)]
    ends = [float(m) for m in re.findall(r"silence_end:\s*([\d.]+)", txt)]
    return list(zip(starts, ends[:len(starts)]))


def split_by_silence(ctx=None) -> None:
    ui.clear(); ui.title_bar("Split Into Tracks", "digitize an album side by silence")
    if not mc.ensure_ffmpeg():
        ui.pause(); return
    src = ui.ask_open_file("Choose the long recording to split", AUDIO_FILTER)
    if not src:
        return
    total = mc._duration(mc.probe(src))
    if not total:
        ui.popup_error("Could not read the recording length."); ui.pause(); return
    thr = ui.ask_string("Silence threshold dB (default -35):", initial="-35") or "-35"
    minsil = ui.ask_string("Minimum gap between tracks in seconds (default 1.0):",
                           initial="1.0") or "1.0"
    try:
        thr = int(float(thr)); minsil = float(minsil)
    except ValueError:
        thr, minsil = -35, 1.0
    mintrack = 3.0   # ignore blips shorter than this

    ui.info("Detecting silences...")
    silences = _detect_silences(Path(src), thr, minsil)

    # Build track segments from the gaps between silences.
    segments, cursor = [], 0.0
    for s_start, s_end in silences:
        if s_start - cursor >= mintrack:
            segments.append((cursor, s_start))
        cursor = s_end
    if total - cursor >= mintrack:
        segments.append((cursor, total))
    if not segments:
        ui.warn("No track boundaries found — try a higher threshold or shorter gap.")
        ui.pause(); return

    ui.ok(f"Found {len(segments)} track(s).")
    fmt, quality = _pick_output()
    if not fmt:
        return
    out_dir = ui.ask_directory("Choose an output folder")
    if not out_dir:
        return

    r = core.Report("Split Into Tracks")
    r.section(f"{Path(src).name} -> {len(segments)} track(s) in {out_dir}")
    r.line("  Source recording is never modified.")
    ok = 0
    for n, (start, end) in enumerate(segments, 1):
        dur = end - start
        print(f"\r  track {n}/{len(segments)}: {start:.1f}-{end:.1f}s      ", end="", flush=True)
        args = ["-ss", f"{start}", "-t", f"{dur}", *mc.audio_args(fmt, quality)]
        res = mc.convert_one(src, out_dir, fmt, "audio", args,
                             expected_duration=dur,
                             out_stem_suffix=f" - Track {n:02d}")
        if res["ok"]:
            ok += 1
            r.finding("PASS", f"Track {n:02d}  [{start:.1f}-{end:.1f}s]  "
                              f"-> {Path(res['out']).name}")
        else:
            r.finding("FAIL", f"Track {n:02d}: {res['detail']}", "MEDIUM",
                      "Some tracks failed (original untouched)")
    print()
    r.line(f"\n  Extracted {ok}/{len(segments)} tracks. Original untouched.")
    ui.deliver_report(r, "Split_Tracks")


# --------------------------------------------------------------------------- #
#  Analyze levels (read-only — writes nothing)
# --------------------------------------------------------------------------- #

def analyze_audio(ctx=None) -> None:
    ui.clear(); ui.title_bar("Analyze Audio Levels", "peak · RMS · loudness · clipping")
    if not mc.ensure_ffmpeg():
        ui.pause(); return
    src = ui.ask_open_file("Choose an audio file to analyze", AUDIO_FILTER)
    if not src:
        return
    ui.info("Analyzing (read-only)...")
    cmd = [mc.ffmpeg_bin(), "-nostdin", "-hide_banner", "-i", str(src),
           "-af", "astats=metadata=1:reset=0,ebur128,volumedetect", "-f", "null", "-"]
    txt = subprocess.run(cmd, capture_output=True, text=True, timeout=3600).stderr or ""

    def find(pat, default="?"):
        m = re.search(pat, txt)
        return m.group(1) if m else default

    info = mc.probe(src) or {}
    astream = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), {})

    r = core.Report("Audio Level Analysis")
    r.section(Path(src).name)
    r.line(f"  codec       {astream.get('codec_name', '?')}")
    r.line(f"  sample rate {astream.get('sample_rate', '?')} Hz")
    r.line(f"  channels    {astream.get('channels', '?')}")
    r.line(f"  duration    {mc._duration(info)} s")

    r.section("Levels")
    max_vol = find(r"max_volume:\s*(-?[\d.]+) dB")
    mean_vol = find(r"mean_volume:\s*(-?[\d.]+) dB")
    r.line(f"  peak (max)  {max_vol} dBFS")
    r.line(f"  mean (RMS)  {mean_vol} dB")
    lufs = find(r"\bI:\s*(-?[\d.]+) LUFS")
    lra = find(r"LRA:\s*(-?[\d.]+) LU")
    tpeak = None
    tp_matches = re.findall(r"Peak:\s*(-?[\d.]+) dBFS", txt)
    if tp_matches:
        tpeak = tp_matches[-1]
    r.line(f"  loudness    {lufs} LUFS (integrated)")
    r.line(f"  range       {lra} LU")
    if tpeak:
        r.line(f"  true peak   {tpeak} dBFS")

    r.section("Health checks")
    clipped = find(r"clipped samples:\s*(\d+)", "0")
    try:
        clip_n = int(clipped)
    except ValueError:
        clip_n = 0
    if clip_n > 0:
        r.finding("WARN", f"{clip_n} clipped samples — recorded too hot", "MEDIUM",
                  "Clipping detected in the recording")
    elif max_vol != "?" and float(max_vol) >= -0.1:
        r.finding("WARN", "peak at/near 0 dBFS — likely clipping")
    else:
        r.finding("PASS", "no clipping detected")

    if lufs != "?" and float(lufs) < -30:
        r.finding("WARN", f"very quiet ({lufs} LUFS) — consider normalizing")
    elif max_vol != "?" and float(max_vol) < -12:
        r.finding("WARN", f"low peak ({max_vol} dBFS) — headroom to amplify")
    else:
        r.finding("PASS", "levels in a healthy range")

    ui.deliver_report(r, "Audio_Analysis")


# --------------------------------------------------------------------------- #
#  Registration
# --------------------------------------------------------------------------- #

def register() -> core.Category:
    cat = core.Category("audio", "Audio Studio (capture & restore)")
    cat.add("restore", "Clean up / restore (denoise, de-hum, declick)", restore_audio)
    cat.add("split", "Split recording into tracks (by silence)", split_by_silence)
    cat.add("trimsil", "Trim silence (dead air)", trim_silence)
    cat.add("fade", "Fade in / out", fade_audio)
    cat.add("gain", "Gain / amplify / peak-normalize", gain_audio)
    cat.add("analyze", "Analyze levels (peak/RMS/loudness/clipping)", analyze_audio)
    return cat
