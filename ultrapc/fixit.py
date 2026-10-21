"""Fix-It — guided offline troubleshooting for networking & sysadmin problems.

Combines three offline sources with the local AI:
  1. The curated troubleshoot corpus (runbooks / cisco / windows / linux
     quick-refs / RFCs) under  C:\\Ultra-PC-Knowledge\\troubleshoot,
     semantically indexed with the local embedding model.
  2. tldr pages (6,800+ command cheat sheets) — exact-name lookup.
  3. The Kiwix vault (Server Fault, Super User, Unix&Linux, Network
     Engineering SE, Ask Ubuntu, Arch Wiki, ...) via whole-library search.

CLI:
  python ultra.py fix "<problem>"       guided diagnostic session (local AI)
  python ultra.py fix index             (re)build the corpus embedding index
  python ultra.py fix search "<q>"      raw corpus+vault retrieval, no AI
  python ultra.py fix tldr <command>    command cheat sheet
  python ultra.py fix prompt "<problem>"  one-shot: build a Claude-ready prompt
  python ultra.py fix status

Inside a session:  /run <cmd>  run a read-only diagnostic (confirmed), feed the
                              output back to the AI
                   /solved   record what fixed it -> distils into the corpus so
                              the same problem is answered from history next time
                   /prompt  write a Claude escalation prompt from the dialog
                   /kb <q>  pull fresh references for a sub-question
                   /tldr <cmd>  show a command cheat sheet
                   /quit    leave

Retrieval is hybrid: BM25 keyword + embedding cosine, fused with Reciprocal
Rank Fusion — so exact error strings (EXSTART, 0x80070035, eth0) hit, and
`fix search` still works with Ollama down (keyword-only).
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from . import ai, core, knowledge, ui

TROUBLE = knowledge.knowledge_dir() / "troubleshoot"
INDEX = TROUBLE / "_fix-index.json"
TLDR = TROUBLE / "tldr" / "pages"
SOLVED_DIR = TROUBLE / "solved"                # self-improving: recorded fixes
SOLVED_FILE = SOLVED_DIR / "solved-cases.md"
CORPUS_DIRS = ("runbooks", "cisco", "windows", "linux", "solved")   # embedded
RFC_DIR = TROUBLE / "rfc"

SYSTEM = (
    "You are a senior network/systems engineer running a hands-on "
    "troubleshooting session, fully offline. Method: work bottom-up "
    "(link -> addressing -> reachability -> transport -> service), change one "
    "thing at a time, and rely on EVIDENCE — ask the user to run specific "
    "commands and paste the output before concluding anything. Give exact "
    "commands for their platform (Linux iproute2 / Cisco IOS / Windows "
    "PowerShell), each on its own line in a fenced code block so the tool can "
    "offer to run the read-only ones automatically and feed you the real "
    "output. Prefer the cheap checks first. When reference material is "
    "provided below, ground your answers in it and mention the source name "
    "in brackets like [runbooks/ssh.md] or [serverfault]. If the user seems "
    "stuck or the problem exceeds what you can resolve, suggest they type "
    "/prompt to generate a well-structured escalation prompt for Claude. "
    "Be concise: next 1-3 diagnostic steps at a time, not a wall of theory."
)


# --------------------------------------------------------------------------- #
#  Corpus index (reuses ai.embed — nomic prefixes added here)
# --------------------------------------------------------------------------- #

def _md_sections(text: str, src: str) -> list[dict]:
    """Split a markdown doc on headings; sub-split long sections w/ overlap."""
    out: list[dict] = []
    head = src
    buf: list[str] = []

    def flush():
        body = "\n".join(buf).strip()
        if not body:
            return
        if len(body) <= 1600:
            out.append({"src": src, "head": head, "text": body})
        else:
            i = 0
            while i < len(body):
                out.append({"src": src, "head": head,
                            "text": body[i:i + 1600]})
                i += 1400
        buf.clear()

    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif line.startswith("#") and not in_fence:   # real heading, not a shell comment
            flush()
            head = line.lstrip("# ").strip() or head
        buf.append(line)
    flush()
    return out


def _rfc_chunks(text: str, src: str) -> list[dict]:
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        body = "\n".join(lines[i:i + 90]).strip()
        if body:
            out.append({"src": src, "head": src, "text": body})
        i += 75
    return out


def _gather_chunks() -> list[dict]:
    chunks: list[dict] = []
    for d in CORPUS_DIRS:
        for f in sorted((TROUBLE / d).glob("*.md")):
            rel = f"{d}/{f.name}"
            chunks.extend(_md_sections(f.read_text(encoding="utf-8",
                                                   errors="replace"), rel))
    for f in sorted(RFC_DIR.glob("*.txt")):
        chunks.extend(_rfc_chunks(f.read_text(encoding="utf-8",
                                              errors="replace"),
                                  f"rfc/{f.name}"))
    return chunks


def build_index() -> dict:
    """Embed the corpus. Returns the index dict (also written to disk)."""
    if not ai.available():
        raise RuntimeError("Ollama is not running — start it, then retry.")
    model = ai.embed_model()
    if not model:
        raise RuntimeError("No embedding model installed "
                           "(ollama pull nomic-embed-text).")
    chunks = _gather_chunks()
    t0 = time.time()
    vecs = ai.embed([f"search_document: {c['head']}\n{c['text']}"
                     for c in chunks], model=model)
    if len(vecs) != len(chunks):
        raise RuntimeError("Embedding failed part-way; index not written.")
    idx = {"built": datetime.now().isoformat(timespec="seconds"),
           "embed_model": model, "chunks": chunks, "vectors": vecs}
    core.write_atomic(INDEX, json.dumps(idx))
    core.log("fixit", f"indexed {len(chunks)} chunks in "
                      f"{time.time() - t0:.0f}s ({model})", "SUCCESS")
    return idx


_IDX_CACHE: dict | None = None


def _load_index() -> dict | None:
    global _IDX_CACHE
    if _IDX_CACHE is None and INDEX.exists():
        try:
            _IDX_CACHE = json.loads(INDEX.read_text(encoding="utf-8"))
        except Exception:
            return None
    return _IDX_CACHE


# --- keyword (BM25) side of the hybrid ranker -------------------------------- #
# Error strings ("EXSTART", "0x80070035", "eth0", "10.1.2.3") are lexical, not
# semantic — embeddings blur them. BM25 catches the exact token; the two signals
# are fused with Reciprocal Rank Fusion. BM25 also means `fix search` still works
# with Ollama down (pure-keyword fallback).

_WORD_RE = re.compile(r"[a-z0-9]+(?:[._/:-][a-z0-9]+)*")
_BM25_CACHE: tuple | None = None   # (index-id, prepared-stats)


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _bm25_prep(idx: dict) -> dict:
    """Build (and cache) per-chunk term stats for the loaded index."""
    global _BM25_CACHE
    if _BM25_CACHE is not None and _BM25_CACHE[0] is idx:
        return _BM25_CACHE[1]
    import math
    from collections import Counter
    docs = [_tokenize(c["head"] + " " + c["text"]) for c in idx["chunks"]]
    n = len(docs) or 1
    df: dict[str, int] = {}
    for toks in docs:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
    doclen = [len(d) for d in docs]
    prep = {"tf": [Counter(d) for d in docs], "idf": idf, "doclen": doclen,
            "avg": (sum(doclen) / n) or 1.0, "n": n}
    _BM25_CACHE = (idx, prep)
    return prep


def _bm25_scores(idx: dict, query: str, k1: float = 1.5, b: float = 0.75) -> list[float]:
    prep = _bm25_prep(idx)
    qterms = set(_tokenize(query))
    out = []
    for i in range(prep["n"]):
        tf, dl, s = prep["tf"][i], prep["doclen"][i], 0.0
        norm = k1 * (1 - b + b * dl / prep["avg"])
        for t in qterms:
            f = tf.get(t, 0)
            if f:
                s += prep["idf"].get(t, 0.0) * (f * (k1 + 1)) / (f + norm)
        out.append(s)
    return out


def corpus_search(query: str, top: int = 6) -> list[dict]:
    """Hybrid keyword+semantic search over the troubleshoot corpus.

    BM25 (keyword) and embedding cosine are each ranked, then fused with
    Reciprocal Rank Fusion. Works keyword-only when Ollama is down. [] if the
    index is missing."""
    idx = _load_index()
    if not idx:
        return []
    chunks = idx["chunks"]
    n = len(chunks)
    if not n:
        return []

    # keyword signal — always available, no AI needed
    bm = _bm25_scores(idx, query)

    # semantic signal — only when the embedder is up. Batched cosine runs on the
    # best backend (GPU torch > numpy > python); bias applied per chunk after.
    cos = [0.0] * n
    if ai.available():
        qv = ai.embed([f"search_query: {query}"], model=idx.get("embed_model"))
        if qv:
            from . import vmath
            bias = {"rfc/": -0.07, "solved/": 0.05}   # solved cases are battle-tested
            sims = vmath.cosine_all(qv[0], idx["vectors"])
            cos = [s + next((d for p, d in bias.items()
                             if chunks[j]["src"].startswith(p)), 0.0)
                   for j, s in enumerate(sims)]

    order_bm = sorted(range(n), key=lambda i: -bm[i])
    order_cos = sorted(range(n), key=lambda i: -cos[i])
    K = 60
    fused = [0.0] * n
    for rank, i in enumerate(order_bm):
        if bm[i] > 0:
            fused[i] += 1.0 / (K + rank)
    for rank, i in enumerate(order_cos):
        if cos[i] > 0.30:            # ignore weak semantic noise
            fused[i] += 1.0 / (K + rank)

    ranked = sorted((i for i in range(n) if fused[i] > 0), key=lambda i: -fused[i])
    top_score = fused[ranked[0]] if ranked else 1.0

    # When the GPU reranker is on, gather a WIDER pool here and let the
    # cross-encoder pick the final `top` — that's where the precision comes from.
    do_rerank = bool(cos and any(cos)) and core.load_config().get("use_reranker", True)
    pool = max(top * 4, 24) if do_rerank else top

    out, per_src = [], {}
    for i in ranked:
        c = chunks[i]
        if per_src.get(c["src"], 0) >= 2:      # diversity: max 2 chunks/file
            continue
        per_src[c["src"]] = per_src.get(c["src"], 0) + 1
        # display a 0-1 relative-relevance so the fused RRF value reads naturally
        out.append(dict(score=round(fused[i] / top_score, 3), **c))
        if len(out) >= pool:
            break

    if do_rerank and len(out) > 1:
        from . import rerank
        if rerank.available():
            out = rerank.rerank(query, out, text_key="text", top_k=top)
            # re-derive the 0-1 display score from the reranked order so it reads
            # monotonically (cross-encoder logits are unbounded / can be negative)
            rs = [o.get("rerank_score", 0.0) for o in out]
            lo, hi = min(rs), max(rs)
            for o in out:
                o["score"] = (round((o["rerank_score"] - lo) / (hi - lo), 3)
                              if hi > lo else 1.0)
    return out[:top]


# --------------------------------------------------------------------------- #
#  tldr + kiwix retrieval
# --------------------------------------------------------------------------- #

def tldr_page(cmd: str) -> str | None:
    slug = cmd.strip().lower().replace(" ", "-")
    for plat in ("common", "linux", "windows"):
        p = TLDR / plat / f"{slug}.md"
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
    return None


def vault_hits(query: str, top: int = 4) -> list[dict]:
    """Kiwix whole-library hits, troubleshooting books ranked above Wikipedia."""
    try:
        if not knowledge.server_running():
            knowledge.serve_start()
        hits = knowledge.search(query, limit=top * 3)
    except Exception:
        return []
    hits.sort(key=lambda h: "wikipedia" in h.get("book", "").lower())
    return hits[:top]


def _reference_block(problem: str, n_corpus: int = 6, n_vault: int = 4) -> str:
    """Assemble a grounded reference block for the model."""
    parts: list[str] = []
    for c in corpus_search(problem, top=n_corpus):
        parts.append(f"--- [{c['src']} · {c['head']}]\n{c['text'][:1200]}")
    for h in vault_hits(problem, top=n_vault):
        try:
            body = knowledge.read_article(h["book"], h["path"], max_chars=1100)
        except Exception:
            continue
        parts.append(f"--- [{h['book']} · {h.get('title', h['path'])}]\n{body}")
    return "\n\n".join(parts) if parts else "(no offline references matched)"


# --------------------------------------------------------------------------- #
#  Safe diagnostic command execution — the AI proposes read-only checks; the
#  user confirms each; output is captured back into the session (and thus the
#  escalation prompt). Allowlist + no-shell-metachar + no-mutator-token, so a
#  proposed command can only ever read state, never change it.
# --------------------------------------------------------------------------- #

SAFE_FIRST = {
    # native diagnostics (Windows + Linux)
    "ping", "tracert", "traceroute", "pathping", "mtr", "ipconfig", "ifconfig",
    "ip", "ss", "netstat", "arp", "route", "getmac", "hostname", "whoami",
    "systeminfo", "ver", "uname", "nslookup", "dig", "host", "resolvectl",
    "nmcli", "ethtool", "netsh", "sysctl",
    # PowerShell read-only cmdlets
    "test-netconnection", "resolve-dnsname", "get-netipconfiguration",
    "get-netipaddress", "get-netroute", "get-dnsclientserveraddress",
    "get-netadapter", "get-nettcpconnection", "get-netneighbor",
    "get-netadapterstatistics", "get-netconnectionprofile",
}
_PS_CMDLETS = {c for c in SAFE_FIRST if "-" in c}
# any of these tokens means the command mutates state -> reject. (Bare flags
# like -d are context-dependent — `arp -d` deletes but `tracert -d` is read-only
# — so those are guarded per-command below, not globally.)
_MUTATORS = {"add", "del", "delete", "set", "flush", "flushdns", "release",
             "release6", "renew", "renew6", "remove", "rm", "stop", "start",
             "restart", "disable", "enable", "new", "reset", "register",
             "unregister", "import", "export"}
# per-command flags that mutate (checked only for that command's first token)
_MUTATING_FLAGS = {"arp": {"-d", "-s"}, "ip": {"-b", "-batch"},
                   "ethtool": {"-s", "-a", "-g", "-c", "-w"}}
_META_RE = re.compile(r"[;&|<>`]|\$\(")


def _is_safe(cmd: str) -> bool:
    """True only for read-only diagnostic commands (allowlisted, no chaining,
    no state-changing subcommand)."""
    import shlex
    cmd = cmd.strip()
    if not cmd or _META_RE.search(cmd):
        return False
    try:
        toks = shlex.split(cmd, posix=False)
    except ValueError:
        return False
    if not toks:
        return False
    first = toks[0].lower().strip('"')
    if first not in SAFE_FIRST:
        return False
    bad_flags = _MUTATING_FLAGS.get(first, set())
    for t in toks[1:]:
        tl = t.lower().strip('"/')
        if tl in _MUTATORS or t.lower() in bad_flags:
            return False
    return True


def _extract_commands(text: str) -> list[str]:
    """Pull candidate commands from fenced/inline code in the AI's answer,
    keeping only the ones that pass the read-only safety check."""
    lines: list[str] = []
    for blk in re.findall(r"```[a-zA-Z0-9]*\n(.*?)```", text, re.S):
        lines += blk.splitlines()
    lines += re.findall(r"`([^`\n]+)`", text)
    out: list[str] = []
    for ln in lines:
        ln = re.sub(r"^\s*(\$|#|PS[^>]*>|[A-Za-z]:\\[^>]*>|>)\s*", "", ln).strip()
        if ln and not ln.startswith("#") and _is_safe(ln) and ln not in out:
            out.append(ln)
    return out[:6]


def _run_safe(cmd: str, timeout: int = 25) -> str:
    """Execute an already-validated safe command; return combined output."""
    import shlex
    import subprocess
    toks = shlex.split(cmd, posix=False)
    first = toks[0].lower().strip('"')
    if first in _PS_CMDLETS:
        argv = ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd]
    else:
        argv = toks
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           errors="replace", timeout=timeout, shell=False)
        out = ((p.stdout or "") + (p.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        out = f"(timed out after {timeout}s)"
    except FileNotFoundError:
        out = f"(command not found on this machine: {first})"
    except Exception as exc:
        out = f"(error running it: {exc})"
    return out.strip()[:4000] or "(no output)"


def _offer_commands(answer: str, messages: list[dict], ca, blue, green) -> bool:
    """Offer to run any safe checks the AI proposed. Runs the chosen ones (each
    confirmed), feeds their output back as a user turn. Returns True if it ran
    at least one (so the caller lets the AI react to the evidence)."""
    cmds = _extract_commands(answer)
    if not cmds:
        return False
    print(ca.color("  ⚙ read-only checks I can run for you:", green))
    for j, c in enumerate(cmds, 1):
        print("     " + ca.color(f"[{j}]", green) + " " + ca.color(c, PAPER))
    try:
        sel = input(ca.color("  run which? #/list ('1,3'), 'all', Enter=skip ▸ ",
                             MUTED)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not sel:
        return False
    if sel == "all":
        chosen = cmds
    else:
        picks = {int(x) for x in re.findall(r"\d+", sel)}
        chosen = [cmds[i - 1] for i in sorted(picks) if 1 <= i <= len(cmds)]
    if not chosen:
        return False

    collected: list[str] = []
    for c in chosen:
        try:
            if not ui.ask_yesno(f"Run:  {c}"):
                continue
        except Exception:
            break
        with ca.Spinner(f"  running {c[:40]}", style="dots", c=blue):
            out = _run_safe(c)
        print(ca.color(f"  $ {c}", green))
        for ln in out.splitlines()[:24]:
            print(ca.color("    " + ln, PAPER))
        extra = out.count("\n") - 23
        if extra > 0:
            print(ca.color(f"    … (+{extra} more lines captured)", MUTED))
        print(ca.gradient("  ·" + "─" * 64 + "·", blue, green))
        collected.append(f"$ {c}\n{out}")
    if not collected:
        return False
    messages.append({"role": "user", "content":
                     "I ran the checks. Here is the actual output — diagnose "
                     "from this evidence:\n\n```\n"
                     + "\n\n".join(collected) + "\n```"})
    return True


# --------------------------------------------------------------------------- #
#  Claude escalation prompt
# --------------------------------------------------------------------------- #

_PROMPT_TEMPLATE = """# Troubleshooting escalation — {date}

