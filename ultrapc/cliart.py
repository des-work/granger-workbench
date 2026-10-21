"""cliart — make CLI tools look cool. Reusable terminal-art helpers: figlet-ish
block banners, boxes, rules, ANSI truecolor gradient/rainbow text, spinners,
and progress bars. Stdlib-only; degrades to plain text if a terminal can't do
ANSI. Import from any Ultra-PC tool (or the thumbdrive kit) — not just here.

    from ultrapc import cliart
    print(cliart.banner("ULTRA"))
    print(cliart.box(["Ready.", "All systems go."], title="STATUS"))
    print(cliart.gradient("loading...", (43,143,214), (150,205,110)))
"""

from __future__ import annotations

import os
import re
import sys
import time
from itertools import cycle
from threading import Event, Thread

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_len(s: str) -> int:
    """Length of a string ignoring ANSI color codes (for alignment)."""
    return len(_ANSI_RE.sub("", s))

# --------------------------------------------------------------------------- #
#  ANSI plumbing
# --------------------------------------------------------------------------- #

def _ensure_utf8() -> bool:
    """Legacy Windows consoles default to cp1252 and choke on box-drawing/block
    glyphs. Try to switch stdout/stderr to UTF-8 (as ui.py does). Return whether
    unicode art is safe to emit; callers fall back to ASCII if not."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
        except Exception:
            pass
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    return "utf" in enc


UTF8 = _ensure_utf8()


def _supports_ansi() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if sys.platform == "win32":
        # Windows 10+ terminals + Windows Terminal handle VT; enable it.
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)  # ENABLE_VIRTUAL_TERMINAL
            return True
        except Exception:
            return os.environ.get("WT_SESSION") is not None
    return sys.stdout.isatty()


ANSI = _supports_ansi()
RESET = "\x1b[0m" if ANSI else ""


def _is_tty() -> bool:
    """Real interactive terminal? Gates in-place animation (spinners, load
    bars) so piped/redirected output isn't spammed with \\r frames."""
    try:
        return bool(sys.stdout.isatty())
    except Exception:
        return False


TTY = _is_tty()


def fg(r: int, g: int, b: int) -> str:
    return f"\x1b[38;2;{r};{g};{b}m" if ANSI else ""


def bg(r: int, g: int, b: int) -> str:
    return f"\x1b[48;2;{r};{g};{b}m" if ANSI else ""


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _as_rgb(c) -> tuple[int, int, int]:
    return _hex_rgb(c) if isinstance(c, str) else tuple(c)  # type: ignore


# --------------------------------------------------------------------------- #
#  Colored text
# --------------------------------------------------------------------------- #

def color(text: str, c) -> str:
    r, g, b = _as_rgb(c)
    return f"{fg(r, g, b)}{text}{RESET}"


def gradient(text: str, c1, c2) -> str:
    """Left→right truecolor gradient across the characters."""
    if not ANSI or not text:
        return text
    (r1, g1, b1), (r2, g2, b2) = _as_rgb(c1), _as_rgb(c2)
    n = max(1, len(text) - 1)
    out = []
    for i, ch in enumerate(text):
        t = i / n
        out.append(fg(int(r1 + (r2 - r1) * t),
                      int(g1 + (g2 - g1) * t),
                      int(b1 + (b2 - b1) * t)) + ch)
    return "".join(out) + RESET


_RAINBOW = [(255, 0, 110), (251, 86, 7), (255, 190, 11),
            (56, 176, 0), (58, 134, 255), (131, 56, 236)]


def rainbow(text: str) -> str:
    if not ANSI or not text:
        return text
    cols = cycle(_RAINBOW)
    return "".join(color(ch, next(cols)) if ch.strip() else ch for ch in text)


# --------------------------------------------------------------------------- #
#  Block-letter banner  (compact built-in 5-row font)
# --------------------------------------------------------------------------- #

