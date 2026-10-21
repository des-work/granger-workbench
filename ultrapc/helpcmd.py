"""`ultra help` — a themed, self-documenting command reference.

The toolkit has grown a lot of subcommands across many modules; this is the one
place that lists them all.  `ultra help` prints everything grouped by area;
`ultra help <topic>` (e.g. `ultra help img`, `ultra help fix`) narrows to one
section with a little extra detail.

Kept as data (the SECTIONS table) so it's trivial to keep in sync — add a row
when you add a command.  Rendered in the same Frutiger-Aero blue→green style as
the rest of the CLI.
"""

from __future__ import annotations

from . import core

CYAN = "#4fc3f7"
PAPER = "#eaf6ff"
MUTED = "#8fb8cf"
WHITE = "#ffffff"

# Each section: (key, title, blurb, [(command, description), ...], detail-lines)
# `key` is what `ultra help <key>` matches (plus the first word of any command).
SECTIONS = [
    ("knowledge", "Knowledge Vault", "Offline reference: Wikipedia + Stack Exchange + DevDocs, searched locally.", [
        ('kb "<query>"',                 "full-text search across the offline vault"),
        ('kb-read "<book>" "<path>"',    "print clean article text from a book"),
        ('kb-status',                    "server + corpus status"),
        ('kb-audit',                     "coverage report — what's registered & searchable"),
        ('kb-reindex',                   "rebuild the library index, restart the server"),
        ('learn "<topic>"',              "AI-planned reading list, verified against your vault"),
        ('ai   (or: chat)',              "open the local-AI RAG chat window"),
    ], [
        "The vault runs on Kiwix (portable, no admin). ZIM archives live in",
        "C:\\Ultra-PC-Knowledge and work fully offline. `ai` needs Ollama running.",
    ]),

    ("fix", "Fix-It — guided troubleshooting", "Networking/sysadmin troubleshooter: curated corpus + your local AI + safe diagnostics.", [
        ('fix "<problem>"',              "guided session (AI proposes read-only checks you confirm)"),
        ('fix search "<q>"',             "hybrid corpus retrieval (BM25 + embeddings + rerank)"),
        ('fix tldr <command>',           "command cheat sheet"),
        ('fix solved',                   "list / record solved cases (self-improving corpus)"),
        ('fix status',                   "retrieval backend + reranker device"),
    ], [
        "Proposed commands can only ever READ state — a strict allowlist blocks",
        "anything that could change the system. `/solved` teaches it your fixes.",
    ]),

    ("img", "Image & Semantic Search (GPU)", "Find images by describing them — no filenames needed. Plus semantic document search.", [
        ('img index <folder> --name <collection>', "CLIP-embed a folder into a named collection"),
        ('img search "<description>"',             'just describe it — "the moon", "map of italy"'),
        ('img search <collection> "<desc>"',       "same, but limited to one collection"),
        ('img similar <image>',                    "find images that look like this one"),
        ('img gallery [collection]',               "the Ultra Archive — endless curated Wikipedia museum"),
        ('img topics [add|remove|block] "<t>"',    "curate what hangs (semantic — no re-indexing)"),
        ('img verify [collection]',                "health-check result links; auto-repairs ZIM URLs"),
        ('img list   /   img status',              "collections / model + backend info"),
        ('vindex build <folder> --name N',         "semantic index over a document folder"),
        ('vindex search <name> "<query>"',         "meaning-based search (zero keyword overlap OK)"),
        ('embed-model [name]',                     "show / switch the text embedding model"),
    ], [
        "A 'collection' is just a folder you indexed with `img index --name`.",
        "You describe what you want in plain English — you never type a filename.",
        "Omit the collection and search runs across ALL of them, so you can just",
        "describe the image (e.g. `ultra img search \"star photos\"`).",
        "",
        "Runs on the RTX 4080 via vmath. Default CLIP is ViT-B/32; use",
        "--model openai/clip-vit-large-patch14 on index for higher quality.",
    ]),

    ("assets", "Design & Art Assets", "An offline design system so UIs look polished by default (web + native).", [
        ('assets web packs|list|search', "46 modern web modules + 15 complete page packs"),
        ('assets web styles', "27 distinct specimens; visual styles vs color registers"),
        ('assets web context <id>', "compact IDs, paths and knobs for cloud models"),
        ('assets web build <pack> <dir>', "assemble a portable site from local assets"),
        ('assets web gallery', "interactive motion, color, glass and layout playground"),
        ('assets demo',                  "open the LIVE demo — everything visual on one page"),
        ('assets profiles [id]',         "27 design-profile briefs (20-section archetype specs)"),
        ('assets profile <id>',          "one full brief: origins, color logic, moves, canon…"),
        ('assets shapes [query]',        "47 signature SVG motifs (sunburst, squiggle, crest…)"),
        ('assets palettes|gradients|patterns', "44 palettes · 17 gradients · 9 patterns"),
        ('assets css|anim|fx|layouts|creative', "snippets, animations, 70 techniques, layouts, creative-coding"),
        ('assets native [preview <style>]', "tkinter/PIL kit: glass, gel, neon, 10 textures, widgets"),
        ('assets kit <style>',           "generate a full themed stylesheet in one shot"),
        ('assets scaffold <dir> --style S', "drop a good-looking starter project"),
        ('assets show <id>',             "print any asset by id, paste-ready"),
        ('assets showcase',              "profile examples built from checked theme kits"),
    ], [
        "27 styles — originals (frutiger-aero, vaporwave, cyberpunk, pastel, earthy,",
        "editorial, mono, jewel, nordic, neutral), the complement wing (golden-archive,",
        "ultraviolet, ember, hi-contrast) and the archetype tokens (avant-basic,",
        "organic-tech, high-fashion, skate-culture, mosaic, art-deco, frutiger-metro,",
        "preppy-2000s, y2k-chrome, dark-academia, swiss-international, bauhaus, art-nouveau).",
        "",
        "When a brief names a vibe, START at `assets profiles` — each is a full",
        "design brief (composition, proportion, color logic, light, type, voice,",
        "kinship, signature moves) plus its component collection. The demo page is",
        "regenerated from the vault data on every sync, so it's never stale.",
        "Native code gets WCAG tools too: nui.contrast / on_color / ensure_contrast.",
        "Catalog: C:\\Ultra-PC-Assets\\DESIGN-SYSTEM.md",
    ]),

    ("dev", "Dev Kit", "Scaffolds, snippets, and semantic search over your own code — stop regenerating boilerplate.", [
        ('stacks list',                  "list project scaffolds"),
        ('stacks new <id> <dir>',        "e.g. python-cli, fastapi, vite-react-ts, static-site"),
        ('snip [query]',                 "reusable code snippets (auth, retry, pagination, ...)"),
        ('prime "<task>"',               "★ session primer — bundle everything to start a task hot (~3-6K tokens)"),
        ('code-index <dir>',             "build a semantic index over a repo"),
        ('code-search "<query>"',        "find your own code by meaning"),
        ('guide new "<Title>"',          "scaffold a Workipedia-style field guide/module"),
        ('guide new "<T>" --style <p> --outline f', "themed by any design profile; chapters from an outline"),
        ('guide styles',                 "list the 13 profile themes for modules"),
    ], [
        "`ultra prime \"<task>\"` is the token-saver: it composes the project",
        "capsule + semantic code-search (where's the work?) + file signatures",
        "+ matching snippets + recent git into one paste-ready bundle, so an AI",
        "session starts oriented at ~3-6K tokens instead of ~25K exploring cold.",
        "Run `ultra code-index <dir>` once per repo to unlock the code section.",
        "",
        "`guide new` builds a self-contained offline HTML module with the nav/",
        "search/progress machinery pre-built and chapters stubbed — same",
        "<h2 id=\"chN\"> contract the Workipedia Reference Desk indexes.",
    ]),

    ("ingest", "Media & Asset Ingest", "One clean intake for camera dumps, textures, models — no more random folders.", [
        ('ingest run <source>',          "classify + rename + dedup + file into the library (copy)"),
        ('ingest run <src> --move',      "verified move — source deleted only after hash check"),
        ('ingest run <src> --dry',       "show the filing plan, touch nothing"),
        ('ingest run <src> --project N', "file under Projects/<N>/ instead"),
        ('ingest run <src> --index',     "then CLIP-index photos (search them by description)"),
        ('ingest status',                "library overview + dedup index size"),
        ('ingest root [path]',           "show / set the library root (default C:\\Ultra-Media)"),
    ], [
        "Categories: camera photos/RAW (EXIF date folders), screenshots, video",
        "(ffprobe'd), audio, textures (PBR sets auto-grouped by suffix), HDRIs,",
        "3D models by format, .blend, Unreal assets, archives — unknowns land in",
        "_Unsorted, never lost. Every run writes a manifest to _ingest/logs.",
    ]),

    ("notes", "Notes → Tracker", "Keywords in seconds now; organized, researched, and filed into your Work Tracker later — or instantly.", [
        ('note "<keywords>"',            "capture in 2 seconds (offline, nothing else needed)"),
        ('note "<keywords>" --go',       "capture → AI-organize → research → filed as a task, one step"),
        ('note list [--all]',            "the inbox (○ inbox · ◐ organized · ● pushed)"),
        ('note organize <id|all>',       "local AI: title, summary, checklist, tags, due hint"),
        ('note research <id>',           "vault citations + article/video search links"),
        ('note push <id|all>',           "file it into tasks.json (auto-organizes first)"),
        ('note push <id> --again',       "file a fresh copy even if already pushed"),
        ('note setup',                   "one-time: point at your tracker's folder"),
        ('note show|rm <id> · status',   "inspect · remove · store/tracker overview"),
    ], [
        "Capture never depends on Ollama or the network — organize falls back to",
        "a plain heuristic offline. Research adds Knowledge-Vault citations plus",
        "ready-made Google/YouTube/Scholar links so finding articles or videos is",
        "one click from inside the tracker. Notes live in the knowledge dir, so",
        "`ultra backup` includes them.",
        "",
        "Targets the local Work Tracker app (ga-planner): push merges a new task",
        "into its tasks.json on disk — that app's live state is browser",
        "localStorage, so open the tracker and click 'Import tasks.json' to pull",
        "pushed notes in. If the tab has unsaved edits, Export there FIRST or",
        "Import will replace them with the file.",
    ]),

    ("read", "Reader · Data · Diagrams", "Read big files cheaply, profile data, and render diagrams from tiny specs.", [
        ('read <file>',                  "clean text from pptx/docx/pdf/xlsx/csv/txt/md"),
        ('codemap <file|dir>',           "code structure: files + signatures (~34× smaller)"),
        ('digest <folder>',              "batch a folder into one digest + coverage report"),
        ('data <file.csv|xlsx>',         "dataset profile (schema, stats) instead of raw rows"),
        ('transcribe <audio|video>',     "local speech-to-text (faster-whisper)"),
        ('diagram <flow|plot|edu|templates>', "render educational diagrams/flowcharts"),
        ('context "<task>" --out context.md', "generate a token-cheap project capsule"),
    ], []),

    ("maintenance", "Maintenance", "Keep the toolkit healthy.", [
        ('selftest',                     "fast offline smoke suite (run before commits)"),
        ('backup',                       "zip irreplaceable data → ~/Ultra-PC-Backups"),
        ('chats list|show|search',       "browse saved AI chat sessions"),
    ], []),
]

