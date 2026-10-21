"""The Ultra Archive — a space-museum gallery over the image indexes.

`ultra img gallery` opens a scrolling exhibition hall for the 6.8M+ indexed
images: a deep-space backdrop with a drifting starfield, exhibits descending
in a Z-path linked by gold constellation lines, museum plaques under every
artifact, and dimmed images floating in the background at a slower parallax
rate so the hall has real depth.  Styling nods to the Voyager Golden Record —
humanity's offline backup — which is exactly what this archive is.

Every launch draws a fresh random sample, so you never walk the same hall
twice — and the hall never ends: a curator thread streams new artifacts for
as long as you keep scrolling.  By default only the ZIM-served archives
(Wikipedia) are exhibited — personal folders stay out of the museum unless
named explicitly (`ultra img gallery pictures`).

The hall is CURATED.  Because every indexed image already has a CLIP vector,
topics are just text in the same vector space: each candidate is scored
against your allow-topics (history, art, maps, space, nature, …) and a block
list (nudity, gore, medical imagery), and only clear passers hang.  Edit the
topics with `ultra img topics add/remove/block "<topic>"` — that IS semantic
curation, no re-indexing ever.  Rate artifacts in the lightbox (♥ / ✕) and
the curator biases future picks toward your taste (persisted across visits).  Click an artifact for a lightbox with
its full plaque and an "open source" action.  Scrolling near the bottom pulls
more artifacts in — the corridor keeps going.

Layers (one tk.Canvas, three scroll rates):
    far   0.12x  starfield + gold nebula, tiled and wrapped
    mid   0.45x  small dim blurred artifacts drifting behind the exhibits
    fore  1.00x  framed exhibits + plaques + constellation path

Requires Pillow + tkinter; images are fetched from the local kiwix server
(started on demand) or from disk, decoded in worker threads, and handed to
the UI thread — the window never blocks on IO.
"""

from __future__ import annotations

import io
import json
import queue
import random
import threading
import urllib.request
from pathlib import Path

from . import core, imgsearch

# ---- the golden-archive palette — sourced from the design vault ------------ #
def _arch_tokens() -> dict:
    """The vault's `golden-archive` style is the single source of truth; the
    fallback keeps this module standalone if the vault isn't importable."""
    try:
        from . import assets
        t = assets.STYLES["golden-archive"]["tokens"]
        return {"bg": t["bg"], "bg2": t["bg2"], "gold": t["accent"],
                "gold2": t["accent2"], "text": t["text"], "muted": t["muted"],
                "line": t["border"], "plaque": t["surface"]}
    except Exception:
        return {"bg": "#04070f", "bg2": "#0a1224", "gold": "#d9b453",
                "gold2": "#f2dc9b", "text": "#e8e2d0", "muted": "#77809a",
                "line": "#5a4b2c", "plaque": "#0b101f"}


ARCH = _arch_tokens()

FONT = "Segoe UI"
SERIF = "Georgia"
MUTED, PAPER, AMBER = imgsearch.MUTED, imgsearch.PAPER, imgsearch.AMBER

_FORE_WIDTHS = (320, 380, 440, 500, 560)
_MAX_MASTER = 1100        # lightbox rendition long-side cap
_POOL_DEFAULT = 400       # kept for --count compat; now the curator buffer hint
_FIRST_BATCH = 22
_MORE_BATCH = 14
_KEEP_MASTERS = 40        # full-res kept for the newest N exhibits (RAM cap)

# ---- the curated exhibition policy ----------------------------------------- #
# Thresholds calibrated on 4000 real Wikipedia vectors (2026-07-04): allow
# p50=0.241, block p50=0.221; amin 0.21 + margin 0.02 keeps ~48% — roughly
# 3.3M museum-grade images.  The rejected tail is exactly the medical /
# explicit / morbid material plus low-signal chrome.
_GATE_AMIN = 0.21         # candidate must clearly resemble an allow topic
_GATE_MARGIN = 0.02       # …and beat its best block score by this much
_GATE_BCAP = 0.30         # …and never look strongly like a block topic
_TASTE_W = 0.35           # how hard ♥/✕ ratings steer the curator

DEFAULT_ALLOW = [
    "portrait of a historical figure",
    "classical painting, fine art",
    "an old map",
    "historical photograph",
    "vintage poster, magazine cover, print advertisement",
    "pop culture, film and music",
    "science and engineering",
    "nature landscape",
    "geography and terrain",
    "outer space, astronomy",
    "a wild animal",
    "plants, flowers, botany",
    "vintage technology, machines, inventions",
    "portrait of an artist, writer, philosopher or scientist",
    "architecture, famous buildings",
    "sculpture and monuments",
]
DEFAULT_BLOCK = [
    "nudity, exposed genitals, sexual content",
    "human genitalia close-up",
    "pornography",
    "gore, blood, graphic injury",
    "a corpse, dead body",
    "surgery, medical operation photo",
    "diseased skin, medical condition close-up",
]


# --------------------------------------------------------------------------- #
#  Pure helpers (testable without tk)
# --------------------------------------------------------------------------- #

def _catalog_no(meta: dict) -> str:
    """Deterministic museum catalog number for an artifact, e.g. UA-4F2A91."""
    import hashlib
    key = str(meta.get("hash") or meta.get("abs") or meta.get("file") or "?")
    return "UA-" + hashlib.md5(key.encode("utf-8")).hexdigest()[:6].upper()


