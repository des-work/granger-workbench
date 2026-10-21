"""Field-guide / educational-module generator — `ultra guide new`.

The user authors a library of self-contained offline HTML "field guides"
(Workipedia, F:\\Guide Books): sidebar nav with live search, reading-progress
bar, font-size controls, and chapters anchored as <h2 id="chN"> — which is
also the contract the Workipedia Reference-Desk indexer splits on.

This generates a new module with all of that machinery pre-built and the
whole thing themed by any DESIGN PROFILE from the vault (tokens, fonts, and
the profile's signature shape as the brand mark), so a new guide starts at
"write the chapters", not "build the book".

    ultra guide new "Bee Keeping"                          # default styling
    ultra guide new "Bee Keeping" --style dark-academia    # any profile
    ultra guide new "Radio" --outline outline.txt --out "F:/Guide Books"
    ultra guide styles                                     # what's available

Outline file format (Parts optional):
    Part I: Foundations
      What a Radio Is
      Waves and Bands
    Part II: Practice
      Your First Receiver

Guarantees kept for Workipedia compatibility: single file, zero network
requests, chapters as <h2 id="ch1..">, works from file:// — after adding a
guide, re-run index-guides.mjs and the Reference Desk knows it.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from string import Template

from . import core

MUTED, PAPER, AMBER, RED = "#8fb8cf", "#eaf6ff", "#febc2e", "#ff6159"

DEFAULT_PROFILE = "golden-archive"

_DEFAULT_OUTLINE = [
    ("Part I — Foundations", ["Orientation", "Core Concepts", "The Toolkit"]),
    ("Part II — Practice", ["First Steps", "Common Failures & Fixes"]),
    ("Part III — Reference", ["Quick Reference", "Where to Go Deeper"]),
]


def _theme():
    from . import cliart
    from .ui import _aero_colors
    blue, green, _ = _aero_colors()
    return cliart, blue, green


# --------------------------------------------------------------------------- #
#  Profile plumbing — tokens, fonts, brand shape from the design vault
# --------------------------------------------------------------------------- #

def _profile(style_id: str) -> dict:
    """Resolve a profile (or bare style) id into everything the template
    needs. Falls back to sane defaults so the generator never dies."""
    from . import assets
    prof = assets.PROFILES.get(style_id)
    style = prof["style"] if prof else style_id
    s = assets.STYLES.get(style, assets.STYLES[
        assets.PROFILES[DEFAULT_PROFILE]["style"]])
    t = dict(s["tokens"])
    body, display = assets.STYLE_FONTS.get(style, ("Inter", "Inter"))
    shape = ""
    if prof:
        for sid in prof.get("shapes", []):
            svg = assets.SHAPES.get(sid, {}).get("svg", "")
            if svg:
                shape = re.sub(r"<svg ", '<svg class="logo" ', svg.strip(), 1)
                break
    if not shape:
        shape = ('<svg class="logo" viewBox="0 0 32 32" '
                 'xmlns="http://www.w3.org/2000/svg">'
                 '<circle cx="16" cy="16" r="12" fill="none" '
                 'stroke="currentColor" stroke-width="2.5"/></svg>')
    return {"tokens": t, "body": body, "display": display, "shape": shape,
            "label": (prof or {}).get("label", s.get("label", style)),
            "vibe": (prof or {}).get("vibe", ""), "style": style}


def _slug(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title).strip()
    return re.sub(r"[\s-]+", "_", s) or "Guide"


def parse_outline(text: str) -> list[tuple[str, list[str]]]:
    """'Part ...' lines open a part; other non-empty lines are chapters."""
    parts: list[tuple[str, list[str]]] = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("-*").strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"(?i)^part\b", line):
            parts.append((line, []))
        else:
            if not parts:
                parts.append(("", []))
            parts[-1][1].append(line)
    return [p for p in parts if p[1]] or list(_DEFAULT_OUTLINE)


# --------------------------------------------------------------------------- #
#  Chapter stubs — house-style components so every element has an example
# --------------------------------------------------------------------------- #

_CH_BODY = Template("""
<h2 id="ch$n">$n. $title</h2>
<p class="lead">One-paragraph promise of this chapter: what the reader can DO
after reading it that they couldn't before.</p>

<h3>$title — the idea</h3>
<p>Explain the concept in plain words first. Then the precise version. Keep
paragraphs short; this is a field guide, not a lecture.</p>

<div class="callout note"><b>Field note.</b> The thing practitioners know that
books forget to mention.</div>

<h3>$title — in practice</h3>
<ol class="steps">
  <li>First concrete action.</li>
  <li>Second action — with the <kbd>exact</kbd> command or tool named.</li>
  <li>How to verify it worked.</li>
</ol>

