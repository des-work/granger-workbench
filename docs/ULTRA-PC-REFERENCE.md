> Legacy toolkit reference. See the repository README and SETUP.md for the supported Linux release and current feature requirements. Some platform-specific helpers are experimental.

# Ultra-PC command reference

An **offline power toolkit** for a well-equipped PC. Diagnostics, media/audio
workflows, math/science, reference utilities, a searchable offline knowledge
vault (Wikipedia + Stack Exchange + DevDocs), a local-AI RAG chat, an offline
guided troubleshooter that can run its own diagnostics, a design system (web +
native) for building non-generic frontends, a dev kit of project scaffolds and
snippets, a cheap-reading layer for large PowerPoints/PDFs/Word/Excel, an
educational diagram renderer, a portable audio/video pipeline, and an artistic
Frutiger Aero CLI splash — with local utility commands in one entry point.

```
python ultra.py         # interactive menu (or double-click ultra.bat)
ultra help              # full command reference (ultra help <topic> narrows it)
ultra fix "ssh times out"   # after install, `ultra …` works from any directory
```

Console-driven with native GUI popups for anything interactive. Windows-first
but degrades gracefully. Optional downloads and configured model providers may access the network.

---

## What's inside

### [1] PC Diagnostics & Health
System overview · Disk / SMART health · Slow-triage (8 checks + verdict) · Network diagnostics · saved to `Reports/NAME_COMPUTER_timestamp.txt` with a synthesized PASS/WARN/FAIL.

### [2] Media Tools · [3] Audio Studio
**Corruption-safe** conversion engine: source is read-only, output written to a temp file, decode-verified (streams + duration) before it's kept, existing files never overwritten. Portable ffmpeg auto-installed to `tools/ffmpeg` on first use.

- Image inspector · integrity scan · batch convert/resize · duplicate finder
- Audio/video convert (mp3/wav/flac/m4a/ogg/opus, mp4/mkv/webm/mov) with quality picker
- Extract audio · lossless remux · **trim** (fast stream-copy or precise re-encode)
- **Loudness normalize** (two-pass EBU R128, −16/−14/−23 LUFS)
- Audio Studio: voice cleanup, tape-hiss reduction, hum removal, vinyl declick, denoise, silence-split into per-track files, fade, gain/peak-normalize, LUFS/true-peak analyzer

### [4] Math & Science
Safe scientific calculator (AST parser — no `eval`) · unit converter · base converter · prime factorization · quick stats

### [5] Reference & Utilities
File hash + verify · encode/decode (base64/hex/url/rot13) · hash identifier · regex tester · password strength/entropy

### [6] Knowledge Vault — offline reference corpus
Powered by **Kiwix** (portable binaries, no admin). `.zim` archives (full sites, compressed + full-text indexed) live outside the repo. Bundled catalog covers the full English Wikipedia + Simple Wikipedia + Super User / Ask Ubuntu / Server Fault / Unix SE / Security SE / **Network Engineering SE** + **Arch Wiki** + 14 DevDocs sets (JS, TS, HTML, CSS, DOM, Python, React, Node, Git, HTTP, Tailwind, Sass, PostgreSQL, Bash).

- **`Vault status` / `Search` / `Web reader` / `Download corpora` / `Library health & coverage`** — the audit tells you which downloads are actually registered and searchable, catching the silent-dark-corpus failure mode where a partial/locked ZIM fails to register.
- **Learn — AI-guided reading list**: your **local Ollama model** proposes real Wikipedia article titles for any topic, Ultra-PC verifies each against your vault, and returns only the ones that exist as a curated learning path. Rate the results 0–5★; ratings feed back into ranking so the system improves as you use it.
- **Ask Local AI** — a themed Frutiger-Aero popup: your question → vault search (title-aware, semantic re-rank) → article text + pictures → your local model answers with sources. Uses local inference when configured accordingly.

Headless commands:
```
python ultra.py kb "how NTFS journaling works"      # offline full-text
python ultra.py kb-read "<book>" "<path>"           # clean article text
python ultra.py kb-status | kb-audit | kb-reindex   # health + coverage
python ultra.py learn "how do plants make food"     # AI reading list
```

### Fix-It — offline guided troubleshooting
A networking/sysadmin troubleshooter that pairs a curated corpus with your local AI, for the "up-to-date how-do-I-actually-fix-this" gap Wikipedia doesn't cover.

