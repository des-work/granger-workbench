"""User interface: colored console output + tkinter GUI popups.

The app is driven from the console (menus, results) but anything interactive
that benefits from a real widget — file pickers, keepable results, save
dialogs, text prompts — pops up a native Tk window.
"""

from __future__ import annotations

import os
import sys

# --------------------------------------------------------------------------- #
#  Console: ANSI colors (enabled on modern Windows terminals)
# --------------------------------------------------------------------------- #

# Force UTF-8 stdout/stderr so article text (emoji, accents, symbols) prints on
# the legacy Windows console instead of crashing with a cp1252 encode error.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_USE_COLOR = True
if os.name == "nt":
    # Enable VT100 processing so ANSI codes render in the classic console too.
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)
    except Exception:
        _USE_COLOR = os.getenv("WT_SESSION") is not None or os.getenv("TERM") is not None


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[91m"; GRN = "\033[92m"; YEL = "\033[93m"
    BLU = "\033[94m"; MAG = "\033[95m"; CYN = "\033[96m"; WHT = "\033[97m"


def _c(text: str, color: str) -> str:
    return f"{color}{text}{C.RESET}" if _USE_COLOR else text


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def title_bar(text: str, sub: str = "") -> None:
    bar = "=" * 62
    print(_c(bar, C.CYN))
    print(_c(f"  {text}", C.BOLD + C.CYN))
    if sub:
        print(_c(f"  {sub}", C.DIM))
    print(_c(bar, C.CYN))


# --------------------------------------------------------------------------- #
#  Frutiger Aero splash — the cool ASCII title (blue→green gel + bubbles)
# --------------------------------------------------------------------------- #

def _aero_colors() -> tuple[str, str, str]:
    """Blue, green, ink from the vault's frutiger-aero tokens (single source)."""
    try:
        from . import assets
        t = assets.theme_colors("frutiger-aero")
        return (t.get("accent", "#2b8fd6"), t.get("accent2", "#96cd6e"),
                t.get("text", "#0b3c5d"))
    except Exception:
        return "#2b8fd6", "#96cd6e", "#0b3c5d"


def hero(version: str = "") -> None:
    """Print the intricate Frutiger Aero ULTRA-PC title card — thin fine-line
    letters inside an ornate gel frame with filigree corners + bubbles."""
    from . import cliart
    blue, green, _ink = _aero_colors()
    W = 56
    fill = W - 10
    top = "╭─◦°✦" + "─" * fill + "✦°◦─╮"
    mid = "├─◦" + "─" * (W - 6) + "◦─┤"
    bot = "╰─◦°✦" + "─" * fill + "✦°◦─╯"
    bub = "   ·  ° ◦ ⊙ ◦ °  ·   ✦   ·  ° ◦ ⊙ ◦ °  ·   ✦   ·  ° ◦ ⊙"
    tag = "~ ° ·  offline power toolkit" + (f"  ·  v{version}" if version else "") + "  · ° ~"
    print()
    print(cliart.gradient(bub, blue, green))
    print(cliart.gradient(top, blue, green))
    print()
    for row in cliart.banner("ULTRA PC", blue, green, font="thin").split("\n"):
        print("       " + row)
    print()
    print(cliart.gradient(mid, green, blue))
    print("       " + cliart.gradient(tag, green, blue))
    print(cliart.gradient(bot, blue, green))
    print(cliart.gradient(bub[::-1], green, blue))
    print()


def welcome(version: str = "") -> None:
    """Rich GitHub-CLI-style landing: title card + neofetch-style logo/info
    panel with color blocks + a quick-start tips box."""
    import platform
    import textwrap
    from . import cliart, core
    try:
        from . import assets
    except Exception:
        assets = None
    blue, green, ink = _aero_colors()
    clear()
    hero(version)

    # ---- neofetch-style logo + info panel -------------------------------- #
    mascot = "the ULTRA-PC toolkit"
    if assets is not None:
        mascot = textwrap.dedent(assets.ASCII_ART["ultra-bot"]["art"])
    mascot = "\n".join(cliart.gradient(r, blue, green) for r in mascot.split("\n"))

    try:
        import psutil
        ram = f"{psutil.virtual_memory().total / 1e9:.0f} GB"
    except Exception:
        ram = "31.6 GB"
    rel = platform.release()
    build = platform.release()
    if platform.system() == "Windows":
        build = platform.version().split(".")[-1]
        try:                       # Win 11 reports release "10"; build ≥22000 = 11
            if int(build) >= 22000:
                rel = "11"
        except ValueError:
            pass
    pc = len(assets.PALETTES) if assets else 0
    st = len(assets.STYLES) if assets else 0
    gr = len(assets.GRADIENTS) if assets else 0
    user = os.getenv("USERNAME") or os.getenv("USER") or "user"
    header = (cliart.color(user, green) + cliart.color("@", ink)
              + cliart.color(core.COMPUTER, blue))
    pairs = [
        ("", header),
        ("-", "36"),
        ("os", f"Windows {rel} (build {build})"),
        ("cpu", f"Intel 16C / {os.cpu_count()}T"),
        ("gpu", "RTX 4080 Laptop"),
        ("ram", ram),
        ("python", platform.python_version()),
        ("shell", f"Ultra-PC CLI v{version}"),
        ("-", "36"),
        ("knowledge", "offline Wikipedia + Stack Exchange"),
        ("assets", f"{pc} palettes · {st} styles · {gr} gradients"),
        ("fonts", "19 offline (OFL)"),
        ("", ""),
        ("", cliart.palette_row(["#2b8fd6", "#60b2f0", "#ceecff", "#ffffff",
                                 "#96cd6e", "#4e9638", "#0b3c5d"])),
    ]
    info = "\n".join(cliart.kv(pairs, key_c=blue))
    print(cliart.two_col(mascot, info, gap=4, indent=3))
    print()

    # ---- quick-start tips ------------------------------------------------- #
    tips = [
        'kb "query"       search the offline knowledge vault',
        "assets kit <s>   generate a full themed stylesheet",
        "[1-8] pick a tool    ·    [r] reports    ·    [0] exit",
    ]
    tip_box = cliart.box(tips, title="quick start", style="round", c=green)
    print("\n".join("   " + ln for ln in tip_box.split("\n")))
    print()


def press_any_key(label: str = "press any key to continue") -> None:
    """Themed pause so the launch screen stays until the user advances.
    Uses a true any-key read on Windows terminals; falls back to Enter."""
    from . import cliart
    blue, green, _ = _aero_colors()
    sys.stdout.write("\n   " + cliart.gradient("▸ " + label + " …", green, blue) + " ")
    sys.stdout.flush()
    try:
        if os.name == "nt" and sys.stdin.isatty():
            import msvcrt
            msvcrt.getch()
        else:
            sys.stdin.readline()
    except (EOFError, KeyboardInterrupt):
        pass
    print()


def boot(version: str = "") -> None:
    """Cool startup: rich welcome screen, animated loading bars, then wait for
    a keypress so the launch page stays up until the user is ready."""
    from . import cliart
    blue, green, _ = _aero_colors()
    welcome(version)
    for label, secs in (("  waking the toolkit", 0.5),
                        ("  loading knowledge vault", 0.5),
                        ("  loading design assets", 0.4), ("  ready", 0.3)):
        cliart.loadbar(label, seconds=secs, c1=blue, c2=green)
    press_any_key("press any key to enter Ultra-PC")


def loading(label: str = "working", seconds: float = 1.2) -> None:
    """Reusable animated Aero loading bar for any slow step."""
    from . import cliart
    blue, green, _ = _aero_colors()
    cliart.loadbar("  " + label, seconds=seconds, c1=blue, c2=green)


def info(text: str) -> None:  print(_c("  " + text, C.WHT))
def dim(text: str) -> None:   print(_c("  " + text, C.DIM))
def ok(text: str) -> None:    print(_c("  [OK]   " + text, C.GRN))
def warn(text: str) -> None:  print(_c("  [WARN] " + text, C.YEL))
def err(text: str) -> None:   print(_c("  [ERR]  " + text, C.RED))
def head(text: str) -> None:  print("\n" + _c(text, C.BOLD + C.MAG))


def status_line(status: str, text: str) -> None:
    color = {"PASS": C.GRN, "OK": C.GRN, "WARN": C.YEL,
             "FAIL": C.RED, "ERR": C.RED}.get(status, C.WHT)
    print("  " + _c(f"[{status:<4}]", color) + " " + text)


def prompt(text: str) -> str:
    try:
        return input(_c("  " + text, C.CYN)).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def pause() -> None:
    prompt("Press Enter to continue...")


def menu(title: str, sub: str, items: list[tuple[str, str]],
         back_label: str = "Back", hero_header: bool = False,
         version: str = "") -> str:
    """Render a menu, return the chosen key (or '0' for back/exit).
    hero_header=True swaps the plain title bar for the Frutiger Aero splash."""
    clear()
    if hero_header:
        hero(version)
        if sub:
            print("  " + _c(sub, C.DIM) + "\n")
    else:
        title_bar(title, sub)
        print()
    for key, label in items:
        print("  " + _c(f"[{key}]", C.BOLD + C.GRN) + f"  {label}")
    print("  " + _c("[0]", C.BOLD + C.GRN) + f"  {back_label}")
    print()
    return prompt("Select: ")


# --------------------------------------------------------------------------- #
#  GUI popups (tkinter). Each creates a throwaway hidden root.
# --------------------------------------------------------------------------- #

def _root():
    import tkinter as tk
    r = tk.Tk()
    r.withdraw()
    r.attributes("-topmost", True)
    return r


def popup_info(message: str, title: str = "Ultra-PC") -> None:
    try:
        from tkinter import messagebox
        r = _root(); messagebox.showinfo(title, message, parent=r); r.destroy()
    except Exception:
        info(message)


def popup_error(message: str, title: str = "Ultra-PC") -> None:
    try:
        from tkinter import messagebox
        r = _root(); messagebox.showerror(title, message, parent=r); r.destroy()
    except Exception:
        err(message)


def ask_yesno(message: str, title: str = "Ultra-PC") -> bool:
    try:
        from tkinter import messagebox
        r = _root(); ans = messagebox.askyesno(title, message, parent=r); r.destroy()
        return bool(ans)
    except Exception:
        return prompt(message + " [y/N]: ").lower().startswith("y")


def ask_string(message: str, title: str = "Ultra-PC", initial: str = "") -> str | None:
    try:
        from tkinter import simpledialog
        r = _root()
        ans = simpledialog.askstring(title, message, initialvalue=initial, parent=r)
        r.destroy()
        return ans
    except Exception:
        val = prompt(message + " ")
        return val or None


def ask_open_file(title: str = "Choose a file", filetypes=None) -> str | None:
    try:
        from tkinter import filedialog
        r = _root()
        path = filedialog.askopenfilename(title=title, parent=r,
                                          filetypes=filetypes or [("All files", "*.*")])
        r.destroy()
        return path or None
    except Exception:
        return prompt(title + " (path): ") or None


def ask_open_files(title: str = "Choose files", filetypes=None) -> list[str]:
    try:
        from tkinter import filedialog
        r = _root()
        paths = filedialog.askopenfilenames(title=title, parent=r,
                                            filetypes=filetypes or [("All files", "*.*")])
        r.destroy()
        return list(paths)
    except Exception:
        p = prompt(title + " (single path): ")
        return [p] if p else []


def ask_directory(title: str = "Choose a folder") -> str | None:
    try:
        from tkinter import filedialog
        r = _root()
        path = filedialog.askdirectory(title=title, parent=r)
        r.destroy()
        return path or None
    except Exception:
        return prompt(title + " (path): ") or None


def ask_save_file(title: str = "Save as", defaultext: str = ".txt",
                  initialfile: str = "") -> str | None:
    try:
        from tkinter import filedialog
        r = _root()
        path = filedialog.asksaveasfilename(title=title, parent=r,
                                            defaultextension=defaultext,
                                            initialfile=initialfile)
        r.destroy()
        return path or None
    except Exception:
        return prompt(title + " (path): ") or None


def deliver_report(report, slug: str) -> None:
    """Save a core.Report, print its verdict to the console, and offer to view."""
    from . import core
    summary = report.verdict()
    path = report.save(slug)
    print()
    title_bar("RESULT", report.title)
    print()
    status = "FAIL" if report.fail else ("WARN" if report.warn else "PASS")
    status_line(status, summary)
    dim(f"Saved: {path}")
    print()
    if ask_yesno("Open the full report now?", "Ultra-PC"):
        show_text(report.text(), f"Ultra-PC — {report.title}")
    pause()


def show_text(content: str, title: str = "Ultra-PC — Result") -> None:
    """Scrollable, copyable text window. Falls back to console printing."""
    try:
        import tkinter as tk
        from tkinter import scrolledtext
        r = tk.Tk()
        r.title(title)
        r.geometry("820x560")
        r.attributes("-topmost", True)
        txt = scrolledtext.ScrolledText(r, wrap="none", font=("Consolas", 10))
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", content)
        txt.configure(state="disabled")
        btns = tk.Frame(r); btns.pack(fill="x")

        def _copy():
            r.clipboard_clear(); r.clipboard_append(content)

        tk.Button(btns, text="Copy all", command=_copy).pack(side="left", padx=4, pady=4)
        tk.Button(btns, text="Close", command=r.destroy).pack(side="right", padx=4, pady=4)
        r.mainloop()
    except Exception:
        print("\n" + content + "\n")