<div class="callout warn"><b>Watch out.</b> The mistake everyone makes once.</div>

<table>
  <thead><tr><th>Thing</th><th>When to use</th><th>Remember</th></tr></thead>
  <tbody>
    <tr><td>Option A</td><td>The common case</td><td>Default to this</td></tr>
    <tr><td>Option B</td><td>The exception</td><td>Costs more</td></tr>
  </tbody>
</table>
""")


def _chapters_html(outline: list[tuple[str, list[str]]]) -> str:
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    out, n = [], 0
    for pi, (part, chapters) in enumerate(outline):
        if part:
            pid = f"part{roman[pi % len(roman)]}"
            out.append(f'\n<h2 class="part" id="{pid}">{part}</h2>')
        for title in chapters:
            n += 1
            out.append(_CH_BODY.substitute(n=n, title=title))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
#  The template — same structural contract as the existing library:
#  #fx #progress #nav #navsearch #scrim #topbar #hamburger #wrap, h2 id="chN"
# --------------------------------------------------------------------------- #

_PAGE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<!-- Generated by Ultra-PC `ultra guide new` · profile: $profile_id
     Self-contained + offline. Chapters are <h2 id="chN"> — the Workipedia
     indexer splits on these; re-run index-guides.mjs after adding. -->
<style>
:root{
  --bg:$bg; --panel:$bg2; --surface:$surface; --ink:$text; --dim:$muted;
  --accent:$accent; --accent2:$accent2; --border:$border; --radius:$radius;
  --body-font:$body_font; --display-font:$display_font;
}
*{box-sizing:border-box} html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.65 var(--body-font);}
#fx{position:fixed;inset:0;z-index:-1;background:
  radial-gradient(at 80% 0%, color-mix(in srgb, var(--accent) 14%, transparent) 0%, transparent 55%),
  radial-gradient(at 10% 100%, color-mix(in srgb, var(--accent2) 10%, transparent) 0%, transparent 50%);}
#progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:99;
  background:linear-gradient(90deg,var(--accent2),var(--accent));}

/* ---- sidebar nav ---- */
#nav{position:fixed;top:0;left:0;bottom:0;width:280px;overflow-y:auto;
  background:var(--panel);border-right:1px solid var(--border);
  padding:18px 14px 40px;z-index:60;transition:transform .25s ease;}
#nav .brand{display:flex;gap:10px;align-items:center;margin-bottom:4px;}
#nav .logo{width:34px;height:34px;color:var(--accent);flex:none;}
#nav h1{font:700 15px/1.25 var(--display-font);letter-spacing:.06em;
  text-transform:uppercase;margin:0;color:var(--accent);}
#nav .sub{font-size:11.5px;color:var(--dim);margin:2px 0 14px;}
#navsearch{width:100%;padding:7px 10px;border-radius:calc(var(--radius)/2);
  border:1px solid var(--border);background:var(--surface);color:var(--ink);
  font:13px var(--body-font);margin-bottom:12px;}
#toc a{display:block;padding:5px 8px;border-radius:calc(var(--radius)/2);
  color:var(--ink);text-decoration:none;font-size:13.5px;}
#toc a:hover{background:color-mix(in srgb, var(--accent) 12%, transparent);}
#toc a.sub{padding-left:22px;font-size:12.5px;color:var(--dim);}
#toc .part{margin:14px 4px 4px;font:700 11px var(--body-font);
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent);}
#toc a.active{background:color-mix(in srgb, var(--accent) 18%, transparent);
  color:var(--accent);}
#scrim{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:55;
  opacity:0;pointer-events:none;transition:opacity .25s;}

/* ---- topbar ---- */
#topbar{position:fixed;top:0;left:280px;right:0;height:46px;z-index:50;
  display:flex;align-items:center;gap:10px;padding:0 16px;
  background:color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--border);}
#topbar button{background:var(--surface);border:1px solid var(--border);
  color:var(--ink);border-radius:calc(var(--radius)/2);padding:4px 10px;
  cursor:pointer;font:13px var(--body-font);}
#hamburger{display:none;}
#crumb{font-size:12.5px;color:var(--dim);overflow:hidden;white-space:nowrap;
  text-overflow:ellipsis;flex:1;}

/* ---- content ---- */
#wrap{max-width:840px;margin:0 auto;padding:76px 32px 120px;margin-left:280px;}
h2{font:700 26px/1.3 var(--display-font);color:var(--accent);
  margin:56px 0 12px;padding-top:14px;border-top:1px solid var(--border);}
h2.part{font-size:15px;letter-spacing:.2em;text-transform:uppercase;
  color:var(--dim);border-top:2px solid var(--accent);}
h3{font:600 18px/1.35 var(--display-font);margin:30px 0 8px;
  color:var(--accent2);}
p.lead{font-size:17.5px;color:var(--dim);}
a{color:var(--accent);}
kbd{background:var(--surface);border:1px solid var(--border);
  border-bottom-width:2px;border-radius:5px;padding:1px 6px;
  font:12.5px ui-monospace,Consolas,monospace;}
.callout{border-left:3px solid var(--accent);background:var(--panel);
  border-radius:calc(var(--radius)/2);padding:12px 14px;margin:16px 0;
  font-size:14.5px;}
.callout.warn{border-left-color:$warn;}
ol.steps li{margin:6px 0;}
table{border-collapse:collapse;width:100%;margin:18px 0;font-size:14px;}
th,td{border:1px solid var(--border);padding:8px 10px;text-align:left;}
th{background:var(--panel);color:var(--accent);
  font:600 12.5px var(--body-font);letter-spacing:.05em;
  text-transform:uppercase;}
tr:nth-child(even) td{background:color-mix(in srgb, var(--panel) 55%, transparent);}
.titleblock{margin:14px 0 8px;}
.titleblock h1{font:800 40px/1.15 var(--display-font);margin:0 0 6px;
  color:var(--accent);}
.titleblock .tag{color:var(--dim);font-size:15px;}

@media (max-width: 960px){
  #nav{transform:translateX(-100%);} body.navopen #nav{transform:none;}
  body.navopen #scrim{opacity:1;pointer-events:auto;}
  #topbar{left:0;} #wrap{margin-left:0;padding:70px 18px 90px;}
  #hamburger{display:block;}
}
@media print{
  #nav,#topbar,#progress,#fx,#scrim{display:none!important;}
  #wrap{margin:0;padding:0;max-width:none;}
  body{background:#fff;color:#000;}
}
</style>
</head>
<body>
<div id="fx"></div>
<div id="progress"></div>

<nav id="nav">
  <div class="brand">
    $brand_shape
    <h1>$title</h1>
  </div>
  <div class="sub">$subtitle</div>
  <input id="navsearch" type="search" placeholder="search chapters…"
         aria-label="Search chapters">
  <div id="toc"></div>
</nav>
<div id="scrim"></div>

<header id="topbar">
  <button id="hamburger" aria-label="Menu">☰</button>
  <div id="crumb">$title</div>
  <button id="fsdown" title="Smaller text">A−</button>
  <button id="fsup" title="Larger text">A+</button>
</header>

<main id="wrap">
  <div class="titleblock">
    <h1>$title</h1>
    <div class="tag">$subtitle &middot; $date</div>
  </div>

  <h2 id="how-to-read">How to read this guide</h2>
  <p class="lead">Two sentences on who this is for and the fastest path
  through it. Skimmers read the callouts and tables; students read in
  order.</p>

  $chapters
</main>

<script>
(function(){
  "use strict";
  var nav=document.getElementById("nav"), toc=document.getElementById("toc"),
      wrap=document.getElementById("wrap"), crumb=document.getElementById("crumb");

  /* build the TOC from h2 (chapters / .part groups) + h3 (subsections) */
  var links=[];
  wrap.querySelectorAll("h2,h3").forEach(function(h){
    if(!h.id) h.id=h.textContent.toLowerCase().replace(/[^a-z0-9]+/g,"-")
                    .replace(/^-|-$$/g,"");
    if(h.tagName==="H2" && h.classList.contains("part")){
      var g=document.createElement("div"); g.className="part";
      g.textContent=h.textContent; toc.appendChild(g); return;
    }
    var a=document.createElement("a");
    a.href="#"+h.id; a.textContent=h.textContent;
    if(h.tagName==="H3") a.className="sub";
    toc.appendChild(a); links.push({a:a,h:h});
  });

  /* live search filter */
  document.getElementById("navsearch").addEventListener("input",function(){
    var q=this.value.toLowerCase();
    toc.querySelectorAll("a").forEach(function(a){
      a.style.display=a.textContent.toLowerCase().indexOf(q)>-1?"":"none";});
  });

  /* reading progress + active chapter + breadcrumb */
  function onscroll(){
    var doc=document.documentElement,
        p=doc.scrollTop/(doc.scrollHeight-doc.clientHeight||1);
    document.getElementById("progress").style.width=(p*100).toFixed(2)+"%";
    var cur=null;
    for(var i=0;i<links.length;i++)
      if(links[i].h.getBoundingClientRect().top<90) cur=links[i];
    links.forEach(function(l){l.a.classList.toggle("active",l===cur);});
    if(cur) crumb.textContent=document.title+"  ·  "+cur.h.textContent;
  }
  addEventListener("scroll",onscroll,{passive:true}); onscroll();

  /* font size (persisted) */
  var fs=+(localStorage.getItem("guide-fs")||16);
  function setfs(v){fs=Math.min(22,Math.max(13,v));
    document.body.style.fontSize=fs+"px";
    localStorage.setItem("guide-fs",fs);}
  document.getElementById("fsup").onclick=function(){setfs(fs+1);};
  document.getElementById("fsdown").onclick=function(){setfs(fs-1);};
  setfs(fs);

  /* mobile nav */
  var scrim=document.getElementById("scrim");
  document.getElementById("hamburger").onclick=function(){
    document.body.classList.toggle("navopen");};
  scrim.onclick=function(){document.body.classList.remove("navopen");};
  toc.addEventListener("click",function(){
    document.body.classList.remove("navopen");});
})();
</script>
</body>
</html>
""")