- **Corpus** (outside the repo, `C:\Ultra-PC-Knowledge\troubleshoot`): 7 decision-tree runbooks (SSH, DNS, DHCP, routing, interface/link, NAT/firewall, methodology), 3 platform quick-refs (Cisco IOS / Windows / Linux), 19 core RFCs, 6,800+ tldr command cheat-sheets, plus whole-library search into the Stack Exchange / Arch Wiki ZIMs.
- **Hybrid retrieval** — BM25 keyword **and** embedding cosine fused with Reciprocal Rank Fusion, so exact error strings (`EXSTART`, `0x80070035`, `eth0`) rank correctly. Search works keyword-only when Ollama is down.
- **Runs its own diagnostics** — the AI proposes read-only checks (`ping`, `ipconfig`, `ip addr`, `Resolve-DnsName`, …); each runs only after you confirm, and the real output is fed back into the session. A strict allowlist means a proposed command can only ever read state, never change it.
- **Self-improving** — record what fixed a problem (`/solved`) and it distils into the corpus, indexed immediately, so the same issue is answered from your own history next time.
- **Escalation prompt** — stuck? `/prompt` distils the whole session (evidence, steps tried, references) into a clean, paste-ready prompt for Claude — never with invented evidence.

```
ultra fix "ssh to 10.1.2.3 times out"     # guided session (local AI + your commands)
ultra fix search "ospf stuck exstart"     # hybrid corpus + vault retrieval
ultra fix tldr tracert                    # command cheat sheet
ultra fix solved                          # list / record solved cases
```

### [7] Design & Art Assets — the source for project aesthetics

Use the [design catalog](assets-vault/DESIGN-SYSTEM.md) before building or
restyling any interface. Choose the project's matching profile and assets;
preserve each program's own visual identity.

- **27 design profiles** define composition, typography, color, materials,
  signature shapes, motion, and explicit boundaries.
- **44 palettes, 47 SVG motifs, 17 gradients, 9 patterns, 7 SVG art pieces**,
  **12 layouts, 70 CSS techniques, 17 components, 12 animations**, and CLI art.
- **19 native tkinter/Pillow recipes** follow the same material decisions:
  matte Swiss surfaces, hard Mono edges, Aero gloss, and gold-only polish
  for Golden Archive. Native previews use the profile's local fonts.
- **16 creative-coding recipes**, **33 local font faces** (WOFF2 plus desktop
  TTF copies), and **10 pinned recipe libraries**, with licenses and a
  SHA-256 inventory in `assets-vault/dependencies.lock.json`.
- **Kit, scaffold, demo and showcase share the same style-aware CSS.**
  Starters copy fonts locally and refuse to overwrite an existing starter.
  Generated kits include keyboard focus indicators and reduced-motion rules.

```sh
python3 ultra.py assets profiles
python3 ultra.py assets profile golden-archive
python3 ultra.py assets show constellation-path
python3 ultra.py assets kit swiss-international
python3 ultra.py assets scaffold ./my-app --style dark-academia
python3 ultra.py assets native preview frutiger-aero
python3 ultra.py assets check
python3 ultra.py assets sync
```

Edit the curated source in `ultrapc/assets.py` and the native renderers in
`ultrapc/nativeui.py`, then run `assets sync` to rebuild the catalog, tokens,
profiles, exports, demo and showcase. Ordinary use stays offline. To restore
vendored assets on a new machine, explicitly run
`python3 tools/vendor_design_assets.py`; it uses pinned registry packages,
checks package integrity, keeps licenses, and never executes downloaded code.
The restore utility needs FontTools with WOFF2 support to make the TTF copies.

### Distinct style atlas

The atlas at `assets-vault/web/styles/index.html` compares **27 complete design
specimens**, including a grayscale structure check. It separates 20 visual
styles from 7 useful system/color registers. Dark Academia, Cyberpunk, High
Fashion and Nordic now have dedicated layouts and original scene SVGs; Nordic
also has a named daylight mode without changing established application colors.
Bauhaus and Art Nouveau add two researched alternatives. All historical research
and source links are saved in `assets-vault/STYLE-RESEARCH.md`, drawing on the
local Wikipedia archive plus design institutions.