_ALIASES = {"kb": "knowledge", "learn": "knowledge", "ai": "knowledge",
            "chat": "knowledge", "search": "knowledge",
            "image": "img", "imgsearch": "img", "vindex": "img",
            "embed-model": "img", "gpu": "img", "gallery": "img",
            "archive": "img", "museum": "img",
            "design": "assets", "css": "assets", "demo": "assets",
            "profiles": "assets", "profile": "assets", "shapes": "assets",
            "styles": "assets", "native": "assets", "palettes": "assets",
            "stacks": "dev", "snip": "dev", "code-search": "dev",
            "guide": "dev", "module": "dev", "workipedia": "dev",
            "prime": "dev", "primer": "dev", "session": "dev",
            "codemap": "read", "digest": "read", "data": "read",
            "transcribe": "read", "diagram": "read", "context": "read",
            "intake": "ingest", "import": "ingest", "media": "ingest",
            "note": "notes", "tracker": "notes", "todo": "notes",
            "backup": "maintenance", "selftest": "maintenance",
            "chats": "maintenance"}


def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


def _print_header(ca, blue, green) -> None:
    from . import __version__
    print()
    print(ca.gradient("  ╭─ ULTRA-PC · command reference " + "─" * 33 + "╮",
                      blue, green))
    tag = f"  offline power toolkit · v{__version__}"
    print("  " + ca.color("│", blue) + ca.color(tag, PAPER)
          + " " * max(1, 64 - len(tag)) + ca.color("│", green))
    hint = "  run  ultra <command>  ·  ultra help <topic> narrows this"
    print("  " + ca.color("│", blue) + ca.color(hint, MUTED)
          + " " * max(1, 64 - len(hint)) + ca.color("│", green))
    print(ca.gradient("  ╰" + "─" * 66 + "╯", green, blue))


