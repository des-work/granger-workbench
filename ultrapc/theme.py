"""Frutiger Aero theme — the glossy, sky-and-grass, bubbly early-2010s
edutainment look. PIL generates the scenery and gel widgets at runtime; the
Tk widgets below wrap them so ai_chat.py can stay focused on behavior.
"""

from __future__ import annotations

import tkinter as tk

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk

try:
    import numpy as np
    HAVE_NP = True
except Exception:
    HAVE_NP = False

FONT = "Segoe UI"


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# Frutiger Aero palette — sourced from the single source of truth in the assets
# vault (ultrapc/assets.py STYLES['frutiger-aero']) so the window and everything
# we vibe-code share one palette. Falls back to literals if assets can't load.
try:
    from . import assets as _assets
    _T = _assets.theme_colors("frutiger-aero")
    GLASS = _T.get("bg2", "#eaf6ff")        # light glass panel  (token: bg2)
    GLASS_EDGE = _T.get("border", "#9fd0f0")   # aqua border      (token: border)
    SKY_HEX = _T.get("bg", "#ceecff")        # sky horizon        (token: bg)
    INK = _T.get("text", "#0b3c5d")          # deep blue text     (token: text)
    AQUA = _hex_rgb(_T.get("accent", "#2b8fd6"))   # gel button base (token: accent)
except Exception:                            # pragma: no cover - defensive
    GLASS, GLASS_EDGE, SKY_HEX, INK = "#eaf6ff", "#9fd0f0", "#ceecff", "#0b3c5d"
    AQUA = (43, 143, 214)

# Scene-specific tuning (PIL scenery), not part of the shared token set.
SKY_TOP = (96, 178, 240)
SKY_HORIZON = _hex_rgb(SKY_HEX)
GRASS_TOP = (150, 205, 110)
GRASS_BOT = (78, 150, 56)
GREEN_BADGE = "#3aa845"


def use_palette(style: str = "frutiger-aero") -> dict:
    """Re-theme the Tk widget palette to any vault style (e.g. 'nordic',
    'earthy'). Updates GLASS/GLASS_EDGE/SKY_HEX/INK/AQUA in-place and returns
    the hex dict. The PIL sky-and-grass scenery stays Frutiger-specific."""
    global GLASS, GLASS_EDGE, SKY_HEX, INK, AQUA
    try:
        from . import assets as _a
        t = _a.theme_colors(style)
    except Exception:
        return {}
    GLASS = t.get("bg2", GLASS)
    GLASS_EDGE = t.get("border", GLASS_EDGE)
    SKY_HEX = t.get("bg", SKY_HEX)
    INK = t.get("text", INK)
    AQUA = _hex_rgb(t.get("accent", "#2b8fd6"))
    return t


# --------------------------------------------------------------------------- #
#  Image generators
# --------------------------------------------------------------------------- #

def _vgrad(w: int, h: int, c1, c2) -> "Image.Image":
    if HAVE_NP:
        t = np.linspace(0, 1, h)[:, None]
        rows = np.array(c1, float) * (1 - t) + np.array(c2, float) * t
        arr = np.repeat(rows[:, None, :], w, axis=1).astype("uint8")
        return Image.fromarray(arr, "RGB")
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    return img