Use `assets web styles` or `assets web context style/dark-academia` to select a
profile, layout and art by ID without reading full implementations. The new
`candlelit-library`, `night-city-console`, `nordic-daylight`, `workshop-modern`
and `botanical-exhibition` packs are portable; `kinetic-editorial` now uses the
fashion campaign composition.

### Modern web production vault

The web wing adds **46 complete modules**: 10 motion systems, 9 color/light
systems, 6 transparency treatments, 14 responsive compositions and 7 working
interactions. Examples include scroll-linked motion, shared-view transitions,
magnetic CTAs, 3D tilt, an original WebGL flow field, perceptual gradients,
prismatic borders, acrylic surfaces, glass docks, command menus and lightboxes.

**15 curated page packs** combine these into complete sites while respecting
the existing profiles. The local `assets-vault/web/index.html` playground shows
real pages and individual assets, with live parameter sliders, motion pause,
opaque-surface mode and compact context copying.

```sh
python3 ultra.py assets web packs
python3 ultra.py assets web search glass --style ultraviolet
python3 ultra.py assets web context luminous-product
python3 ultra.py assets web build luminous-product ./my-site
python3 ultra.py assets web build glass-command ./workspace --zip
python3 ultra.py assets web check
```

For cloud models, start with **`assets-vault/web/MODEL-INDEX.md`** and the
`context` output, then run the assembly command locally. It returns identifiers,
paths and knobs rather than implementation code. Exported sites include
`AI-BRIEF.md`, editable `design.json`, local fonts and their licenses, selected
CSS/JS, and a ready `index.html`. No CDN, bundler or model inference is needed.
Models need filesystem tools or the exported files to use this workflow; copying
the entire library source into a prompt would defeat the context saving.

Effects mount declaratively with `data-uv` and bounded `data-uv-config` values.
They provide static/opaque fallbacks, reader motion preferences, lifecycle cleanup,
and visibility-aware continuous rendering. The shader is capped at 1.5× pixel
density. Browser-specific enhancements are guarded, and content remains present
before JavaScript runs. Profiles that refuse glass, gradients or motion reject
incompatible selections. The implementation references and fallbacks are listed
in each `web/recipes/<id>.md` file.

Curated source: `ultrapc/webassets.py`; regenerate with `assets sync`.

### Image Search — find images by description or visual similarity
CLIP-based search over your local image collections. Describe what you're
looking for in plain English and it finds matching images — or give it an image
and it finds visually similar ones. Powered by the same GPU vector infrastructure
as the text search (vmath.Index on CUDA).

- **Index** a folder of images (incremental — only embeds new/changed files)
- **Text → image** search ("sunset over mountains", "network diagram", "error screenshot") — uses a CLIP prompt ensemble for sharper matches
- **Image → image** reverse search (find visually similar images)
- Opens the best match directly from the results
- **Robust by design** — indexing is crash-resumable (atomic checkpoints every 1k images), EXIF orientation is honored so phone photos embed right-side-up, truncated/corrupt files are skipped instead of failing the run, and the query is always encoded with the same model the index was built with (no dimension mismatch)
- **Configurable model** — `clip_model` in config or `--model` on index; default `clip-vit-base-patch32` (fast), or `openai/clip-vit-large-patch14` for higher quality

```
ultra img index ~/Pictures --name photos    # embed images into a "photos" collection
ultra img search "the moon"                 # just describe it — searches all collections
ultra img search photos "cat on a laptop"   # or narrow to one collection
ultra img similar ./ref.jpg                 # find images that look like this one
ultra img list                              # show indexed collections
ultra img status                            # model + backend info
```

You describe images in plain English — you never type a filename. A *collection*
is just a folder you indexed with `--name`; omit it and search runs across all of
them.

### [8] Dev Kit — code assets so I stop regenerating boilerplate
- **13 project scaffolds** — python-cli · python-package · fastapi · flask · vite-react-ts · next-app · node-express-ts · cloudflare-worker · go-api · streamlit · static-site · bash-tool · chrome-extension (MV3)
- **42 code snippets** across Python / JS / TS / SQL / Dockerfile / YAML / Make / Bash — auth, pagination, retry+backoff, debounce, fetch-with-timeout, React hooks, typed API clients, CRUD, upsert, common regexes...
- **Codebase RAG** — semantic search over your own repos using Ollama + `nomic-embed-text` (`code-index <dir>` / `code-search "<q>"`), so "reuse my existing X" finds real code

