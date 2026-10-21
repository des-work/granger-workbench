"""[6] Knowledge Vault — offline Wikipedia & reference corpus via Kiwix.

Downloads .zim archives (whole sites, compressed + full-text indexed), serves
them locally with kiwix-serve, and exposes search/read so both the user AND
the assistant can consult local knowledge before ever going online.

The headless entry points `kb_search()` and `kb_read()` are what the assistant
calls from the terminal (`python ultra.py kb "..."`).
"""

from __future__ import annotations

import html.parser
import json
import re
import socket
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from . import core, ui

# --------------------------------------------------------------------------- #
#  Paths & constants
# --------------------------------------------------------------------------- #

TOOLS_DIR = core.ROOT / "tools" / "kiwix"
DEFAULT_KNOWLEDGE_DIR = Path("C:/Ultra-PC-Knowledge") if core.IS_WINDOWS else core.ROOT / "Knowledge"
PORT = 4386
HOST = "127.0.0.1"
BASE = f"http://{HOST}:{PORT}"
MIRROR = "https://download.kiwix.org/zim"
CURL_FLAGS = ["-L", "--ssl-no-revoke"]


def knowledge_dir() -> Path:
    cfg = core.load_config()
    p = Path(cfg.get("knowledge_dir") or DEFAULT_KNOWLEDGE_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def library_path() -> Path:
    return knowledge_dir() / "library.xml"


def kiwix(tool: str) -> Path:
    return TOOLS_DIR / (f"{tool}.exe" if core.IS_WINDOWS else tool)


def tools_ready() -> bool:
    return all(kiwix(t).exists() for t in ("kiwix-serve", "kiwix-manage", "kiwix-search"))


# --------------------------------------------------------------------------- #
#  Catalog — curated corpora. subdir+prefix let us resolve the newest dump.
# --------------------------------------------------------------------------- #

CATALOG = {
    "wikipedia_full":   dict(title="Wikipedia (full, with images)", subdir="wikipedia",
                             prefix="wikipedia_en_all_maxi_", approx="~115 GB"),
    "wikipedia_nopic":  dict(title="Wikipedia (text, no images)", subdir="wikipedia",
                             prefix="wikipedia_en_all_nopic_", approx="~49 GB"),
    "wikipedia_top1m":  dict(title="Wikipedia (top 1M articles)", subdir="wikipedia",
                             prefix="wikipedia_en_top1m_maxi_", approx="~46 GB"),
    "wikipedia_mini":   dict(title="Wikipedia (mini / condensed)", subdir="wikipedia",
                             prefix="wikipedia_en_all_mini_", approx="~12 GB"),
    "wikipedia_simple": dict(title="Wikipedia (Simple English)", subdir="wikipedia",
                             prefix="wikipedia_en_simple_all_maxi_", approx="~3 GB"),
    "superuser":        dict(title="Super User (PC troubleshooting Q&A)", subdir="stack_exchange",
                             prefix="superuser.com_en_all_", approx="~4 GB"),
    "askubuntu":        dict(title="Ask Ubuntu (Linux Q&A)", subdir="stack_exchange",
                             prefix="askubuntu.com_en_all_", approx="~3 GB"),
    "serverfault":      dict(title="Server Fault (sysadmin Q&A)", subdir="stack_exchange",
                             prefix="serverfault.com_en_all_", approx="~2 GB"),
    "security_se":      dict(title="Security Stack Exchange", subdir="stack_exchange",
                             prefix="security.stackexchange.com_en_all_", approx="~0.4 GB"),
    "unix_se":          dict(title="Unix & Linux Stack Exchange", subdir="stack_exchange",
                             prefix="unix.stackexchange.com_en_all_", approx="~1 GB"),
    "stackoverflow":    dict(title="Stack Overflow (full, programming)", subdir="stack_exchange",
                             prefix="stackoverflow.com_en_all_", approx="~74 GB"),
    "networkeng_se":    dict(title="Network Engineering SE (routing/switching Q&A)", subdir="stack_exchange",
                             prefix="networkengineering.stackexchange.com_en_all_", approx="~0.3 GB"),
    "archwiki":         dict(title="Arch Wiki (best practical Linux reference)", subdir="other",
                             prefix="archlinux_en_all_maxi_", approx="~0.1 GB"),
}

TECH_PACK = ["superuser", "askubuntu", "serverfault", "security_se", "unix_se",
             "networkeng_se", "archwiki"]
BUNDLES = {
    "starter": ["wikipedia_mini"] + TECH_PACK,
    "recommended": ["wikipedia_nopic"] + TECH_PACK,
    "deep": ["wikipedia_full"] + TECH_PACK,
    "max": ["wikipedia_full", "stackoverflow"] + TECH_PACK,
}


# --------------------------------------------------------------------------- #
#  Resolve newest dump filename from the Kiwix directory listing
# --------------------------------------------------------------------------- #

_href_re = re.compile(r'href="([^"?][^"]*\.zim)"')


def resolve_latest(subdir: str, prefix: str) -> tuple[str, str] | None:
    """Return (filename, url) for the newest .zim matching prefix, or None."""
    listing_url = f"{MIRROR}/{subdir}/"
    out = core.run(["curl", "-s", *CURL_FLAGS, listing_url], timeout=60)
    matches = sorted({m for m in _href_re.findall(out) if m.startswith(prefix)})
    if not matches:
        return None
    newest = matches[-1]  # date-suffixed names sort chronologically
    return newest, f"{MIRROR}/{subdir}/{newest}"


# --------------------------------------------------------------------------- #
#  Local library
# --------------------------------------------------------------------------- #

def local_zims() -> list[Path]:
    return sorted(knowledge_dir().glob("*.zim"))


def book_names() -> dict[str, str]:
    """Map each local .zim filename stem -> the server book name from library.xml.
    Falls back to the stem when the library hasn't been built yet."""
    mapping = {z.stem: z.stem for z in local_zims()}
    lib = library_path()
    if lib.exists():
        try:
            import xml.etree.ElementTree as ET
            for book in ET.parse(lib).getroot().findall("book"):
                path = book.get("path", "")
                name = book.get("name", "")
                stem = Path(path).stem
                if stem and name:
                    mapping[stem] = name
        except Exception:
            pass
    return mapping


def library_books() -> list[dict]:
    """Parse library.xml -> [{name, filename, articles, media}]. These are the
    ONLY corpora that appear in search; anything on disk but not here is 'dark'."""
    import xml.etree.ElementTree as ET
    lib = library_path()
    if not lib.exists():
        return []
    out = []
    try:
        for b in ET.parse(lib).getroot():
            a = b.attrib
            fn = (a.get("path", "") or "").replace("\\", "/").split("/")[-1]
            out.append({"name": a.get("name", ""), "filename": fn,
                        "articles": int(a.get("articleCount", "0") or 0),
                        "media": int(a.get("mediaCount", "0") or 0)})
    except Exception as exc:
        core.log("knowledge", f"library parse error: {exc}", "WARN")
    return out


def rebuild_library() -> int:
    """(Re)create library.xml from every .zim present, verifying each one is
    ACTUALLY registered (a partial/locked ZIM silently fails to add — that's how
    a downloaded corpus ends up invisible). Records a per-file report so audits
    and reindex can show exactly what registered vs failed. Returns count added."""
    lib = library_path()
    if lib.exists():
        lib.unlink()
    added, failed = [], []
    for z in local_zims():
        before = len(library_books())
        r = core.run([str(kiwix("kiwix-manage")), str(lib), "add", str(z)], timeout=180)
        after = len(library_books())
        if after > before:                    # verified by the book count growing
            added.append(z.name)
        else:
            reason = (r.strip().splitlines()[-1][:100] if r.strip()
                      else "add failed (likely incomplete/locked ZIM)")
            failed.append((z.name, reason))
            core.log("knowledge", f"NOT registered: {z.name} — {reason}", "WARN")
    _last_report[:] = [added, failed]
    core.log("knowledge", f"library rebuilt: {len(added)} added, "
             f"{len(failed)} failed", "INFO")
    return len(added)


_last_report: list = [[], []]   # [added_filenames, [(filename, reason), ...]]


def last_reindex_report() -> tuple[list, list]:
    return _last_report[0], _last_report[1]


# --------------------------------------------------------------------------- #
#  Server lifecycle
# --------------------------------------------------------------------------- #

# The port opens before Kiwix finishes loading the full-text index across all
# corpora, so the very first search after a cold start can come back empty.
# `_warmed` lets search() do a single warm-up retry to hide that race.
_warmed = [False]


def server_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, PORT)) == 0


