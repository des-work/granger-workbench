"""Markdown -> clean, readable plain text.

The "read my notes like the browser shows them" renderer. Turns a raw .md file
(full of #, *, `, |, and $$LaTeX$$ noise) into what your eyes actually want:
underlined headings, spaced paragraphs, real • bullets, aligned tables, code
blocks without fences, and LaTeX math prettified into Unicode (η, ∫, √, ≈, …)
instead of backslash soup.

    python ultra.py md <file.md>            # clean readable text
    python ultra.py md <file.md> --width 100 # wrap paragraphs to 100 cols
    python ultra.py md <file.md> --out clean.txt
    python ultra.py read <file.md>          # same thing (read routes .md here)
    python ultra.py read <file.md> --raw    # escape hatch: verbatim markdown

Stdlib-only. Not a spec-perfect CommonMark parser — a pragmatic reader that
kills the symbol noise for the markdown people actually get handed.
"""

from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

# --------------------------------------------------------------------------- #
#  LaTeX -> Unicode  (best-effort; makes $...$ and $$...$$ readable in a shell)
# --------------------------------------------------------------------------- #

_GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "θ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ",
    "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}

_SYMBOLS = {
    r"\mid": " | ", r"\int": "∫", r"\iint": "∬", r"\sum": "Σ", r"\prod": "∏",
    r"\infty": "∞", r"\partial": "∂", r"\nabla": "∇", r"\approx": "≈",
    r"\neq": "≠", r"\leq": "≤", r"\geq": "≥", r"\ll": "≪", r"\gg": "≫",
    r"\equiv": "≡", r"\propto": "∝", r"\times": "×", r"\div": "÷",
    r"\cdot": "·", r"\cdots": "⋯", r"\ldots": "…", r"\dots": "…", r"\pm": "±",
    r"\mp": "∓", r"\to": "→", r"\rightarrow": "→", r"\longrightarrow": "→",
    r"\leftarrow": "←", r"\Rightarrow": "⇒", r"\Leftarrow": "⇐",
    r"\leftrightarrow": "↔", r"\mapsto": "↦", r"\langle": "⟨", r"\rangle": "⟩",
    r"\in": "∈", r"\notin": "∉", r"\subset": "⊂", r"\subseteq": "⊆",
    r"\supset": "⊃", r"\cup": "∪", r"\cap": "∩", r"\forall": "∀",
    r"\exists": "∃", r"\emptyset": "∅", r"\partial": "∂", r"\prime": "′",
    r"\pm": "±", r"\sim": "∼", r"\simeq": "≃", r"\cong": "≅", r"\perp": "⊥",
    r"\angle": "∠", r"\deg": "°", r"\circ": "∘", r"\star": "⋆", r"\ast": "∗",
    r"\oplus": "⊕", r"\otimes": "⊗", r"\wedge": "∧", r"\vee": "∨",
    r"\Vert": "‖", r"\|": "‖", r"\backslash": "\\",
}

# blackboard-bold sets like \mathbb{R}
_BB = {"R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ", "E": "𝔼", "P": "ℙ"}

_SUB = str.maketrans(
    "0123456789+-=()aehijklmnoprstuvx",
    "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ")
_SUP = str.maketrans(
    "0123456789+-=()abcdefghijklmnoprstuvwxyABDEGHIJKLMNOPRTUW",
    "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁᵂ")


def _script(body: str, table) -> str | None:
    """Map a sub/superscript group to Unicode, or None if any char can't map.

    Every entry in the tables maps to a *different* glyph, so a char that comes
    back unchanged simply isn't in the map — bail and let the caller fall back
    to the readable _(...) / ^(...) form."""
    if not body:
        return None
    out = []
    for ch in body:
        m = ch.translate(table)
        if m == ch:
            return None
        out.append(m)
    return "".join(out)


