# Setup

Granger Workbench currently supports a **Linux source checkout with Python 3.10+**. Audio integration uses PipeWire, screenshot capture uses COSMIC, and background job tracking uses Linux/POSIX facilities. Other operating systems are not validated.

## Base runtime

Follow the README's virtual-environment installation, or run `bash scripts/setup_pcstudio.sh`. The installer installs Python dependencies only. It does not modify your shell configuration, install system packages, download models, or configure a background listener.

| Feature | Additional requirement |
| --- | --- |
| Simulation templates | Python standard library |
| Graph analysis | NetworkX (`requirements-pcstudio.txt`) |
| Images and local design assets | Pillow and this checkout's `assets-vault` |
| Typed assistant (`pc ask --text`) | Hermes Agent executable on PATH; configured inference backend |
| Planning, vision, generated scenes | Ollama and a suitable installed model for each role |
| Microphone / playback | PipeWire `pw-record` and `pw-play`; working input/output devices |
| Transcription | `faster-whisper`, model weights, compatible CPU or CUDA runtime |
| Speech output | `piper-tts` and a separately installed ONNX voice plus JSON metadata |
| Optional speaker matching | `resemblyzer` and its model dependencies; experimental |
| Screen observation | COSMIC's `cosmic-screenshot`; optional Tesseract OCR; vision model |
| 3D preview / animation | Blender on PATH or the documented portable path; FFmpeg for video |
| Terminal animation jobs | Separate compatible Termstage checkout |
| Kiwix research | `kiwix-serve`, local ZIM archives, and a `library.xml` registering them |
| Textbook research | Separate compatible `classroom.index` adapter and curated SQLite index |
| Ultra-PC semantic retrieval | Optional embeddings / reranker packages; see `requirements-gpu.txt` |

The textbook adapter and Termstage project are **not distributed here**. Their commands report unavailable or fail explicitly if the external dependency is missing. You can use the rest of the workbench without them.

## Configuration

Export only the overrides you need in your own shell. The repository never reads a `.env` file automatically. Do not commit personal environment files.

| Variable | Default / purpose |
| --- | --- |
| `PCSTUDIO_CHAT_MODEL` | `qwen3:8b`; example default, must be installed in the configured Hermes backend |
| `PCSTUDIO_BUILD_MODEL` | Chat model; Ollama model used for build planning and classification |
| `PCSTUDIO_VISION_MODEL` | `qwen2.5vl:7b`; example default, must be installed and support images |
| `PCSTUDIO_OLLAMA_URL` | `http://127.0.0.1:11434`; direct planning/vision endpoint |
| `PCSTUDIO_ULTRA_ROOT` | This repository; root containing `integrations` and `assets-vault` |
| `PCSTUDIO_HERMES_ROOT` | `~/.hermes/hermes-agent`; optional capability inspection of a Hermes source installation |
| `PCSTUDIO_TERMSTAGE_ROOT` | `optional/termstage` under this checkout; external Termstage root |
| `PCSTUDIO_KNOWLEDGE_ROOT` | `optional/knowledge` under this checkout; external `classroom.index` root |
| `PCSTUDIO_JOBS` | `output/pcstudio/jobs`; build state and artifacts |
| `ULTRA_KIWIX_ROOT` | `/mnt/ultravault`; default requires a mounted vault. An explicitly configured directory need not be a mount. |
| `ULTRA_KIWIX_SERVER` | `kiwix-serve`; executable name or absolute path |

The Kiwix bridge binds only to `127.0.0.1:4386`. Direct Ollama calls and Hermes use distinct configuration: changing `PCSTUDIO_OLLAMA_URL` does not reconfigure Hermes. `--model` can override the model for supported commands. Model names here are convenient defaults, not performance claims. Their upstream catalogs are [Qwen3](https://ollama.com/library/qwen3) and [Qwen2.5-VL](https://ollama.com/library/qwen2.5vl).

## Optional speech

```bash
source .venv/bin/activate
python -m pip install -r requirements-voice.txt
mkdir -p models/tts
python -m piper.download_voices --data-dir models/tts en_US-lessac-medium
pc ask --list-voices
```

This explicitly downloads a voice. First transcription use may download Whisper weights. Check each model/voice license before use. PC Ask's interactive voice path currently requests CUDA by default; use the lower-level CPU transcription command when CUDA is unavailable:

```bash
pcstudio voice recording.wav --cpu
```

The CPU transcription path does not establish that all interactive voice features work on CPU-only systems. GPU libraries must match your hardware and installed runtime; the installer does not borrow libraries from another application's installation. For corporate certificate authorities, configure trusted CA bundles through the relevant library or operating system. Do not disable certificate verification.

After configuring your audio and Hermes backend:

```bash
pc ask
pc granger
```

Granger records listening windows while active. Review [data handling](DATA-AND-PERMISSIONS.md) before enabling standby or speaker enrollment.

## MCP servers

Each bridge uses newline-delimited JSON-RPC over **stdio**, rather than an exposed network server. Launch from the checkout with its virtual-environment Python. Example client configuration (replace `/absolute/path/granger-workbench`):

```json
{
  "mcpServers": {
    "pc-workbench": {
      "command": "/absolute/path/granger-workbench/.venv/bin/python",
      "args": ["-m", "pcstudio.mcp"],
      "cwd": "/absolute/path/granger-workbench"
    },
    "ultra-design": {
      "command": "/absolute/path/granger-workbench/.venv/bin/python",
      "args": ["/absolute/path/granger-workbench/integrations/design_assets.py"]
    },
    "device-health": {
      "command": "/absolute/path/granger-workbench/.venv/bin/python",
      "args": ["/absolute/path/granger-workbench/integrations/device_health.py"]
    },
    "local-kiwix-kb": {
      "command": "/absolute/path/granger-workbench/.venv/bin/python",
      "args": ["/absolute/path/granger-workbench/integrations/hermes_kb.py"],
      "env": {"ULTRA_KIWIX_ROOT": "/absolute/path/your-zim-library"}
    }
  }
}
```

Client configuration formats differ. Enable only the tools you intend the assistant to use. There is no authentication or operating-system sandbox inside these stdio processes; they run with your account's permissions.
