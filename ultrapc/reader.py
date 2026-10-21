"""Reader / Digest — read large PowerPoints and codebases CHEAPLY.

The point: don't feed raw .pptx/source files into a paid model. Ultra-PC extracts
the essence locally (clean slide text, code structure maps) — a fraction of the
tokens — and can even summarize with your LOCAL Ollama model so the assistant
reads a digest instead of the whole thing.

    python ultra.py read <deck.pptx>            # clean per-slide text
    python ultra.py read <deck.pptx> --outline  # just slide titles
    python ultra.py codemap <file|dir>          # structure: files + signatures
    python ultra.py digest <dir> [--out f.md]   # batch a folder -> one digest
    add --summarize to any of the above         # local-model summary (Ollama)

Stdlib-only for extraction (zipfile + ast); summaries reuse ultrapc/ai.py.
"""

from __future__ import annotations

import ast
import html
import re
import zipfile
import zlib
from pathlib import Path

from . import core

try:
    from .coderag import CODE_EXTS, SKIP_DIRS
except Exception:                              # keep working if coderag changes
    CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
                 ".c", ".h", ".cpp", ".cs", ".rb", ".php", ".sql", ".sh"}
    SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "dist", "build",
                 "__pycache__", ".next", "target", "vendor"}

# --------------------------------------------------------------------------- #
#  PowerPoint extraction (a .pptx is a zip of XML — no python-pptx needed)
# --------------------------------------------------------------------------- #

_T_RE = re.compile(r"<a:t>(.*?)</a:t>", re.S)
_P_RE = re.compile(r"<a:p>(.*?)</a:p>", re.S)
_SLIDE_RE = re.compile(r"ppt/slides/slide(\d+)\.xml$")
_NOTES_RE = re.compile(r"ppt/notesSlides/notesSlide(\d+)\.xml$")


def _para_lines(xml: str) -> list[str]:
    lines = []
    for para in _P_RE.findall(xml):
        txt = html.unescape("".join(_T_RE.findall(para))).strip()
        if txt:
            lines.append(txt)
    if not lines:                              # slides with odd structure
        txt = html.unescape(" ".join(_T_RE.findall(xml))).strip()
        if txt:
            lines = [txt]
    return lines


def pptx_slides(path: str, with_notes: bool = False) -> list[dict]:
    """Return [{n, title, body:[...], notes}] in slide order. Cheap + offline."""
    p = Path(path)
    slides: list[dict] = []
    with zipfile.ZipFile(p) as z:
        names = [(int(m.group(1)), n) for n in z.namelist()
                 if (m := _SLIDE_RE.search(n))]
        names.sort()
        notes_by_n: dict[int, str] = {}
        if with_notes:
            for n in z.namelist():
                m = _NOTES_RE.search(n)
                if m:
                    nl = _para_lines(z.read(n).decode("utf-8", "replace"))
                    notes_by_n[int(m.group(1))] = " ".join(nl)
        for idx, (num, name) in enumerate(names, 1):
            lines = _para_lines(z.read(name).decode("utf-8", "replace"))
            slides.append({"n": idx, "title": lines[0] if lines else "(untitled)",
                           "body": lines[1:], "notes": notes_by_n.get(num, "")})
    return slides