def generate(title: str, style_id: str = DEFAULT_PROFILE,
             subtitle: str = "", outline_text: str = "",
             out_dir: str | Path = ".") -> Path:
    """Write <Title>_Guide.html themed by a design profile. Returns the path."""
    p = _profile(style_id)
    t = p["tokens"]
    outline = parse_outline(outline_text) if outline_text.strip() \
        else list(_DEFAULT_OUTLINE)
    html = _PAGE.substitute(
        title=title, subtitle=subtitle or f"A field guide · {p['label']}",
        profile_id=style_id, date=date.today().strftime("%B %Y"),
        bg=t["bg"], bg2=t["bg2"], surface=t["surface"], text=t["text"],
        muted=t["muted"], accent=t["accent"], accent2=t["accent2"],
        border=t["border"], radius=t.get("radius", "10px"),
        warn="#e3b341",
        body_font=f"'{p['body']}', 'Segoe UI', system-ui, sans-serif",
        display_font=f"'{p['display']}', 'Segoe UI', system-ui, sans-serif",
        brand_shape=p["shape"],
        chapters=_chapters_html(outline),
    )
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{_slug(title)}_Guide.html"
    i = 2
    while dest.exists():
        dest = out / f"{_slug(title)}_Guide_{i}.html"
        i += 1
    core.write_atomic(dest, html)
    return dest