def _zigzag_x(i: int) -> float:
    """X position (fraction of width) for exhibit i — a descending Z-path:
    left, right, left, right … with a centered beat every fifth exhibit."""
    if i % 5 == 4:
        return 0.5
    return 0.27 if (i % 2 == 0) else 0.73


def _mix_plan(counts: dict[str, int], n: int) -> dict[str, int]:
    """How many artifacts to sample per collection.  Sqrt-weighted so a 3k
    personal folder still shows up next to 6.8M Wikipedia images, and the
    biggest collection is capped at 85% so the mix stays a mix."""
    live = {k: c for k, c in counts.items() if c > 0}
    if not live:
        return {}
    w = {k: c ** 0.5 for k, c in live.items()}
    tot = sum(w.values())
    share = {k: v / tot for k, v in w.items()}
    if len(share) > 1:
        big = max(share, key=share.get)
        if share[big] > 0.85:
            excess = share[big] - 0.85
            share[big] = 0.85
            rest = sum(v for k, v in share.items() if k != big) or 1.0
            for k in share:
                if k != big:
                    share[k] += excess * share[k] / rest
    plan = {}
    for k, s in share.items():
        plan[k] = min(live[k], max(1, round(n * s)))
    return plan


def _plaque_lines(meta: dict, size: tuple[int, int] | None,
                  collection: str) -> tuple[str, str, str]:
    """The three plaque lines: TITLE / catalog · collection · dims / source."""
    title = str(meta.get("file") or "Untitled").strip()
    if len(title) > 52:
        title = title[:49] + "…"
    dims = f"{size[0]}×{size[1]}" if size else "—"
    mid = f"{_catalog_no(meta)}  ·  {collection}  ·  {dims}"
    abs_t = str(meta.get("abs", ""))
    src = ("Wikipedia — offline archive" if abs_t.startswith("http")
           else str(Path(abs_t).parent) if abs_t else "unknown origin")
    if len(src) > 58:
        src = "…" + src[-55:]
    return title.upper(), mid, src


# --------------------------------------------------------------------------- #
#  PIL set-dressing — starfield, gold disk, frames, plaques
# --------------------------------------------------------------------------- #

def _star_tile(w: int, h: int, seed: int) -> "Image.Image":
    """One tile of deep space: navy gradient, gold/indigo nebula blobs, and a
    few hundred stars (a handful with glow)."""
    from PIL import Image, ImageDraw, ImageFilter
    from . import nativeui as nui
    img = nui.vgrad(w, h, ARCH["bg"], ARCH["bg2"]).convert("RGBA")
    rnd = random.Random(seed)
    neb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neb)
    for col, alpha in (((90, 74, 32), 26), ((32, 42, 92), 34),
                       ((70, 56, 24), 18)):
        cx, cy = rnd.randint(0, w), rnd.randint(0, h)
        rr = int(min(w, h) * rnd.uniform(0.28, 0.5))
        nd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(*col, alpha))
    img.alpha_composite(neb.filter(ImageFilter.GaussianBlur(80)))
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 3800)):
        x, y = rnd.randint(0, w - 1), rnd.randint(0, h - 1)
        b = rnd.randint(70, 220)
        warm = rnd.random() < 0.22
        col = (b, int(b * 0.92), int(b * 0.62)) if warm else (b, b, min(255, b + 20))
        if rnd.random() < 0.08:                       # a bright one with glow
            glow = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse([6, 6, 12, 12], fill=(*col, 180))
            img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(3)),
                                (x - 9, y - 9))
            d.point((x, y), fill=(255, 255, 255, 255))
        else:
            d.point((x, y), fill=(*col, 255))
    return img.convert("RGB")