# Each glyph is 5 rows; '#' = ink, ' ' = space. Uppercase, digits, few symbols.
_FONT_BLOCK: dict[str, list[str]] = {
    " ": ["   "] * 5,
    "A": ["███", "█ █", "███", "█ █", "█ █"],
    "B": ["██ ", "█ █", "██ ", "█ █", "██ "],
    "C": ["███", "█  ", "█  ", "█  ", "███"],
    "D": ["██ ", "█ █", "█ █", "█ █", "██ "],
    "E": ["███", "█  ", "██ ", "█  ", "███"],
    "F": ["███", "█  ", "██ ", "█  ", "█  "],
    "G": ["███", "█  ", "█ █", "█ █", "███"],
    "H": ["█ █", "█ █", "███", "█ █", "█ █"],
    "I": ["███", " █ ", " █ ", " █ ", "███"],
    "J": ["███", "  █", "  █", "█ █", "███"],
    "K": ["█ █", "██ ", "█  ", "██ ", "█ █"],
    "L": ["█  ", "█  ", "█  ", "█  ", "███"],
    "M": ["█ █", "███", "███", "█ █", "█ █"],
    "N": ["█ █", "██ ", "███", " ██", "█ █"],
    "O": ["███", "█ █", "█ █", "█ █", "███"],
    "P": ["███", "█ █", "███", "█  ", "█  "],
    "Q": ["███", "█ █", "█ █", "███", "  █"],
    "R": ["██ ", "█ █", "██ ", "█ █", "█ █"],
    "S": ["███", "█  ", "███", "  █", "███"],
    "T": ["███", " █ ", " █ ", " █ ", " █ "],
    "U": ["█ █", "█ █", "█ █", "█ █", "███"],
    "V": ["█ █", "█ █", "█ █", "█ █", " █ "],
    "W": ["█ █", "█ █", "███", "███", "█ █"],
    "X": ["█ █", "█ █", " █ ", "█ █", "█ █"],
    "Y": ["█ █", "█ █", " █ ", " █ ", " █ "],
    "Z": ["███", "  █", " █ ", "█  ", "███"],
    "0": ["███", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "███"],
    "7": ["███", "  █", " █ ", " █ ", " █ "],
    "8": ["███", "█ █", "███", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "███"],
    "-": ["   ", "   ", "███", "   ", "   "],
    "!": [" █ ", " █ ", " █ ", "   ", " █ "],
    "?": ["███", "  █", " ██", "   ", " █ "],
    ".": ["   ", "   ", "   ", "   ", " █ "],
}

# Thin fine-line font — box-drawing glyphs, 4 cols x 5 rows. Elegant/intricate,
# for delicate title cards. Needs UTF-8; falls back to the block font if not.
_FONT_THIN: dict[str, list[str]] = {
    " ": ["    "] * 5,
    "A": ["╭──╮", "│  │", "├──┤", "│  │", "╵  ╵"],
    "B": ["├──╮", "│  │", "├──┤", "│  │", "├──╯"],
    "C": ["╭──╴", "│   ", "│   ", "│   ", "╰──╴"],
    "D": ["├──╮", "│  │", "│  │", "│  │", "├──╯"],
    "E": ["├──╴", "│   ", "├── ", "│   ", "╰──╴"],
    "F": ["├──╴", "│   ", "├── ", "│   ", "╵   "],
    "G": ["╭──╴", "│   ", "│ ─╮", "│  │", "╰──╯"],
    "H": ["╷  ╷", "│  │", "├──┤", "│  │", "╵  ╵"],
    "I": ["╶──╴", " │  ", " │  ", " │  ", "╶──╴"],
    "J": ["   ╷", "   │", "   │", "│  │", "╰──╯"],
    "K": ["╷ ╱ ", "│╱  ", "├╴  ", "│╲  ", "╵ ╲ "],
    "L": ["╷   ", "│   ", "│   ", "│   ", "╰──╴"],
    "M": ["╭╮╭╮", "││││", "│╰╯│", "│  │", "╵  ╵"],
    "N": ["╷  ╷", "│╲ │", "│ ╲│", "│  │", "╵  ╵"],
    "O": ["╭──╮", "│  │", "│  │", "│  │", "╰──╯"],
    "P": ["├──╮", "│  │", "├──╯", "│   ", "╵   "],
    "Q": ["╭──╮", "│  │", "│  │", "│ ╲│", "╰──╲"],
    "R": ["├──╮", "│  │", "├──╯", "│╲  ", "╵ ╲ "],
    "S": ["╭──╴", "│   ", "╰──╮", "   │", "╶──╯"],
    "T": ["╶──╴", " │  ", " │  ", " │  ", " ╵  "],
    "U": ["╷  ╷", "│  │", "│  │", "│  │", "╰──╯"],
    "V": ["╷  ╷", "│  │", "╲  ╱", " ╲╱ ", "  ╵ "],
    "W": ["╷  ╷", "│  │", "│  │", "│╱╲│", "╰╯╰╯"],
    "X": ["╲  ╱", " ╲╱ ", " ╱╲ ", "╱  ╲", "    "],
    "Y": ["╷  ╷", "╲  ╱", " ╲╱ ", "  │ ", "  ╵ "],
    "Z": ["╶──╴", "  ╱ ", " ╱  ", "╱   ", "╶──╴"],
    "0": ["╭──╮", "│ ╱│", "│╱ │", "│  │", "╰──╯"],
    "1": ["  ╷ ", "  │ ", "  │ ", "  │ ", "  ╵ "],
    "2": ["╭──╮", "   │", "╭──╯", "│   ", "╰──╴"],
    "3": ["╭──╮", "   │", " ──┤", "   │", "╰──╯"],
    "4": ["╷  ╷", "│  │", "╰──┤", "   │", "   ╵"],
    "5": ["├──╴", "│   ", "╰──╮", "   │", "╶──╯"],
    "6": ["╭──╴", "│   ", "├──╮", "│  │", "╰──╯"],
    "7": ["╶──╮", "  ╱ ", " ╱  ", "╱   ", "╵   "],
    "8": ["╭──╮", "│  │", "├──┤", "│  │", "╰──╯"],
    "9": ["╭──╮", "│  │", "╰──┤", "   │", "╶──╯"],
    "-": ["    ", "    ", "╶──╴", "    ", "    "],
    "!": [" ╷  ", " │  ", " │  ", "    ", " ╵  "],
    "?": ["╭──╮", "   │", " ╶─╯", "    ", " ╵  "],
    ".": ["    ", "    ", "    ", "    ", " ╵  "],
}