def _print_section(ca, blue, green, section, detail: bool = False) -> None:
    _key, title, blurb, rows, detail_lines = section
    labels = [f"ultra {cmd}" for cmd, _ in rows]
    w = max((len(x) for x in labels), default=0)
    print()
    print(ca.gradient(f"  ┏━ {title} ", blue, green)
          + ca.color("━" * max(2, 62 - len(title)), green))
    if blurb:
        print("  " + ca.color(blurb, MUTED))
    print()
    for (cmd, desc), label in zip(rows, labels):
        print("   " + ca.color(label.ljust(w), CYAN)
              + "   " + ca.color(desc, PAPER))
    if detail and detail_lines:
        print()
        for ln in detail_lines:
            print("   " + ca.color(ln, MUTED))


def _find(topic: str):
    topic = topic.lower().lstrip("-")
    if topic in _ALIASES:
        topic = _ALIASES[topic]
    for sec in SECTIONS:
        if sec[0] == topic:
            return sec
    # fall back: match the first word of any command in a section
    for sec in SECTIONS:
        for cmd, _ in sec[3]:
            if cmd.split()[0].strip('"').lower() == topic:
                return sec
    return None


def show(topic: str | None = None) -> int:
    ca, blue, green = _theme()
    if topic:
        sec = _find(topic)
        if sec is None:
            print(ca.color(f"  no help topic '{topic}'. "
                           "try: ultra help", MUTED))
            _print_header(ca, blue, green)
            for sec in SECTIONS:
                print("   " + ca.color(f"ultra help {sec[0]:<12}", CYAN)
                      + ca.color(sec[1], PAPER))
            return 0
        _print_header(ca, blue, green)
        _print_section(ca, blue, green, sec, detail=True)
        print()
        return 0

    _print_header(ca, blue, green)
    for sec in SECTIONS:
        _print_section(ca, blue, green, sec, detail=False)
    print()
    print("   " + ca.color("no args → interactive menu   ·   "
                           "ultra help <topic> for detail", MUTED))
    print()
    return 0


def handle(argv: list[str]) -> int | None:
    if not argv:
        return None
    cmd = argv[0].lower()
    if cmd not in ("help", "--help", "-h", "commands", "?"):
        return None
    topic = argv[1] if len(argv) > 1 else None
    return show(topic)