def pptx_to_text(path: str, outline: bool = False, with_notes: bool = False) -> str:
    slides = pptx_slides(path, with_notes)
    out = [f"# {Path(path).name}  ({len(slides)} slides)\n"]
    for s in slides:
        if outline:
            out.append(f"{s['n']:>3}. {s['title']}")
            continue
        out.append(f"\n── Slide {s['n']}: {s['title']} " + "─" * 8)
        for b in s["body"]:
            out.append(f"  • {b}")
        if with_notes and s["notes"]:
            out.append(f"  [notes] {s['notes']}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
#  Word (.docx) — also a zip of XML; no python-docx needed
# --------------------------------------------------------------------------- #

_WT = re.compile(r"<w:t[^>]*>(.*?)</w:t>", re.S)
_WP = re.compile(r"<w:p\b.*?</w:p>", re.S)
_WSTYLE = re.compile(r'<w:pStyle w:val="([^"]+)"')


def docx_to_text(path: str, outline: bool = False) -> str:
    with zipfile.ZipFile(path) as z:
        try:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
        except KeyError:
            return f"# {Path(path).name}\n(no document.xml — not a standard .docx)\n"
    out = [f"# {Path(path).name}\n"]
    for para in _WP.findall(xml):
        txt = html.unescape("".join(_WT.findall(para))).strip()
        if not txt:
            continue
        st = _WSTYLE.search(para)
        style = st.group(1) if st else ""
        if "Heading" in style or "Title" in style:
            m = re.search(r"\d", style)
            level = "#" * (int(m.group()) if m else 1)
            out.append(f"\n{level} {txt}")
        elif not outline:
            out.append(txt)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
#  Excel (.xlsx) — zip of XML; shared strings + sheet cells
# --------------------------------------------------------------------------- #

def xlsx_to_text(path: str, max_rows: int = 300) -> str:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            ss = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
            for si in re.findall(r"<si>(.*?)</si>", ss, re.S):
                shared.append(html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))))
        sheets = sorted(n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        out = [f"# {Path(path).name}  ({len(sheets)} sheet(s))"]
        for sh in sheets:
            xml = z.read(sh).decode("utf-8", "replace")
            out.append(f"\n## {sh.rsplit('/', 1)[-1]}")
            rows = re.findall(r"<row\b[^>]*>(.*?)</row>", xml, re.S)
            for row in rows[:max_rows]:
                cells = []
                for cm in re.finditer(r"<c\b([^>]*)>(.*?)</c>", row, re.S):
                    attrs, inner = cm.group(1), cm.group(2)
                    v = re.search(r"<v>(.*?)</v>", inner, re.S)
                    val = v.group(1) if v else ""
                    if 't="s"' in attrs and val.isdigit() and int(val) < len(shared):
                        val = shared[int(val)]
                    elif 't="inlineStr"' in attrs:
                        val = "".join(re.findall(r"<t[^>]*>(.*?)</t>", inner, re.S))
                    cells.append(html.unescape(val).strip())
                if any(cells):
                    out.append("  " + " | ".join(cells))
            if len(rows) > max_rows:
                out.append(f"  …(+{len(rows) - max_rows} more rows)")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
#  PDF — prefer pypdf/pdfminer if installed; robust stdlib fallback otherwise
# --------------------------------------------------------------------------- #

def _pdf_unescape(b: bytes) -> str:
    b = re.sub(rb"\\([nrtbf()\\])",
               lambda m: {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"",
                          b"f": b"", b"(": b"(", b")": b")", b"\\": b"\\"}[m.group(1)], b)
    return b.decode("latin-1", "replace")


def _pdf_stdlib(path: str) -> str:
    """Dependency-free extraction: inflate content streams, pull Tj/TJ strings.
    Works for many text PDFs; scanned/CID-font PDFs won't yield clean text."""
    data = Path(path).read_bytes()
    chunks: list[str] = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        raw = m.group(1)
        try:
            dec = zlib.decompress(raw)
        except Exception:
            dec = raw
        for tm in re.finditer(rb"\(((?:[^()\\]|\\.)*)\)\s*Tj", dec, re.S):
            chunks.append(_pdf_unescape(tm.group(1)))
        for am in re.finditer(rb"\[(.*?)\]\s*TJ", dec, re.S):
            parts = re.findall(rb"\(((?:[^()\\]|\\.)*)\)", am.group(1), re.S)
            chunks.append("".join(_pdf_unescape(p) for p in parts))
    text = "\n".join(c for c in chunks if c.strip())
    return text


def pdf_to_text(path: str) -> tuple[str, str]:
    """Return (text, method). Tries the best available extractor."""
    try:
        import pypdf
        r = pypdf.PdfReader(path)
        txt = "\n".join((pg.extract_text() or "") for pg in r.pages)
        if txt.strip():
            return txt, f"pypdf, {len(r.pages)} pages"
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_text
        txt = extract_text(path)
        if txt.strip():
            return txt, "pdfminer"
    except Exception:
        pass
    txt = _pdf_stdlib(path)
    if txt.strip():
        return txt, "stdlib (basic — install pypdf for higher fidelity)"
    return "", "NO TEXT (scanned/image-only or encrypted — needs OCR)"


def pdf_text(path: str) -> str:
    txt, method = pdf_to_text(path)
    head = f"# {Path(path).name}  [pdf via {method}]\n"
    return head + (txt if txt.strip() else "(no extractable text layer)\n")


# --------------------------------------------------------------------------- #
#  Plain text / CSV / Markdown
# --------------------------------------------------------------------------- #

def plain_text(path: str, max_chars: int = 200_000) -> str:
    t = Path(path).read_text(encoding="utf-8", errors="ignore")
    clipped = t[:max_chars]
    if len(t) > max_chars:
        clipped += f"\n…(truncated, {len(t) - max_chars:,} more chars)"
    return f"# {Path(path).name}\n{clipped}\n"


def markdown_text(path: str, width: int = 88) -> str:
    """Render markdown into clean, symbol-free readable text (the browser look)."""
    from . import mdrender
    return mdrender.render_file(path, width=width)


# --------------------------------------------------------------------------- #
#  Unified dispatcher
# --------------------------------------------------------------------------- #

DOC_EXTS = {".pptx", ".pptm", ".docx", ".pdf", ".xlsx", ".xlsm",
            ".csv", ".tsv", ".txt", ".md", ".markdown", ".mdown", ".mkd", ".rtf"}


def extract(path: str, outline: bool = False, notes: bool = False,
            raw: bool = False, width: int = 88) -> str:
    """Extract clean text from any supported document type. Raises on unsupported."""
    ext = Path(path).suffix.lower()
    if ext in (".pptx", ".pptm"):
        return pptx_to_text(path, outline=outline, with_notes=notes)
    if ext == ".docx":
        return docx_to_text(path, outline=outline)
    if ext == ".pdf":
        return pdf_text(path)
    if ext in (".xlsx", ".xlsm"):
        return xlsx_to_text(path)
    if ext in (".md", ".markdown", ".mdown", ".mkd") and not raw:
        # markdown reads as clean, symbol-free text by default (--raw for verbatim)
        return markdown_text(path, width=width)
    if ext in (".csv", ".tsv", ".txt", ".md", ".markdown", ".mdown", ".mkd", ".rtf"):
        return plain_text(path)
    raise ValueError(f"unsupported type '{ext}'")


# --------------------------------------------------------------------------- #
#  Code structure map (signatures only — skim a repo at ~5% the tokens)
# --------------------------------------------------------------------------- #

def _py_sigs(src: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out

    def emit(node, indent=0):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            kw = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            out.append((node.lineno, "  " * indent + f"{kw} {node.name}({', '.join(args)})"))
        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(b.id for b in node.bases if isinstance(b, ast.Name))
            out.append((node.lineno, "  " * indent + f"class {node.name}"
                        + (f"({bases})" if bases else "")))
            for c in node.body:
                if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    emit(c, indent + 1)
    for node in tree.body:
        emit(node)
    return out


_DECL_RES = [
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?"
               r"(class|interface|struct|enum|trait|type|record)\s+\w+"),
    re.compile(r"^\s*(?:export\s+)?(?:public|private|protected|static|async|"
               r"func|function|fn|def|sub|proc)\s+[\w<>\[\]*&]+\s*[\w(]"),
    re.compile(r"^\s*(?:export\s+)?const\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
    re.compile(r"^\s*\w[\w<>\[\], *&]*\s+\w+\s*\([^;{]*\)\s*\{"),   # C/Java/Go methods
]


def _generic_sigs(src: str, cap: int = 60) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for i, line in enumerate(src.splitlines(), 1):
        if len(line) > 160:
            continue
        if any(r.search(line) for r in _DECL_RES):
            out.append((i, line.strip()[:120]))
            if len(out) >= cap:
                break
    return out


def code_signatures(path: str) -> list[tuple[int, str]]:
    p = Path(path)
    try:
        src = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    return _py_sigs(src) if p.suffix.lower() == ".py" else _generic_sigs(src)


def code_map(target: str, per_file: int = 40) -> str:
    """Structure map for a file or directory: path · line count · signatures."""
    p = Path(target).expanduser()
    files = [p] if p.is_file() else [
        f for f in sorted(p.rglob("*"))
        if f.is_file() and f.suffix.lower() in CODE_EXTS
        and not any(part in SKIP_DIRS for part in f.parts)]
    root = p if p.is_dir() else p.parent
    out, total_lines, total_files = [], 0, 0
    for f in files:
        try:
            n_lines = sum(1 for _ in f.open("r", encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        total_lines += n_lines
        total_files += 1
        sigs = code_signatures(str(f))
        rel = f.relative_to(root) if root in f.parents or root == f.parent else f.name
        out.append(f"\n▸ {rel}  ({n_lines} lines, {len(sigs)} defs)")
        for ln, sig in sigs[:per_file]:
            out.append(f"    {ln:>5}  {sig}")
        if len(sigs) > per_file:
            out.append(f"    …(+{len(sigs) - per_file} more)")
    header = (f"# code map: {p}\n# {total_files} files, {total_lines:,} lines "
              f"total — signatures only\n")
    return header + "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
#  Optional local-model summary (reuses Ollama; map-reduce for big inputs)
# --------------------------------------------------------------------------- #

def summarize_local(text: str, kind: str = "document") -> str | None:
    from . import ai
    if not ai.available():
        return None
    model = ai.default_model()
    if not model:
        return None

    def one(t: str, instr: str) -> str:
        msg = [{"role": "user", "content": f"{instr}\n\n{t}"}]
        return "".join(ai.chat_stream(model, msg)).strip()

    instr = (f"Summarize this {kind} as concise bullet points — key facts, "
             f"structure, and any action items. Be faithful; do not invent.")
    if len(text) <= 11000:
        return one(text, instr)
    # map-reduce for large inputs so nothing is dropped
    parts, i = [], 0
    while i < len(text) and len(parts) < 12:
        chunk = text[i:i + 9000]
        parts.append(one(chunk, "Summarize this section as tight bullet points:"))
        i += 9000
    combined = "\n".join(parts)
    return one(combined, "Merge these section summaries into one clean summary "
                         "with clear sections and no repetition:")


# --------------------------------------------------------------------------- #
#  Commands
# --------------------------------------------------------------------------- #

def _est_tokens(chars: int) -> int:
    return chars // 4


def _emit(text: str, out: str | None, summarize: bool, kind: str) -> int:
    if summarize:
        s = summarize_local(text, kind)
        if s is None:
            print("(local model unavailable — printing raw extract instead)\n")
        else:
            text = f"{text}\n\n===== LOCAL SUMMARY =====\n{s}\n"
    if out:
        Path(out).expanduser().write_text(text, encoding="utf-8")
        print(f"Wrote {len(text):,} chars (~{_est_tokens(len(text)):,} tokens) -> {out}")
    else:
        print(text)
    return 0


def cmd_read(path: str, outline=False, notes=False, out=None, summarize=False,
             raw=False, width=88) -> int:
    p = Path(path).expanduser()
    if not p.exists():
        print(f"Not found: {p}"); return 1
    ext = p.suffix.lower()
    # DOC_EXTS wins over CODE_EXTS: coderag counts .md/.html as indexable
    # "code", but `read` on a document should read it, not codemap it.
    if ext in CODE_EXTS and ext not in DOC_EXTS:
        print(f"'{p.name}' is code — mapping its structure instead:\n")
        return cmd_codemap(str(p), out=out, summarize=summarize)
    if ext not in DOC_EXTS:
        print(f"Unsupported type '{ext}'. Supported: "
              f"{', '.join(sorted(DOC_EXTS))} (or code via codemap)."); return 2
    try:
        text = extract(str(p), outline=outline, notes=notes, raw=raw, width=width)
    except Exception as exc:
        print(f"Could not read {p.name}: {type(exc).__name__}: {exc}"); return 1
    return _emit(text, out, summarize, "document")


def cmd_md(path: str, out=None, summarize=False, width=88, raw=False) -> int:
    """Render a markdown file to clean readable text (no #, *, `, |, $$ noise)."""
    p = Path(path).expanduser()
    if not p.exists():
        print(f"Not found: {p}"); return 1
    if raw:
        return _emit(plain_text(str(p)), out, summarize, "document")
    try:
        text = markdown_text(str(p), width=width)
    except Exception as exc:
        print(f"Could not render {p.name}: {type(exc).__name__}: {exc}"); return 1
    return _emit(text, out, summarize, "document")


def cmd_codemap(target: str, out=None, summarize=False) -> int:
    p = Path(target).expanduser()
    if not p.exists():
        print(f"Not found: {p}"); return 1
    text = code_map(str(p))
    return _emit(text, out, summarize, "codebase structure")


def cmd_digest(folder: str, out=None, summarize=False, notes=False) -> int:
    """Batch a folder: extract every supported document + a code map of any code,
    and print a clear report of what was read, what was skipped, and the token
    savings — so you can trust nothing was silently missed."""
    d = Path(folder).expanduser()
    if not d.is_dir():
        print(f"Not a folder: {d}"); return 1

    docs = [f for f in sorted(d.rglob("*"))
            if f.is_file() and f.suffix.lower() in DOC_EXTS
            and not any(x in SKIP_DIRS for x in f.parts)]
    code_files = [f for f in d.rglob("*")
                  if f.is_file() and f.suffix.lower() in CODE_EXTS
                  and not any(x in SKIP_DIRS for x in f.parts)]

    parts = [f"# DIGEST of {d}"]
    read_ok, skipped, raw_bytes = [], [], 0
    for f in docs:
        try:
            raw_bytes += f.stat().st_size
        except OSError:
            pass
        try:
            parts.append("\n" + extract(str(f), notes=notes))
            read_ok.append(f)
        except Exception as exc:
            skipped.append((f.name, str(exc)))
            parts.append(f"\n# {f.name}: (skipped — {exc})\n")
    if code_files:
        parts.append("\n" + code_map(str(d)))

    text = "\n".join(parts)

    # ---- confidence report ---------------------------------------------- #
    from collections import Counter
    by_type = Counter(f.suffix.lower() for f in read_ok)
    print("── Digest report " + "─" * 40)
    print(f"  Documents read : {len(read_ok)}  " +
          " ".join(f"{ext}:{n}" for ext, n in sorted(by_type.items())))
    print(f"  Code files     : {len(code_files)} (mapped to signatures)")
    if skipped:
        print(f"  Skipped        : {len(skipped)}")
        for name, why in skipped:
            print(f"     ! {name}: {why[:70]}")
    else:
        print("  Skipped        : 0")
    digest_tokens = _est_tokens(len(text))
    if raw_bytes:
        print(f"  Size           : {raw_bytes/1e6:.1f} MB of source "
              f"-> ~{digest_tokens:,} tokens of digest")
    print("─" * 56)
    print()
    return _emit(text, out, summarize, "collection of documents and code")


# --------------------------------------------------------------------------- #
#  Menu + dispatch
# --------------------------------------------------------------------------- #

def _tool_read(ctx=None) -> None:
    from . import ui
    ui.title_bar("Reader — read a document cheaply")
    f = ui.ask_open_file("Choose a document",
                         [("Documents", "*.pptx *.pptm *.docx *.pdf *.xlsx *.xlsm "
                                        "*.csv *.tsv *.txt *.md"),
                          ("All files", "*.*")])
    if not f:
        ui.pause(); return
    outline = ui.ask_yesno("Outline only (titles/headings)?")
    print()
    cmd_read(f, outline=outline)
    ui.pause()


def _tool_md(ctx=None) -> None:
    from . import ui
    ui.title_bar("Markdown — read a .md file as clean text")
    f = ui.ask_open_file("Choose a markdown file",
                         [("Markdown", "*.md *.markdown *.mdown *.mkd"),
                          ("All files", "*.*")])
    if not f:
        ui.pause(); return
    print()
    cmd_md(f)
    ui.pause()


def _tool_codemap(ctx=None) -> None:
    from . import ui
    ui.title_bar("Reader — map a codebase")
    d = ui.ask_directory("Choose a code folder")
    if not d:
        ui.pause(); return
    print()
    cmd_codemap(d)
    ui.pause()


def _tool_digest(ctx=None) -> None:
    from . import ui
    ui.title_bar("Reader — digest a folder (decks + code)")
    d = ui.ask_directory("Choose a folder")
    if not d:
        ui.pause(); return
    summ = ui.ask_yesno("Also summarize with your local AI? (slower)")
    out = ui.ask_save_file("Save digest as", ".md")
    print()
    cmd_digest(d, out=out or None, summarize=summ)
    ui.pause()


def register() -> core.Category:
    cat = core.Category("reader", "Reader / Digest (read files cheaply)")
    cat.add("read", "Read a document (pptx/docx/pdf/xlsx/txt)", _tool_read)
    cat.add("md", "Markdown -> clean readable text", _tool_md)
    cat.add("codemap", "Map a codebase (structure only)", _tool_codemap)
    cat.add("digest", "Digest a folder (docs + code)", _tool_digest)
    try:
        from . import datatools, transcribe
        datatools.register_tool(cat)
        transcribe.register_tool(cat)
    except Exception:
        pass
    return cat


def _parse_flags(rest: list[str]) -> tuple[list[str], dict]:
    flags = {"outline": False, "notes": False, "summarize": False, "out": None,
             "raw": False, "width": 88}
    pos = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in ("--outline", "-o"):
            flags["outline"] = True
        elif a == "--notes":
            flags["notes"] = True
        elif a in ("--summarize", "-s"):
            flags["summarize"] = True
        elif a == "--raw":
            flags["raw"] = True
        elif a in ("--nowrap", "--no-wrap"):
            flags["width"] = 0
        elif a in ("--width", "-w") and i + 1 < len(rest):
            try:
                flags["width"] = int(rest[i + 1])
            except ValueError:
                pass
            i += 1
        elif a == "--out" and i + 1 < len(rest):
            flags["out"] = rest[i + 1]; i += 1
        else:
            pos.append(a)
        i += 1
    return pos, flags


def handle(argv: list[str]) -> int | None:
    if not argv:
        return None
    cmd = argv[0].lower()
    pos, f = _parse_flags(argv[1:])
    if cmd in ("md", "markdown", "render"):
        if not pos:
            print("usage: md <file.md> [--width N | --nowrap] [--raw] "
                  "[--summarize] [--out f]")
            return 2
        return cmd_md(pos[0], out=f["out"], summarize=f["summarize"],
                      width=f["width"], raw=f["raw"])
    if cmd == "read":
        if not pos:
            print("usage: read <file.pptx|docx|pdf|xlsx|csv|txt|md> "
                  "[--outline] [--notes] [--raw] [--width N] [--summarize] [--out f]")
            return 2
        return cmd_read(pos[0], outline=f["outline"], notes=f["notes"],
                        out=f["out"], summarize=f["summarize"],
                        raw=f["raw"], width=f["width"])
    if cmd in ("codemap", "map"):
        if not pos:
            print("usage: codemap <file|dir> [--summarize] [--out f]"); return 2
        return cmd_codemap(pos[0], out=f["out"], summarize=f["summarize"])
    if cmd == "digest":
        if not pos:
            print("usage: digest <dir> [--notes] [--summarize] [--out f]"); return 2
        return cmd_digest(pos[0], out=f["out"], summarize=f["summarize"],
                          notes=f["notes"])
    return None