FONTS = {"block": _FONT_BLOCK, "thin": _FONT_THIN}


def banner(text: str, c1=None, c2=None, font: str = "block") -> str:
    """figlet-style banner. `font`: 'block' (thick) or 'thin' (fine box-drawing).
    Optional left→right gradient between c1 and c2."""
    if font == "thin" and not UTF8:      # thin needs box-drawing glyphs
        font = "block"
    glyphs = FONTS.get(font, _FONT_BLOCK)
    fallback = glyphs.get("?") or glyphs[" "]
    text = text.upper()
    rows = ["", "", "", "", ""]
    for ch in text:
        glyph = glyphs.get(ch, fallback)
        for i in range(5):
            rows[i] += glyph[i] + " "
    if not UTF8:
        rows = [r.replace("█", "#") for r in rows]
    if c1 is not None and ANSI:
        c2 = c2 if c2 is not None else c1
        rows = [gradient(r, c1, c2) for r in rows]
    return "\n".join(rows)


# --------------------------------------------------------------------------- #
#  Boxes and rules
# --------------------------------------------------------------------------- #

_BOX = {
    "round":  "╭╮╰╯─│", "single": "┌┐└┘─│", "double": "╔╗╚╝═║",
    "heavy":  "┏┓┗┛━┃", "ascii":  "++++-|",
}


def box(lines, title: str = "", style: str = "round", c=None, pad: int = 1) -> str:
    """Frame `lines` (str or list) in a box. Optional title + border color."""
    if isinstance(lines, str):
        lines = lines.splitlines() or [""]
    if not UTF8:
        style = "ascii"
    tl, tr, bl, br, hz, vt = _BOX.get(style, _BOX["round"])
    width = max([len(l) for l in lines] + [len(title) + 2])
    inner = width + pad * 2
    top = tl + hz * inner + tr
    if title:
        label = f" {title} "
        top = tl + hz + label + hz * (inner - len(label) - 1) + tr
    bottom = bl + hz * inner + br
    body = [vt + " " * pad + l.ljust(width) + " " * pad + vt for l in lines]
    if c is not None and ANSI:
        r, g, b = _as_rgb(c)
        col = fg(r, g, b)
        top, bottom = col + top + RESET, col + bottom + RESET
        body = [col + vt + RESET + l[len(vt):-len(vt)] + col + vt + RESET for l in body]
    return "\n".join([top, *body, bottom])


def rule(width: int = 60, char: str = "─", c=None) -> str:
    line = char * width
    return color(line, c) if c is not None else line


# --------------------------------------------------------------------------- #
#  Layout primitives — neofetch-style columns, key/value panels, color blocks
# --------------------------------------------------------------------------- #

def two_col(left: str, right: str, gap: int = 4, indent: int = 2) -> str:
    """Join two multi-line blocks side by side (logo | info), ANSI-aware."""
    L, R = left.split("\n"), right.split("\n")
    n = max(len(L), len(R))
    L += [""] * (n - len(L))
    R += [""] * (n - len(R))
    w = max((visible_len(x) for x in L), default=0)
    pre = " " * indent
    out = []
    for l, r in zip(L, R):
        pad = " " * (w - visible_len(l) + gap)
        out.append(pre + l + pad + r)
    return "\n".join(out)


def kv(pairs, key_c="#2b8fd6", val_c=None, sep=" : ") -> list[str]:
    """Format key/value rows (neofetch style). A pair with key='' is a raw line
    (value printed as-is); key='-' makes a divider using the value as width."""
    kw = max((len(k) for k, _ in pairs if k not in ("", "-")), default=0)
    lines = []
    for k, v in pairs:
        if k == "-":
            lines.append(color("─" * int(v or 24), key_c)); continue
        if k == "":
            lines.append(v); continue
        key = color(k.ljust(kw), key_c)
        val = color(str(v), val_c) if val_c else str(v)
        lines.append(f"{key}{sep}{val}")
    return lines


