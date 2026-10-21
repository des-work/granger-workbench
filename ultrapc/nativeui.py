"""Native UI toolkit — the design vault for DESKTOP apps (tkinter/PIL), not the
web. tkinter can't render CSS/SVG, so real depth (glass, shadows, gel buttons,
gradients, animated splashes) has to be drawn with PIL. These generators do that
and are STYLE-AWARE: they pull colors from the design vault's `assets.STYLES`, so
the same code themes a window as frutiger-aero, cyberpunk, golden-archive, etc.

    from ultrapc import nativeui as nui
    nui.Card(parent, style="cyberpunk")          # a glass panel with depth
    nui.GelButton(parent, "Go", cmd, style=...)  # glossy button
    nui.NeonButton(parent, "Run", cmd, style=...)# outline-glow button
    nui.HeaderBar(root, style=...)               # title bar
    nui.ProgressBar(parent, style=...).set(.6)   # gradient progress bar
    nui.Toggle(parent, style=...)                # on/off switch
    nui.Chip(parent, "beta", style=...)          # pill badge
    nui.StatusDot(parent, "ok", style=...)       # glowing status light
    nui.texture("scanlines", 800, 500, style)    # themed backdrop textures
    nui.ramp("#2b8fd6", 7)                       # tint→shade color ramp
    nui.run_splash(root, on_done, "My App", "subtitle", style=...)
    nui.preview("cyberpunk", "look.png")         # render a static look-preview

Textures (`nui.texture(kind, w, h, style)` or call directly): grain, brushed,
carbon, scanlines, halftone, stripes, mesh, starfield, paper — plus
`vignette(img)` to finish any backdrop.

Stdlib + Pillow (+ numpy if present, for faster gradients/noise).
"""

from __future__ import annotations

import tkinter as tk

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk

try:
    import numpy as np
    _NP = True
except Exception:
    _NP = False

FONT = "Segoe UI"


# --------------------------------------------------------------------------- #
#  Color / token plumbing — pulls from the design vault's styles
# --------------------------------------------------------------------------- #

# Built-in fallback so this module is fully standalone (copy it into any project
# without the rest of Ultra-PC). If the design vault is importable, its full set
# of styles is used instead.
_FALLBACK = {
    "frutiger-aero": {"bg": "#ceecff", "bg2": "#eaf6ff", "surface": "#ffffff",
        "accent": "#257dbc", "accent2": "#96cd6e", "text": "#0b3c5d",
        "muted": "#4a7fa5", "border": "#9fd0f0", "radius": "16px"},
    "cyberpunk": {"bg": "#0d0221", "bg2": "#01012b", "surface": "#12082e",
        "accent": "#05d9e8", "accent2": "#ff2a6d", "text": "#d1f7ff",
        "muted": "#6b7fb3", "border": "#05d9e8", "radius": "10px"},
    "pastel": {"bg": "#fff0f6", "bg2": "#f3e8ff", "surface": "#ffffff",
        "accent": "#d664a0", "accent2": "#a78bfa", "text": "#5b4a63",
        "muted": "#807287", "border": "#f3d9e8", "radius": "20px"},
    "mono": {"bg": "#0a0a0a", "bg2": "#161616", "surface": "#161616",
        "accent": "#ffffff", "accent2": "#a3a3a3", "text": "#f5f5f5",
        "muted": "#737373", "border": "#2e2e2e", "radius": "0px"},
    "nordic": {"bg": "#2e3440", "bg2": "#3b4252", "surface": "#3b4252",
        "accent": "#88c0d0", "accent2": "#a3be8c", "text": "#eceff4",
        "muted": "#9aa4b8", "border": "#4c566a", "radius": "10px"},
}


def tokens(style: str = "frutiger-aero") -> dict:
    """Color tokens for a style — from the design vault if available, else a
    built-in fallback set so this module works standalone."""
    try:
        from . import assets
        return assets.STYLES.get(style, assets.STYLES["frutiger-aero"])["tokens"]
    except Exception:
        return _FALLBACK.get(style, _FALLBACK["frutiger-aero"])


def decisions(style="frutiger-aero") -> dict:
    """Use the same material and motion decisions as the web kit."""
    try:
        from . import assets
        return assets.EXEC.get(style, assets.EXEC["frutiger-aero"])
    except ImportError:
        # Keep the documented standalone use without homogenising its styles.
        matte = style == "mono"
        return {"gloss": 0 if matte else 3 if style == "frutiger-aero" else 1,
                "elevation": "hard" if matte else "glow" if style == "cyberpunk" else "soft",
                "forbid": ["gradient", "radius"] if matte else [], "border": 1}


def _gloss(style, control=False):
    e = decisions(style)
    if "gradient" in e["forbid"] or "bevel" in e["forbid"]:
        return 0
    # The Golden Archive profile reserves polish for the gold, never the void.
    if style == "golden-archive":
        return 2 if control else 0
    return e["gloss"]