def serve_start(wait: float = 6.0) -> bool:
    if server_running():
        return True
    if not local_zims():
        return False
    if not library_path().exists():
        rebuild_library()
    creation = 0x08000000 if core.IS_WINDOWS else 0  # CREATE_NO_WINDOW
    try:
        subprocess.Popen(
            [str(kiwix("kiwix-serve")), "--library", str(library_path()),
             "--port", str(PORT), "--address", HOST],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=creation)
    except Exception as exc:
        core.log("knowledge", f"serve failed: {exc}", "ERROR")
        return False
    deadline = time.time() + wait
    while time.time() < deadline:
        if server_running():
            core.log("knowledge", f"server up on {BASE}", "INFO")
            return True
        time.sleep(0.3)
    return server_running()


def serve_stop() -> None:
    _warmed[0] = False        # a fresh server must warm up again
    if core.IS_WINDOWS:
        core.run(["taskkill", "/F", "/IM", "kiwix-serve.exe"], timeout=15)
    else:
        core.run(["pkill", "-f", "kiwix-serve"], timeout=15)


def _http(path: str, timeout: int = 20) -> str:
    try:
        with urllib.request.urlopen(BASE + path, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "replace")
    except Exception as exc:
        return f"__ERR__{exc}"


# --------------------------------------------------------------------------- #
#  HTML -> text
# --------------------------------------------------------------------------- #

