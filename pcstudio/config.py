"""Source-checkout defaults; overrides never require editing Python files."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
ULTRA_ROOT = Path(os.environ.get('PCSTUDIO_ULTRA_ROOT', ROOT)).expanduser()
HERMES_ROOT = Path(os.environ.get('PCSTUDIO_HERMES_ROOT', Path.home()/'.hermes/hermes-agent')).expanduser()
CHAT_MODEL = os.environ.get('PCSTUDIO_CHAT_MODEL', 'qwen3:8b')
BUILD_MODEL = os.environ.get('PCSTUDIO_BUILD_MODEL', CHAT_MODEL)
VISION_MODEL = os.environ.get('PCSTUDIO_VISION_MODEL', 'qwen2.5vl:7b')
OLLAMA_BASE = os.environ.get('PCSTUDIO_OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