def make_scene(w: int, h: int) -> "Image.Image":
    """Sky gradient over rolling green hills, with soft floating bubbles."""
    w, h = max(w, 200), max(h, 200)
    sky = _vgrad(w, h, SKY_TOP, SKY_HORIZON)
    grass = _vgrad(w, h, GRASS_TOP, GRASS_BOT)
    if HAVE_NP:
        xs = np.arange(w)
        hill = (0.70 * h + 0.03 * h * np.sin(xs / w * 3.1 * np.pi)
                + 0.015 * h * np.sin(xs / w * 7 * np.pi)).astype(int)
        yy = np.arange(h)[:, None]
        mask = yy >= hill[None, :]
        arr = np.where(mask[:, :, None], np.asarray(grass), np.asarray(sky))
        scene = Image.fromarray(arr.astype("uint8"), "RGB")
    else:
        scene = sky
        scene.paste(grass, (0, int(h * 0.70)))
    scene = scene.convert("RGBA")

    # soft light flare, top-right
    flare = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flare)
    fx, fy, fr = int(w * 0.82), int(h * 0.14), int(min(w, h) * 0.28)
    fd.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=(255, 255, 255, 70))
    flare = flare.filter(ImageFilter.GaussianBlur(40))
    scene = Image.alpha_composite(scene, flare)

    # floating bubbles
    bub = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bub)
    import random
    random.seed(7)
    for _ in range(14):
        r = random.randint(int(h * 0.03), int(h * 0.10))
        cx = random.randint(0, w); cy = random.randint(0, int(h * 0.72))
        bd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 26),
                   outline=(255, 255, 255, 55), width=2)
        hr = max(2, r // 4)
        bd.ellipse([cx - r // 2 - hr, cy - r // 2 - hr, cx - r // 2 + hr,
                    cy - r // 2 + hr], fill=(255, 255, 255, 120))
    bub = bub.filter(ImageFilter.GaussianBlur(0.6))
    scene = Image.alpha_composite(scene, bub)
    return scene.convert("RGB")


def rounded_rect(w: int, h: int, radius: int, fill, outline=None, ow: int = 2):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=fill,
                        outline=outline, width=ow)
    return img


def gel_button(w: int, h: int, base=AQUA, hover=False, enabled=True) -> "Image.Image":
    """A glossy aqua gel button: rounded, gradient body, top highlight sheen."""
    r = h // 2
    if not enabled:
        base = tuple(int(c * 0.5 + 128 * 0.5) for c in base)  # desaturate
    top = tuple(min(255, int(c * (1.35 if hover else 1.25))) for c in base)
    bot = tuple(int(c * (0.72 if hover else 0.66)) for c in base)
    body = _vgrad(w, h, top, bot).convert("RGBA")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(body, (0, 0), mask)
    # top sheen
    sheen = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rounded_rectangle([3, 2, w - 4, int(h * 0.48)], radius=r - 2,
                         fill=(255, 255, 255, 150 if hover else 120))
    sheen = sheen.filter(ImageFilter.GaussianBlur(2))
    sm = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sm).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    out = Image.alpha_composite(out, Image.composite(
        sheen, Image.new("RGBA", (w, h), (0, 0, 0, 0)), sm))
    # crisp border
    ImageDraw.Draw(out).rounded_rectangle([0, 0, w - 1, h - 1], radius=r,
                                          outline=(255, 255, 255, 210), width=2)
    return out


def _truetype(size: int, bold: bool = True):
    """Load a serif Windows font for the illuminated capital, with fallbacks."""
    names = (["georgiab.ttf", "constanb.ttf", "timesbd.ttf", "PALATINOB.ttf"]
             if bold else ["georgia.ttf", "constan.ttf", "times.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


def illuminated_capital(letter: str, size: int = 60) -> "Image.Image":
    """A storybook drop-cap: a gilded parchment tile with an ornate initial."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # parchment -> gold gradient body, rounded
    bg = _vgrad(size, size, (250, 238, 205), (212, 172, 98)).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([1, 1, size - 2, size - 2], radius=10, fill=255)
    img.paste(bg, (0, 0), mask)
    d = ImageDraw.Draw(img)
    # soft top sheen
    sheen = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(sheen).rounded_rectangle([3, 2, size - 4, int(size * 0.42)],
                                            radius=8, fill=(255, 255, 255, 90))
    img = Image.alpha_composite(img, Image.composite(
        sheen, Image.new("RGBA", (size, size), (0, 0, 0, 0)), mask))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, size - 2, size - 2], radius=10,
                        outline=(150, 110, 40), width=2)
    d.rounded_rectangle([4, 4, size - 5, size - 5], radius=7,
                        outline=(184, 146, 74), width=1)
    ch = (letter or "?").strip()[:1].upper() or "?"
    font = _truetype(int(size * 0.68))
    bb = d.textbbox((0, 0), ch, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pos = ((size - tw) / 2 - bb[0], (size - th) / 2 - bb[1] - 1)
    d.text((pos[0] + 1, pos[1] + 1), ch, font=font, fill=(120, 90, 40, 90))  # shadow
    d.text(pos, ch, font=font, fill=(122, 28, 30))                           # burgundy ink
    return img


def header_bar(w: int, h: int) -> "Image.Image":
    """Glossy blue title bar: deep gradient, bright top sheen, floating gel
    bubbles, and a bright green→aqua accent line along the bottom edge."""
    body = _vgrad(w, h, (72, 165, 236), (16, 84, 150)).convert("RGBA")
    # top sheen
    sheen = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sheen).rectangle([0, 0, w, int(h * 0.52)], fill=(255, 255, 255, 80))
    sheen = sheen.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(body, sheen)
    # faint depth-of-field gel bubbles drifting behind the title
    bub = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bub)
    import random
    random.seed(11)
    for _ in range(8):
        r = random.randint(int(h * 0.25), int(h * 0.7))
        cx = random.randint(int(w * 0.35), w); cy = random.randint(0, h)
        bd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 16),
                   outline=(255, 255, 255, 34), width=2)
    bub = bub.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, bub)
    # bright accent line (green -> aqua) hugging the bottom
    accent = _hgrad(w, 3, (150, 205, 110), (43, 143, 214))
    img.paste(accent, (0, h - 3))
    # subtle bottom shadow so content below feels layered under it
    d = ImageDraw.Draw(img)
    d.rectangle([0, h - 1, w, h], fill=(10, 40, 70, 120))
    return img.convert("RGB")


def _hgrad(w: int, h: int, c1, c2) -> "Image.Image":
    """Horizontal gradient (left c1 -> right c2)."""
    if HAVE_NP:
        t = np.linspace(0, 1, w)[None, :]
        cols = (np.array(c1, float)[None, None, :] * (1 - t[..., None])
                + np.array(c2, float)[None, None, :] * t[..., None])
        arr = np.repeat(cols, h, axis=0).astype("uint8")
        return Image.fromarray(arr, "RGB")
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for x in range(w):
        t = x / max(1, w - 1)
        d.line([(x, 0), (x, h)],
               fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    return img


def card_bg(w: int, h: int, radius: int = 18, pad: int = 14,
            top=(255, 255, 255), bot=(233, 244, 255),
            accent=None) -> "Image.Image":
    """A glass panel with real depth: a soft drop shadow, a subtly-gradiented
    rounded surface, a top sheen, and a hairline light border. This is the PIL
    translation of the design vault's `glass-card` + `layered-shadows`."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    iw, ih = w - pad * 2, h - pad * 2
    if iw < 10 or ih < 10:
        return img
    # ---- drop shadow (blurred dark rounded rect, offset down) ----
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [pad, pad + 5, pad + iw, pad + ih + 5], radius=radius,
        fill=(20, 60, 100, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(pad * 0.7))
    img = Image.alpha_composite(img, shadow)
    # ---- surface (gradient, rounded) ----
    surf = _vgrad(iw, ih, top, bot).convert("RGBA")
    mask = Image.new("L", (iw, ih), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, iw - 1, ih - 1],
                                           radius=radius, fill=255)
    img.paste(surf, (pad, pad), mask)
    # ---- top sheen: a smooth top-down white fade (no hard band) ----
    sh_h = max(6, int(ih * 0.32))
    sheen = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    if HAVE_NP:
        a = np.linspace(70, 0, sh_h).astype("uint8")
        band = np.zeros((sh_h, iw, 4), "uint8")
        band[..., :3] = 255
        band[..., 3] = a[:, None]
        sheen.paste(Image.fromarray(band, "RGBA"), (0, 0))
    else:
        sd = ImageDraw.Draw(sheen)
        for yy in range(sh_h):
            sd.line([(0, yy), (iw, yy)],
                    fill=(255, 255, 255, int(70 * (1 - yy / sh_h))))
    img.alpha_composite(Image.composite(
        sheen, Image.new("RGBA", (iw, ih), (0, 0, 0, 0)), mask), (pad, pad))
    # ---- accent: a clear colored strip under the top edge ----
    if accent:
        strip = _hgrad(iw - 24, 4, accent[0], accent[1]).convert("RGBA")
        sm = Image.new("L", (iw - 24, 4), 255)
        img.paste(strip, (pad + 12, pad + 8), sm)
    # ---- borders: bright inner + soft outer ----
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + iw - 1, pad + ih - 1], radius=radius,
                        outline=(255, 255, 255, 235), width=2)
    d.rounded_rectangle([pad - 1, pad - 1, pad + iw, pad + ih], radius=radius + 1,
                        outline=(159, 208, 240, 150), width=1)
    return img


