"""Search-result ratings — a feedback loop so retrieval improves as you use it.

Rate each search 0–5:
  0 = returned nothing        1 = nothing relevant
  3 = some useful             5 = exactly what I needed (and a bit more)

Ratings are stored per query-entity + article, and fed back as a ranking boost:
articles that scored well for a topic rise next time; ones that scored badly
sink. Fully local (a JSONL log next to the vault).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import core, knowledge


def _store() -> Path:
    return knowledge.knowledge_dir() / "_ratings.jsonl"


def _entity(query: str) -> str:
    from .ai import _entity as e
    return e(query)[0]


def rate(query: str, paths, stars: int, mode: str = "search") -> None:
    """Record a rating for a query and the articles it surfaced."""
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "query": query,
           "entity": _entity(query), "paths": list(paths)[:8],
           "stars": max(0, min(5, int(stars))), "mode": mode}
    try:
        with _store().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        core.log("ratings", f"{stars}★ for '{query}'", "INFO")
    except Exception as exc:
        core.log("ratings", f"save failed: {exc}", "WARN")


def _all() -> list[dict]:
    p = _store()
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def boost_for(entity: str) -> dict[str, float]:
    """Per-article ranking boost learned from past ratings of this entity.
    avg 5★ -> +0.3, 3★ -> 0, 1★ -> -0.3 (scaled by how many ratings)."""
    if not entity:
        return {}
    agg: dict[str, list[float]] = {}
    for r in _all():
        if r.get("entity") != entity:
            continue
        for p in r.get("paths", []):
            agg.setdefault(p, [0.0, 0])
            agg[p][0] += r["stars"]
            agg[p][1] += 1
    boosts = {}
    for p, (s, c) in agg.items():
        avg = s / c
        boosts[p] = (avg - 3) / 2 * min(1.0, c / 2) * 0.3
    return boosts


def weak_query(entity: str) -> bool:
    """True if this topic has consistently rated poorly (<=1★) — a signal to
    fall back to AI article suggestions instead of plain search."""
    rs = [r["stars"] for r in _all() if r.get("entity") == entity]
    return bool(rs) and sum(rs) / len(rs) <= 1.0


def stats() -> dict:
    rs = _all()
    if not rs:
        return {"count": 0}
    stars = [r["stars"] for r in rs]
    dist = {i: stars.count(i) for i in range(6)}
    return {"count": len(rs), "avg": sum(stars) / len(stars), "dist": dist,
            "topics": len({r["entity"] for r in rs})}