def _apply_scripts(s: str) -> str:
    """x_{t-1} -> xₜ₋₁ when mappable, else x_(t-1);  a^{2} -> a²  etc."""
    # braced groups first
    s = re.sub(r"_\{([^{}]*)\}",
               lambda m: (_script(m.group(1), _SUB) or "_(" + m.group(1) + ")"), s)
    s = re.sub(r"\^\{([^{}]*)\}",
               lambda m: (_script(m.group(1), _SUP) or "^(" + m.group(1) + ")"), s)
    # single-char scripts
    s = re.sub(r"_([A-Za-z0-9])",
               lambda m: (_script(m.group(1), _SUB) or "_" + m.group(1)), s)
    s = re.sub(r"\^([A-Za-z0-9])",
               lambda m: (_script(m.group(1), _SUP) or "^" + m.group(1)), s)
    return s


def _braced(s: str, start: int) -> tuple[str, int]:
    """Given s[start] == '{', return (inner, index_after_close) with nesting."""
    depth, i = 0, start
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i + 1
        i += 1
    return s[start + 1:], len(s)      # unbalanced — take the rest


def _sub_cmd(s: str, cmd: str, nargs: int, fmt) -> str:
    """Replace every \\cmd{..}{..} (balanced braces, nesting-safe) via fmt(args)."""
    out, i, token = [], 0, "\\" + cmd
    while True:
        j = s.find(token, i)
        if j < 0:
            out.append(s[i:])
            break
        out.append(s[i:j])
        k = j + len(token)
        while k < len(s) and s[k] in " \t":
            k += 1
        args = []
        ok = True
        for _ in range(nargs):
            if k < len(s) and s[k] == "{":
                arg, k = _braced(s, k)
                args.append(arg)
            else:
                ok = False
                break
        if ok:
            out.append(fmt(args))
            i = k
        else:                          # not the braced form — leave token as-is
            out.append(token)
            i = j + len(token)
    return "".join(out)


def latex_to_text(s: str) -> str:
    """Best-effort LaTeX -> readable Unicode. Not a math engine; a de-noiser."""
    # \tag{4} -> trailing (4)
    tags = re.findall(r"\\tag\{([^{}]*)\}", s)
    s = _sub_cmd(s, "tag", 1, lambda a: "")

    # structural: \frac, \sqrt, \boxed, \text, \mathrm, \mathbb, \operatorname.
    # Balanced-brace aware, so nested groups like \boxed{ ... ds_{t-1}} survive.
    s = _sub_cmd(s, "dfrac", 2, lambda a: f"({a[0]})/({a[1]})")
    s = _sub_cmd(s, "frac", 2, lambda a: f"({a[0]})/({a[1]})")
    s = _sub_cmd(s, "sqrt", 1, lambda a: f"√({a[0]})")
    s = _sub_cmd(s, "boxed", 1, lambda a: f"[ {a[0].strip()} ]")
    s = _sub_cmd(s, "mathbb", 1, lambda a: _BB.get(a[0], a[0]))
    # accents: \bar b / \hat{x} / \tilde m -> b̄ / x̂ / m̃ (combining marks)
    for acc, mark in (("bar", "̄"), ("hat", "̂"), ("tilde", "̃"),
                      ("vec", "⃗"), ("dot", "̇")):
        s = _sub_cmd(s, acc, 1,
                     lambda a, mk=mark: (a[0][:1] + mk + a[0][1:]) if a[0] else "")
        s = re.sub(r"\\" + acc + r"\s+([A-Za-z])", r"\1" + mark, s)
    for cmd in ("text", "mathrm", "mathbf", "mathit", "mathcal", "mathsf",
                "operatorname", "textbf", "textit", "emph"):
        s = _sub_cmd(s, cmd, 1, lambda a: a[0])

    # operators/functions that read fine as words
    for w in ("argmax", "argmin", "max", "min", "log",
              "ln", "exp", "det", "dim", "sup", "inf", "lim", "sin", "cos",
              "tan", "gcd", "mod", "Pr"):
        s = s.replace("\\" + w.replace(" ", "\\"), w)
    s = s.replace(r"\arg\max", "argmax").replace(r"\arg\min", "argmin")
    s = s.replace(r"\E", "E")

    # symbols + greek (longest first so \varepsilon beats \eta etc.)
    for k in sorted(_SYMBOLS, key=len, reverse=True):
        s = s.replace(k, _SYMBOLS[k])
    # (?![A-Za-z]) not \b: a following _ or ^ IS a word char, so \b would fail
    # on the very common \eta_t / \theta_t and leave "etaₜ" / "thetaₜ".
    for name in sorted(_GREEK, key=len, reverse=True):
        s = re.sub(r"\\" + name + r"(?![A-Za-z])", _GREEK[name], s)

    # spacing / sizing commands -> nothing (or a thin space)
    s = re.sub(r"\\(?:left|right|big|Big|bigg|Bigg|displaystyle|limits)\b", "", s)
    s = re.sub(r"\\[,;:!]", " ", s)
    s = s.replace(r"\quad", "  ").replace(r"\qquad", "    ")
    s = s.replace("\\{", "{").replace("\\}", "}").replace(r"\%", "%")

    s = _apply_scripts(s)

    # any surviving \command -> drop the backslash, keep the word
    s = re.sub(r"\\([A-Za-z]+)", r"\1", s)
    # leftover grouping braces
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    if tags:
        s = f"{s}   ({tags[-1]})"
    return s


