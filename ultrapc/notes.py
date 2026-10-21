"""Quick notes → organized tasks → your own Work Tracker app, in as few
steps as possible.

The workflow this kills: an ad-hoc assignment lands, there's only time to type
a few keywords, and the organizing / researching / tracker-entry becomes a
pile of manual steps later. Now:

    ultra note "wifi audit bldg3 friday"     # capture — instant, offline
    ultra note "..." --go                    # capture → organize → research
                                             #   → straight into the tracker
    ultra note list                          # the inbox
    ultra note organize <id|all>             # local AI: title/summary/checklist/tags
    ultra note research <id>                 # vault citations + article/video links
    ultra note push <id|all>                 # file it as a task in the tracker
    ultra note setup                         # one-time: point at the tracker folder
    ultra note show <id> · rm <id> · status

Organize runs on the LOCAL model (Ollama) and falls back to a plain heuristic
when it's offline — capture never depends on anything being up. Research adds
Knowledge-Vault citations (kiwix) plus ready-made Google/YouTube/Scholar links
so "find articles or videos" is one click from inside the tracker.

Tracker: this targets the user's own local "ga-planner" Work Tracker app —
a single HTML file whose live state is the browser's localStorage, with
tasks.json on disk as the export/seed/import artifact. `push` appends a NOTE
record to that file's `notes[]` (plus the tasks.seed.js mirror the app loads
on refresh, since file:// can't fetch()). The tracker's Notes tab is a triage
inbox: refine the wording, mark resolved/unresolved, and '➜ Make task'
promotes the real work onto the board — so quick captures never pollute the
task board or the timesheet reports until they're actually usable.
"""

from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import core

MUTED, PAPER, AMBER, RED = "#8fb8cf", "#eaf6ff", "#febc2e", "#ff6159"


def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


# --------------------------------------------------------------------------- #
#  Store — one JSON file, atomic writes, lives with the knowledge data so
#  `ultra backup` catches it
# --------------------------------------------------------------------------- #

def _store_path() -> Path:
    from . import knowledge
    return knowledge.knowledge_dir() / "notes" / "notes.json"


def _load() -> dict:
    """Read the store. A corrupt store file is MOVED ASIDE (never silently
    overwritten) so a bad write or disk hiccup can't cost every note."""
    p = _store_path()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d.get("notes"), list):
            return d
    except FileNotFoundError:
        return {"next_id": 1, "notes": []}
    except Exception:
        pass
    # exists but unreadable/misshapen: preserve the evidence
    try:
        wreck = p.with_name(f"notes.corrupt-{time.strftime('%Y%m%d-%H%M%S')}"
                            ".json")
        p.replace(wreck)
        core.log("notes", f"store unreadable — preserved as {wreck.name}",
                 "WARN")
    except OSError:
        pass
    return {"next_id": 1, "notes": []}


def _save(d: dict) -> None:
    p = _store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    core.write_atomic(p, json.dumps(d, indent=1, ensure_ascii=False))


def _lock_for(path: Path) -> Path:
    return path.parent / f"{path.name}.lock"


