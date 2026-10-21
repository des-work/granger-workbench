"""Local AI — RAG chat over the offline Knowledge Vault, using Ollama.

Ask a question; Ultra-PC retrieves the most relevant Wikipedia articles (and
their images) from the local vault, hands them to your LOCAL model as trusted
context, and shows the answer + pictures in a roomy popup window. Fully offline.
"""

from __future__ import annotations

import io
import json
import re
import threading
import urllib.parse
import urllib.request
from queue import Queue, Empty

from . import core, knowledge

OLLAMA = "http://127.0.0.1:11434"
PREFERRED = ["qwen2.5:14b", "qwen2.5", "mistral", "llama3.2"]


# --------------------------------------------------------------------------- #
#  Ollama plumbing
# --------------------------------------------------------------------------- #

def available() -> bool:
    return not _get("/api/tags").startswith("__ERR__")


def _get(path: str, timeout: int = 5) -> str:
    try:
        with urllib.request.urlopen(OLLAMA + path, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as exc:
        return f"__ERR__{exc}"


def list_models() -> list[str]:
    raw = _get("/api/tags")
    if raw.startswith("__ERR__"):
        return []
    try:
        models = [m["name"] for m in json.loads(raw).get("models", [])]
    except Exception:
        return []
    # hide pure-embedding models from the chat picker
    return [m for m in models if "embed" not in m.lower()]


def all_models() -> list[str]:
    raw = _get("/api/tags")
    if raw.startswith("__ERR__"):
        return []
    try:
        return [m["name"] for m in json.loads(raw).get("models", [])]
    except Exception:
        return []


# Stronger embedders than the 137M nomic default — the 4080 runs any of these
# without breaking a sweat; bigger = better recall at the cost of a reindex.
_EMBED_SUGGESTIONS = [
    ("mxbai-embed-large", "335M · 1024-dim · strong general retrieval"),
    ("bge-large", "335M · BAAI · excellent on question-style queries"),
    ("snowflake-arctic-embed2", "568M · top MTEB, multilingual"),
    ("nomic-embed-text", "137M · the current fast default"),
]


def cmd_embed_model(arg: str = "") -> int:
    """Show or switch the embedding model. Switching pulls it if missing and
    reindexes the Fix-It corpus; other indexes (coderag, vindex) rebuild lazily
    or on demand. The whole app is model-agnostic, so this is safe."""
    from . import cliart, core
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    MUTED, PAPER = "#8fb8cf", "#eaf6ff"
    cur = embed_model() or "(none installed)"
    installed = [m for m in all_models() if "embed" in m.lower()]

    if not arg:
        print()
        print(cliart.color("  ▸ embedding model: ", green)
              + cliart.color(cur, "#ffffff"))
        print(cliart.color("    installed: " + (", ".join(installed) or "none"),
                           MUTED))
        print(cliart.gradient("  " + "─" * 60, blue, green))
        print(cliart.color("  stronger options (GPU handles all easily):", MUTED))
        for name, desc in _EMBED_SUGGESTIONS:
            mark = cliart.color(" ✓", green) if any(name in m for m in installed) else ""
            print("   " + cliart.color(f"{name:<26}", green)
                  + cliart.color(desc, PAPER) + mark)
        print(cliart.color('\n  switch:  ultra embed-model <name>'
                           '   (pulls if missing, then reindexes)', MUTED))
        return 0

    import subprocess
    name = arg.strip()
    if name not in all_models():
        print(cliart.color(f"  pulling {name} (one-time download)...", MUTED))
        if subprocess.call(["ollama", "pull", name]) != 0:
            print(cliart.color(f"  ✕ could not pull {name}", "#ff5f57")); return 1
    cfg = core.load_config()
    cfg["embed_model"] = name
    core.save_config(cfg)
    print(cliart.color(f"  ✓ embedding model set to {name}", green))
    try:
        from . import fixit
        with cliart.Spinner("  reindexing the Fix-It corpus", c=blue):
            fixit.build_index()
        print(cliart.color("  ✓ Fix-It corpus reindexed", green))
    except Exception as exc:
        print(cliart.color(f"  ! reindex Fix-It later (`ultra fix index`): {exc}",
                           "#febc2e"))
    print(cliart.color("    also rebuild if you use them:  ultra code-index <dir>"
                       "  ·  ultra vindex build <folder>", MUTED))
    return 0


def default_model() -> str:
    """Chosen chat model. Honors a pinned `chat_model` in config, else prefers
    a known-good one, else falls back to whatever is installed — so the app
    stays functional across model swaps."""
    models = list_models()
    pin = core.load_config().get("chat_model", "")
    if pin:
        for m in models:                       # exact or family match
            if m == pin or m.startswith(pin):
                return m
    for pref in PREFERRED:
        for m in models:
            if m.startswith(pref):
                return m
    return models[0] if models else "qwen2.5:14b"


def num_ctx() -> int:
    """Context window from config, clamped to a safe range so a tiny model
    doesn't get an oversized window (functional, if lower quality)."""
    try:
        n = int(core.load_config().get("num_ctx", 8192))
    except (TypeError, ValueError):
        n = 8192
    return max(2048, min(n, 32768))


def chat_stream(model: str, messages: list[dict], ctx_override: int | None = None):
    """Yield answer tokens from Ollama /api/chat (streaming). Context window
    defaults to the configured (model-aware) size."""
    if not model:
        yield "\n[no local chat model found — install one, e.g. `ollama pull llama3.2`]"
        return
    ctx = ctx_override if ctx_override is not None else num_ctx()
    body = json.dumps({
        "model": model, "messages": messages, "stream": True,
        "options": {"temperature": 0.2, "num_ctx": ctx},
    }).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                tok = obj.get("message", {}).get("content", "")
                if tok:
                    yield tok
                if obj.get("done"):
                    break
    except Exception as exc:
        yield f"\n[local AI error: {exc}]"


# --------------------------------------------------------------------------- #
#  Retrieval from the vault (text + images + sources)
# --------------------------------------------------------------------------- #

_alt_re = re.compile(r'\balt="([^"]*)"', re.I)
_RASTER = re.compile(r"\.(jpe?g|png|gif|webp)(\?|$)", re.I)
_JUNK = re.compile(r"(static/|/skin/|icon|logo|button|edit|magnify|sprite|"
                   r"avatar|gravatar|favicon|apple-touch|\.svg)", re.I)


def _images_from_html(html: str, base_url: str, limit: int = 6) -> list[tuple[str, str]]:
    """Extract real content images (not UI chrome) as (abs_local_url, caption)."""
    out, seen = [], set()
    for tag in re.finditer(r"<img\b[^>]*>", html, re.I):
        m = re.search(r'\bsrc="([^"]+)"', tag.group(0), re.I)
        if not m:
            continue
        src = m.group(1)
        if src.startswith("data:") or src.startswith("http"):
            continue                      # local ZIM images only
        if _JUNK.search(src):
            continue                      # drop icons / logos / svg chrome
        if not (_RASTER.search(src) or "/I/" in src):
            continue                      # keep only real raster content images
        url = urllib.parse.urljoin(base_url, src)
        if url in seen:
            continue
        seen.add(url)
        alt_m = _alt_re.search(tag.group(0))
        out.append((url, alt_m.group(1) if alt_m else ""))
        if len(out) >= limit:
            break
    return out


def _fetch_raw(book: str, path: str) -> str:
    raw = knowledge._http(f"/content/{book}/{urllib.parse.quote(path)}", timeout=25)
    if raw.startswith("__ERR__"):
        raw = knowledge._http(f"/content/{book}/{path}", timeout=25)
    return raw


# --------------------------------------------------------------------------- #
#  Semantic retrieval (nomic-embed-text via Ollama) — hybrid re-rank
# --------------------------------------------------------------------------- #

_STOP = set("a an the of to in on for and or is are was were be been being how "
            "what why when where who which that this these those with from into "
            "does do did can could should would will vs versus about it its as at "
            "by".split())


def embed_model() -> str | None:
    """The embedding model to use. Honors a pinned `embed_model` in config,
    else the first installed model whose name contains 'embed'."""
    raw = _get("/api/tags")
    if raw.startswith("__ERR__"):
        return None
    try:
        names = [m["name"] for m in json.loads(raw).get("models", [])]
    except Exception:
        return None
    pin = core.load_config().get("embed_model", "")
    if pin:
        for n in names:
            if n == pin or n.startswith(pin):
                return n
    for n in names:
        if "embed" in n.lower():
            return n
    return None


def _prefixed(model: str | None, kind: str, text: str) -> str:
    """nomic-embed-text is trained with 'search_query:'/'search_document:'
    task prefixes and retrieves markedly better with them. Apply only for nomic
    so other embedding models are unaffected (they just see the raw text)."""
    if model and "nomic" in model.lower():
        return f"{kind}: {text}"
    return text


def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Batch-embed texts with the local embedding model. Returns [] on failure."""
    model = model or embed_model()
    if not model or not texts:
        return []
    vecs: list[list[float]] = []
    for i in range(0, len(texts), 64):        # batch to keep requests modest
        batch = texts[i:i + 64]
        body = json.dumps({"model": model, "input": batch}).encode()
        req = urllib.request.Request(OLLAMA + "/api/embed", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                got = json.loads(r.read().decode()).get("embeddings", [])
            if len(got) != len(batch):
                return []
            vecs.extend(got)
        except Exception as exc:
            core.log("ai", f"embed error: {exc}", "WARN")
            return []
    return vecs


def _cosine(a: list[float], b: list[float]) -> float:
    import math
    if len(a) != len(b):        # different embed model / dimension — not comparable
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _chunk(text: str, size: int = 900, max_chunks: int = 8) -> list[str]:
    """Split an article into overlapping passages. Larger + more chunks than
    before so relevant material deeper in long articles is actually reachable."""
    text = text.strip()
    if not text:
        return []
    chunks, i = [], 0
    while i < len(text) and len(chunks) < max_chunks:
        chunks.append(text[i:i + size])
        i += size - 150                        # overlap
    return chunks


def _entity(question: str) -> tuple[str, list[str]]:
    """Strip question/stop words -> (entity phrase, salient words). E.g.
    'what is the moon' -> ('moon', ['moon'])."""
    words = [w for w in re.findall(r"[a-zA-Z0-9']+", question.lower())
             if w not in _STOP and len(w) > 1]
    return " ".join(words), words


_FOLLOWUP_RE = re.compile(
    r"^\s*(who|what|where|when|why|how|any|are|is|and|also|tell|can|could|show|"
    r"list|more|else|which|another|other|others|next|before|after|then)\b.{0,40}?"
    r"\b(else|more|next|other|others|another|about\s+(?:that|this|them|it|"
    r"him|her)|happen(?:ed|s)?|then|about|examples?)\b", re.I)

_PRONOUNS = {"that", "this", "these", "those", "them", "they", "it",
             "he", "she", "him", "her", "there", "its", "their"}


def is_followup(question: str, history: list[dict]) -> bool:
    """Heuristic: is this a follow-up that needs the previous topic to make
    sense? True for short questions with follow-up markers or bare pronouns."""
    if not history:
        return False
    q = question.strip().lower()
    if len(q) < 6:
        return True
    if _FOLLOWUP_RE.search(q):
        return True
    words = set(re.findall(r"[a-z']+", q))
    _, salient = _entity(question)
    # short + has pronoun + no clear noun of its own
    if len(q) < 60 and words & _PRONOUNS and len(salient) <= 2:
        return True
    return False


def last_topic(history: list[dict]) -> str:
    """Pull the most recent user question's entity — the topic we're on."""
    for m in reversed(history):
        if m.get("role") == "user":
            ent, _ = _entity(m.get("content", ""))
            if ent:
                return ent
    return ""


def enrich_query(question: str, history: list[dict] | None) -> str:
    """If `question` looks like a follow-up, prepend the previous topic so
    retrieval doesn't lose the thread. Otherwise return the question as-is."""
    history = history or []
    if is_followup(question, history):
        topic = last_topic(history)
        if topic:
            return f"{topic} {question}"
    return question


def _candidate_hits(question: str, n: int) -> list[dict]:
    """Candidates for re-ranking, in priority order: the CANONICAL article whose
    title matches the query entity (title index) → title suggestions → full-text
    search. This is what surfaces 'Moon' for 'what is the moon'."""
    merged, seen = [], set()

    def add(h):
        key = (h["book"], h["path"])
        if key not in seen:
            seen.add(key)
            merged.append(h)

    phrase, words = _entity(question)
    longest = max(words, key=len) if words else ""

    # 1) canonical title resolution (highest priority)
    for term in (phrase, longest):
        if term:
            hit = knowledge.resolve_title(term)
            if hit:
                add(hit)
    # 2) title suggestions for the entity
    for term in (phrase, longest):
        if term:
            for h in knowledge.suggest(term, n=6):
                add(h)
    # 3) full-text search (raw question + keyword variant)
    for qy in (question, phrase):
        if qy:
            for h in knowledge.search(qy, n):
                add(h)
    return merged


def _title_bonus(title: str, phrase: str, words: list[str]) -> float:
    """Boost articles whose TITLE is the query entity; penalise disambiguated
    off-topic titles (songs/albums/films)."""
    clean = re.sub(r"\s*\(.*?\)", "", title).strip().lower()
    t = title.lower()
    bonus = 0.0
    if clean == phrase:
        bonus += 0.35
    elif phrase and phrase in clean:
        bonus += 0.12
    if words and clean in words:
        bonus += 0.30
    if knowledge._DISAMBIG.search(title):
        bonus -= 0.20
    if "(" in t and clean != phrase:
        bonus -= 0.05
    return bonus


def semantic_retrieve(question: str, k: int = 4) -> dict:
    """Hybrid retrieval: kiwix candidates -> embed & re-rank passages. Pulls more
    candidates, chunks deeper, and fills a model-sized context budget so answers
    have enough to work with."""
    if not knowledge.serve_start():
        return {"passages": [], "images": [], "sources": [], "mode": "none"}
    hits = _candidate_hits(question, 20)
    if not hits:
        return {"passages": [], "images": [], "sources": [], "mode": "semantic"}

    em = embed_model()
    raw_by_key: dict[tuple, str] = {}
    chunks: list[dict] = []
    for h in hits[:16]:                         # fetch more candidate articles
        raw = _fetch_raw(h["book"], h["path"])
        if raw.startswith("__ERR__"):
            continue
        key = (h["book"], h["path"])
        raw_by_key[key] = raw
        text = knowledge.html_to_text(raw)
        for c in _chunk(text):
            chunks.append({"book": h["book"], "path": h["path"], "title": h["title"],
                           "text": c, "key": key})
    if not chunks:
        return _keyword_retrieve(question, k)

    vecs = embed([_prefixed(em, "search_query", question)]
                 + [_prefixed(em, "search_document", c["text"]) for c in chunks], em)
    if not vecs or len(vecs) != len(chunks) + 1:
        return _keyword_retrieve(question, k)   # graceful fallback
    qv, cvs = vecs[0], vecs[1:]
    phrase, words = _entity(question)
    try:
        from . import ratings
        boosts = ratings.boost_for(phrase)
    except Exception:
        boosts = {}
    from . import vmath
    sims = vmath.cosine_all(qv, cvs)              # batched on GPU/numpy backend
    scored = [(c, v, s + _title_bonus(c["title"], phrase, words)
               + boosts.get(c["path"], 0.0))
              for (c, v), s in zip(zip(chunks, cvs), sims)]
    ranked = [(c, v) for c, v, _s in sorted(scored, key=lambda p: p[2], reverse=True)]

    # GPU cross-encoder rerank of the shortlist — the biggest precision lever,
    # so the passages the model actually sees are the ones that answer the query.
    if core.load_config().get("use_reranker", True):
        try:
            from . import rerank
            if rerank.available():
                head = ranked[:24]
                items = [{"text": c["text"], "_i": i}
                         for i, (c, _v) in enumerate(head)]
                order = rerank.rerank(question, items, top_k=len(items))
                ranked = [head[it["_i"]] for it in order] + ranked[24:]
        except Exception:
            pass                                  # reranker is best-effort


    # Fill a context budget (scaled to the chat model's window) instead of a
    # fixed tiny passage count — this is the main "more info" fix.
    budget = max(3000, num_ctx() * 3 - 1500)    # ~chars; leaves room for answer
    passages, sources, images = [], [], []
    per_article, used_articles = {}, []
    chosen_vecs: list[list[float]] = []
    used_chars = 0
    for chunk, vec in ranked:
        key = chunk["key"]
        if per_article.get(key, 0) >= 3:        # up to 3 passages per article
            continue
        if any(_cosine(vec, cv) > 0.93 for cv in chosen_vecs):
            continue                            # skip near-duplicate passages
        passages.append({"title": chunk["title"], "text": chunk["text"]})
        chosen_vecs.append(vec)
        per_article[key] = per_article.get(key, 0) + 1
        used_chars += len(chunk["text"])
        if key not in used_articles:
            used_articles.append(key)
            book, path = key
            sources.append({"title": chunk["title"], "book": book, "path": path,
                            "url": f"{knowledge.BASE}/content/{book}/{path}"})
        if used_chars >= budget or len(passages) >= 12:
            break

    # images from the contributing articles, Wikipedia-biased.
    # Each image carries its source article path + URL so the UI can rate the
    # article on image feedback and let the user click the image to the article.
    ordered = sorted(used_articles, key=lambda kk: 0 if kk[0].startswith("wikipedia") else 1)
    for book, path in ordered:
        raw = raw_by_key.get((book, path), "")
        base = f"{knowledge.BASE}/content/{book}/{path}"
        for url, alt in _images_from_html(raw, base, limit=6 - len(images)):
            images.append({"url": url, "alt": alt, "book": book,
                           "article_path": path, "article_url": base})
        if len(images) >= 6:
            break
    if len(images) < 3:
        for h in hits:
            if h["book"].startswith("wikipedia") and (h["book"], h["path"]) not in raw_by_key:
                raw = _fetch_raw(h["book"], h["path"])
                base = f"{knowledge.BASE}/content/{h['book']}/{h['path']}"
                for url, alt in _images_from_html(raw, base, limit=6 - len(images)):
                    images.append({"url": url, "alt": alt, "book": h["book"],
                                   "article_path": h["path"], "article_url": base})
                if len(images) >= 3:
                    break
    return {"passages": passages, "images": images, "sources": sources,
            "mode": "semantic"}


def retrieve(question: str, k: int = 4, per_article_chars: int = 2200,
             history: list[dict] | None = None) -> dict:
    """Dispatch to semantic retrieval when embeddings are available (and enabled),
    else keyword retrieval. If `history` is given and `question` looks like a
    follow-up ('who else?', 'what happened next?'), the retrieval query is
    enriched with the previous topic so the thread isn't lost."""
    retrieval_q = enrich_query(question, history)
    cfg = core.load_config()
    if cfg.get("use_semantic", True) and embed_model():
        try:
            r = semantic_retrieve(retrieval_q, k)
            if r["passages"] or r.get("mode") == "semantic":
                r["followup"] = retrieval_q != question
                return r
        except Exception as exc:
            core.log("ai", f"semantic failed, fallback: {exc}", "WARN")
    r = _keyword_retrieve(retrieval_q, k, per_article_chars)
    r["mode"] = "keyword"
    r["followup"] = retrieval_q != question
    return r


def _keyword_retrieve(question: str, k: int = 4, per_article_chars: int = 2600) -> dict:
    """Return {passages, images, sources} from the local vault. Text/sources come
    from the best hits across all corpora; images are biased toward Wikipedia.
    Used when no embedding model is available — still fills a context budget."""
    if not knowledge.serve_start():
        return {"passages": [], "images": [], "sources": []}
    hits = _candidate_hits(question, 12)
    budget = max(3000, num_ctx() * 3 - 1500)
    passages, images, sources = [], [], []
    used_chars = 0
    for h in hits:
        raw = _fetch_raw(h["book"], h["path"])
        if raw.startswith("__ERR__"):
            continue
        base = f"{knowledge.BASE}/content/{h['book']}/{h['path']}"
        text = knowledge.html_to_text(raw)[:per_article_chars]
        passages.append({"title": h["title"], "text": text})
        sources.append({"title": h["title"], "book": h["book"],
                        "path": h["path"], "url": base})
        for url, alt in _images_from_html(raw, base, limit=6 - len(images)):
            images.append({"url": url, "alt": alt, "book": h["book"],
                           "article_path": h["path"], "article_url": base})
        used_chars += len(text)
        if used_chars >= budget or len(passages) >= 8:
            break

    # Bias pictures toward Wikipedia: if we have few images, pull from the best
    # Wikipedia article for this question.
    if len(images) < 3:
        wiki_hits = [h for h in hits if h["book"].startswith("wikipedia")]
        for h in wiki_hits[:2]:
            raw = _fetch_raw(h["book"], h["path"])
            if raw.startswith("__ERR__"):
                continue
            base = f"{knowledge.BASE}/content/{h['book']}/{h['path']}"
            for url, alt in _images_from_html(raw, base, limit=6 - len(images)):
                images.append({"url": url, "alt": alt, "book": h["book"],
                               "article_path": h["path"], "article_url": base})
            if not any(s["path"] == h["path"] for s in sources):
                sources.append({"title": h["title"], "book": h["book"],
                                "path": h["path"], "url": base})
            if len(images) >= 4:
                break
    return {"passages": passages, "images": images, "sources": sources}


VALUES = (
    "Values: Explain history, ideology, atrocities, hate groups, and "
    "controversial figures FACTUALLY. Wikipedia exists to inform — describe "
    "them clearly, cite the article, and reflect historical consensus. Hate "
    "groups (Nazi Germany, KKK, other white-supremacist / extremist / "
    "terrorist movements) and mass violence are widely and rightly condemned; "
    "do not write sympathetic advocacy or recruitment material for them.\n\n"
    "TECHNICAL FIELDS ARE FULLY OPEN. The user is a professional cybersecurity "
    "practitioner (red teamer / offensive security). Cybersecurity topics — "
    "including hacking techniques, malware analysis, red team operations, "
    "penetration testing, exploit development, reverse engineering, OSINT, "
    "social engineering, network attacks, digital forensics, security tooling, "
    "vulnerability research, and blue-team defense — are LEGITIMATE and "
    "expected. Same for robotics, mechanical/electrical/software/chemical "
    "engineering, physics, chemistry, biology, and weapons systems as an "
    "engineering topic. Explain these fully, technically, and without hedging. "
    "Do NOT refuse, moralize, or add legal disclaimers on technical questions.\n\n"
    "Do NOT: help plan physical violence against specific real people; produce "
    "step-by-step operational instructions for terrorism or mass-casualty "
    "attacks; write propaganda intended to recruit for hate groups; glorify "
    "perpetrators of violence in ways that encourage imitation. If a request "
    "mixes information and clearly harmful operational planning against a "
    "named real person, answer the informational part and briefly decline the "
    "operational part."
)

SYSTEM_PROMPT = (
    "You are a local, offline research assistant. Answer the user's question "
    "using ONLY the provided Wikipedia context when it is relevant, and say so "
    "when the context is insufficient. Be accurate and concise, cite the article "
    "titles you used in parentheses, and never invent facts not supported by the "
    "context or your general knowledge. Prefer the local context over guessing.\n\n"
    + VALUES
)


def build_messages(question: str, passages: list[dict], history: list[dict]) -> list[dict]:
    if passages:
        ctx = "\n\n".join(f"### {p['title']}\n{p['text']}" for p in passages)
        context_block = (f"Local Wikipedia context:\n{ctx}\n\n"
                         f"Question: {question}")
    else:
        context_block = (f"(No local vault articles matched. Answer from general "
                         f"knowledge and note that no local source was found.)\n\n"
                         f"Question: {question}")
    return ([{"role": "system", "content": SYSTEM_PROMPT}]
            + history
            + [{"role": "user", "content": context_block}])


def fetch_image(url: str, max_px: int = 240):
    """Download a local ZIM image and return a thumbnailed PIL image, or None."""
    try:
        from PIL import Image
        with urllib.request.urlopen(url, timeout=20) as r:
            data = r.read()
        im = Image.open(io.BytesIO(data))
        im.load()
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        im.thumbnail((max_px, max_px))
        return im
    except Exception:
        return None
