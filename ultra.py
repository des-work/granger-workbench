#!/usr/bin/env python3
"""Ultra-PC — offline power toolkit.

Launch:  python ultra.py     (or double-click ultra.bat)

A console-driven toolkit with GUI popups: PC diagnostics, media tools,
math/science calculators, reference utilities, and a launcher for your
portable thumbdrive .bat kit.
"""

from __future__ import annotations

import sys
import traceback

from ultrapc import (core, ui, diagnostics, media, mathtools, reference,
                     scripts, knowledge, audiofx, assets, devkit, reader,
                     diagrams, imgsearch)
from ultrapc import __version__


def build_categories() -> list[core.Category]:
    return [
        diagnostics.register(),
        media.register(),
        audiofx.register(),
        mathtools.register(),
        reference.register(),
        knowledge.register(),
        imgsearch.register(),
        assets.register(),
        devkit.register(),
        reader.register(),
        diagrams.register(),
        scripts.register(),
    ]


def run_category(cat: core.Category) -> None:
    # A single-tool category (e.g. the script launcher) runs straight through.
    if len(cat.tools) == 1:
        _run_tool(cat.tools[0])
        return
    while True:
        items = [(str(i + 1), t.label) for i, t in enumerate(cat.tools)]
        choice = ui.menu(cat.label, "choose a tool", items, "Back to main menu")
        if choice == "0" or not choice:
            return
        if choice.isdigit() and 1 <= int(choice) <= len(cat.tools):
            _run_tool(cat.tools[int(choice) - 1])


def _run_tool(tool: core.Tool) -> None:
    try:
        tool.func(None)
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        core.log(tool.key, f"crashed: {exc}", "ERROR")
        ui.err(f"Tool error: {exc}")
        ui.dim(traceback.format_exc().splitlines()[-1])
        ui.pause()


def handle_cli(argv: list[str]) -> int | None:
    """Headless subcommands (used by the assistant / scripts). Returns an exit
    code if a subcommand handled the args, else None to fall through to the menu."""
    if not argv:
        return None
    cmd = argv[0].lower()
    if cmd in ("help", "--help", "-h", "commands", "?"):
        from ultrapc import helpcmd
        return helpcmd.handle(argv)
    if cmd in ("kb", "search"):
        if len(argv) < 2:
            print('usage: python ultra.py kb "<query>"'); return 2
        # `kb tune ...` / `kb rate <n>` are management subcommands, not
        # queries — but only when their argument shape is unambiguous, so
        # a genuine search like `kb rate limiting` still searches
        if argv[1] == "tune" and (len(argv) == 2 or argv[2] in
                                  ("list", "add", "rm", "test")):
            return knowledge.cmd_tune(argv[2:])
        if argv[1] == "rate" and len(argv) == 3 and argv[2].isdigit():
            return knowledge.cmd_rate(int(argv[2]))
        return knowledge.kb_search(" ".join(argv[1:]))
    if cmd in ("kb-read", "read"):
        # "read" is shared with the document reader (reader.handle below).
        # If the first arg is an existing file, this is a document read —
        # fall through so `ultra read <file.pptx> --outline` works.
        import pathlib
        is_doc = (cmd == "read" and len(argv) > 1
                  and pathlib.Path(argv[1]).expanduser().exists())
        if not is_doc:
            if len(argv) < 3:
                print('usage: python ultra.py kb-read "<book>" "<path>"'); return 2
            return knowledge.kb_read(argv[1], argv[2])
    if cmd in ("kb-status",):
        for ln in knowledge._status_lines():
            print(ln)
        return 0
    if cmd in ("kb-audit", "kb-coverage"):
        return knowledge.kb_audit()
    if cmd in ("learn", "suggest"):
        from ultrapc import suggest as ai_suggest
        return ai_suggest.cmd_learn(" ".join(argv[1:]))
    if cmd in ("kb-reindex",):
        n = knowledge.rebuild_library()
        knowledge.serve_stop()
        knowledge.serve_start()
        added, failed = knowledge.last_reindex_report()
        print(f"reindexed {n} book(s); server restarted")
        if failed:
            print(f"  skipped {len(failed)} (not registered / not searchable):")
            for fn, why in failed:
                print(f"    - {fn}: {why}")
        return 0
    if cmd in ("ai", "chat", "ask"):
        from ultrapc import ai_chat
        ai_chat.open_chat_window()
        return 0
    if cmd == "assets":
        return assets.handle(argv[1:])
    if cmd == "fix":
        from ultrapc import fixit
        return fixit.handle(argv)
    if cmd == "backup":
        from ultrapc import backup
        return backup.handle(argv)
    if cmd == "vindex":
        from ultrapc import vindex
        return vindex.handle(argv)
    if cmd in ("img", "imgsearch", "image"):
        from ultrapc import imgsearch
        return imgsearch.handle(argv)
    if cmd in ("embed-model", "embed_model"):
        from ultrapc import ai as _ai
        return _ai.cmd_embed_model(" ".join(argv[1:]))
    if cmd in ("selftest", "smoke"):
        import subprocess
        return subprocess.call([sys.executable,
                                str(core.ROOT / "tests" / "smoke.py")])
    dk = devkit.handle(argv)
    if dk is not None:
        return dk
    from ultrapc import coderag
    cr = coderag.handle(argv)
    if cr is not None:
        return cr
    rd = reader.handle(argv)
    if rd is not None:
        return rd
    dg = diagrams.handle(argv)
    if dg is not None:
        return dg
    from ultrapc import (datatools, transcribe, context, chat_store, guidegen,
                         ingest, prime, notes)
    for mod in (datatools, transcribe, context, chat_store, guidegen, ingest,
                prime, notes):
        r = mod.handle(argv)
        if r is not None:
            return r
    return None


def main() -> int:
    core.ensure_dirs()
    core.log("ultra", f"start v{__version__}", "INFO")
    ui.boot(__version__)          # cool Frutiger Aero splash + animated load bars
    cats = build_categories()
    while True:
        items = [(str(i + 1), c.label) for i, c in enumerate(cats)]
        items.append(("h", "Help — command reference"))
        items.append(("r", "Open Reports folder"))
        choice = ui.menu(
            f"ULTRA-PC  v{__version__}",
            f"on {core.COMPUTER}",
            items, "Exit", hero_header=True, version=__version__)
        if choice == "0" or choice.lower() in ("q", "exit"):
            ui.info("Bye."); return 0
        if choice.lower() == "h":
            from ultrapc import helpcmd
            helpcmd.show(); ui.pause(); continue
        if choice.lower() == "r":
            core.open_in_os(core.REPORTS_DIR); continue
        if choice.isdigit() and 1 <= int(choice) <= len(cats):
            run_category(cats[int(choice) - 1])


if __name__ == "__main__":
    try:
        rc = handle_cli(sys.argv[1:])
        sys.exit(rc if rc is not None else main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