# --------------------------------------------------------------------------- #
#  Tk widgets
# --------------------------------------------------------------------------- #

class Scene:
    """Full-window scenic background that regenerates (debounced) on resize."""

    def __init__(self, root: tk.Misc):
        self.root = root
        self.label = tk.Label(root, bd=0)
        self.label.place(x=0, y=0, relwidth=1, relheight=1)
        self.label.lower()
        self._img = None
        self._job = None
        self._size = (0, 0)
        root.bind("<Configure>", self._on_configure, add="+")
        root.after(30, lambda: self._render(root.winfo_width(), root.winfo_height()))

    def _on_configure(self, e):
        if e.widget is not self.root:
            return
        if (e.width, e.height) == self._size:
            return
        if self._job:
            self.root.after_cancel(self._job)
        self._job = self.root.after(120, lambda: self._render(e.width, e.height))

    def _render(self, w, h):
        if w < 50 or h < 50:
            return
        self._size = (w, h)
        self._img = ImageTk.PhotoImage(make_scene(w, h))
        self.label.configure(image=self._img)
        self.label.lower()


class GelButton(tk.Canvas):
    """A glossy aqua gel button with hover + enable states."""

    def __init__(self, master, text, command, width=118, height=40,
                 base=AQUA, bg=GLASS, font_size=11):
        super().__init__(master, width=width, height=height, highlightthickness=0,
                         bd=0, bg=bg)
        self.command = command
        self.text = text
        self.base = base
        self.w, self.h = width, height
        self.font_size = font_size
        self._enabled = True
        self._imgs = {}
        self._draw(False)
        self.bind("<Enter>", lambda e: self._enabled and self._draw(True))
        self.bind("<Leave>", lambda e: self._enabled and self._draw(False))
        self.bind("<Button-1>", self._click)

    def _photo(self, hover):
        key = (hover, self._enabled)
        if key not in self._imgs:
            self._imgs[key] = ImageTk.PhotoImage(
                gel_button(self.w, self.h, self.base, hover, self._enabled))
        return self._imgs[key]

    def _draw(self, hover):
        self.delete("all")
        self._cur = self._photo(hover)
        self.create_image(0, 0, anchor="nw", image=self._cur)
        color = "white" if self._enabled else "#e8f2ff"
        self.create_text(self.w // 2, self.h // 2, text=self.text, fill=color,
                         font=(FONT, self.font_size, "bold"))

    def _click(self, _e):
        if self._enabled and self.command:
            self.command()

    def set_text(self, t):
        self.text = t; self._draw(False)

    def set_enabled(self, b):
        self._enabled = b; self._draw(False)