class _Text(html.parser.HTMLParser):
    _SKIP = {"script", "style", "head", "nav", "footer"}

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip += 1
        if tag in ("p", "br", "div", "li", "h1", "h2", "h3", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        raw = "".join(self.parts)
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", raw)).strip()


def html_to_text(raw: str) -> str:
    p = _Text()
    try:
        p.feed(raw)
    except Exception:
        pass
    return p.text()


# --------------------------------------------------------------------------- #
#  Search & read  (finalized against the live server response format)
# --------------------------------------------------------------------------- #

# kiwix-serve /search results: <a href="/content/<book>/<path>"><cite>snippet</cite>
_result_re = re.compile(
    r'href="/content/([^"/]+)/([^"]+)">\s*(?:<cite>(.*?)</cite>)?', re.S)
_tag_re = re.compile(r"<[^>]+>")


def _search_once(query: str, limit: int, start: int = 0) -> list[dict]:
    q = urllib.parse.urlencode({"pattern": query, "pageLength": limit,
                                "start": start})
    html_out = _http(f"/search?{q}", timeout=40)
    if html_out.startswith("__ERR__"):
        return []
    results: list[dict] = []
    seen = set()
    for book, path, snippet in _result_re.findall(html_out):
        if (book, path) in seen:
            continue
        seen.add((book, path))
        title = urllib.parse.unquote(path.rsplit("/", 1)[-1]).replace("_", " ")
        snip = _tag_re.sub("", snippet or "")
        snip = re.sub(r"\s+", " ", snip).strip()
        results.append({"book": book, "path": path, "title": title, "snippet": snip})
        if len(results) >= limit:
            break
    return results


def search(query: str, limit: int = 8, start: int = 0) -> list[dict]:
    """Full-text search across the whole local library via the local server.
    Returns ranked hits: {book, path, title, snippet}. `start` offsets into the
    ranking so you can page past the first results and reach deeper matches. On
    the first search after a cold start, retries once after a short pause so an
    empty result caused by the still-loading index doesn't look like 'no matches'."""
    if not serve_start():
        return []
    hits = _search_once(query, limit, start)
    if not hits and start == 0 and not _warmed[0]:
        time.sleep(2.0)                       # let Kiwix finish loading the index
        hits = _search_once(query, limit, start)
    _warmed[0] = True                         # only pay the warm-up cost once
    return hits


def audit() -> dict:
    """Coverage report: which downloaded corpora are actually registered and
    searchable, and which are 'dark' (on disk but invisible to search)."""
    zims = local_zims()
    books = library_books()
    reg_stems = {b["filename"].rsplit(".zim", 1)[0] for b in books if b["filename"]}
    dark = []
    for z in zims:
        if z.stem not in reg_stems:
            try:
                growing = (time.time() - z.stat().st_mtime) < 180
                size = z.stat().st_size
            except OSError:
                growing, size = False, 0
            dark.append({"stem": z.stem, "bytes": size, "growing": growing})
    total_bytes = sum((z.stat().st_size for z in zims), 0)
    probe = bool(search("linux", 1)) if books else False
    return {"zims": len(zims), "total_bytes": total_bytes, "registered": books,
            "dark": dark, "articles": sum(b["articles"] for b in books),
            "search_ok": probe}


def wiki_book() -> str | None:
    """The main full Wikipedia book id, else Simple Wikipedia, else any."""
    stems = [z.stem for z in local_zims()]
    for pref in ("wikipedia_en_all_maxi", "wikipedia_en_simple", "wikipedia"):
        for s in stems:
            if s.startswith(pref):
                return s
    return None


def suggest(term: str, book: str | None = None, n: int = 8) -> list[dict]:
    """Kiwix TITLE search (its built-in title index). Far better than full-text
    for 'what is X' — returns the article actually titled X. Returns hits."""
    import json
    book = book or wiki_book()
    if not book or not serve_start():
        return []
    q = urllib.parse.urlencode({"content": book, "term": term})
    raw = _http(f"/suggest?{q}", timeout=15)
    if raw.startswith("__ERR__"):
        return []
    try:
        arr = json.loads(raw)
    except Exception:
        return []
    out = []
    for a in arr[:n]:
        if a.get("kind") != "path":
            continue
        path = a.get("path", "")
        out.append({"book": book, "path": path,
                    "title": a.get("value") or path.replace("_", " ")})
    return out


_DISAMBIG = re.compile(r"\((song|album|film|band|disambiguation|TV series|"
                       r"video game|novel|EP|opera|play)\)", re.I)


def resolve_title(term: str, book: str | None = None) -> dict | None:
    """Try to fetch the CANONICAL article whose title is `term` (Wikipedia caps
    the first letter). Returns the article hit if a substantial page exists."""
    book = book or wiki_book()
    if not book or not serve_start():
        return None
    t = term.strip()
    variants = []
    base = t.replace(" ", "_")
    if base:
        variants.append(base[0].upper() + base[1:])          # first letter cap
    variants.append("_".join(w.capitalize() for w in t.split()))  # Title Case
    seen = set()
    for cand in variants:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        raw = _http(f"/content/{book}/{urllib.parse.quote(cand)}", timeout=20)
        if raw.startswith("__ERR__") or len(raw) < 4000:
            continue
        head = raw[:2500].lower()
        if "may refer to" in head or "may also refer" in head:   # disambiguation
            continue
        return {"book": book, "path": cand, "title": cand.replace("_", " ")}
    return None


def read_article(book: str, path: str, max_chars: int = 6000) -> str:
    """Fetch an article's plain text from the local server."""
    if not serve_start():
        return "(knowledge server unavailable)"
    raw = _http(f"/content/{book}/{path}")
    if raw.startswith("__ERR__"):
        return f"(could not fetch: {raw[7:]})"
    text = html_to_text(raw)
    return text[:max_chars] + ("\n...[truncated]" if len(text) > max_chars else "")


# --------------------------------------------------------------------------- #
#  Headless entry points for the assistant / CLI
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
#  Result ranking — Kiwix's Xapian order is only the CANDIDATE pool. The
#  cross-encoder judges actual relevance (this is what sinks "HIStory (Michael
#  Jackson album)" for a query about history), ratings feed back what you've
#  starred, and tuning rules hold associations learned through the
#  /tune-search protocol.
# --------------------------------------------------------------------------- #

def _tuning_path() -> Path:
    return knowledge_dir() / "search_tuning.json"


def tuning_rules() -> list[dict]:
    try:
        r = json.loads(_tuning_path().read_text(encoding="utf-8"))
        return r if isinstance(r, list) else []
    except Exception:
        return []


def save_tuning(rules: list[dict]) -> None:
    core.write_atomic(_tuning_path(), json.dumps(rules, indent=1))


def _pattern_in(pattern: str, hay: str) -> bool:
    """Substring match that RESPECTS case when the pattern carries meaning in
    its case ('HIStory' must not degrade into 'history' and nuke every real
    history article); all-lowercase patterns match case-insensitively."""
    if pattern != pattern.lower():
        return pattern in hay
    return pattern in hay.lower()


def apply_tuning(query: str, hits: list[dict],
                 rules: list[dict] | None = None) -> list[dict]:
    """Apply learned associations: rules whose `match` appears in the query
    demote/boost hits by title+path substring. Deltas are decisive (±1000) —
    a rule exists precisely because ranking got it wrong on its own."""
    q = query.lower()
    for r in (tuning_rules() if rules is None else rules):
        if r.get("match", "").lower() not in q:
            continue
        for h in hits:
            hay = f"{h.get('title', '')} {h.get('path', '')}"
            if any(_pattern_in(d, hay) for d in r.get("demote", [])):
                h["score"] = h.get("score", 0.0) - 1000.0
                h["tuned"] = "demoted"
            if any(_pattern_in(b, hay) for b in r.get("boost", [])):
                h["score"] = h.get("score", 0.0) + 1000.0
                h["tuned"] = "boosted"
    hits.sort(key=lambda h: -h.get("score", 0.0))
    return hits


def rank_hits(query: str, pool: list[dict], limit: int = 8) -> list[dict]:
    """Candidate pool -> final order: cross-encoder relevance (GPU, safe
    no-op when absent) + ratings boosts + tuning rules."""
    items = [dict(h) for h in pool]
    n = len(items)
    for i, h in enumerate(items):                 # base: kiwix order, 0..1
        h["text"] = f"{h.get('title', '')}. {h.get('snippet', '')}"
        h["score"] = (n - i) / max(n, 1)
    if core.load_config().get("use_reranker", True):
        from . import rerank
        items = rerank.rerank(query, items)
        for h in items:
            if "rerank_score" in h:               # logits, roughly -11..+11
                h["score"] = float(h["rerank_score"])
    try:
        from . import ratings
        boosts = ratings.boost_for(ratings._entity(query))
        for h in items:                           # learned stars: ±0.3-ish,
            h["score"] += boosts.get(h.get("path", ""), 0.0) * 8  # make felt
    except Exception:
        pass
    return apply_tuning(query, items)[:limit]


def _last_search_path() -> Path:
    return knowledge_dir() / "_last_search.json"


def kb_search(query: str, limit: int = 8) -> int:
    if not tools_ready():
        print("Knowledge Vault not set up (kiwix tools missing).")
        return 2
    if not local_zims():
        print("No corpora downloaded yet. Run: python ultra.py  -> Knowledge Vault.")
        return 3
    pool = search(query, max(limit * 3, 18))      # wide pool for the reranker
    if not pool:
        print(f"No local results for: {query}")
        return 1
    hits = rank_hits(query, pool, limit)
    print(f"Local results for: {query}\n")
    for i, h in enumerate(hits, 1):
        tag = {"demoted": " [demoted by tuning]",
               "boosted": " [boosted by tuning]"}.get(h.get("tuned"), "")
        print(f"[{i}] {h['title']}   ({h['book']}){tag}")
        if h.get("snippet"):
            print(f"     {h['snippet'][:200]}")
        print(f"     read: python ultra.py kb-read \"{h['book']}\" \"{h['path']}\"")
    try:
        core.write_atomic(_last_search_path(), json.dumps(
            {"query": query, "paths": [h["path"] for h in hits],
             "ts": time.strftime("%Y-%m-%d %H:%M:%S")}))
    except Exception:
        pass
    print("\nbad results? `ultra kb rate <0-5>` — or tell Claude to run "
          "/tune-search")
    return 0


def cmd_rate(stars: int) -> int:
    """Rate the LAST kb search (0-5). Feeds the ratings boost + gives the
    /tune-search protocol its trail of what disappointed you."""
    try:
        last = json.loads(_last_search_path().read_text(encoding="utf-8"))
    except Exception:
        print("no recent search to rate — run `ultra kb \"...\"` first")
        return 1
    from . import ratings
    ratings.rate(last["query"], last.get("paths", []), stars, mode="search")
    print(f"saved {stars}★ for '{last['query']}'"
          + ("  (low rating noted — `/tune-search` in Claude can fix this "
             "topic)" if stars <= 2 else ""))
    return 0


def cmd_tune(args: list[str]) -> int:
    """`ultra kb tune list|add|rm|test` — manage learned search associations.
    add:  ultra kb tune add "<query-term>" --demote "X" [--boost "Y"] [--note t]
    test: ultra kb tune test "<query>"   (before/after, marks tuned hits)"""
    sub = args[0].lower() if args else "list"
    rules = tuning_rules()
    if sub == "list":
        if not rules:
            print("no tuning rules yet — "
                  "`ultra kb tune add \"<term>\" --demote \"<title>\"`")
        for r in rules:
            print(f"[{r['id']}] when query has '{r['match']}': "
                  + " ".join([f"demote {d!r}" for d in r.get("demote", [])]
                             + [f"boost {b!r}" for b in r.get("boost", [])])
                  + (f"   — {r['note']}" if r.get("note") else ""))
        return 0
    if sub == "add" and len(args) > 1:
        match, demote, boost, note = args[1], [], [], ""
        i = 2
        while i < len(args):
            if args[i] == "--demote" and i + 1 < len(args):
                demote.append(args[i + 1]); i += 2
            elif args[i] == "--boost" and i + 1 < len(args):
                boost.append(args[i + 1]); i += 2
            elif args[i] == "--note" and i + 1 < len(args):
                note = args[i + 1]; i += 2
            else:
                i += 1
        if not (demote or boost):
            print("nothing to do — give --demote and/or --boost"); return 2
        nid = max((r["id"] for r in rules), default=0) + 1
        rules.append({"id": nid, "match": match.lower(), "demote": demote,
                      "boost": boost, "note": note,
                      "created": time.strftime("%Y-%m-%d")})
        save_tuning(rules)
        print(f"rule [{nid}] saved — test it: ultra kb tune test \"{match}\"")
        return 0
    if sub == "rm" and len(args) > 1 and args[1].isdigit():
        keep = [r for r in rules if r["id"] != int(args[1])]
        if len(keep) == len(rules):
            print(f"no rule [{args[1]}]"); return 1
        save_tuning(keep)
        print(f"rule [{args[1]}] removed")
        return 0
    if sub == "test" and len(args) > 1:
        query = " ".join(args[1:])
        pool = search(query, 18)
        if not pool:
            print("no results to test against"); return 1
        before = rank_hits(query, pool, 8)        # includes tuning already…
        plain = [dict(h) for h in pool][:8]       # raw kiwix order
        print(f"raw kiwix order          vs   tuned+reranked ('{query}')")
        for i in range(max(len(plain), len(before))):
            l = plain[i]["title"][:34] if i < len(plain) else ""
            r = before[i]["title"][:34] if i < len(before) else ""
            mark = {"demoted": "▼", "boosted": "▲"}.get(
                before[i].get("tuned"), " ") if i < len(before) else " "
            print(f"  {i+1}. {l:<36} | {mark} {r}")
        return 0
    print('usage: ultra kb tune list · add "<term>" --demote "X" '
          '[--boost "Y"] [--note t] · rm <id> · test "<query>"')
    return 2


def kb_read(book: str, path: str) -> int:
    if not tools_ready():
        print("Knowledge Vault not set up.")
        return 2
    print(read_article(book, path))
    return 0


# --------------------------------------------------------------------------- #
#  Interactive menu tools
# --------------------------------------------------------------------------- #

def _status_lines() -> list[str]:
    zims = local_zims()
    lines = [f"Knowledge dir: {knowledge_dir()}",
             f"kiwix tools:   {'ready' if tools_ready() else 'MISSING'}",
             f"Corpora:       {len(zims)} downloaded",
             f"Server:        {'running ' + BASE if server_running() else 'stopped'}"]
    for z in zims:
        size = z.stat().st_size / 1024 / 1024 / 1024
        lines.append(f"   - {z.name}  ({size:.1f} GB)")
    return lines


def vault_status(ctx=None) -> None:
    ui.clear(); ui.title_bar("Knowledge Vault — Status", "local offline corpus")
    print()
    for ln in _status_lines():
        ui.info(ln)
    print()
    ui.pause()


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


def _audit_lines() -> list[str]:
    if not serve_start():
        return ["Knowledge server unavailable (kiwix tools missing?)."]
    a = audit()
    L = [f"Corpora on disk : {a['zims']}   ({_fmt_bytes(a['total_bytes'])})",
         f"Registered/searchable : {len(a['registered'])} book(s), "
         f"{a['articles']:,} articles",
         f"Whole-library search working : {'YES' if a['search_ok'] else 'NO'}",
         ""]
    L.append("Registered corpora (these DO appear in search):")
    for b in sorted(a["registered"], key=lambda x: -x["articles"]):
        L.append(f"   {b['articles']:>9,}  {b['filename']}")
    if a["dark"]:
        L += ["", "⚠  NOT REGISTERED — these will NOT appear in search:"]
        for d in a["dark"]:
            note = ("still downloading — will register on completion"
                    if d["growing"] else
                    "run 'Rebuild index' (a partial/locked ZIM won't register)")
            L.append(f"   !! {d['stem']}  ({_fmt_bytes(d['bytes'])}) — {note}")
    else:
        L += ["", "✓  Every downloaded corpus is registered and searchable."]
    added, failed = last_reindex_report()
    if failed:
        L += ["", "Last index rebuild skipped:"]
        for fn, why in failed:
            L.append(f"   - {fn}: {why}")
    return L


def vault_audit(ctx=None) -> None:
    ui.clear(); ui.title_bar("Library Health & Coverage",
                             "is everything you downloaded actually searchable?")
    print()
    for ln in _audit_lines():
        if ln.startswith("   !!") or "NOT REGISTERED" in ln or ln.endswith("NO"):
            ui.warn(ln)
        elif ln.startswith("✓"):
            ui.ok(ln)
        else:
            ui.info(ln)
    print()
    if any(d for d in audit()["dark"] if not d["growing"]):
        if ui.ask_yesno("Some corpora aren't registered. Rebuild the index now?"):
            ui.info("Rebuilding library index…")
            n = rebuild_library(); serve_stop(); serve_start()
            ui.ok(f"Reindexed — {n} book(s) now registered.")
    ui.pause()


def kb_audit() -> int:
    """Headless: python ultra.py kb-audit"""
    for ln in _audit_lines():
        print(ln)
    return 0


def vault_search(ctx=None) -> None:
    ui.clear(); ui.title_bar("Search the Vault", "offline full-text search")
    if not local_zims():
        ui.err("No corpora downloaded yet. Use 'Download corpora' first.")
        ui.pause(); return
    ui.dim("Type keywords (e.g. 'install python ubuntu'), Enter to search, a "
           "number to open, 'm' for more results, 'r' to rate, 'a' for AI "
           "reading list, or 'q' to go back.")
    page = 12
    last_paths: list = []
    last_query = ""
    while True:
        q = ui.prompt("search> ").strip()
        if not q or q.lower() in ("q", "quit", "exit"):
            return
        if q.lower() == "r" and last_query:
            _rate_last(last_query, last_paths); continue
        if q.lower() == "a":
            from . import suggest as ai_suggest
            topic = ui.prompt("topic for AI reading list: ").strip()
            if topic:
                print(); ai_suggest.cmd_learn(topic)
            continue
        last_query = q
        start, hits = 0, search(q, page, 0)
        last_paths = [h["path"] for h in hits]
        if not hits:
            ui.warn("No results — try simpler keywords (fewer, more specific words).")
            continue
        while True:
            print()
            for i, h in enumerate(hits, 1):
                print("  " + ui._c(f"[{i}]", ui.C.BOLD + ui.C.CYN) +
                      f" {h['title']}  " + ui._c(f"({h['book'].split('_20')[0]})", ui.C.DIM))
            print(ui._c(f"  (showing {start + 1}-{start + len(hits)} — "
                        f"'m' = more, # = open, Enter = new search)", ui.C.DIM))
            sel = ui.prompt("Open # / m / Enter: ").strip().lower()
            if sel == "m":
                start += page
                more = search(q, page, start)
                if not more:
                    ui.dim("No further results."); start -= page
                else:
                    hits = more
                continue
            if sel.isdigit() and 1 <= int(sel) <= len(hits):
                h = hits[int(sel) - 1]
                url = f"{BASE}/content/{h['book']}/{h['path']}"
                serve_start()                            # ensure Kiwix is up
                ui.info(f"Opening {h['title']} in your browser...")
                import webbrowser
                webbrowser.open(url)
                continue
            break   # Enter / anything else -> new search


def vault_serve(ctx=None) -> None:
    ui.clear(); ui.title_bar("Knowledge Vault — Web Reader", "browse in your browser")
    if not local_zims():
        ui.err("No corpora downloaded yet."); ui.pause(); return
    ui.info("Starting local Kiwix server...")
    if serve_start():
        ui.ok(f"Server running at {BASE}")
        if ui.ask_yesno("Open it in your browser now?", "Knowledge Vault"):
            core.open_in_os(BASE)
    else:
        ui.err("Could not start the server.")
    ui.pause()


def vault_download(ctx=None) -> None:
    ui.clear(); ui.title_bar("Download Corpora", "add offline knowledge")
    have_prefixes = {z.name.split("20")[0] for z in local_zims()}
    items = []
    keys = list(CATALOG)
    for i, key in enumerate(keys, 1):
        meta = CATALOG[key]
        owned = any(pre.startswith(meta["prefix"]) or meta["prefix"].startswith(pre)
                    for pre in have_prefixes)
        mark = " [have]" if owned else ""
        items.append((str(i), f"{meta['title']}  ({meta['approx']}){mark}"))
    choice = ui.menu("Download Corpora", "pick one to download (resumable)",
                     items, "Back")
    if choice == "0" or not choice or not choice.isdigit():
        return
    idx = int(choice) - 1
    if not (0 <= idx < len(keys)):
        return
    key = keys[idx]; meta = CATALOG[key]
    ui.info(f"Resolving newest {meta['title']} ...")
    resolved = resolve_latest(meta["subdir"], meta["prefix"])
    if not resolved:
        ui.err("Could not find that corpus on the mirror."); ui.pause(); return
    fname, url = resolved
    dest = knowledge_dir() / fname
    if not ui.ask_yesno(f"Download {fname}\nto {dest}?\n\n"
                        "This runs in the foreground; large files take a while. "
                        "It resumes if interrupted.", "Download"):
        return
    ui.info(f"Downloading {fname} (Ctrl+C to pause; re-run to resume)...")
    rc = subprocess.call(["curl", *CURL_FLAGS, "-C", "-", "-o", str(dest), url])
    if rc == 0:
        ui.ok("Download complete. Rebuilding library index...")
        rebuild_library()
        ui.ok("Added to the vault.")
    else:
        ui.warn("Download interrupted — re-run to resume from where it stopped.")
    ui.pause()


def vault_ai_chat(ctx=None) -> None:
    ui.clear(); ui.title_bar("Ask Local AI", "RAG chat over your offline vault")
    if not local_zims():
        ui.err("No corpora downloaded yet. Use 'Download corpora' first.")
        ui.pause(); return
    ui.info("Opening the local AI chat window...")
    ui.dim("(Uses your Ollama models + the offline vault. Close it to return.)")
    from . import ai_chat
    ai_chat.open_chat_window()


def _rate_last(query: str, paths: list) -> None:
    """Prompt the user to rate the most recent search results (0-5)."""
    from . import ratings
    ui.dim("  0 = nothing  ·  1 = nothing relevant  ·  3 = some useful  ·  "
           "5 = exactly what I needed")
    s = ui.prompt("  rating (0-5, Enter to skip): ").strip()
    if s.isdigit():
        stars = max(0, min(5, int(s)))
        ratings.rate(query, paths, stars, mode="search")
        ui.ok(f"Saved {stars}★ — future searches on this topic will improve.")


def _tool_learn(ctx=None) -> None:
    from . import suggest as ai_suggest
    ui.title_bar("Learn — AI-guided reading list",
                 "your local model recommends articles from your vault")
    topic = ui.prompt("What do you want to learn about? ").strip()
    if not topic:
        ui.pause(); return
    print()
    ai_suggest.cmd_learn(topic)
    ui.pause()


def _tool_ratings_stats(ctx=None) -> None:
    from . import ratings
    ui.title_bar("Search feedback — how the system is learning")
    s = ratings.stats()
    if not s.get("count"):
        ui.info("No ratings yet.")
        ui.dim("Rate results with 'r' inside search or after 'Learn' — the "
               "system boosts articles that scored well next time.")
    else:
        ui.info(f"Total ratings : {s['count']}")
        ui.info(f"Topics rated  : {s['topics']}")
        ui.info(f"Average       : {s['avg']:.2f}★")
        print("  Distribution :")
        for k, v in s["dist"].items():
            bar = "█" * min(30, v)
            print(f"    {k}★  {bar}  ({v})")
    ui.pause()


def register() -> core.Category:
    cat = core.Category("kb", "Knowledge Vault (offline Wikipedia)")
    cat.add("ai", "Ask Local AI  (chat + pictures, offline)", vault_ai_chat)
    cat.add("learn", "Learn — AI plans your reading list", _tool_learn)
    cat.add("status", "Vault status", vault_status)
    cat.add("audit", "Library health & coverage (what's searchable)", vault_audit)
    cat.add("search", "Search the vault (offline)", vault_search)
    cat.add("ratings", "Search feedback stats", _tool_ratings_stats)
    cat.add("serve", "Open web reader in browser", vault_serve)
    cat.add("download", "Download corpora", vault_download)
    try:
        from . import fixit
        fixit.register_tools(cat)
    except Exception:
        pass
    return cat
