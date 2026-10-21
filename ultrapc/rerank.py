"""GPU cross-encoder reranker — the highest-precision stage in retrieval.

Hybrid search (BM25 + embeddings) is good at *recall* — pulling the right
candidates into a shortlist. A cross-encoder is good at *precision* — it reads
the query and a passage together and scores how well the passage actually
answers the query, which bi-encoder cosine can't. Running it over the top ~30
candidates and reordering is the single biggest quality lever in modern RAG.

Runs on the GPU when a CUDA torch build is present (falls back to CPU). Fully
optional: if sentence-transformers or the model weights aren't available, callers
get their candidates back unchanged, so nothing breaks offline.

Config (ultra_config.json):
  use_reranker    bool   default True
  reranker_model  str    default 'cross-encoder/ms-marco-MiniLM-L-6-v2'
                         (small/fast/English; set 'BAAI/bge-reranker-v2-m3' for
                          the heavier multilingual model)
"""

from __future__ import annotations

import contextlib
import io
import os

from . import core

_DEFAULT = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_MODEL = None
_TRIED = False


def _device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def model_name() -> str:
    return core.load_config().get("reranker_model") or _DEFAULT


def _load():
    """Lazy-load the cross-encoder once. Returns None (and stays None) if the
    library or weights aren't available — callers treat that as 'no reranker'."""
    global _MODEL, _TRIED
    if _MODEL is not None or _TRIED:
        return _MODEL
    _TRIED = True
    if not core.load_config().get("use_reranker", True):
        return None
    try:
        from sentence_transformers import CrossEncoder
    except Exception as exc:
        core.log("rerank", f"sentence-transformers missing ({exc})", "WARN")
        return None
    name, dev = model_name(), _device()
    # keep model-load chatter (progress bars, weight-load reports) out of the CLI
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
    try:
        import logging
        for lg in ("huggingface_hub", "transformers", "sentence_transformers"):
            logging.getLogger(lg).setLevel(logging.ERROR)
        import transformers
        transformers.logging.set_verbosity_error()
    except Exception:
        pass
    # Retain the HTTP libraries' certificate verification defaults.
    # Corporate CAs can be configured through the libraries' normal CA settings.
    try:
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            _MODEL = CrossEncoder(name, device=dev, max_length=512)
        core.log("rerank", f"loaded {name} on {dev}", "INFO")
    except Exception as exc:
        core.log("rerank", f"unavailable ({exc}); passing candidates through",
                 "WARN")
        _MODEL = None
    return _MODEL


def available() -> bool:
    return _load() is not None


def status() -> dict:
    cfg = core.load_config()
    return {"enabled": cfg.get("use_reranker", True),
            "model": model_name(), "device": _device(),
            "loaded": available()}


def rerank(query: str, items: list[dict], text_key: str = "text",
           top_k: int | None = None) -> list[dict]:
    """Reorder `items` (dicts) by cross-encoder relevance to `query`. Adds a
    'rerank_score' to each returned item. If the reranker is unavailable, returns
    the items unchanged (optionally truncated to top_k) — a safe no-op."""
    if not items:
        return items
    m = _load()
    if m is None:
        return items[:top_k] if top_k else items
    pairs = [[query, (it.get(text_key) or "")[:2000]] for it in items]
    try:
        scores = m.predict(pairs, convert_to_numpy=True, show_progress_bar=False)
    except Exception as exc:
        core.log("rerank", f"predict failed: {exc}", "WARN")
        return items[:top_k] if top_k else items
    order = sorted(range(len(items)), key=lambda i: -float(scores[i]))
    out = []
    for i in order:
        it = dict(items[i])
        it["rerank_score"] = round(float(scores[i]), 4)
        out.append(it)
    return out[:top_k] if top_k else out