@contextmanager
def _locked(lock_path: Path | None = None, timeout: float = 2.0):
    """Best-effort cross-process lock around read-modify-write cycles, so two
    rapid-fire captures (or a note-store write racing a tracker-file write)
    can't lose each other. Never hangs: on timeout it proceeds (single-user
    machine; losing the lock beats losing the note)."""
    lk = lock_path if lock_path is not None else _lock_for(_store_path())
    lk.parent.mkdir(parents=True, exist_ok=True)
    fd, t0 = None, time.time()
    while fd is None:
        try:
            fd = os.open(lk, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.time() - t0 > timeout:
                core.log("notes", "store lock timeout — proceeding", "WARN")
                break
            time.sleep(0.05)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
            Path(lk).unlink(missing_ok=True)


def _get(d: dict, nid: int) -> dict | None:
    return next((n for n in d["notes"] if n["id"] == nid), None)


def _save_note(note: dict) -> None:
    """Merge ONE note back into a freshly-loaded store (replace by id). Long
    steps (AI organize, research, push) hold no lock while they run — this
    re-merge means a capture that happened meanwhile is never lost."""
    with _locked():
        d = _load()
        for i, n in enumerate(d["notes"]):
            if n["id"] == note["id"]:
                d["notes"][i] = note
                break
        else:
            d["notes"].append(note)
        _save(d)


def capture(text: str) -> dict:
    """The 2-second step: keywords in, note stored, everything else later."""
    with _locked():
        d = _load()
        note = {"id": d["next_id"], "text": text.strip(), "status": "inbox",
                "created": datetime.now().isoformat(timespec="seconds")}
        d["next_id"] += 1
        d["notes"].append(note)
        _save(d)
    return note


# --------------------------------------------------------------------------- #
#  Organize — local AI expands keywords into a real task; heuristic fallback
#  so the step works with Ollama down
# --------------------------------------------------------------------------- #

_ORGANIZE_PROMPT = """You turn a few hasty keywords into a clear task entry.
Keywords (typed in a hurry): {text}
Today: {today}

Reply with ONLY a JSON object, no prose:
{{"title": "short imperative task title",
  "summary": "1-2 sentences of what this task likely involves",
  "checklist": ["3-5 concrete steps"],
  "tags": ["1-4 lowercase tags"],
  "due_hint": "if a due date is implied, resolve it to YYYY-MM-DD using today's \
date above; else \\"\\""}}"""


def _heuristic_organize(text: str) -> dict:
    words = [w for w in re.split(r"[\s,;]+", text) if w]
    title = " ".join(words[:8]).capitalize()
    return {"title": title or "Untitled note",
            "summary": f"Captured keywords: {text}",
            "checklist": ["Clarify the ask", "Do the work",
                          "Record the result in the tracker"],
            "tags": [w.lower() for w in words[:3] if len(w) > 2][:3],
            "due_hint": ""}


def _ai_organize(text: str) -> dict | None:
    try:
        from . import ai
        if not ai.available():
            return None
        model = ai.default_model()
        if not model:
            return None
        prompt = _ORGANIZE_PROMPT.format(
            text=text, today=datetime.now().strftime("%A %Y-%m-%d"))
        out = "".join(ai.chat_stream(model, [{"role": "user",
                                              "content": prompt}]))
        m = re.search(r"\{.*\}", out, re.S)
        j = json.loads(m.group(0)) if m else {}
        if not j.get("title"):
            return None
        return {"title": str(j["title"])[:120],
                "summary": str(j.get("summary", ""))[:500],
                "checklist": [str(c)[:160] for c in
                              (j.get("checklist") or [])[:6]],
                "tags": [str(t).lower()[:24] for t in
                         (j.get("tags") or [])[:4]],
                "due_hint": str(j.get("due_hint", ""))[:40]}
    except Exception:
        return None


def organize(note: dict) -> dict:
    plan = _ai_organize(note["text"]) or _heuristic_organize(note["text"])
    note.update(plan)
    if note.get("status", "inbox") == "inbox":
        note["status"] = "organized"
    return note


# --------------------------------------------------------------------------- #
#  Research — vault citations + ready-made article/video search links
# --------------------------------------------------------------------------- #

def search_links(query: str) -> list[dict]:
    q = urllib.parse.quote_plus(query)
    return [
        {"label": "Articles (Google)",
         "url": f"https://www.google.com/search?q={q}"},
        {"label": "Videos (YouTube)",
         "url": f"https://www.youtube.com/results?search_query={q}"},
        {"label": "Papers (Scholar)",
         "url": f"https://scholar.google.com/scholar?q={q}"},
    ]


def _kb_junk(path: str) -> bool:
    """Tag-listing and pagination pages from the Stack Exchange ZIMs — real
    entries in the index, useless as research citations."""
    return bool(re.search(r"questions/tagged|_page%3D|/tag/|users/",
                          path or ""))


def _kb_title(path: str) -> str:
    """'A/Wireless_site_survey' -> 'Wireless site survey' — human title from
    a ZIM entry path."""
    seg = urllib.parse.unquote((path or "").rsplit("/", 1)[-1])
    return seg.replace("_", " ").strip() or path


def _kb_hits(query: str, limit: int = 4) -> list[dict]:
    try:
        from . import knowledge
        if not knowledge.serve_start():
            return []
        hits = knowledge.search(query, limit * 3) or []
        out = []
        for h in hits:
            if _kb_junk(h.get("path", "")):
                continue
            out.append({"title": _kb_title(h.get("path", "")),
                        "url": f"{knowledge.BASE}/content/{h['book']}/"
                               f"{h['path']}"})
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def research(note: dict) -> dict:
    query = note.get("title") or note["text"]
    note["links"] = search_links(query)
    note["kb"] = _kb_hits(query)
    return note


# --------------------------------------------------------------------------- #
#  Due-date hints -> the ISO date the tracker's <input type="date"> expects.
#  Deliberately conservative: an unparsable hint returns None (left blank)
#  rather than guess — a wrong date silently entered into a real tracker is
#  worse than a missing one.
# --------------------------------------------------------------------------- #

_WEEKDAYS = {"monday": 0, "mon": 0, "tuesday": 1, "tue": 1, "tues": 1,
            "wednesday": 2, "wed": 2, "thursday": 3, "thu": 3, "thurs": 3,
            "friday": 4, "fri": 4, "saturday": 5, "sat": 5,
            "sunday": 6, "sun": 6}

_MONTHS = {m: i for i, ms in enumerate(
    [("january", "jan"), ("february", "feb"), ("march", "mar"),
     ("april", "apr"), ("may",), ("june", "jun"), ("july", "jul"),
     ("august", "aug"), ("september", "sep", "sept"), ("october", "oct"),
     ("november", "nov"), ("december", "dec")], start=1) for m in ms}


def parse_due_hint(hint: str, today: datetime | None = None) -> str | None:
    if not hint:
        return None
    h = hint.strip().lower()
    today = today or datetime.now()
    if h == "today":
        return today.strftime("%Y-%m-%d")
    if h in ("tomorrow", "tmrw"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if re.match(r"^\d{4}-\d{2}-\d{2}$", h):
        return h
    m = re.match(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$", h)
    if m:
        mo, da, yr = m.groups()
        yr = int(yr) if yr else today.year
        if yr < 100:
            yr += 2000
        try:
            return datetime(yr, int(mo), int(da)).strftime("%Y-%m-%d")
        except ValueError:
            return None
    # prose the local model actually emits: "Friday, July 25, 2026" /
    # "July 25" / "25 July" — resolve the month name, infer a sensible year
    mp = re.search(r"(?:^|,\s*)([a-z]+)\s+(\d{1,2})(?:,?\s*(\d{4}))?$", h)
    if not mp:
        mp = re.search(r"(\d{1,2})\s+([a-z]+)(?:,?\s*(\d{4}))?$", h)
        if mp:
            da, mon, yr = mp.groups()
        else:
            mon = None
    else:
        mon, da, yr = mp.groups()
    if mp and mon in _MONTHS:
        try:
            year = int(yr) if yr else today.year
            cand = datetime(year, _MONTHS[mon], int(da))
            if not yr and cand.date() < today.date():   # bare "July 25" past?
                cand = cand.replace(year=year + 1)
            return cand.strftime("%Y-%m-%d")
        except ValueError:
            return None
    force_next = h.startswith("next ")
    word = (h[5:] if force_next else h).strip()
    if word not in _WEEKDAYS:
        return None
    delta = (_WEEKDAYS[word] - today.weekday()) % 7
    if force_next and delta == 0:
        delta = 7
    return (today + timedelta(days=delta)).strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
#  The tracker — a local single-file app (ga-planner / Work_Tracker.html)
#  whose live state is the browser's localStorage; tasks.json on disk is its
#  export/import artifact. `push` merges a new task into that file — it never
#  touches localStorage, because nothing outside the browser tab can.
# --------------------------------------------------------------------------- #

def _iso_now() -> str:
    """Match JS `new Date().toISOString()`: milliseconds + trailing Z, UTC."""
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _task_id() -> str:
    return f"t-{int(time.time() * 1000):x}{random.randrange(46656):03x}"


def _guess_tracker_dir() -> str:
    for cand in (core.ROOT.parent / "ga-planner",
                Path.home() / "AI Programs" / "ga-planner"):
        if (cand / "tasks.json").exists():
            return str(cand)
    return ""


def tracker_dir() -> Path | None:
    d = core.load_config().get("tracker_dir", "")
    return Path(d) if d else None


def build_note_record(note: dict) -> dict:
    """Pure: a captured note -> the record the tracker's Notes inbox shows
    (testable offline). Notes are RAW MATERIAL: the tracker lets you refine
    the wording, then promote the real work into a task — which is why this
    keeps the organized parts as separate fields instead of flattening them
    into a task's free-text notes blob."""
    ts = _iso_now()
    return {"id": "n-" + _task_id()[2:],
            "text": note.get("text", ""),
            "title": (note.get("title") or note.get("text", ""))[:200],
            "summary": note.get("summary", ""),
            "checklist": list(note.get("checklist", [])),
            "tags": list(note.get("tags", [])),
            "links": list(note.get("links", [])),
            "kb": list(note.get("kb", [])),
            "due": parse_due_hint(note.get("due_hint", "")),
            "status": "open",          # open | resolved (set in the GUI)
            "taskId": None,            # set when promoted to a task
            "capturedAt": note.get("created", ""),
            "createdAt": ts, "updatedAt": ts}


def _write_seed(t_dir: Path, data: dict) -> None:
    """Mirror tasks.json into tasks.seed.js beside it — a <script>-loadable
    'mailbox' the tracker reads on load. This is what makes push → refresh →
    done work: the app can't fetch() a local file from file:// (browsers
    block it), but it CAN load a sibling <script src>. The app merges only
    task ids it hasn't seen, so re-writing the whole mirror is safe."""
    seed = t_dir / "tasks.seed.js"
    core.write_atomic(seed, "window.__ULTRA_SEED__ = "
                      + json.dumps(data, indent=2) + ";\n")


class AlreadyPushed(RuntimeError):
    """Raised instead of silently filing a duplicate tracker task."""


def push(note: dict, force: bool = False) -> dict:
    if note.get("tracker_id") and not force:
        raise AlreadyPushed(f"already in the tracker (task "
                            f"{note['tracker_id']}) — use `push <id> "
                            "--again` to file a fresh copy")
    t_dir = tracker_dir()
    if not t_dir:
        raise RuntimeError("tracker not configured — run `ultra note setup`")
    tasks_path = t_dir / "tasks.json"
    if not tasks_path.exists():
        raise RuntimeError(f"tasks.json not found at {tasks_path} — check "
                           "`ultra note setup`")
    if not note.get("title"):
        organize(note)
    entry = build_note_record(note)
    with _locked(_lock_for(tasks_path)):
        try:
            data = json.loads(tasks_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"couldn't read {tasks_path} — refusing to "
                               f"touch your tracker file ({exc})") from None
        if not isinstance(data.get("tasks"), list):
            raise RuntimeError(f"{tasks_path} doesn't look like a tasks "
                               "file — refusing to touch it")
        data.setdefault("notes", [])
        if not isinstance(data["notes"], list):
            raise RuntimeError(f"{tasks_path} has a non-list 'notes' key — "
                               "refusing to touch it")
        data["notes"].append(entry)
        data["updated"] = _iso_now()
        core.write_atomic(tasks_path, json.dumps(data, indent=2))
        _write_seed(t_dir, data)
    note["status"] = "pushed"
    note["tracker_id"] = entry["id"]
    note["tracker_path"] = str(tasks_path)
    note["pushed_at"] = datetime.now().isoformat(timespec="seconds")
    return note


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

_SUBCOMMANDS = {"list", "ls", "show", "organize", "research", "push",
                "setup", "status", "rm", "delete", "help"}


def _route(rest: list[str]) -> str:
    """'capture' or the subcommand name. Guards the sacred path: keywords
    that merely START with a subcommand word ('list bugs friday') must still
    capture — a note wrongly routed to a listing is a lost thought."""
    if not rest:
        return "list"
    first = rest[0].lower()
    if first not in _SUBCOMMANDS:
        return "capture"
    args = [a for a in rest[1:] if not a.startswith("--")]
    if first in ("list", "ls"):
        return first if not args else "capture"
    if first in ("setup", "status", "help"):
        return first if not args else "capture"
    if first in ("show", "rm", "delete", "organize", "research", "push"):
        if not args:                      # bare `note push` -> usage message
            return first
        ok = args[0].lower() == "all" or args[0].isdigit()
        return first if ok else "capture"
    return first


def _parse_id(s: str) -> int | None:
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def _print_note(ca, green, n: dict, full: bool = False) -> None:
    mark = {"inbox": "○", "organized": "◐", "pushed": "●"}.get(
        n["status"], "?")
    line = f"  {mark} #{n['id']:<3} {n.get('title') or n['text']}"
    print(ca.color(line[:78], PAPER))
    if full:
        print(ca.color(f"      captured {n['created']} · {n['status']}"
                       + (f" · task {n['tracker_id']}" if n.get("tracker_id")
                          else ""), MUTED))
        if n.get("summary"):
            print(ca.color(f"      {n['summary']}", MUTED))
        for c in n.get("checklist", []):
            print(ca.color(f"        ☐ {c}", PAPER))
        if n.get("tags"):
            print(ca.color("      tags: " + ", ".join(n["tags"]), MUTED))
        for l in n.get("links", []) + n.get("kb", []):
            print(ca.color(f"      ↗ {l.get('label') or l.get('title')}"
                           f" — {l['url'][:60]}", MUTED))


def _ids_arg(d: dict, arg: str) -> list[dict]:
    if arg == "all":
        return [n for n in d["notes"] if n["status"] != "pushed"]
    nid = _parse_id(arg)
    n = _get(d, nid) if nid is not None else None
    return [n] if n else []


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() not in ("note", "notes"):
        return None
    ca, blue, green = _theme()
    rest = argv[1:]
    sub = _route(rest)

    if sub == "capture":
        go = "--go" in rest
        text = " ".join(a for a in rest if a != "--go").strip()
        if not text:
            print('usage: ultra note "<keywords>" [--go]'); return 2
        n = capture(text)
        print(ca.color(f"  ✓ captured #{n['id']} — {text}", green))
        if not go:
            print(ca.color("    later: ultra note organize "
                           f"{n['id']} · research {n['id']} · push "
                           f"{n['id']}   (or --go to do it all now)", MUTED))
            return 0
        print(ca.color("  ▸ organizing (local AI)…", MUTED))
        organize(n)
        _save_note(n)                       # progress survives a later crash
        print(ca.color("  ▸ researching (vault + links)…", MUTED))
        research(n)
        _save_note(n)
        try:
            print(ca.color("  ▸ filing it in the tracker…", MUTED))
            push(n)
            print(ca.color("  ✓ sent — refresh the Work Tracker and open the "
                           "Notes tab to refine it", green))
        except RuntimeError as exc:
            print(ca.color(f"  ⚠ {exc}", AMBER))
            print(ca.color(f"    the note is safe locally — `ultra note "
                           f"push {n['id']}` once the tracker is set up",
                           MUTED))
        _save_note(n)
        _print_note(ca, green, n, full=True)
        return 0

    args = rest[1:]

    if sub in ("list", "ls"):
        d = _load()
        notes = d["notes"] if "--all" in args else \
            [n for n in d["notes"] if n["status"] != "pushed"]
        print()
        print(ca.color("  ▸ notes — ○ inbox · ◐ organized · ● pushed", green))
        if not notes:
            print(ca.color("    (empty — `ultra note \"a few keywords\"` "
                           "to capture)", MUTED))
        for n in notes:
            _print_note(ca, green, n)
        return 0

    if sub == "show" and args:
        d = _load()
        nid = _parse_id(args[0])
        n = _get(d, nid) if nid is not None else None
        if not n:
            print(ca.color(f"  no note #{args[0]}", RED)); return 1
        print()
        _print_note(ca, green, n, full=True)
        return 0

    if sub in ("rm", "delete") and args:
        with _locked():
            d = _load()
            nid = _parse_id(args[0])
            n = _get(d, nid) if nid is not None else None
            if not n:
                print(ca.color(f"  no note #{args[0]}", RED)); return 1
            d["notes"].remove(n)
            _save(d)
        print(ca.color(f"  ✓ removed #{args[0]}", green))
        return 0

    if sub in ("organize", "research", "push") and args:
        again = "--again" in rest
        args = [a for a in args if not a.startswith("--")]  # flags aside
        d = _load()
        targets = _ids_arg(d, args[0])
        if not targets:
            print(ca.color(f"  no note matching '{args[0]}'", RED)); return 1
        rc = 0
        for n in targets:
            try:
                if sub == "organize":
                    organize(n)
                elif sub == "research":
                    if not n.get("title"):
                        organize(n)
                    research(n)
                else:
                    if not n.get("links"):
                        research(organize(n) if not n.get("title") else n)
                    push(n, force=again)
                _print_note(ca, green, n, full=True)
            except AlreadyPushed as exc:
                print(ca.color(f"  · #{n['id']}: {exc}", MUTED))
            except (RuntimeError, ValueError) as exc:
                print(ca.color(f"  ✕ #{n['id']}: {exc}", RED))
                rc = 1
            _save_note(n)                 # per-note merge: no lost updates
        return rc

    if sub == "setup":
        cfg = core.load_config()
        print()
        print(ca.color("  ▸ Work Tracker setup — one time", green))
        guess = _guess_tracker_dir()
        prompt = f"  tracker folder [{guess}]: " if guess else \
            "  tracker folder (the one with tasks.json): "
        raw = input(prompt).strip()
        t_dir = Path(raw or guess) if (raw or guess) else None
        if not t_dir or not (t_dir / "tasks.json").exists():
            print(ca.color(f"  ✕ no tasks.json found in "
                           f"{t_dir or '(nothing entered)'}", RED))
            return 1
        try:
            data = json.loads((t_dir / "tasks.json").read_text(
                encoding="utf-8"))
            n_tasks = len(data.get("tasks", []))
        except Exception as exc:
            print(ca.color(f"  ✕ couldn't parse tasks.json: {exc}", RED))
            return 1
        cfg["tracker_dir"] = str(t_dir)
        core.save_config(cfg)
        print(ca.color(f"  ✓ connected — {n_tasks} existing task(s) found "
                       f"in {t_dir}", green))
        print(ca.color("    pushed notes land in the tracker's Notes tab; "
                       "refine them there, then '➜ Make task' promotes the "
                       "real work onto the board.", MUTED))
        return 0

    if sub == "status":
        d = _load()
        by = {}
        for n in d["notes"]:
            by[n["status"]] = by.get(n["status"], 0) + 1
        print()
        print(ca.color(f"  notes: {by or 'none yet'} · store: "
                       f"{_store_path()}", PAPER))
        t_dir = tracker_dir()
        if t_dir and (t_dir / "tasks.json").exists():
            try:
                n_tasks = len(json.loads((t_dir / "tasks.json").read_text(
                    encoding="utf-8")).get("tasks", []))
                print(ca.color(f"  tracker: {t_dir}  ({n_tasks} tasks)",
                               PAPER))
            except Exception:
                print(ca.color(f"  tracker: {t_dir}  (tasks.json unreadable"
                               ")", AMBER))
        else:
            print(ca.color("  tracker: not set up — ultra note setup",
                           PAPER))
        return 0

    print('usage: ultra note "<keywords>" [--go] · list [--all] · show <id> '
          '· organize <id|all> · research <id> · push <id|all> · setup · '
          'status · rm <id>')
    return 0