def _radius(style, h):
    return min(max(0, _px(tokens(style).get("radius"), 0)), max(0, h // 2))


def _material(w, h, base, style, control=False, hover=False):
    gloss = _gloss(style, control)
    if not gloss:
        return Image.new("RGBA", (w, h), (*_rgb(base), 255))
    amount = (0.06, 0.06, 0.18, 0.28)[gloss] + (0.04 if hover else 0)
    return vgrad(w, h, lighten(base, amount), darken(base, amount)).convert("RGBA")


def _rgb(h) -> tuple[int, int, int]:
    if isinstance(h, (tuple, list)):
        return tuple(h[:3])
    h = str(h).lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lighten(c, t=0.2):
    return _mix(_rgb(c), (255, 255, 255), t)


def darken(c, t=0.2):
    return _mix(_rgb(c), (0, 0, 0), t)


def _px(v, default=16) -> int:
    try:
        return int(str(v).replace("px", "").strip())
    except (TypeError, ValueError):
        return default


def _is_dark(c) -> bool:
    r, g, b = _rgb(c)
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128


# --------------------------------------------------------------------------- #
#  Gradients + shapes
# --------------------------------------------------------------------------- #

def vgrad(w, h, c1, c2) -> "Image.Image":
    c1, c2 = _rgb(c1), _rgb(c2)
    if _NP:
        t = np.linspace(0, 1, h)[:, None]
        rows = np.array(c1, float) * (1 - t) + np.array(c2, float) * t
        return Image.fromarray(np.repeat(rows[:, None, :], w, 1).astype("uint8"), "RGB")
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=_mix(c1, c2, t))
    return img


def hgrad(w, h, c1, c2) -> "Image.Image":
    c1, c2 = _rgb(c1), _rgb(c2)
    if _NP:
        t = np.linspace(0, 1, w)[None, :, None]
        cols = np.array(c1, float) * (1 - t) + np.array(c2, float) * t
        return Image.fromarray(np.repeat(cols, h, 0).astype("uint8"), "RGB")
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for x in range(w):
        d.line([(x, 0), (x, h)], fill=_mix(c1, c2, x / max(1, w - 1)))
    return img


def rounded_mask(w, h, radius) -> "Image.Image":
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    return m


def _hex(c) -> str:
    r, g, b = _rgb(c)
    return f"#{r:02x}{g:02x}{b:02x}"


def ramp(color, n: int = 5, spread: float = 0.75) -> list[str]:
    """A tint→shade ramp around one color: n hexes, lightest first.  Reach for
    this instead of hand-picking 'a lighter version of the accent'."""
    base = _rgb(color)
    out = []
    for i in range(n):
        t = (i / max(1, n - 1)) * 2 - 1          # -1 … +1
        c = _mix(base, (255, 255, 255), -t * spread) if t < 0 else \
            _mix(base, (0, 0, 0), t * spread)
        out.append(_hex(c))
    return out


def _rel_lum(c) -> float:
    """WCAG relative luminance."""
    def chan(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (_rgb(c))
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast(c1, c2) -> float:
    """WCAG contrast ratio between two colors (1..21).  AA body text needs
    4.5, AAA needs 7 — check, don't guess."""
    l1, l2 = _rel_lum(c1), _rel_lum(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def on_color(bg) -> str:
    """The readable ink for any background: black or white, whichever wins."""
    return "#000000" if contrast("#000000", bg) >= contrast("#ffffff", bg) \
        else "#ffffff"


def ensure_contrast(fg, bg, ratio: float = 4.5) -> str:
    """Nudge fg toward black/white until it clears `ratio` against bg —
    keeps the hue where possible instead of slamming to pure ink."""
    if contrast(fg, bg) >= ratio:
        return _hex(_rgb(fg))
    target = _rgb(on_color(bg))
    c = _rgb(fg)
    for _ in range(20):
        c = _mix(c, target, 0.12)
        if contrast(c, bg) >= ratio:
            return _hex(c)
    return _hex(target)


def harmony(color) -> dict:
    """Color-wheel relatives of one color (all hex): complement, two analogous,
    two triadic — for accents that go together without guessing."""
    import colorsys
    r, g, b = (v / 255 for v in _rgb(color))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    def rot(deg):
        rr, gg, bb = colorsys.hsv_to_rgb((h + deg / 360) % 1.0, s, v)
        return _hex((int(rr * 255), int(gg * 255), int(bb * 255)))
    return {"base": _hex(_rgb(color)), "complement": rot(180),
            "analogous": [rot(-30), rot(30)], "triadic": [rot(120), rot(240)]}


# --------------------------------------------------------------------------- #
#  Textures — themed backdrops with real surface character (not flat gradients)
# --------------------------------------------------------------------------- #

def _noise_img(w, h, strength=18, seed=7) -> "Image.Image":
    """Monochrome noise layer (L mode, mid-grey ± strength)."""
    if _NP:
        rng = np.random.RandomState(seed)
        arr = rng.randint(128 - strength, 128 + strength + 1, (h, w), "uint8")
        return Image.fromarray(arr, "L")
    import random as _r
    rnd = _r.Random(seed)
    img = Image.new("L", (w, h), 128)
    px = img.load()
    for y in range(0, h, 2):                       # sparse fallback, still textured
        for x in range(0, w, 2):
            px[x, y] = 128 + rnd.randint(-strength, strength)
    return img


def grain(w, h, style="frutiger-aero", strength=0.16) -> "Image.Image":
    """Film grain over the style's bg gradient — the native twin of the web
    vault's grain-overlay: kills flat-gradient banding, adds tooth."""
    t = tokens(style)
    base = vgrad(w, h, t["bg"], t["bg2"])
    noise = _noise_img(w, h).convert("RGB")
    return Image.blend(base, noise, strength)


def brushed(w, h, style="frutiger-aero") -> "Image.Image":
    """Brushed-metal: horizontal noise streaks over a vertical sheen gradient."""
    t = tokens(style)
    dark = _is_dark(t["surface"])
    a = lighten(t["surface"], .10 if dark else .04)
    b = darken(t["surface"], .25)
    base = vgrad(w, h, a, b)
    streaks = _noise_img(w, h, 26).resize((max(1, w // 6), h)).resize((w, h))
    streaks = streaks.filter(ImageFilter.GaussianBlur(0.6)).convert("RGB")
    img = Image.blend(base, streaks, 0.22)
    sheen = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sheen).ellipse([-w * .3, -h * .8, w * 1.3, h * .55], fill=46)
    return Image.composite(lighten_img(img, .16), img,
                           sheen.filter(ImageFilter.GaussianBlur(h // 6 or 1)))


def lighten_img(img: "Image.Image", t: float) -> "Image.Image":
    from PIL import ImageEnhance
    return ImageEnhance.Brightness(img).enhance(1 + t)


def carbon(w, h, style="mono", cell: int = 14) -> "Image.Image":
    """Carbon-fiber weave: alternating light/dark half-cells, tiled."""
    t = tokens(style)
    lo, hi = darken(t["surface"], .45), lighten(t["surface"], .08)
    tile = Image.new("RGB", (cell * 2, cell * 2), lo)
    d = ImageDraw.Draw(tile)
    g = _mix(_rgb(lo), _rgb(hi), .5)
    for ox, oy in ((0, 0), (cell, cell)):
        d.rectangle([ox, oy, ox + cell - 2, oy + cell - 2], fill=hi)
        d.rectangle([ox, oy + cell // 2, ox + cell - 2, oy + cell - 2], fill=g)
    tile = tile.filter(ImageFilter.GaussianBlur(0.7))
    img = Image.new("RGB", (w, h))
    for y in range(0, h, cell * 2):
        for x in range(0, w, cell * 2):
            img.paste(tile, (x, y))
    return img


def scanlines(w, h, style="cyberpunk", gap: int = 3) -> "Image.Image":
    """CRT scanlines + phosphor glow at the top — terminals, HUDs, retro-tech."""
    t = tokens(style)
    img = vgrad(w, h, t["bg"], t["bg2"]).convert("RGBA")
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([-w * .25, -h * .7, w * 1.25, h * .4],
                                 fill=(*_rgb(t["accent"]), 38))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(h // 8 or 1)))
    lines = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    for y in range(0, h, gap):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 64))
    img.alpha_composite(lines)
    return vignette(img.convert("RGB"), 0.25)


def halftone(w, h, style="frutiger-aero", cell: int = 12) -> "Image.Image":
    """Print-style dot grid that fades down the page."""
    t = tokens(style)
    img = vgrad(w, h, t["bg"], t["bg2"]).convert("RGBA")
    dots = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(dots)
    ink = _rgb(t["accent"])
    for gy, y in enumerate(range(cell // 2, h, cell)):
        r = max(0.6, (1 - y / h) * cell * 0.36)
        for x in range(cell // 2 + (gy % 2) * cell // 2, w, cell):
            d.ellipse([x - r, y - r, x + r, y + r], fill=(*ink, 46))
    img.alpha_composite(dots)
    return img.convert("RGB")


def stripes(w, h, style="frutiger-aero", width: int = 26) -> "Image.Image":
    """Soft 45° diagonal stripes in the style's surface tones."""
    t = tokens(style)
    big = int((w + h) * 1.5)
    tile = Image.new("RGB", (big, big), t["bg"])
    d = ImageDraw.Draw(tile)
    alt = lighten(t["bg"], .05) if _is_dark(t["bg"]) else darken(t["bg"], .04)
    for x in range(0, big, width * 2):
        d.rectangle([x, 0, x + width, big], fill=alt)
    tile = tile.rotate(45, expand=False)
    return tile.crop(((big - w) // 2, (big - h) // 2,
                      (big + w) // 2, (big + h) // 2))


def mesh(w, h, style="frutiger-aero", seed: int = 5) -> "Image.Image":
    """Multi-point mesh gradient — the trendy blurry-blob hero backdrop, drawn
    from the style's accent family instead of hand-picked colors."""
    import random as _r
    t = tokens(style)
    rnd = _r.Random(seed)
    img = vgrad(w, h, t["bg"], t["bg2"]).convert("RGBA")
    cols = [t["accent"], t["accent2"], harmony(t["accent"])["analogous"][0],
            t["accent"]]
    blobs = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(blobs)
    for c in cols:
        cx, cy = rnd.randint(0, w), rnd.randint(0, h)
        rr = int(min(w, h) * rnd.uniform(.30, .55))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(*_rgb(c), 52))
    img.alpha_composite(blobs.filter(ImageFilter.GaussianBlur(min(w, h) // 7 or 1)))
    return img.convert("RGB")


def starfield(w, h, style="golden-archive", seed: int = 11) -> "Image.Image":
    """Deep-space backdrop (as shipped in the Ultra Archive): bg gradient,
    accent-tinted nebula blobs, a few hundred stars, the bright ones glowing."""
    import random as _r
    t = tokens(style)
    rnd = _r.Random(seed)
    img = vgrad(w, h, darken(t["bg"], .3), t["bg2"]).convert("RGBA")
    neb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neb)
    for c, a in ((t["accent"], 26), (t["accent2"], 20), (t["accent"], 14)):
        cx, cy = rnd.randint(0, w), rnd.randint(0, h)
        rr = int(min(w, h) * rnd.uniform(.28, .5))
        nd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(*_rgb(c), a))
    img.alpha_composite(neb.filter(ImageFilter.GaussianBlur(min(w, h) // 8 or 1)))
    d = ImageDraw.Draw(img)
    warm = _rgb(t["accent"])
    for _ in range(max(60, w * h // 3800)):
        x, y = rnd.randint(0, w - 1), rnd.randint(0, h - 1)
        b = rnd.randint(70, 220)
        col = _mix((b, b, min(255, b + 20)), warm, .5) if rnd.random() < .22 \
            else (b, b, min(255, b + 20))
        if rnd.random() < .08:
            glow = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse([6, 6, 12, 12], fill=(*col, 180))
            img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(3)),
                                (x - 9, y - 9))
            d.point((x, y), fill=(255, 255, 255, 255))
        else:
            d.point((x, y), fill=(*col, 255))
    return img.convert("RGB")


def paper(w, h, style="pastel") -> "Image.Image":
    """Light paper: warm base, fine fiber noise, a whisper of vignette."""
    t = tokens(style)
    base = vgrad(w, h, lighten(t["bg"], .04), t["bg"])
    fib = _noise_img(w, h, 10, seed=3).filter(
        ImageFilter.GaussianBlur(0.4)).convert("RGB")
    return vignette(Image.blend(base, fib, 0.10), 0.12)


def vignette(img: "Image.Image", strength: float = 0.35) -> "Image.Image":
    """Darken the edges of any backdrop — instant focus + depth."""
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([-w * .25, -h * .25, w * 1.25, h * 1.25], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(w, h) // 5 or 1))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, Image.blend(img, dark, strength), m)


def terrazzo(w, h, style="mosaic", chip: int = 15, seed: int = 9) -> "Image.Image":
    """Terrazzo / trencadís: stone chips in the style's accent family scattered
    on a plaster ground — the mosaic profile's signature surface."""
    import random as _r
    t = tokens(style)
    rnd = _r.Random(seed)
    ground = lighten(t["bg"], .04) if not _is_dark(t["bg"]) else lighten(t["bg"], .06)
    img = Image.new("RGB", (w, h), ground)
    d = ImageDraw.Draw(img)
    cols = [t["accent"], t["accent2"], harmony(t["accent"])["analogous"][1],
            darken(t["accent"], .3), t["muted"], t["border"]]
    for _ in range(max(12, w * h // (chip * chip * 2))):
        cx, cy = rnd.uniform(0, w), rnd.uniform(0, h)
        r0 = rnd.uniform(chip * .18, chip * .55)
        ang = rnd.uniform(0, 6.283)
        pts = []
        import math
        for k in range(rnd.randint(4, 7)):
            a = ang + k * 6.283 / rnd.randint(4, 7) + rnd.uniform(-.3, .3)
            rr = r0 * rnd.uniform(.6, 1.25)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=_mix(_rgb(rnd.choice(cols)), _rgb(ground),
                                 rnd.uniform(0, .25)))
    return Image.blend(img, _noise_img(w, h, 8, seed).convert("RGB"), 0.05)


TEXTURES = ("grain", "brushed", "carbon", "scanlines", "halftone", "stripes",
            "mesh", "starfield", "paper", "terrazzo")


def texture(kind: str, w: int, h: int, style: str = "frutiger-aero",
            **kw) -> "Image.Image":
    """Dispatcher: any TEXTURES kind by name, themed by style."""
    fn = {"grain": grain, "brushed": brushed, "carbon": carbon,
          "scanlines": scanlines, "halftone": halftone, "stripes": stripes,
          "mesh": mesh, "starfield": starfield, "paper": paper,
          "terrazzo": terrazzo}[kind]
    return fn(w, h, style, **kw)


# --------------------------------------------------------------------------- #
#  Depth generators (style-aware)
# --------------------------------------------------------------------------- #

def glass_card(w, h, style="frutiger-aero", radius=None, pad=16,
               accent=None) -> "Image.Image":
    """Profile-aware panel; legacy name retained for existing applications."""
    t, e = tokens(style), decisions(style)
    radius = _radius(style, h) if radius is None else radius
    if "radius" in e["forbid"]:
        radius = 0
    iw, ih = w - pad * 2, h - pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if iw < 8 or ih < 8:
        return img
    if e["elevation"] in ("soft", "hard", "glow"):
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = e["elevation"] == "glow"
        hard = e["elevation"] == "hard"
        col = _rgb(t["accent"] if glow else t["text"] if hard else "#000000")
        offset = 5 if not glow else 0
        ImageDraw.Draw(sh).rounded_rectangle(
            [pad + (4 if hard else 0), pad + offset, pad + iw, pad + ih + offset],
            radius=radius, fill=(*col, 255 if hard else 100))
        img = Image.alpha_composite(img, sh if hard else sh.filter(ImageFilter.GaussianBlur(pad * .55)))
    panel = (vgrad(iw,ih,t["surface"],t["bg2"]).convert("RGBA")
             if _gloss(style) else Image.new("RGBA",(iw,ih),t["surface"]))
    img.paste(panel, (pad, pad), rounded_mask(iw, ih, radius))
    d = ImageDraw.Draw(img)
    if e["border"] or e["elevation"] == "flat":
        d.rounded_rectangle([pad, pad, pad + iw - 1, pad + ih - 1],
                            radius=radius, outline=t["border"], width=max(1,e["border"]))
    if _gloss(style) >= 2:
        d.rounded_rectangle([pad + 1, pad + 1, pad + iw - 2, pad + ih - 2],
                            radius=max(0,radius - 1), outline=(255,255,255,100), width=1)
    if accent:
        # Only emit a colour blend where that profile permits gradients.
        strip = (_material(iw - 24, 3, t["accent"], style) if "gradient" in e["forbid"]
                 else hgrad(iw - 24, 3, accent[0], accent[1]).convert("RGBA"))
        img.alpha_composite(strip, (pad + 12, pad + 8))
    return img


def gel_button(w, h, style="frutiger-aero", hover=False,
               enabled=True) -> "Image.Image":
    """Filled action button; polish and corners come from the profile."""
    t = tokens(style)
    base = _rgb(t["accent"])
    if not enabled:
        base = _mix(base, _rgb(t["surface"]), .6)
    r = _radius(style, h)
    body = _material(w, h, base, style, control=True, hover=hover)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = rounded_mask(w, h, r)
    out.paste(body, (0, 0), mask)
    if _gloss(style, True) >= 2:
        sheen = Image.new("RGBA", (w,h), (0,0,0,0))
        ImageDraw.Draw(sheen).rounded_rectangle([2,2,w-3,max(2,int(h*.43))],
             radius=max(0,r-2), fill=(255,255,255,105 if hover else 75))
        out = Image.alpha_composite(out, Image.composite(
            sheen, Image.new("RGBA",(w,h)), mask))
    ImageDraw.Draw(out).rounded_rectangle([0,0,w-1,h-1],radius=r,
        outline=(*_rgb(t["border"]),255),width=max(1,decisions(style)["border"]))
    return out


def header_bar(w, h, style="frutiger-aero") -> "Image.Image":
    """Title band: matte or glossy according to the style, with its own motif."""
    t = tokens(style)
    base = t["accent"] if _gloss(style) >= 2 else t["surface"]
    img = _material(w, h, base, style)
    d = ImageDraw.Draw(img)
    if style == "frutiger-aero":
        import random
        rng = random.Random(11)
        for _ in range(8):
            r = rng.randint(max(1,h//4),max(1,h*7//10))
            x,y = rng.randint(w//3,w),rng.randint(0,h)
            d.ellipse([x-r,y-r,x+r,y+r],outline=(255,255,255,45),width=2)
    d.line([(0,h-2),(w,h-2)],fill=t["accent"],width=2)
    return img.convert("RGB")


def scene(w, h, style="frutiger-aero") -> "Image.Image":
    """Backdrop chosen from the profile instead of an all-style blob wash."""
    if style == "frutiger-aero":
        try:
            from . import theme
            return theme.make_scene(w,h)
        except ImportError:
            return vgrad(w,h,tokens(style)["bg"],tokens(style)["bg2"])
    try:
        from . import assets
        prof = assets.profile_for(style) or {}
        choices = prof.get("textures", [])
        if choices and "texture" not in decisions(style)["forbid"]:
            return texture(choices[0],w,h,style)
    except ImportError:
        pass
    return Image.new("RGB",(w,h),tokens(style)["bg"])


def _font(size: int, bold: bool = False, style=None, role="body"):
    if style == "hi-contrast":
        size = max(16,size)
    # Prefer the profile's actual offline face; Segoe is not installed on Linux.
    candidates = []
    if style:
        try:
            from . import assets
            profile = assets.profile_for(style) or {}
            fonts = profile.get("fonts", {})
            family = fonts.get("display" if bold else role, fonts.get("body", ""))
            for stem, (name, weight, _) in assets.FONT_MAP.items():
                if name == family:
                    candidates.append((abs(weight - (700 if bold else 400)),
                                       str(assets.FONT_DIR / (stem + ".ttf"))))
        except ImportError:
            pass
    paths = [p for _,p in sorted(candidates)] + [
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for path in paths:
        try:
            return ImageFont.truetype(path,size)
        except OSError:
            continue
    return ImageFont.load_default()


def neon_button(w, h, style="cyberpunk", hover=False) -> "Image.Image":
    """Outline action; glow is emitted only by styles that declare it."""
    t,e = tokens(style),decisions(style)
    r = max(0,_radius(style,h)-3)
    img = Image.new("RGBA",(w,h),(0,0,0,0))
    if e["elevation"] == "glow" and "neon" not in e["forbid"]:
        halo = Image.new("RGBA",(w,h),(0,0,0,0))
        ImageDraw.Draw(halo).rounded_rectangle([3,3,w-4,h-4],radius=r,
             outline=(*_rgb(t["accent"]),200 if hover else 110),width=3)
        img = Image.alpha_composite(img,halo.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3,3,w-4,h-4],radius=r,fill=t["bg2"] if hover else t["surface"],
                        outline=t["accent"],width=max(1,e["border"]))
    return img


def progress_img(w, h, frac: float, style="frutiger-aero") -> "Image.Image":
    """Profile-aware progress with visible small values and a clamped fill."""
    t,e = tokens(style),decisions(style)
    frac = min(1.0,max(0.0,frac))
    r = _radius(style,h)
    img = Image.new("RGBA",(w,h),(0,0,0,0));d=ImageDraw.Draw(img)
    d.rounded_rectangle([0,0,w-1,h-1],radius=r,fill=t["bg2"],outline=t["border"])
    fw = int((w-4)*frac)
    if fw > 0 and h > 4:
        fill = _material(fw,h-4,t["accent"],style,control=True)
        img.paste(fill,(2,2),rounded_mask(fw,h-4,min(r,fw//2)))
    return img


def toggle_img(on: bool, style="frutiger-aero", w=56, h=28) -> "Image.Image":
    """On/off control whose material and corners obey the profile."""
    t=tokens(style);r=_radius(style,h)
    img=Image.new("RGBA",(w,h),(0,0,0,0))
    base=t["accent"] if on else t["bg2"]
    img.paste(_material(w,h,base,style,control=True),(0,0),rounded_mask(w,h,r))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle([0,0,w-1,h-1],radius=r,outline=t["border"],width=1)
    x=w-h+4 if on else 4
    d.ellipse([x,4,x+h-8,h-4],fill=on_color(base))
    return img


def badge_img(text: str, style="frutiger-aero", kind: str = "accent",
              h: int = 24) -> "Image.Image":
    """A pill badge/chip.  kind: accent · accent2 · outline · surface."""
    t = tokens(style)
    f = _font(max(9, h - 12), bold=True, style=style)
    tw = int(ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(text, font=f))
    w = tw + h + 4
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = _radius(style,h)
    if kind == "outline":
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r,
                            outline=(*_rgb(t["accent"]), 255), width=2)
        fg = t["accent"]
    else:
        base = t["accent2"] if kind == "accent2" else (
            t["surface"] if kind == "surface" else t["accent"])
        body = _material(w,h,base,style,control=True)
        img.paste(body, (0, 0), rounded_mask(w, h, r))
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r,
                            outline=(255, 255, 255, 90), width=1)
        fg = ensure_contrast(t["text"],base) if kind == "surface" else on_color(base)
    d.text((w // 2 - tw // 2, h // 2 - (h - 12) // 2 - 3), text, font=f,
           fill=_rgb(fg))
    return img


_DOT_STATES = {"ok": None, "warn": "#fdb44b", "err": "#e5484d", "off": None}


def status_dot(d: int = 14, state: str = "ok",
               style="frutiger-aero") -> "Image.Image":
    """A glowing status light: ok (style accent2) · warn · err · off."""
    t = tokens(style)
    col = _rgb({"ok": t["accent2"], "warn": "#fdb44b", "err": "#e5484d",
                "off": t["muted"]}.get(state, t["accent2"]))
    s = d * 3
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    if state != "off" and decisions(style)["elevation"] == "glow":
        glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([d * .8, d * .8, s - d * .8, s - d * .8],
                                     fill=(*col, 130))
        img = Image.alpha_composite(img, glow.filter(
            ImageFilter.GaussianBlur(d // 2 or 1)))
    dr = ImageDraw.Draw(img)
    dr.ellipse([d, d, s - d, s - d], fill=(*col, 255),
               outline=(255, 255, 255, 150), width=1)
    if _gloss(style) >= 2:
        dr.ellipse([d + 2, d + 2, s - d - d * .6, s - d - d * .6],
                   fill=(*_mix(col, (255, 255, 255), .5), 160))
    return img


def plaque(w, h=66, style="golden-archive") -> "Image.Image":
    """Engraved museum plaque strip (born in the Ultra Archive): dark surface,
    accent hairline rule, hairline border.  Put caption text on top."""
    t = tokens(style)
    img = _material(w,h,t["surface"],style)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(*_rgb(t["border"]), 255))
    d.line([(10, 2), (w - 10, 2)], fill=(*_rgb(t["accent"]), 200))
    return img


def divider(w, style="frutiger-aero", h: int = 3) -> "Image.Image":
    """Accent-gradient hairline that fades out at both ends."""
    t = tokens(style)
    if "gradient" in decisions(style)["forbid"]:
        return Image.new("RGBA",(w,h),tokens(style)["accent"])
    img = hgrad(w, h, t["accent2"], t["accent"]).convert("RGBA")
    m = Image.new("L", (w, h), 255)
    md = ImageDraw.Draw(m)
    fade = max(8, w // 8)
    for x in range(fade):
        a = int(255 * x / fade)
        md.line([(x, 0), (x, h)], fill=a)
        md.line([(w - 1 - x, 0), (w - 1 - x, h)], fill=a)
    img.putalpha(m)
    return img


# --------------------------------------------------------------------------- #
#  tkinter widgets
# --------------------------------------------------------------------------- #

class Card(tk.Frame):
    """Glass panel with a drop shadow. Pack content into `card.body`."""

    def __init__(self, master, style="frutiger-aero", radius=None, pad=14,
                 accent=None):
        t = tokens(style)
        self._surface = t["surface"]
        super().__init__(master, bg=t["bg"], highlightthickness=0, bd=0)
        self.style, self.radius, self.pad, self.accent = style, radius, pad, accent
        self._img = None; self._size = (0, 0)
        self._bg = tk.Label(self, bd=0, bg=t["bg"])
        self._bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=t["surface"], highlightthickness=0, bd=0)
        self.body.place(x=pad + 3, y=pad + 3, relwidth=1, relheight=1,
                        width=-(pad + 3) * 2, height=-(pad + 3) * 2)
        self.bind("<Configure>", self._cfg, add="+")

    def _cfg(self, e):
        if (e.width, e.height) == self._size or e.width < 30:
            return
        self._size = (e.width, e.height)
        self._img = ImageTk.PhotoImage(glass_card(
            e.width, e.height, self.style, self.radius, self.pad, self.accent))
        self._bg.configure(image=self._img)


def _caption(img, text, style, outline=False):
    d=ImageDraw.Draw(img);f=_font(15,style=style)
    bbox=d.textbbox((0,0),text,font=f)
    x=(img.width-(bbox[2]-bbox[0]))/2-bbox[0]
    y=(img.height-(bbox[3]-bbox[1]))/2-bbox[1]
    t=tokens(style)
    fg=ensure_contrast(t["accent"],t["surface"]) if outline else on_color(t["accent"])
    d.text((x,y),text,font=f,fill=fg)
    return img


class GelButton(tk.Canvas):
    """Glossy gel button (hover + enabled states), themed by style."""

    def __init__(self, master, text, command, width=120, height=42,
                 style="frutiger-aero", bg=None):
        t = tokens(style)
        super().__init__(master, width=width, height=height, highlightthickness=0,
                         bd=0, bg=bg or t["bg2"])
        self.command, self.text, self.style = command, text, style
        self.w, self.h, self._enabled, self._imgs = width, height, True, {}
        self.configure(takefocus=1,highlightthickness=2,highlightbackground=t["bg2"],highlightcolor=t["accent"])
        for key in ("<Return>","<space>"):
            self.bind(key,lambda e: self._enabled and self.command and self.command())
        self._draw(False)
        self.bind("<Enter>", lambda e: self._enabled and self._draw(True))
        self.bind("<Leave>", lambda e: self._enabled and self._draw(False))
        self.bind("<Button-1>", lambda e: self._enabled and self.command and self.command())

    def _draw(self, hover):
        key = (hover, self._enabled, self.text)
        if key not in self._imgs:
            self._imgs[key] = ImageTk.PhotoImage(
                _caption(gel_button(self.w,self.h,self.style,hover,self._enabled),self.text,self.style))
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self._imgs[key])

    def set_text(self, t): self.text = t; self._draw(False)
    def set_enabled(self, b): self._enabled = b; self._draw(False)


class NeonButton(tk.Canvas):
    """Outline-glow button — for dark styles where gel gloss is too playful."""

    def __init__(self, master, text, command, width=130, height=42,
                 style="cyberpunk", bg=None):
        t = tokens(style)
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, bg=bg or t["bg2"])
        self.command, self.text, self.style = command, text, style
        self.w, self.h, self._imgs = width, height, {}
        self.configure(takefocus=1,highlightthickness=2,highlightbackground=t["bg2"],highlightcolor=t["accent"])
        for key in ("<Return>","<space>"):
            self.bind(key,lambda e: self.command and self.command())
        self._fg = t["accent"]
        self._draw(False)
        self.bind("<Enter>", lambda e: self._draw(True))
        self.bind("<Leave>", lambda e: self._draw(False))
        self.bind("<Button-1>", lambda e: self.command and self.command())

    def _draw(self, hover):
        if hover not in self._imgs:
            self._imgs[hover] = ImageTk.PhotoImage(
                _caption(neon_button(self.w,self.h,self.style,hover),self.text,self.style,outline=True))
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self._imgs[hover])


class ProgressBar(tk.Canvas):
    """Gradient progress bar; `.set(0..1)` to update."""

    def __init__(self, master, width=260, height=14, style="frutiger-aero",
                 bg=None):
        t = tokens(style)
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, bg=bg or t["surface"])
        self.w, self.h, self.style, self._img = width, height, style, None
        self.set(0.0)

    def set(self, frac: float):
        self._img = ImageTk.PhotoImage(
            progress_img(self.w, self.h, frac, self.style))
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self._img)


class Toggle(tk.Canvas):
    """On/off switch.  `command` (if given) receives the new bool state."""

    def __init__(self, master, on=False, command=None, style="frutiger-aero",
                 bg=None):
        t = tokens(style)
        super().__init__(master, width=56, height=28, highlightthickness=0,
                         bd=0, bg=bg or t["surface"], cursor="hand2")
        self.on, self.command, self.style = bool(on), command, style
        self._imgs = {}
        self._draw()
        self.bind("<Button-1>", self._flip)
        self.configure(takefocus=1,highlightthickness=2,highlightbackground=t["surface"],highlightcolor=t["accent"])
        self.bind("<space>",self._flip)
        self.bind("<Return>",self._flip)

    def _draw(self):
        if self.on not in self._imgs:
            self._imgs[self.on] = ImageTk.PhotoImage(
                toggle_img(self.on, self.style))
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self._imgs[self.on])

    def _flip(self, _e=None):
        self.on = not self.on
        self._draw()
        if self.command:
            self.command(self.on)


class Chip(tk.Label):
    """Pill badge label.  kind: accent · accent2 · outline · surface."""

    def __init__(self, master, text, style="frutiger-aero", kind="accent",
                 bg=None):
        self._img = ImageTk.PhotoImage(badge_img(text, style, kind))
        super().__init__(master, image=self._img, bd=0,
                         bg=bg or tokens(style)["surface"])


class StatusDot(tk.Label):
    """Glowing status light; `.set_state("ok"|"warn"|"err"|"off")`."""

    def __init__(self, master, state="ok", style="frutiger-aero", size=12,
                 bg=None):
        self.style, self.size = style, size
        self._bg = bg or tokens(style)["surface"]
        self._img = ImageTk.PhotoImage(status_dot(size, state, style))
        super().__init__(master, image=self._img, bd=0, bg=self._bg)

    def set_state(self, state: str):
        self._img = ImageTk.PhotoImage(status_dot(self.size, state, self.style))
        self.configure(image=self._img)


class Divider(tk.Label):
    """Fading accent hairline; pack with fill='x'."""

    def __init__(self, master, width=280, style="frutiger-aero", bg=None):
        self._img = ImageTk.PhotoImage(divider(width, style))
        super().__init__(master, image=self._img, bd=0,
                         bg=bg or tokens(style)["surface"])


class HeaderBar(tk.Canvas):
    """Glossy themed header hosting a title (+ other widgets)."""

    def __init__(self, master, height=56, style="frutiger-aero"):
        super().__init__(master, height=height, highlightthickness=0, bd=0)
        self.h, self.style, self._img = height, style, None
        self.bind("<Configure>", self._redraw)

    def _redraw(self, e):
        self._img = ImageTk.PhotoImage(header_bar(max(e.width, 1), self.h, self.style))
        self.delete("bg")
        self.create_image(0, 0, anchor="nw", image=self._img, tags="bg")
        self.tag_lower("bg")


def run_splash(root, on_done, title="App", subtitle="", style="frutiger-aero",
               duration=1600):
    """Animated landing overlay: themed backdrop, a glass title card, a gradient
    loading bar, and rising bubbles — then clears and calls on_done()."""
    if decisions(style).get("dur",1600) == 0:
        root.after(0,on_done)
        return
    root.update_idletasks()
    W, H = max(root.winfo_width(), 900), max(root.winfo_height(), 600)
    t = tokens(style)
    cv = tk.Canvas(root, highlightthickness=0, bd=0, width=W, height=H)
    cv.place(x=0, y=0, relwidth=1, relheight=1)
    tk.Misc.lift(cv)   # NOT cv.lift(): Canvas.lift == tag_raise (item method)
    refs = {"bg": ImageTk.PhotoImage(scene(W, H, style))}
    cv.create_image(0, 0, anchor="nw", image=refs["bg"])
    cw, ch, cx, cy = min(560, W - 80), 200, W // 2, int(H * .42)
    refs["card"] = ImageTk.PhotoImage(glass_card(
        cw + 28, ch + 28, style, None, 14, accent=(_rgb(t["accent2"]), _rgb(t["accent"]))))
    cv.create_image(cx, cy + 30, image=refs["card"])
    title_i = cv.create_text(cx, cy - 24, text=title, font=(FONT, 34, "bold"),
                             fill=t["text"])
    cv.create_text(cx, cy + 16, text=subtitle, font=(FONT, 15), fill=t["accent"])
    cv.create_text(cx, cy + 46, text="powered locally · offline",
                   font=(FONT, 10, "italic"), fill=t["muted"])
    bw = min(360, W - 160); bx, by = cx - bw // 2, cy + 78
    cv.create_rectangle(bx, by, bx + bw, by + 8, outline=t["border"],
                        fill=t["bg2"], width=1)
    bar = cv.create_rectangle(bx, by, bx, by + 8, outline="", fill=t["accent"])
    import random
    rng = random.Random(3)
    bubbles = [[cv.create_oval(0, 0, 0, 0, outline="#ffffff", width=2), rng.randint(0, W),
                rng.randint(H, H + 300), rng.randint(4, 16), rng.uniform(1.5, 4)]
               for _ in range(18 if style == "frutiger-aero" else 0)]
    acc2, acc = _rgb(t["accent2"]), _rgb(t["accent"])
    steps = max(12, duration // 40); st = {"i": 0}

    def step():
        i = st["i"]; f = i / steps
        cv.coords(bar, bx, by, bx + int(bw * f), by + 8)
        cv.itemconfig(bar, fill=t["accent"] if "gradient" in decisions(style)["forbid"]
                      else "#%02x%02x%02x" % _mix(acc2, acc, f))
        cv.coords(title_i, cx, (cy - 24) - int((1 - min(1, f * 2)) * min(14,decisions(style).get("travel",0))))
        for b in bubbles:
            b[2] -= b[4]
            cv.coords(b[0], b[1] - b[3], b[2] - b[3], b[1] + b[3], b[2] + b[3])
        st["i"] += 1
        root.after(40, step) if i < steps else (cv.destroy(), on_done())

    root.after(120, step)


# --------------------------------------------------------------------------- #
#  Static look-preview (headless) + live demo window
# --------------------------------------------------------------------------- #

def preview(style="frutiger-aero", out="native_preview.png") -> str:
    """Compose a static PNG showing the style's whole native wardrobe: header,
    glass cards, every widget state, the color ramp, and the texture strip.
    Great for eyeballing a style without opening a GUI."""
    W, H = 1000, 780
    img = scene(W,H,style).convert("RGBA")
    img.alpha_composite(header_bar(W, 56, style).convert("RGBA"), (0, 0))
    t = tokens(style)
    acc = (_rgb(t["accent2"]), _rgb(t["accent"]))
    surface_fg = _rgb(t["text"])

    # left card: interactive components in both states
    img.alpha_composite(glass_card(600, 470, style), (22, 76))
    img.alpha_composite(gel_button(150, 44, style).convert("RGBA"), (60, 120))
    img.alpha_composite(gel_button(150, 44, style, hover=True).convert("RGBA"), (222, 120))
    img.alpha_composite(neon_button(150, 44, style), (60, 178))
    img.alpha_composite(neon_button(150, 44, style, hover=True), (222, 178))
    img.alpha_composite(toggle_img(True, style), (60, 244))
    img.alpha_composite(toggle_img(False, style), (128, 244))
    img.alpha_composite(progress_img(320, 14, 0.66, style), (60, 292))
    for i, kind in enumerate(("accent", "accent2", "outline", "surface")):
        img.alpha_composite(badge_img(kind, style, kind), (60 + i * 96, 330))
    for i, st in enumerate(("ok", "warn", "err", "off")):
        img.alpha_composite(status_dot(12, st, style), (56 + i * 52, 372))
    img.alpha_composite(divider(320, style), (60, 430))
    img.alpha_composite(plaque(320, 60, style), (60, 456))

    # right card: the color system
    img.alpha_composite(glass_card(340, 470, style, accent=acc), (636, 76))
    d = ImageDraw.Draw(img)
    for i, hx in enumerate(ramp(t["accent"], 7)):
        d.rectangle([672 + i * 38, 130, 672 + i * 38 + 32, 176], fill=hx)
    for i, hx in enumerate(ramp(t["accent2"], 7)):
        d.rectangle([672 + i * 38, 186, 672 + i * 38 + 32, 232], fill=hx)
    try:
        from . import assets
        profile = assets.profile_for(style) or {}
        palette = assets.find_palette(profile.get("palette", ""))
        swatches = palette["colors"][:7] if palette else [t[k] for k in ("accent","accent2","text")]
    except ImportError:
        swatches = [t[k] for k in ("accent","accent2","text")]
    for i, hx in enumerate(swatches):
        d.rectangle([672 + i * 38, 258, 672 + i * 38 + 32, 304], fill=hx)
    for i, key in enumerate(("bg", "bg2", "surface", "border", "muted", "text")):
        d.rectangle([672 + i * 44, 330, 672 + i * 44 + 38, 376], fill=t[key])
    d.text((672, 396), "Accent ramps\nProfile palette\nSurface and text roles",
           font=_font(12,style=style), fill=surface_fg)

    # Label real controls so shape/material and foreground can be judged.
    for x,label in ((60,"Continue"),(222,"Hover")):
        d.text((x+14,132),label,font=_font(15,style=style),fill=on_color(t["accent"]))
    d.text((60,92),"Your next idea",font=_font(18,bold=True,style=style),fill=t["text"])
    d.text((60,400),"Secondary text stays readable.",font=_font(14,style=style),fill=t["muted"])
    # Texture strip is a labelled library sampler, not a profile backdrop.
    d.text((22,562),"Texture library samples",font=_font(13,style=style),fill=t["text"])
    # texture strip along the bottom
    tile_w, tile_h, x0, y0 = (W-44-(len(TEXTURES)-1)*5)//len(TEXTURES), 150, 22, 590
    for i, kind in enumerate(TEXTURES):
        tx = x0 + i * (tile_w + 5)
        img.paste(texture(kind, tile_w, tile_h, style), (tx, y0))
        d.rectangle([tx, y0, tx + tile_w - 1, y0 + tile_h - 1],
                    outline=_rgb(t["border"]))
        d.text((tx + 4, y0 + tile_h - 20), kind, font=_font(11,style=style),
               fill="white" if _is_dark(t["bg"]) else _rgb(t["text"]))

    d.text((20, 16), f"native UI · {style}", font=_font(22,bold=True,style=style),
           fill=on_color(t["accent"]) if _gloss(style)>=2 else t["text"])
    from pathlib import Path
    p = Path(out).expanduser()
    img.convert("RGB").save(p)
    return str(p)


def demo(style="frutiger-aero") -> None:
    """Open a live sample window in the given style (header + card + gel button)."""
    root = tk.Tk()
    root.title(f"nativeui demo — {style}")
    root.geometry("820x560")
    t = tokens(style)
    root.configure(bg=t["bg"])
    lbl = tk.Label(root, bd=0)
    lbl.place(x=0, y=0, relwidth=1, relheight=1)
    _sc = ImageTk.PhotoImage(scene(820, 560, style))
    lbl.configure(image=_sc)
    hdr = HeaderBar(root, style=style)
    hdr.pack(fill="x", side="top")
    hdr.bind("<Configure>", lambda e: (hdr._redraw(e), hdr.create_text(
        20, 28, anchor="w", text=f"Native UI  ·  {style}", fill="white",
        font=(FONT, 15, "bold"))), add="+")
    card = Card(root, style=style, accent=(_rgb(t["accent2"]), _rgb(t["accent"])))
    card.pack(fill="both", expand=True, padx=24, pady=20)
    tk.Label(card.body, text="Glass card with real depth", bg=t["surface"],
             fg=t["text"], font=(FONT, 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
    tk.Label(card.body, text="Drop shadow · gradient surface · sheen · themed border.\n"
             "Same code, any vault style.", bg=t["surface"], fg=t["muted"],
             justify="left", font=(FONT, 11)).pack(anchor="w", padx=16)
    GelButton(card.body, "Get started", lambda: None, style=style,
              bg=t["surface"]).pack(anchor="w", padx=16, pady=16)
    root.after(150, lambda: run_splash(root, on_done=lambda: None,
                                       title="Native UI", subtitle=style, style=style))
    root.mainloop()