### [9] Reader / Digest — read files at a fraction of the tokens
Instead of ingesting raw PowerPoints or codebases:
- **`read <file>`** — clean text from **pptx · docx · pdf · xlsx/xlsm · csv · txt · md · rtf** (auto-detects). PDF fidelity via `pypdf`, else stdlib fallback.
- **`codemap <dir>`** — file structure + function/class signatures. Measured **~34× smaller** than raw source.
- **`digest <folder>`** — batch a mixed folder; prints a coverage report (docs read by type, code files mapped, anything skipped and why).
- **`--summarize`** — offload the summary to your local Ollama model.
- **`data <file.csv|xlsx>`** — pandas profile (schema, dtypes, nulls, stats, top categories, sample) instead of raw rows.
- **`transcribe <audio|video>`** — `faster-whisper` local transcription, tiny/base/small/medium/large-v3 models, GPU if available.

### [10] Diagrams — educational, from tiny specs
- **`diagram flow <spec>`** — Mermaid-style flowchart with a layered cycle-breaking layout (matplotlib + networkx, no Graphviz binary needed)
- **`diagram plot <code.py>`** — matplotlib figure from a small snippet
- **`diagram edu <template>`** — artistic *dark-technical-tutorial* SVG style (glowing color-coded nodes, labeled orange arrows). Templates: git-three-areas, git-branch, git-merge, pipeline, **net-topology / net-star / net-mesh / web-graph** (node-link graphs and network topology)
- **`diagram templates`** — flowchart · tree · concept-map · cycle · sequence · function-plot · bar-chart

A ~35-token spec renders a clean PNG/SVG — versus ~1.5–2.5k tokens of hand-drawn SVG.

### [11] Thumbdrive Scripts
Auto-detects `\Scripts\0_START_HERE.bat` on a USB drive, lists your scripts, and launches any one in its own console — same as running it off the stick.

---

## Architecture

```
ultra.py                 entry point (menu + CLI dispatch)
ultra.bat                Windows launcher (finds Python via py -3.11 → 311 → py)
ultrapc/
  core.py                paths, config, report engine, logging, atomic writes
  ui.py                  themed console (Frutiger Aero splash), Tk popups
  cliart.py              banners (2 fonts), gradients, boxes, spinners, loadbar
  theme.py, nativeui.py  Tk widget themes + portable native-UI depth toolkit

  diagnostics.py         [1] PC health
  media.py, mediaconv.py [2] image / video / safe conversion engine
  audiofx.py             [3] Audio Studio
  mathtools.py           [4] math & science
  reference.py           [5] hashing / encoding / regex

  knowledge.py           [6] Kiwix vault + kb search + library audit
  ai.py, ai_chat.py          local RAG chat (Ollama) + themed window
  suggest.py                 AI-guided reading list (learn command)
  ratings.py, chat_store.py  0-5★ retrieval feedback + saved chat sessions
  fixit.py                   offline guided troubleshooter (hybrid + safe cmds)
  vmath.py                   GPU/numpy vector math · rerank.py  GPU cross-encoder
  vindex.py                  GPU semantic index over document folders
  imgsearch.py               CLIP image search (text→image + image→image)

  assets.py              [7] design vault (palettes/gradients/techniques/native/kit)
  devkit.py              [8] project scaffolds + snippet vault
  coderag.py                 semantic search over your own repos
  reader.py              [9] pptx/docx/pdf/xlsx/text extraction + codemap + digest
  datatools.py               pandas profile of CSV/XLSX
  transcribe.py              faster-whisper local transcription
  diagrams.py           [10] Mermaid flow + matplotlib plot + artistic SVG generators

  scripts.py            [11] USB script launcher
  context.py            context-capsule generator · backup.py  data backup
tests/smoke.py           fast offline regression suite (`ultra selftest`)
```

