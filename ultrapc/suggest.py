"""AI-guided article suggestions — your LOCAL Ollama model recommends what to
read from the vault. Not a guess: the model proposes Wikipedia-style article
titles (things it knows Wikipedia HAS), Ultra-PC verifies each one against the
local vault, and returns the ones that actually exist as a reading list.

    python ultra.py learn "how do plants make food"    # suggests articles
    python ultra.py learn --topic "quantum mechanics"  # a full reading list

Combined with the ratings loop (ultrapc/ratings.py), the system guides learning
rather than guessing at keywords.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import ai, core, knowledge, ratings


SYSTEM = (
    "You recommend real Wikipedia articles the user should read to learn about "
    "a topic. Return ONLY a JSON array of 6-10 objects, each with keys:\n"
    '  "title"  – the exact Wikipedia article title (as it would appear)\n'
    '  "why"    – one short sentence on what this article teaches\n'
    "Order from most fundamental to most specialized. Prefer canonical articles "
    "(e.g. 'Photosynthesis' over 'Photosynthesis in plants'). No commentary "
    "outside the JSON array. No markdown, no code fences.\n\n"
    + ai.VALUES + "\n\n"
    "Recommend articles ABOUT hate groups, terrorism, atrocities, and "
    "controversial figures freely — history and understanding require it. "
    "Recommend TECHNICAL articles freely, including cybersecurity (offensive "
    "and defensive: hacking, malware, red team, pen testing, exploits, reverse "
    "engineering, network attacks), robotics, engineering, weapons as "
    "engineering, chemistry, biology, physics. The user is a cybersecurity "
    "professional; do NOT refuse or hedge on these topics.\n"
    "Only return an empty JSON array [] if the topic is inherently "
    "operational-harmful against real people (e.g. 'how to poison my "
    "neighbor', 'plan an attack on this specific location')."
)


def _extract_json(text: str) -> list[dict]:
    m = re.search(r"\[\s*\{.*?\}\s*\]", text, re.S)
    if not m:
        return []
    try:
        arr = json.loads(m.group(0))
    except Exception:
        return []
    return [x for x in arr if isinstance(x, dict) and x.get("title")]


def _rated_hints(topic: str) -> tuple[list[str], list[str]]:
    """Look up your past ratings for this topic's entity so we can bias the AI:
    return (well_rated_titles, poorly_rated_titles). Titles are prettified from
    the article paths so the AI recognizes them."""
    entity = ai._entity(topic)[0]
    boosts = ratings.boost_for(entity) if entity else {}
    good = [p.replace("_", " ") for p, b in boosts.items() if b > 0.05]
    bad = [p.replace("_", " ") for p, b in boosts.items() if b < -0.05]
    return good, bad


def ai_suggestions(topic: str, model: str | None = None) -> list[dict]:
    """Ask the local model for a curated reading list. Returns raw suggestions
    (title + why); NOT yet verified against the vault. Incorporates your past
    ratings so the AI knows what worked and what didn't for this topic."""
    model = model or ai.default_model()
    if not model:
        return []
    good, bad = _rated_hints(topic)
    hints = ""
    if good:
        hints += ("\n\nThe user previously rated these articles as HELPFUL on "
                  f"this topic — include them near the top:\n- "
                  + "\n- ".join(good[:6]))
    if bad:
        hints += ("\n\nThe user previously rated these as NOT relevant on this "
                  f"topic — do NOT include them:\n- "
                  + "\n- ".join(bad[:6]))
    prompt = (f"Topic: {topic}{hints}\n\nGive me a Wikipedia reading list for "
              f"this topic as JSON.")
    msg = [{"role": "system", "content": SYSTEM},
           {"role": "user", "content": prompt}]
    out = "".join(ai.chat_stream(model, msg))
    return _extract_json(out)


def verify_in_vault(suggestions: list[dict]) -> list[dict]:
    """Keep only suggestions whose article actually exists locally, and attach
    the vault path so the user can open them."""
    hits = []
    for s in suggestions:
        title = s.get("title", "").strip()
        if not title:
            continue
        found = knowledge.resolve_title(title)
        if not found:
            for hit in knowledge.suggest(title, n=3):
                if hit["title"].strip().lower() == title.lower():
                    found = hit
                    break
        if found:
            hits.append({"title": found["title"], "path": found["path"],
                         "book": found["book"], "why": s.get("why", ""),
                         "url": f"{knowledge.BASE}/content/{found['book']}/{found['path']}"})
    return hits


def learn(topic: str, model: str | None = None) -> dict:
    """Full pipeline: local AI recommends -> vault verifies -> reading list."""
    if not ai.available():
        return {"error": "Local AI (Ollama) is not running. Start Ollama and try again."}
    raw = ai_suggestions(topic, model)
    if not raw:
        return {"error": "The local model didn't return usable suggestions. "
                         "Try a broader topic or a bigger model."}
    verified = verify_in_vault(raw)
    return {"topic": topic, "raw": raw, "verified": verified,
            "missing": [s["title"] for s in raw
                        if not any(v["title"].lower() == s.get("title", "").lower()
                                   for v in verified)]}


# --------------------------------------------------------------------------- #
#  CLI + menu
# --------------------------------------------------------------------------- #