# --------------------------------------------------------------------------- #
#  Inline markdown
# --------------------------------------------------------------------------- #

def _inline(text: str) -> str:
    stash: list[str] = []

    def keep(val: str) -> str:
        stash.append(val)
        return f"\x00{len(stash) - 1}\x00"

    # inline code — protect its contents from every other transform
    text = re.sub(r"`([^`]+)`", lambda m: keep(m.group(1)), text)
    # inline math $...$  (not $$, handled at block level)
    text = re.sub(r"(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)",
                  lambda m: keep(latex_to_text(m.group(1))), text)

    text = html.unescape(text)
    # images ![alt](url) -> alt (or a marker)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)",
                  lambda m: m.group(1) or "[image]", text)
    # links [text](url) -> text, keeping url only when it adds info
    def link(m):
        label, url = m.group(1), m.group(2).strip()
        url = re.sub(r'\s+"[^"]*"$', "", url)  # drop title
        if not label:
            return url
        if url.startswith("#") or url == label:
            return label
        return f"{label} ({url})"
    text = re.sub(r"\[([^\]]*)\]\(([^)]*)\)", link, text)
    # reference-style [text][ref] -> text
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    # autolinks <http...> and <email>
    text = re.sub(r"<((?:https?://|mailto:)[^>]+)>", r"\1", text)

    # emphasis / strong / strike — strip the markers, keep the words
    text = re.sub(r"\*\*\*([^*]+)\*\*\*", r"\1", text)
    text = re.sub(r"___([^_]+)___", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*(?!\w)", r"\1", text)
    text = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"\1", text)
    text = re.sub(r"~~([^~]+)~~", r"\1", text)

    # backslash escapes \* \_ \# etc.
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>~|])", r"\1", text)

    # single-pass restore (avoids O(spans × length) repeated .replace scans)
    if stash:
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


# --------------------------------------------------------------------------- #
#  Tables
# --------------------------------------------------------------------------- #