class HeaderBar(tk.Canvas):
    """Glossy blue header that hosts a title and (optionally) other widgets."""

    def __init__(self, master, height=54):
        super().__init__(master, height=height, highlightthickness=0, bd=0)
        self.h = height
        self._img = None
        self.bind("<Configure>", self._redraw)

    def _redraw(self, e):
        self._img = ImageTk.PhotoImage(header_bar(max(e.width, 1), self.h))
        self.delete("bg")
        self.create_image(0, 0, anchor="nw", image=self._img, tags="bg")
        self.tag_lower("bg")


class Card(tk.Frame):
    """A glass panel with a drop shadow + rounded surface. Pack content into
    `card.body`; the card image (shadow + gradient surface + sheen) sits behind
    it and regenerates on resize. Replaces the flat white boxes with depth."""

    def __init__(self, master, radius=18, pad=14, accent=None, surface="#f6fcff"):
        super().__init__(master, bg=SKY_HEX, highlightthickness=0, bd=0)
        self.radius, self.pad, self.accent = radius, pad, accent
        self._img = None
        self._size = (0, 0)
        self._bg = tk.Label(self, bd=0, bg=SKY_HEX)
        self._bg.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=surface, highlightthickness=0, bd=0)
        # inset the body so the card's shadow + border show around it
        self.body.place(x=pad + 3, y=pad + 3, relwidth=1, relheight=1,
                        width=-(pad + 3) * 2, height=-(pad + 3) * 2)
        self.bind("<Configure>", self._on_configure, add="+")

    def _on_configure(self, e):
        if (e.width, e.height) == self._size or e.width < 30:
            return
        self._size = (e.width, e.height)
        self._img = ImageTk.PhotoImage(
            card_bg(e.width, e.height, self.radius, self.pad, accent=self.accent))
        self._bg.configure(image=self._img)


