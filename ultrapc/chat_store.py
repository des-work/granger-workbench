"""Persistent chat sessions for the offline AI. Every Q/A turn is appended to
one JSONL log next to the vault so your local knowledge base grows over time —
you can browse, resume, and search across every conversation you've ever had.

Storage: C:\\Ultra-PC-Knowledge\\_chat_sessions.jsonl (one JSON per line).

    from ultrapc import chat_store
    sid = chat_store.new_session()
    chat_store.save_turn(sid, question, answer, sources, images)
    chat_store.list_sessions(limit=20)   # [(sid, first_q, ts, turns), ...]
    chat_store.load_session(sid)         # [{q, a, sources, images, ts}, ...]
    chat_store.search("photosynthesis")  # [(sid, q, snippet, ts), ...]
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import core, knowledge


def _store() -> Path:
    return knowledge.knowledge_dir() / "_chat_sessions.jsonl"


def new_session() -> str:
    return "sess_" + time.strftime("%Y%m%d_%H%M%S")


def save_turn(session_id: str, question: str, answer: str,
              sources: list, images: list) -> None:
    """Append a Q/A turn to the persistent log. Images are stored WITHOUT the
    binary data — just the article link + alt, so this stays small."""
    rec = {"session": session_id,
           "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "q": question, "a": answer,
           "sources": [{"title": s.get("title", ""), "url": s.get("url", ""),
                        "path": s.get("path", "")} for s in sources or []],
           "images": [{"alt": (i.get("alt", "") if isinstance(i, dict) else ""),
                       "article_path": (i.get("article_path", "")
                                        if isinstance(i, dict) else "")}
                      for i in images or []]}
    try:
        with _store().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        core.log("chat_store", f"save failed: {exc}", "WARN")


def _all() -> list[dict]:
    p = _store()
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def list_sessions(limit: int = 20) -> list[dict]:
    """Return recent sessions summarised: {sid, first_q, ts, turns}."""
    by_sid: dict[str, dict] = {}
    for rec in _all():
        sid = rec.get("session", "")
        if not sid:
            continue
        d = by_sid.setdefault(sid, {"sid": sid, "first_q": rec.get("q", ""),
                                    "first_ts": rec.get("ts", ""),
                                    "last_ts": rec.get("ts", ""), "turns": 0})
        d["turns"] += 1
        if rec.get("ts", "") > d["last_ts"]:
            d["last_ts"] = rec.get("ts", "")
    ordered = sorted(by_sid.values(), key=lambda x: x["last_ts"], reverse=True)
    return ordered[:limit]


def load_session(session_id: str) -> list[dict]:
    """Return all turns for one session, oldest first."""
    return [r for r in _all() if r.get("session") == session_id]


def search(query: str, limit: int = 20) -> list[dict]:
    """Keyword search across every stored Q and A. Returns matches with a small
    snippet around the hit."""
    q = query.strip().lower()
    if not q:
        return []
    hits = []
    for r in _all():
        blob = ((r.get("q", "") + " " + r.get("a", "")).lower())
        if q in blob:
            snippet_src = r.get("a", "") or r.get("q", "")
            idx = snippet_src.lower().find(q)
            start = max(0, idx - 60)
            snippet = snippet_src[start:start + 200].replace("\n", " ")
            hits.append({"sid": r.get("session", ""), "ts": r.get("ts", ""),
                         "q": r.get("q", ""), "snippet": snippet})
    return hits[-limit:][::-1]


# --------------------------------------------------------------------------- #
#  Headless CLI
# --------------------------------------------------------------------------- #

def cmd_list(limit: int = 20) -> int:
    sess = list_sessions(limit)
    if not sess:
        print("No saved chat sessions yet."); return 0
    print(f"Recent chat sessions ({len(sess)}):\n")
    for s in sess:
        print(f"  {s['sid']}  ({s['turns']} turns · last {s['last_ts']})")
        print(f"      \x1b[2m{(s['first_q'] or '')[:100]}\x1b[0m")
    print(f"\n  Show one:  python ultra.py chats show <sid>")
    print(f"  Search:    python ultra.py chats search \"<query>\"")
    return 0


def cmd_show(session_id: str) -> int:
    turns = load_session(session_id)
    if not turns:
        print(f"No such session: {session_id}"); return 1
    print(f"Session {session_id}  ({len(turns)} turns)\n")
    for t in turns:
        print(f"── {t.get('ts','')} " + "─" * 30)
        print(f"You: {t.get('q','')}\n")
        print(f"AI:  {t.get('a','').strip()}\n")
        if t.get("sources"):
            print("  sources: " + ", ".join(s["title"] for s in t["sources"][:4]))
        print()
    return 0


def cmd_search(query: str) -> int:
    hits = search(query)
    if not hits:
        print(f"No matches for {query!r}."); return 1
    print(f"Matches for {query!r} ({len(hits)}):\n")
    for h in hits:
        print(f"  {h['sid']}  ({h['ts']})")
        print(f"      Q: {h['q'][:80]}")
        print(f"      …{h['snippet']}…\n")
    return 0


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() != "chats":
        return None
    rest = argv[1:]
    if not rest:
        return cmd_list()
    sub = rest[0].lower()
    if sub in ("list", "ls"):
        return cmd_list()
    if sub == "show":
        if len(rest) < 2:
            print("usage: chats show <session_id>"); return 2
        return cmd_show(rest[1])
    if sub == "search":
        if len(rest) < 2:
            print("usage: chats search \"<query>\""); return 2
        return cmd_search(" ".join(rest[1:]))
    # bare "chats <query>" = search
    return cmd_search(" ".join(rest))