def _is_sep_row(line: str) -> bool:
    if "-" not in line:
        return False
    core = line.strip().strip("|")
    cells = [c.strip() for c in core.split("|")]
    # every cell must be a dash run (with optional : alignment) — no empties,
    # so a stray "||" line is never mistaken for a table separator.
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells)


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # split on unescaped pipes
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def _render_table(rows: list[list[str]], aligns: list[str]) -> list[str]:
    rows = [[_inline(c) for c in r] for r in rows]
    ncol = max(len(r) for r in rows)
    for r in rows:
        r += [""] * (ncol - len(r))
    widths = [max(len(r[i]) for r in rows) for i in range(ncol)]
    aligns += ["l"] * (ncol - len(aligns))

    def fmt(cell, w, a):
        if a == "r":
            return cell.rjust(w)
        if a == "c":
            return cell.center(w)
        return cell.ljust(w)

    out = []
    header, body = rows[0], rows[1:]
    out.append("  " + "   ".join(fmt(header[i], widths[i], aligns[i])
                                 for i in range(ncol)).rstrip())
    out.append("  " + "   ".join("─" * widths[i] for i in range(ncol)).rstrip())
    for r in body:
        out.append("  " + "   ".join(fmt(r[i], widths[i], aligns[i])
                                     for i in range(ncol)).rstrip())
    return out


# --------------------------------------------------------------------------- #
#  Block renderer
# --------------------------------------------------------------------------- #

_ATX = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_HR = re.compile(r"^\s{0,3}([-*_])(?:\s*\1){2,}\s*$")
_ULI = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_OLI = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_BULLETS = ["•", "◦", "▪", "·"]