def palette_row(colors, block: str = "███", sep: str = " ") -> str:
    """A row of solid color blocks — the classic neofetch palette strip."""
    b = block if UTF8 else "###"
    return sep.join(color(b, c) for c in colors)


# --------------------------------------------------------------------------- #
#  Spinner + progress bar
# --------------------------------------------------------------------------- #

SPINNERS = {
    "dots": "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", "line": "|/-\\", "bar": "▁▂▃▄▅▆▇█▇▆▅▄▃▂",
    "moon": "🌑🌒🌓🌔🌕🌖🌗🌘", "arrow": "←↖↑↗→↘↓↙", "bounce": "⠁⠂⠄⠂",
}


class Spinner:
    """Context manager: `with cliart.Spinner('working'): ...`."""

    def __init__(self, label: str = "", style: str = "dots", c=None):
        if not UTF8 and style not in ("line",):
            style = "line"
        self.label, self.frames, self.c = label, SPINNERS.get(style, SPINNERS["dots"]), c
        self._stop, self._th = Event(), None

    def _run(self):
        for fr in cycle(self.frames):
            if self._stop.is_set():
                break
            sym = color(fr, self.c) if self.c is not None else fr
            sys.stdout.write(f"\r{sym} {self.label}")
            sys.stdout.flush()
            time.sleep(0.08)
        sys.stdout.write("\r" + " " * (len(self.label) + 4) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        if ANSI and TTY:
            self._th = Thread(target=self._run, daemon=True); self._th.start()
        elif self.label:
            # not a terminal — announce once, don't spam \r frames into a pipe
            sym = color("*", self.c) if self.c is not None else "*"
            sys.stdout.write(f"{sym} {self.label.strip()}...\n")
            sys.stdout.flush()
        return self

    def __exit__(self, *a):
        self._stop.set()
        if self._th:
            self._th.join(timeout=0.3)


def progress(frac: float, width: int = 30, c=None, fill: str = "█", empty: str = "░") -> str:
    """Return a progress-bar string for frac in [0,1]. Print with end='\\r'."""
    if not UTF8:
        fill, empty = "#", "-"
    frac = max(0.0, min(1.0, frac))
    n = int(width * frac)
    bar = fill * n + empty * (width - n)
    if c is not None:
        bar = color(bar, c)
    return f"{bar} {int(frac * 100):3d}%"


def gradient_bar(frac: float, width: int, c1, c2, fill: str, empty: str) -> str:
    """A progress bar whose filled cells fade c1→c2 across the full width."""
    (r1, g1, b1), (r2, g2, b2) = _as_rgb(c1), _as_rgb(c2)
    n = int(width * max(0.0, min(1.0, frac)))
    cells = []
    for i in range(width):
        if i < n and ANSI:
            t = i / max(1, width - 1)
            cells.append(fg(int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t),
                            int(b1 + (b2 - b1) * t)) + fill)
        elif i < n:
            cells.append(fill)
        else:
            cells.append((f"\x1b[2m{empty}{RESET}" if ANSI else empty))
    return "".join(cells) + (RESET if ANSI else "")


def loadbar(label: str = "", seconds: float = 1.2, width: int = 34,
            c1="#2b8fd6", c2="#96cd6e") -> None:
    """Animate a gradient loading bar to 100% over `seconds`, in place."""
    if not TTY:                      # piped/redirected — don't spam \r frames
        if label:
            sys.stdout.write(f"{label.strip()}... done\n"); sys.stdout.flush()
        return
    fill, empty = ("█", "░") if UTF8 else ("#", "-")
    steps = max(1, int(seconds / 0.03))
    for s in range(steps + 1):
        frac = s / steps
        bar = gradient_bar(frac, width, c1, c2, fill, empty)
        sys.stdout.write(f"\r{label} {bar} {int(frac * 100):3d}%")
        sys.stdout.flush()
        time.sleep(0.03)
    sys.stdout.write("\n")
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
#  Self-demo
# --------------------------------------------------------------------------- #

def demo() -> None:
    print(banner("ULTRA PC", (43, 143, 214), (150, 205, 110)))
    print()
    print(box(["Offline power toolkit.", "Now with cool CLIs."],
              title="ULTRA-PC", style="double", c="#2b8fd6"))
    print()
    print("gradient : " + gradient("smooth color transition across text", "#ff71ce", "#01cdfe"))
    print("rainbow  : " + rainbow("taste the rainbow"))
    print("rule     : " + rule(40, "─", "#96cd6e"))
    print()
    for i in range(0, 101, 20):
        sys.stdout.write("\rprogress : " + progress(i / 100, c="#2b8fd6"))
        sys.stdout.flush(); time.sleep(0.15)
    print()
    with Spinner("thinking", style="dots", c="#b967ff"):
        time.sleep(1.2)
    print("done.")


if __name__ == "__main__":
    demo()
