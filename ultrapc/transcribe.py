"""Transcribe — turn lecture audio/video into text LOCALLY (faster-whisper), so
the assistant reads a cheap transcript instead of the media. Fully offline once
the model is cached; uses the GPU if available, else CPU.

    python ultra.py transcribe <audio|video> [--model base] [--out f.txt]

First run downloads the chosen Whisper model (cached under ~/.cache); after that
it's offline. Models: tiny · base · small · medium · large-v3 (bigger = better,
slower). Audio/video decoding uses the bundled ffmpeg / PyAV.
"""

from __future__ import annotations

from pathlib import Path

from . import core, ui

_MODELS: dict = {}
MEDIA_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma",
              ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4b", ".opus"}


def available() -> bool:
    import importlib.util
    return importlib.util.find_spec("faster_whisper") is not None


def _get_model(size: str):
    if size in _MODELS:
        return _MODELS[size]
    from faster_whisper import WhisperModel
    last = None
    for dev, ct in (("cuda", "float16"), ("cpu", "int8")):
        try:
            m = WhisperModel(size, device=dev, compute_type=ct)
            _MODELS[size] = m
            core.log("transcribe", f"whisper {size} on {dev}", "INFO")
            return m
        except Exception as exc:
            last = exc
    raise RuntimeError(f"could not load whisper model '{size}': {last}")


def _ts(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60:02d}:{s % 60:02d}"


def transcribe_file(path: str, model_size: str = "base", language=None,
                    timestamps: bool = True):
    """Return (text, info_str). Downloads the model on first use."""
    model = _get_model(model_size)
    segments, info = model.transcribe(path, language=language, vad_filter=True)
    lines = []
    for seg in segments:
        txt = seg.text.strip()
        if not txt:
            continue
        lines.append(f"[{_ts(seg.start)}] {txt}" if timestamps else txt)
    header = (f"# transcript: {Path(path).name}\n"
              f"# language={info.language} ({info.language_probability:.0%}), "
              f"duration={_ts(info.duration)}, model={model_size}\n")
    return header + "\n".join(lines) + "\n", info


def cmd_transcribe(path: str, model_size="base", out=None, language=None) -> int:
    p = Path(path).expanduser()
    if not p.exists():
        print(f"Not found: {p}"); return 1
    if not available():
        print("faster-whisper not installed "
              "(pip install faster-whisper)."); return 1
    print(f"Transcribing {p.name} with Whisper '{model_size}' "
          f"(first run downloads the model)…")
    try:
        text, info = transcribe_file(str(p), model_size=model_size, language=language)
    except Exception as exc:
        print(f"Transcription failed: {exc}"); return 1
    if out is None:
        out = str(p.with_suffix(".txt"))
    Path(out).write_text(text, encoding="utf-8")
    print(f"Wrote transcript (~{len(text)//4:,} tokens) -> {out}")
    return 0


def _tool_transcribe(ctx=None) -> None:
    ui.title_bar("Transcribe — audio/video to text (offline)")
    if not available():
        ui.err("faster-whisper isn't installed.")
        ui.dim("Install:  pip install faster-whisper"); ui.pause(); return
    f = ui.ask_open_file("Choose audio/video",
                         [("Media", "*.mp3 *.wav *.m4a *.mp4 *.mkv *.mov *.webm *.flac"),
                          ("All files", "*.*")])
    if not f:
        ui.pause(); return
    sizes = ["tiny", "base", "small", "medium", "large-v3"]
    items = [(str(i + 1), s) for i, s in enumerate(sizes)]
    ch = ui.menu("Model size", "bigger = better + slower", items, "base")
    size = sizes[int(ch) - 1] if ch.isdigit() and 1 <= int(ch) <= len(sizes) else "base"
    print()
    cmd_transcribe(f, model_size=size)
    ui.pause()


def register_tool(cat) -> None:
    cat.add("transcribe", "Transcribe audio/video to text (offline)", _tool_transcribe)


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() != "transcribe":
        return None
    rest = argv[1:]
    out, size, lang, pos = None, "base", None, []
    i = 0
    while i < len(rest):
        if rest[i] == "--out" and i + 1 < len(rest):
            out = rest[i + 1]; i += 2
        elif rest[i] == "--model" and i + 1 < len(rest):
            size = rest[i + 1]; i += 2
        elif rest[i] == "--lang" and i + 1 < len(rest):
            lang = rest[i + 1]; i += 2
        else:
            pos.append(rest[i]); i += 1
    if not pos:
        print("usage: transcribe <audio|video> [--model base] [--lang en] [--out f]")
        return 2
    return cmd_transcribe(pos[0], model_size=size, out=out, language=lang)