def cmd_learn(topic: str) -> int:
    if not topic:
        print('usage: learn "<topic>"'); return 2

    from . import cliart
    from .ui import _aero_colors
    blue, green, ink = _aero_colors()

    # -------- themed header + prompt line --------------------------------- #
    print()
    print(cliart.gradient("  ╭◦°" + "─" * 62 + "°◦╮", blue, green))
    for row in cliart.banner("LEARN", blue, green, font="thin").split("\n"):
        print("       " + row)
    print(cliart.gradient(
        f"       ~ ° ·  your local AI plans a reading list  · ° ~", green, blue))
    print(cliart.gradient("  ╰◦°" + "─" * 62 + "°◦╯", blue, green))
    print()
    print(cliart.color(f"  ▸ Topic: ", green) + cliart.color(topic, "#ffffff"))
    print(cliart.color("    (local model · offline · your vault)", "#8fb8cf"))
    print()

    # -------- spinner while the model composes ---------------------------- #
    holder = {"r": None}

    def worker():
        holder["r"] = learn(topic)

    import threading
    th = threading.Thread(target=worker, daemon=True)
    th.start()
    with cliart.Spinner("  consulting local AI", style="dots", c=blue):
        th.join()
    r = holder["r"] or {"error": "no result"}

    if "error" in r:
        print(cliart.color("  ✕ " + r["error"], "#ff5f57"))
        return 1

    verified = r["verified"]
    if not verified:
        print(cliart.color("  ! The AI suggested articles, but none matched "
                           "local vault titles.", "#febc2e"))
        print(cliart.color("    (Try a broader topic, or a bigger model)",
                           "#8fb8cf"))
        for s in r["raw"][:8]:
            print(f"      · {s['title']}")
        return 1

    # -------- animated reveal + themed reading-list box ------------------- #
    cliart.loadbar("  composing your reading list", seconds=0.6,
                   c1=blue, c2=green)
    print()

    header = f" Reading list · {len(verified)} articles from your vault "
    top = cliart.gradient("  ╭─" + "─" * (max(60, len(header) + 4)) + "─╮",
                          blue, green)
    print(top)
    print("  " + cliart.color("│", blue) + cliart.color(header, "#ffffff")
          + " " * (max(60, len(header) + 4) - len(header) + 1)
          + cliart.color("│", green))
    print(cliart.gradient("  ├─" + "─" * (max(60, len(header) + 4)) + "─┤",
                          blue, green))
    for i, v in enumerate(verified, 1):
        num = cliart.color(f"[{i}]", green)
        title = cliart.color(v["title"], "#eaf6ff")
        print(f"  {cliart.color('│', blue)}  {num} {title}")
        if v.get("why"):
            print(f"  {cliart.color('│', blue)}      "
                  + cliart.color(v["why"][:80], "#8fb8cf"))
    print(cliart.gradient("  ╰─" + "─" * (max(60, len(header) + 4)) + "─╯",
                          blue, green))

    if r["missing"]:
        print()
        print(cliart.color(
            "  ° AI also suggested (not in local vault): "
            + ", ".join(r["missing"][:5]), "#8fb8cf"))

    print()
    hint = ("  ▸ enter #, comma-list, or 'all' to open in your browser  ·  "
            "Enter to skip")
    print(cliart.gradient(hint, green, blue))

    # Offer to open any/all (e.g. "1", "1,3,5", "all"), then rate
    from . import ui
    sel = ui.prompt("\nOpen # (comma-separated, 'all', Enter to skip): ").strip().lower()
    opened_paths = [v["path"] for v in verified]
    to_open: list = []
    if sel == "all":
        to_open = verified
    elif sel:
        for part in sel.replace(" ", "").split(","):
            if part.isdigit() and 1 <= int(part) <= len(verified):
                to_open.append(verified[int(part) - 1])
    if to_open:
        knowledge.serve_start()
        import webbrowser
        for v in to_open:
            ui.info(f"Opening {v['title']}…")
            webbrowser.open(v["url"])
    _prompt_rating(topic, opened_paths, mode="learn")
    return 0


def _prompt_rating(query: str, paths: list, mode: str) -> None:
    """Ask the user to rate what they got (0-5). Silently no-op on Enter."""
    from . import ui, cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    print()
    print("  " + cliart.gradient("─" * 62, blue, green))
    print("  " + cliart.color("★ Rate these results — 0 to 5", green))
    star_line = ("  " + cliart.color("0", "#8fb8cf") + " nothing   "
                 + cliart.color("1", "#8fb8cf") + " nothing relevant   "
                 + cliart.color("3", "#febc2e") + " some useful   "
                 + cliart.color("5", green) + " exactly what I needed")
    print(star_line)
    s = ui.prompt("  ▸ rating (Enter to skip): ").strip()
    if s.isdigit():
        stars = max(0, min(5, int(s)))
        ratings.rate(query, paths, stars, mode=mode)
        icons = "★" * stars + "☆" * (5 - stars)
        print("  " + cliart.gradient(icons, blue, green)
              + cliart.color(f"  saved — future searches on this topic "
                             f"will improve.", "#8fb8cf"))


def _tool_learn(ctx=None) -> None:
    from . import ui
    ui.title_bar("Learn — AI-guided reading list",
                 "your local model recommends articles from your vault")
    topic = ui.prompt("What do you want to learn about? ").strip()
    if not topic:
        ui.pause(); return
    print()
    cmd_learn(topic)
    ui.pause()


def handle(argv: list[str]) -> int | None:
    if not argv:
        return None
    cmd = argv[0].lower()
    rest = argv[1:]
    if cmd in ("learn", "suggest"):
        i = 0
        topic_parts = []
        while i < len(rest):
            if rest[i] == "--topic" and i + 1 < len(rest):
                topic_parts.append(rest[i + 1]); i += 2
            else:
                topic_parts.append(rest[i]); i += 1
        return cmd_learn(" ".join(topic_parts))
    return None