def _gold_disk(diam: int = 68) -> "Image.Image":
    """The Voyager-record motif: a grooved gold disk with a bright sweep."""
    from PIL import Image, ImageDraw, ImageFilter
    from . import nativeui as nui
    s = 4                                             # supersample for crisp rings
    D = diam * s
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gold, bright = nui._rgb(ARCH["gold"]), nui._rgb(ARCH["gold2"])
    dark = nui.darken(ARCH["gold"], 0.55)
    d.ellipse([0, 0, D - 1, D - 1], fill=(*dark, 255))
    step = max(2, D // 34)
    for i, r in enumerate(range(D // 2, D // 9, -step)):     # grooves
        c = gold if i % 2 else nui._mix(gold, dark, 0.55)
        d.ellipse([D // 2 - r, D // 2 - r, D // 2 + r, D // 2 + r],
                  outline=(*c, 255), width=max(1, step // 2))
    hole = D // 10
    d.ellipse([D // 2 - hole, D // 2 - hole, D // 2 + hole, D // 2 + hole],
              fill=(8, 10, 16, 255), outline=(*bright, 255), width=s)
    sweep = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(sweep).pieslice([0, 0, D - 1, D - 1], 205, 245,
                                   fill=(*bright, 90))
    img.alpha_composite(sweep.filter(ImageFilter.GaussianBlur(D // 16)))
    d.ellipse([0, 0, D - 1, D - 1], outline=(*bright, 220), width=s)
    return img.resize((diam, diam), Image.LANCZOS)


def _frame_exhibit(img, glow: bool = False) -> "Image.Image":
    """A museum frame: thin double gold border + soft halo on deep space."""
    from PIL import Image, ImageDraw, ImageFilter
    from . import nativeui as nui
    pad = 14
    w, h = img.size
    W, H = w + pad * 2, h + pad * 2
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gold = nui._rgb(ARCH["gold2" if glow else "gold"])
    ImageDraw.Draw(halo).rectangle([pad - 3, pad - 3, W - pad + 3, H - pad + 3],
                                   fill=(*gold, 70 if glow else 40))
    out.alpha_composite(halo.filter(ImageFilter.GaussianBlur(9)))
    out.paste(img.convert("RGB"), (pad, pad))
    d = ImageDraw.Draw(out)
    d.rectangle([pad - 1, pad - 1, W - pad, H - pad],
                outline=(*nui._rgb(ARCH["gold"]), 255), width=1)
    d.rectangle([pad - 4, pad - 4, W - pad + 3, H - pad + 3],
                outline=(*nui._rgb(ARCH["line"]), 255), width=1)
    return out


def _plaque_img(w: int, h: int = 66) -> "Image.Image":
    """A dark engraved plaque strip with a gold hairline rule."""
    from PIL import Image, ImageDraw
    from . import nativeui as nui
    img = nui.vgrad(w, h, ARCH["plaque"], nui.darken(ARCH["plaque"], 0.35))
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(*nui._rgb(ARCH["line"]), 255))
    d.line([(10, 2), (w - 10, 2)], fill=(*nui._rgb(ARCH["gold"]), 200))
    return img


def _dim_for_mid(img) -> "Image.Image":
    """Background-layer treatment: small, dark, blurred, cooled toward navy."""
    from PIL import Image, ImageEnhance, ImageFilter
    from . import nativeui as nui
    im = img.copy()
    im.thumbnail((190, 190))
    im = ImageEnhance.Brightness(im).enhance(0.28)
    im = im.filter(ImageFilter.GaussianBlur(2.6))
    veil = Image.new("RGB", im.size, nui._rgb(ARCH["bg2"]))
    return Image.blend(im.convert("RGB"), veil, 0.45)


# --------------------------------------------------------------------------- #
#  Curation policy — topics + taste, persisted next to the indexes
# --------------------------------------------------------------------------- #

def _gate(a: float, b: float) -> bool:
    """Does a candidate hang in the museum?  `a` = best allow-topic score,
    `b` = best block-topic score (CLIP cosines)."""
    return a >= _GATE_AMIN and (a - b) >= _GATE_MARGIN and b < _GATE_BCAP


def _topics_path() -> Path:
    return imgsearch._root() / "gallery_topics.json"


def load_topics() -> dict:
    """{'allow': [...], 'block': [...]} — user file over defaults."""
    try:
        t = json.loads(_topics_path().read_text(encoding="utf-8"))
        allow = [s for s in t.get("allow", []) if s.strip()]
        block = [s for s in t.get("block", []) if s.strip()]
        if allow and block:
            return {"allow": allow, "block": block}
    except Exception:
        pass
    return {"allow": list(DEFAULT_ALLOW), "block": list(DEFAULT_BLOCK)}


def save_topics(t: dict) -> None:
    imgsearch._root().mkdir(parents=True, exist_ok=True)
    core.write_atomic(_topics_path(), json.dumps(t, indent=2))


def _taste_path() -> Path:
    return imgsearch._root() / "gallery_taste.json"


def load_taste() -> dict:
    try:
        t = json.loads(_taste_path().read_text(encoding="utf-8"))
        return {"likes": list(t.get("likes", [])),
                "dislikes": list(t.get("dislikes", []))}
    except Exception:
        return {"likes": [], "dislikes": []}


def save_taste(t: dict) -> None:
    imgsearch._root().mkdir(parents=True, exist_ok=True)
    core.write_atomic(_taste_path(), json.dumps(t))


def _pref_vector(like_vecs: list, dislike_vecs: list):
    """The taste direction: toward what you ♥, away from what you ✕."""
    import numpy as np
    if not like_vecs and not dislike_vecs:
        return None
    dim = len(like_vecs[0]) if like_vecs else len(dislike_vecs[0])
    p = np.zeros(dim, dtype=np.float32)
    if like_vecs:
        p += np.mean(np.asarray(like_vecs, dtype=np.float32), axis=0)
    if dislike_vecs:
        p -= 0.6 * np.mean(np.asarray(dislike_vecs, dtype=np.float32), axis=0)
    n = float(np.linalg.norm(p))
    return p / n if n > 1e-6 else None


# --------------------------------------------------------------------------- #
#  Artifact pipeline — sample metas, fetch + decode off-thread
# --------------------------------------------------------------------------- #

def _exhibit_infos(infos: list[dict], only: str | None) -> list[dict]:
    """Which collections hang in the hall.  By default the museum shows only
    the ZIM-served archives (Wikipedia) — personal folders full of screenshots
    are not exhibition material unless named explicitly
    (`ultra img gallery pictures`).  Falls back to everything if no ZIM
    collection exists, so folder-only users still get a gallery."""
    if only:
        return [it for it in infos if it.get("name") == only]
    zim = [it for it in infos if str(it.get("source", "")).startswith("zim:")]
    return zim or infos


class _Coll:
    """Direct row access to one collection's vectors + metadata (either
    on-disk format), for the curator's gate — no images decoded to filter."""

    def __init__(self, info: dict):
        import numpy as np
        self.name = info["name"]
        self.model = info.get("model", "")
        self.count = int(info.get("count", 0))
        d = imgsearch._dir(self.name)
        f16 = d / "vectors.f16"
        if f16.exists():
            self.vecs = np.memmap(f16, dtype=np.float16, mode="r",
                                  shape=(self.count, int(info["dim"])))
            self.metas = imgsearch._JsonlMeta(
                d / "meta.jsonl", imgsearch._ensure_offsets(d, self.count))
        else:
            self.vecs = np.load(d / "vectors.npy")
            self.metas = json.loads((d / "meta.json").read_text(encoding="utf-8"))

    def vec(self, i: int):
        import numpy as np
        return np.asarray(self.vecs[i], dtype=np.float32)

    def meta(self, i: int) -> dict:
        return self.metas[i]


class Curator(threading.Thread):
    """Streams an endless, topic-gated, taste-biased sequence of artifacts.

    Runs the expensive setup (CLIP load, topic embedding) on its own thread so
    the hall opens instantly; then keeps a small buffer of accepted candidates
    filled.  Gating reads VECTORS, never images — candidates are judged in
    microseconds and only the accepted ones are ever fetched/decoded."""

    def __init__(self, infos: list[dict]):
        super().__init__(daemon=True)
        self.out: "queue.Queue" = queue.Queue(maxsize=64)
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._infos = infos
        self.topics = load_topics()
        self.taste = load_taste()
        self.ready = False          # topics embedded, gate active
        self.gated = 0              # rejected so far (for the HUD)
        self._seen: set = set()
        self._skip: set = set()     # (coll, idx) the user ✕'d — never again
        self._pref_dirty = True

    # -- called from the UI thread -------------------------------------- #
    def rate(self, coll: str, idx: int, meta: dict, up: bool) -> None:
        entry = {"coll": coll, "idx": int(idx),
                 "hash": str(meta.get("hash") or meta.get("abs") or "")}
        with self._lock:
            key = "likes" if up else "dislikes"
            self.taste[key] = [e for e in self.taste[key]
                               if e.get("hash") != entry["hash"]]
            self.taste[key].append(entry)
            other = "dislikes" if up else "likes"
            self.taste[other] = [e for e in self.taste[other]
                                 if e.get("hash") != entry["hash"]]
            save_taste(self.taste)
            if not up:
                self._skip.add((coll, int(idx)))
            self._pref_dirty = True

    def stop(self) -> None:
        self._stop.set()

    # -- worker side ------------------------------------------------------ #
    def run(self) -> None:
        import numpy as np
        try:
            colls = [_Coll(it) for it in self._infos if int(it.get("count", 0))]
        except Exception as exc:
            core.log("gallery", f"curator can't read indexes: {exc}", "ERROR")
            return
        weights = _mix_plan({c.name: c.count for c in colls}, 100)
        names = [c.name for c in colls]
        cum, byname = [], {c.name: c for c in colls}
        tot = 0
        for n in names:
            tot += weights.get(n, 0)
            cum.append(tot)

        # topic matrices per CLIP model (collections may differ)
        mats: dict[str, tuple] = {}

        def _matrices(model: str):
            if model not in mats:
                clip = imgsearch._get_clip(model)
                if clip is None:
                    mats[model] = None
                else:
                    with self._lock:
                        allow, block = (list(self.topics["allow"]),
                                        list(self.topics["block"]))
                    A = np.stack([imgsearch._embed_query(clip, t) for t in allow])
                    B = np.stack([imgsearch._embed_query(clip, t) for t in block])
                    mats[model] = (A, B)
            return mats[model]

        # taste: recover vectors for saved ratings
        pref = {}
        self._pref_dirty = True

        def _refresh_pref():
            with self._lock:
                likes, dislikes = list(self.taste["likes"]), list(self.taste["dislikes"])
                for e in dislikes:
                    if e.get("coll") in byname:
                        self._skip.add((e["coll"], int(e.get("idx", -1))))
            for c in colls:
                lv = [c.vec(int(e["idx"])) for e in likes
                      if e.get("coll") == c.name and 0 <= int(e.get("idx", -1)) < c.count]
                dv = [c.vec(int(e["idx"])) for e in dislikes
                      if e.get("coll") == c.name and 0 <= int(e.get("idx", -1)) < c.count]
                pref[c.name] = _pref_vector(lv, dv)
            self._pref_dirty = False

        rnd = random.Random()
        while not self._stop.is_set():
            if self.out.full():
                self._stop.wait(0.15)
                continue
            if self._pref_dirty:
                _refresh_pref()
            # pick a collection by the mix plan
            r = rnd.uniform(0, tot or 1)
            c = byname[names[next(i for i, v in enumerate(cum) if r <= v)]] \
                if tot else colls[0]
            i = rnd.randrange(c.count)
            if (c.name, i) in self._seen or (c.name, i) in self._skip:
                continue
            self._seen.add((c.name, i))
            m = _matrices(c.model)
            score = 0.0
            if m is not None:
                v = c.vec(i)
                a = float((m[0] @ v).max())
                b = float((m[1] @ v).max())
                self.ready = True
                if not _gate(a, b):
                    self.gated += 1
                    continue
                p = pref.get(c.name)
                score = a + (_TASTE_W * float(v @ p) if p is not None else 0.0)
            # taste-biased acceptance: weak candidates sometimes wait for better
            if score and rnd.random() > min(1.0, 0.55 + score):
                continue
            try:
                meta = c.meta(i)
            except Exception:
                continue
            self.out.put((meta, c.name, i))


def _fetch_master(meta: dict):
    """Bytes -> RGB PIL image (EXIF-corrected, long side capped), or None."""
    from PIL import Image, ImageOps
    target = str(meta.get("abs", ""))
    try:
        if target.startswith("http"):
            with urllib.request.urlopen(target, timeout=15) as r:
                data = r.read()
            img = Image.open(io.BytesIO(data))
            img.load()
            img = ImageOps.exif_transpose(img).convert("RGB")
        else:
            img = imgsearch._load_image(Path(target))
            if img is None:
                return None
        img.thumbnail((_MAX_MASTER, _MAX_MASTER))
        return img
    except Exception:
        return None


class _Loader:
    """Worker threads that turn queued metas into decoded PIL images."""

    def __init__(self, threads: int = 3):
        self.jobs: "queue.Queue" = queue.Queue()
        self.done: "queue.Queue" = queue.Queue()
        self._stop = threading.Event()
        for _ in range(threads):
            threading.Thread(target=self._run, daemon=True).start()

    def submit(self, meta: dict, collection: str, idx: int, kind: str) -> None:
        self.jobs.put((meta, collection, idx, kind))

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                meta, coll, idx, kind = self.jobs.get(timeout=0.4)
            except queue.Empty:
                continue
            master = _fetch_master(meta)
            if master is not None:
                self.done.put((meta, coll, idx, kind, master))


# --------------------------------------------------------------------------- #
#  The hall itself
# --------------------------------------------------------------------------- #

class Archive:
    def __init__(self, root, curator: Curator, total: int):
        import tkinter as tk
        from PIL import ImageTk
        self.tk, self.ImageTk = tk, ImageTk
        self.root = root
        self.curator = curator
        self.total = total
        self.cv = tk.Canvas(root, highlightthickness=0, bd=0, bg=ARCH["bg"])
        self.cv.pack(fill="both", expand=True)
        root.update_idletasks()
        self.W = max(root.winfo_width(), 1000)
        self.H = max(root.winfo_height(), 640)

        self.refs: dict = {}            # keep PhotoImage references alive
        self.exhibits: list[dict] = []  # {'items':[ids], 'meta', 'master', ...}
        self.offset = 0.0               # world scroll position (fore units)
        self.target = 0.0
        self.layer_pos = {"mid": 0.0, "fore": 0.0}
        self.next_y = 225.0             # next fore world-y (clears the header)
        self.mid_y = 160.0
        self.prev_anchor: tuple[float, float] | None = None
        self.pending = 0                # jobs in flight
        self.placed = 0                 # artifacts placed (fore + mid)
        self.modal_items: list[int] = []
        self.loader = _Loader()

        self._starfield()
        self._hud()
        self._request(_FIRST_BATCH)
        self.cv.bind_all("<MouseWheel>", self._wheel)
        root.bind("<Escape>", self._escape)
        root.protocol("WM_DELETE_WINDOW", self._close)
        self._tick()
        self._pump()

    # ---- far layer ---------------------------------------------------------- #
    def _starfield(self):
        self.tile_h = max(self.H + 400, 1200)
        tw = max(self.W, 1600)
        self.refs["star0"] = self.ImageTk.PhotoImage(
            _star_tile(tw, self.tile_h, seed=random.randint(0, 9999)))
        self.refs["star1"] = self.ImageTk.PhotoImage(
            _star_tile(tw, self.tile_h, seed=random.randint(0, 9999)))
        self.star_items = [
            self.cv.create_image(0, 0, anchor="nw", image=self.refs["star0"]),
            self.cv.create_image(0, self.tile_h, anchor="nw",
                                 image=self.refs["star1"])]

    def _place_stars(self):
        far = (self.offset * 0.12) % (self.tile_h * 2)
        for i, item in enumerate(self.star_items):
            y = i * self.tile_h - far
            if y < -self.tile_h:
                y += self.tile_h * 2
            self.cv.coords(item, 0, y)

    # ---- pinned header / footer --------------------------------------------- #
    def _hud(self):
        cv, W = self.cv, self.W
        self.refs["hud_bar"] = self.ImageTk.PhotoImage(_hud_bar(W, 96))
        cv.create_image(0, 0, anchor="nw", image=self.refs["hud_bar"],
                        tags="hud")
        self.refs["disk"] = self.ImageTk.PhotoImage(_gold_disk(64))
        cv.create_image(48, 48, image=self.refs["disk"], tags="hud")
        cv.create_text(96, 34, anchor="w", text="THE  ULTRA  ARCHIVE",
                       font=(FONT, 19, "bold"), fill=ARCH["gold2"], tags="hud")
        cv.create_text(96, 62, anchor="w",
                       text=f"{self.total:,} artifacts preserved · offline",
                       font=(SERIF, 11, "italic"), fill=ARCH["muted"],
                       tags="hud")
        cv.create_text(W - 20, 62, anchor="e",
                       text="scroll to walk the hall  ·  click an artifact  ·  Esc to leave",
                       font=(FONT, 9), fill=ARCH["muted"], tags="hud")
        self.hud_status = cv.create_text(
            W - 20, 34, anchor="e", text="curating the collection…",
            font=(SERIF, 10, "italic"), fill=ARCH["gold"], tags="hud")

    # ---- artifact requests (from the curator's endless stream) --------------- #
    def _request(self, n: int):
        for _ in range(n):
            try:
                meta, coll, idx = self.curator.out.get_nowait()
            except queue.Empty:
                return
            self.placed += 1
            kind = "mid" if (self.placed % 3 == 0) else "fore"
            self.loader.submit(meta, coll, idx, kind)
            self.pending += 1

    # ---- decoded images arriving from the workers ---------------------------- #
    def _pump(self):
        try:
            for _ in range(4):
                meta, coll, idx, kind, master = self.loader.done.get_nowait()
                self.pending -= 1
                if kind == "fore":
                    self._add_exhibit(meta, coll, idx, master)
                else:
                    self._add_mid(master)
        except queue.Empty:
            pass
        if self.curator.ready:
            n = len(self.curator.topics["allow"])
            self.cv.itemconfig(self.hud_status,
                               text=f"curated · {n} topics on view · "
                                    f"{self.curator.gated:,} artifacts declined")
        self.root.after(70, self._pump)

    def _add_mid(self, master):
        from PIL import Image  # noqa: F401
        im = _dim_for_mid(master)
        ph = self.ImageTk.PhotoImage(im)
        self.refs[f"mid{len(self.refs)}"] = ph
        x = random.uniform(0.08, 0.92) * self.W
        y = self.mid_y + random.uniform(0, 420)
        self.mid_y = y + 160
        item = self.cv.create_image(x, y - self.layer_pos["mid"], image=ph,
                                    tags="mid")
        self.cv.tag_lower(item)
        for s in self.star_items:
            self.cv.tag_lower(s)

    def _add_exhibit(self, meta: dict, coll: str, idx: int, master):
        cv = self.cv
        i = len(self.exhibits)
        w = random.choice(_FORE_WIDTHS)
        im = master.copy()
        im.thumbnail((w, 560))
        framed = _frame_exhibit(im)
        ph = self.ImageTk.PhotoImage(framed)
        pw = im.size[0] + 8
        plq = self.ImageTk.PhotoImage(_plaque_img(pw))
        tag = f"ex{i}"
        x = _zigzag_x(i) * self.W + random.uniform(-24, 24)
        y = self.next_y + framed.size[1] / 2
        sy = -self.layer_pos["fore"]          # current fore screen shift

        items = []
        # constellation connector from the previous exhibit
        if self.prev_anchor:
            px, py = self.prev_anchor
            items.append(cv.create_line(px, py + sy, x, y - framed.size[1] / 2 - 26 + sy,
                                        fill=ARCH["line"], dash=(2, 6),
                                        tags=("fore", tag)))
            for nx, ny in ((px, py), (x, y - framed.size[1] / 2 - 26)):
                items.append(cv.create_oval(nx - 3, ny - 3 + sy, nx + 3, ny + 3 + sy,
                                            outline=ARCH["gold2"], width=1,
                                            tags=("fore", tag)))
        items.append(cv.create_image(x, y + sy, image=ph, tags=("fore", tag)))

        lines = _plaque_lines(meta, im.size, coll)
        py0 = y + framed.size[1] / 2 + 30
        items.append(cv.create_image(x, py0 + sy, image=plq, tags=("fore", tag)))
        items.append(cv.create_text(x, py0 - 16 + sy, text=lines[0],
                                    font=(FONT, 10, "bold"), fill=ARCH["text"],
                                    width=pw - 20, tags=("fore", tag)))
        items.append(cv.create_text(x, py0 + 3 + sy, text=lines[1],
                                    font=(FONT, 8), fill=ARCH["gold"],
                                    tags=("fore", tag)))
        items.append(cv.create_text(x, py0 + 20 + sy, text=lines[2],
                                    font=(SERIF, 8, "italic"), fill=ARCH["muted"],
                                    tags=("fore", tag)))

        self.refs[f"ex{i}_img"], self.refs[f"ex{i}_plq"] = ph, plq
        rec = {"meta": meta, "coll": coll, "idx": idx, "master": master,
               "size": im.size, "items": items}
        self.exhibits.append(rec)
        # RAM cap on an endless hall: full-res masters only for the newest N
        # (the lightbox re-fetches older ones from the local server on demand)
        if len(self.exhibits) > _KEEP_MASTERS:
            self.exhibits[-_KEEP_MASTERS - 1]["master"] = None
        cv.tag_bind(tag, "<Button-1>", lambda e, r=rec: self._lightbox(r))
        cv.tag_bind(tag, "<Enter>", lambda e: cv.configure(cursor="hand2"))
        cv.tag_bind(tag, "<Leave>", lambda e: cv.configure(cursor=""))

        self.prev_anchor = (x, py0 + 44)
        self.next_y = py0 + 44 + random.uniform(56, 118)
        cv.tag_raise("hud")

    # ---- scrolling: eased parallax ------------------------------------------- #
    def _wheel(self, e):
        if self.modal_items:
            return
        self.target -= (e.delta / 120.0) * 130
        max_y = max(0.0, self.next_y - self.H + 300)
        self.target = min(max(self.target, 0.0), max_y)

    def _tick(self):
        d = self.target - self.offset
        if abs(d) > 0.4:
            self.offset += d * 0.18
            self._place_stars()
            for layer, rate in (("mid", 0.45), ("fore", 1.0)):
                want = self.offset * rate
                delta = want - self.layer_pos[layer]
                if abs(delta) > 0.01:
                    self.cv.move(layer, 0, -delta)
                    self.layer_pos[layer] = want
        # walking near the end of the hall? extend it — the curator never runs
        # out, so the hall has no end
        if self.pending < 6 and self.target > self.next_y - self.H * 2.2:
            self._request(_MORE_BATCH)
        self.root.after(16, self._tick)

    # ---- lightbox (with ♥ / ✕ curation) --------------------------------------- #
    def _lightbox(self, rec: dict):
        if self.modal_items:
            self._close_modal()
        cv, W, H = self.cv, self.W, self.H
        master = rec.get("master") or _fetch_master(rec["meta"])
        if master is None:
            return
        im = master.copy()
        im.thumbnail((W - 260, H - 260))
        framed = _frame_exhibit(im, glow=True)
        self.refs["modal_img"] = self.ImageTk.PhotoImage(framed)
        mi = []
        mi.append(cv.create_rectangle(-4, -4, W + 4, H + 4, fill=ARCH["bg"],
                                      stipple="gray75", outline="", tags="modal"))
        cx, cy = W / 2, H / 2 - 46
        mi.append(cv.create_image(cx, cy, image=self.refs["modal_img"],
                                  tags="modal"))
        lines = _plaque_lines(rec["meta"], master.size, rec["coll"])
        base = cy + framed.size[1] / 2 + 22
        mi.append(cv.create_text(cx, base, text=lines[0],
                                 font=(FONT, 12, "bold"), fill=ARCH["gold2"],
                                 tags="modal"))
        mi.append(cv.create_text(cx, base + 22, text=lines[1], font=(FONT, 9),
                                 fill=ARCH["gold"], tags="modal"))
        mi.append(cv.create_text(cx, base + 41, text=lines[2],
                                 font=(SERIF, 9, "italic"), fill=ARCH["muted"],
                                 tags="modal"))
        self.modal_items = mi
        target = str(rec["meta"].get("abs", ""))

        # action row: each its own item so clicks are unambiguous
        acts = [("♥  more like this", "act_up"), ("✕  less of this", "act_dn"),
                ("open source", "act_open"), ("close", "act_close")]
        n = len(acts)
        for k, (label, atag) in enumerate(acts):
            ax = cx + (k - (n - 1) / 2) * 170
            mi.append(cv.create_text(ax, base + 70, text=f"[ {label} ]",
                                     font=(FONT, 10, "bold"), fill=ARCH["text"],
                                     tags=("modal", atag)))

        def _feedback(atag, txt):
            cv.itemconfig(atag, text=txt, fill=ARCH["gold2"])

        def _rate(up):
            self.curator.rate(rec["coll"], rec.get("idx", -1), rec["meta"], up)
            _feedback("act_up" if up else "act_dn",
                      "♥ saved — curating…" if up else "✕ noted — less of this")

        def _bg_click(_e):
            # clicks on an action item also carry an act_* tag — leave those
            # to their own handlers; anything else closes the lightbox
            tags = cv.gettags("current")
            if not any(str(t).startswith("act_") for t in tags):
                self._close_modal()

        cv.tag_bind("act_up", "<Button-1>", lambda e: _rate(True))
        cv.tag_bind("act_dn", "<Button-1>", lambda e: _rate(False))
        cv.tag_bind("act_open", "<Button-1>", lambda e: _open_target(target))
        cv.tag_bind("act_close", "<Button-1>", lambda e: self._close_modal())
        cv.tag_bind("modal", "<Button-1>", _bg_click, add="+")
        self.root.bind("+", lambda e: _rate(True))
        self.root.bind("-", lambda e: _rate(False))
        cv.tag_raise("modal")

    def _close_modal(self):
        self.cv.delete("modal")
        self.modal_items = []
        self.root.unbind("+")
        self.root.unbind("-")

    def _escape(self, _e=None):
        if self.modal_items:
            self._close_modal()
        else:
            self._close()

    def _close(self):
        self.loader.stop()
        self.curator.stop()
        self.root.destroy()


def _hud_bar(w: int, h: int) -> "Image.Image":
    """Translucent header band with a gold hairline — pinned over the hall."""
    from PIL import Image, ImageDraw
    from . import nativeui as nui
    img = nui.vgrad(w, h, nui.darken(ARCH["bg"], 0.1), ARCH["bg"]).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.line([(0, h - 2), (w, h - 2)], fill=(*nui._rgb(ARCH["gold"]), 170))
    d.line([(0, h - 1), (w, h - 1)], fill=(*nui._rgb(ARCH["line"]), 255))
    return img


def _open_target(target: str) -> None:
    try:
        if target.startswith("http"):
            import webbrowser
            webbrowser.open(target)
        elif target:
            core.open_in_os(Path(target))
    except Exception as exc:
        core.log("gallery", f"open failed: {exc}", "WARN")


# --------------------------------------------------------------------------- #
#  Entry
# --------------------------------------------------------------------------- #

def open_gallery(only: str | None = None, pool_size: int = _POOL_DEFAULT,
                 snapshot: str | None = None, auto_ms: int = 0) -> int:
    try:
        import tkinter as tk
        from PIL import ImageTk  # noqa: F401
    except Exception:
        print("  gallery needs tkinter + Pillow")
        return 1

    infos = imgsearch.list_indexes()
    if only and not any(it.get("name") == only for it in infos):
        print(f"  no collection named '{only}' — try `ultra img list`")
        return 1
    if not infos:
        print("  nothing indexed yet — `ultra img index <folder>` or "
              "`ultra img index-zim <zim>` first")
        return 1
    exhibit = _exhibit_infos(infos, only)
    total = sum(int(it.get("count", 0)) for it in exhibit)

    # ZIM-served artifacts need the local kiwix server
    if any(str(it.get("source", "")).startswith("zim:") for it in exhibit):
        try:
            from . import knowledge
            knowledge.serve_start()
        except Exception:
            pass

    curator = Curator(exhibit)
    curator.start()

    root = tk.Tk()
    root.title("The Ultra Archive")
    root.geometry("1200x780")
    root.configure(bg=ARCH["bg"])
    # open front-and-center (momentary topmost — not pinned)
    root.lift()
    root.attributes("-topmost", True)
    root.after(800, lambda: root.attributes("-topmost", False))
    hall = Archive(root, curator, total)

    if snapshot:                       # verification hook: grab a frame + exit
        def _shoot():
            try:
                from PIL import ImageGrab
                root.attributes("-topmost", True)   # make sure we're the one on film
                root.update()
                x, y = root.winfo_rootx(), root.winfo_rooty()
                ImageGrab.grab((x, y, x + root.winfo_width(),
                                y + root.winfo_height())).save(snapshot)
            finally:
                hall._close()
        root.after(max(auto_ms, 1500), _shoot)
    root.mainloop()
    return 0


def cli(args: list[str]) -> int:
    only, pool, snapshot, auto = None, _POOL_DEFAULT, None, 0
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--count" and i + 1 < len(args):
            try:
                pool = max(10, int(args[i + 1]))
            except ValueError:
                pass
            i += 2
        elif a == "--snapshot" and i + 1 < len(args):
            snapshot = args[i + 1]; i += 2
        elif a == "--wait" and i + 1 < len(args):
            try:
                auto = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            only = a; i += 1
    return open_gallery(only, pool, snapshot, auto)


# --------------------------------------------------------------------------- #
#  Topic curation CLI — `ultra img topics ...`
# --------------------------------------------------------------------------- #

def cli_topics(args: list[str]) -> int:
    from . import cliart as ca
    from .ui import _aero_colors
    _, green, _ = _aero_colors()
    t = load_topics()

    def _show() -> int:
        print()
        print(ca.color("  ▸ gallery topics — what hangs in the museum", green))
        print(ca.color("    on view:", PAPER))
        for s in t["allow"]:
            print(ca.color(f"      · {s}", PAPER))
        print(ca.color("    never shown:", AMBER))
        for s in t["block"]:
            print(ca.color(f"      · {s}", MUTED))
        print(ca.color('\n    curate:  ultra img topics add "<topic>"'
                       '   [--block]', MUTED))
        print(ca.color('             ultra img topics remove "<topic>"'
                       "   ·   ultra img topics reset", MUTED))
        return 0

    if not args:
        return _show()
    op = args[0].lower()
    if op == "reset":
        save_topics({"allow": list(DEFAULT_ALLOW), "block": list(DEFAULT_BLOCK)})
        print(ca.color("  ✓ topics reset to the default exhibition", green))
        return 0
    if op in ("add", "block") and len(args) > 1:
        topic = " ".join(a for a in args[1:] if a != "--block").strip()
        key = "block" if (op == "block" or "--block" in args) else "allow"
        if topic and topic not in t[key]:
            t[key].append(topic)
            save_topics(t)
        word = "never shown" if key == "block" else "on view"
        print(ca.color(f'  ✓ "{topic}" — {word} (applies next visit)', green))
        return 0
    if op in ("remove", "rm", "unblock") and len(args) > 1:
        topic = " ".join(args[1:]).strip().lower()
        n0 = len(t["allow"]) + len(t["block"])
        t["allow"] = [s for s in t["allow"] if s.lower() != topic]
        t["block"] = [s for s in t["block"] if s.lower() != topic]
        if len(t["allow"]) + len(t["block"]) < n0:
            save_topics(t)
            print(ca.color(f'  ✓ "{topic}" removed (applies next visit)', green))
        else:
            print(ca.color(f'  ? no topic matching "{topic}" — current list:',
                           AMBER))
            _show()
        return 0
    return _show()