# --------------------------------------------------------------------------- #
#  CLI — `ultra guide ...`
# --------------------------------------------------------------------------- #

def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() not in ("guide", "module", "guidebook"):
        return None
    ca, blue, green = _theme()
    rest = argv[1:]
    sub = rest[0].lower() if rest else "help"

    if sub in ("styles", "profiles", "list"):
        from . import assets
        print(ca.color("\n  ▸ guide styles — any design profile themes a "
                       "module", green))
        for k, v in assets.PROFILES.items():
            print(ca.color(f"    {k:<20}", PAPER)
                  + ca.color(v["vibe"][:72] + "…", MUTED))
        print(ca.color('\n    ultra guide new "<Title>" --style <profile>',
                       MUTED))
        return 0

    if sub == "new":
        args = rest[1:]
        title, style, out, outline_f, subtitle = None, DEFAULT_PROFILE, ".", None, ""
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--style" and i + 1 < len(args):
                style = args[i + 1]; i += 2
            elif a == "--out" and i + 1 < len(args):
                out = args[i + 1]; i += 2
            elif a == "--outline" and i + 1 < len(args):
                outline_f = args[i + 1]; i += 2
            elif a == "--subtitle" and i + 1 < len(args):
                subtitle = args[i + 1]; i += 2
            else:
                title = a if title is None else f"{title} {a}"; i += 1
        if not title:
            print('usage: ultra guide new "<Title>" [--style <profile>] '
                  '[--out <dir>] [--outline <file>] [--subtitle "<s>"]')
            return 2
        from . import assets
        if style not in assets.PROFILES and style not in assets.STYLES:
            print(ca.color(f"  ✕ no profile or style named '{style}' — "
                           "`ultra guide styles`", RED))
            return 1
        outline_text = ""
        if outline_f:
            fp = Path(outline_f).expanduser()
            if not fp.is_file():
                print(ca.color(f"  ✕ outline file not found: {fp}", RED))
                return 1
            outline_text = fp.read_text(encoding="utf-8")
        dest = generate(title, style, subtitle, outline_text, out)
        kb = dest.stat().st_size / 1024
        print()
        print(ca.color(f"  ✓ module scaffolded → {dest}  ({kb:.0f} KB)", green))
        print(ca.color(f"    profile: {style} · chapters stubbed with the "
                       "house components (callouts, steps, tables)", MUTED))
        print(ca.color("    Workipedia: chapters are <h2 id=\"chN\"> — drop "
                       "it in the library and re-run index-guides.mjs", MUTED))
        return 0

    print('usage: ultra guide new "<Title>" [--style <profile>] [--out <dir>]'
          ' [--outline <file>]   ·   ultra guide styles')
    return 0