def run_splash(root: tk.Misc, on_done, title="ULTRA-PC",
               subtitle="Knowledge Explorer", duration=1600):
    """A landing overlay: scenic backdrop, a glass title card that fades/rises
    in, an animated gradient loading bar and rising bubbles — then it clears to
    reveal the app. `on_done()` is called when the animation finishes."""
    root.update_idletasks()
    W = max(root.winfo_width(), 900)
    H = max(root.winfo_height(), 600)
    cv = tk.Canvas(root, highlightthickness=0, bd=0, width=W, height=H)
    cv.place(x=0, y=0, relwidth=1, relheight=1)
    tk.Misc.lift(cv)   # NOT cv.lift(): Canvas.lift == tag_raise (item method)

    refs = {}
    refs["scene"] = ImageTk.PhotoImage(make_scene(W, H))
    cv.create_image(0, 0, anchor="nw", image=refs["scene"])

    # centered glass title card
    cw, ch = min(560, W - 80), 200
    cx, cy = W // 2, int(H * 0.42)
    refs["card"] = ImageTk.PhotoImage(
        card_bg(cw + 28, ch + 28, radius=22, pad=14,
                top=(255, 255, 255), bot=(206, 236, 255),
                accent=((150, 205, 110), (43, 143, 214))))
    card_item = cv.create_image(cx, cy + 30, image=refs["card"])

    title_item = cv.create_text(cx, cy - 24, text=title,
                                font=(FONT, 34, "bold"), fill="#0b3c5d")
    sub_item = cv.create_text(cx, cy + 16, text=subtitle,
                              font=(FONT, 15), fill="#2b8fd6")
    tag_item = cv.create_text(cx, cy + 46, text="offline · powered by your own AI",
                              font=(FONT, 10, "italic"), fill="#4a7fa5")

    # loading bar geometry
    bw, bx, by = min(360, W - 160), cx - min(360, W - 160) // 2, cy + 78
    cv.create_rectangle(bx, by, bx + bw, by + 8, outline="#9fd0f0",
                        fill="#eaf6ff", width=1)
    bar = cv.create_rectangle(bx, by, bx, by + 8, outline="", fill="#2b8fd6")

    # rising bubbles
    import random
    random.seed(3)
    bubbles = []
    for _ in range(18):
        r = random.randint(4, 16)
        x = random.randint(0, W); y = random.randint(H, H + 300)
        bubbles.append([cv.create_oval(x - r, y - r, x + r, y + r,
                        outline="#ffffff", fill="", width=2), x, y, r,
                        random.uniform(1.5, 4)])

    steps = max(12, duration // 40)
    state = {"i": 0}

    def _hex(a, b, t):
        return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def step():
        i = state["i"]; f = i / steps
        # loading bar fills + shifts hue green->aqua
        cv.coords(bar, bx, by, bx + int(bw * f), by + 8)
        cv.itemconfig(bar, fill=_hex((150, 205, 110), (43, 143, 214), f))
        # title rises + brightens slightly (fake fade via color lightening early)
        cv.coords(title_item, cx, (cy - 24) - int((1 - min(1, f * 2)) * 14))
        # bubbles float up
        for bub in bubbles:
            bub[2] -= bub[4]
            cv.coords(bub[0], bub[1] - bub[3], bub[2] - bub[3],
                      bub[1] + bub[3], bub[2] + bub[3])
        state["i"] += 1
        if i < steps:
            root.after(40, step)
        else:
            cv.destroy()
            on_done()

    root.after(120, step)