## Problem
{problem}

## Environment / topology
(fill in: OS + versions, devices in path, IPs/VLANs, what changed recently)

## Evidence collected
{evidence}

## Steps already tried, with results
{tried}

## Offline references consulted
{refs}

## Ask
Please diagnose the most likely root cause and give the next 3 concrete
diagnostic or corrective steps, with exact commands.
"""


def _write_prompt_file(text: str) -> Path:
    core.ensure_dirs()
    out = core.REPORTS_DIR / f"fix-prompt-{datetime.now():%Y%m%d-%H%M%S}.md"
    out.write_text(text, encoding="utf-8")
    return out


def generate_prompt(problem: str, transcript: list[dict]) -> Path:
    """Distill the session into a Claude-ready escalation prompt (local AI,
    with a plain template fallback)."""
    refs = [f"- {c['src']} · {c['head']}" for c in corpus_search(problem, 4)]
    body = None
    # Only distill with the model when there IS a session to distill — from a
    # bare problem statement the model invents plausible-looking "evidence"
    # (fake command outputs), which poisons the escalation. Template instead.
    has_session = any(m["role"] == "assistant" for m in transcript)
    if has_session and ai.available():
        convo = "\n".join(f"{m['role'].upper()}: {m['content'][:1500]}"
                          for m in transcript if m["role"] != "system")
        ask = (
            "Write a self-contained escalation prompt (markdown) that I can "
            "paste to an online AI assistant to get help with this problem. "
            "Include: ## Problem (one precise paragraph), ## Environment "
            "(everything we learned: OS, devices, IPs, versions), ## Evidence "
            "(the actual command outputs pasted during this session, verbatim "
            "in code blocks), ## Steps already tried and their results, and "
            "## Ask (what we want diagnosed). Do NOT invent details that are "
            "not in the session; mark unknowns as '(unknown)'. Session:\n\n"
            + convo)
        try:
            body = "".join(ai.chat_stream(ai.default_model(),
                                          [{"role": "user", "content": ask}]))
        except Exception:
            body = None
    if not body or body.startswith("\n[no local chat model"):
        tried = "\n".join(f"- {m['content'][:300]}" for m in transcript
                          if m["role"] == "user") or "(none recorded)"
        body = _PROMPT_TEMPLATE.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            problem=problem, evidence="(paste command output here)",
            tried=tried, refs="\n".join(refs) or "(none)")
    else:
        body += "\n\n## Offline references consulted\n" + ("\n".join(refs)
                                                           or "(none)")
    return _write_prompt_file(body)


# --------------------------------------------------------------------------- #
#  Self-improving corpus — solved cases distil back into indexed runbooks, so
#  the same problem is answered from your own history next time.
# --------------------------------------------------------------------------- #

def _index_append(new_chunks: list[dict]) -> bool:
    """Embed a few new chunks and append them to the on-disk index in place
    (no full rebuild). Returns True if the live index was updated."""
    global _BM25_CACHE
    idx = _load_index()
    if idx is None or not ai.available() or not new_chunks:
        return False
    vecs = ai.embed([f"search_document: {c['head']}\n{c['text']}"
                     for c in new_chunks], model=idx.get("embed_model"))
    if len(vecs) != len(new_chunks):
        return False
    idx["chunks"].extend(new_chunks)
    idx["vectors"].extend(vecs)
    idx["built"] = datetime.now().isoformat(timespec="seconds")
    core.write_atomic(INDEX, json.dumps(idx))
    _BM25_CACHE = None            # keyword stats now stale
    return True


def _evidence_from_transcript(transcript: list[dict]) -> str:
    """Pull the command-output blocks the user pasted/ran during the session."""
    blocks = []
    for m in transcript:
        if m["role"] == "user" and ("$ " in m["content"] or "```" in m["content"]):
            for b in re.findall(r"```.*?\n(.*?)```", m["content"], re.S):
                b = b.strip()
                if b:
                    blocks.append(b)
    return "\n\n".join(blocks[-4:])   # keep the last few, cap size


def record_solved(problem: str, resolution: str,
                  transcript: list[dict] | None = None) -> tuple[Path, bool]:
    """Append a solved case to the corpus and index it immediately. Returns
    (file, indexed_now)."""
    SOLVED_DIR.mkdir(parents=True, exist_ok=True)
    title = " ".join(problem.split()[:9]).strip().rstrip(".") or "case"
    evidence = _evidence_from_transcript(transcript or [])
    section = (
        f"\n\n# Solved: {title}\n\n"
        f"_recorded {datetime.now():%Y-%m-%d %H:%M}_\n\n"
        f"## Problem\n{problem.strip()}\n\n"
        f"## What fixed it\n{resolution.strip()}\n"
    )
    if evidence:
        section += f"\n## Evidence from the session\n```\n{evidence[:1500]}\n```\n"
    with SOLVED_FILE.open("a", encoding="utf-8") as fh:
        fh.write(section)
    core.log("fixit", f"recorded solved case: {title}", "SUCCESS")
    # index just this new section so it's searchable right away
    chunks = _md_sections(section, "solved/solved-cases.md")
    indexed = _index_append(chunks)
    return SOLVED_FILE, indexed


def list_solved() -> list[dict]:
    """Parse recorded solved cases (title + date) for display."""
    if not SOLVED_FILE.exists():
        return []
    text = SOLVED_FILE.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in re.finditer(r"# Solved: (.+?)\n+_recorded (.+?)_", text):
        out.append({"title": m.group(1).strip(), "date": m.group(2).strip()})
    return out


# --------------------------------------------------------------------------- #
#  Themed output helpers (Ultra-PC Frutiger Aero branding)
# --------------------------------------------------------------------------- #

MUTED = "#8fb8cf"      # muted cyan — captions/hints
PAPER = "#eaf6ff"      # near-white body text
RED = "#ff5f57"
AMBER = "#febc2e"


def _theme():
    """(cliart, blue, green) — one import point for all themed output."""
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


def _fx_header(subtitle: str) -> None:
    ca, blue, green = _theme()
    print()
    print(ca.gradient("  ╭◦°" + "─" * 62 + "°◦╮", blue, green))
    for row in ca.banner("FIX-IT", blue, green, font="thin").split("\n"):
        print("       " + row)
    print(ca.gradient(f"       ~ ° ·  {subtitle}  · ° ~", green, blue))
    print(ca.gradient("  ╰◦°" + "─" * 62 + "°◦╯", blue, green))
    print()


def _print_tldr(page: str) -> None:
    """Style a tldr page: title green, examples white, commands aqua."""
    ca, blue, green = _theme()
    for ln in page.splitlines():
        if ln.startswith("# "):
            print("  " + ca.gradient("▸ " + ln[2:], blue, green))
        elif ln.startswith(">"):
            print("  " + ca.color(ln[1:].strip(), MUTED))
        elif ln.startswith("- "):
            print("  " + ca.color("• " + ln[2:], PAPER))
        elif ln.startswith("`"):
            print("      " + ca.color(ln.strip("`"), green))
        elif ln.strip():
            print("  " + ln)
    print()


# --------------------------------------------------------------------------- #
#  The guided session
# --------------------------------------------------------------------------- #

def run_session(problem: str) -> int:
    ca, blue, green = _theme()
    _fx_header("evidence-first troubleshooting · offline")
    print(ca.color("  ▸ Problem: ", green) + ca.color(problem, "#ffffff"))

    if not ai.available():
        print(ca.color("  ✕ Ollama isn't running — start it for the guided "
                       "session.", RED))
        print(ca.color(f'    meanwhile, raw retrieval:  ultra fix search '
                       f'"{problem}"', MUTED))
        return 1
    model = ai.default_model()
    print(ca.color(f"    (model: {model} · offline · corpus + vault)", MUTED))
    print()

    if not _load_index():
        ca.loadbar("  first run — indexing the corpus", seconds=0.4,
                   c1=blue, c2=green)
        build_index()

    # -------- spinner while references + first answer are prepared -------- #
    holder = {"refs": ""}

    def _gather():
        holder["refs"] = _reference_block(problem)

    import threading
    th = threading.Thread(target=_gather, daemon=True)
    th.start()
    with ca.Spinner("  consulting runbooks + vault", style="dots", c=blue):
        th.join()
    messages = [
        {"role": "system", "content": SYSTEM + "\n\n=== OFFLINE REFERENCES ===\n"
                                      + holder["refs"]},
        {"role": "user", "content":
            f"My problem: {problem}\n\nStart the diagnosis: what are the "
            "first 1-3 things I should check, with exact commands?"},
    ]
    print(ca.gradient("  " + "─" * 66, blue, green))
    print(ca.color("   /run <cmd>", green) + ca.color(" check  ·", MUTED)
          + ca.color(" /solved", green) + ca.color(" record fix  ·", MUTED)
          + ca.color(" /prompt", green) + ca.color(" escalate  ·", MUTED)
          + ca.color(" /kb <q>", green) + ca.color(" refs  ·", MUTED)
          + ca.color(" /tldr", green) + ca.color("  ·", MUTED)
          + ca.color(" /quit", green))
    print(ca.gradient("  " + "─" * 66, blue, green))
    print()

    ai_label = ca.gradient("◆ AI ▸ ", blue, green)
    you_label = ca.color("● you ▸ ", green)

    while True:
        print(ai_label, end="", flush=True)
        answer = ""
        for tok in ai.chat_stream(model, messages):
            print(tok, end="", flush=True)
            answer += tok
        print()
        print(ca.gradient("  ·" + "─" * 64 + "·", blue, green))
        messages.append({"role": "assistant", "content": answer})

        # offer to run any read-only checks the AI proposed; if we do, feed the
        # real output back and let the AI react before asking the user again
        if _offer_commands(answer, messages, ca, blue, green):
            continue

        try:
            user = input(you_label).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            user = "/quit"
        if not user:
            continue
        low = user.lower()
        if low in ("/quit", "/q", "exit"):
            print(ca.gradient("  ~ ° ·  good hunting  · ° ~", green, blue))
            return 0
        if low in ("/solved", "/fixed"):
            try:
                res = input(ca.color("  what fixed it? ▸ ", green)).strip()
            except (EOFError, KeyboardInterrupt):
                print(); res = ""
            if not res:
                print(ca.color("  (skipped — nothing recorded)", MUTED)); print()
                continue
            with ca.Spinner("  distilling into your solved-cases corpus",
                            style="dots", c=blue):
                _, indexed = record_solved(problem, res, messages)
            print(ca.color("  ✓ recorded — Fix-It will recall this next time",
                           green))
            print(ca.color("    " + ("indexed now" if indexed
                           else "will index on next `ultra fix index`"), MUTED))
            print()
            continue
        if low.startswith("/prompt"):
            holder2 = {"p": None}

            def _distill():
                holder2["p"] = generate_prompt(problem, messages)

            th2 = threading.Thread(target=_distill, daemon=True)
            th2.start()
            with ca.Spinner("  distilling this session into a Claude prompt",
                            style="dots", c=blue):
                th2.join()
            path = holder2["p"]
            ca.loadbar("  packaging evidence", seconds=0.5, c1=blue, c2=green)
            print(ca.color("  ✓ escalation prompt ready", green))
            print(ca.color(f"    {path}", PAPER))
            print(ca.color("    paste its contents into Claude — it carries "
                           "your evidence + steps tried", MUTED))
            try:
                if ui.ask_yesno("Open the prompt file?"):
                    core.open_in_os(path)
            except Exception:
                pass
            print()
            continue
        if low.startswith("/tldr "):
            page = tldr_page(user[6:])
            print()
            if page:
                _print_tldr(page)
            else:
                print(ca.color("  (no tldr page for that command)", AMBER))
                print()
            continue
        if low.startswith("/run "):
            cmd = user[5:].strip()
            if not _is_safe(cmd):
                print(ca.color("  ✕ refused — only read-only diagnostics are "
                               "allowed (no state changes / chaining).", RED))
                print()
                continue
            try:
                if not ui.ask_yesno(f"Run:  {cmd}"):
                    continue
            except Exception:
                continue
            with ca.Spinner(f"  running {cmd[:40]}", style="dots", c=blue):
                out = _run_safe(cmd)
            print(ca.color(f"  $ {cmd}", green))
            for ln in out.splitlines()[:24]:
                print(ca.color("    " + ln, PAPER))
            print(ca.gradient("  ·" + "─" * 64 + "·", blue, green))
            messages.append({"role": "user", "content":
                             f"I ran `{cmd}`. Output:\n```\n{out}\n```"})
            continue
        if low.startswith("/kb "):
            with ca.Spinner("  pulling fresh references", style="dots", c=blue):
                extra = _reference_block(user[4:], n_corpus=4, n_vault=3)
            messages.append({"role": "system",
                             "content": "=== MORE REFERENCES ===\n" + extra})
            messages.append({"role": "user", "content": user[4:]})
            continue
        # normal turn — refresh retrieval when the message looks substantive
        if len(user) > 60:
            fresh = _reference_block(user, n_corpus=3, n_vault=2)
            if "(no offline references" not in fresh:
                messages.append({"role": "system",
                                 "content": "=== MORE REFERENCES ===\n" + fresh})
        messages.append({"role": "user", "content": user})


# --------------------------------------------------------------------------- #
#  CLI + menu
# --------------------------------------------------------------------------- #

def cmd_search(query: str) -> int:
    ca, blue, green = _theme()
    print()
    print(ca.color("  ▸ Fix-It search: ", green) + ca.color(query, "#ffffff"))
    print(ca.gradient("  " + "─" * 66, blue, green))
    hits = corpus_search(query, top=6)
    if hits:
        print(ca.color("  runbooks & references", MUTED))
        for h in hits:
            first = h["text"].strip().splitlines()[0][:80]
            print("   " + ca.color(f"{h['score']:.2f}", green)
                  + ca.color(f"  {h['src']} · {h['head']}", "#4fc3f7"))
            print("         " + ca.color(first, MUTED))
    else:
        print(ca.color("  (no corpus matches — index built? `ultra fix index`)",
                       AMBER))
    vh = vault_hits(query, top=4)
    if vh:
        print(ca.color("  vault (Server Fault / SE / Arch Wiki / ...)", MUTED))
        for h in vh:
            book = h["book"].split("_en_all")[0].split(".stackexchange")[0]
            print("   " + ca.color("◦ ", blue) + ca.color(f"[{book}] ", green)
                  + ca.color(h.get("title", h["path"]), PAPER))
    print(ca.gradient("  " + "─" * 66, green, blue))
    print(ca.color('  ▸ guided session:  ultra fix "<problem>"', MUTED))
    return 0


def cmd_status() -> int:
    ca, blue, green = _theme()
    idx = _load_index()
    n_tldr = sum(1 for _ in TLDR.rglob("*.md")) if TLDR.exists() else 0
    n_rfc = len(list(RFC_DIR.glob("*.txt"))) if RFC_DIR.exists() else 0
    n_docs = sum(len(list((TROUBLE / d).glob("*.md"))) for d in CORPUS_DIRS
                 if (TROUBLE / d).exists())

    def row(k, v, vc=PAPER):
        print("  " + ca.color("│", blue) + ca.color(f" {k:<14}", MUTED)
              + ca.color(str(v), vc)
              + " " * max(1, 50 - len(str(v))) + ca.color("│", green))

    print()
    print(ca.gradient("  ╭─ Fix-It · offline troubleshooter " + "─" * 31 + "╮",
                      blue, green))
    row("corpus", str(TROUBLE))
    row("curated docs", f"{n_docs}  (runbooks + platform quick-refs)")
    row("RFCs", n_rfc)
    row("tldr pages", n_tldr)
    if idx:
        row("index", f"{len(idx['chunks'])} chunks · {idx['embed_model']}")
        row("built", idx["built"])
    else:
        row("index", "NOT BUILT — ultra fix index", AMBER)
    up = ai.available()
    row("ollama", "up" if up else "DOWN — start it for guided sessions",
        green if up else RED)
    try:
        from . import vmath
        row("vector math", f"{vmath.backend()}"
            + ("  (GPU)" if vmath.gpu() else ""),
            green if vmath.gpu() else PAPER)
    except Exception:
        pass
    if core.load_config().get("use_reranker", True):
        try:
            from . import rerank
            rs = rerank.status()
            row("reranker", f"{rs['model'].split('/')[-1]} · {rs['device']}"
                + ("  ✓" if rs["loaded"] else "  (loads on first search)"),
                green if rs["device"] == "cuda" else PAPER)
        except Exception:
            pass
    print(ca.gradient("  ╰" + "─" * 66 + "╯", green, blue))
    return 0


def handle(argv: list[str]) -> int | None:
    """Dispatch `fix ...`; None if argv isn't ours."""
    if not argv or argv[0].lower() != "fix":
        return None
    rest = argv[1:]
    if not rest:
        ca, blue, green = _theme()
        _fx_header("evidence-first troubleshooting · offline")
        for cmd, desc in (
                ('fix "<problem>"', "guided diagnostic session (local AI)"),
                ("fix search <q>", "raw corpus + vault retrieval"),
                ("fix tldr <cmd>", "command cheat sheet"),
                ('fix prompt "<p>"', "one-shot Claude escalation prompt"),
                ("fix solved", "list / record solved cases (self-improving)"),
                ("fix index", "(re)build the corpus embedding index"),
                ("fix status", "corpus health")):
            print("   " + ca.color(f"ultra {cmd:<18}", green)
                  + ca.color(desc, MUTED))
        print()
        print(ca.color("   in-session: ", MUTED) + ca.color("/prompt", green)
              + ca.color(" · ", MUTED) + ca.color("/kb <q>", green)
              + ca.color(" · ", MUTED) + ca.color("/tldr <cmd>", green)
              + ca.color(" · ", MUTED) + ca.color("/quit", green))
        return cmd_status()
    sub = rest[0].lower()
    if sub == "index":
        ca, blue, green = _theme()
        try:
            holder = {"idx": None, "err": None}

            def _build():
                try:
                    holder["idx"] = build_index()
                except RuntimeError as exc:
                    holder["err"] = exc

            import threading
            th = threading.Thread(target=_build, daemon=True)
            th.start()
            with ca.Spinner("  embedding the troubleshoot corpus",
                            style="dots", c=blue):
                th.join()
            if holder["err"]:
                raise holder["err"]
            idx = holder["idx"]
            print(ca.color(f"  ✓ indexed {len(idx['chunks'])} chunks "
                           f"({idx['embed_model']})", green))
            return 0
        except RuntimeError as exc:
            print(ca.color(f"  ✕ {exc}", RED)); return 1
    if sub == "status":
        return cmd_status()
    if sub == "search":
        if len(rest) < 2:
            print('usage: ultra fix search "<query>"'); return 2
        return cmd_search(" ".join(rest[1:]))
    if sub == "tldr":
        if len(rest) < 2:
            print("usage: ultra fix tldr <command>"); return 2
        page = tldr_page(" ".join(rest[1:]))
        if page:
            print()
            _print_tldr(page)
            return 0
        ca, _, _ = _theme()
        print(ca.color("  (no tldr page for that command)", AMBER))
        return 1
    if sub == "solved":
        ca, blue, green = _theme()
        if len(rest) >= 3:                     # ultra fix solved "<problem>" "<fix>"
            _, indexed = record_solved(rest[1], " ".join(rest[2:]))
            print(ca.color("  ✓ solved case recorded"
                           + (" + indexed" if indexed else ""), green))
            return 0
        cases = list_solved()
        print()
        head = f"─ Solved cases · {len(cases)} recorded "
        print(ca.gradient("  ╭" + head + "─" * (66 - len(head)) + "╮",
                          blue, green))

        def brow(text, col=PAPER):
            print("  " + ca.color("│", blue) + ca.color("  " + text, col)
                  + " " * max(1, 64 - len(text)) + ca.color("│", green))

        if not cases:
            brow("none yet — record fixes so Fix-It recalls them:", MUTED)
            brow('  · inside a session:  /solved', MUTED)
            brow('  · one-shot:  ultra fix solved "<problem>" "<fix>"', MUTED)
        for c in cases[-12:]:
            brow(f"{c['title'][:42]:<42} {c['date']}")
        print(ca.gradient("  ╰" + "─" * 66 + "╯", green, blue))
        return 0
    if sub == "prompt":
        if len(rest) < 2:
            print('usage: ultra fix prompt "<problem>"'); return 2
        ca, blue, green = _theme()
        problem = " ".join(rest[1:])
        path = generate_prompt(problem, [
            {"role": "user", "content": problem}])
        ca.loadbar("  packaging escalation prompt", seconds=0.5,
                   c1=blue, c2=green)
        print(ca.color("  ✓ Claude escalation prompt ready", green))
        print(ca.color(f"    {path}", PAPER))
        return 0
    return run_session(" ".join(rest))


def _tool_session(ctx=None) -> None:
    ui.title_bar("Fix-It — guided troubleshooting")
    q = ui.prompt("describe the problem (e.g. 'ssh to 10.1.2.3 times out')").strip()
    if q:
        print()
        run_session(q)
    ui.pause()


def _tool_index(ctx=None) -> None:
    ui.title_bar("Fix-It — rebuild corpus index")
    try:
        idx = build_index()
        ui.ok(f"Indexed {len(idx['chunks'])} chunks ({idx['embed_model']}).")
    except RuntimeError as exc:
        ui.err(str(exc))
    ui.pause()


def _tool_status(ctx=None) -> None:
    ui.title_bar("Fix-It — status")
    cmd_status()
    ui.pause()


def register_tools(cat) -> None:
    """Attach Fix-It tools to an existing category (knowledge vault)."""
    cat.add("fix", "Fix-It: guided troubleshooting (offline AI)", _tool_session)
    cat.add("fix-index", "Fix-It: rebuild troubleshooting index", _tool_index)
    cat.add("fix-status", "Fix-It: corpus status", _tool_status)