### Design principles
- **Stdlib-first.** The app boots even if optional libraries are missing; tools that need them say so instead of crashing.
- **No `eval`.** The calculator parses an AST and only allows math functions.
- **Deterministic offline.** Downloads (ZIMs, models, libraries) live in external folders (`C:\Ultra-PC-Knowledge`, `C:\Ultra-PC-Assets`) — the code layer is small and portable.
- **Model-agnostic.** `ultra_config.json` lets you pin `chat_model` / `embed_model` / `num_ctx`. Retrieval degrades gracefully when a model changes or is missing.
- **Assets as data.** Palettes, gradients, techniques, snippets, scaffolds — all Python dicts written to disk by `sync()`, so the library is trivially extensible.
- **Corruption-safe file writes.** Any tool that produces a file — including the search indexes and config — writes to a temp path, fsyncs, then atomically replaces the target (`core.write_atomic`); a crash mid-write leaves the original intact.
- **Guarded by a smoke suite.** `ultra selftest` runs a fast, offline, dependency-light suite (module imports, the Fix-It command allowlist, hybrid keyword retrieval, sync round-trip, backup) so regressions are caught before they ship.

---

## Run it

```
python ultra.py                    # interactive menu
python ultra.py kb "<query>"       # offline search
python ultra.py learn "<topic>"    # AI-planned reading list
python ultra.py assets fx          # browse advanced CSS techniques
python ultra.py assets kit nordic  # generate a full themed stylesheet
python ultra.py codemap ./src      # cheap code structure map
python ultra.py read ./deck.pptx   # clean slide text
python ultra.py diagram edu net-topology -o topo.svg
python ultra.py fix "dns resolves internally but not on the vpn"
```

### `ultra` from anywhere
A one-line shim (`ultra.cmd`) in `%LOCALAPPDATA%\Microsoft\WindowsApps` — always on
PATH — lets you run `ultra …` from any directory in PowerShell or cmd, no profile
edits. It jumps to the project and delegates to `ultra.bat` (which finds Python).

### GPU acceleration (optional)
With an NVIDIA GPU + a CUDA build of PyTorch, search gets faster *and* more
accurate — all of it degrades gracefully to numpy/CPU or no-ops without it (see
`requirements-gpu.txt`).

- **Batched vector math** (`vmath.py`) — GPU torch → numpy → pure Python, auto-detected. A million-vector search runs in ~25 ms on an RTX 4080.
- **Cross-encoder reranker** (`rerank.py`) — after hybrid retrieval, a GPU cross-encoder rescores the top candidates by true query↔passage relevance (the biggest precision lever in RAG). Wired into `fix` and the KB chat; toggle with `use_reranker` in config.
- **Semantic index over your documents** (`vindex.py`) — embed a folder once, search it by meaning on the GPU; finds the right passage with zero keyword overlap.
- **CLIP image search** (`imgsearch.py`) — index a folder of images with a CLIP model, then search by text description or find visually similar images. Incremental indexing (only embeds new/changed files). Same vmath.Index GPU search underneath.
- **Stronger embeddings** — `ultra embed-model <name>` swaps in a bigger embedder (mxbai/bge/arctic) via Ollama; the 4080 runs them without breaking a sweat.

```
ultra img index ~/Pictures --name photos   # CLIP-embed images (GPU, incremental)
ultra img search photos "sunset"           # text → image
ultra img similar photos ./ref.jpg         # image → image (reverse search)
ultra img gallery                          # the Ultra Archive — space-museum photo hall
ultra img verify                           # health-check stored result links
ultra vindex build ./notes --name notes    # GPU semantic index over a folder
ultra vindex search notes "<query>"
ultra embed-model                          # show / switch the embedding model
ultra fix status                           # shows vector-math backend + reranker device
```

### Maintenance
```
python ultra.py selftest    # fast offline smoke suite (imports, safety, retrieval, sync)
python ultra.py backup      # zip the irreplaceable data -> ~/Ultra-PC-Backups
```
`backup` saves only what isn't re-downloadable or in git: your ratings, saved chats,
config, Fix-It solved cases, locally-edited runbooks, and Claude escalation prompts.

## Optional tools

The app installs / vendors these on demand — nothing required upfront:
- **ffmpeg / ffprobe** (portable, fetched to `tools/ffmpeg` on first audio/video use)
- **Kiwix** (portable, in `tools/kiwix`)
- **Ollama** (for local chat + embeddings; the vault works without it)
- **Python packages** — `pypdf`, `matplotlib`, `networkx`, `pandas`, `openpyxl`, `faster-whisper` (auto-detected; the reader/data/transcribe/diagram features light up when present)

---

## License

MIT. Personal / offline / experimental — a toolkit built for one specific
machine, but the modules are self-contained and portable.
