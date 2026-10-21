"""Speaker verification for `pc ask`, so it only acts on one enrolled voice.

Uses resemblyzer (a small, CPU-fast speaker-embedding model) to compare each
turn's recording against a saved voice profile by cosine similarity. Not
installed via its normal dependency chain - see the webrtcvad note below.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np

PROFILE_PATH = Path(__file__).resolve().parent.parent / "models/voiceid/profile.npy"

# Experimental threshold derived from synthetic-voice samples, not a validated
# biometric evaluation. Speaker matching is a convenience filter, not an
# authentication or authorization mechanism. Tune only using consented data.
MATCH_THRESHOLD = 0.62

# Require the real upstream voice-processing dependencies. Import failures are
# handled by the optional-feature path in the assistant; no fake VAD is injected.
from resemblyzer import VoiceEncoder, preprocess_wav  # noqa: E402

_encoder = None


def _get_encoder() -> VoiceEncoder:
    global _encoder
    if _encoder is None:
        _encoder = VoiceEncoder("cpu")
    return _encoder


def embed(wav_path: Path) -> np.ndarray:
    wav = preprocess_wav(str(wav_path))
    return _get_encoder().embed_utterance(wav)


def is_enrolled() -> bool:
    return PROFILE_PATH.is_file()


def enrolled_on() -> str:
    """When the active profile was recorded, for the startup line. A profile
    you don't remember making is the one that silently rejects you."""
    if not is_enrolled():
        return "never"
    stamp = datetime.fromtimestamp(PROFILE_PATH.stat().st_mtime)
    return stamp.strftime("%d %b %Y %H:%M")


def enroll(wav_paths: list[Path]) -> None:
    """Average embeddings from one or more clips into a single profile.
    Several takes centers out per-utterance noise better than one clip."""
    embeddings = [embed(p) for p in wav_paths]
    profile = np.mean(embeddings, axis=0)
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(PROFILE_PATH, profile)


def verify(wav_path: Path) -> tuple[bool, float]:
    """Returns (is_match, similarity). Always True if nothing is enrolled
    yet - verification is opt-in, not a lockout by default."""
    if not is_enrolled():
        return True, 1.0
    profile = np.load(PROFILE_PATH)
    candidate = embed(wav_path)
    similarity = float(np.dot(profile, candidate) /
                       (np.linalg.norm(profile) * np.linalg.norm(candidate)))
    return similarity >= MATCH_THRESHOLD, similarity