def render(md: str, width: int = 88) -> str:
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    def blank():
        if out and out[-1] != "":
            out.append("")

    # strip a leading YAML front-matter block — but ONLY if it really looks like
    # YAML (has a `key:` line). A file that just opens with a `---` divider must
    # not have its first section eaten as "front matter".
    if lines and lines[0].strip() == "---":
        close = None
        for j in range(1, min(n, 80)):
            if lines[j].strip() in ("---", "..."):
                close = j
                break
        if close is not None and any(
                re.match(r"^[A-Za-z0-9_.\-]+\s*:(\s|$)", ln)
                for ln in lines[1:close]):
            lines = lines[close + 1:]
            n = len(lines)

    _last_i = -1
    while i < n:
        # forward-progress guard: every branch below must advance i before its
        # `continue`. A branch that forgets caused a runaway loop that ate all
        # RAM (the "---" hr bug) — fail loudly instead of freezing the machine.
        if i == _last_i:
            raise RuntimeError(
                f"mdrender stalled at line {i + 1}: {lines[i][:80]!r} "
                "(renderer bug — no forward progress)")
        _last_i = i

        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # fenced code block
        fence = re.match(r"^(\s*)(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker = fence.group(2)[0]
            body = []
            i += 1
            while i < n and not re.match(r"^\s*" + re.escape(marker) + r"{3,}\s*$",
                                         lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # closing fence
            blank()
            for b in body:
                out.append("    " + b)
            blank()
            continue

        # block math $$ ... $$
        if stripped.startswith("$$"):
            body = []
            # single-line $$...$$
            m = re.match(r"^\$\$(.*)\$\$$", stripped)
            if m and m.group(1).strip():
                body = [m.group(1)]
                i += 1
            else:
                buf = [stripped[2:]]
                i += 1
                while i < n and "$$" not in lines[i]:
                    buf.append(lines[i])
                    i += 1
                if i < n:
                    buf.append(lines[i].split("$$")[0])
                    i += 1
                body = buf
            joined = " ".join(x.strip() for x in body if x.strip())
            pretty = latex_to_text(joined)
            blank()
            if pretty:
                out.append("    " + pretty)
            blank()
            continue

        # horizontal rule
        if _HR.match(line):
            blank()
            out.append("─" * min(width if width else 60, 60))
            blank()
            i += 1
            continue

        # blank line
        if stripped == "":
            blank()
            i += 1
            continue

        # ATX heading
        m = _ATX.match(line)
        if m:
            level = len(m.group(1))
            txt = _inline(m.group(2))
            blank()
            if level == 1:
                out.append(txt.upper())
                out.append("═" * len(txt))
            elif level == 2:
                out.append(txt)
                out.append("─" * len(txt))
            else:
                out.append(("  " * (level - 3) if level > 3 else "") + txt + ":")
            blank()
            i += 1
            continue

        # setext heading (text underlined by === or ---)
        if (i + 1 < n and stripped and lines[i + 1].strip()
                and re.fullmatch(r"[=]{2,}", lines[i + 1].strip())):
            txt = _inline(stripped)
            blank(); out.append(txt.upper()); out.append("═" * len(txt)); blank()
            i += 2
            continue
        if (i + 1 < n and stripped and lines[i + 1].strip()
                and re.fullmatch(r"[-]{2,}", lines[i + 1].strip())
                and not _ULI.match(line)):
            txt = _inline(stripped)
            blank(); out.append(txt); out.append("─" * len(txt)); blank()
            i += 2
            continue

        # table: a header row followed by a separator row
        if "|" in line and i + 1 < n and _is_sep_row(lines[i + 1]):
            aligns = []
            for c in _split_row(lines[i + 1]):
                c = c.strip()
                if c.startswith(":") and c.endswith(":"):
                    aligns.append("c")
                elif c.endswith(":"):
                    aligns.append("r")
                else:
                    aligns.append("l")
            rows = [_split_row(line)]
            i += 2
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_split_row(lines[i]))
                i += 1
            blank()
            out.extend(_render_table(rows, aligns))
            blank()
            continue

        # blockquote (possibly nested)
        if re.match(r"^\s*>", line):
            quote = []
            while i < n and re.match(r"^\s*>", lines[i]):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            blank()
            inner = render("\n".join(quote), width - 2 if width else 0)
            for q in inner.rstrip("\n").split("\n"):
                out.append(("│ " + q).rstrip())
            blank()
            continue

        # list (unordered / ordered), grouped with nesting by indent
        if _ULI.match(line) or _OLI.match(line):
            blank()
            while i < n and (_ULI.match(lines[i]) or _OLI.match(lines[i])
                             or (lines[i].startswith(("    ", "\t"))
                                 and lines[i].strip())):
                cur = lines[i]
                mu, mo = _ULI.match(cur), _OLI.match(cur)
                if mu:
                    indent = len(mu.group(1).replace("\t", "    "))
                    depth = indent // 2 if indent else 0
                    bullet = _BULLETS[min(depth, len(_BULLETS) - 1)]
                    out.append("  " * (depth + 1) + f"{bullet} "
                               + _inline(mu.group(2)))
                elif mo:
                    indent = len(mo.group(1).replace("\t", "    "))
                    depth = indent // 2 if indent else 0
                    out.append("  " * (depth + 1) + f"{mo.group(2)}. "
                               + _inline(mo.group(3)))
                else:  # lazy continuation line of the previous item
                    out.append("      " + _inline(cur.strip()))
                i += 1
            blank()
            continue

        # paragraph — gather until a blank line or a block starter
        para = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (nxt == "" or _ATX.match(lines[i]) or _HR.match(lines[i])
                    or _ULI.match(lines[i]) or _OLI.match(lines[i])
                    or re.match(r"^\s*>", lines[i]) or nxt.startswith("$$")
                    or re.match(r"^(\s*)(`{3,}|~{3,})", lines[i])):
                break
            para.append(nxt)
            i += 1
        text = _inline(" ".join(para))
        blank()
        if width and width > 0:
            out.extend(textwrap.wrap(text, width=width) or [""])
        else:
            out.append(text)

    # collapse 3+ blank lines to 1, trim edges
    result = "\n".join(out)
    result = re.sub(r"\n{3,}", "\n\n", result).strip("\n")
    return result + "\n"


def render_file(path: str, width: int = 88) -> str:
    p = Path(path).expanduser()
    md = p.read_text(encoding="utf-8", errors="ignore")
    title = p.name
    bar = "═" * len(title)
    return f"{title}\n{bar}\n\n{render(md, width=width)}"
