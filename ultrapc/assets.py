"""Design & Art Assets vault — a curated, offline library of color palettes,
CSS snippets, and animations so anything we build (or vibe-code) starts from
"polished" instead of "default".

Two halves:
  * Curated seed content lives in THIS module (version-controlled Python data)
    and is written to disk by `sync()`, which also regenerates the machine-
    readable manifest.json and the DESIGN-SYSTEM.md catalog that Claude reads
    before building UIs.
  * Vendored open-source libraries (Animate.css, fonts, particles, ...) live on
    disk under the vault and are scanned into the manifest.

Storage:  C:\\Ultra-PC-Assets\\  (large, external — like the knowledge vault)
CLI:      python ultra.py assets <palettes|css|anim|show|scaffold|status|sync>

Stdlib-only; Pillow/numpy not required. Terminal swatches use ANSI truecolor.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from . import core, ui

# --------------------------------------------------------------------------- #
#  Where the vault lives
# --------------------------------------------------------------------------- #

def _default_root() -> Path:
    if core.IS_WINDOWS:
        return Path("C:/Ultra-PC-Assets")
    return core.ROOT / "assets-vault"


ASSETS_DIR = _default_root()
PALETTE_DIR = ASSETS_DIR / "palettes"
CSS_DIR = ASSETS_DIR / "css"
ANIM_DIR = ASSETS_DIR / "animations"
FONT_DIR = ASSETS_DIR / "fonts"
LIB_DIR = ASSETS_DIR / "libraries"
GRAD_DIR = ASSETS_DIR / "gradients"
PATTERN_DIR = ASSETS_DIR / "patterns"
ART_DIR = ASSETS_DIR / "svg-art"
LAYOUT_DIR = ASSETS_DIR / "layouts"
TECH_DIR = ASSETS_DIR / "techniques"
CREATIVE_DIR = ASSETS_DIR / "creative"
ASCII_DIR = ASSETS_DIR / "ascii-art"
NATIVE_DIR = ASSETS_DIR / "native"
PROFILE_DIR = ASSETS_DIR / "profiles"
SHAPES_DIR = ASSETS_DIR / "shapes"
EXPORT_DIR = ASSETS_DIR / "exports"
MANIFEST = ASSETS_DIR / "manifest.json"
CATALOG = ASSETS_DIR / "DESIGN-SYSTEM.md"
SHOWCASE = ASSETS_DIR / "showcase.html"

# --------------------------------------------------------------------------- #
#  Curated palettes  (real, hand-picked hex — quality over quantity)
# --------------------------------------------------------------------------- #

PALETTES: list[dict] = [
    # ---- Frutiger Aero ---------------------------------------------------- #
    {"id": "frutiger-aero-sky", "style": "frutiger-aero",
     "name": "Frutiger Aero — Sky",
     "tags": ["aqua", "glossy", "nature", "optimistic", "clean"],
     "colors": ["#2b8fd6", "#60b2f0", "#ceecff", "#eaf6ff", "#ffffff",
                "#96cd6e", "#4e9638", "#0b3c5d"],
     "notes": "Glossy sky-blue + green-hills palette. Deep blue (#0b3c5d) for "
              "text, white/glass for surfaces, aqua for accents."},
    {"id": "frutiger-aqua-gloss", "style": "frutiger-aero",
     "name": "Frutiger Aero — Aqua Gloss",
     "tags": ["water", "gel", "bubbles", "shine"],
     "colors": ["#00a3e0", "#38c6f4", "#8fe3ff", "#d6f6ff", "#ffffff",
                "#0077b6", "#023e8a"],
     "notes": "Wetter, gel-button feel. Pair light-to-dark for glossy 3D."},
    {"id": "frutiger-nature-tech", "style": "frutiger-aero",
     "name": "Frutiger Aero — Nature Tech",
     "tags": ["eco", "leaf", "fresh", "edutainment"],
     "colors": ["#7ac74f", "#a8e063", "#d9f2b4", "#eafbe0", "#ffffff",
                "#2b8fd6", "#1b6ca8"],
     "notes": "Green-forward 'technology + nature' harmony from the era's ads."},

    # ---- Vaporwave / Y2K -------------------------------------------------- #
    {"id": "vaporwave-sunset", "style": "vaporwave",
     "name": "Vaporwave — Sunset",
     "tags": ["neon", "pastel", "80s", "retro", "gradient"],
     "colors": ["#ff71ce", "#b967ff", "#01cdfe", "#05ffa1", "#fffb96",
                "#2d1b4e", "#1a1a2e"],
     "notes": "The canonical vaporwave five (pink/purple/cyan/green/yellow) "
              "over a deep indigo night."},
    {"id": "y2k-chrome", "style": "vaporwave",
     "name": "Y2K — Chrome & Bubblegum",
     "tags": ["y2k", "chrome", "metallic", "millennium", "shine"],
     "colors": ["#c0c6d0", "#e8ecf3", "#ff5fa2", "#7b6cff", "#5ff0ff",
                "#20123a", "#ffffff"],
     "notes": "Liquid-chrome silver with hot-pink + cyber-lilac accents. Use "
              "the silvers as gradients for that metallic Y2K sheen."},
    {"id": "miami-nights", "style": "vaporwave",
     "name": "Vaporwave — Miami Nights",
     "tags": ["synthwave", "teal", "magenta", "palm", "dusk"],
     "colors": ["#ff2e97", "#00e5ff", "#8a2be2", "#ffcf40", "#0f1b3d",
                "#071130"],
     "notes": "Teal↔magenta gradient dusk. Great for hero backgrounds."},

    # ---- Neon / Cyberpunk ------------------------------------------------- #
    {"id": "cyberpunk-night", "style": "cyberpunk",
     "name": "Cyberpunk — Night City",
     "tags": ["neon", "dark", "hacker", "high-contrast", "glow"],
     "colors": ["#0d0221", "#01012b", "#ff2a6d", "#05d9e8", "#d1f7ff",
                "#f9f002", "#7700ff"],
     "notes": "Near-black backgrounds with hot-pink/cyan glow accents. Pair "
              "accent on dark and add a glow shadow of the same hue."},
    {"id": "neon-terminal", "style": "cyberpunk",
     "name": "Neon — Terminal Green",
     "tags": ["matrix", "crt", "mono", "hacker"],
     "colors": ["#000000", "#0a1a0a", "#00ff41", "#00d4aa", "#39ff14",
                "#0affef"],
     "notes": "Classic phosphor-green terminal. Use with a monospace font and "
              "a subtle scanline overlay."},
    {"id": "synthwave-grid", "style": "cyberpunk",
     "name": "Neon — Synthwave Grid",
     "tags": ["synthwave", "grid", "sunset", "outrun"],
     "colors": ["#ff006e", "#fb5607", "#ffbe0b", "#8338ec", "#3a86ff",
                "#12002b"],
     "notes": "Outrun sunset ramp (pink→orange→yellow) over violet, plus a "
              "blue for the perspective grid floor."},

    # ---- Neutral utility (every app needs backgrounds + text) ------------- #
    {"id": "ink-and-glass", "style": "neutral",
     "name": "Neutral — Ink & Glass",
     "tags": ["neutral", "ui", "slate", "readable"],
     "colors": ["#0f172a", "#1e293b", "#334155", "#94a3b8", "#e2e8f0",
                "#f8fafc", "#ffffff"],
     "notes": "Slate neutral ramp for text, surfaces, and borders on any theme."},
    {"id": "warm-sand", "style": "neutral",
     "name": "Neutral — Warm Sand",
     "tags": ["neutral", "warm", "paper", "cozy"],
     "colors": ["#1c1917", "#44403c", "#78716c", "#d6d3d1", "#f5f5f4",
                "#fafaf9", "#ffffff"],
     "notes": "Warm stone neutrals — softer than pure grey for cozy/editorial UIs."},

    # ---- Pastel  (light, soft — the counterweight to neon/dark) ------------ #
    {"id": "pastel-dream", "style": "pastel",
     "name": "Pastel — Dream",
     "tags": ["soft", "light", "airy", "kawaii", "calm"],
     "colors": ["#ffd1dc", "#ffe5b4", "#c7ceea", "#b5ead7", "#e2f0cb",
                "#fff5e1", "#6d5d6e"],
     "notes": "Low-saturation dreamy pastels on cream. Deliberate opposite of "
              "the neon sets — reach here for gentle, friendly, high-key UIs."},
    {"id": "cotton-candy", "style": "pastel",
     "name": "Pastel — Cotton Candy",
     "tags": ["pink", "blue", "sweet", "bubbly", "light"],
     "colors": ["#ffafcc", "#ffc8dd", "#bde0fe", "#a2d2ff", "#cdb4db",
                "#ffffff"],
     "notes": "Pink↔blue candy pastels. Great for playful gradients on white."},

    # ---- Earthy  (muted, organic, warm — juxtaposes glossy aqua/neon) ----- #
    {"id": "terracotta-clay", "style": "earthy",
     "name": "Earthy — Terracotta Clay",
     "tags": ["terracotta", "warm", "muted", "organic", "artisan"],
     "colors": ["#c1440e", "#e07856", "#e6a57e", "#d9c5a0", "#8a9a5b",
                "#f5efe6", "#3b2f2a"],
     "notes": "Burnt clay + sage + oat on warm cream. Grounded, hand-made feel."},
    {"id": "sage-stone", "style": "earthy",
     "name": "Earthy — Sage & Stone",
     "tags": ["sage", "green", "muted", "calm", "natural"],
     "colors": ["#7d8c5c", "#a3b18a", "#cbd5c0", "#dad7cd", "#8d8177",
                "#f4f1ea", "#40483a"],
     "notes": "Muted eucalyptus greens and stone — spa-calm, wellness, organic."},
    {"id": "desert-sunset", "style": "earthy",
     "name": "Earthy — Desert Sunset",
     "tags": ["desert", "warm", "dusty", "rose", "adobe"],
     "colors": ["#e07a5f", "#f2cc8f", "#e6b89c", "#cd9777", "#81574a",
                "#3d405b"],
     "notes": "Adobe orange, sand, and dusty rose against a deep dusk navy."},
    {"id": "autumn-warmth", "style": "earthy",
     "name": "Earthy — Autumn Warmth",
     "tags": ["autumn", "rust", "mustard", "burgundy", "cozy"],
     "colors": ["#6f1d1b", "#99582a", "#bb9457", "#dda15e", "#e9c46a",
                "#f4ede4", "#432818"],
     "notes": "Rust, mustard, and burgundy — harvest-season warmth."},
    {"id": "coastal-calm", "style": "earthy",
     "name": "Earthy — Coastal Calm",
     "tags": ["coastal", "teal", "sand", "balanced", "friendly"],
     "colors": ["#264653", "#2a9d8f", "#8ab17d", "#e9c46a", "#e76f51",
                "#f4f1de"],
     "notes": "The popular teal→sand→coral scheme. Versatile, warm-but-fresh."},
    {"id": "retro-70s", "style": "earthy",
     "name": "Earthy — Retro 70s",
     "tags": ["retro", "avocado", "harvest-gold", "vintage", "warm"],
     "colors": ["#a44a3f", "#d68c45", "#e0b04a", "#6b8e5a", "#4a6d7c",
                "#f0e6d2"],
     "notes": "Avocado + harvest-gold + rust — 1970s vintage without the neon."},

    # ---- Editorial  (minimal, high-key, one bold accent) ------------------ #
    {"id": "editorial-ink", "style": "editorial",
     "name": "Editorial — Ink on Paper",
     "tags": ["minimal", "editorial", "monochrome", "magazine", "clean"],
     "colors": ["#111111", "#2b2b2b", "#6b6b6b", "#cfcfcf", "#f2f2f2",
                "#ffffff", "#e11d2a"],
     "notes": "Ink-black type on paper-white with a single red accent. "
              "Restrained, magazine-grade — the anti-vaporwave."},
    {"id": "swiss-minimal", "style": "editorial",
     "name": "Editorial — Swiss Minimal",
     "tags": ["swiss", "grid", "minimal", "bold", "functional"],
     "colors": ["#000000", "#ffffff", "#ff3b30", "#0a84ff", "#f2f2f7",
                "#8e8e93"],
     "notes": "Black/white with one red + one blue — International Typographic "
              "Style. Let whitespace and type do the work."},

    # ---- Mono  (brutalist, high-contrast grayscale) ----------------------- #
    {"id": "mono-noir", "style": "mono",
     "name": "Mono — Noir",
     "tags": ["monochrome", "brutalist", "high-contrast", "dark", "stark"],
     "colors": ["#0a0a0a", "#262626", "#525252", "#a3a3a3", "#d4d4d4",
                "#f5f5f5", "#ffffff"],
     "notes": "Pure grayscale ramp for stark, brutalist, type-driven dark UIs."},
    {"id": "ivory-charcoal", "style": "mono",
     "name": "Mono — Ivory & Charcoal",
     "tags": ["monochrome", "warm-grey", "soft", "elegant"],
     "colors": ["#1a1a1a", "#3d3d3d", "#767676", "#b8b3aa", "#e8e4dc",
                "#faf8f3"],
     "notes": "Warm-toned greyscale — softer, more elegant than pure noir."},

    # ---- Jewel + Nordic  (rich/refined, saturated but NOT neon) ----------- #
    {"id": "jewel-royal", "style": "jewel",
     "name": "Jewel — Royal",
     "tags": ["jewel", "gold", "luxe", "deep", "sophisticated"],
     "colors": ["#14213d", "#1b2a4a", "#5f0f40", "#0f766e", "#7c3aed",
                "#d4af37", "#f8f4e8"],
     "notes": "Navy + plum + emerald + amethyst with a gold accent. Deep and "
              "luxe — richness of the neon sets without the glow."},
    {"id": "forest-botanical", "style": "jewel",
     "name": "Jewel — Forest Botanical",
     "tags": ["forest", "green", "deep", "botanical", "rich"],
     "colors": ["#081c15", "#1b4332", "#2d6a4f", "#40916c", "#74c69d",
                "#b7e4c7", "#d8f3dc"],
     "notes": "A deep-to-pale green ramp — lush, botanical, calming depth."},
    {"id": "nordic-frost", "style": "nordic",
     "name": "Nordic — Frost",
     "tags": ["nordic", "muted", "cool", "hygge", "calm"],
     "colors": ["#2e3440", "#3b4252", "#4c566a", "#88c0d0", "#a3be8c",
                "#d8dee9", "#eceff4"],
     "notes": "The Nord palette — muted slate blues with soft frost + sage. "
              "Cool, quiet, easy on the eyes for long sessions."},
    {"id": "golden-archive", "style": "golden-archive",
     "name": "Golden Archive — Voyager Record",
     "tags": ["gold", "space", "museum", "dark", "archive", "voyager",
              "starfield", "engraved"],
     "colors": ["#04070f", "#0a1224", "#0b101f", "#5a4b2c", "#d9b453",
                "#f2dc9b", "#e8e2d0"],
     "notes": "Deep-space navy with engraved gold — the Voyager Golden Record "
              "as a UI. Museum plaques, starfields, thin gold artifact frames, "
              "italic serif captions. Born in the Ultra Archive gallery."},
    {"id": "ultraviolet-bloom", "style": "ultraviolet",
     "name": "Ultraviolet — Bloom",
     "tags": ["violet", "indigo", "electric", "dark", "complement", "neon"],
     "colors": ["#0a0618", "#150e2e", "#1a1238", "#3c2f6e", "#8a70ff",
                "#c77dff", "#ece7ff"],
     "notes": "The color-wheel complement of Golden Archive's gold: deep "
              "indigo with electric violet. Pair them across a two-app "
              "workflow and they sing."},
    {"id": "ember-forge", "style": "ember",
     "name": "Ember — Forge",
     "tags": ["orange", "warm", "dark", "fire", "complement", "charcoal"],
     "colors": ["#140d0a", "#241511", "#2a1a14", "#4d2e1f", "#ff6b35",
                "#ffc15e", "#ffefe2"],
     "notes": "Charcoal + burnt orange + amber — the warm complement of "
              "frutiger-aero's cool blue. Forge-glow energy for dark tools."},
    {"id": "signal-contrast", "style": "hi-contrast",
     "name": "Hi-Contrast — Signal",
     "tags": ["contrast", "accessibility", "black", "yellow", "aaa", "bold"],
     "colors": ["#000000", "#0d0d0d", "#101010", "#ffe600", "#c7c7c7", "#ffffff"],
     "notes": "Black/white with one signal yellow and a neutral ramp. White "
              "and yellow carry text on black; check each actual foreground "
              "and background pair before using the intermediate greys."},

    # ---- design-profile archetype palettes (see PROFILES) ------------------ #
    {"id": "avant-play", "style": "avant-basic",
     "name": "Avant Basic — Playhouse",
     "tags": ["avant-basic", "checkerboard", "squiggle", "retro", "maximalist",
              "memphis"],
     "colors": ["#f6e7ee", "#d81b7a", "#5438dc", "#f3a712", "#7fc243",
                "#3a2038", "#fffaf5"],
     "notes": "Shein-era Instagram maximalism: bright retro pastels + hot pink "
              "and cobalt for warped checkerboards, squiggles and daisies. "
              "Clash on purpose — matching is the only mistake."},
    {"id": "living-earth", "style": "organic-tech",
     "name": "Organic Tech — Living Earth",
     "tags": ["organic", "biomorphic", "sage", "moss", "clay", "calm",
              "biophilic"],
     "colors": ["#edeee4", "#dfe4d2", "#52704a", "#8ba888", "#a5643a",
                "#d9c8a9", "#262e22"],
     "notes": "Sage, moss, clay, sand — the biophilic 'living earth' set. "
              "Everything flows: no hard corners, gradients shift within "
              "shapes, forms read as cells or water."},
    {"id": "runway-ivory", "style": "high-fashion",
     "name": "High Fashion — Runway",
     "tags": ["fashion", "editorial", "luxury", "ivory", "black", "champagne",
              "vogue"],
     "colors": ["#f7f4ee", "#ffffff", "#141414", "#8e7747", "#b4a284",
                "#6b665c", "#d8d2c5"],
     "notes": "Ivory, ink black, champagne. The palette whispers so the "
              "typography (Didone serifs, huge scale contrast) and the "
              "whitespace can do the talking."},
    {"id": "grip-tape", "style": "skate-culture",
     "name": "Skate Culture — Grip Tape",
     "tags": ["skate", "street", "grunge", "sticker", "asphalt", "urban"],
     "colors": ["#141518", "#1f2125", "#ff5c1f", "#ffd23f", "#e63946",
                "#989fa8", "#f1efe8"],
     "notes": "Asphalt + safety orange + hazard yellow with a hit of red — "
              "deck-art energy. Wants grain, distress, sticker outlines and "
              "hand-marker type, never polish."},
    {"id": "trencadis", "style": "mosaic",
     "name": "Mosaic — Trencadís",
     "tags": ["mosaic", "terrazzo", "tile", "gaudi", "stained-glass",
              "fragments"],
     "colors": ["#f1ece0", "#16697a", "#a8442c", "#d9a441", "#4a7c59",
                "#6f6a5b", "#2b2721"],
     "notes": "Glazed-tile fragments on plaster: teal, terracotta, ochre, "
              "moss with warm grout. Broken-then-recomposed — every surface "
              "is a field of chips."},
    {"id": "gatsby-gold", "style": "art-deco",
     "name": "Art Deco — Gatsby",
     "tags": ["art-deco", "gold", "gatsby", "sunburst", "geometric", "1920s",
              "luxury"],
     "colors": ["#12100c", "#d4af37", "#2f9e77", "#25567b", "#8c2f39",
                "#99907a", "#f0e7d0"],
     "notes": "Black + gold + jewel accents (emerald, sapphire, ruby). "
              "High-contrast metallics, graduated sunbursts, stepped frames, "
              "strict symmetry — controlled opulence."},
    {"id": "metro-bloom", "style": "frutiger-metro",
     "name": "Frutiger Metro — Bloom",
     "tags": ["frutiger-metro", "vector", "bloom", "flat", "2000s", "vivid"],
     "colors": ["#ffffff", "#c81e82", "#8ec400", "#00a5cf", "#f97a00",
                "#7a3fb8", "#22303b"],
     "notes": "Frutiger Aero's flat 2D sibling: loud magenta/lime/aqua/orange "
              "vector blooms, flourishes and silhouettes on clean white — "
              "humanist type, full-spectrum gradients, zero gloss."},
    {"id": "millennium-chrome", "style": "y2k-chrome",
     "name": "Y2K — Millennium Chrome",
     "tags": ["y2k", "chrome", "silver", "futurism", "millennium", "blob"],
     "colors": ["#eef2f7", "#dfe7f2", "#8fa5bc", "#2e5fd0", "#7de0e6",
                "#c9b8e8", "#1a2333"],
     "notes": "Liquid chrome, ice white and electric blue with translucent "
              "candy accents — the future as it looked from 1999: a silver "
              "showroom where every object floats."},
    {"id": "candlelit-study", "style": "dark-academia",
     "name": "Dark Academia — Candlelit Study",
     "tags": ["academia", "walnut", "oxblood", "brass", "parchment",
              "scholarly", "moody"],
     "colors": ["#201812", "#2c221a", "#8c3838", "#3e4a36", "#b08d4f",
                "#96876f", "#e9ddc8"],
     "notes": "Walnut, oxblood, forest and old brass under parchment — "
              "everything steeped in tea and time. Knowledge as romance; "
              "libraries as cathedrals."},
    {"id": "swiss-signal", "style": "swiss-international",
     "name": "Swiss — Signal Red",
     "tags": ["swiss", "grid", "helvetica", "red", "objective", "modernist"],
     "colors": ["#ffffff", "#f2f2f2", "#d9d9d9", "#595959", "#111111",
                "#d0021b", "#0a4d8c"],
     "notes": "White field, black ink, one signal red. Color is information, "
              "never decoration — if red appears twice it means two "
              "things."},
    {"id": "mall-prep", "style": "preppy-2000s",
     "name": "2000s Preppy — Mall Prep",
     "tags": ["preppy", "2000s", "argyle", "polo", "navy", "collegiate"],
     "colors": ["#f7f2e6", "#1e3a67", "#c22f6d", "#2b7a3d", "#7fb2e5",
                "#d9c04a", "#23304b"],
     "notes": "Polo navy + pink + kelly green on cream: argyle, gingham, "
              "crests and varsity slab type — collegiate optimism, mall-era "
              "gloss kept to a clean sheen."},
]

# --------------------------------------------------------------------------- #
#  Design tokens per style — the :root variables scaffolds and exports use
# --------------------------------------------------------------------------- #

STYLES: dict[str, dict] = {
    "frutiger-aero": {
        "label": "Frutiger Aero", "font": "'Segoe UI', system-ui, sans-serif",
        "mono": "'Cascadia Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#ceecff", "bg2": "#eaf6ff", "surface": "#ffffff",
            "surface-glass": "rgba(255,255,255,0.55)", "accent": "#257dbc",
            "accent2": "#96cd6e", "text": "#0b3c5d", "muted": "#376b90",
            "border": "#9fd0f0", "radius": "16px",
            "shadow": "0 8px 24px rgba(43,143,214,0.25)",
        }},
    "vaporwave": {
        "label": "Vaporwave / Y2K", "font": "'Segoe UI', system-ui, sans-serif",
        "mono": "'Cascadia Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#1a1a2e", "bg2": "#2d1b4e", "surface": "#241a44",
            "surface-glass": "rgba(255,113,206,0.10)", "accent": "#ff71ce",
            "accent2": "#01cdfe", "text": "#fdf5ff", "muted": "#b39ddb",
            "border": "#b967ff", "radius": "14px",
            "shadow": "0 0 24px rgba(255,113,206,0.45)",
        }},
    "cyberpunk": {
        "label": "Neon / Cyberpunk", "font": "'Segoe UI', system-ui, sans-serif",
        "mono": "'Cascadia Code', 'JetBrains Mono', monospace",
        "tokens": {
            "bg": "#0d0221", "bg2": "#01012b", "surface": "#12082e",
            "surface-glass": "rgba(5,217,232,0.06)", "accent": "#05d9e8",
            "accent2": "#ff2a6d", "text": "#d1f7ff", "muted": "#6b7fb3",
            "border": "#05d9e8", "radius": "10px",
            "shadow": "0 0 20px rgba(5,217,232,0.55)",
        }},
    "neutral": {
        "label": "Neutral", "font": "'Segoe UI', system-ui, sans-serif",
        "mono": "'Cascadia Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#0f172a", "bg2": "#1e293b", "surface": "#1e293b",
            "surface-glass": "rgba(255,255,255,0.05)", "accent": "#3b82f6",
            "accent2": "#22d3ee", "text": "#e2e8f0", "muted": "#94a3b8",
            "border": "#334155", "radius": "12px",
            "shadow": "0 8px 24px rgba(0,0,0,0.35)",
        }},
    "pastel": {
        "label": "Pastel", "font": "'Quicksand', 'Segoe UI', sans-serif",
        "mono": "'Cascadia Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#fff0f6", "bg2": "#f3e8ff", "surface": "#ffffff",
            "surface-glass": "rgba(255,255,255,0.6)", "accent": "#d664a0",
            "accent2": "#a78bfa", "text": "#5b4a63", "muted": "#73647b",
            "border": "#f3d9e8", "radius": "20px",
            "shadow": "0 10px 30px rgba(244,114,182,0.18)",
        }},
    "earthy": {
        "label": "Earthy", "font": "'Inter', 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#f5efe6", "bg2": "#ece3d4", "surface": "#fffdf9",
            "surface-glass": "rgba(255,253,249,0.6)", "accent": "#c1440e",
            "accent2": "#7d8c5c", "text": "#3b2f2a", "muted": "#706257",
            "border": "#e3d7c5", "radius": "8px",
            "shadow": "0 8px 24px rgba(59,47,42,0.15)",
        }},
    "editorial": {
        "label": "Editorial", "font": "'Inter', 'Helvetica Neue', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#ffffff", "bg2": "#fafafa", "surface": "#ffffff",
            "surface-glass": "rgba(255,255,255,0.8)", "accent": "#e11d2a",
            "accent2": "#111111", "text": "#111111", "muted": "#6b6b6b",
            "border": "#e5e5e5", "radius": "2px",
            "shadow": "0 1px 2px rgba(0,0,0,0.08)",
        }},
    "mono": {
        "label": "Mono / Brutalist", "font": "'Space Grotesk', system-ui, sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#0a0a0a", "bg2": "#161616", "surface": "#161616",
            "surface-glass": "rgba(255,255,255,0.04)", "accent": "#ffffff",
            "accent2": "#a3a3a3", "text": "#f5f5f5", "muted": "#818181",
            "border": "#2e2e2e", "radius": "0px",
            "shadow": "0 0 0 1px #2e2e2e",
        }},
    "jewel": {
        "label": "Jewel", "font": "'Space Grotesk', 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#14213d", "bg2": "#1b2a4a", "surface": "#1f2f52",
            "surface-glass": "rgba(212,175,55,0.06)", "accent": "#d4af37",
            "accent2": "#7c3aed", "text": "#f8f4e8", "muted": "#9aa6c4",
            "border": "#2e4370", "radius": "12px",
            "shadow": "0 12px 32px rgba(0,0,0,0.4)",
        }},
    "nordic": {
        "label": "Nordic", "font": "'Inter', 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#2e3440", "bg2": "#3b4252", "surface": "#3b4252",
            "surface-glass": "rgba(216,222,233,0.05)", "accent": "#88c0d0",
            "accent2": "#a3be8c", "text": "#eceff4", "muted": "#a7b0c1",
            "border": "#4c566a", "radius": "10px",
            "shadow": "0 8px 24px rgba(20,25,35,0.4)",
        }},
    "golden-archive": {
        "label": "Golden Archive", "font": "'Fraunces', 'Georgia', serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#04070f", "bg2": "#0a1224", "surface": "#0b101f",
            "surface-glass": "rgba(217,180,83,0.06)", "accent": "#d9b453",
            "accent2": "#f2dc9b", "text": "#e8e2d0", "muted": "#77809a",
            "border": "#5a4b2c", "radius": "6px",
            "shadow": "0 0 24px rgba(217,180,83,0.18)",
        }},
    # -- the complement wing: color-wheel opposites of the flagship styles --- #
    "ultraviolet": {
        "label": "Ultraviolet", "font": "'Sora', 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#0a0618", "bg2": "#150e2e", "surface": "#1a1238",
            "surface-glass": "rgba(138,112,255,0.07)", "accent": "#8a70ff",
            "accent2": "#c77dff", "text": "#ece7ff", "muted": "#8e86b8",
            "border": "#3c2f6e", "radius": "12px",
            "shadow": "0 0 28px rgba(138,112,255,0.25)",
        }},
    "ember": {
        "label": "Ember", "font": "'DM Sans', 'Segoe UI', sans-serif",
        "mono": "'Fira Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#140d0a", "bg2": "#241511", "surface": "#2a1a14",
            "surface-glass": "rgba(255,107,53,0.06)", "accent": "#ff6b35",
            "accent2": "#ffc15e", "text": "#ffefe2", "muted": "#a8887a",
            "border": "#4d2e1f", "radius": "10px",
            "shadow": "0 0 26px rgba(255,107,53,0.22)",
        }},
    "hi-contrast": {
        "label": "Hi-Contrast", "font": "'Inter', 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#000000", "bg2": "#0d0d0d", "surface": "#101010",
            "surface-glass": "rgba(255,255,255,0.06)", "accent": "#ffe600",
            "accent2": "#ffffff", "text": "#ffffff", "muted": "#c7c7c7",
            "border": "#ffffff", "radius": "4px",
            "shadow": "0 0 0 2px #ffffff",
        }},
    # -- design-profile archetype tokens (see PROFILES for full collections) -- #
    "avant-basic": {
        "label": "Avant Basic", "font": "'Fredoka', 'Segoe UI', sans-serif",
        "mono": "'Fira Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#f6e7ee", "bg2": "#efd9e6", "surface": "#fffaf5",
            "surface-glass": "rgba(216,27,122,0.06)", "accent": "#d81b7a",
            "accent2": "#5438dc", "text": "#3a2038", "muted": "#725975",
            "border": "#e6c8d8", "radius": "20px",
            "shadow": "0 10px 26px rgba(216,27,122,0.16)",
        }},
    "organic-tech": {
        "label": "Organic Tech", "font": "'DM Sans', 'Segoe UI', sans-serif",
        "mono": "'Fira Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#edeee4", "bg2": "#dfe4d2", "surface": "#f8f8f1",
            "surface-glass": "rgba(82,112,74,0.07)", "accent": "#52704a",
            "accent2": "#a5643a", "text": "#262e22", "muted": "#5d6653",
            "border": "#c9d0ba", "radius": "24px",
            "shadow": "0 12px 30px rgba(82,112,74,0.18)",
        }},
    "high-fashion": {
        "label": "High Fashion", "font": "'Lora', 'Georgia', serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#f7f4ee", "bg2": "#ece7dd", "surface": "#ffffff",
            "surface-glass": "rgba(20,20,20,0.04)", "accent": "#141414",
            "accent2": "#8e7747", "text": "#121212", "muted": "#6b665c",
            "border": "#d8d2c5", "radius": "0px",
            "shadow": "0 1px 0 rgba(20,20,20,0.9)",
        }},
    "skate-culture": {
        "label": "Skate Culture", "font": "'Inter', 'Segoe UI', sans-serif",
        "mono": "'Fira Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#141518", "bg2": "#1f2125", "surface": "#1b1d21",
            "surface-glass": "rgba(255,92,31,0.07)", "accent": "#ff5c1f",
            "accent2": "#ffd23f", "text": "#f1efe8", "muted": "#989fa8",
            "border": "#383b41", "radius": "8px",
            "shadow": "4px 4px 0 rgba(255,92,31,0.7)",
        }},
    "mosaic": {
        "label": "Mosaic", "font": "'Lora', 'Georgia', serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#f1ece0", "bg2": "#e6ddca", "surface": "#faf7ee",
            "surface-glass": "rgba(22,105,122,0.06)", "accent": "#16697a",
            "accent2": "#a8442c", "text": "#2b2721", "muted": "#656052",
            "border": "#d6cdb6", "radius": "6px",
            "shadow": "0 8px 22px rgba(43,39,33,0.16)",
        }},
    "art-deco": {
        "label": "Art Deco", "font": "'Poppins', 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#12100c", "bg2": "#1e1a12", "surface": "#171410",
            "surface-glass": "rgba(212,175,55,0.07)", "accent": "#d4af37",
            "accent2": "#2f9e77", "text": "#f0e7d0", "muted": "#99907a",
            "border": "#6e5c2e", "radius": "2px",
            "shadow": "0 0 0 1px #6e5c2e, 0 14px 34px rgba(0,0,0,0.5)",
        }},
    "frutiger-metro": {
        "label": "Frutiger Metro", "font": "'Poppins', 'Segoe UI', sans-serif",
        "mono": "'Fira Code', 'Consolas', monospace",
        "tokens": {
            "bg": "#ffffff", "bg2": "#eef5fa", "surface": "#ffffff",
            "surface-glass": "rgba(200,30,130,0.05)", "accent": "#c81e82",
            "accent2": "#8ec400", "text": "#22303b", "muted": "#5c7082",
            "border": "#cddeeb", "radius": "16px",
            "shadow": "0 10px 24px rgba(34,48,59,0.12)",
        }},
    "preppy-2000s": {
        "label": "2000s Preppy", "font": "'Lora', 'Georgia', serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#f7f2e6", "bg2": "#eae2cf", "surface": "#ffffff",
            "surface-glass": "rgba(30,58,103,0.05)", "accent": "#1e3a67",
            "accent2": "#c22f6d", "text": "#23304b", "muted": "#676355",
            "border": "#d9d1bc", "radius": "12px",
            "shadow": "0 8px 20px rgba(30,58,103,0.14)",
        }},
    "y2k-chrome": {
        "label": "Y2K Chrome", "font": "'Space Grotesk', 'Segoe UI', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#eef2f7", "bg2": "#dfe7f2", "surface": "#f8fafd",
            "surface-glass": "rgba(46,95,208,0.06)", "accent": "#2e5fd0",
            "accent2": "#8fa5bc", "text": "#1a2333", "muted": "#5a677a",
            "border": "#c3cfdd", "radius": "22px",
            "shadow": "0 14px 34px rgba(46,95,208,0.18)",
        }},
    "dark-academia": {
        "label": "Dark Academia", "font": "'Lora', 'Georgia', serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#201812", "bg2": "#2c221a", "surface": "#271e16",
            "surface-glass": "rgba(176,141,79,0.06)", "accent": "#b08d4f",
            "accent2": "#8c3838", "text": "#e9ddc8", "muted": "#998a72",
            "border": "#4a3a28", "radius": "4px",
            "shadow": "0 10px 28px rgba(0,0,0,0.5)",
        }},
    "swiss-international": {
        "label": "Swiss International", "font": "'Inter', 'Helvetica', sans-serif",
        "mono": "'JetBrains Mono', 'Consolas', monospace",
        "tokens": {
            "bg": "#ffffff", "bg2": "#f2f2f2", "surface": "#ffffff",
            "surface-glass": "rgba(0,0,0,0.03)", "accent": "#d0021b",
            "accent2": "#1a1a1a", "text": "#111111", "muted": "#595959",
            "border": "#d9d9d9", "radius": "0px",
            "shadow": "none",
        }},
}

# --------------------------------------------------------------------------- #
#  Executable design decisions  (the bridge from profile prose to real CSS)
# --------------------------------------------------------------------------- #
#  The PROFILES below say things like "two or three type sizes with unmistakable
#  jumps", "rules exactly one point", "ONE signal red". None of that survives in
#  a 13-colour token file, so every style used to render as the same page with
#  different hex codes. EXEC is the machine-readable half of the prose: the
#  decisions a generator can actually act on, and a linter can actually check.
#
#    measure    characters per line. Line-length research puts continuous text
#               at 45-75 cpl (66 ideal), multi-column at 40-50, and >80 too long.
#    ratio      modular scale step between type sizes.
#    sizes      how many sizes the style permits (Swiss: three, and no more).
#    weights    the only weights allowed; hierarchy must come from these.
#    gloss      0 matte · 1 subtle sheen · 2 glossy · 3 wet//chrome.
#    elevation  none · flat (hairline) · soft · hard (offset block) · glow.
#    accents    how many accent colours may appear. 1 means one *meaning*.
#    forbid     vocabulary this style refuses; `assets check` enforces it.
#
#  Leading is NOT stored: it is computed by _leading() from measure and
#  background polarity, because the typographic rule is a relationship, not a
#  constant — wide measure wants more leading, and reversed (light-on-dark)
#  text wants more again.

EXEC: dict[str, dict] = {
    # ---- systematic / informational ------------------------------------- #
    "swiss-international": {
        "measure": 66, "ratio": 1.5, "sizes": 3, "base": 17,
        "weights": (400, 700), "tracking": "-0.011em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 0, "elevation": "none", "border": 1,
        "dur": 120, "ease": "linear", "travel": 0, "accents": 1,
        "forbid": ["gradient", "glass", "shadow", "center", "texture"]},
    "editorial": {
        "measure": 68, "ratio": 1.414, "sizes": 4, "base": 18,
        "weights": (400, 600), "tracking": "-0.01em", "case": "none",
        "align": "left", "columns": 12, "gutter": 28,
        "gloss": 0, "elevation": "flat", "border": 1,
        "dur": 180, "ease": "cubic-bezier(.2,0,.2,1)", "travel": 8, "accents": 1,
        "forbid": ["gradient", "glass", "neon"]},
    "hi-contrast": {
        "measure": 60, "ratio": 1.5, "sizes": 3, "base": 18,
        "weights": (400, 700), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 0, "elevation": "flat", "border": 2,
        "dur": 100, "ease": "linear", "travel": 0, "accents": 1,
        "forbid": ["gradient", "glass", "shadow", "texture", "lowcontrast"]},
    "neutral": {
        "measure": 68, "ratio": 1.25, "sizes": 5, "base": 16,
        "weights": (400, 500, 600), "tracking": "-0.011em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 1, "elevation": "soft", "border": 1,
        "dur": 200, "ease": "cubic-bezier(.4,0,.2,1)", "travel": 8, "accents": 2,
        "forbid": ["neon"]},
    "mono": {
        "measure": 72, "ratio": 1.333, "sizes": 4, "base": 16,
        "weights": (400, 700), "tracking": "0em", "case": "upper",
        "align": "left", "columns": 12, "gutter": 0,
        "gloss": 0, "elevation": "hard", "border": 2,
        "dur": 0, "ease": "steps(1,end)", "travel": 0, "accents": 1,
        "forbid": ["gradient", "glass", "radius", "softshadow"]},

    # ---- glossy / optimistic -------------------------------------------- #
    "frutiger-aero": {
        "measure": 64, "ratio": 1.25, "sizes": 5, "base": 16,
        "weights": (400, 600, 700), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 3, "elevation": "soft", "border": 1,
        "dur": 320, "ease": "cubic-bezier(.25,.8,.25,1)", "travel": 12,
        "accents": 2, "forbid": ["grunge", "flat"]},
    "frutiger-metro": {
        "measure": 64, "ratio": 1.333, "sizes": 4, "base": 16,
        "weights": (300, 400, 600), "tracking": "-0.02em", "case": "none",
        "align": "left", "columns": 12, "gutter": 20,
        "gloss": 1, "elevation": "flat", "border": 0,
        "dur": 250, "ease": "cubic-bezier(.1,.9,.2,1)", "travel": 16,
        "accents": 3, "forbid": ["skeuomorph", "bevel", "texture"]},
    "y2k-chrome": {
        "measure": 60, "ratio": 1.414, "sizes": 4, "base": 16,
        "weights": (400, 700, 800), "tracking": "0.01em", "case": "none",
        "align": "center", "columns": 12, "gutter": 20,
        "gloss": 3, "elevation": "glow", "border": 2,
        "dur": 280, "ease": "cubic-bezier(.34,1.56,.64,1)", "travel": 14,
        "accents": 3, "forbid": ["matte", "muted"]},
    "pastel": {
        "measure": 62, "ratio": 1.25, "sizes": 4, "base": 16,
        "weights": (400, 600), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 2, "elevation": "soft", "border": 1,
        "dur": 300, "ease": "cubic-bezier(.25,.8,.25,1)", "travel": 10,
        "accents": 3, "forbid": ["neon", "harshshadow"]},

    # ---- dark / electric ------------------------------------------------ #
    "cyberpunk": {
        "measure": 72, "ratio": 1.333, "sizes": 4, "base": 15,
        "weights": (400, 700), "tracking": "0.04em", "case": "upper",
        "align": "left", "columns": 12, "gutter": 16,
        "gloss": 1, "elevation": "glow", "border": 1,
        "dur": 90, "ease": "steps(3,end)", "travel": 4, "accents": 3,
        "forbid": ["pastel", "softshadow", "serif"]},
    "vaporwave": {
        "measure": 60, "ratio": 1.414, "sizes": 4, "base": 16,
        "weights": (400, 700), "tracking": "0.12em", "case": "upper",
        "align": "center", "columns": 12, "gutter": 24,
        "gloss": 2, "elevation": "glow", "border": 2,
        "dur": 600, "ease": "cubic-bezier(.4,0,.6,1)", "travel": 18,
        "accents": 3, "forbid": ["muted", "corporate"]},
    "ultraviolet": {
        "measure": 68, "ratio": 1.333, "sizes": 4, "base": 16,
        "weights": (400, 600), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 2, "elevation": "glow", "border": 1,
        "dur": 400, "ease": "cubic-bezier(.2,.8,.2,1)", "travel": 12,
        "accents": 2, "forbid": ["beige", "flat"]},
    "ember": {
        "measure": 68, "ratio": 1.333, "sizes": 4, "base": 16,
        "weights": (400, 600, 700), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 2, "elevation": "glow", "border": 1,
        "dur": 350, "ease": "cubic-bezier(.3,.7,.3,1)", "travel": 10,
        "accents": 2, "forbid": ["cool", "pastel"]},
    "golden-archive": {
        "measure": 66, "ratio": 1.618, "sizes": 4, "base": 17,
        "weights": (400, 500, 700), "tracking": "0.06em", "case": "small-caps",
        "align": "center", "columns": 12, "gutter": 32,
        "gloss": 1, "elevation": "glow", "border": 1,
        "dur": 700, "ease": "cubic-bezier(.22,1,.36,1)", "travel": 8,
        "accents": 2, "forbid": ["neon", "bounce"]},
    "jewel": {
        "measure": 66, "ratio": 1.414, "sizes": 4, "base": 17,
        "weights": (400, 600), "tracking": "0.01em", "case": "none",
        "align": "left", "columns": 12, "gutter": 28,
        "gloss": 2, "elevation": "soft", "border": 1,
        "dur": 400, "ease": "cubic-bezier(.22,1,.36,1)", "travel": 10,
        "accents": 2, "forbid": ["neon", "pastel"]},
    "nordic": {
        "measure": 68, "ratio": 1.25, "sizes": 4, "base": 16,
        "weights": (400, 500, 600), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 1, "elevation": "soft", "border": 1,
        "dur": 220, "ease": "cubic-bezier(.4,0,.2,1)", "travel": 8, "accents": 2,
        "forbid": ["neon", "gloss3"]},

    # ---- earthy / crafted ----------------------------------------------- #
    "earthy": {
        "measure": 66, "ratio": 1.25, "sizes": 4, "base": 17,
        "weights": (400, 600), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 24,
        "gloss": 0, "elevation": "soft", "border": 1,
        "dur": 300, "ease": "cubic-bezier(.3,.7,.3,1)", "travel": 10,
        "accents": 2, "forbid": ["neon", "glass", "chrome"]},
    "organic-tech": {
        "measure": 64, "ratio": 1.25, "sizes": 4, "base": 17,
        "weights": (400, 500), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 28,
        "gloss": 1, "elevation": "soft", "border": 0,
        "dur": 520, "ease": "cubic-bezier(.34,1.2,.64,1)", "travel": 14,
        "accents": 2, "forbid": ["sharpcorner", "neon", "grid-rigid"]},
    "mosaic": {
        "measure": 64, "ratio": 1.333, "sizes": 4, "base": 16,
        "weights": (400, 700), "tracking": "0em", "case": "none",
        "align": "left", "columns": 12, "gutter": 12,
        "gloss": 1, "elevation": "flat", "border": 2,
        "dur": 260, "ease": "cubic-bezier(.3,.7,.3,1)", "travel": 8, "accents": 3,
        "forbid": ["gradient", "glass"]},
    "dark-academia": {
        "measure": 68, "ratio": 1.414, "sizes": 4, "base": 18,
        "weights": (400, 600), "tracking": "0.01em", "case": "small-caps",
        "align": "left", "columns": 12, "gutter": 32,
        "gloss": 0, "elevation": "soft", "border": 1,
        "dur": 420, "ease": "cubic-bezier(.25,.8,.3,1)", "travel": 8, "accents": 2,
        "forbid": ["neon", "glass", "chrome", "bounce"]},

    # ---- loud / expressive ---------------------------------------------- #
    "avant-basic": {
        "measure": 58, "ratio": 1.618, "sizes": 4, "base": 17,
        "weights": (400, 700), "tracking": "0.01em", "case": "none",
        "align": "left", "columns": 12, "gutter": 20,
        "gloss": 0, "elevation": "hard", "border": 3,
        "dur": 450, "ease": "cubic-bezier(.34,1.56,.64,1)", "travel": 20,
        "accents": 4, "forbid": ["gradient", "beige", "minimal"]},
    "skate-culture": {
        "measure": 64, "ratio": 1.5, "sizes": 4, "base": 16,
        "weights": (400, 800), "tracking": "-0.02em", "case": "upper",
        "align": "left", "columns": 12, "gutter": 16,
        "gloss": 0, "elevation": "hard", "border": 3,
        "dur": 140, "ease": "steps(2,end)", "travel": 6, "accents": 2,
        "forbid": ["glass", "pastel", "polish"]},
    "preppy-2000s": {
        "measure": 62, "ratio": 1.333, "sizes": 4, "base": 16,
        "weights": (400, 700), "tracking": "0.01em", "case": "none",
        "align": "center", "columns": 12, "gutter": 20,
        "gloss": 2, "elevation": "soft", "border": 2,
        "dur": 260, "ease": "cubic-bezier(.34,1.3,.64,1)", "travel": 10,
        "accents": 3, "forbid": ["grunge", "dark"]},
    "high-fashion": {
        "measure": 70, "ratio": 1.618, "sizes": 3, "base": 17,
        "scale_rem": ("clamp(3rem, 12vw, 9rem)", "2.75rem", "1.0625rem"),
        "weights": (300, 400), "tracking": "0.18em", "case": "upper",
        "align": "left", "columns": 12, "gutter": 40,
        "gloss": 0, "elevation": "none", "border": 1,
        "dur": 800, "ease": "cubic-bezier(.16,1,.3,1)", "travel": 24,
        "accents": 1, "forbid": ["gradient", "glass", "shadow", "bounce", "neon"]},
    "art-deco": {
        "measure": 64, "ratio": 1.618, "sizes": 4, "base": 17,
        "weights": (400, 700), "tracking": "0.08em", "case": "upper",
        "align": "center", "columns": 12, "gutter": 28,
        "gloss": 2, "elevation": "hard", "border": 2,
        "dur": 380, "ease": "cubic-bezier(.2,.9,.3,1)", "travel": 10,
        "accents": 2, "forbid": ["organic", "grunge", "pastel"]},
}


# --------------------------------------------------------------------------- #
#  Curated CSS snippets  (drop-in, self-contained)
# --------------------------------------------------------------------------- #

CSS_SNIPPETS: dict[str, dict] = {
    # --- structural primitives: the profile claims that had no code ------ #
    "grid-system": {
        "style": "neutral", "tags": ["grid", "layout", "columns", "structure"],
        "desc": "The actual grid. Several profiles call the grid their first "
                "move and then had nothing to build it with. Columns and "
                "gutter come from the style's tokens.",
        "css": """/* `.layout`, not `.grid`: the subgrid-align technique already owns
   `.grid` and would win on cascade order wherever both ship. */
.layout {
  display: grid;
  /* 12 is rewritten to the style's --columns when the kit is generated:
     repeat() takes a literal integer and silently breaks on a var() count. */
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--gutter, 24px);
  width: min(100% - 2rem, 72rem);
  margin-inline: auto;
}
/* span helpers — align to the grid or don't ship */
.layout > .col-3  { grid-column: span 3; }
.layout > .col-4  { grid-column: span 4; }
.layout > .col-6  { grid-column: span 6; }
.layout > .col-8  { grid-column: span 8; }
.layout > .col-12 { grid-column: span 12; }
@media (max-width: 720px) { .layout > * { grid-column: 1 / -1; } }
/* debug: see the armature you are aligning to */
.layout--show {
  background-image: repeating-linear-gradient(to right,
    color-mix(in srgb, var(--accent) 8%, transparent) 0 calc((100% / 12) - var(--gutter)),
    transparent 0 calc(100% / 12));
}"""},
    "type-scale": {
        "style": "neutral", "tags": ["type", "scale", "measure", "leading"],
        "desc": "Binds the computed type scale, leading and measure to real "
                "elements, so the style's size budget is what the page uses.",
        "css": """body {
  font-family: var(--font);
  font-size: var(--base, 16px);
  line-height: var(--leading, 1.5);
  font-weight: var(--weight-body, 400);
  letter-spacing: var(--tracking, 0);
  color: var(--text);
  background: var(--bg);
}
h1 { font-size: var(--size-0); }
h2 { font-size: var(--size-1); }
h3 { font-size: var(--size-2, var(--size-1)); }
h1, h2, h3 {
  font-weight: var(--weight-strong, 700);
  line-height: calc(var(--leading) - 0.35);
  letter-spacing: var(--tracking);
  text-transform: var(--case, none);
  text-wrap: balance;
}
/* The measure is a ceiling, not a floor — inside a narrow column it has to
   yield to the column, or the line runs off the page. */
p, li, blockquote { max-width: min(var(--measure, 66ch), 100%); }
.prose { max-width: min(var(--measure, 66ch), 100%); text-align: var(--align, left); }"""},
    "navbar-solid": {
        "style": "swiss-international",
        "tags": ["navbar", "header", "matte", "sticky", "flat"],
        "desc": "Matte navigation bar for styles that forbid glass. Same job "
                "as navbar-glass with no backdrop-filter and no translucency.",
        "css": """.nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.8rem 1.4rem; position: sticky; top: 0; z-index: 50;
  background: var(--surface);
  border-bottom: var(--border-width, 1px) solid var(--border);
}
.nav .brand { font-weight: var(--weight-strong, 700); letter-spacing: var(--tracking); }
.nav a {
  color: inherit; text-decoration: none; margin-left: 1.2rem;
  font-weight: var(--weight-body, 400);
}
.nav a:hover { color: var(--accent); }
.nav a[aria-current="page"] { box-shadow: inset 0 -2px 0 var(--accent); }"""},
    "hero-flush": {
        "style": "swiss-international",
        "tags": ["hero", "landing", "flush-left", "asymmetric", "grid"],
        "desc": "Asymmetric flush-left hero on the grid — the counterpart to "
                "hero-centered for styles whose rule is 'never centre'.",
        "css": """.hero {
  display: grid;
  /* 12 is rewritten to the style's --columns when the kit is generated:
     repeat() takes a literal integer and silently breaks on a var() count. */
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--gutter, 24px);
  align-content: center;
  min-height: 62vh;
  padding: 4rem 1.5rem;
  width: min(100% - 2rem, 72rem);
  margin-inline: auto;
}
.hero > * { grid-column: 1 / span 7; }
.hero h1 {
  font-size: var(--size-0);
  line-height: calc(var(--leading) - 0.4);
  letter-spacing: var(--tracking);
  text-transform: var(--case, none);
  margin-bottom: 0.6rem;
}
.hero p { max-width: min(var(--measure, 66ch), 100%); color: var(--muted); }
.hero .cta { display: flex; gap: 0.8rem; margin-top: 1.4rem; }
@media (max-width: 720px) { .hero > * { grid-column: 1 / -1; } }"""},
    "glass-card": {
        "style": "frutiger-aero", "tags": ["glassmorphism", "card", "frosted"],
        "desc": "Frosted-glass panel with blur, inner sheen, and soft border.",
        "css": """.glass-card {
  /* The pane picks up the style's own glass tint. A fixed white panel is a
     bright slab on any dark palette, which is the opposite of frosted. */
  background: var(--surface-glass, rgba(255, 255, 255, 0.45));
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  box-shadow: 0 8px 32px color-mix(in srgb, var(--text) 25%, transparent),
              inset 0 1px 0 rgba(255, 255, 255, 0.7);
  padding: 1.5rem;
}"""},
    "aqua-gel-button": {
        "style": "frutiger-aero", "tags": ["button", "glossy", "gel", "3d"],
        "desc": "Glossy Frutiger-Aero gel button with top highlight sheen.",
        "css": """.aqua-btn {
  position: relative;
  padding: 0.7rem 1.6rem;
  /* The gel is the accent lit from above: a lighter crown, the accent at
     the waist, a darker base — all derived, so any style can wear it. */
  --gel-lo: color-mix(in srgb, var(--accent) 72%, #000);
  --gel-hi: color-mix(in srgb, var(--accent) 65%, #fff);
  border: 1px solid var(--gel-lo);
  border-radius: 999px;
  color: #fff;
  font-weight: var(--weight-strong, 600);
  cursor: pointer;
  background: linear-gradient(var(--gel-hi) 0%, var(--accent) 50%, var(--gel-lo) 100%);
  box-shadow: 0 4px 10px color-mix(in srgb, var(--gel-lo) 40%, transparent),
              inset 0 1px 0 rgba(255, 255, 255, 0.6);
  overflow: hidden;
  transition: filter 0.15s, transform 0.05s;
}
.aqua-btn::before {           /* top-half glass sheen */
  content: "";
  position: absolute; inset: 0 0 50% 0;
  background: linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.1));
  border-radius: 999px 999px 40% 40%;
}
.aqua-btn:hover { filter: brightness(1.08); }
.aqua-btn:active { transform: translateY(1px); }"""},
    "neon-glow": {
        "style": "cyberpunk", "tags": ["neon", "glow", "text", "button"],
        "desc": "Neon glow for text and outlined buttons (uses currentColor).",
        "css": """.neon {
  color: var(--accent);
  text-shadow: 0 0 4px currentColor, 0 0 12px currentColor,
               0 0 28px currentColor;
}
.neon-btn {
  color: var(--accent);
  background: transparent;
  border: 2px solid currentColor;
  border-radius: 8px;
  padding: 0.6rem 1.4rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  box-shadow: 0 0 8px var(--accent),
              inset 0 0 8px color-mix(in srgb, var(--accent) 35%, transparent);
  transition: box-shadow 0.2s, color 0.2s;
}
.neon-btn:hover {
  color: #fff;
  box-shadow: 0 0 14px var(--accent), 0 0 28px var(--accent),
              inset 0 0 14px color-mix(in srgb, var(--accent) 60%, transparent);
}"""},
    "vaporwave-bg": {"literals": "the sunset ramp and cyan grid floor are the asset itself — this is the vaporwave hero, not a neutral background that happens to be pink",
        "style": "vaporwave", "tags": ["background", "gradient", "grid", "hero"],
        "desc": "Vaporwave hero: sunset gradient with a perspective grid floor.",
        "css": """.vapor-bg {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(180deg, #2d1b4e 0%, #ff2e97 60%, #ffcf40 100%);
  overflow: hidden;
}
.vapor-bg::after {            /* perspective neon grid floor */
  content: "";
  position: absolute; left: 0; right: 0; bottom: 0; height: 45%;
  background-image:
    linear-gradient(rgba(1, 205, 254, 0.6) 1px, transparent 1px),
    linear-gradient(90deg, rgba(1, 205, 254, 0.6) 1px, transparent 1px);
  background-size: 40px 40px;
  transform: perspective(300px) rotateX(60deg);
  transform-origin: bottom;
  mask-image: linear-gradient(transparent, #000 40%);
}"""},
    "crt-scanlines": {
        "style": "cyberpunk", "tags": ["crt", "retro", "overlay", "scanlines"],
        "desc": "CRT scanline + flicker overlay. Put over any container.",
        "css": """.crt {
  position: relative;
}
.crt::before {
  content: "";
  position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(
    to bottom, rgba(0,0,0,0.18) 0 1px, transparent 1px 3px);
  mix-blend-mode: multiply;
  animation: crt-flicker 3s infinite steps(60);
}
@keyframes crt-flicker { 0%,97%{opacity:1;} 98%{opacity:0.85;} 100%{opacity:1;} }"""},
    "animated-gradient-bg": {
        "style": "neutral", "tags": ["background", "gradient", "animated"],
        "desc": "Slowly-shifting multi-color gradient background.",
        "css": """.gradient-bg {
  background: linear-gradient(-45deg, var(--accent), var(--accent2),
              color-mix(in srgb, var(--accent), var(--accent2)), var(--accent));
  background-size: 400% 400%;
  animation: gradient-shift 16s ease infinite;
}
@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}"""},
    "elevation-shadows": {
        "style": "neutral", "tags": ["shadow", "elevation", "tokens", "depth"],
        "desc": "A 5-step soft shadow elevation scale (utility classes).",
        "css": """/* Soft, layered elevation — cheaper on the eyes than one hard shadow.
   Tinted from the style's own ink, so the ramp sits on the page instead of
   washing every palette with the same blue-grey. */
:root { --e-soft: color-mix(in srgb, var(--text) 7%, transparent);
        --e-deep: color-mix(in srgb, var(--text) 13%, transparent); }
.e1 { box-shadow: 0 1px 2px var(--e-soft), 0 1px 3px var(--e-deep); }
.e2 { box-shadow: 0 2px 4px var(--e-soft), 0 4px 8px var(--e-deep); }
.e3 { box-shadow: 0 4px 8px var(--e-soft), 0 8px 16px var(--e-deep); }
.e4 { box-shadow: 0 8px 16px var(--e-soft), 0 16px 32px var(--e-deep); }
.e5 { box-shadow: 0 16px 32px var(--e-soft), 0 24px 48px var(--e-deep); }"""},
    "gradient-text": {
        "style": "vaporwave", "tags": ["text", "gradient", "heading"],
        "desc": "Gradient-filled heading text (clip to text).",
        "css": """.gradient-text {
  background: linear-gradient(90deg, var(--accent), var(--accent2),
              color-mix(in srgb, var(--accent), var(--accent2)));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-weight: 800;
}"""},
    "navbar-glass": {
        "style": "neutral", "tags": ["navbar", "header", "glass", "sticky"],
        "desc": "Sticky frosted-glass top navigation bar.",
        "css": """.nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.8rem 1.4rem; position: sticky; top: 0; z-index: 50;
  /* Tinted from the style's own --surface-glass. A hardcoded white bar
     turns invisible on every dark style that asks for glass. */
  background: var(--surface-glass, rgba(255, 255, 255, 0.55));
  color: var(--text);
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
  border-bottom: var(--border-width, 1px) solid var(--border);
}
.nav .brand { font-weight: var(--weight-strong, 700); letter-spacing: var(--tracking); }
.nav a { color: var(--muted); text-decoration: none; margin-left: 1.2rem; }
.nav a:hover { color: var(--text); }
.nav a[aria-current="page"] { color: var(--text); box-shadow: inset 0 -2px 0 var(--accent); }"""},
    "hero-centered": {
        "style": "neutral", "tags": ["hero", "landing", "layout", "headline"],
        "desc": "Centered hero section with fluid headline.",
        "css": """.hero {
  min-height: 70vh; display: grid; place-items: center;
  text-align: center; padding: 4rem 1.5rem; gap: 1rem;
}
.hero h1 {
  font-size: clamp(var(--size-1, 2rem), 6vw, var(--size-0, 4rem));
  line-height: calc(var(--leading, 1.5) - 0.4);
  letter-spacing: var(--tracking, -0.02em);
  text-transform: var(--case, none);
}
.hero p {
  max-width: min(var(--measure, 52ch), 100%); margin: 0 auto;
  color: var(--muted); font-size: var(--base, 1.1rem);
}
.hero .cta { display: flex; gap: 0.8rem; justify-content: center; margin-top: 0.6rem; }"""},
    "feature-card": {
        "style": "neutral", "tags": ["card", "feature", "hover", "grid"],
        "desc": "Lifting feature card with an accent icon chip. Uses your tokens.",
        "css": """.feature {
  padding: 1.5rem;
  border-radius: var(--radius, 16px);
  background: var(--surface, #fff);
  background-image: var(--sheen, none);
  border: var(--border-width, 1px) solid var(--border, #e5e7eb);
  transition: transform var(--dur, 200ms) var(--ease, ease),
              box-shadow var(--dur, 200ms) var(--ease, ease);
}
.feature:hover {
  transform: translateY(calc(var(--travel, 8px) * -0.5));
  box-shadow: var(--shadow, none);
}
.feature .icon {
  width: 44px; height: 44px; display: grid; place-items: center;
  border-radius: calc(var(--radius, 16px) * 0.75);
  background: color-mix(in srgb, var(--accent, #2b8fd6) 15%, transparent);
  color: var(--accent, #2b8fd6); margin-bottom: 0.8rem;
}"""},
    "badge-pill": {
        "style": "neutral", "tags": ["badge", "tag", "pill", "label"],
        "desc": "Accent-tinted pill badge (auto-colors from --accent).",
        "css": """.badge {
  display: inline-flex; align-items: center; gap: 0.35em;
  padding: 0.25em 0.7em; font-size: var(--size-sm, 0.8rem);
  border-radius: max(var(--radius, 999px), 0.2em);
  font-weight: var(--weight-strong, 600);
  text-transform: var(--case, none); letter-spacing: var(--tracking, 0);
  background: color-mix(in srgb, var(--accent, #2b8fd6) 15%, transparent);
  color: var(--accent, #2b8fd6);
}"""},
    "input-field": {
        "style": "neutral", "tags": ["form", "input", "field", "focus"],
        "desc": "Text input with an accent focus ring. Uses your tokens.",
        "css": """.field {
  width: 100%; padding: 0.7rem 1rem;
  border-radius: var(--radius, 10px);
  border: var(--border-width, 1px) solid var(--border, #d1d5db);
  background: var(--surface, #fff); color: inherit; font: inherit;
  transition: border-color var(--dur, 150ms) var(--ease, ease),
              box-shadow var(--dur, 150ms) var(--ease, ease);
}
.field:focus {
  outline: none; border-color: var(--accent, #2b8fd6);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent, #2b8fd6) 25%, transparent);
}"""},
}

# --------------------------------------------------------------------------- #
#  Curated animations  (text-first, since that was the ask)
# --------------------------------------------------------------------------- #

ANIMATIONS: dict[str, dict] = {
    "typewriter": {
        "kind": "css", "style": "neutral", "tags": ["text", "type", "caret"],
        "desc": "Typewriter reveal with a blinking caret (single line).",
        "code": """.typewriter {
  --steps: 24;                 /* set to your text length in characters */
  display: inline-block;
  overflow: hidden;
  white-space: nowrap;
  border-right: 2px solid currentColor;
  width: 0;
  animation: type 2.4s steps(var(--steps)) forwards, caret 0.8s step-end infinite;
}
@keyframes type { to { width: 24ch; } }   /* match --steps (in ch) */
@keyframes caret { 50% { border-color: transparent; } }"""},
    "glitch-text": {
        "kind": "css", "style": "cyberpunk", "tags": ["text", "glitch", "rgb"],
        "desc": "RGB-split glitch on text. Set data-text to the same string.",
        "code": """.glitch {
  position: relative;
  color: var(--text);
  font-weight: 800;
}
.glitch::before, .glitch::after {
  content: attr(data-text);
  position: absolute; left: 0; top: 0; width: 100%;
  clip-path: inset(0 0 0 0);
}
.glitch::before { color: var(--accent); animation: glitch-x 2s infinite linear alternate; }
.glitch::after  { color: var(--accent2); animation: glitch-x 1.4s infinite linear alternate-reverse; }
@keyframes glitch-x {
  0% { transform: translate(0); } 20% { transform: translate(-2px, 1px); }
  40% { transform: translate(2px, -1px); } 60% { transform: translate(-1px, 0); }
  80% { transform: translate(1px, 1px); } 100% { transform: translate(0); }
}"""},
    "neon-flicker": {
        "kind": "css", "style": "cyberpunk", "tags": ["text", "neon", "flicker"],
        "desc": "Neon sign flicker — irregular blinks then steady glow.",
        "code": """.flicker {
  color: var(--accent);
  text-shadow: 0 0 6px currentColor, 0 0 16px currentColor;
  animation: flicker 3.5s infinite;
}
@keyframes flicker {
  0%,18%,22%,25%,53%,57%,100% { opacity: 1; }
  20%,24%,55% { opacity: 0.35; text-shadow: none; }
}"""},
    "gradient-text-shift": {
        "kind": "css", "style": "vaporwave", "tags": ["text", "gradient", "animated"],
        "desc": "Animated gradient sweeping through heading text.",
        "code": """.grad-shift {
  background: linear-gradient(90deg, var(--accent), var(--accent2),
              color-mix(in srgb, var(--accent), var(--accent2)), var(--accent));
  background-size: 300% 100%;
  -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: grad-move 6s linear infinite;
}
@keyframes grad-move { to { background-position: 300% 0; } }"""},
    "wave-text": {
        "kind": "css", "style": "neutral", "tags": ["text", "wave", "bounce"],
        "desc": "Per-letter bobbing wave. Wrap each letter in <span> and set delays.",
        "code": """.wave span {
  display: inline-block;
  animation: wave 1.6s ease-in-out infinite;
}
/* stagger: .wave span:nth-child(n) { animation-delay: calc(n * 0.08s); } */
@keyframes wave { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-0.35em); } }"""},
    "float": {
        "kind": "css", "style": "frutiger-aero", "tags": ["float", "bob", "hover"],
        "desc": "Gentle floating bob — great for glossy icons/bubbles.",
        "code": """.float { animation: float 4s ease-in-out infinite; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }"""},
    "pulse-glow": {
        "kind": "css", "style": "cyberpunk", "tags": ["pulse", "glow", "attention"],
        "desc": "Breathing glow to draw attention to a button/badge.",
        "code": """.pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }
@keyframes pulse-glow {
  0%,100% { box-shadow: 0 0 6px currentColor; }
  50% { box-shadow: 0 0 20px currentColor, 0 0 36px currentColor; }
}"""},
    "fade-in-up": {
        "kind": "css", "style": "neutral", "tags": ["entrance", "reveal", "scroll"],
        "desc": "Standard entrance: fade + rise. Add to elements on load.",
        "code": """.fade-in-up { animation: fade-in-up 0.6s cubic-bezier(0.22,1,0.36,1) both; }
@keyframes fade-in-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: none; } }"""},
    "shimmer": {
        "kind": "css", "style": "neutral", "tags": ["loading", "skeleton", "shine"],
        "desc": "Skeleton-loading shimmer sweep.",
        "code": """.shimmer {
  /* the sweep is the surface lightened, so a skeleton matches its own page */
  --sk: color-mix(in srgb, var(--surface) 92%, var(--text));
  background: linear-gradient(90deg, var(--sk) 25%, var(--surface) 37%, var(--sk) 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}
@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }"""},
    "bubbles-js": {
        "kind": "js", "style": "frutiger-aero", "tags": ["canvas", "bubbles", "background"],
        "desc": "Rising translucent bubbles on a <canvas id='bubbles'> — Frutiger Aero.",
        "code": """// <canvas id="bubbles" style="position:fixed;inset:0;z-index:-1"></canvas>
const c = document.getElementById('bubbles'), x = c.getContext('2d');
let W, H, bubbles = [];
function resize(){ W = c.width = innerWidth; H = c.height = innerHeight; }
resize(); addEventListener('resize', resize);
for (let i = 0; i < 40; i++) bubbles.push({
  x: Math.random()*W, y: Math.random()*H, r: 6+Math.random()*26,
  s: 0.3+Math.random()*0.9
});
(function loop(){
  x.clearRect(0,0,W,H);
  for (const b of bubbles){
    b.y -= b.s; if (b.y + b.r < 0){ b.y = H + b.r; b.x = Math.random()*W; }
    const g = x.createRadialGradient(b.x-b.r*0.3, b.y-b.r*0.3, 1, b.x, b.y, b.r);
    // the bubble's rim picks up the page accent; the core stays specular white
    const tint = getComputedStyle(document.documentElement)
                   .getPropertyValue('--accent').trim() || '#60b2f0';
    g.addColorStop(0,'rgba(255,255,255,0.9)'); g.addColorStop(1, tint + '26');
    x.beginPath(); x.arc(b.x,b.y,b.r,0,7); x.fillStyle=g; x.fill();
  }
  requestAnimationFrame(loop);
})();"""},
    "matrix-rain-js": {
        "kind": "js", "style": "cyberpunk", "tags": ["canvas", "matrix", "background"],
        "desc": "Falling green code rain on a <canvas id='matrix'>.",
        "code": """// <canvas id="matrix" style="position:fixed;inset:0;z-index:-1;background:#000"></canvas>
const c = document.getElementById('matrix'), x = c.getContext('2d');
let W = c.width = innerWidth, H = c.height = innerHeight;
addEventListener('resize', () => { W = c.width = innerWidth; H = c.height = innerHeight; });
const cols = Math.floor(W / 14), drops = Array(cols).fill(0);
const chars = 'ｱｲｳｴｵｶ01<>=/*-+アカサタナ'.split('');
setInterval(() => {
  x.fillStyle = 'rgba(0,0,0,0.06)'; x.fillRect(0,0,W,H);
  // the glyph colour comes from the page, with matrix green as the fallback
  const accent = getComputedStyle(document.documentElement)
                   .getPropertyValue('--accent').trim() || '#00ff41';
  x.fillStyle = accent; x.font = '14px monospace';
  drops.forEach((y, i) => {
    x.fillText(chars[Math.random()*chars.length|0], i*14, y*14);
    drops[i] = (y*14 > H && Math.random() > 0.975) ? 0 : y + 1;
  });
}, 55);"""},
    "starfield-js": {
        "kind": "js", "style": "vaporwave", "tags": ["canvas", "stars", "background"],
        "desc": "Warp starfield flying toward the viewer on <canvas id='stars'>.",
        "code": """// <canvas id="stars" style="position:fixed;inset:0;z-index:-1;background:var(--bg)"></canvas>
const c = document.getElementById('stars'), x = c.getContext('2d');
let W, H, stars = [];
function resize(){ W = c.width = innerWidth; H = c.height = innerHeight; }
resize(); addEventListener('resize', resize);
for (let i = 0; i < 300; i++) stars.push({ x:(Math.random()-0.5)*W, y:(Math.random()-0.5)*H, z:Math.random()*W });
(function loop(){
  // trail colour from the page background, so stars sit on the real field
  const root = getComputedStyle(document.documentElement);
  const bg = root.getPropertyValue('--bg').trim() || '#0f1b3d';
  const star = root.getPropertyValue('--accent').trim();
  x.fillStyle = bg + '66'; x.fillRect(0,0,W,H);
  for (const s of stars){
    s.z -= 6; if (s.z <= 0){ s.z = W; s.x = (Math.random()-0.5)*W; s.y = (Math.random()-0.5)*H; }
    const k = 128/s.z, sx = s.x*k + W/2, sy = s.y*k + H/2, r = (1-s.z/W)*2.5;
    x.fillStyle = star || '#01cdfe'; x.fillRect(sx, sy, r, r);
  }
  requestAnimationFrame(loop);
})();"""},
}

# --------------------------------------------------------------------------- #
#  Curated gradients  (paste the value straight into `background:`)
# --------------------------------------------------------------------------- #

GRADIENTS: dict[str, dict] = {
    "aurora": {"style": "pastel", "tags": ["soft", "cool", "hero"],
               "css": "linear-gradient(135deg, #8ec5fc 0%, #e0c3fc 100%)"},
    "cotton-candy": {"style": "pastel", "tags": ["pink", "warm", "soft"],
                     "css": "linear-gradient(135deg, #ffafbd 0%, #ffc3a0 100%)"},
    "peachy": {"style": "pastel", "tags": ["peach", "warm", "gentle"],
               "css": "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)"},
    "mint-fresh": {"style": "pastel", "tags": ["green", "fresh", "spring"],
                   "css": "linear-gradient(135deg, #a8ff78 0%, #78ffd6 100%)"},
    "sunset-warm": {"style": "vaporwave", "tags": ["hot", "vivid", "hero"],
                    "css": "linear-gradient(135deg, #ff6a00 0%, #ee0979 100%)"},
    "purple-haze": {"style": "vaporwave", "tags": ["magenta", "vivid"],
                    "css": "linear-gradient(135deg, #7f00ff 0%, #e100ff 100%)"},
    "gold-hour": {"style": "earthy", "tags": ["gold", "warm", "amber"],
                  "css": "linear-gradient(135deg, #f7971e 0%, #ffd200 100%)"},
    "forest-mist": {"style": "jewel", "tags": ["green", "deep", "calm"],
                    "css": "linear-gradient(135deg, #134e5e 0%, #71b280 100%)"},
    "ocean-deep": {"style": "nordic", "tags": ["blue", "deep", "cool"],
                   "css": "linear-gradient(135deg, #2b5876 0%, #4e4376 100%)"},
    "royal-jewel": {"style": "jewel", "tags": ["navy", "luxe", "deep"],
                    "css": "linear-gradient(135deg, #141e30 0%, #243b55 100%)"},
    "mono-fade": {"style": "mono", "tags": ["grey", "subtle", "neutral"],
                  "css": "linear-gradient(135deg, #232526 0%, #414345 100%)"},
    "cyber-glow": {"style": "cyberpunk", "tags": ["neon", "dark", "vivid"],
                   "css": "linear-gradient(135deg, #0d0221 0%, #ff2a6d 50%, #05d9e8 100%)"},
    # Trendy multi-point "mesh" backgrounds — expensive to hand-derive.
    "mesh-vibrant": {"style": "vaporwave", "tags": ["mesh", "blurry", "hero", "dark"],
                     "css": "radial-gradient(at 20% 20%, #ff71ce 0px, transparent 50%), "
                            "radial-gradient(at 80% 0%, #01cdfe 0px, transparent 50%), "
                            "radial-gradient(at 0% 80%, #05ffa1 0px, transparent 50%), "
                            "radial-gradient(at 80% 100%, #b967ff 0px, transparent 50%), #1a1a2e"},
    "ultraviolet-nebula": {"style": "ultraviolet",
                           "tags": ["violet", "dark", "electric", "hero"],
                           "css": "radial-gradient(at 75% 15%, rgba(199,125,255,0.25) 0px, transparent 50%), "
                                  "radial-gradient(at 15% 80%, rgba(138,112,255,0.30) 0px, transparent 55%), "
                                  "linear-gradient(160deg, #0a0618 0%, #150e2e 100%)"},
    "ember-heat": {"style": "ember",
                   "tags": ["orange", "warm", "dark", "glow", "hero"],
                   "css": "radial-gradient(at 50% 110%, rgba(255,107,53,0.35) 0px, transparent 60%), "
                          "radial-gradient(at 85% 20%, rgba(255,193,94,0.12) 0px, transparent 45%), "
                          "linear-gradient(180deg, #140d0a 0%, #241511 100%)"},
    "archive-space": {"style": "golden-archive",
                      "tags": ["gold", "dark", "space", "museum", "hero"],
                      "css": "radial-gradient(at 72% 8%, rgba(217,180,83,0.13) 0px, transparent 45%), "
                             "radial-gradient(at 18% 85%, rgba(32,42,92,0.55) 0px, transparent 55%), "
                             "linear-gradient(180deg, #04070f 0%, #0a1224 100%)"},
    "mesh-pastel": {"style": "pastel", "tags": ["mesh", "blurry", "hero", "light"],
                    "css": "radial-gradient(at 27% 37%, #ffd1dc 0px, transparent 45%), "
                           "radial-gradient(at 97% 21%, #c7ceea 0px, transparent 40%), "
                           "radial-gradient(at 52% 99%, #b5ead7 0px, transparent 40%), "
                           "radial-gradient(at 10% 90%, #ffe5b4 0px, transparent 40%), #fff5e1"},
}

# --------------------------------------------------------------------------- #
#  Curated background patterns / SVG art  (geometric = CSS, organic = SVG)
# --------------------------------------------------------------------------- #

PATTERNS: dict[str, dict] = {
    "dots": {"kind": "css", "tags": ["dots", "subtle", "background"],
             "desc": "Polka-dot grid. Change color/size via the two values.",
             "code": """.bg-dots {
  background-color: #ffffff;
  background-image: radial-gradient(rgba(0,0,0,0.15) 1px, transparent 1px);
  background-size: 16px 16px;
}"""},
    "grid": {"kind": "css", "tags": ["grid", "lines", "background"],
             "desc": "Thin line grid.",
             "code": """.bg-grid {
  background-color: #ffffff;
  background-image:
    linear-gradient(rgba(0,0,0,0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.08) 1px, transparent 1px);
  background-size: 24px 24px;
}"""},
    "graph-paper": {"kind": "css", "tags": ["grid", "graph", "engineering"],
                    "desc": "Layered minor+major grid (graph paper).",
                    "code": """.bg-graph {
  background-color: #ffffff;
  background-image:
    linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px),
    linear-gradient(rgba(0,0,0,0.10) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.10) 1px, transparent 1px);
  background-size: 20px 20px, 20px 20px, 100px 100px, 100px 100px;
}"""},
    "diagonal-stripes": {"kind": "css", "tags": ["stripes", "diagonal", "background"],
                         "desc": "45° candy stripes.",
                         "code": """.bg-stripes {
  background: repeating-linear-gradient(45deg,
    #f5f5f5 0, #f5f5f5 10px, #ffffff 10px, #ffffff 20px);
}"""},
    "checkerboard": {"kind": "css", "tags": ["checker", "retro", "background"],
                     "desc": "Soft checkerboard via conic-gradient.",
                     "code": """.bg-checker {
  background-color: #ffffff;
  background-image:
    conic-gradient(rgba(0,0,0,0.05) 90deg, transparent 90deg 180deg,
                   rgba(0,0,0,0.05) 180deg 270deg, transparent 270deg);
  background-size: 24px 24px;
}"""},
    "noise-texture": {"kind": "css", "tags": ["noise", "grain", "texture", "overlay"],
                      "desc": "Film-grain overlay (SVG feTurbulence data-URI). Put on a "
                              "positioned parent; tweak opacity to taste.",
                      "code": """.noise { position: relative; }
.noise::after {
  content: ""; position: absolute; inset: 0; pointer-events: none; opacity: 0.06;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}"""},
    "wave-divider": {"kind": "svg", "tags": ["divider", "wave", "section", "separator"],
                     "desc": "Wave section divider. Set a color via `fill`/currentColor; "
                             "place at the bottom of a section.",
                     "code": """<svg viewBox="0 0 1440 120" preserveAspectRatio="none"
     style="display:block; width:100%; height:80px; color:#2b8fd6">
  <path fill="currentColor"
    d="M0,64 C240,120 480,0 720,32 C960,64 1200,120 1440,72 L1440,120 L0,120 Z"/>
</svg>"""},
    "blob": {"kind": "svg", "tags": ["blob", "organic", "shape", "decor"],
             "desc": "Organic blob shape — decorative accent behind content.",
             "code": """<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"
     style="width:280px; color:#a78bfa">
  <path fill="currentColor" transform="translate(100 100)"
    d="M45,-63C58,-54,68,-40,72,-25C76,-9,74,9,67,25C60,41,48,55,33,63
       C18,71,0,73,-18,69C-36,65,-54,55,-65,40C-76,25,-80,5,-77,-14
       C-74,-33,-64,-51,-49,-61C-34,-71,-17,-73,0,-72C17,-71,34,-72,45,-63Z"/>
</svg>"""},
    "topographic": {"kind": "svg", "tags": ["topographic", "contour", "lines", "background"],
                    "desc": "Concentric contour lines — subtle map-like texture.",
                    "code": """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"
     style="opacity:0.15; color:#3b2f2a">
  <g fill="none" stroke="currentColor" stroke-width="1.2">
    <circle cx="100" cy="100" r="20"/><circle cx="100" cy="100" r="42"/>
    <circle cx="100" cy="100" r="66"/><circle cx="100" cy="100" r="92"/>
  </g>
</svg>  <!-- tile as a repeating background, or place as a decorative layer -->"""},
}

# --------------------------------------------------------------------------- #
#  SVG art  (icons sprite, section dividers, hero illustrations) — inline SVG,
#  reusable and recolorable via currentColor / CSS `color`. Big token savers.
# --------------------------------------------------------------------------- #

SVG_ART: dict[str, dict] = {
    "icon-set": {"tags": ["icons", "line", "sprite", "ui"],
                 "desc": "16 stroke icons as a hidden <symbol> sprite. Drop once, "
                         "then reuse: <svg class='ic'><use href='#i-home'/></svg>. "
                         "Style .ic { width:24px; height:24px; stroke:currentColor; "
                         "fill:none; stroke-width:2; stroke-linecap:round; "
                         "stroke-linejoin:round; }",
                 "code": """<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="i-home" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></symbol>
  <symbol id="i-search" viewBox="0 0 24 24"><circle cx="10" cy="10" r="6"/><path d="M15 15l5 5"/></symbol>
  <symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/></symbol>
  <symbol id="i-settings" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/></symbol>
  <symbol id="i-heart" viewBox="0 0 24 24"><path d="M12 21C7 17 3 13 3 8.5 3 6 5 4 7.5 4 9 4 12 6 12 6s3-2 4.5-2C19 4 21 6 21 8.5 21 13 17 17 12 21z"/></symbol>
  <symbol id="i-star" viewBox="0 0 24 24"><path d="M12 3l2.7 5.5 6 .9-4.3 4.2 1 6-5.4-2.8-5.4 2.8 1-6L3.3 9.4l6-.9z"/></symbol>
  <symbol id="i-bell" viewBox="0 0 24 24"><path d="M6 16v-5a6 6 0 1 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/></symbol>
  <symbol id="i-mail" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></symbol>
  <symbol id="i-check" viewBox="0 0 24 24"><path d="M4 12l5 5 11-11"/></symbol>
  <symbol id="i-x" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
  <symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></symbol>
  <symbol id="i-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
  <symbol id="i-trash" viewBox="0 0 24 24"><path d="M4 7h16M6 7l1 13h10l1-13M9 7V4h6v3"/></symbol>
  <symbol id="i-download" viewBox="0 0 24 24"><path d="M12 3v12M7 11l5 5 5-5M4 21h16"/></symbol>
  <symbol id="i-arrow-right" viewBox="0 0 24 24"><path d="M4 12h15M13 6l6 6-6 6"/></symbol>
  <symbol id="i-chevron-down" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></symbol>
</svg>"""},
    "divider-tilt": {"tags": ["divider", "tilt", "slope", "section"],
                     "desc": "Straight tilted section divider.",
                     "code": """<svg viewBox="0 0 1440 100" preserveAspectRatio="none"
     style="display:block; width:100%; height:70px; color:#ffffff">
  <path fill="currentColor" d="M0,100 L1440,0 L1440,100 Z"/>
</svg>"""},
    "divider-curve": {"tags": ["divider", "curve", "concave", "section"],
                      "desc": "Smooth concave curve divider.",
                      "code": """<svg viewBox="0 0 1440 100" preserveAspectRatio="none"
     style="display:block; width:100%; height:70px; color:#ffffff">
  <path fill="currentColor" d="M0,100 C480,0 960,0 1440,100 L1440,100 L0,100 Z"/>
</svg>"""},
    "divider-zigzag": {"tags": ["divider", "zigzag", "jagged", "section"],
                       "desc": "Zigzag divider edge.",
                       "code": """<svg viewBox="0 0 1440 60" preserveAspectRatio="none"
     style="display:block; width:100%; height:40px; color:#ffffff">
  <path fill="currentColor" d="M0,60 L120,10 L240,60 L360,10 L480,60 L600,10 L720,60
    L840,10 L960,60 L1080,10 L1200,60 L1320,10 L1440,60 Z"/>
</svg>"""},
    "hero-blobs": {"tags": ["hero", "blobs", "decor", "background", "organic"],
                   "desc": "Two soft overlapping blobs — decorative hero backdrop. "
                           "Recolor via the two fills; set position:absolute behind content.",
                   "code": """<svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg"
     style="width:100%; height:auto">
  <g opacity="0.85">
    <path fill="#a78bfa" transform="translate(180 180)"
      d="M120,-150C150,-120,160,-70,150,-25C140,20,110,60,70,95C30,130,-20,160,-70,150
         C-120,140,-170,90,-180,35C-190,-20,-160,-80,-120,-120C-80,-160,-30,-180,20,-175
         C70,-170,90,-180,120,-150Z"/>
    <path fill="#f472b6" opacity="0.75" transform="translate(400 230)"
      d="M100,-120C130,-95,150,-55,145,-15C140,25,110,60,75,90C40,120,0,145,-45,140
         C-90,135,-135,100,-150,55C-165,10,-150,-45,-115,-85C-80,-125,-25,-150,20,-150
         C65,-150,70,-145,100,-120Z"/>
  </g>
</svg>"""},
    "hero-landscape": {"tags": ["hero", "landscape", "mountains", "geometric", "scene"],
                       "desc": "Layered geometric hills/mountains scene — clean generic "
                               "hero art. Swap the layer fills to match any palette.",
                       "code": """<svg viewBox="0 0 1440 500" xmlns="http://www.w3.org/2000/svg"
     style="width:100%; height:auto">
  <rect width="1440" height="500" fill="#ceecff"/>
  <circle cx="1150" cy="130" r="70" fill="#fff3b0"/>
  <path fill="#8fd0e8" d="M0,340 L240,220 L480,330 L760,180 L1040,320 L1440,200 L1440,500 L0,500 Z"/>
  <path fill="#5bb3cc" d="M0,400 L300,300 L620,400 L900,290 L1200,400 L1440,320 L1440,500 L0,500 Z"/>
  <path fill="#96cd6e" d="M0,440 L360,380 L720,450 L1080,390 L1440,450 L1440,500 L0,500 Z"/>
  <path fill="#4e9638" d="M0,480 L400,450 L800,485 L1200,455 L1440,485 L1440,500 L0,500 Z"/>
</svg>"""},
    "hero-grid": {"tags": ["hero", "grid", "synthwave", "sun", "retro", "scene"],
                  "desc": "Synthwave sun + perspective grid horizon — retro/cyberpunk hero.",
                  "code": """<svg viewBox="0 0 1440 500" xmlns="http://www.w3.org/2000/svg"
     style="width:100%; height:auto">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#2d1b4e"/><stop offset="1" stop-color="#ff2e97"/>
    </linearGradient>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffcf40"/><stop offset="1" stop-color="#ff2e97"/>
    </linearGradient>
    <clipPath id="sunclip"><circle cx="720" cy="250" r="130"/></clipPath>
  </defs>
  <rect width="1440" height="500" fill="url(#sky)"/>
  <g clip-path="url(#sunclip)">
    <rect x="590" y="120" width="260" height="260" fill="url(#sun)"/>
    <g stroke="#2d1b4e" stroke-width="8">
      <line x1="590" y1="300" x2="850" y2="300"/><line x1="590" y1="330" x2="850" y2="330"/>
      <line x1="590" y1="360" x2="850" y2="360"/>
    </g>
  </g>
  <g stroke="#01cdfe" stroke-width="1.5" opacity="0.8">
    <line x1="720" y1="330" x2="-400" y2="500"/><line x1="720" y1="330" x2="200" y2="500"/>
    <line x1="720" y1="330" x2="600" y2="500"/><line x1="720" y1="330" x2="840" y2="500"/>
    <line x1="720" y1="330" x2="1240" y2="500"/><line x1="720" y1="330" x2="1840" y2="500"/>
    <line x1="0" y1="360" x2="1440" y2="360"/><line x1="0" y1="400" x2="1440" y2="400"/>
    <line x1="0" y1="450" x2="1440" y2="450"/>
  </g>
</svg>"""},
}

# --------------------------------------------------------------------------- #
#  Web layout templates  (page structure / orientation — the arrangement, not
#  the paint). Token-driven skeletons; combine with a style's tokens + kit.
# --------------------------------------------------------------------------- #

LAYOUTS: dict[str, dict] = {
    "single-column": {
        "best_for": "blogs, docs, articles, long-form reading",
        "desc": "One centered, measure-limited column. The most readable layout.",
        "html": """<style>
  .l-single { max-width: 68ch; margin: 0 auto; padding: 3rem 1.25rem; line-height: 1.7; }
  .l-single h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); margin-bottom: 1rem; }
  .l-single p { margin: 0 0 1.1rem; }
</style>
<article class="l-single">
  <h1>Headline</h1>
  <p>Body copy sits in a single readable column ~60–75 characters wide…</p>
</article>"""},
    "hero-cta": {
        "best_for": "SaaS / product landing pages",
        "desc": "Full-viewport hero: big headline, subcopy, primary + ghost CTA.",
        "html": """<style>
  .l-hero { min-height: 88vh; display: grid; place-items: center; text-align: center;
            padding: 4rem 1.5rem; gap: 1.2rem;
            background: linear-gradient(160deg, var(--bg,#0f172a), var(--bg2,#1e293b)); }
  .l-hero h1 { font-size: clamp(2.2rem, 7vw, 4.5rem); line-height: 1.03; max-width: 16ch; }
  .l-hero p { max-width: 52ch; opacity: .8; font-size: 1.15rem; }
  .l-hero .row { display: flex; gap: .8rem; flex-wrap: wrap; justify-content: center; }
</style>
<section class="l-hero">
  <h1>Your bold value proposition</h1>
  <p>One clear sentence on the outcome you deliver.</p>
  <div class="row"><button class="btn">Start free</button>
    <button class="btn" style="background:transparent;color:inherit">See how</button></div>
</section>"""},
    "z-pattern": {
        "best_for": "landing pages with a few key points",
        "desc": "Alternating left/right rows guide the eye in a Z — image ⇄ text.",
        "html": """<style>
  .l-z { display: grid; gap: 3rem; max-width: 1100px; margin: 0 auto; padding: 3rem 1.25rem; }
  .l-z .row { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: center; }
  .l-z .row:nth-child(even) .media { order: 2; }
  .l-z .media { aspect-ratio: 4/3; border-radius: var(--radius,12px);
                background: var(--surface,#1e293b); }
  @media (max-width:720px){ .l-z .row{ grid-template-columns:1fr } .l-z .media{ order:0 } }
</style>
<div class="l-z">
  <div class="row"><div class="media"></div><div><h2>Point one</h2><p>Explain it.</p></div></div>
  <div class="row"><div class="media"></div><div><h2>Point two</h2><p>Explain it.</p></div></div>
</div>"""},
    "f-pattern": {
        "best_for": "content-heavy / news / scannable pages",
        "desc": "Left-aligned headings + text blocks matching natural F-scan reading.",
        "html": """<style>
  .l-f { max-width: 900px; margin: 0 auto; padding: 2.5rem 1.25rem; }
  .l-f section { margin-bottom: 2rem; }
  .l-f h2 { margin-bottom: .4rem; }
  .l-f p { max-width: 70ch; opacity: .85; }
  .l-f .lead { font-size: 1.15rem; border-left: 3px solid var(--accent,#3b82f6);
               padding-left: 1rem; }
</style>
<main class="l-f">
  <section><h1>Top headline (widest scan)</h1><p class="lead">Lead paragraph…</p></section>
  <section><h2>Subhead</h2><p>Supporting text, left-aligned…</p></section>
  <section><h2>Subhead</h2><p>Supporting text…</p></section>
</main>"""},
    "split-screen": {
        "best_for": "portfolios, two equal choices, product vs pricing",
        "desc": "50/50 vertical split — two panels of equal weight side by side.",
        "html": """<style>
  .l-split { display: grid; grid-template-columns: 1fr 1fr; min-height: 90vh; }
  .l-split > div { display: grid; place-items: center; padding: 3rem; text-align: center; }
  .l-split .a { background: var(--accent,#3b82f6); color:#fff; }
  .l-split .b { background: var(--surface,#1e293b); }
  @media (max-width:720px){ .l-split{ grid-template-columns:1fr } }
</style>
<div class="l-split">
  <div class="a"><div><h2>Left</h2><p>One path.</p></div></div>
  <div class="b"><div><h2>Right</h2><p>The other.</p></div></div>
</div>"""},
    "sidebar-app": {
        "best_for": "web apps, docs with nav, settings",
        "desc": "Fixed left sidebar + fluid content — the classic app shell.",
        "html": """<style>
  .l-app { display: grid; grid-template-columns: 240px 1fr; min-height: 100vh; }
  .l-app aside { background: var(--surface,#1e293b); border-right:1px solid var(--border,#334155);
                 padding: 1.25rem; }
  .l-app aside a { display:block; padding:.5rem .6rem; border-radius:8px; color:inherit;
                   text-decoration:none; opacity:.8; }
  .l-app aside a:hover { background: var(--bg2,#0f172a); opacity:1; }
  .l-app main { padding: 2rem; }
  @media (max-width:720px){ .l-app{ grid-template-columns:1fr } .l-app aside{ display:none } }
</style>
<div class="l-app">
  <aside><strong>Menu</strong><nav><a>Dashboard</a><a>Projects</a><a>Settings</a></nav></aside>
  <main><h1>Content</h1></main>
</div>"""},
    "card-grid": {
        "best_for": "galleries, catalogs, dashboards, blog indexes",
        "desc": "Responsive auto-fit card grid — columns adapt to width.",
        "html": """<style>
  .l-cards { display: grid; gap: 1rem; padding: 2rem 1.25rem; max-width: 1200px; margin: 0 auto;
             grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
  .l-cards .card { background: var(--surface,#1e293b); border:1px solid var(--border,#334155);
                   border-radius: 12px; padding: 1.25rem; }
</style>
<div class="l-cards">
  <div class="card">One</div><div class="card">Two</div>
  <div class="card">Three</div><div class="card">Four</div>
</div>"""},
    "bento-grid": {
        "best_for": "modern landing feature sections, overviews",
        "desc": "Trendy 'bento box' grid — mixed-size tiles in one frame.",
        "html": """<style>
  .l-bento { display: grid; gap: 1rem; max-width: 1100px; margin: 0 auto; padding: 2rem 1.25rem;
             grid-template-columns: repeat(4, 1fr); grid-auto-rows: 150px; }
  .l-bento div { background: var(--surface,#1e293b); border:1px solid var(--border,#334155);
                 border-radius: 16px; padding: 1rem; }
  .l-bento .big { grid-column: span 2; grid-row: span 2; }
  .l-bento .wide { grid-column: span 2; }
  @media (max-width:720px){ .l-bento{ grid-template-columns:repeat(2,1fr) } }
</style>
<div class="l-bento">
  <div class="big">Feature</div><div>·</div><div>·</div>
  <div class="wide">Wide</div><div>·</div><div>·</div><div>·</div>
</div>"""},
    "magazine": {
        "best_for": "editorial homepages, publications",
        "desc": "Asymmetric multi-column with a lead story — magazine feel.",
        "html": """<style>
  .l-mag { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; max-width: 1100px;
           margin: 0 auto; padding: 2.5rem 1.25rem; }
  .l-mag .lead { grid-row: span 2; }
  .l-mag article { border-bottom: 1px solid var(--border,#e5e5e5); padding-bottom: 1rem; }
  .l-mag .lead h1 { font-size: clamp(1.8rem,4vw,3rem); }
  @media (max-width:720px){ .l-mag{ grid-template-columns:1fr } }
</style>
<div class="l-mag">
  <article class="lead"><h1>Lead story</h1><p>Feature copy…</p></article>
  <article><h3>Secondary</h3></article>
  <article><h3>Tertiary</h3></article>
</div>"""},
    "full-screen-sections": {
        "best_for": "storytelling scroll sites, product tours",
        "desc": "Scroll-snap sections that each fill the viewport.",
        "html": """<style>
  .l-fs { height: 100vh; overflow-y: scroll; scroll-snap-type: y mandatory; }
  .l-fs section { height: 100vh; scroll-snap-align: start; display: grid; place-items: center;
                  font-size: 2rem; }
  .l-fs section:nth-child(odd){ background: var(--bg,#0f172a); }
  .l-fs section:nth-child(even){ background: var(--surface,#1e293b); }
</style>
<div class="l-fs"><section>One</section><section>Two</section><section>Three</section></div>"""},
    "dashboard": {
        "best_for": "admin panels, analytics, back-office",
        "desc": "Topbar + sidebar + content metric grid — full admin shell.",
        "html": """<style>
  .l-dash { display: grid; grid-template-columns: 220px 1fr; grid-template-rows: 56px 1fr;
            min-height: 100vh; }
  .l-dash .top { grid-column: 1 / -1; display:flex; align-items:center; padding:0 1.25rem;
                 background: var(--surface,#1e293b); border-bottom:1px solid var(--border,#334155); }
  .l-dash .side { background: var(--bg2,#0f172a); padding:1rem; }
  .l-dash .main { padding:1.5rem; display:grid; gap:1rem;
                  grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); align-content:start; }
  .l-dash .stat { background: var(--surface,#1e293b); border-radius:12px; padding:1.1rem; }
  @media (max-width:720px){ .l-dash{ grid-template-columns:1fr } .l-dash .side{ display:none } }
</style>
<div class="l-dash">
  <header class="top"><strong>Dashboard</strong></header>
  <aside class="side">Nav</aside>
  <main class="main"><div class="stat">12.4k</div><div class="stat">98%</div><div class="stat">$3.2k</div></main>
</div>"""},
    "masonry": {
        "best_for": "image walls, Pinterest-style feeds",
        "desc": "Uneven-height items packed in balanced columns (CSS columns).",
        "html": """<style>
  .l-masonry { column-count: 3; column-gap: 1rem; max-width: 1100px; margin: 0 auto;
               padding: 2rem 1.25rem; }
  .l-masonry .item { break-inside: avoid; margin: 0 0 1rem; border-radius: 12px;
                     background: var(--surface,#1e293b); border:1px solid var(--border,#334155); }
  @media (max-width:900px){ .l-masonry{ column-count:2 } }
  @media (max-width:560px){ .l-masonry{ column-count:1 } }
</style>
<div class="l-masonry">
  <div class="item" style="height:160px"></div><div class="item" style="height:230px"></div>
  <div class="item" style="height:120px"></div><div class="item" style="height:200px"></div>
</div>"""},
}

# --------------------------------------------------------------------------- #
#  Advanced CSS techniques — the things that separate intricate/artistic from
#  generic "AI-looking" frontends: layered depth, real texture, custom shapes,
#  blend/filter compositing, and motion tied to scroll. Modern CSS, paste-ready.
# --------------------------------------------------------------------------- #

TECHNIQUES: dict[str, dict] = {
    # ---- Color & gradient ------------------------------------------------ #
    "animated-gradient-border": {"cat": "color",
        "tags": ["border", "conic", "houdini", "@property", "glow"],
        "desc": "Rotating conic-gradient border via @property (Houdini). The "
                "signature 'this isn't a default template' border.",
        "code": """@property --angle { syntax: "<angle>"; initial-value: 0deg; inherits: false; }
.grad-border {
  position: relative; border-radius: 16px; padding: 2px; isolation: isolate;
  background: conic-gradient(from var(--angle), var(--accent), var(--accent2),
              var(--accent));
  animation: gb-spin 4s linear infinite;
}
.grad-border > * { border-radius: calc(var(--radius) - 2px); background: var(--surface); }
@keyframes gb-spin { to { --angle: 360deg; } }"""},
    "aurora-blur": {"cat": "color",
        "tags": ["aurora", "gradient", "blur", "ambient", "background"],
        "desc": "Soft drifting aurora — 3 blurred color blobs behind content. "
                "Replaces the flat one-gradient hero.",
        "code": """.aurora { position: relative; overflow: hidden; background: var(--bg); }
.aurora::before {
  content: ""; position: absolute; inset: -40%; z-index: 0;
  background:
    radial-gradient(closest-side, var(--accent), transparent) 0% 0% / 55% 55%,
    radial-gradient(closest-side, var(--accent2), transparent) 100% 0% / 50% 50%,
    radial-gradient(closest-side, color-mix(in srgb, var(--accent), var(--accent2)),
                    transparent) 50% 100% / 60% 60%;
  background-repeat: no-repeat; filter: blur(60px);
  animation: aurora-drift 14s ease-in-out infinite alternate;
}
.aurora > * { position: relative; z-index: 1; }
@keyframes aurora-drift {
  to { background-position: 100% 100%, 0% 60%, 40% 0%; }
}"""},
    "hue-rotate-text": {"cat": "color",
        "tags": ["text", "hue", "@property", "animated", "rainbow"],
        "desc": "Smoothly cycle a heading's hue with an animated custom property.",
        "code": """@property --hue { syntax: "<number>"; initial-value: 0; inherits: false; }
.hue-text {
  color: hsl(var(--hue) 90% 62%);
  text-shadow: 0 0 18px hsl(var(--hue) 90% 62% / 0.5);
  animation: hue-cycle 6s linear infinite;
}
@keyframes hue-cycle { to { --hue: 360; } }"""},

    # ---- Depth & lighting ------------------------------------------------ #
    "layered-shadows": {"cat": "depth",
        "tags": ["shadow", "depth", "realistic", "elevation"],
        "desc": "Stacked shadows that fake real light falloff — far softer/richer "
                "than one hard drop shadow (the #1 generic tell).",
        "code": """/* --shade is derived from the style's own ink, so the stack tints with the
   page instead of dropping a blue-grey wash on every palette. */
.depth {
  --shade: color-mix(in srgb, var(--text) 8%, transparent);
  box-shadow:
    0 1px 1px var(--shade), 0 2px 2px var(--shade),
    0 4px 4px var(--shade), 0 8px 8px var(--shade),
    0 16px 16px var(--shade), 0 32px 32px var(--shade);
}"""},
    "neumorphism": {"cat": "depth", "tags": ["neumorphism", "soft-ui", "shadow"],
        "desc": "Soft-UI dual light/dark shadow so elements extrude from the bg.",
        "code": """.neu {
  /* Both shadows are the surface itself, pushed darker and lighter — which
     is what makes the shape look extruded from the page it sits on. */
  --neu-dark: color-mix(in srgb, var(--surface) 78%, #000);
  --neu-lite: color-mix(in srgb, var(--surface) 78%, #fff);
  background: var(--bg2); border-radius: var(--radius);
  box-shadow: 8px 8px 16px var(--neu-dark), -8px -8px 16px var(--neu-lite);
}
.neu-inset { box-shadow: inset 6px 6px 12px var(--neu-dark),
                         inset -6px -6px 12px var(--neu-lite); }"""},
    "text-3d-extrude": {"cat": "depth", "tags": ["text", "3d", "extrude", "retro"],
        "desc": "Extruded 3D text via a stack of offset shadows.",
        "code": """.text-3d {
  --ext: color-mix(in srgb, var(--accent) 55%, #000);
  --ext-deep: color-mix(in srgb, var(--accent) 32%, #000);
  color: var(--accent); font-weight: 800;
  text-shadow: 1px 1px 0 var(--ext), 2px 2px 0 var(--ext), 3px 3px 0 var(--ext),
               4px 4px 0 var(--ext), 5px 5px 0 var(--ext-deep),
               7px 7px 10px rgba(0,0,0,.35);
}"""},
    "tilt-3d": {"cat": "depth", "tags": ["3d", "perspective", "hover", "card"],
        "desc": "Perspective tilt on hover — pairs with the spotlight-hover JS.",
        "code": """.tilt {
  transform-style: preserve-3d;
  transition: transform .25s cubic-bezier(.22,1,.36,1);
}
.tilt:hover {
  transform: perspective(900px) rotateX(6deg) rotateY(-8deg) translateZ(12px);
}
.tilt > * { transform: translateZ(30px); }"""},
    "spotlight-hover": {"cat": "depth", "tags": ["hover", "cursor", "glow", "js"],
        "desc": "Radial glow that follows the cursor across a card (CSS + 4 lines JS).",
        "code": """.spot { position: relative; overflow: hidden; }
.spot::before {
  content: ""; position: absolute; inset: 0; opacity: 0; transition: opacity .3s;
  background: radial-gradient(220px circle at var(--mx,50%) var(--my,50%),
              color-mix(in srgb, var(--accent) 25%, transparent), transparent 65%);
}
.spot:hover::before { opacity: 1; }
/* JS:
document.querySelectorAll('.spot').forEach(el => el.addEventListener('mousemove', e => {
  const r = el.getBoundingClientRect();
  el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
  el.style.setProperty('--my', (e.clientY - r.top) + 'px');
})); */"""},

    # ---- Shape & masking ------------------------------------------------- #
    "clip-path-shapes": {"cat": "shape",
        "tags": ["clip-path", "polygon", "diagonal", "hexagon", "shape"],
        "desc": "Break the rectangle — diagonal sections, hexagons, arrows via clip-path.",
        "code": """.diagonal { clip-path: polygon(0 0, 100% 0, 100% 88%, 0 100%); }
.hexagon  { clip-path: polygon(25% 0,75% 0,100% 50%,75% 100%,25% 100%,0 50%); }
.arrow    { clip-path: polygon(0 0,75% 0,100% 50%,75% 100%,0 100%); }
.blob-cut { clip-path: polygon(0 15%,15% 0,85% 0,100% 15%,100% 85%,85% 100%,15% 100%,0 85%); }"""},
    "blob-morph": {"cat": "shape", "tags": ["blob", "organic", "morph", "animated"],
        "desc": "Organic blob that slowly morphs — great as a decorative mask/backdrop.",
        "code": """.blob {
  border-radius: 42% 58% 70% 30% / 45% 45% 55% 55%;
  animation: blob 8s ease-in-out infinite;
}
@keyframes blob {
  0%,100% { border-radius: 42% 58% 70% 30% / 45% 45% 55% 55%; }
  33% { border-radius: 70% 30% 46% 54% / 30% 60% 40% 70%; }
  66% { border-radius: 34% 66% 60% 40% / 65% 35% 60% 40%; }
}"""},
    "mask-fade-reveal": {"cat": "shape",
        "tags": ["mask", "gradient", "fade", "reveal", "knockout"],
        "desc": "Gradient masks: fade edges, and knock an image out through text.",
        "code": """.mask-fade {
  -webkit-mask-image: linear-gradient(#000 55%, transparent);
          mask-image: linear-gradient(#000 55%, transparent);
}
.text-knockout {
  background: var(--knockout-image, var(--text));
  background-position: center; background-size: cover;
  -webkit-background-clip: text; background-clip: text; color: transparent;
  font-weight: 900; font-size: var(--size-0);
}"""},
    "scroll-mask-wipe": {"cat": "shape",
        "tags": ["mask", "scroll", "reveal", "wipe"],
        "desc": "A mask that wipes open as the element scrolls into view (no JS).",
        "code": """@keyframes wipe { from { -webkit-mask-size: 0 100%; mask-size: 0 100%; }
                  to   { -webkit-mask-size: 100% 100%; mask-size: 100% 100%; } }
.wipe {
  -webkit-mask: linear-gradient(#000,#000) left/0 100% no-repeat;
          mask: linear-gradient(#000,#000) left/0 100% no-repeat;
  animation: wipe linear both; animation-timeline: view();
  animation-range: entry 10% cover 45%;
}"""},

    # ---- Filters & compositing ------------------------------------------- #
    "gooey": {"cat": "filter", "tags": ["svg-filter", "gooey", "blob", "merge"],
        "desc": "Gooey merge filter — blobs/menu items melt together (SVG filter + CSS).",
        "code": """<svg style="position:absolute;width:0;height:0"><defs>
  <filter id="goo">
    <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="b"/>
    <feColorMatrix in="b" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7"/>
  </filter>
</defs></svg>
.goo { filter: url(#goo); }        /* put on the PARENT of the blobs */"""},
    "grain-overlay": {"cat": "filter",
        "tags": ["grain", "noise", "texture", "film", "animated"],
        "desc": "Film-grain over the whole page — instant analog richness. Default "
                "STATIC (free); the animated variant repaints a 2x-viewport fixed "
                "layer ~7x/sec and visibly janks pages that also use blurs/filters.",
        "code": """/* Static grain (default — texture reads the same, zero per-frame cost) */
.grain::after {
  content: ""; position: fixed; inset: 0; z-index: 9999; pointer-events: none;
  opacity: .06;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
/* Animated variant — ONLY for pages with few other filters/blurs:
   add `inset: -50%; animation: grain .6s steps(4) infinite;` plus
   @keyframes grain { 0%{transform:translate(0,0)} 50%{transform:translate(-4%,3%)} 100%{transform:translate(3%,-2%)} } */"""},
    "duotone": {"cat": "filter", "tags": ["duotone", "svg-filter", "image", "editorial"],
        "desc": "Duotone any image into two brand colors (SVG feColorMatrix map).",
        "code": """<svg style="position:absolute;width:0;height:0"><defs>
  <filter id="duo">
    <feColorMatrix type="matrix" values="0.3 0.6 0.1 0 0  0.3 0.6 0.1 0 0  0.3 0.6 0.1 0 0  0 0 0 1 0"/>
    <feComponentTransfer color-interpolation-filters="sRGB">
      <feFuncR type="table" tableValues="0.05 0.95"/>
      <feFuncG type="table" tableValues="0.10 0.80"/>
      <feFuncB type="table" tableValues="0.30 0.60"/>
    </feComponentTransfer>
  </filter>
</defs></svg>
img.duo { filter: url(#duo); }"""},
    "chromatic-aberration": {"literals": "red/cyan fringing is the optical effect being imitated; recolouring it to the palette stops it reading as lens dispersion","cat": "filter",
        "tags": ["glitch", "rgb-split", "chromatic", "text"],
        "desc": "RGB-split chromatic aberration on hover — subtle digital-glitch edge.",
        "code": """.chroma { transition: text-shadow .2s, transform .2s; }
.chroma:hover {
  text-shadow: -2px 0 rgba(255,0,90,.8), 2px 0 rgba(0,220,255,.8);
  transform: translateX(0.5px);
}"""},
    "liquid-hover": {"cat": "filter",
        "tags": ["svg-filter", "displacement", "liquid", "distortion", "hover"],
        "desc": "Turbulence + displacement for a liquid/heat-haze distortion on hover.",
        "code": """<svg style="position:absolute;width:0;height:0"><defs>
  <filter id="liquid">
    <feTurbulence type="fractalNoise" baseFrequency="0.012 0.02" numOctaves="2" result="t"/>
    <feDisplacementMap in="SourceGraphic" in2="t" scale="0">
      <animate attributeName="scale" begin="mouseover" dur="0.6s" values="0;22;0" fill="freeze"/>
    </feDisplacementMap>
  </filter>
</defs></svg>
.liquid:hover { filter: url(#liquid); }"""},
    "blend-duotone-bg": {"cat": "filter",
        "tags": ["mix-blend-mode", "blend", "compositing", "layered"],
        "desc": "Layer color over imagery with blend modes (multiply/overlay/screen) "
                "for editorial compositing instead of flat overlays.",
        "code": """.blend {
  position: relative; background: url(photo.jpg) center/cover;
}
.blend::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(45deg, var(--accent), var(--accent2));
  mix-blend-mode: overlay;      /* try: multiply, screen, color, difference */
}"""},

    # ---- Motion & scroll ------------------------------------------------- #
    "scroll-reveal": {"cat": "motion",
        "tags": ["scroll", "reveal", "animation-timeline", "no-js"],
        "desc": "Fade + rise as elements enter the viewport — pure CSS scroll-driven "
                "animation, no IntersectionObserver.",
        "code": """@keyframes reveal { from { opacity: 0; transform: translateY(40px); }
                    to   { opacity: 1; transform: none; } }
.reveal {
  animation: reveal linear both;
  animation-timeline: view();
  animation-range: entry 0% cover 40%;
}"""},
    "scroll-parallax": {"cat": "motion",
        "tags": ["scroll", "parallax", "animation-timeline", "depth"],
        "desc": "Real parallax bound to scroll progress (no JS, no jank).",
        "code": """.parallax {
  animation: para linear both;
  animation-timeline: scroll(root);
}
@keyframes para { to { transform: translateY(-140px); } }"""},
    "infinite-marquee": {"cat": "motion",
        "tags": ["marquee", "ticker", "loop", "kinetic"],
        "desc": "Seamless infinite marquee (duplicate the track for the loop).",
        "code": """.marquee { overflow: hidden; }
.marquee__track {
  display: inline-flex; gap: 3rem; white-space: nowrap;
  animation: marquee 22s linear infinite;
}
.marquee:hover .marquee__track { animation-play-state: paused; }
@keyframes marquee { to { transform: translateX(-50%); } }
/* duplicate the content twice inside .marquee__track */"""},
    "view-transitions": {"cat": "motion",
        "tags": ["view-transitions", "morph", "spa", "page-transition"],
        "desc": "Smooth morphing transitions between DOM states (View Transitions API).",
        "code": """/* CSS */
::view-transition-old(root), ::view-transition-new(root) { animation-duration: .45s; }
.hero-img { view-transition-name: hero; }   /* shared element morph */
/* JS */
if (document.startViewTransition) {
  document.startViewTransition(() => updateTheDOM());
} else { updateTheDOM(); }"""},

    # ---- Type ------------------------------------------------------------ #
    "stroke-text": {"cat": "type", "tags": ["text", "outline", "stroke", "editorial"],
        "desc": "Outlined (hollow) display type — huge headings without a fill.",
        "code": """.stroke {
  -webkit-text-stroke: 2px var(--accent); color: transparent;
  font-weight: 900; font-size: clamp(var(--size-0, 3rem), 12vw, 9rem);
}
.stroke-fill:hover { color: var(--accent); -webkit-text-stroke-color: transparent; }"""},
    "variable-font-anim": {"cat": "type",
        "tags": ["text", "variable-font", "weight", "kinetic"],
        "desc": "Animate a variable font's weight/width for living, kinetic type.",
        "code": """.vf {
  font-variation-settings: "wght" 300;
  animation: vf-breathe 3s ease-in-out infinite alternate;
}
@keyframes vf-breathe {
  to { font-variation-settings: "wght" 800; letter-spacing: .02em; }
}"""},

    # ===================== WAVE 2 — newest CSS ============================= #
    # ---- Color ----------------------------------------------------------- #
    "oklch-gradients": {"cat": "color",
        "tags": ["oklch", "gradient", "perceptual", "vivid"],
        "desc": "Interpolate gradients in oklch so the midpoint stays vivid — no "
                "muddy gray middle you get from sRGB blends.",
        "code": """.oklch-bg { background: linear-gradient(90deg in oklch, var(--accent), var(--accent2)); }
/* perceptually-even ramp (great for data viz / heatmaps): */
.ramp { background: linear-gradient(in oklch, oklch(72% .17 250), oklch(72% .17 20)); }"""},
    "color-mix-theming": {"cat": "color",
        "tags": ["color-mix", "theming", "tokens", "tints"],
        "desc": "Derive hovers, tints, and borders from ONE brand var with "
                "color-mix() — no separate shade tokens to maintain.",
        "code": """:root { --brand: var(--accent, #2b8fd6); }
.btn        { background: var(--brand); }
.btn:hover  { background: color-mix(in oklab, var(--brand), #000 14%); }
.tint       { background: color-mix(in srgb, var(--brand) 12%, transparent); }
.soft-border{ border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent); }"""},
    "holographic-conic": {"literals": "iridescence is a spread across the spectrum, not a brand pair — two accents produce a gradient, not a hologram","cat": "color",
        "tags": ["holographic", "iridescent", "conic", "@property", "animated"],
        "desc": "Spinning iridescent/holographic sheen from an animated conic gradient.",
        "code": """@property --a { syntax: "<angle>"; initial-value: 0deg; inherits: false; }
.holo {
  background: conic-gradient(from var(--a),
    #ff71ce, #01cdfe, #05ffa1, #fffb96, #b967ff, #ff71ce);
  animation: holo 6s linear infinite;
}
@keyframes holo { to { --a: 360deg; } }"""},
    "progress-ring": {"cat": "color",
        "tags": ["progress", "ring", "conic", "@property", "gauge"],
        "desc": "Conic progress ring with a masked hole and a smoothly animatable %.",
        "code": """@property --p { syntax: "<number>"; initial-value: 0; inherits: false; }
.ring {
  --p: 65; width: 120px; aspect-ratio: 1; border-radius: 50%;
  background: conic-gradient(var(--accent) calc(var(--p) * 1%), var(--border) 0);
  -webkit-mask: radial-gradient(farthest-side, transparent 70%, #000 72%);
          mask: radial-gradient(farthest-side, transparent 70%, #000 72%);
  transition: --p 1s ease;
}"""},

    # ---- Depth ----------------------------------------------------------- #
    "glass-layered": {"cat": "depth",
        "tags": ["glass", "glassmorphism", "backdrop", "light"],
        "desc": "Proper frosted glass: blur+saturate, a top sheen, and a light "
                "inner border — not just a translucent white box.",
        "code": """.glass {
  background: var(--surface-glass, rgba(255,255,255,.08));
  background-image: var(--sheen, linear-gradient(rgba(255,255,255,.14),
                                                 rgba(255,255,255,.04)));
  backdrop-filter: blur(16px) saturate(170%);
  -webkit-backdrop-filter: blur(16px) saturate(170%);
  border: 1px solid rgba(255,255,255,.25); border-radius: 18px;
  box-shadow: 0 8px 32px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.35);
}"""},
    "gradient-border-mask": {"cat": "depth",
        "tags": ["border", "gradient", "mask-composite", "true-gradient"],
        "desc": "A REAL gradient border (any radius) via mask-composite — no "
                "padding-box hack, content keeps its own background.",
        "code": """.g-border { position: relative; border-radius: 16px; }
.g-border::before {
  content: ""; position: absolute; inset: 0; padding: 2px; border-radius: inherit;
  background: linear-gradient(135deg, var(--accent), var(--accent2), var(--accent));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none;
}"""},
    "pixel-art-shadow": {"cat": "depth",
        "tags": ["pixel-art", "box-shadow", "retro", "8-bit"],
        "desc": "Draw pixel art with box-shadow (one shadow = one pixel), scaled up.",
        "code": """.pixel {
  width: 6px; height: 6px; transform: scale(6); transform-origin: top left;
  image-rendering: pixelated; background: var(--accent);
  box-shadow:
    6px 0 var(--accent), 12px 6px var(--accent2), 0 6px var(--accent2),
    18px 12px var(--text);
  /* generate the shadow list programmatically for real sprites */
}"""},

    # ---- Layout ---------------------------------------------------------- #
    "anchor-tooltip": {"cat": "layout",
        "tags": ["anchor-positioning", "tooltip", "popover", "modern"],
        "desc": "Tether a tooltip/popover to an element with CSS anchor positioning "
                "— no JS positioning math.",
        "code": """.trigger { anchor-name: --t; }
.tooltip {
  position: absolute; position-anchor: --t;
  top: anchor(bottom); justify-self: anchor-center; translate: 0 8px;
  /* @supports not (anchor-name: --t) { fall back to position:absolute } */
}"""},
    "container-query": {"cat": "layout",
        "tags": ["container-query", "responsive", "component", "@container"],
        "desc": "Style a component by ITS OWN width, not the viewport — real "
                "reusable responsive components.",
        "code": """.card-wrap { container-type: inline-size; }
.card { display: grid; gap: 1rem; }
@container (min-width: 420px) {
  .card { grid-template-columns: 140px 1fr; align-items: center; }
}"""},
    "subgrid-align": {"cat": "layout",
        "tags": ["subgrid", "grid", "alignment"],
        "desc": "Make card internals (title/body/footer) line up ACROSS cards with "
                "subgrid.",
        "code": """.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.card { display: grid; grid-row: span 3; grid-template-rows: subgrid; gap: .5rem; }
/* every card's title row, body row, and footer row now share a baseline */"""},
    "scroll-snap-carousel": {"cat": "layout",
        "tags": ["scroll-snap", "carousel", "slider", "no-js"],
        "desc": "A snappy horizontal carousel with zero JS.",
        "code": """.carousel {
  display: flex; gap: 1rem; overflow-x: auto; scroll-snap-type: x mandatory;
  scrollbar-width: none; scroll-behavior: smooth;
}
.carousel::-webkit-scrollbar { display: none; }
.carousel > * { flex: 0 0 78%; scroll-snap-align: center; }"""},
    "sticky-stack-cards": {"cat": "layout",
        "tags": ["sticky", "stack", "scroll", "cards"],
        "desc": "Cards that pin and stack under each other as you scroll (the "
                "'deck' effect).",
        "code": """.stack { display: grid; gap: 2rem; }
.stack .card {
  position: sticky; top: 6vh; min-height: 70vh; border-radius: 22px;
}
/* each successive card scrolls up and pins over the previous one */"""},

    # ---- Filter ---------------------------------------------------------- #
    "svg-soft-glow": {"cat": "filter",
        "tags": ["glow", "neon", "svg-filter", "bloom"],
        "desc": "Soft bloom/neon glow around anything (SVG blur + merge filter).",
        "code": """<svg style="position:absolute;width:0;height:0"><defs>
  <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs></svg>
.glow { filter: url(#glow); }"""},
    "halftone-dots": {"cat": "filter",
        "tags": ["halftone", "dots", "print", "comic", "texture"],
        "desc": "Comic/print halftone dot texture over a fill (blend a dot grid).",
        "code": """.halftone {
  /* hard-stop dots (30% -> 31%) are an edge, not a blend — this is a
     printing screen, and it inherits the page's own ink and field. */
  background:
    radial-gradient(currentColor 30%, transparent 31%) 0 0 / 8px 8px,
    var(--bg2, #fff);
  background-blend-mode: multiply;
}"""},

    # ---- Motion ---------------------------------------------------------- #
    "scroll-scrub-sequence": {"cat": "motion",
        "tags": ["scroll", "scrub", "scroll-timeline", "hero", "no-js"],
        "desc": "Scrub a hero animation to scroll position (zoom/pan a background "
                "as you scroll) — scroll-timeline, no JS.",
        "code": """@keyframes zoom { to { transform: scale(1.35); opacity: .35; } }
.hero__img {
  animation: zoom linear both;
  animation-timeline: scroll(root block);
  animation-range: 0 70vh;
}"""},
    "staggered-reveal": {"cat": "motion",
        "tags": ["scroll", "stagger", "reveal", "view-timeline"],
        "desc": "A list whose items reveal one-by-one as each enters view (natural "
                "stagger, no per-item JS delays).",
        "code": """@keyframes rise { from { opacity: 0; transform: translateY(28px); }
                  to   { opacity: 1; transform: none; } }
.stagger > * {
  animation: rise linear both;
  animation-timeline: view();
  animation-range: entry 0% cover 28%;
}"""},
    "sticky-shrink-header": {"cat": "motion",
        "tags": ["header", "scroll", "shrink", "scroll-timeline"],
        "desc": "Header that condenses + frosts as you scroll — driven by scroll "
                "progress, not a JS scroll listener.",
        "code": """@keyframes condense {
  to { padding-block: .4rem;
       background: color-mix(in srgb, var(--bg) 85%, transparent);
       backdrop-filter: blur(10px); }
}
.site-header {
  position: sticky; top: 0; padding-block: 1.2rem;
  animation: condense linear both;
  animation-timeline: scroll(root); animation-range: 0 140px;
}"""},
    "card-flip-3d": {"cat": "motion",
        "tags": ["3d", "flip", "card", "backface"],
        "desc": "3D flip card (front/back) on hover.",
        "code": """.flip { perspective: 1000px; }
.flip__inner { position: relative; transition: transform .6s; transform-style: preserve-3d; }
.flip:hover .flip__inner { transform: rotateY(180deg); }
.flip__front, .flip__back {
  position: absolute; inset: 0; backface-visibility: hidden; border-radius: 16px;
}
.flip__back { transform: rotateY(180deg); }"""},
    "elastic-ease": {"cat": "motion",
        "tags": ["easing", "spring", "linear()", "overshoot"],
        "desc": "Springy overshoot with the new linear() easing — bouncy motion "
                "without a physics lib.",
        "code": """.pop { transition: transform .5s linear(
  0, .38 12%, .82 24%, 1.05 40%, 1.02 52%, .99 68%, 1); }
.pop:hover { transform: scale(1.14); }"""},
    "sheen-sweep": {"cat": "motion",
        "tags": ["sheen", "shine", "hover", "gloss"],
        "desc": "A light sheen that sweeps across a card/button on hover (glossy).",
        "code": """.sheen { position: relative; overflow: hidden; }
.sheen::after {
  content: ""; position: absolute; inset: 0; transform: translateX(-120%);
  background: linear-gradient(105deg, transparent 40%,
              rgba(255,255,255,.4) 50%, transparent 60%);
  transition: transform .6s;
}
.sheen:hover::after { transform: translateX(120%); }"""},

    # ---- Interaction ----------------------------------------------------- #
    "has-relational": {"cat": "interaction",
        "tags": [":has", "relational", "parent", "state", "modern-selector"],
        "desc": "Style a parent from its children/state with :has() — quantity "
                "queries, form validity, active card, all with no JS.",
        "code": """.card:has(input:checked) { border-color: var(--accent);
                           background: color-mix(in srgb, var(--accent) 6%, transparent); }
label:has(+ input:focus) { color: var(--accent); }
form:has(:invalid) button[type="submit"] { opacity: .5; pointer-events: none; }
.grid:has(> :nth-child(6)) { gap: .5rem; }   /* quantity query */"""},
    "css-only-accordion": {"cat": "interaction",
        "tags": ["accordion", "details", "disclosure", "no-js"],
        "desc": "Accessible accordion/disclosure with zero JS using <details>.",
        "code": """<details class="acc"><summary>Section title</summary>
  <div class="acc__body">Content…</div>
</details>
.acc { border-bottom: 1px solid var(--border, #334155); }
.acc summary { cursor: pointer; list-style: none; padding: 1rem 0; font-weight: 600; }
.acc summary::-webkit-details-marker { display: none; }
.acc[open] summary { color: var(--accent, #05d9e8); }"""},

    # ---- Type ------------------------------------------------------------ #
    "text-on-path": {"cat": "type",
        "tags": ["text", "svg", "textpath", "curved", "kinetic"],
        "desc": "Flow text along a curved SVG path — badges, seals, kinetic headers.",
        "code": """<svg viewBox="0 0 300 130" width="300">
  <path id="curve" fill="none" d="M12,95 Q150,5 288,95"/>
  <text font-size="22" font-weight="700" fill="currentColor" style="color: var(--accent)">
    <textPath href="#curve" startOffset="50%" text-anchor="middle">
      curved kinetic type
    </textPath>
  </text>
</svg>"""},

    # ===================== WAVE 3 — bleeding-edge CSS ===================== #
    # ---- Color ----------------------------------------------------------- #
    "relative-color-syntax": {"cat": "color",
        "tags": ["relative-color", "derive", "palette", "oklch", "modern"],
        "desc": "Derive tints/shades/alpha from ONE color with Relative Color "
                "Syntax — generate a whole ramp from a single brand var.",
        "code": """:root { --brand: var(--accent, #2b8fd6); }
.lighter { background: oklch(from var(--brand) calc(l + .12) c h); }
.darker  { background: oklch(from var(--brand) calc(l - .12) c h); }
.faded   { background: oklch(from var(--brand) l c h / .15); }
.comp    { background: oklch(from var(--brand) l c calc(h + 180)); } /* complement */"""},
    "light-dark-fn": {"literals": "a syntax demonstration of light-dark(); the two literals are the sample light and dark values the function switches between","cat": "color",
        "tags": ["light-dark", "theming", "dark-mode", "modern"],
        "desc": "Automatic light/dark values with the light-dark() function — one "
                "declaration, both modes, no media query.",
        "code": """:root { color-scheme: light dark; }
body {
  background: light-dark(#f8fafc, #0d0221);
  color:      light-dark(#0b3c5d, #d1f7ff);
}
.card { border: 1px solid light-dark(#e2e8f0, #1e293b); }"""},
    "mesh-gradient-svg": {"cat": "color",
        "tags": ["mesh", "gradient", "svg", "hero", "smooth"],
        "desc": "True smooth mesh gradient (SVG) — richer than layered radials.",
        "code": """<svg width="100%" height="100%" style="position:absolute;inset:0;z-index:-1">
  <defs>
    <radialGradient id="g1" cx="20%" cy="20%"><stop offset="0" stop-color="var(--accent)"/>
      <stop offset="1" stop-color="var(--accent)" stop-opacity="0"/></radialGradient>
    <radialGradient id="g2" cx="80%" cy="30%"><stop offset="0" stop-color="var(--accent2)"/>
      <stop offset="1" stop-color="var(--accent2)" stop-opacity="0"/></radialGradient>
    <radialGradient id="g3" cx="50%" cy="90%"><stop offset="0"
        stop-color="color-mix(in srgb, var(--accent), var(--accent2))"/>
      <stop offset="1" stop-color="transparent"/></radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="var(--bg)"/>
  <rect width="100%" height="100%" fill="url(#g1)"/>
  <rect width="100%" height="100%" fill="url(#g2)"/>
  <rect width="100%" height="100%" fill="url(#g3)"/>
</svg>"""},

    # ---- Depth ----------------------------------------------------------- #
    "squircle-corners": {"cat": "depth",
        "tags": ["squircle", "corner-shape", "superellipse", "ios", "modern"],
        "desc": "Apple-style squircle corners with corner-shape: superellipse "
                "(smoother than border-radius).",
        "code": """.squircle {
  border-radius: 28px;
  corner-shape: superellipse(4);   /* higher = squarer; ~2.2 ≈ iOS */
}
/* @supports not (corner-shape: superellipse(4)) { .squircle { border-radius: 22px } } */"""},
    "emboss-letterpress": {"cat": "depth",
        "tags": ["text", "emboss", "letterpress", "engrave", "subtle"],
        "desc": "Letterpress/emboss text — carved into or raised off the surface.",
        "code": """/* on a mid-tone bg: */
/* The bevel highlights stay achromatic — they are light, not palette — while
   the ink comes from the style so the effect works on any ground. */
.letterpress { color: var(--muted); text-shadow: 0 1px 0 rgba(255,255,255,.6),
                                                 0 -1px 0 rgba(0,0,0,.5); }
.engrave     { color: var(--text); text-shadow: 0 1px 1px rgba(255,255,255,.5); }"""},

    # ---- Shape ----------------------------------------------------------- #
    "shape-outside-wrap": {"cat": "shape",
        "tags": ["shape-outside", "text-wrap", "float", "editorial"],
        "desc": "Wrap paragraph text around a circle/blob — real magazine flow.",
        "code": """.wrapper { float: left; width: 220px; height: 220px; margin: 0 1.5rem 1rem 0;
  shape-outside: circle(50%); clip-path: circle(50%);
  background: url(portrait.jpg) center/cover; }
/* following text now hugs the circular image */"""},
    "clip-path-animate": {"cat": "shape",
        "tags": ["clip-path", "animate", "reveal", "morph"],
        "desc": "Animate clip-path to wipe/morph a reveal (transition or keyframes).",
        "code": """.reveal-clip {
  clip-path: inset(0 100% 0 0);
  transition: clip-path .6s cubic-bezier(.22,1,.36,1);
}
.reveal-clip.in { clip-path: inset(0 0 0 0); }
/* or a shape morph: */
@keyframes morph { to { clip-path: polygon(0 0,100% 0,100% 100%,0 85%); } }"""},

    # ---- Interaction ----------------------------------------------------- #
    "popover-api": {"cat": "interaction",
        "tags": ["popover", "native", "menu", "modal", "no-js"],
        "desc": "Native Popover API — menus/tooltips/dialogs with top-layer + "
                "backdrop and zero JS.",
        "code": """<button popovertarget="menu">Open</button>
<div id="menu" popover>…</div>
[popover] { border: 1px solid var(--border,#334155); border-radius: 12px; padding: 1rem; }
/* a solid scrim, not a blur: backdrop-filter costs contrast and some
   styles refuse glass outright. */
[popover]::backdrop { background: rgba(0,0,0,.55); }"""},
    "field-sizing-auto": {"cat": "interaction",
        "tags": ["field-sizing", "textarea", "auto-grow", "form", "modern"],
        "desc": "Auto-growing inputs/textareas with field-sizing: content — no JS "
                "resize hack.",
        "code": """textarea, input { field-sizing: content; min-height: 2.5rem; max-height: 12rem; }"""},
    "css-tabs": {"cat": "interaction",
        "tags": ["tabs", "radio", ":has", "no-js"],
        "desc": "Pure-CSS tabs (radio inputs + :has) — no JavaScript.",
        "code": """<div class="tabs">
  <input type="radio" name="t" id="t1" checked><label for="t1">One</label>
  <input type="radio" name="t" id="t2"><label for="t2">Two</label>
  <div class="panel p1">First</div><div class="panel p2">Second</div>
</div>
.tabs .panel { display: none; }
.tabs:has(#t1:checked) .p1, .tabs:has(#t2:checked) .p2 { display: block; }
.tabs label { cursor: pointer; padding: .5rem 1rem; }
.tabs input { display: none; }
.tabs:has(#t1:checked) label[for=t1] { border-bottom: 2px solid var(--accent,#05d9e8); }"""},

    # ---- Filter ---------------------------------------------------------- #
    "crt-screen": {"cat": "filter",
        "tags": ["crt", "retro", "scanlines", "vignette", "flicker"],
        "desc": "Full CRT monitor look — scanlines + vignette + subtle flicker.",
        "code": """.crt { position: relative; overflow: hidden; }
.crt::before {  /* scanlines */
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 2;
  background: repeating-linear-gradient(rgba(0,0,0,.15) 0 1px, transparent 1px 3px);
}
.crt::after {   /* vignette + flicker */
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 3;
  background: radial-gradient(circle, transparent 60%, rgba(0,0,0,.5));
  animation: crt-flick 6s infinite steps(120);
}
@keyframes crt-flick { 0%,98%{opacity:1} 99%{opacity:.82} 100%{opacity:1} }"""},
    "turbulence-bg": {"cat": "filter",
        "tags": ["turbulence", "marble", "clouds", "svg", "animated", "background"],
        "desc": "Living organic background (marble / clouds / smoke) via animated "
                "SVG feTurbulence.",
        "code": """<svg style="position:absolute;inset:0;width:100%;height:100%;z-index:-1">
  <filter id="marble">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.012" numOctaves="4" seed="7">
      <animate attributeName="baseFrequency" dur="30s"
        values="0.008 0.012; 0.012 0.008; 0.008 0.012" repeatCount="indefinite"/>
    </feTurbulence>
    <feColorMatrix values="0 0 0 0 0.17  0 0 0 0 0.56  0 0 0 0 0.84  0 0 0 1 0"/>
  </filter>
  <rect width="100%" height="100%" filter="url(#marble)"/>
</svg>"""},
    "frosted-noise": {"cat": "filter",
        "tags": ["glass", "frosted", "noise", "realistic", "backdrop"],
        "desc": "Realistic frosted glass = backdrop blur + a faint noise grain on top.",
        "code": """.frosted {
  position: relative; backdrop-filter: blur(18px) saturate(160%);
  background: var(--surface-glass, rgba(255,255,255,.06));
  border-radius: var(--radius, 16px);
}
.frosted::after {
  content: ""; position: absolute; inset: 0; border-radius: inherit; opacity: .5;
  mix-blend-mode: overlay; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='0.9'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.4'/%3E%3C/svg%3E");
}"""},

    # ---- Motion ---------------------------------------------------------- #
    "scroll-progress-bar": {"cat": "motion",
        "tags": ["scroll", "progress", "reading-bar", "scroll-timeline", "no-js"],
        "desc": "A reading-progress bar that fills with page scroll — pure CSS "
                "scroll-timeline.",
        "code": """.progress {
  position: fixed; top: 0; left: 0; height: 3px; width: 100%; transform-origin: left;
  background: var(--accent, #2b8fd6);
  animation: grow linear; animation-timeline: scroll(root);
}
@keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }"""},
    "parallax-layers": {"cat": "motion",
        "tags": ["parallax", "layers", "depth", "scroll-timeline"],
        "desc": "Multi-depth parallax — background/mid/foreground move at different "
                "speeds, all scroll-driven.",
        "code": """.layer { animation: shift linear both; animation-timeline: scroll(root block); }
.layer--bg  { --d: -60px; }  .layer--mid { --d: -140px; }  .layer--fg { --d: -260px; }
@keyframes shift { to { transform: translateY(var(--d)); } }"""},
    "text-line-reveal": {"cat": "motion",
        "tags": ["text", "reveal", "lines", "scroll", "mask"],
        "desc": "Reveal a heading line-by-line (each line rises out of a clip) as it "
                "enters view.",
        "code": """.reveal-lines .line { overflow: hidden; }
.reveal-lines .line > span {
  display: inline-block; transform: translateY(100%);
  animation: line-up linear both; animation-timeline: view();
  animation-range: entry 0% cover 30%;
}
@keyframes line-up { to { transform: translateY(0); } }"""},
    "rotating-text-ring": {"cat": "motion",
        "tags": ["text", "circular", "rotate", "3d", "badge"],
        "desc": "Circular text badge that slowly rotates (each letter positioned "
                "around a ring).",
        "code": """.ring { position: relative; width: 180px; aspect-ratio: 1;
  animation: spin 12s linear infinite; }
.ring span {
  position: absolute; inset: 0; text-align: center;
  transform: rotate(calc(var(--i) * 15deg));      /* set --i per letter */
}
.ring span b { display: inline-block; transform: translateY(-84px); }
@keyframes spin { to { transform: rotate(360deg); } }"""},

    # ---- Type ------------------------------------------------------------ #
    "dropcap-initial-letter": {"cat": "type",
        "tags": ["dropcap", "initial-letter", "editorial", "typography"],
        "desc": "Real drop cap with initial-letter — sinks the first letter across "
                "N lines like print.",
        "code": """p.article::first-letter {
  initial-letter: 3;            /* 3 lines tall */
  font-weight: 800; margin-right: .5rem; color: var(--accent, #c1440e);
}"""},
    "text-balance-wrap": {"cat": "type",
        "tags": ["text-wrap", "balance", "pretty", "typography"],
        "desc": "Pro typographic line-breaking: balanced headlines, no orphans in "
                "body copy.",
        "code": """h1, h2, h3 { text-wrap: balance; }   /* even, centered-looking lines */
p        { text-wrap: pretty; }    /* avoids single-word last lines (orphans) */"""},

    # ---- Houdini --------------------------------------------------------- #
    "houdini-paint": {"cat": "filter",
        "tags": ["houdini", "paint-worklet", "procedural", "advanced"],
        "desc": "Procedural backgrounds with the CSS Paint API (Houdini worklet) — "
                "draw anything (confetti, waves, noise) as a CSS background.",
        "code": """/* paint.js */
registerPaint("sprinkles", class {
  static get inputProperties() { return ["--sprinkle-color"]; }
  paint(ctx, size, props) {
    const c = props.get("--sprinkle-color").toString() || "currentColor";
    for (let i = 0; i < 60; i++) {
      ctx.fillStyle = c; ctx.globalAlpha = Math.random();
      ctx.fillRect(Math.random()*size.width, Math.random()*size.height, 3, 3);
    }
  }
});
/* CSS */  /* CSS.paintWorklet.addModule("paint.js") */
.sprinkled { background-image: paint(sprinkles); --sprinkle-color: var(--accent); }"""},

    # ---- Anti-bubble containers (born on the IST5930 robotics site) ------- #
    "hud-plate": {"cat": "depth",
        "tags": ["cut-corner", "panel", "card", "hud", "anti-bubble", "plate",
                 "technical", "clip-path"],
        "desc": "The anti-bubble card: cut-corner plate (clip-path) with an accent "
                "notch strip, hairline inset edge, drop-shadow depth that follows "
                "the shape, and a corner-cut morph on hover. Use INSTEAD of "
                "rounded 'glass bubble' cards — the #1 generic-AI-site tell.",
        "code": """/* Set --mc (accent) per card for color-coded notches. No border-radius anywhere. */
@property --cut { syntax: "<length>"; initial-value: 18px; inherits: false; }
.plate {
  --cut: 18px; --mc: var(--accent);
  position: relative;
  background:
    /* accent notch strip along the top-right cut */
    linear-gradient(to bottom left,
      color-mix(in srgb, var(--mc) 75%, transparent) calc(var(--cut) + 1px),
      transparent calc(var(--cut) + 1px))
      top right / calc(var(--cut) * 2.2) calc(var(--cut) * 2.2) no-repeat,
    linear-gradient(color-mix(in srgb, var(--text) 9%, transparent),
                    color-mix(in srgb, var(--text) 2%, transparent)),
    linear-gradient(color-mix(in srgb, var(--surface) 45%, transparent),
                    color-mix(in srgb, var(--surface) 45%, transparent));
  /* PERF: no backdrop-filter here — over a flat page bg the frosting is
     invisible but costs a live blur pass per plate (x25 plates = jank).
     Only add backdrop-filter when the plate truly overlaps busy imagery. */
  clip-path: polygon(0 0, calc(100% - var(--cut)) 0, 100% var(--cut),
                     100% 100%, var(--cut) 100%, 0 calc(100% - var(--cut)));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--text) 17%, transparent),
              inset 0 1px 0 rgba(255,255,255,.12);
  /* outer box-shadow gets clipped — drop-shadow follows the cut shape instead.
     PERF: ONE drop-shadow; stacking two doubles the filter cost per plate. */
  filter: drop-shadow(0 12px 24px rgba(0,0,0,.35));
  transition: --cut .35s cubic-bezier(.22,1,.36,1);  /* shape morph (needs @property) */
}
.plate:hover { --cut: 30px; }
/* Bonus: oversized ghost numeral floating behind card content */
.plate .ghostnum {
  position: absolute; right: .4rem; bottom: -1.6rem; pointer-events: none;
  font-size: var(--size-0); font-weight: 700; line-height: 1; color: transparent;
  -webkit-text-stroke: 1px color-mix(in srgb, var(--mc) 38%, transparent); opacity: .55;
}"""},
    "cut-corner-button": {"cat": "shape",
        "tags": ["button", "cut-corner", "anti-pill", "cta", "technical"],
        "desc": "Sharp cut-corner CTA — replaces the default 999px pill button "
                "(the other generic-AI tell). Uppercase display type, clipped "
                "corners, drop-shadow depth.",
        "code": """.btn {
  display: inline-block; padding: .75rem 1.7rem; border: none; border-radius: 0;
  font-weight: 600; font-size: var(--size-sm); letter-spacing: .08em; text-transform: uppercase;
  background: var(--surface, transparent); background-image: var(--sheen, none);
  color: inherit;
  clip-path: polygon(14px 0, 100% 0, 100% calc(100% - 14px),
                     calc(100% - 14px) 100%, 0 100%, 0 14px);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--text) 30%, transparent),
              inset 0 1px 0 rgba(255,255,255,.2);
  filter: drop-shadow(0 3px 6px rgba(0,0,0,.4));
  transition: transform .2s, filter .2s; cursor: pointer;
}
.btn:hover { transform: translateY(-2px); }
.btn-accent { background: var(--accent, #2b8fd6); background-image: var(--sheen, none);
              color: var(--bg, #06121f); }"""},
    "editorial-float": {"cat": "layout",
        "tags": ["boxless", "floating-text", "editorial", "narrative", "no-card",
                 "anti-bubble"],
        "desc": "Boxless floating text section — a glowing spine rule + ghost "
                "stroke-word backdrop + a larger lede paragraph instead of "
                "wrapping prose in yet another rounded card. Use for manifesto/"
                "about/narrative sections, especially near the top of the page.",
        "code": """.flow { position: relative; max-width: 760px; margin: 0 auto; padding-left: 2.2rem; }
.flow::before {            /* glowing spine instead of a box */
  content: ""; position: absolute; left: 0; top: .4rem; bottom: .4rem; width: 2px;
  background: linear-gradient(180deg, var(--accent), var(--accent2) 55%, transparent);
  box-shadow: 0 0 calc(14px * var(--gloss, 1)) var(--accent);
}
.flow::after {             /* ghost stroke word floating behind — set per section */
  content: "MINDSET"; position: absolute; z-index: -1; right: -14rem; top: -3.2rem;
  font-weight: 700; font-size: clamp(6rem, 16vw, 11rem); letter-spacing: .04em;
  color: transparent;
  -webkit-text-stroke: 1px color-mix(in srgb, var(--text) 13%, transparent);
  pointer-events: none; user-select: none;
}
.flow p { max-width: 62ch; }
.flow p:first-of-type {    /* the lede — bigger, brighter */
  font-size: 1.28rem; line-height: 1.55; font-weight: 500;
}
/* parent section needs overflow: hidden so the ghost word doesn't cause scroll */"""},
}

# --------------------------------------------------------------------------- #
#  Creative coding — beyond-CSS design recipes (GLSL shaders, WebGL/Three.js,
#  Lottie, JS motion, generative art, physics). `lib` = the vendored offline
#  file under libraries/ (downloaded by _download_creative.sh). Paste-ready.
# --------------------------------------------------------------------------- #

CREATIVE: dict[str, dict] = {
    "shader-gradient-bg": {"cat": "shader", "lib": "(none — raw WebGL)",
        "tags": ["glsl", "shader", "webgl", "background", "animated"],
        "desc": "Full-screen animated GLSL fragment-shader background (GPU). Swap "
                "the fragment for aurora/plasma/noise — this is the un-templatey "
                "hero backdrop CSS can't do.",
        "code": """<canvas id="glcanvas" style="position:fixed;inset:0;z-index:-1"></canvas>
<script type="x-shader/x-fragment" id="frag">
precision highp float;
uniform vec2 u_res; uniform float u_time;
void main(){
  vec2 uv = gl_FragCoord.xy / u_res;
  float t = u_time * 0.25;
  vec3 col = 0.5 + 0.5 * cos(t + uv.xyx * 3.0 + vec3(0.0, 2.0, 4.0));
  col = mix(vec3(0.05,0.01,0.12), col, smoothstep(0.0, 1.0, uv.y));
  gl_FragColor = vec4(col, 1.0);
}
</script>
<script>
const c = document.getElementById('glcanvas'), gl = c.getContext('webgl');
const rs = () => { c.width = innerWidth; c.height = innerHeight; };
rs(); addEventListener('resize', rs);
const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; };
const p = gl.createProgram();
gl.attachShader(p, sh(gl.VERTEX_SHADER, 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}'));
gl.attachShader(p, sh(gl.FRAGMENT_SHADER, document.getElementById('frag').textContent));
gl.linkProgram(p); gl.useProgram(p);
const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,3,-1,-1,3]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(p, 'p'); gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
const uR = gl.getUniformLocation(p,'u_res'), uT = gl.getUniformLocation(p,'u_time');
(function loop(t){ gl.uniform2f(uR,c.width,c.height); gl.uniform1f(uT,t*0.001);
  gl.drawArrays(gl.TRIANGLES,0,3); requestAnimationFrame(loop); })(0);
</script>"""},
    "three-hero": {"cat": "3d", "lib": "three.min.js",
        "tags": ["three", "webgl", "3d", "hero", "material"],
        "desc": "Three.js hero: a faceted metallic solid with real lighting. Swap "
                "geometry/material for glass, torus knots, etc.",
        "code": """<canvas id="c" style="position:fixed;inset:0;z-index:-1"></canvas>
<script src="libraries/three.min.js"></script>
<script>
const rn = new THREE.WebGLRenderer({ canvas: c, antialias: true, alpha: true });
rn.setSize(innerWidth, innerHeight);
const sc = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(60, innerWidth/innerHeight, .1, 100); cam.position.z = 4;
const mesh = new THREE.Mesh(
  new THREE.IcosahedronGeometry(1.3, 0),
  new THREE.MeshStandardMaterial({ color: 0x2b8fd6, roughness: .2, metalness: .6, flatShading: true }));
sc.add(mesh, new THREE.AmbientLight(0xffffff, .4));
const l = new THREE.DirectionalLight(0x96cd6e, 1.4); l.position.set(3,3,3); sc.add(l);
addEventListener('resize', () => { cam.aspect = innerWidth/innerHeight; cam.updateProjectionMatrix(); rn.setSize(innerWidth, innerHeight); });
(function loop(){ mesh.rotation.x += .004; mesh.rotation.y += .006; rn.render(sc, cam); requestAnimationFrame(loop); })();
</script>"""},
    "three-particles": {"cat": "3d", "lib": "three.min.js",
        "tags": ["three", "particles", "points", "3d", "background"],
        "desc": "Three.js drifting 3D particle field (Points).",
        "code": """<canvas id="c" style="position:fixed;inset:0;z-index:-1;background:#0d0221"></canvas>
<script src="libraries/three.min.js"></script>
<script>
const rn = new THREE.WebGLRenderer({ canvas: c }); rn.setSize(innerWidth, innerHeight);
const sc = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(70, innerWidth/innerHeight, .1, 100); cam.position.z = 6;
const n = 1500, pos = new Float32Array(n*3);
for (let i=0;i<n*3;i++) pos[i] = (Math.random()-.5)*14;
const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos,3));
const pts = new THREE.Points(g, new THREE.PointsMaterial({ color: 0x05d9e8, size: .04 }));
sc.add(pts);
(function loop(){ pts.rotation.y += .0015; pts.rotation.x += .0008; rn.render(sc, cam); requestAnimationFrame(loop); })();
</script>"""},
    "lottie-player": {"cat": "motion", "lib": "lottie.min.js",
        "tags": ["lottie", "animation", "vector", "json", "designer"],
        "desc": "Play a designer-made After Effects animation (Lottie JSON) — pro "
                "motion for near-zero effort. Grab .json files from lottiefiles.com.",
        "code": """<div id="lottie" style="width:320px;height:320px"></div>
<script src="libraries/lottie.min.js"></script>
<script>
lottie.loadAnimation({
  container: document.getElementById('lottie'),
  renderer: 'svg', loop: true, autoplay: true,
  path: 'animation.json',        // your Lottie file
});
</script>"""},
    "anime-timeline": {"cat": "motion", "lib": "anime.min.js",
        "tags": ["anime", "timeline", "stagger", "sequence"],
        "desc": "Anime.js timeline with staggered entrance — sequencing CSS can't do.",
        "code": """<script src="libraries/anime.min.js"></script>
<script>
anime.timeline({ easing: 'easeOutExpo', duration: 700 })
  .add({ targets: '.box', translateY: [40, 0], opacity: [0, 1],
         delay: anime.stagger(80) })
  .add({ targets: '.title', scale: [.9, 1], opacity: [0, 1] }, '-=400');
</script>"""},
    "motion-spring": {"cat": "motion", "lib": "motion.min.js",
        "tags": ["motion-one", "spring", "physics", "animate"],
        "desc": "Motion One spring physics — natural, bouncy entrances (tiny lib).",
        "code": """<script src="libraries/motion.min.js"></script>
<script>
const { animate, spring } = Motion;
animate('.card', { y: [40, 0], opacity: [0, 1] },
  { delay: 0.1, easing: spring({ stiffness: 200, damping: 18 }) });
</script>"""},
    "svg-line-draw": {"cat": "motion", "lib": "anime.min.js",
        "tags": ["svg", "line-draw", "stroke", "reveal"],
        "desc": "Self-drawing SVG lines/logos (animate stroke) — signature intro move.",
        "code": """<!-- path.draw { fill:none; stroke:#05d9e8; stroke-width:2; } -->
<script src="libraries/anime.min.js"></script>
<script>
anime({
  targets: 'path.draw',
  strokeDashoffset: [anime.setDashoffset, 0],
  easing: 'easeInOutSine', duration: 1600, delay: (el, i) => i * 250,
});
</script>"""},
    "p5-flow-field": {"cat": "generative", "lib": "p5.min.js",
        "tags": ["p5", "generative", "flow-field", "noise", "particles"],
        "desc": "Generative flow-field background (Perlin-noise particle streams) — "
                "endlessly unique, alive.",
        "code": """<script src="libraries/p5.min.js"></script>
<script>
let ps = [];
function setup(){ createCanvas(windowWidth, windowHeight); background(13,2,33);
  for (let i=0;i<900;i++) ps.push(createVector(random(width), random(height)));
  stroke(43,143,214,22); }
function draw(){ for (const p of ps){
  const a = noise(p.x*0.002, p.y*0.002, frameCount*0.003) * TAU * 2;
  const nx = p.x + cos(a), ny = p.y + sin(a);
  line(p.x, p.y, nx, ny); p.set(nx, ny);
  if (p.x<0||p.x>width||p.y<0||p.y>height) p.set(random(width), random(height)); } }
function windowResized(){ resizeCanvas(windowWidth, windowHeight); }
</script>"""},
    "rough-sketch": {"cat": "generative", "lib": "rough.js",
        "tags": ["rough", "hand-drawn", "sketch", "illustration", "anti-generic"],
        "desc": "Hand-drawn / sketchy shapes (Rough.js) — the literal opposite of "
                "clean AI-generic. Great for playful, editorial, or zine looks.",
        "code": """<canvas id="rc" width="440" height="300"></canvas>
<script src="libraries/rough.js"></script>
<script>
const rc = rough.canvas(document.getElementById('rc'));
rc.rectangle(20, 20, 180, 110, { fill: '#2b8fd6', fillStyle: 'hachure', roughness: 2 });
rc.circle(320, 120, 130, { stroke: '#ff2a6d', strokeWidth: 2, roughness: 1.6 });
rc.line(20, 200, 420, 240, { stroke: '#96cd6e', roughness: 2.5 });
</script>"""},
    "matter-physics": {"cat": "generative", "lib": "matter.min.js",
        "tags": ["matter", "physics", "interactive", "drag", "toy"],
        "desc": "Draggable 2D physics playground (Matter.js) — bouncy, tactile UI toys.",
        "code": """<div id="world"></div>
<script src="libraries/matter.min.js"></script>
<script>
const { Engine, Render, Runner, Bodies, Composite, Mouse, MouseConstraint } = Matter;
const e = Engine.create();
const r = Render.create({ element: document.getElementById('world'), engine: e,
  options: { width: 600, height: 400, wireframes: false, background: '#0d0221' } });
const ground = Bodies.rectangle(300, 395, 600, 20, { isStatic: true });
const balls = Array.from({ length: 12 }, (_, i) =>
  Bodies.circle(80 + i*40, 40, 18, { restitution: .7, render: { fillStyle: '#05d9e8' } }));
Composite.add(e.world, [ground, ...balls,
  MouseConstraint.create(e, { mouse: Mouse.create(r.canvas) })]);
Render.run(r); Runner.run(Runner.create(), e);
</script>"""},

    # ---- Color science & tokens (programmatic palettes) ------------------ #
    "chroma-palette": {"cat": "color", "lib": "chroma.min.js",
        "tags": ["chroma", "palette", "ramp", "scale", "generate"],
        "desc": "Generate a full perceptual color ramp from a few seed colors "
                "(bezier + corrected lightness) instead of hand-picking every stop.",
        "code": """<script src="libraries/chroma.min.js"></script>
<script>
// smooth, perceptually-even 9-stop ramp between brand colors:
const ramp = chroma.bezier(['#2b8fd6', '#b967ff', '#ff2a6d'])
  .scale().correctLightness().colors(9);
// 5 tints + 5 shades from ONE color:
const base = chroma('#2b8fd6');
const tints  = [.15,.3,.5,.7,.85].map(t => chroma.mix('#fff', base, t).hex());
const shades = [.15,.3,.5,.7,.85].map(t => chroma.mix('#000', base, t).hex());
</script>"""},
    "chroma-contrast": {"cat": "color", "lib": "chroma.min.js",
        "tags": ["chroma", "contrast", "wcag", "a11y", "readable"],
        "desc": "Pick guaranteed-readable text colors and enforce WCAG AA contrast "
                "programmatically — no more failing color combos.",
        "code": """<script src="libraries/chroma.min.js"></script>
<script>
// best readable text (black/white) for any background:
const onColor = bg => chroma.contrast(bg, 'white') >= 4.5 ? '#fff' : '#111';
// darken a foreground until it passes AA against a bg:
function ensureAA(fg, bg, min = 4.5) {
  let c = chroma(fg);
  while (chroma.contrast(c, bg) < min && c.luminance() > 0) c = c.darken(0.1);
  return c.hex();
}
</script>"""},
    "chroma-data-scale": {"cat": "color", "lib": "chroma.min.js",
        "tags": ["chroma", "data-viz", "scale", "heatmap", "gradient"],
        "desc": "Map data values to colors with a perceptual (lab) scale — proper "
                "heatmaps/choropleths, not a rainbow.",
        "code": """<script src="libraries/chroma.min.js"></script>
<script>
const scale = chroma.scale(['#f8fafc', '#2b8fd6', '#0b3c5d'])
  .mode('lab').domain([0, 100]);
const colorFor = v => scale(v).hex();   // v in 0..100
// diverging scale (e.g. -100..100):
const diverging = chroma.scale(['#ff2a6d', '#f8fafc', '#05d9e8']).mode('lab').domain([-100, 0, 100]);
</script>"""},
    "color-harmonies": {"cat": "color", "lib": "chroma.min.js",
        "tags": ["chroma", "harmony", "complementary", "triadic", "analogous"],
        "desc": "Derive complementary / triadic / analogous palettes from one hue.",
        "code": """<script src="libraries/chroma.min.js"></script>
<script>
const base = chroma('#2b8fd6'), h = base.get('hsl.h');
const rot = d => base.set('hsl.h', (h + d + 360) % 360).hex();
const complementary = rot(180);
const triadic  = [0, 120, 240].map(rot);
const analogous = [-30, 0, 30].map(rot);
const splitComp = [0, 150, 210].map(rot);
</script>"""},
    "open-props-use": {"cat": "tokens", "lib": "open-props.min.css",
        "tags": ["open-props", "tokens", "css-variables", "shadows", "easings"],
        "desc": "Use Open Props — a huge ready set of CSS variables (shadows, "
                "easings, gradients, sizes) so you never hand-tune those again.",
        "code": """<link rel="stylesheet" href="libraries/open-props.min.css">
<style>
.card {
  border-radius: var(--radius-3);
  box-shadow: var(--shadow-4);
  background: var(--gradient-8);          /* 30+ ready gradients */
  transition: transform 0.4s var(--ease-elastic-3);
  padding: var(--size-4);
}
.card:hover { transform: scale(1.03); }
</style>"""},
    "style-dictionary-tokens": {"cat": "tokens", "lib": "(Node: style-dictionary)",
        "tags": ["style-dictionary", "design-tokens", "build", "multi-platform"],
        "desc": "Single source of design tokens (JSON) → build to CSS vars / JS / "
                "iOS / Android. The pro way to keep one theme across platforms.",
        "code": """// tokens.json
{ "color": { "brand": { "value": "#2b8fd6" }, "text": { "value": "#0b3c5d" } },
  "space": { "sm": { "value": "8px" }, "md": { "value": "16px" } } }

// config.json   ->   npx style-dictionary build
{ "source": ["tokens.json"],
  "platforms": { "css": { "transformGroup": "css", "buildPath": "build/",
    "files": [{ "destination": "tokens.css", "format": "css/variables" }] } } }"""},
}

# --------------------------------------------------------------------------- #
#  ASCII art  (static text art for CLI tools — banners, mascots, dividers).
#  For dynamic block-text banners use the `cliart` module (cliart.banner).
# --------------------------------------------------------------------------- #

ASCII_ART: dict[str, dict] = {
    "robot": {"tags": ["mascot", "robot", "cute"], "desc": "Little robot mascot.",
              "art": r"""
     [^_^]
    /|___|\
     d| |b
    """},
    "ultra-bot": {"tags": ["mascot", "robot", "monitor", "logo", "frutiger"],
                  "desc": "Detailed glossy Ultra-PC monitor-bot logo (neofetch-style).",
                  "art": """       ╭◦───────────────◦╮
       │ ╭─────────────╮ │
       │ │  ●       ●  │ │
       │ │      ▿      │ │
       │ │  ╲       ╱  │ │
       │ │   ╰─────╯   │ │
       │ ╰─────────────╯ │
       ╰───────┬┬────────╯
          ╭────┴┴────╮
          ╰──────────╯"""},
    "cat": {"tags": ["mascot", "cat", "cute"], "desc": "Sleeping cat.",
            "art": r"""
    |\---/|
    | o_o |
     \_^_/
    """},
    "computer": {"tags": ["pc", "computer", "logo"], "desc": "Desktop computer.",
                 "art": r"""
     ________
    |  ____  |
    | |ULTRA| |
    | |__PC_| |
    |________|
    \________/
    """},
    "rocket": {"tags": ["rocket", "launch", "space"], "desc": "Rocket, for launches.",
               "art": r"""
        /\
       /  \
      |ULT |
      |PC  |
     /|    |\
    /_|____|_\
       /\/\
      /_/\_\
    """},
    "trophy": {"tags": ["trophy", "win", "success"], "desc": "Trophy, for PASS/success.",
               "art": r"""
     ___________
    '._==_==_=_.'
    .-\:      /-.
   | (|:.     |) |
    '-|:.     |-'
      \::.    /
       '::. .'
         ) (
       _.' '._
      '-------'
    """},
    "divider-stars": {"tags": ["divider", "stars"], "desc": "Star divider line.",
                      "art": r"* · * · * · * · * · * · * · * · * · * · * · * · *"},
    "divider-wave": {"tags": ["divider", "wave"], "desc": "Wave divider line.",
                     "art": r"~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~^~"},
    "arrow-banner": {"tags": ["divider", "arrows", "header"], "desc": "Arrow header rule.",
                     "art": r">>=====================[ ULTRA-PC ]=====================>>"},
}

# --------------------------------------------------------------------------- #
#  Native / desktop UI recipes — the vault for tkinter/PIL apps (NOT web). CSS
#  and SVG don't render in native GUIs; these use `ultrapc/nativeui.py`, a
#  self-contained, style-aware PIL depth toolkit (glass cards, gel buttons,
#  header bars, animated splash). Same styles as the web vault.
# --------------------------------------------------------------------------- #

NATIVE: dict[str, dict] = {
    "themed-window": {"tags": ["window", "skeleton", "tkinter", "app"],
        "desc": "A complete themed desktop window (header + glass card + gel "
                "button + landing splash), style-swappable.",
        "code": """import tkinter as tk
from ultrapc import nativeui as nui      # self-contained; copy this file into your project

STYLE = "frutiger-aero"                   # or cyberpunk, pastel, mono, nordic, ...
t = nui.tokens(STYLE)

root = tk.Tk(); root.geometry("860x600"); root.configure(bg=t["bg"])
bg = tk.Label(root, bd=0); bg.place(x=0, y=0, relwidth=1, relheight=1)
_scene = nui.ImageTk.PhotoImage(nui.scene(860, 600, STYLE)); bg.configure(image=_scene)

hdr = nui.HeaderBar(root, style=STYLE); hdr.pack(fill="x")
card = nui.Card(root, style=STYLE, accent=(nui._rgb(t["accent2"]), nui._rgb(t["accent"])))
card.pack(fill="both", expand=True, padx=24, pady=20)
tk.Label(card.body, text="Hello", bg=t["surface"], fg=t["text"],
         font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=16)
nui.GelButton(card.body, "Go", lambda: None, style=STYLE, bg=t["surface"]).pack(padx=16)

root.after(150, lambda: nui.run_splash(root, on_done=lambda: None,
                                       title="My App", subtitle="offline", style=STYLE))
root.mainloop()"""},
    "glass-card": {"tags": ["card", "glass", "depth", "shadow", "panel"],
        "desc": "Glass panel with drop shadow + gradient surface + sheen. Pack "
                "content into `card.body`.",
        "code": """from ultrapc import nativeui as nui
card = nui.Card(parent, style="frutiger-aero", radius=18, pad=14,
                accent=(nui._rgb("#96cd6e"), nui._rgb("#2b8fd6")))  # accent optional
card.pack(fill="both", expand=True, padx=20, pady=16)
# put widgets inside card.body (its bg matches the style surface):
tk.Label(card.body, text="…", bg=nui.tokens("frutiger-aero")["surface"]).pack()"""},
    "gel-button": {"tags": ["button", "glossy", "gel", "aqua"],
        "desc": "Filled action button with profile-specific material, corners, typography and enabled states.",
        "code": """from ultrapc import nativeui as nui
btn = nui.GelButton(parent, "Ask ▸", on_click, width=120, height=44,
                    style="frutiger-aero")
btn.pack()
btn.set_text("…"); btn.set_enabled(False)   # while busy"""},
    "header-bar": {"tags": ["header", "title-bar", "glossy"],
        "desc": "Profile-aware title bar: matte for flat styles, polished where allowed, bubbles for Aero.",
        "code": """from ultrapc import nativeui as nui
hdr = nui.HeaderBar(root, height=56, style="cyberpunk")
hdr.pack(fill="x", side="top")
hdr.bind("<Configure>", lambda e: (hdr._redraw(e),
    hdr.create_text(20, 28, anchor="w", text="My App", fill="white",
                    font=("Segoe UI", 15, "bold"))), add="+")"""},
    "splash": {"tags": ["splash", "landing", "loading", "animation"],
        "desc": "Animated landing overlay: glass title card + gradient loading "
                "bar + rising bubbles, then reveals the app.",
        "code": """from ultrapc import nativeui as nui
# after building your window, before mainloop:
root.after(150, lambda: nui.run_splash(
    root, on_done=lambda: entry.focus_set(),
    title="My App", subtitle="offline · local", style="frutiger-aero"))
root.mainloop()"""},
    "style-swap": {"tags": ["theme", "style", "tokens", "recolor"],
        "desc": "Re-theme the whole native UI by changing one string — every "
                "generator reads the style's tokens.",
        "code": """from ultrapc import nativeui as nui
# styles: frutiger-aero · cyberpunk · golden-archive · pastel · mono · nordic · …
for style in ("frutiger-aero", "cyberpunk", "golden-archive"):
    nui.preview(style, f"look-{style}.png")   # static PNG look-preview, no GUI
# in a live app just pass style= to Card / GelButton / HeaderBar / run_splash"""},
    "textures": {"tags": ["texture", "backdrop", "background", "surface", "grain"],
        "desc": "Ten themed backdrop textures — grain, brushed metal, carbon "
                "weave, CRT scanlines, halftone, diagonal stripes, mesh "
                "gradient, starfield, paper — one dispatcher, any style.",
        "code": """from ultrapc import nativeui as nui
# kinds: nui.TEXTURES = grain brushed carbon scanlines halftone stripes mesh starfield paper
img = nui.texture("scanlines", 900, 620, "cyberpunk")
img = nui.vignette(img, 0.3)                      # optional edge-darken finisher
bg = nui.ImageTk.PhotoImage(img)
tk.Label(root, image=bg, bd=0).place(x=0, y=0)    # keep the reference!"""},
    "starfield": {"tags": ["space", "stars", "nebula", "backdrop", "archive"],
        "desc": "Deep-space backdrop (as shipped in the Ultra Archive): "
                "accent-tinted nebula + glowing stars, themed by style.",
        "code": """from ultrapc import nativeui as nui
space = nui.starfield(1200, 780, "golden-archive")   # or cyberpunk, nordic…
# tile two of these and scroll them slowly for a parallax hall"""},
    "scanlines-crt": {"tags": ["crt", "retro", "terminal", "hud", "scanlines"],
        "desc": "CRT scanlines + phosphor glow — terminals, HUDs, retro-tech "
                "panels.",
        "code": """from ultrapc import nativeui as nui
crt = nui.scanlines(860, 560, "cyberpunk")   # gap=3 by default"""},
    "brushed-metal": {"tags": ["metal", "brushed", "industrial", "texture"],
        "desc": "Brushed-metal panel: horizontal streak noise + soft sheen.",
        "code": """from ultrapc import nativeui as nui
panel = nui.brushed(600, 220, "mono")   # works in any style's surface tones"""},
    "mesh-gradient": {"tags": ["mesh", "blob", "hero", "gradient", "backdrop"],
        "desc": "Multi-point mesh gradient (the trendy blurry-blob hero), drawn "
                "from the style's accent family automatically.",
        "code": """from ultrapc import nativeui as nui
hero = nui.mesh(1000, 620, "vaporwave", seed=5)   # vary seed for new layouts"""},
    "neon-button": {"tags": ["button", "neon", "glow", "outline", "dark"],
        "desc": "Outline-glow button (hover brightens the halo) — the dark-"
                "style counterpart to the gel button.",
        "code": """from ultrapc import nativeui as nui
nui.NeonButton(parent, "RUN", on_click, width=140, height=42,
               style="cyberpunk").pack()"""},
    "progress-bar": {"tags": ["progress", "loading", "bar", "gradient"],
        "desc": "Profile-aware progress bar; bounded .set(0..1), visible small values, optional gloss.",
        "code": """from ultrapc import nativeui as nui
bar = nui.ProgressBar(parent, width=280, height=14, style="frutiger-aero")
bar.pack(); bar.set(0.66)"""},
    "toggle-switch": {"tags": ["toggle", "switch", "checkbox", "setting"],
        "desc": "Keyboard-accessible on/off switch with the profile's material and corner treatment.",
        "code": """from ultrapc import nativeui as nui
sw = nui.Toggle(parent, on=True, command=lambda on: print(on),
                style="frutiger-aero")
sw.pack()"""},
    "badge-chip": {"tags": ["badge", "chip", "pill", "tag", "label"],
        "desc": "Pill badges/chips in four kinds: accent, accent2, outline, "
                "surface.",
        "code": """from ultrapc import nativeui as nui
for kind in ("accent", "accent2", "outline", "surface"):
    nui.Chip(parent, "beta", style="nordic", kind=kind).pack(side="left", padx=4)"""},
    "status-dot": {"tags": ["status", "indicator", "light", "glow", "health"],
        "desc": "Glowing status light: ok / warn / err / off — with "
                ".set_state() for live dashboards.",
        "code": """from ultrapc import nativeui as nui
dot = nui.StatusDot(parent, "ok", style="frutiger-aero"); dot.pack()
dot.set_state("warn")   # ok=accent2 · warn=amber · err=red · off=muted"""},
    "plaque": {"tags": ["plaque", "caption", "museum", "engraved", "archive"],
        "desc": "Engraved museum plaque strip (born in the Ultra Archive) — "
                "dark surface, accent hairline; put caption text on top.",
        "code": """from ultrapc import nativeui as nui
img = nui.plaque(340, 66, "golden-archive")
# draw/pack your caption text over it (title / catalog line / source)"""},
    "contrast-tools": {"tags": ["contrast", "wcag", "accessibility", "readable",
                                "a11y"],
        "desc": "WCAG contrast math for native UIs: measure ratios, pick "
                "readable ink, auto-fix a color until it passes — check, "
                "don't guess.",
        "code": """from ultrapc import nativeui as nui
nui.contrast("#77809a", "#04070f")        # -> ratio 1..21 (AA body 4.5, AAA 7)
nui.on_color("#d9b453")                    # -> '#000000' or '#ffffff' (best ink)
safe = nui.ensure_contrast("#8a70ff", "#150e2e", ratio=4.5)  # nudged until it passes
# every vault style is smoke-tested to: text/bg >= 4.5, accent/bg + muted/bg >= 3.0"""},
    "divider-ramp": {"tags": ["divider", "hairline", "ramp", "color", "harmony"],
        "desc": "Fading accent divider + color utilities: ramp() tint→shade "
                "scales and harmony() complement/analogous/triadic — stop "
                "hand-picking 'a lighter accent'.",
        "code": """from ultrapc import nativeui as nui
nui.Divider(parent, width=320, style="jewel").pack(fill="x", pady=8)
shades = nui.ramp("#d4af37", 7)          # ['#f6ecd1', …, '#241d09']
mates = nui.harmony("#d4af37")           # complement / analogous / triadic"""},
}


# --------------------------------------------------------------------------- #
#  DESIGN PROFILES — full archetype collections. A profile bundles everything
#  the vault knows that belongs to one design language: tokens (STYLES),
#  palette, fonts (incl. wave-3 display faces), textures + gloss treatment
#  (nativeui), signature SHAPES, matching patterns/techniques/gradients, and
#  researched do/don't rules. `assets profiles`, `assets profile <id>`.
#  Grounded in design-education sources (CARI/aesthetics wikis, Envato, deco
#  typography guides) — see each profile's `vibe`.
# --------------------------------------------------------------------------- #

PROFILES: dict[str, dict] = {
    "avant-basic": {
        "label": "Avant Basic", "style": "avant-basic", "palette": "avant-play",
        "vibe": "2019-22 Instagram/Shein-era maximalism reviving Memphis and "
                "the 60s-70s: warped checkerboards, squiggles, solid daisies, "
                "diamond stars and arch 'window' shapes in bright retro "
                "pastels + hot pink and cobalt. Playful, clashing, flat.",
        "origins": "A direct revolt against 2010s millennial minimalism (beige "
                "rooms, thin sans-serifs, tasteful sameness). It resurrects "
                "the Memphis Group (Sottsass, 1981) and 60s-70s psychedelia "
                "through e-commerce and Instagram interiors — wavy mirrors, "
                "checkered rugs, squiggle candles — where being photographed "
                "well matters more than being restrained.",
        "composition": "Dense and busy on purpose: every zone hosts a motif, "
                "elements overlap like stickers, and the same shape repeats "
                "at several scales. Grids exist to be warped — checkerboards "
                "bend and perspective-melt. Balance is achieved by color "
                "weight, not symmetry; nothing is centered out of politeness.",
        "color": "Bright retro pastels held at near-equal saturation — lilac, "
                "butter yellow, tangerine, lime, cobalt, hot pink — with no "
                "neutral doing rescue work. Adjacent colors are chosen to "
                "vibrate (pink beside red, lime beside lilac). Fields meet at "
                "hard edges; a gradient would be an apology.",
        "type": "Chubby and bulbous: 70s bubble-serif display (Cooper Black "
                "energy — Shrikhand) set wide and generous, often bending "
                "along an arch or wave. Body text stays in a simple rounded "
                "sans so the display face can be the loudest object in the "
                "room.",
        "materiality": "Flat matte, like screen-printed vinyl or glazed "
                "ceramic. In objects: lacquered wavy mirrors, tufted rugs, "
                "checkered tile. There is no gloss, no drop shadow, no depth "
                "— dimension comes from overlap and outline, never light.",
        "motion": "Cartoon physics: squash-and-stretch, wobble, wiggle. "
                "Squiggles undulate, daisies spin lazily, stickers land with "
                "a bounce and a few degrees of rotation jitter. Easing is "
                "playful overshoot, never linear.",
        "imagery": "Flat vector illustration over photography. When photos "
                "appear they are staged still-lifes on colored seamless "
                "backdrops — objects arranged like candy, lit flat, no "
                "moody shadows.",
        "proportion": "Chunky everything: stroke weights at least 6% of the "
                "element's width (marker-line minimum), radii pill-round, "
                "motifs repeated at three scales stepping roughly 2.5x. "
                "Spacing runs tight — about half of what a minimalist would "
                "leave — because emptiness reads as timidity here.",
        "hierarchy": "Motif > color clash > display type > layout. The "
                "pattern IS the message; body copy is a polite guest who "
                "gets a clean white card to stand on and no more.",
        "canon": "Study: the Memphis Group's Carlton bookcase (Sottsass, "
                "1981), Camille Walala's murals, Lisa Says Gah lookbooks, "
                "the c. 2021 wavy-mirror/checkered-rug Instagram interior, "
                "squiggle candles and Poster Club prints.",
        "adaptation": "Pattern never sits behind body copy — text floats on "
                "cream/white cards above the chaos. Hot pink fails contrast "
                "on lilac, so running text falls back to deep plum. Dark "
                "mode: swap the cream field for deep plum and keep motifs at "
                "FULL saturation — it becomes avant-after-dark, never gray.",
        "era": "c. 2019–2023 — peak Instagram/TikTok interiors and DTC e-commerce",
        "light": "Flat, even, shadowless — lit like product photography on a "
                "colored seamless. Color does all the modeling; light is not "
                "allowed to editorialize. In rooms: bright daylight bouncing "
                "off lacquered color, no moody corners anywhere.",
        "voice": "Playful lowercase, pun-forward, chatty — 'hi, we make cute "
                "stuff.' Copy sounds like a friend captioning a photo, never "
                "a brand issuing a statement. Emoji-adjacent energy without "
                "leaning on emoji; formality is the only banned word.",
        "sound": "Bubbly plucks, marimba pop, bedroom indie-pop; interface "
                "blips as rounded as the shapes. Nothing aggressive, nothing "
                "epic — the soundtrack of a nice afternoon with snacks.",
        "space": "Creator studios and Gen-Z apartments (the wavy mirror, the "
                "checkered rug, the squiggle candle), DTC packaging, nail "
                "salons, sticker sheets, phone cases, tote bags — anywhere a "
                "photo might be taken of the thing.",
        "kinship": "Direct child of Memphis (1981) and 60s-70s psychedelia; "
                "cousin of vaporwave (shares the nostalgia, rejects the "
                "digital chrome); sworn enemy of millennial minimalism. "
                "Don't confuse with `pastel` — pastel is calm, avant is loud "
                "in pastel's clothing.",
        "moves": ["Warp a checkerboard and put it behind the subject",
                  "Set the title in a bubble serif riding an arch",
                  "Scatter daisies + diamond stars at three different scales",
                  "Pick two clashing pastels and let them touch with a hard edge"],
        "failure": "You've lost it when the palette starts matching "
                "tastefully, when a gradient or soft shadow sneaks in, or "
                "when the type turns thin and elegant — the whole point is "
                "confident, flat, deliberate clash.",
        "fonts": {"display": "Shrikhand", "body": "Fredoka",
                  "files": ["shrikhand-400.woff2", "fredoka-500.woff2"]},
        "textures": ["halftone", "stripes"],
        "gloss": "flat-pop: hard flat fills, zero gel/glass; depth comes from "
                 "overlapping shapes and offset outlines, not shadows",
        "shapes": ["squiggle", "daisy", "checker-wave", "diamond-star",
                   "arch-window"],
        "patterns": ["checkerboard"], "gradients": [],
        "techniques": ["blob-morph", "stroke-text", "pixel-art-shadow"],
        "rules": "DO warp/liquify grids, mismatch colors on purpose, repeat "
                 "one motif big. DON'T add gloss, gradients or drop shadows — "
                 "flatness is the point.",
    },
    "organic-tech": {
        "label": "Organic Tech", "style": "organic-tech",
        "palette": "living-earth",
        "vibe": "Biomorphic + biophilic: shapes that read as cells, water or "
                "pebbles; the 'living earth' palette (sage, moss, clay, sand); "
                "gradients that shift *within* shapes; no harsh corners "
                "anywhere; spring-physics motion. Nature wired to a device.",
        "origins": "Biomorphism (Arp's reliefs, Noguchi's tables) crossed "
                "with biophilic-design research — the finding that organic "
                "pattern measurably calms — arriving in 2020s product design "
                "as wellness tech, solarpunk optimism and the soft rebuttal "
                "to cold techno-minimalism. Nature is the interface metaphor.",
        "composition": "Generous negative space, but soft: content sits in "
                "rounded pools rather than boxes, and cards read as pebbles "
                "or cells scattered in loose organic clusters. The grid is "
                "felt, never seen; boundaries dissolve into the field instead "
                "of ending at a border.",
        "color": "Low-saturation earth — a sage field with moss and clay "
                "used sparingly, the way plants sit in a room. Whites are "
                "warm (bone, oat), never clinical pure white. Contrast is "
                "carried by VALUE, not hue; nothing fluoresces. Gradients "
                "shift gently within a shape, like light through a leaf.",
        "type": "Humanist or geometric-rounded sans with low stroke "
                "contrast, roomy line-height and sentence case — reading "
                "should feel like a calm voice. No all-caps shouting; "
                "emphasis comes from weight and space, not size explosions.",
        "materiality": "Matte ceramic, unglazed clay, frosted glass, linen, "
                "river stone. Grain is fine and organic. Light DIFFUSES "
                "rather than reflects — a frosted glow, never a wet "
                "highlight or chrome edge.",
        "motion": "Spring physics everywhere: elements settle rather than "
                "snap, blobs morph continuously, and idle surfaces breathe "
                "(slow 2-4% scale oscillation). Nothing moves in a straight "
                "line at constant speed — that reads as machine, not "
                "organism.",
        "imagery": "Macro nature — leaf venation, water meniscus, stone "
                "texture — in soft daylight with shallow depth of field. "
                "Products photographed on stone, linen or oak; hands appear "
                "often; screens appear rarely.",
        "proportion": "Radii at least 25% of element height — the pebble "
                "ratio — and clusters arranged in loose golden-ish "
                "asymmetry. Line weights approach zero: separation comes "
                "from ~8% value steps, not strokes. Whitespace holds 40%+ "
                "of the field, and the type scale climbs gently (1.25x), "
                "never leaps.",
        "hierarchy": "Shape language > palette calm > motion feel > type. "
                "If the corners are right, half the work is done; if the "
                "motion springs, the other half follows.",
        "canon": "Study: Noguchi's coffee table, Arp's reliefs, Headspace's "
                "blob era, Calm and Oura's branding, Karim Rashid's "
                "'blobject' years (the Garbo can), and solarpunk concept "
                "art where circuitry grows leaves.",
        "adaptation": "Sage and moss hover near 3:1 — reserve them for "
                "large elements and keep running text in deep loam ink. "
                "Dark mode is a nighttime greenhouse: deep moss field, sage "
                "as the light accent, whites kept warm. Reduced-motion "
                "users get slow crossfades — remove the springs, never the "
                "rounding.",
        "era": "c. 2020–present — wellness tech and post-minimal product design",
        "light": "Diffused daylight through frosted glass: soft shadows with "
                "wide penumbras, golden-hour warmth welcome, hard specular "
                "points banned. Light behaves like it passed through a leaf "
                "or a paper shade on the way in.",
        "voice": "Calm and low-ego, gentle second person — 'take a moment.' "
                "Science softened by nature metaphor; short sentences with "
                "room to breathe. It never urges, never counts down, never "
                "uses an exclamation point.",
        "sound": "Ambient pads, field recordings — water over stone, leaves "
                "— and soft haptic thumps. A notification should sound like "
                "a pebble dropped in a pond, not a bell demanding anything.",
        "space": "Wellness and sleep apps, smart-home objects in oak-and-"
                "linen rooms, spa and skincare branding, sustainable "
                "packaging, biotech that wants to feel kind instead of "
                "clinical.",
        "kinship": "Heir to biomorphism (Arp, Noguchi) and biophilic "
                "architecture; sibling of `pastel` (shares the softness, "
                "trades sugar for earth); natural complement of "
                "`hi-contrast`. Don't confuse with farmhouse-rustic — this "
                "is precise softness, engineered like a lens, not distressed "
                "like a barn door.",
        "moves": ["Replace every rectangle with a pebble or cell blob",
                  "One sage field, one clay accent, warm off-whites — stop there",
                  "Give every element spring-settle motion; let idle things breathe",
                  "Add fine grain so flat fields feel like paper, not pixels"],
        "failure": "Dead the moment a hard corner, hairline border, neon "
                "accent or pure black arrives — or when motion turns linear "
                "and mechanical. If it feels like a lab instead of a "
                "greenhouse, back up.",
        "fonts": {"display": "Sora", "body": "DM Sans",
                  "files": ["sora-600.woff2", "dm-sans-500.woff2"]},
        "textures": ["mesh", "grain", "paper"],
        "gloss": "soft-matte: frosted layers and blurred blob glows; use "
                 "glass-card at low opacity, never wet gel",
        "shapes": ["blob-cell", "pebble-stack", "leaf-vein"],
        "patterns": ["blob", "topographic"],
        "gradients": [],
        "techniques": ["aurora-blur", "gooey", "blob-morph", "elastic-ease",
                       "grain-overlay"],
        "rules": "DO round every corner (radius 20px+), blend layers, animate "
                 "with springs. DON'T use straight lines, hard borders or "
                 "neon — calm is the material.",
    },
    "high-fashion": {
        "label": "High Fashion", "style": "high-fashion",
        "palette": "runway-ivory",
        "vibe": "Editorial luxury: ivory field, ink-black Didone serifs at "
                "huge scale contrast, hairline rules, champagne accents and "
                "aggressive whitespace. The layout behaves like a magazine "
                "spread — photography and type carry everything.",
        "origins": "The 20th-century editorial canon: Vogue and Harper's "
                "Bazaar under Brodovitch ('Astonish me'), Didot/Bodoni "
                "mastheads, 90s minimal luxury branding, runway invitations "
                "printed on paper heavier than the message. Luxury speaks "
                "quietly because it doesn't need to persuade.",
        "composition": "Whitespace is the luxury good — spend it "
                "extravagantly. One dominant element per spread, extreme "
                "scale hierarchy (a 140pt headline against a 9pt caption), "
                "rigid alignment used to stage dramatic asymmetry. Margins "
                "are wide because the content can afford them.",
        "color": "Near-absence: ivory field, ink black, and at most ONE "
                "guest — champagne metal or a single seasonal accent, never "
                "both. Black is the color; everything else is lighting. "
                "Saturation anywhere reads as discount.",
        "type": "Didone display — razor thick/thin contrast — letter-spaced "
                "caps for mastheads, refined serif for body, italic for "
                "whispered captions. Type is allowed to kiss or overlap the "
                "photography; scale contrast does the work decoration "
                "would.",
        "materiality": "Uncoated stock, matte laminate, letterpress bite, "
                "foil applied with restraint. Surfaces are paper, not "
                "screens; there is no digital gloss, bevel or glow — the "
                "only shine permitted arrives by foil or silk.",
        "motion": "Slow and editorial: long crossfades, masked reveals that "
                "behave like a page turning, text that rises a line at a "
                "time. Restraint is confidence; anything bouncy is beneath "
                "it.",
        "imagery": "Photography IS the design — full-bleed portraiture, "
                "controlled studio light or brutal noon sun, styled to the "
                "millimeter. Art direction replaces ornament; if the image "
                "is weak no layout will save the page.",
        "proportion": "Extreme scale ratios — display type 8-12x the body "
                "size, not the timid 2-3x of ordinary hierarchies. "
                "Hairlines stay hairlines (a point at most). Margins claim "
                "15%+ of the page per side; a text column never exceeds "
                "~45 characters. The ornament budget is exactly one.",
        "hierarchy": "Imagery > typography > whitespace > color. Color is "
                "barely on the team — it's allowed to hold the coat while "
                "the photograph and the Didone do the talking.",
        "canon": "Study: Brodovitch's Harper's Bazaar spreads, the Vogue "
                "Didot masthead, Cassandre's YSL monogram, Phoebe Philo-era "
                "Céline lookbooks, Comme des Garçons invitations, any "
                "September-issue cover wall.",
        "adaptation": "Ink on ivory sits near 17:1 — AAA without trying. "
                "Dark mode inverts gracefully to ivory-on-ink (fashion "
                "always loved a black page). Champagne is display-only — "
                "too soft for small text on ivory; spend it on numerals "
                "and rules. Letter-space caps only, never body text.",
        "era": "canon 1930s–90s editorial; evergreen wherever luxury speaks",
        "light": "Two modes, both deliberate: sculpted single-key studio "
                "light, or brutal noon sun with knife-edge shadows. Always "
                "high contrast, never golden-hour cozy — light is casting "
                "judgment, not comfort.",
        "voice": "The declarative whisper: short verdicts without hedging — "
                "'The coat. Nothing else.' French loanwords permitted, "
                "exclamation points never. Copy behaves like it was expensive "
                "to print, because it was.",
        "sound": "Near-silence: room tone, a heel on marble, one held cello "
                "note. If music, spare piano or cold electronica kept low — "
                "the audio equivalent of whitespace.",
        "space": "Mastheads and campaign spreads, lookbooks, boutique "
                "windows, runway invitations, perfume boxes — objects whose "
                "job is to be desired before they are read.",
        "kinship": "Parent of every 'quiet luxury' wave; cousin of "
                "`editorial` (shares the typographic discipline, adds "
                "glamour and cruelty); opposite of `preppy-2000s` (same "
                "money, opposite volume). Don't confuse with `art-deco` — "
                "deco decorates its luxury, fashion abstains from "
                "decoration entirely.",
        "moves": ["One full-bleed image + one Didone headline — nothing else on the page",
                  "Letter-space the caps until they can breathe",
                  "Permit exactly one ornament: a hairline rule with a centered diamond",
                  "Cut every second element; then cut once more"],
        "failure": "It collapses into mall-brand the instant there are two "
                "accent colors, a rounded corner, a gradient, or a crowded "
                "spread. If every element survived the edit, the edit "
                "didn't happen.",
        "fonts": {"display": "Bodoni Moda", "body": "Lora",
                  "files": ["bodoni-moda-700.woff2", "lora-400.woff2"]},
        "textures": ["paper"],
        "gloss": "none: matte paper only; if depth is needed use a 1px ink "
                 "rule or a paper grain, never a shadow stack",
        "shapes": ["hairline-frame", "editorial-rule"],
        "patterns": [], "gradients": [],
        "techniques": ["mask-fade-reveal", "text-line-reveal",
                       "dropcap-initial-letter", "text-balance-wrap"],
        "rules": "DO letter-space caps, mix 12px body with 120px display, "
                 "leave 60% of the page empty. DON'T use more than one accent, "
                 "rounded corners, or any gradient.",
    },
    "skate-culture": {
        "label": "Skate Culture", "style": "skate-culture",
        "palette": "grip-tape",
        "vibe": "Deck art + sticker bombing + zine grunge: asphalt darks under "
                "safety orange and hazard yellow, distressed textures, thick "
                "white sticker outlines, hand-marker and pop display type, "
                "collage energy (Screaming-Hand-era Santa Cruz, Thrasher).",
        "origins": "1970s-90s California skate: Dogtown's spray-can Z, Jim "
                "Phillips' Screaming Hand for Santa Cruz (1985), "
                "Powell-Peralta skull iconography, Thrasher's flaming "
                "masthead, photocopied zines and the sticker toss. Graphics "
                "made to be shredded — they had to read at speed and look "
                "better scratched.",
        "composition": "Collage chaos with one focal scream: a single loud "
                "central graphic, everything else applied like stickers at "
                "random rotations. Edges bleed, registration is deliberately "
                "off, and empty space gets tagged. Neatness is suspicious.",
        "color": "Asphalt black base with safety orange, hazard yellow and "
                "blood red at full saturation — colors layered like "
                "screen-print passes, separated by fat white outlines, never "
                "blended. If two inks touch, it's with a hard trap line, not "
                "a fade.",
        "type": "Loud hand-drawn display — marker, brush, blade — ALL CAPS, "
                "warped to fill whatever shape it's trapped in. Ransom-note "
                "mixing is legal. Legibility loses to attitude on every "
                "close call.",
        "materiality": "Grip-tape grit, xerox noise, scraped ply, spray-"
                "stencil bleed, ripped paper, curb wax. Every surface is "
                "distressed by USE, not by a filter trying to look like "
                "use — wear patterns belong where wear would happen.",
        "motion": "Abrupt punk cuts: jump cuts, frame-skips, shake on "
                "impact, marquees that scroll like a bearing rolling. VHS "
                "artifacts welcome. Smooth easing is for mall brands.",
        "imagery": "High-contrast black-and-white fisheye skate photography, "
                "hand illustration (skulls, hands, flames, eyeballs), "
                "photocopied halftones. Faces sneer; nothing poses.",
        "proportion": "Outlines fat — 4-6% of the graphic's width — with "
                "hard offsets of 4-8px. Applied elements carry 2-8 degrees "
                "of rotation jitter. Display type fills 70%+ of whatever "
                "contains it. Nothing is centered unless it's mocking the "
                "idea of being centered.",
        "hierarchy": "Attitude > central graphic > texture > type > color. "
                "Color is a costume; attitude is the body wearing it. A "
                "technically perfect comp with no snarl is a failed comp.",
        "canon": "Study: Jim Phillips' Screaming Hand (Santa Cruz, 1985), "
                "VCJ's Ripper for Powell-Peralta, the Dogtown cross, "
                "Thrasher's flaming masthead, Toy Machine's devil, "
                "Spitfire's bighead, and any sticker-bombed lamppost.",
        "adaptation": "Distress the display, never the body copy — captions "
                "stay clean on asphalt at AA+. Safety orange on black "
                "clears 7:1; don't stack orange text on yellow stickers. "
                "Light mode is the xerox: near-white paper, black ink, one "
                "red accent — the zine was always light mode.",
        "era": "core 1975–1999; permanent revival cycles ever since",
        "light": "Harsh direct flash (fisheye at dusk), fluorescent parking-"
                "garage flatness, xerox blowout. Light documents, it never "
                "flatters — if the shot looks lit by a professional, reshoot "
                "it with the flash your friend was holding.",
        "voice": "Shouted slang and inside jokes — 'SK8 OR DIE' — loyal, "
                "self-deprecating, allergic to marketing-speak. The copy "
                "sounds hand-lettered even when typed, and it's talking to "
                "the crew, not to a demographic.",
        "sound": "Punk and thrash, lo-fi hip-hop, urethane wheels on "
                "concrete, the ka-chunk of a landed kickflip, tape hiss over "
                "everything. Production polish is treated as a betrayal.",
        "space": "Deck bottoms and grip tape, sticker-bombed rails and "
                "lampposts, zines, shop walls, tour vans, curbs that have "
                "been waxed by three generations.",
        "kinship": "Sibling of punk zines and graffiti; parent of modern "
                "streetwear graphics; cousin of grunge; the mall's other "
                "tribe and sworn opposite of `preppy-2000s`. Don't confuse "
                "with generic 'urban' styling — skate runs on specific "
                "brands, specific spots and in-jokes that gatekeep "
                "themselves.",
        "moves": ["One screaming central graphic; everything else is stickers",
                  "Fat white outline + hard 4px offset shadow on any element that matters",
                  "Rotate every applied element 2–8 degrees — nothing sits straight",
                  "Finish with a grain/xerox pass over the whole composition"],
        "failure": "Instant poser-merch when polish arrives: soft shadows, "
                "gradients, symmetric layouts, corporate-clean type, or "
                "distress applied evenly everywhere like a texture swatch.",
        "fonts": {"display": "Bangers", "accent": "Permanent Marker",
                  "body": "Inter",
                  "files": ["bangers-400.woff2", "permanent-marker-400.woff2",
                            "inter-400.woff2"]},
        "textures": ["grain", "stripes", "carbon"],
        "gloss": "gritty-flat: heavy grain over everything; sticker elements "
                 "get a fat white outline + hard offset shadow (4px 4px 0), "
                 "never a soft blur",
        "shapes": ["burst-sticker", "flame-line", "stencil-arrow"],
        "patterns": ["noise-texture", "diagonal-stripes"], "gradients": [],
        "techniques": ["grain-overlay", "stroke-text", "pixel-art-shadow",
                       "infinite-marquee"],
        "rules": "DO rotate stickers a few degrees, distress edges, clash "
                 "orange on black. DON'T center things neatly or use thin "
                 "elegant type — it should look hand-applied.",
    },
    "mosaic": {
        "label": "Mosaic", "style": "mosaic", "palette": "trencadis",
        "vibe": "Tessellation as a design language: terrazzo chips, Gaudí "
                "trencadís crackle, stained-glass panes with visible grout. "
                "Glazed jewel fragments (teal, terracotta, ochre, moss) on "
                "warm plaster; surfaces are fields of pieces, not solids.",
        "origins": "Five thousand years of putting small pieces together: "
                "Roman and Byzantine tesserae, Islamic zellige geometry, "
                "Venetian terrazzo floors, Gaudí smashing tiles for Park "
                "Güell's trencadís (1900-14), cathedral stained glass — and "
                "the 2018+ terrazzo-print revival that put chips on "
                "everything again. Wholeness built from fragments.",
        "composition": "Surfaces are FIELDS OF PIECES: large forms emerge "
                "from small units, the way a face emerges from tesserae. "
                "Silhouettes stay bold and simple because the interior is "
                "busy. Borders are bands of tiles; the underlying grid is "
                "irregular and handmade, but the overall shape is "
                "architectural.",
        "color": "Glazed jewel fragments — teal, terracotta, ochre, moss — "
                "distributed so no zone monopolizes a hue, on warm plaster/"
                "grout that is a REAL working color, not background. The "
                "cardinal rule: color changes happen BETWEEN pieces, never "
                "within one. A gradient inside a chip breaks the spell.",
        "type": "Inscriptional — engraved romans (Cinzel) that feel chiseled "
                "beside stone, or at display sizes letterforms literally "
                "assembled from tiles. Body text stays a quiet serif; the "
                "surfaces are the ornament, the text is the plaque.",
        "materiality": "Fired glaze, stone chip, grout ridge, cool plaster. "
                "Each piece catches light slightly differently — a subtle "
                "per-fragment variance in tone and sheen is what makes it "
                "read as handmade rather than wallpaper.",
        "motion": "Assembly and settling: pieces arrive staggered and click "
                "into place; transitions shatter and recompose "
                "kaleidoscopically. The rhythm is many small events "
                "composing one large one — never a single smooth sweep.",
        "imagery": "Architectural detail photography — courtyards, fountains, "
                "domes — and macro texture shots where grout lines are "
                "visible. Crafted objects over lifestyle; hands laying "
                "tiles over faces smiling.",
        "proportion": "Chips run 2-6% of the composition's width, smaller "
                "toward edges and detail zones. Grout gaps hold steady at "
                "8-12% of chip size — consistency of gap is what sells the "
                "craft. Borders are one chip-row thick; silhouettes claim "
                "60%+ of the frame so fragmentation never costs legibility.",
        "hierarchy": "Silhouette > fragment rhythm > palette distribution > "
                "grout color > type. If the outline reads from across the "
                "room and the pieces read up close, it's working at both "
                "distances — that's the whole trick.",
        "canon": "Study: San Vitale's mosaics in Ravenna, the zellige of "
                "Fez, Gaudí's serpentine bench at Park Güell, Venetian "
                "palazzo terrazzo, the Palau de la Música ceiling, and the "
                "2018+ terrazzo-print packaging wave.",
        "adaptation": "Text never sits on tesserae — give it a plaster "
                "plaque or a solid pane. Teal and terracotta clear 3:1 on "
                "plaster for large elements; body ink stays near-black. "
                "Dark mode is a night courtyard: charcoal grout, slate "
                "plaster, glazes slightly muted. Reduced motion: the "
                "assemble becomes a crossfade — drop the stagger.",
        "era": "antiquity → Gaudí c. 1900s → terrazzo-print revival 2018+",
        "light": "Raking light that catches grout ridges and glaze edges; "
                "sun through stained glass throwing colored patches on "
                "plaster. Every fragment glints on its own schedule — "
                "uniform studio lighting flattens the craft out of it.",
        "voice": "Artisanal and patient: the copy talks about craft, "
                "provenance and hours — 'cut, placed and grouted by hand.' "
                "Metaphors of many-making-one. It never rushes and never "
                "brags in percentages.",
        "sound": "Ceramic clinks, stone on stone, courtyard reverb, Spanish "
                "guitar or oud. Rhythm built from many small hits — mallets, "
                "handclaps — the percussion equivalent of tesserae.",
        "space": "Courtyards, fountains, floors you photograph your shoes "
                "on; spa and hotel identities, artisan food packaging, "
                "cultural institutions, anywhere craft is the promise.",
        "kinship": "The ancestor tradition behind the terrazzo print trend; "
                "cousin of `jewel` (shares the gem tones, adds "
                "fragmentation); kindred spirit of `organic-tech` (both "
                "handmade-feeling — mosaic hard, organic soft). Don't "
                "confuse with pixel art: pixels obey a grid, tesserae "
                "follow the form.",
        "moves": ["Build one bold silhouette out of many small chips",
                  "Let the grout be a visible, working color — not background",
                  "Border every panel with a tessera band",
                  "Vary each fragment's tone a few percent so it reads handmade"],
        "failure": "Broken by seamless blends, perfectly regular grids, or "
                "grout that matches the tiles — if the pieces stop being "
                "visible as pieces, you've made a gradient with extra "
                "steps.",
        "fonts": {"display": "Cinzel", "body": "Lora",
                  "files": ["cinzel-600.woff2", "lora-400.woff2"]},
        "textures": ["terrazzo", "paper"],
        "gloss": "glazed-tile: a subtle top sheen on chips/panes (like fired "
                 "glaze) — use the glass-card sheen at half strength",
        "shapes": ["terrazzo-chips", "trencadis-pane", "tessera-band"],
        "patterns": ["topographic"], "gradients": [],
        "techniques": ["clip-path-shapes", "duotone", "squircle-corners"],
        "rules": "DO break big surfaces into visible pieces with grout gaps, "
                 "vary fragment sizes. DON'T use seamless gradients — color "
                 "changes happen BETWEEN pieces, not within them.",
    },
    "art-deco": {
        "label": "Art Deco", "style": "art-deco", "palette": "gatsby-gold",
        "vibe": "1920s-40s controlled opulence: black + gold + jewel tones, "
                "graduated sunbursts (rays tighter at the center), stepped "
                "ziggurat frames, fans, chevrons, strict symmetry, and tall "
                "geometric letterforms with uniform strokes.",
        "origins": "Named for the 1925 Paris Exposition des Arts Décoratifs: "
                "machine-age optimism wearing jewelry. Cassandre's travel "
                "posters, the Chrysler Building's crown (1930), Erté's "
                "figures, ocean-liner ballrooms and Gatsby's parties — "
                "geometry, luxury and speed fused into one discipline.",
        "composition": "Strict bilateral symmetry with vertical thrust: "
                "compositions ASCEND in stepped tiers like a ziggurat. "
                "Frames nest within frames; ornament concentrates at borders "
                "and crowns while centers stay calm. Everything either "
                "radiates from a point or climbs toward one.",
        "color": "Black lacquer is the ground and gold is the protagonist. "
                "Exactly one jewel tone guests per composition — emerald OR "
                "sapphire OR ruby, never a chorus. Cream provides the "
                "breathing room. High contrast, zero pastels, no earth "
                "tones — this is a nighttime aesthetic.",
        "type": "Tall, condensed, geometric letterforms with uniform strokes "
                "and high waistlines, set as letter-spaced caps (Poiret One; "
                "Cinzel for engraved moments). Numerals are treated as "
                "jewelry. Nothing bubbly, nothing distressed, nothing "
                "lowercase-casual.",
        "materiality": "Polished brass and gold leaf, black lacquer, "
                "macassar ebony, frosted glass, chrome trim. Surfaces are "
                "hard and reflective but CONTROLLED — an even sheen, never "
                "glitter or sparkle. Metal reads as machined, not molten.",
        "motion": "Mechanical elegance on clockwork timing: rays sweep "
                "outward, elements rise step by step, reveals fan open like "
                "a peacock or a hand of cards. Precise starts and stops — "
                "bounce and overshoot are vulgarities.",
        "imagery": "Stylized streamlined illustration in the Cassandre "
                "manner — simplified planes, dramatic diagonals — or "
                "architectural photography shot looking UP. People appear "
                "as elongated elegant silhouettes, never candid.",
        "proportion": "Strong verticality: display lockups at 2:1 height-to-"
                "width or taller. Stepped frames in odd tier counts (3, 5, "
                "7), each step roughly halving. Sunbursts carry 9-15 rays "
                "with graduated spacing. Borders travel in thick-thin "
                "pairs — a 5px line escorted by a 1px line.",
        "hierarchy": "Symmetry > gold/black contrast > typography > "
                "ornament > the jewel accent. Break the symmetry and "
                "nothing downstream can save you; keep it and even sparse "
                "ornament reads as opulence.",
        "canon": "Study: Cassandre's Normandie poster, the Chrysler "
                "Building's crown, Erté's Symphony in Black, Hildreth "
                "Meière's Radio City plaques, Gatsby title treatments, and "
                "any 1930 cinema marquee photographed at night.",
        "adaptation": "Gold on near-black clears 7:1 — AAA at display "
                "sizes; emerald is for large elements only. Daytime deco "
                "exists: cream field, black geometry, gold accents (think "
                "deco menus and invitations). Never dim gold with opacity — "
                "mix it toward bronze so it stays metal, not ghost.",
        "era": "1925–1940 machine-age zenith; revived for luxury ever since",
        "light": "Warm key light on polished brass — reflections drawn as "
                "controlled lines along edges, never scattered sparkle. "
                "Marquee bulbs, candlelight on lacquer; light forms RAYS "
                "and edges, not pools.",
        "voice": "Title-case proclamations with period confidence — 'The "
                "Future Arrives Nightly.' Formal, theatrical, a little "
                "grand; superlatives are permitted because the symmetry "
                "earned them.",
        "sound": "Big-band brass, a clarinet glissando, champagne fizz, the "
                "chime of a brass elevator. Tempo strict and metronomic — "
                "the music, like the geometry, does not rubato.",
        "space": "Hotel lobbies and theatre marquees, liquor and perfume "
                "packaging, gala invitations, film title sequences, "
                "penthouse bars — places where evening is the native hour.",
        "kinship": "Child of cubism and the machine age; sibling of "
                "`golden-archive` (both gold-on-dark — the archive is "
                "cosmic and quiet, deco is urban and theatrical); opposite "
                "of `organic-tech` (geometry vs biology). Don't confuse "
                "with art nouveau — nouveau curves like a vine, deco steps "
                "like a skyscraper.",
        "moves": ["Frame the subject in a symmetric stepped (ziggurat) border",
                  "Graduated sunburst behind the title — rays tighter at the center",
                  "Letter-spaced condensed caps; treat numerals as jewelry",
                  "Black field, gold protagonist, exactly one emerald guest"],
        "failure": "Undone by asymmetry, organic squiggles, more than one "
                "jewel tone at once, or soft rounded type. Deco is "
                "discipline wearing jewelry — remove the discipline and "
                "it's a casino carpet.",
        "fonts": {"display": "Poiret One", "accent": "Cinzel", "body": "Poppins",
                  "files": ["poiret-one-400.woff2", "cinzel-600.woff2",
                            "poppins-600.woff2"]},
        "textures": ["brushed", "grain"],
        "gloss": "metallic: gold elements get the gel treatment (they read as "
                 "polished brass); everything else stays lacquer-flat",
        "shapes": ["sunburst", "deco-fan", "stepped-frame", "chevron-band"],
        "patterns": ["grid"], "gradients": ["gold-hour"],
        "techniques": ["gradient-border-mask", "emboss-letterpress",
                       "text-3d-extrude"],
        "rules": "DO center and mirror everything, graduate ray spacing, pair "
                 "gold with one jewel tone. DON'T use organic shapes or "
                 "asymmetry — geometry is the glamour.",
    },
    "frutiger-metro": {
        "label": "Frutiger Metro", "style": "frutiger-metro",
        "palette": "metro-bloom",
        "vibe": "Frutiger Aero's flat 2D sibling (mid-2000s vector culture): "
                "loud magenta/lime/aqua/orange color blocks, bloom flowers "
                "and flourishes, human silhouettes, dot constellations and "
                "speech bubbles on clean white — humanist type, rich "
                "gradients inside flat shapes, zero skeuomorphic gloss.",
        "origins": "Mid-2000s vector/Flash culture: music-player skins, "
                "mobile-carrier ads, club flyers and Web-2.0 branding, "
                "catalogued by CARI as the flat 2D sibling of Frutiger Aero "
                "— where Aero rendered glossy water and glass, Metro drew "
                "the same humanist optimism as crisp vector blooms and "
                "dancing silhouettes.",
        "composition": "Motifs cluster in a corner and BLEED off the edge — "
                "a dense flourish zone against a big calm color field. "
                "Diagonal energy carries the eye across; generous white (or "
                "one flat field) keeps the loud colors legible. Never "
                "wallpaper the whole surface.",
        "color": "Full-spectrum saturated jumps — magenta to lime to aqua to "
                "orange to violet — sitting on clean white. Gradients are "
                "smooth hue sweeps that live INSIDE shapes (a petal shifts "
                "pink→orange); backgrounds stay flat. Black is rare and "
                "soft (slate), never harsh.",
        "type": "Rounded humanist sans in the Frutiger/Segoe lineage, "
                "friendly and lowercase-leaning, often framed in speech "
                "bubbles or riding a swoosh. No serifs, no distress, no "
                "letter-spaced shouting — it talks like a helpful kiosk.",
        "materiality": "Pure vector — the crisp anti-aliased edge IS the "
                "material. At most a soft glow behind a motif. No bevels, "
                "no gloss, no photo texture: flatness here is a positive "
                "quality, not a missing feature.",
        "motion": "Growth and cascade: vines and blooms draw themselves, "
                "dot constellations pour in one after another, silhouettes "
                "dance mid-jump. Flash-tween smoothness — energetic, "
                "continuous, never jittery.",
        "imagery": "Human silhouettes mid-dance or mid-leap, filled with "
                "gradients or patterns rather than detail; vector birds and "
                "butterflies; no photography at all — people are shapes "
                "with joy, not faces.",
        "proportion": "Motif clusters claim 25-35% of the canvas, anchored "
                "to a corner. Dot constellations fade along a curve, each "
                "dot about 0.75x the last. Swooshes span the full width on "
                "15-25 degree diagonals. Rounded rects at roughly one-sixth "
                "of their height; white keeps at least half the field.",
        "hierarchy": "Motif energy > hue jumps > silhouette > type. There "
                "is no texture tier at all — remove the blooms and dots "
                "and nothing is left, which is exactly the point.",
        "canon": "Study: the dopplr identity, last.fm-era gig flyers, "
                "Nokia and T-Mobile carrier ads c. 2006, Winamp and WMP "
                "skin culture, Vodafone's speechmark years, and the iPod "
                "silhouette campaign (the crossover hit).",
        "adaptation": "Magenta on white clears 5:1 — body-safe. Lime is "
                "decorative ONLY (under 2:1); all running text sits in "
                "slate. Period-authentic dark mode barely existed — do "
                "'club mode' instead: deep violet field, motifs glowing "
                "brighter, white type. Being vector-native it survives any "
                "DPI unharmed.",
        "era": "c. 2004–2012 — Web 2.0, vector-Flash and phone-box culture",
        "light": "No diegetic light at all — but plenty of GLOW: a soft "
                "radial bloom behind motif clusters like a dance-floor "
                "wash. Whites stay bright, nothing casts a shadow, nothing "
                "reflects; luminosity is drawn, not simulated.",
        "voice": "Friendly kiosk optimism: lowercase, inclusive 'we', one "
                "exclamation point allowed — 'share your world!' Technology "
                "promises phrased as feelings; nothing ironic, nothing "
                "edgy, everything invitational.",
        "sound": "Club-lite electro and airy synth stabs with ringtone-era "
                "gloss; UI sounds bright and short, like drawn bubbles "
                "popping. The soundtrack of a 2007 phone ad where everyone "
                "is dancing.",
        "space": "Phone-box packaging, carrier ads, music-player skins, "
                "event flyers, mall kiosks and early social-web branding — "
                "surfaces selling connection itself.",
        "kinship": "THE defining relationship: flat 2D sibling of "
                "`frutiger-aero` — Aero renders glossy water and glass, "
                "Metro draws the same humanist optimism in vectors. Cousin "
                "of vectordelia. Don't confuse with Microsoft's Metro UI — "
                "that's typographic austerity; this is decorative bloom.",
        "moves": ["Cluster a bloom flourish in one corner and bleed it off-edge",
                  "Run a smooth hue sweep INSIDE each petal; keep the field flat",
                  "Cascade a dot constellation that fades as it travels",
                  "Add one dancing silhouette filled with pattern, not detail"],
        "failure": "Ruined by importing Aero's gloss — aqua bubbles, 3D "
                "bevels, water droplets — or by photo textures and dark "
                "grunge. If it stops looking like it shipped on a 2006 "
                "phone box, it's drifted.",
        "fonts": {"display": "Fredoka", "body": "Poppins",
                  "files": ["fredoka-500.woff2", "poppins-600.woff2"]},
        "textures": ["halftone", "mesh"],
        "gloss": "flat-vivid: no bevels or glass; energy comes from saturated "
                 "fills and gradient sweeps inside crisp vector shapes",
        "shapes": ["bloom-flower", "metro-dots", "swoosh-ribbon"],
        "patterns": ["dots", "wave-divider"], "gradients": ["mesh-vibrant"],
        "techniques": ["holographic-conic", "svg-soft-glow", "sheen-sweep"],
        "rules": "DO cluster motifs into corners and let them bleed off-edge, "
                 "use full-spectrum hue jumps. DON'T add 3D depth, drop "
                 "shadows or photo textures — Aero does that; Metro is flat.",
    },
    "preppy-2000s": {
        "label": "2000s Preppy", "style": "preppy-2000s", "palette": "mall-prep",
        "vibe": "Mall-era collegiate (Abercrombie/Hollister/AE): polo navy + "
                "pink + kelly green on cream, argyle and gingham, crests, "
                "ribbons, monograms, varsity slab numerals — old-money motifs "
                "made bright, casual and logo-proud.",
        "origins": "Ivy and old-money style democratized by 2000s mall "
                "brands — Abercrombie at its peak, Hollister, American "
                "Eagle, Juicy — plus Lilly Pulitzer prints and collegiate "
                "athletic heraldry. The quiet WASP wardrobe turned loud, "
                "logo-proud and aspirational: sunshine you could buy at "
                "the food court.",
        "composition": "Orderly and centered like a store display: a crest "
                "or badge as the focal point, striped bands framing top and "
                "bottom, patterns applied as neat filled panels. Layered "
                "the way an outfit is layered — collar, sweater, jacket — "
                "each element visible and tidy.",
        "color": "Crayon-clean and laundered: polo navy anchors, pink and "
                "kelly green do the charm, cream and khaki hold the ground, "
                "sky blue and gold trim the edges. Colors sit side by side "
                "in stripes and argyle — never blended, never muddied, "
                "never moody.",
        "type": "Varsity slab serifs and athletic numerals for display "
                "(arched across a crest like a letterman jacket), a classic "
                "book serif for body, and script as the monogram accent — "
                "used once, like a signature, not as a paragraph.",
        "materiality": "Cotton piqué, grosgrain ribbon, embroidered patches, "
                "rugby knit, madras. Everything crisp, pressed and "
                "laundered. One soft highlight is allowed — polo-shirt "
                "sheen — but never wet gloss or metallic flash.",
        "motion": "Perky with a small overshoot: badges pop in, ribbons "
                "wave once and settle, stripes slide into place. Cheerful "
                "school-spirit energy — bouncy-lite, never chaotic, never "
                "slow-luxury.",
        "imagery": "Golden-hour campus and beach lifestyle: group laughter, "
                "lacrosse sticks, convertibles, lens flare optional. Or "
                "catalog flat-lays of folded clothing in color-sorted "
                "grids. Everyone looks like they smell like the mall.",
        "proportion": "The crest holds 20-30% of the composition's height, "
                "dead center. Stripe bands run 3-7% of height and travel "
                "in pairs. Argyle diamonds sit near 10% of width with the "
                "dashed overline at a quarter of the diamond's stroke. "
                "Radii modest, 8-12px — piqué collar, not bubble.",
        "hierarchy": "Emblem > pattern panel > palette cheer > type > "
                "motion. The crest is the quarterback; everything else "
                "blocks for it.",
        "canon": "Study: A&F Quarterly covers, Hollister's shuttered "
                "storefronts, Lilly Pulitzer prints, the Ralph Lauren polo "
                "player (the ancestor), Juicy tracksuit lockups, and a "
                "2005 yearbook superlatives spread.",
        "adaptation": "Navy on cream clears 10:1 — body-safe everywhere. "
                "Pink and kelly are large-element accents, not text "
                "colors. Dark mode is the navy blazer: navy field, cream "
                "type, pink and gold trims — it stays preppy in the dark. "
                "Keep patterns confined to panels so text zones stay "
                "quiet.",
        "era": "c. 1998–2008 mall apex; Ivy/old-money roots in the 1950s",
        "light": "Golden hour, forever: beach bonfires, campus quads at "
                "5pm, lens flare optional but welcome. Indoors it's bright "
                "even retail wash. Nothing moody, nothing gray, no weather "
                "except summer.",
        "voice": "Earnest school-spirit cheer with monogrammed sign-offs — "
                "'Go team! xo, E.B.' Brand names dropped casually, irony "
                "banned. The copy sounds like a yearbook inscription "
                "written by someone popular and genuinely nice.",
        "sound": "Pop-punk and acoustic summer anthems, crowd cheers, "
                "flip-flops on a boardwalk. Everything jingle-friendly and "
                "singable from a car with the top down.",
        "space": "Mall storefronts, yearbooks, dorm rooms, beach houses, "
                "varsity jackets, stationery, gift bags with tissue paper — "
                "the retail theater of belonging.",
        "kinship": "Ivy/old-money style democratized and turned up; sworn "
                "opposite of `skate-culture` (the mall's two tribes); "
                "cousin of `pastel` (shares the sweetness, adds heraldry). "
                "Don't confuse with dark academia — same campus, opposite "
                "weather.",
        "moves": ["Crest front and center with arched varsity lettering",
                  "Argyle or gingham as one filled panel — never full wallpaper",
                  "Navy anchors the layout; pink and kelly green do the charm",
                  "Band the top and bottom with grosgrain-ribbon stripes"],
        "failure": "Falls apart with distressing, dark moody palettes, "
                "neon, or irony. This aesthetic is EARNEST — the moment it "
                "winks at the camera or looks worn-in, it's a different "
                "decade.",
        "fonts": {"display": "Alfa Slab One", "accent": "Pacifico",
                  "body": "Lora",
                  "files": ["alfa-slab-one-400.woff2", "pacifico-400.woff2",
                            "lora-400.woff2"]},
        "textures": ["stripes", "paper"],
        "gloss": "clean-sheen: crisp cotton flatness with one soft highlight "
                 "on badges/buttons (polo-shirt clean, never wet)",
        "shapes": ["argyle-tile", "gingham-tile", "crest-shield",
                   "ribbon-banner"],
        "patterns": ["diagonal-stripes", "checkerboard"], "gradients": [],
        "techniques": ["badge-pill", "sheen-sweep"],
        "rules": "DO layer argyle over solids, monogram everything, keep "
                 "colors crayon-clean. DON'T distress, darken or neon it — "
                 "this is sunshine and lacrosse fields.",
    },
    "frutiger-aero": {
        "label": "Frutiger Aero", "style": "frutiger-aero",
        "palette": "frutiger-aqua-gloss",
        "vibe": "2004-13 techno-optimist humanism: glossy water, glass, "
                "grass and sky. Bubbles rise, koi drift, interfaces float as "
                "translucent panes over bright ecosystems — technology and "
                "nature presented as best friends, sincerely.",
        "origins": "Named (by the CARI community, c. 2017) after Adrian "
                "Frutiger, whose humanist typefaces captioned the era: "
                "Windows Vista/7 Aero glass, PSP and Wii packaging, bottled-"
                "water and airline ads, eco-tech marketing. The optimistic "
                "prelude to flat design — the future as a clean bright "
                "morning.",
        "composition": "Horizon-based: airy sky above, grounded detail "
                "below, content floating mid-air in glass panels. Circular "
                "elements — orbs, bubbles, lens glints — drift through the "
                "upper field. Depth comes from stacked translucency, not "
                "shadow; everything gets air around it.",
        "proportion": "Glass panels rounded 12-20px; bubble clusters of 3-7 "
                "spanning three scales; the specular highlight claims the "
                "top 30-45% of any glossy object. Horizon sits at the lower "
                "third. Whitespace is literal air — crowding breaks the "
                "weather.",
        "color": "Sky blues, aqua cyans and grass greens with white light "
                "everywhere; gradients behave like light through water. "
                "Saturation is high but nature-calibrated — never neon. A "
                "warm accent (koi orange) appears rarely and reads as "
                "precious.",
        "light": "Everything is backlit by a friendly sun: specular "
                "highlights, caustic shimmer, lens glints on glass edges. "
                "Light sources sit above-and-behind; whites bloom softly. "
                "Nothing is ever underlit or moody — the weather is "
                "permanently 10am.",
        "type": "Humanist sans (the Frutiger/Segoe lineage), sentence case, "
                "friendly and unforced — often white with a soft glow when "
                "set over imagery. No serifs, no condensed shouting, no "
                "distress; the type is a clear announcement in a bright "
                "terminal.",
        "materiality": "Water, glass, dew, polished plastic, wet grass. "
                "Every surface is clean and slightly wet — the wet look IS "
                "the aesthetic. Surfaces reflect and refract; dryness reads "
                "as broken.",
        "motion": "Buoyant drift: bubbles rise, light sweeps across glass, "
                "clouds parallax slowly. Easing behaves like water — "
                "smooth, continuous, gently damped. Nothing snaps or "
                "bounces; things surface.",
        "imagery": "Macro water droplets, koi and dolphins, grass blades "
                "against blue sky, wind turbines, kids mid-jump — stock-"
                "photo optimism rendered pristine and saturated. The camera "
                "loves condensation.",
        "voice": "Bright kiosk warmth with an eco-promise: 'technology in "
                "harmony with nature.' Simple present tense, inclusive and "
                "sincere — this is the pre-irony internet speaking, and it "
                "genuinely believes the future will be nice.",
        "sound": "Airy pads, water-drop UI sounds, glassy chimes — the "
                "Vista startup chord is the national anthem. Everything "
                "sounds hydrated and slightly reverberant, like a bright "
                "atrium.",
        "space": "OS chrome and default wallpapers, device packaging, "
                "airport ad lightboxes, bottled-water labels, hopeful "
                "institutional PowerPoints, early smart-home concepts — "
                "surfaces selling clean futures.",
        "kinship": "Parent of `frutiger-metro` (its flat 2D sibling — Aero "
                "renders the gloss Metro draws); grandparent of modern "
                "glassmorphism; cousin of `y2k-chrome` (shared optimism — "
                "Y2K chromes it, Aero hydrates it). Don't confuse with "
                "vaporwave, which mourns this era ironically; Aero lives "
                "it sincerely.",
        "hierarchy": "Light and gloss > color ecology > glass depth > "
                "imagery > type. If the surfaces stop glinting, no "
                "arrangement of the rest will bring the morning back.",
        "canon": "Study: Windows Vista/7 Aero UI and wallpaper suites, PSP "
                "packaging, Fiji and Evian label eras, ANA/Singapore "
                "Airlines ads c. 2008, the glossy-orb icon culture of "
                "2006 — and this vault's own frutiger-aero default theme.",
        "adaptation": "White type over imagery needs a glow or scrim; body "
                "ink stays deep sea-blue on the light field (tokens are "
                "contrast-audited). Dark mode is 'aero night': deep-ocean "
                "blues, bioluminescent accents, glass still glossy. Reduced "
                "motion: stop the drift, keep the gloss.",
        "era": "c. 2004–2013 — Vista/PSP-era techno-optimism",
        "fonts": {"display": "Poppins", "body": "Inter",
                  "files": ["poppins-600.woff2", "inter-400.woff2"]},
        "textures": ["mesh", "grain"],
        "gloss": "maximum wet: gel + glass + sheen everywhere — this is the "
                 "aesthetic the nativeui gel button and glass card were "
                 "born from; if in doubt, add another highlight",
        "shapes": ["aqua-bubbles", "gloss-orb", "grass-swoosh"],
        "patterns": ["dots", "wave-divider"], "gradients": [],
        "techniques": ["glass-layered", "aurora-blur", "sheen-sweep",
                       "svg-soft-glow"],
        "rules": "DO stack translucent layers, keep nature in frame, light "
                 "from above-behind. DON'T flatten (that's Metro), don't "
                 "neon (that's cyberpunk), don't wink (that's vaporwave).",
        "moves": ["Glass panel with a top sheen floating over a sky-to-grass scene",
                  "Bubble cluster rising through one corner at three scales",
                  "One glossy orb as the hero object, highlight in its upper third",
                  "Horizon at the lower third with a white glow at the seam"],
        "failure": "Dry equals dead: the moment surfaces stop being wet and "
                "backlit it collapses into generic corporate blue. Equally "
                "fatal: irony, darkness, or flattening the gloss away.",
    },
    "y2k-chrome": {
        "label": "Y2K Chrome", "style": "y2k-chrome",
        "palette": "millennium-chrome",
        "vibe": "1997-2003 millennium futurism: liquid chrome, silver "
                "everything, translucent candy plastic, lens flares and "
                "blob forms floating in white voids — the future staged as "
                "a showroom you were about to enter.",
        "origins": "Designed in the countdown to 2000: the iMac G3's "
                "translucent candy shells, The Designers Republic and "
                "Wipeout's identities, TDK/MiniDisc ads, inflatable "
                "furniture, early CGI metaballs. Optimism with a metallic "
                "taste — everyone was about to live in the future, and the "
                "future was silver.",
        "composition": "A centered hero object floats in a white or "
                "gradient void; orbit rings and elliptical arcs circle it; "
                "a swoosh crosses behind. Generous emptiness is the point — "
                "the future is uncluttered because everything old was "
                "thrown away.",
        "proportion": "Blobs bulge past geometry — superellipse corners, "
                "radius beyond 50%. Chrome bevels stay thin (1-2% of the "
                "object). Flare stars carry 4-8 points; orbit rings tilt "
                "15-30 degrees. Type stays small relative to the hero "
                "object — the object is the message.",
        "color": "Silver-to-white chrome gradients, ice white, electric "
                "blue — with translucent candy (blueberry, lime, grape) as "
                "accents. Black is rare. Color exists mostly to make the "
                "chrome look colder and the plastic look edible.",
        "light": "Infinite studio: white-cyc lighting with hard speculars, "
                "reflections of a showroom that doesn't exist, and a lens "
                "flare earned by every bright edge. Light is an effect, "
                "never a mood.",
        "type": "Techno grotesques and squared faces (Orbitron energy), "
                "lowercase futurism or widely spaced caps, often set on a "
                "curve or riding an orbit ring. Digital-display faces "
                "appear as accents. Serifs do not exist in this future.",
        "materiality": "Liquid mercury, polycarbonate, brushed aluminum, "
                "holographic foil, inflatable PVC. Everything is hard, "
                "cool and reflective — matte is forbidden; even shadows "
                "look polished.",
        "motion": "Metaballs morph, orbits rotate slowly, flares sweep on "
                "cue; the camera moves like a product turntable. Easing is "
                "sleek and continuous — mechanical confidence, no bounce, "
                "no jitter.",
        "imagery": "3D-rendered hero products floating mid-air, silver "
                "humanoids, wireframe globes, macro shots of translucent "
                "plastic. Humans appear reflected in chrome, rarely in "
                "person.",
        "voice": "Millennium-promise speak: 'welcome to tomorrow.' Product "
                "neologisms with internal caps (iThing, eEverything), "
                "confident and slightly alien — a voice assembled in a "
                "clean room, cool to the touch.",
        "sound": "Trance and big-beat, TR-909 sheen, the ghost of a modem "
                "handshake, the Intel bong. UI sounds are metallic ticks "
                "and airlock whooshes — the room tone of a server that "
                "loves you.",
        "space": "Gadget packaging, CD-ROM intros, music-channel idents, "
                "car-show concept stands, sneaker-tech ads, winamp-skin "
                "desktops — anywhere the millennium was being sold in "
                "advance.",
        "kinship": "Cousin of `frutiger-aero` — the same optimism one era "
                "earlier: Y2K chromes it, Aero hydrates it. Vaporwave "
                "samples THIS material ironically twenty years later. "
                "Shares hardware with `cyberpunk` but not weather: Y2K is "
                "showroom-clean, cyberpunk is street-dirty.",
        "hierarchy": "Material (chrome) > hero object > flare and light > "
                "motion > type. If the chrome convinces, everything else "
                "is garnish; if it doesn't, nothing survives.",
        "canon": "Study: the iMac G3 and clamshell iBook, The Designers "
                "Republic's Wipeout 3 identity, TDK MiniDisc ads, the Air "
                "Max 97, Windows Media Player skin culture, Björk's 'All "
                "Is Full of Love' video.",
        "adaptation": "Electric blue clears 4.5:1 on the ice field — body-"
                "safe; chrome gradients are for objects, never behind text "
                "(legibility dies on mirrors). Dark mode is 'showroom "
                "night': graphite field, chrome stays bright, blue glows. "
                "Reduced motion: freeze the orbits, keep the flare "
                "static.",
        "era": "c. 1997–2003 — the millennium countdown and its morning after",
        "fonts": {"display": "Orbitron", "body": "Space Grotesk",
                  "files": ["orbitron-700.woff2", "space-grotesk-500.woff2"]},
        "textures": ["brushed", "mesh"],
        "gloss": "mirror-grade: chrome-gel every primary element (the "
                 "nativeui gel at maximum), glass second; anything matte "
                 "has wandered in from another decade and must leave",
        "shapes": ["chrome-blob", "lens-flare", "orbit-rings"],
        "patterns": ["grid"], "gradients": [],
        "techniques": ["chromatic-aberration", "holographic-conic",
                       "liquid-hover"],
        "rules": "DO center the hero, tilt the orbit, earn the flare. "
                 "DON'T add warmth, texture or clutter — the void is the "
                 "luxury; one object floating beats five arranged.",
        "moves": ["One chrome blob hero centered in a white void",
                  "Tilted elliptical orbit ring passing behind the subject",
                  "A four-point lens flare on the brightest edge",
                  "Type on a curve: lowercase, letter-spaced, slightly alien"],
        "failure": "Dies of warmth: wood, paper grain, hand-drawn anything, "
                "or matte surfaces. Also dies of clutter — two hero objects "
                "is zero hero objects. The future has room for exactly one "
                "thing at a time.",
    },
    "dark-academia": {
        "label": "Dark Academia", "style": "dark-academia",
        "palette": "candlelit-study",
        "vibe": "Candlelit scholarship: oxblood and walnut, brass and "
                "parchment, annotated margins, plaster casts and rain "
                "against tall windows. Knowledge treated as romance and "
                "libraries as cathedrals — study, but make it a novel.",
        "origins": "Donna Tartt's 'The Secret History' (1992) gave it a "
                "founding text; Tumblr codified it c. 2014 and TikTok "
                "canonized it in 2020. Behind those: Oxbridge gothic "
                "architecture, classical education iconography, 'Dead "
                "Poets Society', and every reading lamp that ever glowed "
                "green in a dark room.",
        "composition": "Dense and layered like stacked spines: vertical "
                "rhythms, centered classical symmetry gently broken by the "
                "clutter of actual use — a margin note, a ribbon marker. "
                "Edges vignette into shadow; the room always continues "
                "past the frame.",
        "proportion": "Text is a first-class citizen: comfortable 60-75ch "
                "measures, generous leading. Ornaments stay small and "
                "engraved — a seal at ~5% of the page. Frames are double-"
                "ruled fine lines; drop caps run 3-4 lines deep; images "
                "sit in wide dark mats.",
        "color": "Walnut and espresso grounds, parchment for text fields, "
                "oxblood + forest + old brass as accents. Nothing fully "
                "saturated — every color looks steeped in tea and time. "
                "Gold here is always brass: aged, never bright.",
        "light": "Candlelight and green-shaded lamps: warm pools in "
                "darkness with strong vignettes. Daylight arrives grey "
                "through tall windows. Light always has a source you "
                "could touch — nothing is lit from nowhere.",
        "type": "Transitional and old-style serifs — Playfair Display for "
                "title pages, Lora for the long read — with true italics "
                "doing serious work and small caps for inscriptions. "
                "Handwritten marginalia (Caveat) is the only informality "
                "permitted.",
        "materiality": "Worn leather, foxed paper, brass fittings, sealing "
                "wax, chalk dust, tweed. Age is carried honestly — patina "
                "earned by hands and years, never a distress filter "
                "sprayed on evenly.",
        "motion": "Slow page-turns, ink blooming into paper, a candle "
                "flame's 2-3% flutter, dust motes crossing a light shaft. "
                "Transitions dissolve like memory; nothing in a library "
                "bounces.",
        "imagery": "Statuary details, books photographed from above, "
                "handwritten letters, rain-dark quads, chiaroscuro "
                "portraits. Hands hold pens and cups — never phones. The "
                "camera behaves like a patient reader.",
        "voice": "Literary and allusive; semicolons welcome; a Latin "
                "epigraph now and then. Conspiratorially second-person — "
                "'you've read this before, haven't you' — sincere about "
                "beauty, lightly melancholy, never cynical.",
        "sound": "String quartets, rain on glass, page turns, a nib "
                "scratching, distant bells; vinyl crackle as room tone. "
                "Silence is furniture here — leave space for it.",
        "space": "Reading apps and library software, bookstores, heritage "
                "university brands, stationery and tea packaging, museum "
                "education wings, book covers that want to be kept.",
        "kinship": "`preppy-2000s`' nocturnal sibling — same campus, "
                "opposite weather. Cousin of `editorial` (shares the serif "
                "discipline, adds shadow and sentiment). Complement of "
                "`golden-archive`: both sanctify knowledge — academia by "
                "candlelight, the archive by starlight. Don't confuse "
                "with gothic horror: academia romanticizes study, not "
                "death.",
        "hierarchy": "Atmosphere (light + material) > typography > steeped "
                "color > imagery > ornament. If the room doesn't feel "
                "warm-dark and inhabited, no amount of serif will rescue "
                "it.",
        "canon": "Study: 'The Secret History' cover lineage, the Bodleian "
                "and Trinity College Long Room, 'Dead Poets Society' "
                "stills, Sargent's portraits, Penguin Clothbound "
                "Classics, and a decade of Tumblr study-blog "
                "photography.",
        "adaptation": "Parchment on walnut clears 10:1 — read all night. "
                "Brass is display-only (~4:1); oxblood is for seals and "
                "spines, not sentences. Light mode is 'the reading room "
                "at noon': parchment field, walnut ink, oxblood accents — "
                "period-true and gorgeous. Reduced motion: still the "
                "candle, keep the vignette.",
        "era": "founding text 1992; aesthetic codified c. 2014–2022",
        "fonts": {"display": "Playfair Display", "body": "Lora",
                  "accent": "Caveat",
                  "files": ["playfair-display-700.woff2", "lora-400.woff2",
                            "caveat-400.woff2"]},
        "textures": ["paper", "grain"],
        "gloss": "none — brass patina and beeswax at most; the shiniest "
                 "thing in the room is a candle flame reflected in dark "
                 "wood, and it flickers",
        "shapes": ["wax-seal", "open-book", "laurel-corner"],
        "patterns": ["graph-paper"], "gradients": [],
        "techniques": ["dropcap-initial-letter", "emboss-letterpress",
                       "grain-overlay"],
        "rules": "DO vignette, annotate, steep every color in tea, cite "
                 "your sources in italic. DON'T brighten, flatten, or "
                 "sanitize the clutter — a too-clean study is a showroom, "
                 "not a mind.",
        "moves": ["Vignette the edges; pool warm lamplight at the center",
                  "Double-rule a fine frame and sink a 3-line drop cap",
                  "Annotate the margin in a handwritten hand, slightly tilted",
                  "Seal one element in oxblood wax as the mark of care"],
        "failure": "Breaks under brightness, crisp minimalism, or irony — "
                "and equally under costume-party excess (skulls and "
                "daggers everywhere). It's a place where someone actually "
                "reads; lose that and it's a Halloween set.",
    },
    "swiss-international": {
        "label": "Swiss International", "style": "swiss-international",
        "palette": "swiss-signal",
        "vibe": "The International Typographic Style: objective white "
                "space, a mathematical grid, one neo-grotesque family, one "
                "signal red. Design as civic infrastructure — it informs "
                "perfectly and refuses, on principle, to decorate.",
        "origins": "1950s Basel and Zürich: Müller-Brockmann's concert "
                "posters, Max Bill's concrete art, Emil Ruder's typography "
                "course — Bauhaus and De Stijl distilled into a teachable "
                "system that became the world's default 'good design' "
                "(airports, corporate identity, the NASA manual).",
        "composition": "The grid is sacred: modular columns, flush-left "
                "rag-right, asymmetric balance computed rather than felt. "
                "White space is structural, not leftover. Elements align "
                "across the entire system or they don't ship.",
        "proportion": "Grid modules in strict ratios (thirds, fifths); two "
                "or three type sizes per piece with unmistakable jumps; "
                "rules exactly one point. The red element occupies under "
                "10% of the area and collects 90% of the attention — "
                "that asymmetry is the design.",
        "color": "White field, black ink, ONE signal red. Photography "
                "stays black-and-white. Color is information, never "
                "decoration: if red appears twice, it means two things — "
                "and if it doesn't mean two things, delete one.",
        "light": "None. The page is a shadowless printed surface; any "
                "simulated depth betrays the flat honest plane. What "
                "light exists lives inside the documentary photography, "
                "which brings its own grey daylight.",
        "type": "A neo-grotesque (Helvetica/Univers lineage — Inter here) "
                "in few weights, flush left, with tight even 'color' of "
                "the text block. Hierarchy by size, weight and position "
                "only. Tabular numerals; italics only when bold cannot "
                "do the job.",
        "materiality": "Smooth offset paper, silkscreen ink, enamel "
                "signage. The material is PRINT itself — flatness as "
                "integrity. A texture would be a confession that the "
                "layout couldn't carry the page.",
        "motion": "If it must move: strict translations along grid axes, "
                "hard cuts or metric easing, type never distorting. The "
                "model is a station departure board updating — precise, "
                "legible, indifferent to delight.",
        "imagery": "Objective black-and-white photography — documentary, "
                "unstyled, unsentimental — or none. Diagrams and "
                "pictograms outrank illustration. The map, the timetable "
                "and the poster are the native genres.",
        "voice": "Informational, verb-lean, verifiable: 'Zürich 19:04, "
                "Gleis 7.' No adjective survives unless it can be "
                "measured. The designer is invisible; the message is "
                "everything; exclamation points do not exist.",
        "sound": "Station room tone: an announcement, a clock tick, "
                "footsteps on terrazzo. If music, metronome-precise "
                "minimalism. Interface sounds are single dry clicks — "
                "confirmation, not celebration.",
        "space": "Transit systems and wayfinding, museums, government "
                "forms, corporate identity manuals, pharmaceutical "
                "packaging — and every tech company that wants to look "
                "neutral and trustworthy.",
        "kinship": "Ancestor of `mono` (Swiss gone brutalist-dark) and of "
                "`neutral`; `hi-contrast` is Swiss stripped to pure "
                "accessibility signal. Sworn opposite of `avant-basic` — "
                "the grid versus the warp. Don't confuse with lifestyle "
                "minimalism: Swiss is dense with information, empty only "
                "of decoration.",
        "hierarchy": "Grid > typography > white space > the red element > "
                "photography. Everything else was already deleted before "
                "the first draft.",
        "canon": "Study: Müller-Brockmann's Beethoven poster, the NASA "
                "Graphics Standards Manual, Vignelli's NYC subway map "
                "and the SBB rail identity, Ruder's 'Typographie', the "
                "'Helvetica' documentary.",
        "adaptation": "Black on white is 21:1; the signal red clears 5:1 "
                "for text but should stay a signal. Dark mode is the "
                "departure board — black field, white type, red signals — "
                "already canonical. Because the grid is ratio-based it "
                "survives any size, medium or century unchanged.",
        "era": "1950s Basel/Zürich; the global default through the 70s–80s; permanent",
        "fonts": {"display": "Inter", "body": "Inter",
                  "files": ["inter-700.woff2", "inter-400.woff2"]},
        "textures": ["paper"],
        "gloss": "zero — matte print forever; even the red is flat ink. A "
                 "gradient here is not a choice, it is a scandal",
        "shapes": ["grid-marks", "signal-dot", "crossbar-arrow"],
        "patterns": ["grid", "graph-paper"], "gradients": [],
        "techniques": ["subgrid-align", "text-balance-wrap",
                       "container-query"],
        "rules": "DO build the grid first and let the alignments show; "
                 "set flush left; earn every element. DON'T center "
                 "sentimentally, decorate, or use two accent colors — "
                 "one red, one meaning.",
        "moves": ["Build the grid first; let it show in ruthless alignment",
                  "Two sizes of one grotesque, flush left, and nothing else",
                  "Place ONE red element exactly where the eye should land",
                  "Replace every decoration you were about to add with white space"],
        "failure": "Fails by ornament, by centering everything politely, "
                "by a second accent color, or by breaking the grid 'just "
                "this once.' Also fails by cosplay: Swiss without real "
                "information design is just Helvetica on a poster.",
    },
    "golden-archive": {
        "label": "Golden Archive", "style": "golden-archive",
        "palette": "golden-archive",
        "vibe": "This vault's homegrown aesthetic: a starlit museum for "
                "human knowledge. Deep-space navy, engraved gold, thin "
                "artifact frames with halos, constellation paths between "
                "exhibits, plaques in italic serif — the Voyager Golden "
                "Record as an interface language.",
        "origins": "Born 2026-07-04 in this vault's Ultra Archive gallery, "
                "designed to exhibit 6.8 million Wikipedia images. Its "
                "ancestry: the Voyager Golden Record (1977, Sagan and "
                "Drake's offline backup of humanity), museum plaque "
                "conventions, star atlases and planetarium graphics.",
        "composition": "Exhibits descend a Z-path linked by dashed "
                "constellation lines, one artifact per wall segment with "
                "real air around it. Chrome stays pinned and minimal at "
                "the top. Depth is parallax — far stars, mid ghosts, "
                "foreground artifacts — a corridor, not a page.",
        "proportion": "Frames thin (1-2px gold) with a 10-16px halo; "
                "plaques ~64px under any artifact; catalog numbers six "
                "hex characters; parallax ratios near 0.12/0.45/1.0; "
                "gaps between exhibits of 0.5-1.5 artifact heights so "
                "each gets its wall.",
        "color": "Deep-space navy grounds with gold as the ONLY metal — "
                "#d9b453 rising to #f2dc9b highlights — parchment for "
                "text, starlight blue-grey for whispers. Jewel accents "
                "are deliberately absent: gold is alone because the "
                "artifacts provide all other color.",
        "light": "Starlight and halo: pinpoint speculars, soft gold glow "
                "around frames, nebula washes at 5-10% alpha. The room "
                "stays dark on purpose — light never floods, so every "
                "artifact reads as the brightest thing near it.",
        "type": "The plaque voice: bold small-cap sans for titles, italic "
                "serif (Georgia/Fraunces) for captions, counts and "
                "provenance. Gold for headings, parchment for body, "
                "starlight for metadata. Engraved, never printed-loud.",
        "materiality": "Void, gold leaf, museum glass, engraved brass "
                "plaques; film-fine grain over the dark. Every surface is "
                "matte except the gold, which is polished — one material "
                "gets to shine and it earned it in 1977.",
        "motion": "Drift and parallax: layers scroll at different rates, "
                "stars wrap slowly, artifacts glide in and settle. A "
                "lightbox blooms out of its exhibit and returns to it. "
                "Nothing bounces — this is a museum, not an arcade.",
        "imagery": "The artifacts themselves — any image becomes imagery "
                "once framed in thin gold on the void. Between them: "
                "star fields, the grooved gold disk, engraved pictograms "
                "in the Voyager manner.",
        "voice": "Curatorial reverence with quiet wonder: '6,840,001 "
                "artifacts preserved · offline.' Plaques state catalog, "
                "collection, dimensions, source — facts as poetry. The "
                "museum never exclaims; the collection is the "
                "exclamation.",
        "sound": "Planetarium hush: sub-bass room tone, one soft chime on "
                "interaction, the faint tick of a rotating record. "
                "Silence is the default state and every sound must "
                "justify breaking it.",
        "space": "The Ultra Archive gallery (its birthplace), knowledge "
                "and backup tools, personal wikis, library software, "
                "portfolio 'collections' pages — any surface whose job is "
                "to EXHIBIT rather than to sell.",
        "kinship": "`art-deco`'s cosmic sibling — both gold-on-dark, but "
                "deco is urban theatre and the archive is deep-space "
                "quiet. Cousin of `dark-academia` (both sanctify "
                "knowledge: academia by candlelight, archive by "
                "starlight). Child of this vault itself. Don't confuse "
                "with generic dark-luxury: the archive is scientific, "
                "not indulgent.",
        "hierarchy": "The void > gold discipline > the artifact > plaque "
                "typography > constellation connective tissue. Darkness "
                "carries it: brighten the room and the museum becomes a "
                "banner ad.",
        "canon": "Study: the Voyager Golden Record etching and its cover "
                "diagram, NASA/JPL mission patches, Uranometria star "
                "plates, museum label conventions, Cosmos title cards — "
                "and this vault's own gallery.py, where the style was "
                "born.",
        "adaptation": "Contrast-audited at birth: gold on navy ~10:1, "
                "parchment body ~15:1, starlight metadata ~5:1. Light "
                "mode is 'the catalog print': parchment field, navy ink, "
                "gold rules — a printed museum catalog. Reduced motion: "
                "freeze the parallax; the hush survives stillness "
                "perfectly.",
        "era": "born 2026 in this vault; ancestry 1977 (Voyager record)",
        "fonts": {"display": "Playfair Display", "body": "Fraunces",
                  "files": ["playfair-display-700.woff2",
                            "fraunces-600.woff2"]},
        "textures": ["starfield", "grain"],
        "gloss": "polished gold only: gel treatment reserved for gold "
                 "elements (nativeui's golden-archive does this natively); "
                 "everything else stays void-matte so the gold means "
                 "something",
        "shapes": ["gold-disk", "constellation-path", "stepped-frame"],
        "patterns": ["topographic"], "gradients": ["archive-space"],
        "techniques": ["gradient-border-mask", "svg-soft-glow",
                       "grain-overlay"],
        "rules": "DO frame everything in thin gold with a halo, plaque "
                 "every artifact, connect with constellation lines. DON'T "
                 "add a second metal or jewel tones, brighten the void, "
                 "or let chrome outshine the collection.",
        "moves": ["Frame anything in thin gold with a soft halo on near-black",
                  "Plaque beneath: small-cap title, gold catalog line, italic source",
                  "Link elements with dashed gold constellation lines and node dots",
                  "One grooved gold disk as the seal — the record still spinning"],
        "failure": "Lost when the room brightens, a second metal arrives, "
                "or exhibits crowd each other off the wall. And if the "
                "plaques start selling instead of cataloguing, it's not "
                "an archive anymore — it's a storefront in a dark "
                "theme.",
    },
    # ---- systematic / informational ------------------------------------- #
    "editorial": {
        "label": "Editorial", "style": "editorial", "palette": "editorial-ink",
        "vibe": "The page as argument: a column grid, a serif that can carry "
                "4,000 words, one red that means 'read this first', and white "
                "space measured in column inches rather than sprinkled. "
                "Journalism's own design language — built to be read, at "
                "speed, by someone standing up.",
        "origins": "Nineteenth-century newspapers were densely packed vertical "
                "type with a stack of headlines per article, and the craft "
                "grew out of fixing that: layout dummies that specified column "
                "widths before a typesetter set a word, copy measured in "
                "column inches, headline sizes chosen as both letter size and "
                "space budget. Paste-up replaced typesetting, direct-to-plate "
                "replaced paste-up, InDesign replaced the drawing board — and "
                "the column grid survived all three.",
        "composition": "Columns first, everything else negotiated against "
                "them. Asymmetric by default, with a dominant element per "
                "spread and a clear second; rules and white gutters do the "
                "dividing so boxes don't have to. The eye is given one "
                "entrance and a route, never a menu of equals.",
        "proportion": "Measure 60-70ch for the long read, 40-50ch when the "
                "page runs multi-column. A 1.414 scale gives four unmistakable "
                "steps — deck, standfirst, body, caption — and hairline rules "
                "stay at exactly 1px. Drop caps run three lines; pull quotes "
                "take a column and a half and never full width.",
        "color": "Black ink on white stock, a grey for secondary matter, and "
                "one editorial red reserved for signal — section marks, "
                "breaking flags, the live link. Colour is a wayfinding system "
                "here, not a mood: if a second accent appears, the reader now "
                "has two things to decode instead of one.",
        "light": "Flat page light, no modelled depth. What dimensionality "
                "exists comes from the photography and from the tonal step "
                "between body grey and headline black. A drop shadow on a "
                "news page reads as a banner ad and is treated as one.",
        "type": "An old-style or transitional serif for the body (Lora here) "
                "with real italics and true small caps, against a display cut "
                "with tighter fit (Playfair Display) for heads. Tabular "
                "figures in tables, oldstyle in running text. Hierarchy comes "
                "from size, weight and position — never from colour alone.",
        "materiality": "Newsprint and coated magazine stock: ink that gains "
                "slightly, paper with a visible tooth, a fold that the layout "
                "respects. The material fact is that this was printed and "
                "someone paid per page — every element justifies its inches.",
        "motion": "Minimal and functional. Content arrives, it does not "
                "perform: short cross-fades, a sticky masthead that shrinks, "
                "progress along the read. If an element animates it is because "
                "the reader's position changed, not because the page wanted "
                "attention.",
        "imagery": "Documentary photography with captions that add fact rather "
                "than repeat the headline; information graphics that could run "
                "without the article. Images are cropped decisively and sized "
                "by importance — a half-column mugshot and a full-bleed opener "
                "are both editorial decisions, visible as such.",
        "voice": "Declarative, sourced, front-loaded: the first sentence "
                "carries the news and the rest supports it. Subheads are "
                "navigational rather than witty. Adjectives survive only when "
                "a fact is underneath them, and the byline takes the credit "
                "so the design doesn't have to.",
        "sound": "Essentially silent — the rustle of a turned broadsheet, a "
                "pen on a crossword. Interface sound is limited to a single "
                "soft confirmation; a news page that chimes at you has "
                "mistaken itself for a notification.",
        "space": "Newspapers and magazines, long-form online, annual reports, "
                "documentation, research publication, any product whose core "
                "object is an article — plus every blog that wants to be "
                "believed before it is read.",
        "kinship": "`swiss-international` stripped of its dogma and given a "
                "serif: same grid discipline, warmer and willing to use "
                "ornament when it aids reading. Parent of `neutral`'s layout "
                "logic; daylight cousin of `dark-academia`, which shares the "
                "serif but adds shadow and sentiment. Don't confuse with "
                "minimalism: an editorial page is dense, just organised.",
        "hierarchy": "Grid > typographic hierarchy > white space > the red "
                "signal > imagery > ornament. If a reader can't find the "
                "start of the article in one second, nothing further down "
                "this list will save the page.",
        "canon": "Study: the Times and Guardian redesigns, National "
                "Geographic and The Economist's grids, Harper's and The New "
                "Yorker's text pages, Edward Tufte on information density, and "
                "any newspaper front page from before colour printing.",
        "adaptation": "Black on white is 21:1 and the grey secondary holds "
                "7:1; the editorial red clears AA for text but belongs on "
                "small signal elements. Dark mode inverts to a warm off-black "
                "with paper-white type and needs a step more leading, since "
                "reversed text blooms. The grid is ratio-based, so a phone "
                "gets the same system at one column.",
        "era": "modern form from the 1850s; digital since the mid-1990s; permanent",
        "fonts": {"display": "Playfair Display", "body": "Lora",
                  "files": ["playfair-display-700.woff2", "lora-400.woff2"]},
        "textures": ["paper"],
        "gloss": "none — this is ink on stock. The only shine permitted is a "
                "coated-paper sheen in a photograph of the magazine, never in "
                "the interface itself; a gloss here reads as advertising.",
        "shapes": ["editorial-rule", "hairline-frame"],
        "patterns": ["graph-paper"],
        "gradients": [],
        "techniques": ["dropcap-initial-letter", "shape-outside-wrap",
                       "text-balance-wrap", "scroll-progress-bar"],
        "rules": "DO set a real column grid, lead with the news, rule rather "
                "than box, and caption every image with a fact. DON'T centre "
                "body copy, letterspace lowercase, or introduce a second "
                "accent colour — the red already means something.",
        "moves": ["Build the column grid and let the gutters divide the page",
                  "Sink a three-line drop cap to mark the true start",
                  "Set one pull quote at a column and a half, never full width",
                  "Reserve the red for signal; everything else is ink and grey"],
        "failure": "Fails by decoration, by centring, and by the second accent "
                "colour. It fails hardest when the content is thin: editorial "
                "design is a system for organising a lot of information, and "
                "over three paragraphs it just looks like a newspaper costume.",
    },
    "neutral": {
        "label": "Neutral", "style": "neutral", "palette": "ink-and-glass",
        "vibe": "The modern product default, done properly: a slate ramp, one "
                "blue that means 'act', generous space and nothing with an "
                "opinion of its own. Deliberately quiet so the data, the "
                "document or the dashboard can be the loud thing.",
        "origins": "Descends from post-war minimalism — Judd, Agnes Martin, "
                "Flavin, Andre — which set out to reduce art to its essentials "
                "and put the object and the viewer's experience ahead of the "
                "artist's mediation. Software inherited exactly that argument: "
                "the interface should not be the thing you notice. Swiss "
                "method, American product management, a decade of design "
                "systems.",
        "composition": "A 12-column grid with real alignment and a consistent "
                "vertical rhythm; content in cards or sections of predictable "
                "width. Asymmetry where it helps scanning, symmetry where it "
                "helps comparison. Nothing overlaps, nothing bleeds, nothing "
                "surprises — the layout is infrastructure.",
        "proportion": "A gentle 1.25 scale across five steps, because product "
                "UI needs many sizes that stay close together rather than few "
                "that shout. Measure 68ch for prose, narrower in a sidebar. "
                "Spacing runs on a 4px base; radius 12px; a card's padding is "
                "always a multiple of the gutter.",
        "color": "A full slate ramp from near-black to near-white doing almost "
                "all the work, with a single blue accent for primary action "
                "and semantic green/amber/red reserved strictly for state. "
                "Saturation stays low enough that a chart's own colours are "
                "the most colourful thing on screen.",
        "light": "A soft, diffuse, single top light — enough to separate a "
                "card from its background and nothing more. Elevation is a "
                "tool for layering, not for drama: four steps at most, each "
                "meaning a different distance from the page.",
        "type": "One humanist grotesque across the whole system (Inter here) "
                "at three weights, with tabular figures everywhere numbers "
                "align. Tracking tightens slightly as size grows. If a second "
                "family appears it is a monospace for code, and it earns its "
                "place by being code.",
        "materiality": "Nothing — and that is the position. No paper, no "
                "glass, no metal; surfaces are just planes at different "
                "elevations. The honesty here is admitting a screen is a "
                "screen, which is why the style survives redesigns that "
                "skeuomorphic systems do not.",
        "motion": "Short, functional, 200ms on a standard ease. Motion "
                "explains a relationship — where a panel came from, what "
                "changed — and then gets out of the way. Nothing bounces, "
                "nothing overshoots, and anything over 300ms needs to justify "
                "the wait.",
        "imagery": "Sparse: product screenshots, abstract geometry, "
                "illustration kept to a thin consistent line. Photography is "
                "used for people and rarely for mood. Icons are a single "
                "stroke weight and sit on a 24px grid without exception.",
        "voice": "Plain, second-person, present tense: 'Connect your account.' "
                "Error messages say what happened and what to do next. No "
                "exclamation marks, no personality bolted on in microcopy — "
                "the product is a tool and the tone respects the user's time.",
        "sound": "Near-silent. A short soft tick for confirmation, a quieter "
                "one for dismissal, nothing for routine success. The absence "
                "is intentional: this is a style people have open for eight "
                "hours.",
        "space": "SaaS dashboards, admin panels, documentation, developer "
                "tools, internal software, settings screens — anywhere the "
                "interface will be used daily by someone who did not choose "
                "it and cannot escape it.",
        "kinship": "`swiss-international`'s pragmatic descendant: same grid, "
                "looser rules, a second accent allowed for state. Shares the "
                "restraint of `nordic` without the warmth, and of "
                "`editorial` without the serif. `hi-contrast` is where it goes "
                "when accessibility stops being a checkbox. Don't confuse "
                "quiet with empty — a dense dashboard is still this style.",
        "hierarchy": "Grid > typographic scale > spacing rhythm > elevation > "
                "the single accent > colour semantics. Get the spacing wrong "
                "and no palette will rescue it; get it right and almost any "
                "palette works.",
        "canon": "Study: the Material and Human Interface guidelines, GitHub "
                "Primer, Stripe and Linear's product surfaces, Tufte on "
                "data-ink, and the slate ramps in Tailwind and Radix.",
        "adaptation": "Built dark here — slate on near-black at 13:1, with the "
                "muted grey at 7:1. The light inversion is the same system "
                "with the ramp reversed and is equally canonical. Because "
                "hierarchy comes from spacing and weight rather than hue, it "
                "survives colour-blind use and forced-colours mode unchanged.",
        "era": "minimalist roots from the 1960s; the software default since c. 2014",
        "fonts": {"display": "Space Grotesk", "body": "Inter",
                  "files": ["space-grotesk-600.woff2", "inter-400.woff2"]},
        "textures": ["grain"],
        "gloss": "almost none — a 1-level sheen at most on a primary button, "
                "and only to signal that it is the thing to press. Any "
                "glassmorphism belongs to `frutiger-aero`, which is a "
                "different argument about what a screen should pretend to be.",
        "shapes": ["grid-marks", "signal-dot"],
        "patterns": ["dots", "grid"],
        "gradients": [],
        "techniques": ["container-query", "subgrid-align", "has-relational",
                       "light-dark-fn", "color-mix-theming"],
        "rules": "DO run everything off one spacing base, keep one accent for "
                "action, and use colour only for state. DON'T decorate, don't "
                "let a marketing gradient into the product surface, and don't "
                "invent a size that isn't on the scale.",
        "moves": ["Set the 4px spacing base and never break it",
                  "One blue for action; green, amber and red only for state",
                  "Separate layers with elevation, not with borders and colour",
                  "Tabular figures anywhere two numbers sit above each other"],
        "failure": "Fails by blandness when nobody makes a decision — the "
                "style tolerates restraint but punishes indifference, and an "
                "unconsidered neutral page is just grey. Also fails by "
                "creeping accents: the fifth brand colour turns a system into "
                "a swatch library.",
    },
    "hi-contrast": {
        "label": "High Contrast", "style": "hi-contrast",
        "palette": "signal-contrast",
        "vibe": "Legibility as the entire design: pure black, pure white, and "
                "a signal yellow that can be read across a car park at dusk. "
                "Not a theme so much as a floor — the version of an interface "
                "that still works when nothing else does.",
        "origins": "Takes its logic from high-visibility safety equipment, "
                "where conspicuity is regulated rather than styled: "
                "fluorescent yellow and orange are the standard colours under "
                "ISO 20471, and studies of motorcyclists found roughly a third "
                "of collisions might have been avoided by reflective or "
                "fluorescent clothing. Transfer that to software and the "
                "argument is identical — being seen is a safety property.",
        "composition": "Simple, linear, generously spaced: one column where "
                "possible, large hit areas, obvious grouping, and no layout "
                "that depends on noticing a subtle alignment. Reading order "
                "and DOM order agree, because a screen reader is a first-class "
                "user of this layout.",
        "proportion": "18px base and nothing smaller than 16px anywhere. "
                "Three sizes on a 1.5 scale so the jumps are unmistakable; "
                "borders 2px so they survive a bad monitor; targets at least "
                "44px square; focus rings 3px with a 2px offset so they never "
                "sit on top of the thing they indicate.",
        "color": "Black field, white type, one saturated signal — and every "
                "pair checked, not estimated. Colour never carries meaning "
                "alone: a state is a colour plus an icon plus a word, because "
                "a palette is useless to the eight percent of men who cannot "
                "separate two of its hues.",
        "light": "None. Shadows are unreliable at low vision and invisible in "
                "forced-colours mode, so separation comes from borders and "
                "space. If a layer matters, it gets a 2px edge rather than a "
                "blur that may not render.",
        "type": "A humanist grotesque with open apertures and unambiguous "
                "characters — the 1, l and I must be distinguishable, as must "
                "0 and O. Normal weight for body, bold for emphasis, no "
                "italics for anything long, and no letterspaced lowercase. "
                "Line length stays at 60ch so returns are easy to track.",
        "materiality": "Enamel sign, road marking, reflective tape, moulded "
                "switch. The reference objects are all things designed to be "
                "found by someone who is tired, rushed, or in bad light — "
                "which is also the honest description of most users.",
        "motion": "Minimal by default and removable entirely: everything under "
                "100ms, linear, no parallax and no autoplay. "
                "`prefers-reduced-motion` is honoured as a hard stop, not a "
                "reduction, because for some users motion is nausea rather "
                "than delight.",
        "imagery": "Pictograms over illustration, and every one paired with a "
                "label. High-contrast line work at a heavy stroke; no "
                "low-contrast decorative photography behind text, ever. If an "
                "image carries information, that information also exists as "
                "text.",
        "voice": "Short sentences, concrete verbs, plain words — the reading "
                "level is a design parameter. Instructions say what to do "
                "rather than what not to do, errors name the fix, and nothing "
                "depends on a metaphor the reader has to decode.",
        "sound": "Distinct and optional: different confirmations for success "
                "and failure so the two are not merely louder versions of each "
                "other, every one duplicated visually and in text. Nothing is "
                "audio-only, because the user may not have sound at all.",
        "space": "Government services, healthcare, transport and ticketing, "
                "emergency and safety interfaces, kiosk and field equipment, "
                "and the accessible mode of everything else — plus any product "
                "that intends to pass a WCAG audit rather than argue with one.",
        "kinship": "`swiss-international` with the aesthetics removed and the "
                "legibility kept, and the floor beneath `neutral` and `mono`. "
                "Direct opposite of `pastel`, which spends its whole contrast "
                "budget on mood. Don't confuse it with ugliness: constraint "
                "this tight is a design problem, not an excuse.",
        "hierarchy": "Contrast > target size > type size > focus visibility > "
                "reading order > everything else. Any trade that costs "
                "contrast has been lost before it was made.",
        "canon": "Study: WCAG 2.2 and the AAA 7:1 threshold, the GOV.UK Design "
                "System, ISO 20471 safety colours, Windows High Contrast and "
                "forced-colours mode, and the NHS and US Web design systems.",
        "adaptation": "White on black is 21:1 and the signal yellow clears "
                "AAA. Light mode is the same system inverted at the same "
                "ratios. It must survive 200% zoom, 400% reflow, "
                "forced-colours, and a monochrome display — and if it does, "
                "it is the one style here that is never wrong to ship.",
        "era": "safety-colour logic from the 1960s; WCAG since 1999; permanent",
        "fonts": {"display": "Archivo Black", "body": "Inter",
                  "files": ["archivo-black-400.woff2", "inter-400.woff2"]},
        "textures": ["stripes"],
        "gloss": "zero, and not as taste — a sheen lowers local contrast and "
                "can erase a glyph for a low-vision reader. Flat colour is the "
                "only finish, and the one decorative liberty is a hazard "
                "stripe used as a rule.",
        "shapes": ["signal-dot", "crossbar-arrow", "stencil-arrow"],
        "patterns": ["diagonal-stripes"],
        "gradients": [],
        "techniques": ["field-sizing-auto", "text-balance-wrap",
                       "has-relational", "popover-api"],
        "rules": "DO check every pair against AAA, pair colour with text and "
                "shape, and make focus unmissable. DON'T place text on an "
                "image, convey state by hue alone, or go below 16px for "
                "anything a person has to read.",
        "moves": ["Check every colour pair against 7:1 before shipping it",
                  "Give every state a colour, an icon and a word",
                  "Put a 3px focus ring with a 2px offset on everything",
                  "Separate layers with 2px borders rather than shadow"],
        "failure": "Fails the moment a designer 'softens' it — a grey "
                "placeholder, a thin weight, a tasteful low-contrast caption, "
                "and the one property it exists for is gone. It also fails by "
                "being treated as a toggle bolted on at the end rather than "
                "the baseline the rest is tested against.",
    },
    "mono": {
        "label": "Mono / Brutalist", "style": "mono", "palette": "mono-noir",
        "vibe": "Raw structure, visible: hard edges, no radius, a hairline "
                "grid you are meant to see, black and white with one colour "
                "used like a warning label. The page admits it is a document "
                "made of boxes and refuses to pretend otherwise.",
        "origins": "Architectural brutalism, read literally. Hans Asplund "
                "coined nybrutalism in 1950 for Villa Göth; Alison Smithson "
                "used 'new brutalism' in 1953 and stated the intention plainly "
                "— to have the structure exposed entirely, without interior "
                "finishes wherever practicable. Reyner Banham's 1955 essay "
                "tied it to béton brut and art brut, raw concrete and raw art. "
                "Web brutalism took the ethic and dropped the concrete.",
        "composition": "Boxes with visible borders, flush alignment, and "
                "deliberate collisions. The grid is exposed rather than "
                "implied — rules run to the page edge, sections butt against "
                "each other with no softening margin, and an element that "
                "overlaps does so obviously and on purpose.",
        "proportion": "Zero radius everywhere; 2px borders; a 1.333 scale "
                "across four steps. Measure runs long at 72ch because density "
                "is the point and comfort is not the brief. Gutters collapse "
                "to nothing where two blocks should read as one slab.",
        "color": "Near-black and bone white carrying everything, with one "
                "colour used sparingly and bluntly — closer to a stencilled "
                "warning than to a brand accent. No tints, no mid-greys doing "
                "diplomacy: a thing is foreground or it is background.",
        "light": "None, and the absence is the statement. Depth comes from "
                "hard offset blocks — a solid shadow with no blur, which reads "
                "as a second slab rather than as light. A soft shadow here is "
                "a finish, and finishes are what this style refuses.",
        "type": "A grotesque or a monospace set tight, with a heavy display "
                "cut (Archivo Black) for anything that shouts. Uppercase for "
                "labels, system defaults worn proudly, and no optical nicety "
                "that would smooth the page. Text may run to the edge; "
                "comfort is not owed.",
        "materiality": "Béton brut: poured concrete with the board marks left "
                "in, exposed I-beams, unpainted brick, raw steel. The "
                "digital translation is the unstyled element — the default "
                "border, the browser's own control, the visible seam where two "
                "systems meet.",
        "motion": "Instant or stepped. No easing curves, no fades: state "
                "changes snap, because an eased transition is a finish applied "
                "to a movement. Where something must move it moves in one "
                "hard increment, like a mechanical counter.",
        "imagery": "Harsh black-and-white, high-grain, halftone or dithered to "
                "one bit; screenshots left unretouched; diagrams drawn in the "
                "same 2px stroke as the borders. Nothing is colour-graded, "
                "because grading is flattery.",
        "voice": "Blunt, declarative, lowercase or caps with nothing in "
                "between. No onboarding warmth, no apology, no "
                "exclamation — the copy tells you what the thing is and lets "
                "you decide. Honesty here extends to admitting what the "
                "product does not do.",
        "sound": "Mechanical: a relay click, a key thunk, a printer step. "
                "Nothing tonal and nothing designed to feel pleasant; sound "
                "confirms that a mechanism moved and that is its whole job.",
        "space": "Portfolios and studio sites, zines and small-press "
                "publishing, developer tools that want to look unmarketed, "
                "art and music releases, and any product whose position is "
                "that it is not trying to charm you.",
        "kinship": "`swiss-international` gone dark and angry — same grid, "
                "opposite manners. Shares `hi-contrast`'s black-and-white "
                "economy with none of its duty of care, and `editorial`'s "
                "density with none of its serif courtesy. Don't confuse with "
                "lazy: brutalism is exposed structure, which requires there to "
                "be structure.",
        "hierarchy": "Structure > contrast > typography > density > the one "
                "accent. If the skeleton isn't worth exposing, this style has "
                "nothing to work with and becomes mere ugliness.",
        "canon": "Study: the Smithsons' Hunstanton School, Le Corbusier's "
                "Unité d'habitation, Goldfinger's Trellick Tower, Banham's "
                "'The New Brutalism: Ethic or Aesthetic?', brutalistwebsites, "
                "and Wim Crouwel's harder grids.",
        "adaptation": "Bone on near-black runs 17:1 and the long 72ch measure "
                "gets extra leading because reversed text needs it. Light mode "
                "is the same slab inverted — and arguably more period-correct, "
                "since the concrete it refers to is grey. Reduced motion costs "
                "nothing here: there was no motion to remove.",
        "era": "nybrutalism 1950; Banham's essay 1955; the web revival from c. 2014",
        "fonts": {"display": "Archivo Black", "body": "Space Grotesk",
                  "files": ["archivo-black-400.woff2", "space-grotesk-400.woff2"]},
        "textures": ["carbon", "halftone"],
        "gloss": "zero, as a matter of ethics rather than taste — gloss is a "
                "finish and the whole argument is that finishes conceal "
                "structure. The only permitted highlight is the white of the "
                "paper showing through a halftone.",
        "shapes": ["stencil-arrow", "grid-marks", "crossbar-arrow"],
        "patterns": ["grid", "diagonal-stripes", "noise-texture"],
        "gradients": [],
        "techniques": ["pixel-art-shadow", "stroke-text", "halftone-dots",
                       "cut-corner-button"],
        "rules": "DO expose the grid, keep every corner square, and let "
                "elements collide. DON'T round anything, don't blur a shadow, "
                "and don't ease a transition — each of those is a finish, and "
                "finishes are the thing being refused.",
        "moves": ["Square every corner and set borders to a visible 2px",
                  "Offset a hard unblurred shadow so it reads as a second slab",
                  "Run a rule or a block of text clean off the page edge",
                  "Snap state changes with no easing and no fade"],
        "failure": "Fails when it is costume — raw type over a soft gradient, "
                "or a 'brutalist' page with rounded cards underneath. Fails "
                "equally by becoming unusable: exposed structure is still "
                "structure, and a page nobody can navigate is not austere, "
                "just broken.",
    },
    # ---- dark / electric ------------------------------------------------ #
    "cyberpunk": {
        "label": "Neon / Cyberpunk", "style": "cyberpunk",
        "palette": "cyberpunk-night",
        "vibe": "Film noir with the lights replaced by signage: wet black "
                "streets, magenta and cyan bleeding into the dark, monospace "
                "everywhere, and an interface that looks like it was built by "
                "someone who did not have permission. High tech, visibly low "
                "life.",
        "origins": "The literary movement of the early 1980s — Gibson, "
                "Sterling, Blade Runner's production design — set in a "
                "near-future post-industrial dystopia rather than a galactic "
                "one, with plots turning on AI, hackers and megacorporations. "
                "Much of its atmosphere is borrowed straight from film noir, "
                "and its governing proverb is Gibson's: the street finds its "
                "own uses for things. That last part is the design brief.",
        "composition": "Dense and layered like a HUD: panels overlapping, "
                "readouts in the corners, data where a magazine would put "
                "white space. Alignment is tight and technical, but the layers "
                "are allowed to stack and occlude — the screen is a surface "
                "someone has been working on, not a page someone composed.",
        "proportion": "Small, dense type at a 15px base on a 1.333 scale, "
                "72ch measures, 16px gutters. Chrome is thin — 1px borders, "
                "hairline rules — so the glow has something precise to bloom "
                "against. Labels run uppercase with 0.04em tracking at caption "
                "size.",
        "color": "Near-black grounds — true void, not grey — carrying hot "
                "magenta and electric cyan as the primary pair, with acid "
                "green reserved for terminal states. The accents are allowed "
                "to be the only chroma on screen; everything structural is "
                "black, and nothing is pastel.",
        "light": "Everything is emissive. There is no ambient light at all: "
                "surfaces are lit only by the signs on them, so glow is the "
                "entire lighting model — tight bloom around text, a halo on "
                "focus, a dim pulse on anything live. Soft shadows are wrong "
                "here, because nothing is being lit from outside.",
        "type": "Monospace as the default voice (JetBrains Mono), because the "
                "fiction is that you are closer to the machine than you should "
                "be, with a wide geometric display face (Orbitron) for "
                "titling. Uppercase labels, tabular figures, visible cursors. "
                "No serif ever — a serif implies an institution.",
        "materiality": "Wet asphalt, scratched acrylic, CRT phosphor, "
                "anodised metal, cable looms and gaffer tape. Everything is "
                "either mass-produced and worn or hand-modified and ugly; "
                "the two states together are the texture of the genre.",
        "motion": "Fast and glitchy: 90ms steps rather than smooth curves, "
                "scanline drift, occasional RGB split on state change, text "
                "that decodes rather than fades. Motion should feel like a "
                "signal arriving through interference, never like an "
                "animation someone tuned.",
        "imagery": "Rain-lit streets, kanji and katakana signage, wireframes "
                "and point clouds, surveillance crops, exploded diagrams of "
                "hardware. People appear as silhouettes against light "
                "sources. Anything photographic gets pushed toward two "
                "channels and a lot of black.",
        "voice": "Terse, technical, slightly hostile: system output rather "
                "than copywriting. Status over reassurance — 'LINK DOWN', not "
                "'Something went wrong'. Jargon is allowed to stand "
                "unexplained, because the fiction is that you belong here.",
        "sound": "Rain and distant traffic as room tone, modem handshakes, "
                "relay clicks, a synth pad holding one chord too long. "
                "Interface sounds are short, dry and slightly clipped — "
                "a confirmation should sound like a switch, not a chime.",
        "space": "Security and network tooling, terminals and developer "
                "surfaces, game UI and overlays, music and streaming for "
                "electronic genres, hardware dashboards — anywhere looking "
                "technical is part of the value.",
        "kinship": "`vaporwave`'s harder sibling: same neon, opposite "
                "politics — vaporwave is nostalgic and ironic, cyberpunk is "
                "near-future and sincere. Shares `ultraviolet`'s dark field "
                "with more aggression and less elegance; `mono` is this style "
                "with the power cut. Don't confuse with synthwave, which is a "
                "sunset and a sports car, not a tenement and a deadline.",
        "hierarchy": "Darkness > emissive accent > monospace density > glow > "
                "glitch. The void has to be genuinely dark first; neon on "
                "charcoal is just a dark theme with a hobby.",
        "canon": "Study: Blade Runner and 2049's signage, Ghost in the Shell's "
                "interface plates, Gibson's Neuromancer, Syd Mead's concept "
                "work, and the HUDs in Deus Ex and Cyberpunk 2077.",
        "adaptation": "Pale cyan on void runs 15:1, and the 72ch measure takes "
                "extra leading because reversed text blooms. Magenta is "
                "display-only at around 4:1 — never body copy. There is no "
                "light mode: inverted, this becomes a different style "
                "entirely, so ship `neutral` instead. Reduced motion must kill "
                "the glitch, which is a seizure risk, and keep only the glow.",
        "era": "literary movement from 1982; a permanent interface dialect since",
        "fonts": {"display": "Orbitron", "body": "JetBrains Mono",
                  "files": ["orbitron-700.woff2", "jetbrains-mono-400.woff2"]},
        "textures": ["scanlines", "carbon", "grain"],
        "gloss": "low but emissive — surfaces are matte and the light comes "
                "from inside them. What reads as shine is bloom around a lit "
                "element, so a highlight only ever appears where something is "
                "switched on.",
        "shapes": ["grid-marks", "signal-dot", "crossbar-arrow"],
        "patterns": ["grid", "graph-paper", "noise-texture"],
        "gradients": ["cyber-glow"],
        "techniques": ["crt-screen", "chromatic-aberration", "hud-plate",
                       "svg-soft-glow", "scroll-scrub-sequence"],
        "rules": "DO make the black genuinely black, let the accents emit, and "
                "keep the type monospaced and dense. DON'T use a soft drop "
                "shadow, a pastel, or a serif — each one imports a politeness "
                "the genre doesn't have.",
        "moves": ["Start from true void, not charcoal, and let signs light it",
                  "Bloom the accent instead of shadowing the surface",
                  "Set labels in uppercase monospace with wide tracking",
                  "Snap state changes in steps so they read as interference"],
        "failure": "Fails as cosplay the moment the neon is decoration rather "
                "than light — a pink heading on a grey card is not this. Fails "
                "also by prettiness: cyberpunk is grimy and overloaded, and a "
                "clean, well-spaced version of it is just a dark theme with "
                "cyan buttons.",
    },
    "vaporwave": {
        "label": "Vaporwave / Y2K", "style": "vaporwave",
        "palette": "vaporwave-sunset",
        "vibe": "A shopping mall at 3am rendered on a machine from 1996: hot "
                "pink and cyan, a Greco-Roman bust, fullwidth letterforms, "
                "VHS tracking error. Nostalgic for a corporate future that was "
                "advertised and never delivered.",
        "origins": "Emerged as an ironic variant of chillwave around 2010-11 — "
                "Chuck Person's Eccojams Vol. 1, Ferraro's Far Side Virtual, "
                "and Floral Shoppe, which set the blueprint — built from "
                "chopped-and-screwed samples of smooth jazz, lounge and "
                "elevator music. Visually it pulls 1990s web design, glitch "
                "art, anime, Greco-Roman statuary, Memphis geometry and "
                "3D-rendered objects, and generally keeps its source material "
                "between Japan's 1980s boom and the dot-com crash.",
        "composition": "Centred and symmetrical in a way that feels like a "
                "default rather than a decision — the aesthetic of a template "
                "nobody customised. Objects float on a grid plane, elements "
                "are spaced too evenly, and the composition is allowed to look "
                "like a screensaver.",
        "proportion": "Display type enormous and letterspaced to 0.12em, body "
                "type small and plain beneath it — the gap between them is the "
                "joke. A 1.414 scale, 60ch measures, 2px borders. Fullwidth "
                "characters stretch a word until it stops being a word and "
                "becomes a logo.",
        "color": "Hot pink and cyan as the governing pair over a deep indigo "
                "night, with acid green and electric violet in support. "
                "Saturation stays high and the hues stay adjacent enough to "
                "vibrate. Nothing is muted and nothing is corporate — the "
                "irony only works at full intensity.",
        "light": "Sunset gradients and CRT bloom, with no physical logic "
                "whatsoever: a grid plane glows at the horizon, objects cast "
                "no shadows, and the light source is wherever the gradient "
                "says it is. Chrome reflects a sky that does not exist.",
        "type": "A geometric or grotesque display face set wide (Righteous), "
                "with fullwidth Unicode for titles and a plain system sans "
                "beneath. Japanese characters appear as texture rather than "
                "language — which is part of the critique and worth being "
                "deliberate about.",
        "materiality": "VHS tape degradation, chrome, marble, mall tile, "
                "CRT phosphor, early 3D with visible polygons. Everything "
                "looks mass-produced and slightly degraded, as though "
                "recovered from a format nobody archived properly.",
        "motion": "Slow, floating, unhurried — 600ms drifts, a bust rotating "
                "at a pace nobody asked for, scanlines rolling. Motion is "
                "ambient rather than responsive, and the signature effect is "
                "tracking error rather than easing.",
        "imagery": "Classical statuary, palm trees, early 3D renders, "
                "dolphins, Windows 95 chrome, empty malls and pools, product "
                "shots of obsolete hardware. The rule is that everything "
                "depicted was once aspirational and is now landfill.",
        "voice": "Fragmentary and affectless, often in fullwidth caps, "
                "sometimes in a language the author doesn't speak. Copy reads "
                "like advertising stripped of its product — the tone of a "
                "slogan with nothing left to sell.",
        "sound": "Slowed and reverb-drenched: lounge jazz pitched down, mall "
                "ambience, a sample looped past the point of function. "
                "Interface sounds are startup chimes from operating systems "
                "that no longer boot.",
        "space": "Music releases and cover art, streaming overlays, event "
                "pages and merch, retro-gaming and emulation, creative "
                "portfolios — anywhere the audience is in on the reference.",
        "kinship": "`cyberpunk`'s nostalgic twin — identical palette, opposite "
                "tense: one mourns a past future, the other dreads a near one. "
                "Shares `y2k-chrome`'s materials and `avant-basic`'s Memphis "
                "geometry, since vaporwave borrowed from Memphis directly. "
                "Don't confuse with synthwave, which plays the 80s straight; "
                "vaporwave is always at least partly a critique.",
        "hierarchy": "Palette > nostalgia-object > typography > glitch > "
                "layout. Composition is deliberately the least considered "
                "layer, because the style's whole posture is that someone "
                "assembled this quickly and meant it anyway.",
        "canon": "Study: Floral Shoppe's cover, Far Side Virtual, early "
                "Geocities and Windows 95 interfaces, Memphis Milano "
                "catalogues, and any mall photographed after closing.",
        "adaptation": "Near-white on indigo runs 15:1, but the neon accents "
                "sit at 3-4:1 and must stay display-only. Hero gradients here "
                "span bright blobs over a dark base, so the kit scrims them "
                "rather than hoping — text over a vaporwave gradient needs the "
                "wash. No light mode: this style is nocturnal by definition. "
                "Reduced motion removes the drift and keeps the colour.",
        "era": "music and aesthetic from c. 2010-2012; peak 2015; permanent as reference",
        "fonts": {"display": "Righteous", "body": "Space Grotesk",
                  "files": ["righteous-400.woff2", "space-grotesk-400.woff2"]},
        "textures": ["scanlines", "starfield", "grain", "mesh"],
        "gloss": "high and fake — chrome type, wet plastic, a specular "
                "highlight on a sphere that has no light to reflect. The gloss "
                "is explicitly a render artifact rather than a material "
                "property, and looking artificial is the point.",
        "shapes": ["chrome-blob", "lens-flare", "orbit-rings", "checker-wave"],
        "patterns": ["grid", "checkerboard", "noise-texture"],
        "gradients": ["sunset-warm", "purple-haze", "mesh-vibrant"],
        "techniques": ["chromatic-aberration", "crt-screen", "holographic-conic",
                       "rotating-text-ring", "turbulence-bg"],
        "rules": "DO centre things, oversize and letterspace the display type, "
                "and keep saturation at maximum. DON'T mute the palette or "
                "tidy the layout into something tasteful — restraint reads as "
                "a brand trying to borrow the look.",
        "moves": ["Set the title fullwidth and letterspaced past legibility",
                  "Float one classical or 3D object with no shadow at all",
                  "Lay a glowing horizon grid under the whole composition",
                  "Let tracking error and scanlines sit over the hero"],
        "failure": "Fails when a brand uses it sincerely — the aesthetic is "
                "about corporate emptiness, so deploying it to sell something "
                "collapses the joke. Fails also when cleaned up: a tasteful, "
                "well-aligned, slightly-pink page has removed everything that "
                "made it vaporwave.",
    },
    "nordic": {
        "label": "Nordic", "style": "nordic", "palette": "nordic-frost",
        "vibe": "Long winter light handled well: muted blue-greys, pale wood, "
                "generous space and nothing shouting. Calm without being "
                "cold, plain without being cheap — designed for a room that is "
                "dark for most of the day.",
        "origins": "Scandinavian design, which emerged in the early twentieth "
                "century and flourished through the 1950s across Denmark, "
                "Finland, Norway, Sweden and Iceland on a programme of "
                "simplicity, minimalism and functionality. Aalto in "
                "architecture and furniture, Jacobsen and Wegner in chairs, "
                "Poul Henningsen in lamps, Maija Isola in textiles; the "
                "Lunning Prize from 1951 and the Brooklyn Museum's 1954 "
                "'Design in Scandinavia' exported it. Its stated ideal was "
                "democratic: good objects at a price ordinary people pay.",
        "composition": "Calm and horizontal, with real breathing room and "
                "furniture-like proportions. Nothing is crowded and nothing is "
                "centred for ceremony; elements sit where they are useful. "
                "Negative space is treated as material, in the way an empty "
                "wall is part of a Nordic room.",
        "proportion": "A restrained 1.25 scale over four steps — this style "
                "does not raise its voice typographically either. Measure "
                "68ch, gutters 24px, radius 10px: softened but not rounded. "
                "Components are generously padded, because cramped is the one "
                "thing this aesthetic cannot be.",
        "color": "Polar night greys and slate blues with frost and snow as the "
                "light end, plus one cool accent — a glacier blue or a muted "
                "aurora green. Everything is desaturated toward grey, which is "
                "what northern daylight actually does to colour.",
        "light": "Low, soft and lateral: the light of a sun that stays near "
                "the horizon. Shadows are long, diffuse and gentle; there is "
                "no overhead glare. The reference object is a Henningsen lamp "
                "— layered shades that give light with no visible bulb and no "
                "hard edge anywhere.",
        "type": "A humanist grotesque with open shapes (Inter) at a "
                "comfortable size, with a slightly geometric display face "
                "(Sora) above. Set loose, never tight, and never fewer than "
                "the ascenders need. Hierarchy is quiet — a step in size and "
                "a step in colour, rarely weight.",
        "materiality": "Pale ash and birch, wool and linen, matte ceramic, "
                "brushed steel, unlacquered leather. Materials are honest and "
                "age visibly; nothing is coated to look like something else. "
                "A surface should look like it would be pleasant to touch.",
        "motion": "Gentle and brief — 220ms on a soft ease, small travel. "
                "Motion behaves like a well-made drawer: damped, quiet, "
                "arriving without a bounce. Nothing springs, because nothing "
                "in a Nordic interior springs.",
        "imagery": "Landscape and interior photography in flat northern light, "
                "lots of sky and snow, objects shot plainly against pale "
                "backgrounds. People are shown using things rather than posing "
                "with them. Illustration is thin-line and sparse.",
        "voice": "Plain, warm and unhurried; short sentences, no superlatives, "
                "no urgency. The tone assumes the reader is an adult who will "
                "decide in their own time — a style that would rather be "
                "trusted than clicked.",
        "sound": "Wind, water, wood, a fire somewhere else in the house. Very "
                "quiet interface sounds with soft attacks — nothing percussive "
                "and nothing bright. Silence is comfortable here rather than "
                "empty.",
        "space": "Furniture and homeware, wellness and healthcare, fintech "
                "that wants to feel safe, public services in the Nordics, "
                "productivity software with a calm posture, and sustainability "
                "brands that mean it.",
        "kinship": "Shares `neutral`'s restraint but adds warmth and a cooler "
                "palette; shares `earthy`'s honesty about materials with the "
                "colour temperature reversed. `organic-tech` is this style "
                "with the curves turned up. Don't confuse with minimalism for "
                "its own sake: Scandinavian design is about comfort and "
                "affordability, not austerity.",
        "hierarchy": "Space > light > material honesty > typography > the one "
                "cool accent. If the layout doesn't feel like a room you could "
                "stand in comfortably, adjusting the palette won't help.",
        "canon": "Study: Aalto's Paimio chair and Savoy vase, Henningsen's PH "
                "lamps, Wegner's Wishbone, Marimekko's Isola prints, the 1954 "
                "'Design in Scandinavia' catalogue, and Nordic public-service "
                "design systems.",
        "adaptation": "Snow on polar night runs 11:1 with the muted grey "
                "holding 5:1. The light inversion — frost field, slate ink — "
                "is equally canonical and arguably the summer version of the "
                "same room. Reduced motion costs little, since the motion was "
                "already small and damped.",
        "era": "early 20th century; golden age 1950s-60s; continuous since",
        "fonts": {"display": "Sora", "body": "Inter",
                  "files": ["sora-600.woff2", "inter-400.woff2"]},
        "textures": ["grain", "paper"],
        "gloss": "very low — matte ceramic and oiled wood, with a single soft "
                "sheen where a glass or steel object catches the low sun. "
                "A high-gloss surface would read as plastic, which is the one "
                "material this tradition is suspicious of.",
        "shapes": ["pebble-stack", "leaf-vein", "grid-marks"],
        "patterns": ["dots", "topographic"],
        "gradients": ["ocean-deep"],
        "techniques": ["layered-shadows", "squircle-corners", "scroll-reveal",
                       "light-dark-fn"],
        "rules": "DO give everything room, desaturate toward grey, and keep "
                "light soft and lateral. DON'T saturate, crowd, or add a "
                "second accent; and don't mistake plainness for the goal — "
                "the goal is comfort.",
        "moves": ["Pad everything generously and let the empty wall stand",
                  "Desaturate every hue toward the grey of northern daylight",
                  "Light from the side, long and soft, never from overhead",
                  "Keep one cool accent and let hierarchy come from space"],
        "failure": "Fails by turning cold — remove the warmth and it becomes "
                "`neutral` in a cardigan. Fails also as marketing shorthand: "
                "pale wood and a sans-serif is not the tradition, which was "
                "fundamentally about well-made objects being affordable.",
    },
    "earthy": {
        "label": "Earthy", "style": "earthy", "palette": "terracotta-clay",
        "vibe": "Clay, rust, olive and sand: a palette taken from fired "
                "pottery and dry landscape, set in a warm serif with plenty of "
                "room. Grounded and unhurried, with the handmade left visible "
                "rather than sanded off.",
        "origins": "Earth tones — browns, greens, greys and warm muted shades "
                "drawn from natural materials — were the palette of the 1970s "
                "and early 1980s, rising with the environmental movement as "
                "people reached for something more natural than what came "
                "before. Memphis neon displaced them in the mid-to-late "
                "eighties; they returned through craft, ceramics and "
                "sustainability branding, which now use them to signal "
                "authenticity and environmental seriousness.",
        "composition": "Relaxed and asymmetric, with organic spacing rather "
                "than a visible mathematical grid. Elements settle rather than "
                "align — a layout that feels arranged by hand. Generous "
                "margins, soft section breaks, and room for an image to sit "
                "slightly off-axis without it reading as a mistake.",
        "proportion": "A 1.25 scale over four steps at a 17px base, 66ch "
                "measure, 8px radius. Nothing is tight: padding runs loose and "
                "line spacing comfortable, because the whole posture is "
                "unhurried. Rules are soft-edged or omitted in favour of "
                "space.",
        "color": "Terracotta and rust against sand and bone, with olive and "
                "moss as the cool counterweight. Everything is muted — these "
                "are pigments mixed with grey and ochre, not hues picked off a "
                "wheel. Nothing here is fully saturated, and nothing is "
                "fluorescent.",
        "light": "Warm, low, late-afternoon: light that has travelled through "
                "dust. Shadows are soft and brown rather than grey, and the "
                "whole image sits slightly warm. The reference is a window in "
                "a room with a tiled floor at five o'clock.",
        "type": "A warm old-style serif for reading (Lora) with a characterful "
                "display cut above (Fraunces), set loose. Real italics, "
                "oldstyle figures, and a willingness to let a heading have a "
                "little personality — the type should feel like it was chosen "
                "rather than specified.",
        "materiality": "Unglazed and matte-glazed ceramic, raw linen, jute, "
                "oiled wood, hammered copper, lime plaster. Every surface has "
                "tooth; variation is a sign of the hand rather than a defect, "
                "and nothing has been polished to uniformity.",
        "motion": "Slow and soft — 300ms with an easing that settles rather "
                "than snaps. Things fade and drift a short distance. Nothing "
                "springs or bounces, because nothing made of clay does.",
        "imagery": "Still life with pottery and raw ingredients, hands "
                "working, dry landscape, textiles photographed close enough to "
                "see the weave. Natural light only. The camera lingers on "
                "texture and imperfection rather than hiding them.",
        "voice": "Warm, direct and a little plainspoken; first person is "
                "welcome. Talks about process and provenance — where it came "
                "from, who made it, how long it took — without slipping into "
                "sanctimony about it.",
        "sound": "Room tone with birds or a kettle, wood and ceramic contact "
                "sounds, acoustic instruments. Interface sounds are soft and "
                "woody, with no digital brightness anywhere in them.",
        "space": "Food and beverage, ceramics and craft retail, wellness, "
                "sustainability and agriculture brands, slow-travel and "
                "hospitality, cookbooks — anywhere provenance is part of the "
                "product.",
        "kinship": "Shares `nordic`'s material honesty at the opposite colour "
                "temperature, and `organic-tech`'s curves without the "
                "technology. Cousin of `dark-academia` through the serif and "
                "the patina, though academia is interior and nocturnal while "
                "this is outdoors at four in the afternoon. Don't confuse with "
                "rustic pastiche: the palette is muted, not dirty.",
        "hierarchy": "Palette warmth > material texture > typography > "
                "generous space > imagery. Get the muting wrong — let one hue "
                "go saturated — and the whole thing turns into autumn "
                "clip-art.",
        "canon": "Study: 1970s environmental-movement graphics, Bauhaus and "
                "mid-century studio pottery, Leach and Hamada's ceramics, "
                "Kinfolk's photography, and the branding of any serious "
                "coffee roaster.",
        "adaptation": "Espresso on sand runs 9:1, though the muted secondary "
                "sits near 3.6:1 and should be darkened before it carries "
                "text. The dark inversion — bone type on deep clay — works and "
                "keeps the warmth, which matters, since a cold dark mode would "
                "break the whole premise.",
        "era": "palette of the 1970s-early 80s; revived through craft from c. 2015",
        "fonts": {"display": "Fraunces", "body": "Lora",
                  "files": ["fraunces-600.woff2", "lora-400.woff2"]},
        "textures": ["paper", "grain", "terrazzo"],
        "gloss": "almost none — the sheen of a glazed rim on an otherwise "
                "matte pot. Where gloss appears it is partial and uneven, "
                "because a kiln does not produce a uniform finish and "
                "pretending otherwise loses the handmade claim.",
        "shapes": ["pebble-stack", "leaf-vein", "blob-cell"],
        "patterns": ["noise-texture", "topographic"],
        "gradients": ["gold-hour"],
        "techniques": ["grain-overlay", "shape-outside-wrap", "scroll-reveal",
                       "dropcap-initial-letter"],
        "rules": "DO mute every hue toward ochre or grey, keep light warm and "
                "low, and leave texture visible. DON'T saturate, don't use a "
                "cool grey, and don't sand the imperfection out — uniformity "
                "is what this style is reacting against.",
        "moves": ["Mute every hue with grey or ochre before using it",
                  "Set a warm serif loose, with real italics doing work",
                  "Let an image sit slightly off-axis and leave it there",
                  "Keep the texture visible at the scale it is actually seen"],
        "failure": "Fails by saturation — one pure orange and the clay becomes "
                "Halloween. Fails equally by over-polish: the appeal rests on "
                "visible making, so a perfectly uniform surface reads as a "
                "stock photo of craft rather than the thing itself.",
    },
    # ---- tonal modes ------------------------------------------------------ #
    "pastel": {
        "label": "Pastel", "style": "pastel", "palette": "pastel-dream",
        "vibe": "High value, low saturation, and air: lilac, butter, mint and "
                "baby blue on a blush field, with soft corners and nothing "
                "with a hard edge. Reads as gentle and a little nostalgic — "
                "an interface that is trying not to raise anyone's pulse.",
        "origins": "A colour family before it was a style: pastels sit high "
                "in value and low to medium in saturation, and take their "
                "name from the drawing medium, whose sticks were historically "
                "less saturated than paints made from the same pigment. The "
                "effect is documented rather than fashionable — pastels are "
                "used in healthcare to reduce anxiety and in classrooms to "
                "help concentration, which is why the palette keeps returning "
                "whenever software decides it has been shouting.",
        "composition": "Open and airy with large soft shapes, rounded cards "
                "and plenty of gap. Nothing is dense; the layout is allowed to "
                "be a little sparse because crowding destroys the calm the "
                "palette is doing all this work to produce. Centred headings "
                "are acceptable here in a way they are not elsewhere.",
        "proportion": "A gentle 1.25 scale over four steps, 62ch measure, "
                "20px radius and very generous padding. Everything is "
                "slightly larger and slightly further apart than strictly "
                "necessary, which is the mechanism by which the style feels "
                "unhurried rather than merely pale.",
        "color": "Blush, lilac, mint, periwinkle, peach and butter, all held "
                "near the same high value so none of them dominates — the "
                "palette is a chord, not a hierarchy. The risk is structural: "
                "when everything is light, contrast has to be bought back "
                "deliberately in the text colours.",
        "light": "Diffuse and shadowless, like an overcast morning through a "
                "net curtain. Shadows are wide, soft and tinted with the hue "
                "beneath them rather than grey. No hard light anywhere — a "
                "crisp shadow would introduce the drama the style is "
                "avoiding.",
        "type": "A rounded geometric sans (Quicksand) with a friendly "
                "companion (Poppins) above, set loose and never heavy. "
                "Weights stay at 400 and 600; a black weight would break the "
                "softness. Letterforms with circular bowls do most of the "
                "work of making the thing feel kind.",
        "materiality": "Matte paper, sugar paper, frosted acrylic, soft "
                "cotton, macaron glaze. Surfaces are smooth and slightly "
                "powdery — the tactile reference is chalk rather than plastic, "
                "which is what keeps the palette from reading as childish.",
        "motion": "Slow and floating: 300ms with a soft settle, small "
                "distances, gentle scale rather than translation. Nothing "
                "arrives abruptly. Motion here should feel like something "
                "drifting down rather than snapping into place.",
        "imagery": "Soft-focus photography in flat light, simple rounded "
                "illustration, gradient blobs, nothing high-contrast. Subjects "
                "are shot against pale grounds with no deep shadow, and "
                "anything with a hard black in it will fight the whole page.",
        "voice": "Warm, encouraging and low-pressure; short friendly "
                "sentences without exclamation-mark enthusiasm. The tone "
                "reassures rather than persuades, which suits the contexts "
                "the palette is clinically used in.",
        "sound": "Soft mallets, felt piano, gentle pads with slow attacks. "
                "Nothing percussive or bright; confirmations are a quiet "
                "rounded tone. The sound design has the same brief as the "
                "colour — lower the heart rate.",
        "space": "Wellness and mental-health products, children's and "
                "education software, healthcare onboarding, beauty and "
                "lifestyle, journalling and habit apps — anywhere the user "
                "may arrive anxious.",
        "kinship": "`frutiger-aero` with the gloss removed and the optimism "
                "kept. The exact inverse of `hi-contrast`, which spends its "
                "contrast budget on legibility where this spends it on mood — "
                "and the tension between those two is this style's central "
                "problem. Cousin of `avant-basic`, which uses similar hues at "
                "full volume. Don't confuse pale with weak: this is a "
                "deliberate low-arousal palette.",
        "hierarchy": "Value range > spacing > soft form > typography > "
                "accent. Because the hues are nearly equal in weight, "
                "hierarchy has to come from space and size rather than "
                "colour — which is the discipline most pastel designs skip.",
        "canon": "Study: colour-theory treatments of value and saturation, "
                "healthcare and paediatric interior palettes, Wes Anderson's "
                "production design, Japanese stationery, and macaron "
                "photography done properly.",
        "adaptation": "This is the style most likely to fail an audit: the "
                "plum text holds 8:1 on blush, but the muted secondary sits "
                "near 4:1 and needs darkening before it carries anything. "
                "Accents are decorative, never text. A dark mode means deep "
                "plum grounds with the pastels as accents — the same chord "
                "played low.",
        "era": "colour family long-standing; a UI default in waves since c. 2016",
        "fonts": {"display": "Poppins", "body": "Quicksand",
                  "files": ["poppins-600.woff2", "quicksand-400.woff2"]},
        "textures": ["grain", "mesh"],
        "gloss": "soft and low — a 2-level sheen like the glaze on a macaron: "
                "present enough to suggest a surface, far too diffuse to "
                "produce a highlight. Chrome or wet gloss would snap the "
                "whole mood.",
        "shapes": ["blob-cell", "bloom-flower", "gloss-orb"],
        "patterns": ["dots", "blob"],
        "gradients": ["mesh-pastel", "cotton-candy", "aurora", "peachy"],
        "techniques": ["aurora-blur", "squircle-corners", "gooey",
                       "layered-shadows"],
        "rules": "DO keep every hue at the same high value, buy contrast back "
                "in the text, and give everything room. DON'T let an accent "
                "carry text, don't introduce a hard black, and don't crowd — "
                "a dense pastel layout is just washed out.",
        "moves": ["Hold every hue at the same value so none dominates",
                  "Darken the text until it clears AA, then stop adjusting",
                  "Round the corners and widen the gaps past comfortable",
                  "Tint the shadow with the hue beneath it, never grey"],
        "failure": "Fails accessibility first and hardest — pale on pale is "
                "the single most common way this style ships broken. Fails "
                "aesthetically when it goes saccharine: without the "
                "discipline of equal values and real text contrast it stops "
                "reading as calm and starts reading as a nursery.",
    },
    "jewel": {
        "label": "Jewel", "style": "jewel", "palette": "jewel-royal",
        "vibe": "Deep saturated colour over dark grounds: emerald, sapphire, "
                "garnet and old gold, lit like a display case. Luxurious "
                "without glitter — the richness comes from pigment depth "
                "rather than from shine.",
        "origins": "A colourist's position rather than a movement. Jewel "
                "tones are shades: a hue mixed toward black, which deepens it "
                "while reducing chroma, so they stay saturated without "
                "becoming bright. The cultural weight is older — Tyrian "
                "purple was ruinously expensive in antiquity, which is "
                "precisely why Roman and Byzantine emperors wore it, and deep "
                "colour has signalled cost ever since. Stained glass, "
                "lacquer, enamel and velvet all trade on the same effect.",
        "composition": "Formal and generously margined, with a clear centre "
                "of attention — a composition that behaves like a vitrine. "
                "Symmetry is used where it adds ceremony; elements are given "
                "space around them the way an object in a case is, so that "
                "isolation reads as value.",
        "proportion": "A 1.414 scale over four steps at a 17px base, 66ch "
                "measure, 28px gutters. Margins are wide and deliberate. "
                "Metallic rules stay hairline — thick gold is costume, thin "
                "gold is jewellery, and the difference is about one pixel.",
        "color": "Deep green, deep blue and oxblood over near-black, with "
                "aged brass as the only metallic. Every hue is a shade rather "
                "than a tint — darkened, never greyed — so the colour stays "
                "rich at low lightness. Two accents at most, and gold counts "
                "as one of them.",
        "light": "Directional and warm, like a single spot in a dark room: "
                "one side of an object lit, the other falling into the "
                "ground. Highlights are small and specular. The whole image "
                "sits dark so the lit parts can be the subject.",
        "type": "A high-contrast serif with real thick-thin modulation "
                "(Playfair Display) over a warm text face (Fraunces), with "
                "small caps for labels. The serif's contrast is doing the "
                "same job as the palette — depth through range rather than "
                "through weight.",
        "materiality": "Velvet, lacquer, enamel, stained glass, polished "
                "stone, aged brass. Surfaces are deep rather than shiny: the "
                "reference is light going into a material and coming back "
                "changed, which is what makes a gemstone look different from "
                "a sequin.",
        "motion": "Slow and weighted — 400ms on a long settle, small travel, "
                "a sheen that passes rather than flashes. Everything moves as "
                "though it has mass. Nothing is quick, because haste reads as "
                "cheap in this register.",
        "imagery": "Dark-ground still life, chiaroscuro product photography, "
                "textiles and stones shot close, architectural detail in low "
                "light. The background is usually darker than the subject and "
                "often falls off to black entirely.",
        "voice": "Measured and confident, slightly formal, never hurried. "
                "Short declarative sentences with no superlatives — the copy "
                "assumes the quality is evident and does not argue for it. "
                "Urgency and discounting both break the register instantly.",
        "sound": "Low strings, a struck singing bowl, the soft close of a "
                "well-made box. Interface sounds are warm, low and brief — "
                "the audio equivalent of weight.",
        "space": "Luxury retail and jewellery, spirits and fine dining, "
                "premium hospitality, private banking and members' services, "
                "theatre and opera, and any product whose argument is that it "
                "costs more for a reason.",
        "kinship": "Shares `golden-archive`'s dark ground and metallic, "
                "though the archive is cosmic and institutional where this is "
                "material and commercial. Cousin of `dark-academia` through "
                "the serif and the low light, minus the clutter and the "
                "melancholy. `art-deco` is this palette given geometry. Don't "
                "confuse with `cyberpunk` dark: nothing here emits.",
        "hierarchy": "Depth of colour > directional light > the serif's "
                "contrast > space around objects > the metallic. If the "
                "colours are bright rather than deep, no amount of gold rule "
                "will buy back the richness.",
        "canon": "Study: Dutch golden-age still life, stained glass at "
                "Chartres, Cartier and Asprey's identities, Fortuny and "
                "Venetian velvets, and the colour plates in any good book on "
                "lacquer.",
        "adaptation": "Cream on navy runs 13:1 and reversed text takes the "
                "extra leading it needs. Brass is display-only at around "
                "4:1 — a gold caption is a legibility bug wearing a nice "
                "suit. A light mode exists as cream grounds with jewel "
                "accents, though it loses the vitrine effect and becomes a "
                "different, gentler style.",
        "era": "pigment economics from antiquity; a continuous luxury register since",
        "fonts": {"display": "Playfair Display", "body": "Fraunces",
                  "files": ["playfair-display-700.woff2", "fraunces-400.woff2"]},
        "textures": ["grain", "brushed"],
        "gloss": "moderate and deep — lacquer rather than chrome. Light "
                "should look as though it entered the surface and returned "
                "slightly coloured, so highlights are small, warm and few. A "
                "broad white specular reads as plastic and undoes the whole "
                "material claim.",
        "shapes": ["gold-disk", "stepped-frame", "laurel-corner"],
        "patterns": ["noise-texture", "topographic"],
        "gradients": ["royal-jewel", "forest-mist"],
        "techniques": ["spotlight-hover", "sheen-sweep", "gradient-border-mask",
                       "emboss-letterpress"],
        "rules": "DO darken hues rather than greying them, light from one "
                "direction, and keep the metallic hairline. DON'T brighten, "
                "don't add glitter, and don't let gold carry body text — "
                "depth is the effect, not sparkle.",
        "moves": ["Shade every hue toward black, never toward grey",
                  "Light one side only and let the rest fall to the ground",
                  "Keep the metallic to hairline rules and small marks",
                  "Give the hero object vitrine space and nothing else nearby"],
        "failure": "Fails by brightness and by glitter — a saturated bright "
                "green with a gold gradient is a casino, not a jeweller. "
                "Fails also by over-application: the richness depends on "
                "restraint and darkness, so a page where everything is deep "
                "and gold has no hierarchy left at all.",
    },
    "ultraviolet": {
        "label": "Ultraviolet", "style": "ultraviolet",
        "palette": "ultraviolet-bloom",
        "vibe": "Indigo depth with violet and electric blue blooming out of "
                "it: the short end of the spectrum, treated as a mood. Dark "
                "but not grim, synthetic but not neon — closer to a nebula "
                "than to a nightclub.",
        "origins": "Violet is the shortest visible wavelength, roughly 380 to "
                "450 nanometres, and one of the seven colours Newton named "
                "when he divided the spectrum in 1672. It is a spectral "
                "colour in a way purple is not — purple is a mixture, violet "
                "is a single wavelength — which is why screens render it "
                "slightly beyond what pigment can do. Historically it carried "
                "Tyrian purple's expense and the robes of emperors, bishops "
                "and professors; one European study found violet is the "
                "colour most associated with extravagance, individualism and "
                "ambiguity, which is a fair description of how it behaves in "
                "an interface.",
        "composition": "Spacious and vertical, built around a glowing focal "
                "point with everything else receding into the field. Layers "
                "are separated by luminosity rather than by borders. The "
                "layout breathes — crowding kills the sense of depth the "
                "palette exists to create.",
        "proportion": "A 1.333 scale over four steps, 68ch measure, 24px "
                "gutters, 12px radius. Headings can run large because the "
                "dark field will carry them. Borders stay at 1px: structure "
                "should be felt rather than drawn, with glow doing the "
                "separating.",
        "color": "Deep indigo and near-black violet as the field, with "
                "electric violet, periwinkle and a cool magenta blooming "
                "through it. Saturation is high but lightness stays low "
                "except at the focal point — the effect depends on most of "
                "the screen staying dark.",
        "light": "Emissive and volumetric: large soft glows behind content, "
                "as though light were passing through a medium rather than "
                "falling on a surface. No hard shadows and no single source — "
                "the field itself is faintly luminous, the way a nebula is.",
        "type": "A geometric sans with generous counters (Sora) above a "
                "neutral grotesque (Space Grotesk), set at normal tracking. "
                "The type stays plain on purpose: when the background is "
                "doing this much, a characterful typeface competes and both "
                "lose.",
        "materiality": "Nothing solid — ionised gas, blacklight, dyed "
                "acrylic, deep-dyed velvet seen under UV. Surfaces are "
                "translucent rather than reflective, and depth comes from "
                "layers of light rather than from texture.",
        "motion": "Slow drifts and long fades — 400ms, easing out over a "
                "distance, with ambient movement in the background that never "
                "resolves. Glows pulse slowly rather than flashing. Motion "
                "should feel atmospheric, like weather in the field.",
        "imagery": "Astrophotography, long exposures, light through smoke, "
                "macro of iridescent surfaces, abstract volumetric renders. "
                "Nothing brightly lit, nothing with a hard edge, and almost "
                "nothing with a horizon.",
        "voice": "Confident and slightly elevated, favouring the abstract "
                "noun — vision, signal, depth. It suits products making a "
                "claim about intelligence or scale, and it needs watching: "
                "the register slides into vagueness faster than any other "
                "style here.",
        "sound": "Deep pads, long reverb tails, sub-bass that is felt rather "
                "than heard, a single bell held and allowed to decay. "
                "Interface sounds are soft and slightly detuned.",
        "space": "AI and data products, music and audio tools, crypto and "
                "fintech with a futurist posture, conference and launch "
                "identities, premium dark-mode marketing sites.",
        "kinship": "`cyberpunk` without the grime and the hostility — same "
                "darkness, but atmospheric rather than dystopian. Shares "
                "`golden-archive`'s cosmic scale with violet in place of gold, "
                "and `jewel`'s depth with light instead of pigment. Don't "
                "confuse with `vaporwave`: there is no irony in this one, "
                "which is both its strength and its risk.",
        "hierarchy": "Darkness of the field > the glow > space > typography > "
                "accent. The field must be genuinely dark and genuinely "
                "indigo; violet on grey is a tinted dark theme and reads as "
                "one.",
        "canon": "Study: Hubble and Webb imagery, Pantone's 2018 Ultra "
                "Violet, James Turrell's light installations, Blade Runner "
                "2049's interiors, and the dark-mode launch pages of the "
                "last few years of AI products.",
        "adaptation": "Lavender-white on indigo runs 15:1, and reversed text "
                "at a 68ch measure takes the leading step the computation "
                "already adds. The violet accent clears AA for large text "
                "only. There is no good light mode — inverted, the glow has "
                "nothing to glow against — so pair it with `neutral` rather "
                "than inverting it.",
        "era": "spectral since Newton 1672; the dominant dark-mode register since c. 2018",
        "fonts": {"display": "Sora", "body": "Space Grotesk",
                  "files": ["sora-600.woff2", "space-grotesk-400.woff2"]},
        "textures": ["starfield", "mesh", "grain"],
        "gloss": "moderate but emissive — nothing reflects, things glow. "
                "A highlight means a light source behind the surface rather "
                "than a lamp in front of it, so sheen is soft, wide and "
                "coloured rather than white.",
        "shapes": ["constellation-path", "gold-disk", "orbit-rings"],
        "patterns": ["noise-texture", "dots"],
        "gradients": ["ultraviolet-nebula"],
        "techniques": ["aurora-blur", "svg-soft-glow", "mesh-gradient-svg",
                       "oklch-gradients", "scroll-reveal"],
        "rules": "DO keep the field dark and indigo, separate layers with "
                "glow, and leave the typography plain. DON'T add a warm "
                "accent, don't flatten the field to grey, and don't let the "
                "copy drift into atmosphere with no claim in it.",
        "moves": ["Keep the field deep indigo and let most of it stay dark",
                  "Separate layers with volumetric glow instead of borders",
                  "Place one bloom behind the focal element and nothing else",
                  "Set plain type and let the background carry the character"],
        "failure": "Fails by becoming generic — this is the most imitated "
                "dark register in software, and without a specific idea "
                "underneath it reads as a template. Fails technically when "
                "the field lightens toward grey, at which point the glow has "
                "nothing to bloom against and the depth collapses.",
    },
    "ember": {
        "label": "Ember", "style": "ember", "palette": "ember-forge",
        "vibe": "A dark room with a fire in it: near-black browns carrying "
                "orange and amber heat, warm shadows, and light that comes "
                "from one low source. A dark theme that feels inhabited "
                "rather than switched off.",
        "origins": "Not a historical movement but a deliberate correction — "
                "most dark interfaces are built on blue-grey, which reads as "
                "clinical and makes long sessions feel colder than they are. "
                "This one takes its reference from combustion: the forge, the "
                "hearth, the kiln, where everything visible is lit by the "
                "work itself. The colour logic is literal, since a heated "
                "material really does run from deep red through orange to "
                "yellow-white, and that ramp is the palette.",
        "composition": "Grounded and bottom-weighted, with warmth "
                "concentrated where the attention should be and the edges "
                "falling away into dark. Generous margins, a single clear "
                "focus, and a layout that behaves like a room with one lamp "
                "rather than a page with many panels.",
        "proportion": "A 1.333 scale over four steps at 16px, 68ch measure, "
                "24px gutters, 10px radius. Nothing is cramped: the dark "
                "ground swallows tight spacing and makes a dense layout read "
                "as muddy, so padding runs a step looser than it would on a "
                "light field.",
        "color": "Charred brown and near-black as the ground — warm, never "
                "blue — with the heat ramp from deep rust through orange to "
                "amber doing all the accent work. Cool colours are excluded "
                "on principle: a single blue in here reads as a bug report.",
        "light": "One low warm source, falling off fast. Glow is tight around "
                "hot elements and the rest of the field sits genuinely dark. "
                "Shadows are warm brown rather than neutral grey, which is "
                "the detail that separates this from an ordinary dark theme.",
        "type": "A clean humanist sans for text (DM Sans) under a condensed "
                "display face (Bebas Neue) for headings — industrial signage "
                "rather than decoration. Heading weight is heavy, text weight "
                "is normal, and the contrast between them carries hierarchy "
                "without any colour change.",
        "materiality": "Forged and blackened steel, firebrick, cast iron, "
                "charcoal, leather apron, soot on stone. Surfaces are matte "
                "and slightly rough; what shines is hot metal, and it shines "
                "because of its temperature rather than its finish.",
        "motion": "Warm and organic — 350ms with a soft settle, plus slow "
                "ambient flicker on anything glowing, kept under about five "
                "percent so it reads as a flame and not as a fault. Nothing "
                "snaps; heat does not move in steps.",
        "imagery": "Low-light process photography — metal being worked, "
                "sparks, kilns, hands and tools — shot warm with deep "
                "shadows. Subjects are lit by the thing they are making. No "
                "flat studio lighting anywhere.",
        "voice": "Direct, physical and a little blunt, with verbs that "
                "describe making: forge, temper, cut, finish. Confident "
                "without the luxury register — this is craft that is proud of "
                "effort rather than of price.",
        "sound": "Fire, bellows, hammer on anvil, the hiss of a quench. "
                "Interface sounds are low and warm with a soft attack; "
                "nothing bright or digital survives contact with this "
                "palette.",
        "space": "Developer tools that want warmth, maker and workshop "
                "brands, barbecue and coffee roasting, gaming and streaming "
                "overlays, fitness and strength training, and any dark "
                "product tired of looking like a terminal.",
        "kinship": "The warm answer to `cyberpunk` and `ultraviolet`, which "
                "are both cool and emissive; shares `earthy`'s pigment family "
                "seen at night. `golden-archive` is this palette cooled and "
                "sent to a museum. Don't confuse with a red error state — "
                "here the orange is the light source, not a warning.",
        "hierarchy": "Warmth of the ground > the single light source > the "
                "heat ramp > typography > space. If the dark is blue rather "
                "than brown, everything above it fails and the page becomes "
                "an ordinary dark theme with orange buttons.",
        "canon": "Study: forge and foundry photography, Rembrandt's lit "
                "interiors, blackbody colour temperature charts, Japanese "
                "sumi-e firelight, and the warmer end of terminal themes like "
                "Gruvbox.",
        "adaptation": "Warm white on charred brown runs 14:1, with the heat "
                "accents clearing AA for large text and small amber marks. "
                "Keep the brown warm when darkening further. There is no "
                "faithful light mode — the premise is a light source in "
                "darkness — so ship `earthy` as the daylight companion, since "
                "it is the same pigment family at noon.",
        "era": "a deliberate warm-dark register; current in tooling since c. 2016",
        "fonts": {"display": "Bebas Neue", "body": "DM Sans",
                  "files": ["bebas-neue-400.woff2", "dm-sans-400.woff2"]},
        "textures": ["grain", "carbon", "brushed"],
        "gloss": "low and hot — matte everywhere except where something is "
                "glowing, and there the brightness is temperature rather than "
                "reflection. A cool specular highlight would imply a lamp in "
                "the room, which contradicts the single-source premise.",
        "shapes": ["flame-line", "burst-sticker", "stepped-frame"],
        "patterns": ["noise-texture", "diagonal-stripes"],
        "gradients": ["ember-heat"],
        "techniques": ["svg-soft-glow", "grain-overlay", "spotlight-hover",
                       "layered-shadows"],
        "rules": "DO keep the dark warm and brown, light from one low source, "
                "and run accents along the heat ramp. DON'T introduce a cool "
                "hue, don't use neutral grey shadows, and don't let the "
                "orange read as an error colour.",
        "moves": ["Build the ground from warm brown-black, never blue-black",
                  "Light from one low source and let the edges fall away",
                  "Run every accent along the rust-orange-amber heat ramp",
                  "Tint shadows warm and flicker the glow under five percent"],
        "failure": "Fails the moment a cool colour enters — one blue link and "
                "the fire goes out. Fails also by over-lighting: if the whole "
                "field glows there is no darkness for the heat to sit in, and "
                "the result is an orange page rather than a lit room.",
    },
}


# --------------------------------------------------------------------------- #
#  SHAPES — signature SVG motifs per profile (the 'missing shapes' index).
#  All use currentColor so they inherit whatever token you set; pattern tiles
#  note their intended repeat. `assets shapes [query]`, `assets show <id>`.
# --------------------------------------------------------------------------- #

SHAPES: dict[str, dict] = {
    # ---- avant basic ---------------------------------------------------- #
    "squiggle": {"profile": "avant-basic", "tags": ["wavy", "line", "groovy"],
        "svg": """<svg viewBox="0 0 120 40" xmlns="http://www.w3.org/2000/svg">
  <path d="M4 20 Q14 4 24 20 T44 20 T64 20 T84 20 T104 20 T116 20"
        fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>
</svg>"""},
    "daisy": {"profile": "avant-basic", "tags": ["flower", "retro", "70s"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor">
    <ellipse cx="50" cy="18" rx="13" ry="19"/><ellipse cx="50" cy="82" rx="13" ry="19"/>
    <ellipse cx="18" cy="50" rx="19" ry="13"/><ellipse cx="82" cy="50" rx="19" ry="13"/>
    <ellipse cx="27" cy="27" rx="15" ry="15"/><ellipse cx="73" cy="27" rx="15" ry="15"/>
    <ellipse cx="27" cy="73" rx="15" ry="15"/><ellipse cx="73" cy="73" rx="15" ry="15"/>
  </g><circle cx="50" cy="50" r="16" fill="currentColor" opacity=".35"/>
</svg>"""},
    "checker-wave": {"profile": "avant-basic",
        "tags": ["checkerboard", "warped", "pattern-tile"],
        "svg": """<svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor"><path d="M0 0h20v18H0z"/><path d="M40 2h20v16H40z"/>
  <path d="M20 18h20v16H20z"/><path d="M60 18h20v18H60z"/>
  <path d="M0 34h20v18H0z"/><path d="M40 36h20v16H40z"/>
  <path d="M20 52h20v16H20z"/><path d="M60 54h20v18H60z"/></g>
</svg>"""},
    "diamond-star": {"profile": "avant-basic", "tags": ["sparkle", "star", "y2k"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 2 C55 35 65 45 98 50 C65 55 55 65 50 98 C45 65 35 55 2 50 C35 45 45 35 50 2Z"
        fill="currentColor"/>
</svg>"""},
    "arch-window": {"profile": "avant-basic", "tags": ["arch", "window", "frame"],
        "svg": """<svg viewBox="0 0 80 110" xmlns="http://www.w3.org/2000/svg">
  <path d="M8 102 V44 A32 32 0 0 1 72 44 V102 Z" fill="none"
        stroke="currentColor" stroke-width="7"/>
  <path d="M24 102 V52 A16 16 0 0 1 56 52 V102" fill="currentColor" opacity=".3"/>
</svg>"""},
    # ---- organic tech ---------------------------------------------------- #
    "blob-cell": {"profile": "organic-tech", "tags": ["blob", "cell", "organic"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 6 C74 4 96 22 94 48 C92 76 74 96 48 94 C22 92 4 74 6 48 C8 24 26 8 50 6Z"
        fill="currentColor" opacity=".85"/>
  <path d="M52 26 C66 26 76 36 75 50 C74 66 64 76 50 75 C36 74 26 64 27 50 C28 36 38 26 52 26Z"
        fill="currentColor" opacity=".35"/>
</svg>"""},
    "pebble-stack": {"profile": "organic-tech", "tags": ["pebble", "stone", "zen"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="50" cy="82" rx="36" ry="14" fill="currentColor" opacity=".9"/>
  <ellipse cx="48" cy="58" rx="28" ry="12" fill="currentColor" opacity=".65"/>
  <ellipse cx="52" cy="38" rx="20" ry="10" fill="currentColor" opacity=".45"/>
  <ellipse cx="50" cy="22" rx="12" ry="7" fill="currentColor" opacity=".3"/>
</svg>"""},
    "leaf-vein": {"profile": "organic-tech", "tags": ["leaf", "nature", "line"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 96 C20 70 20 34 50 4 C80 34 80 70 50 96Z" fill="currentColor" opacity=".25"/>
  <path d="M50 90 V10 M50 70 C40 64 34 56 32 44 M50 70 C60 64 66 56 68 44
           M50 46 C43 42 39 36 38 28 M50 46 C57 42 61 36 62 28"
        fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
</svg>"""},
    # ---- high fashion ---------------------------------------------------- #
    "hairline-frame": {"profile": "high-fashion",
        "tags": ["frame", "editorial", "border"],
        "svg": """<svg viewBox="0 0 120 160" xmlns="http://www.w3.org/2000/svg">
  <rect x="6" y="6" width="108" height="148" fill="none" stroke="currentColor" stroke-width="1"/>
  <rect x="12" y="12" width="96" height="136" fill="none" stroke="currentColor" stroke-width=".5"/>
</svg>"""},
    "editorial-rule": {"profile": "high-fashion",
        "tags": ["rule", "divider", "masthead"],
        "svg": """<svg viewBox="0 0 200 20" xmlns="http://www.w3.org/2000/svg">
  <path d="M4 10 H88 M112 10 H196" stroke="currentColor" stroke-width="1"/>
  <path d="M100 3 L107 10 L100 17 L93 10 Z" fill="currentColor"/>
</svg>"""},
    # ---- skate culture --------------------------------------------------- #
    "burst-sticker": {"profile": "skate-culture",
        "tags": ["burst", "sticker", "price-tag"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 4 L58 22 L76 12 L74 32 L94 32 L80 46 L96 58 L76 62 L82 82 L62 76 L58 96
           L48 78 L32 92 L32 70 L12 72 L24 56 L6 46 L26 40 L18 20 L38 26 Z"
        fill="currentColor"/>
  <circle cx="51" cy="51" r="24" fill="none" stroke="#fff" stroke-width="4" opacity=".9"/>
</svg>"""},
    "flame-line": {"profile": "skate-culture", "tags": ["flame", "fire", "hot"],
        "svg": """<svg viewBox="0 0 120 60" xmlns="http://www.w3.org/2000/svg">
  <path d="M4 56 C24 50 20 34 34 30 C30 42 44 44 48 32 C50 42 60 44 64 30
           C68 42 80 40 82 26 C88 38 100 36 102 20 C110 32 116 28 116 14
           C118 34 108 56 84 56 Z" fill="currentColor"/>
</svg>"""},
    "stencil-arrow": {"profile": "skate-culture",
        "tags": ["arrow", "stencil", "spray"],
        "svg": """<svg viewBox="0 0 120 70" xmlns="http://www.w3.org/2000/svg">
  <path d="M6 26 H52 V24 H6 Z M6 46 H52 V44 H6 Z M6 26 V44 H10 V26 Z M48 26 V44 H52 V26 Z"
        fill="currentColor"/>
  <path d="M58 12 L114 35 L58 58 L70 35 Z" fill="currentColor"/>
</svg>"""},
    # ---- mosaic ----------------------------------------------------------- #
    "terrazzo-chips": {"profile": "mosaic",
        "tags": ["terrazzo", "chips", "pattern-tile"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor"><path d="M14 12 L30 8 L34 22 L20 28 Z"/>
  <path d="M62 6 L76 14 L70 26 L58 20 Z" opacity=".7"/>
  <path d="M84 44 L96 52 L88 64 L78 56 Z"/>
  <path d="M38 40 L54 36 L58 52 L44 58 Z" opacity=".5"/>
  <path d="M10 62 L24 58 L28 72 L14 78 Z" opacity=".8"/>
  <path d="M52 72 L68 68 L72 84 L56 90 Z" opacity=".6"/>
  <path d="M30 86 L40 82 L44 92 L34 96 Z"/></g>
</svg>"""},
    "trencadis-pane": {"profile": "mosaic",
        "tags": ["gaudi", "crackle", "stained-glass"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor"><path d="M4 4 L44 8 L36 40 L6 34 Z" opacity=".85"/>
  <path d="M48 6 L96 4 L92 30 L42 42 Z" opacity=".55"/>
  <path d="M8 38 L34 44 L28 70 L4 64 Z" opacity=".6"/>
  <path d="M38 46 L88 34 L94 62 L46 72 Z" opacity=".9"/>
  <path d="M6 68 L26 74 L22 96 L4 94 Z" opacity=".5"/>
  <path d="M30 76 L92 66 L96 96 L28 96 Z" opacity=".7"/></g>
</svg>"""},
    "tessera-band": {"profile": "mosaic", "tags": ["tiles", "band", "border"],
        "svg": """<svg viewBox="0 0 160 24" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor">
    <rect x="2" y="4" width="16" height="16" rx="2"/><rect x="22" y="4" width="16" height="16" rx="2" opacity=".6"/>
    <rect x="42" y="4" width="16" height="16" rx="2" opacity=".85"/><rect x="62" y="4" width="16" height="16" rx="2" opacity=".45"/>
    <rect x="82" y="4" width="16" height="16" rx="2" opacity=".7"/><rect x="102" y="4" width="16" height="16" rx="2"/>
    <rect x="122" y="4" width="16" height="16" rx="2" opacity=".55"/><rect x="142" y="4" width="16" height="16" rx="2" opacity=".8"/>
  </g>
</svg>"""},
    # ---- art deco --------------------------------------------------------- #
    "sunburst": {"profile": "art-deco", "tags": ["rays", "sun", "gatsby"],
        "svg": """<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
  <g stroke="currentColor" fill="none">
    <path d="M100 96 V8" stroke-width="3"/>
    <path d="M100 96 L64 12 M100 96 L136 12" stroke-width="2.5"/>
    <path d="M100 96 L34 26 M100 96 L166 26" stroke-width="2"/>
    <path d="M100 96 L12 48 M100 96 L188 48" stroke-width="1.5"/>
    <path d="M100 96 L4 78 M100 96 L196 78" stroke-width="1"/>
  </g><circle cx="100" cy="96" r="10" fill="currentColor"/>
</svg>"""},
    "deco-fan": {"profile": "art-deco", "tags": ["fan", "shell", "arcs"],
        "svg": """<svg viewBox="0 0 120 70" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke="currentColor" stroke-width="2">
    <path d="M10 66 A50 50 0 0 1 110 66"/><path d="M22 66 A38 38 0 0 1 98 66"/>
    <path d="M34 66 A26 26 0 0 1 86 66"/><path d="M46 66 A14 14 0 0 1 74 66"/>
    <path d="M60 66 V16 M60 66 L28 26 M60 66 L92 26"/>
  </g>
</svg>"""},
    "stepped-frame": {"profile": "art-deco",
        "tags": ["ziggurat", "frame", "corner"],
        "svg": """<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M4 116 V44 H16 V32 H28 V20 H40 V8 H116" fill="none"
        stroke="currentColor" stroke-width="5"/>
  <path d="M16 116 V56 H28 V44 H40 V32 H52 V20 H116" fill="none"
        stroke="currentColor" stroke-width="2"/>
</svg>"""},
    "chevron-band": {"profile": "art-deco",
        "tags": ["chevron", "zigzag", "pattern-tile"],
        "svg": """<svg viewBox="0 0 160 40" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke="currentColor">
    <path d="M0 28 L20 8 L40 28 L60 8 L80 28 L100 8 L120 28 L140 8 L160 28" stroke-width="5"/>
    <path d="M0 36 L20 16 L40 36 L60 16 L80 36 L100 16 L120 36 L140 16 L160 36"
          stroke-width="2" opacity=".6"/>
  </g>
</svg>"""},
    # ---- frutiger metro ---------------------------------------------------- #
    "bloom-flower": {"profile": "frutiger-metro",
        "tags": ["bloom", "vector", "flower"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor">
    <path d="M50 50 C50 20 66 8 82 12 C86 30 72 46 50 50Z"/>
    <path d="M50 50 C80 50 92 66 88 82 C70 86 54 72 50 50Z" opacity=".7"/>
    <path d="M50 50 C50 80 34 92 18 88 C14 70 28 54 50 50Z" opacity=".55"/>
    <path d="M50 50 C20 50 8 34 12 18 C30 14 46 28 50 50Z" opacity=".4"/>
  </g><circle cx="50" cy="50" r="7" fill="currentColor"/>
</svg>"""},
    "metro-dots": {"profile": "frutiger-metro",
        "tags": ["dots", "constellation", "fade"],
        "svg": """<svg viewBox="0 0 140 60" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor"><circle cx="16" cy="30" r="12"/><circle cx="44" cy="18" r="9" opacity=".8"/>
  <circle cx="66" cy="40" r="7" opacity=".65"/><circle cx="88" cy="22" r="5.5" opacity=".5"/>
  <circle cx="106" cy="38" r="4" opacity=".4"/><circle cx="122" cy="26" r="3" opacity=".3"/>
  <circle cx="134" cy="34" r="2" opacity=".25"/></g>
</svg>"""},
    "swoosh-ribbon": {"profile": "frutiger-metro",
        "tags": ["swoosh", "ribbon", "flow"],
        "svg": """<svg viewBox="0 0 160 60" xmlns="http://www.w3.org/2000/svg">
  <path d="M2 50 C40 54 60 20 92 18 C120 16 140 28 158 10 C150 34 122 44 96 40
           C64 36 44 60 2 50Z" fill="currentColor"/>
  <path d="M10 44 C46 44 66 16 96 14" fill="none" stroke="currentColor"
        stroke-width="2" opacity=".5"/>
</svg>"""},
    # ---- 2000s preppy ------------------------------------------------------ #
    "argyle-tile": {"profile": "preppy-2000s",
        "tags": ["argyle", "diamond", "pattern-tile"],
        "svg": """<svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <path d="M40 0 L80 40 L40 80 L0 40 Z" fill="currentColor" opacity=".85"/>
  <path d="M40 16 L64 40 L40 64 L16 40 Z" fill="currentColor" opacity=".35"/>
  <path d="M0 0 L80 80 M80 0 L0 80" stroke="currentColor" stroke-width="1.5"
        stroke-dasharray="4 4" opacity=".8"/>
</svg>"""},
    "gingham-tile": {"profile": "preppy-2000s",
        "tags": ["gingham", "plaid", "pattern-tile"],
        "svg": """<svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor"><rect x="20" y="0" width="20" height="80" opacity=".35"/>
  <rect x="60" y="0" width="20" height="80" opacity=".35"/>
  <rect x="0" y="20" width="80" height="20" opacity=".35"/>
  <rect x="0" y="60" width="80" height="20" opacity=".35"/>
  <rect x="20" y="20" width="20" height="20" opacity=".55"/>
  <rect x="60" y="20" width="20" height="20" opacity=".55"/>
  <rect x="20" y="60" width="20" height="20" opacity=".55"/>
  <rect x="60" y="60" width="20" height="20" opacity=".55"/></g>
</svg>"""},
    "crest-shield": {"profile": "preppy-2000s",
        "tags": ["crest", "shield", "varsity"],
        "svg": """<svg viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 6 L92 18 V60 C92 88 74 106 50 114 C26 106 8 88 8 60 V18 Z"
        fill="none" stroke="currentColor" stroke-width="5"/>
  <path d="M50 16 L84 26 V60 C84 82 70 96 50 104 C30 96 16 82 16 60 V26 Z"
        fill="currentColor" opacity=".2"/>
  <path d="M22 44 L50 62 L78 44" fill="none" stroke="currentColor" stroke-width="5"/>
</svg>"""},
    "ribbon-banner": {"profile": "preppy-2000s",
        "tags": ["ribbon", "banner", "label"],
        "svg": """<svg viewBox="0 0 160 50" xmlns="http://www.w3.org/2000/svg">
  <path d="M20 12 H140 V38 H20 Z" fill="currentColor" opacity=".9"/>
  <path d="M20 12 L2 25 L20 38 Z M140 12 L158 25 L140 38 Z" fill="currentColor" opacity=".6"/>
  <path d="M26 18 H134 M26 32 H134" stroke="#fff" stroke-width="1.5" opacity=".7"/>
</svg>"""},
    # ---- frutiger aero ------------------------------------------------------ #
    "aqua-bubbles": {"profile": "frutiger-aero",
        "tags": ["bubbles", "gloss", "water"],
        "svg": """<svg viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg">
  <g fill="currentColor"><circle cx="40" cy="60" r="30" opacity=".35"/>
  <circle cx="84" cy="34" r="18" opacity=".5"/><circle cx="100" cy="72" r="10" opacity=".4"/>
  <circle cx="20" cy="22" r="8" opacity=".55"/></g>
  <g fill="#fff"><ellipse cx="30" cy="46" rx="12" ry="7" opacity=".8"/>
  <ellipse cx="78" cy="26" rx="7" ry="4" opacity=".85"/>
  <ellipse cx="97" cy="67" rx="4" ry="2.5" opacity=".8"/></g>
</svg>"""},
    "gloss-orb": {"profile": "frutiger-aero", "tags": ["orb", "sphere", "icon"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="44" fill="currentColor"/>
  <circle cx="50" cy="50" r="44" fill="none" stroke="#fff" stroke-width="1.5" opacity=".6"/>
  <ellipse cx="50" cy="30" rx="30" ry="17" fill="#fff" opacity=".55"/>
  <ellipse cx="50" cy="76" rx="22" ry="9" fill="#fff" opacity=".18"/>
</svg>"""},
    "grass-swoosh": {"profile": "frutiger-aero",
        "tags": ["grass", "horizon", "swoosh"],
        "svg": """<svg viewBox="0 0 160 60" xmlns="http://www.w3.org/2000/svg">
  <path d="M0 44 C40 28 90 30 160 18 V60 H0 Z" fill="currentColor" opacity=".85"/>
  <path d="M0 50 C50 38 100 40 160 30 V60 H0 Z" fill="currentColor" opacity=".55"/>
  <path d="M0 40 C40 26 90 28 160 16" fill="none" stroke="#fff"
        stroke-width="2" opacity=".5"/>
</svg>"""},
    # ---- y2k chrome ---------------------------------------------------------- #
    "chrome-blob": {"profile": "y2k-chrome", "tags": ["blob", "metaball", "chrome"],
        "svg": """<svg viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M60 8 C92 6 112 28 108 52 C104 76 84 94 56 92 C28 90 8 72 12 46 C16 22 34 10 60 8Z"
        fill="currentColor" opacity=".85"/>
  <path d="M58 20 C80 18 96 32 93 50 C90 66 76 80 56 78 C36 76 24 62 27 44 C30 28 42 21 58 20Z"
        fill="#fff" opacity=".25"/>
  <ellipse cx="46" cy="34" rx="18" ry="9" fill="#fff" opacity=".7"/>
</svg>"""},
    "lens-flare": {"profile": "y2k-chrome", "tags": ["flare", "star", "glint"],
        "svg": """<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <path d="M60 4 L64 52 L112 60 L64 68 L60 116 L56 68 L8 60 L56 52 Z"
        fill="currentColor" opacity=".9"/>
  <circle cx="60" cy="60" r="7" fill="#fff"/>
  <circle cx="60" cy="60" r="20" fill="none" stroke="currentColor"
          stroke-width="1" opacity=".4"/>
</svg>"""},
    "orbit-rings": {"profile": "y2k-chrome", "tags": ["orbit", "ring", "ellipse"],
        "svg": """<svg viewBox="0 0 140 100" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke="currentColor">
    <ellipse cx="70" cy="50" rx="64" ry="22" stroke-width="2"
             transform="rotate(-18 70 50)"/>
    <ellipse cx="70" cy="50" rx="46" ry="14" stroke-width="1" opacity=".5"
             transform="rotate(-18 70 50)"/>
  </g>
  <circle cx="118" cy="30" r="5" fill="currentColor"/>
</svg>"""},
    # ---- dark academia -------------------------------------------------------- #
    "wax-seal": {"profile": "dark-academia", "tags": ["seal", "wax", "stamp"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 6 C64 4 78 10 86 22 C94 34 96 50 88 64 C80 78 66 94 48 92
           C30 90 14 78 10 60 C6 42 12 26 24 16 C32 9 40 7 50 6Z"
        fill="currentColor" opacity=".9"/>
  <circle cx="50" cy="50" r="26" fill="none" stroke="#fff"
          stroke-width="2" opacity=".5"/>
  <path d="M40 60 V38 L50 50 L60 38 V60" fill="none" stroke="#fff"
        stroke-width="3" opacity=".75"/>
</svg>"""},
    "open-book": {"profile": "dark-academia", "tags": ["book", "pages", "read"],
        "svg": """<svg viewBox="0 0 140 90" xmlns="http://www.w3.org/2000/svg">
  <path d="M70 16 C56 6 30 6 12 12 V74 C30 68 56 68 70 78 C84 68 110 68 128 74 V12
           C110 6 84 6 70 16Z" fill="currentColor" opacity=".25"/>
  <path d="M70 16 V78 M70 16 C56 6 30 6 12 12 V74 C30 68 56 68 70 78
           M70 16 C84 6 110 6 128 12 V74 C110 68 84 68 70 78"
        fill="none" stroke="currentColor" stroke-width="3"/>
  <path d="M24 26 C38 22 54 23 62 28 M24 40 C38 36 54 37 62 42
           M78 28 C86 23 102 22 116 26 M78 42 C86 37 102 36 116 40"
        fill="none" stroke="currentColor" stroke-width="1.5" opacity=".6"/>
</svg>"""},
    "laurel-corner": {"profile": "dark-academia",
        "tags": ["laurel", "wreath", "classical"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M14 90 C10 58 22 26 52 12" fill="none" stroke="currentColor"
        stroke-width="3"/>
  <g fill="currentColor">
    <ellipse cx="20" cy="72" rx="11" ry="5" transform="rotate(-58 20 72)"/>
    <ellipse cx="26" cy="52" rx="11" ry="5" transform="rotate(-46 26 52)"/>
    <ellipse cx="36" cy="34" rx="11" ry="5" transform="rotate(-32 36 34)"/>
    <ellipse cx="50" cy="20" rx="11" ry="5" transform="rotate(-16 50 20)"/>
    <ellipse cx="34" cy="76" rx="11" ry="5" transform="rotate(-72 34 76)" opacity=".6"/>
    <ellipse cx="42" cy="56" rx="11" ry="5" transform="rotate(-58 42 56)" opacity=".6"/>
    <ellipse cx="54" cy="38" rx="11" ry="5" transform="rotate(-40 54 38)" opacity=".6"/>
  </g>
</svg>"""},
    # ---- swiss international --------------------------------------------------- #
    "grid-marks": {"profile": "swiss-international",
        "tags": ["grid", "crop", "registration"],
        "svg": """<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <g stroke="currentColor" stroke-width="1">
    <path d="M40 4 V116 M80 4 V116 M4 40 H116 M4 80 H116" opacity=".35"/>
    <path d="M4 12 H20 M12 4 V20 M116 12 H100 M108 4 V20
             M4 108 H20 M12 116 V100 M116 108 H100 M108 116 V100"/>
  </g>
</svg>"""},
    "signal-dot": {"profile": "swiss-international",
        "tags": ["dot", "signal", "accent"],
        "svg": """<svg viewBox="0 0 160 60" xmlns="http://www.w3.org/2000/svg">
  <g stroke="currentColor" stroke-width="1" opacity=".4">
    <path d="M8 12 H152 M8 28 H120 M8 44 H136"/>
  </g>
  <circle cx="140" cy="28" r="12" fill="currentColor"/>
</svg>"""},
    "crossbar-arrow": {"profile": "swiss-international",
        "tags": ["arrow", "wayfinding", "direction"],
        "svg": """<svg viewBox="0 0 140 60" xmlns="http://www.w3.org/2000/svg">
  <path d="M8 30 H112" stroke="currentColor" stroke-width="8"/>
  <path d="M96 8 L132 30 L96 52 Z" fill="currentColor"/>
</svg>"""},
    # ---- golden archive --------------------------------------------------------- #
    "gold-disk": {"profile": "golden-archive",
        "tags": ["record", "voyager", "disk", "seal"],
        "svg": """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="46" fill="currentColor" opacity=".9"/>
  <g fill="none" stroke="#fff">
    <circle cx="50" cy="50" r="38" stroke-width="1" opacity=".4"/>
    <circle cx="50" cy="50" r="30" stroke-width="1.5" opacity=".55"/>
    <circle cx="50" cy="50" r="22" stroke-width="1" opacity=".4"/>
    <circle cx="50" cy="50" r="14" stroke-width="1.5" opacity=".55"/>
  </g>
  <circle cx="50" cy="50" r="6" fill="#0a0a12"/>
  <circle cx="50" cy="50" r="6" fill="none" stroke="#fff" opacity=".8"/>
</svg>"""},
    "constellation-path": {"profile": "golden-archive",
        "tags": ["constellation", "stars", "path"],
        "svg": """<svg viewBox="0 0 160 90" xmlns="http://www.w3.org/2000/svg">
  <path d="M14 70 L52 30 L96 52 L146 16" fill="none" stroke="currentColor"
        stroke-width="1.5" stroke-dasharray="3 6"/>
  <g fill="none" stroke="currentColor" stroke-width="1.5">
    <circle cx="14" cy="70" r="4"/><circle cx="52" cy="30" r="4"/>
    <circle cx="96" cy="52" r="4"/><circle cx="146" cy="16" r="4"/>
  </g>
  <g fill="currentColor"><circle cx="34" cy="14" r="1.5"/><circle cx="76" cy="76" r="1.5"/>
  <circle cx="120" cy="34" r="1.5"/><circle cx="142" cy="66" r="1"/></g>
</svg>"""},
}


# --------------------------------------------------------------------------- #
#  Terminal helpers — ANSI truecolor swatches
# --------------------------------------------------------------------------- #

def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _swatch(h: str, width: int = 4) -> str:
    try:
        r, g, b = _hex_rgb(h)
    except Exception:
        return " " * width
    return f"\x1b[48;2;{r};{g};{b}m{' ' * width}\x1b[0m"


def _swatches(colors: list[str]) -> str:
    return "".join(_swatch(c) for c in colors)


# --------------------------------------------------------------------------- #
#  The vault DEMO — one auto-generated page showing EVERYTHING visual.
#  Rebuilt by sync() from the data itself, so new palettes/styles/layouts/
#  shapes/profiles appear in the demo the moment they're added. Never stale.
# --------------------------------------------------------------------------- #

DEMO = ASSETS_DIR / "demo.html"

_DEMO_CSS = """
:root{--bg:#0e1116;--panel:#161b23;--surface:#1c2330;--ink:#dce3ec;
  --dim:#8b95a5;--line:#2a3342;--acc:#4ba3e3;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.6 'Segoe UI',system-ui,sans-serif;}
header{position:sticky;top:0;z-index:9;background:rgba(14,17,22,.92);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
  padding:10px 22px;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap;}
header b{font-size:17px;color:var(--acc);}
header a{color:var(--dim);text-decoration:none;font-size:13px;}
header a:hover{color:var(--ink);}
main{max-width:1280px;margin:0 auto;padding:26px 22px 120px;}
h2{font-size:22px;margin:54px 0 4px;color:var(--acc);
  border-top:1px solid var(--line);padding-top:20px;}
h2 small{color:var(--dim);font-weight:400;font-size:13px;}
p.hint{color:var(--dim);font-size:13px;margin:2px 0 18px;}
code{background:var(--surface);padding:1px 6px;border-radius:5px;
  font-size:12.5px;}
.grid{display:grid;gap:14px;}
.g-style{grid-template-columns:repeat(auto-fill,minmax(230px,1fr));}
.g-prof{grid-template-columns:repeat(auto-fill,minmax(360px,1fr));}
.g-pal{grid-template-columns:repeat(auto-fill,minmax(290px,1fr));}
.g-tile{grid-template-columns:repeat(auto-fill,minmax(170px,1fr));}
.g-shape{grid-template-columns:repeat(auto-fill,minmax(120px,1fr));}
.g-layout{grid-template-columns:repeat(auto-fill,minmax(280px,1fr));}
.cell{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:10px;}
.cell .lbl{font-size:12px;color:var(--dim);margin-top:6px;}
.cell .lbl b{color:var(--ink);font-weight:600;}
.sw{display:flex;height:34px;border-radius:6px;overflow:hidden;
  border:1px solid var(--line);}
.sw i{flex:1;}
.hexes{font:10.5px ui-monospace,Consolas,monospace;color:var(--dim);
  margin-top:5px;word-spacing:4px;}
.tile{height:110px;border-radius:8px;border:1px solid var(--line);}
.shapebox{height:84px;display:flex;align-items:center;justify-content:center;}
.shapebox svg{max-width:100%;max-height:78px;}
.thumb{width:100%;height:190px;overflow:hidden;border-radius:8px;
  border:1px solid var(--line);background:#fff;position:relative;}
.thumb iframe{width:1200px;height:840px;border:0;transform:scale(.235);
  transform-origin:0 0;pointer-events:none;}
.mini{border-radius:var(--mr,10px);overflow:hidden;
  border:1px solid var(--mb);}
.mini .bar{height:26px;display:flex;align-items:center;padding:0 10px;
  font-size:10.5px;font-weight:700;color:#fff;letter-spacing:.04em;}
.mini .body{padding:10px;min-height:104px;}
.mini .card{border-radius:calc(var(--mr,10px)*.7);padding:8px 10px;
  font-size:11px;border:1px solid var(--mb);}
.mini .btn{display:inline-block;margin-top:8px;padding:4px 12px;
  border-radius:999px;font-size:10.5px;font-weight:700;}
.mini .chip{display:inline-block;margin:8px 0 0 6px;padding:3px 9px;
  border-radius:999px;font-size:10px;font-weight:700;}
.prof{border-left:4px solid var(--pa);}
.prof .era{font-size:11px;color:var(--dim);}
.prof .vibe{font-size:12.5px;color:var(--ink);margin:6px 0;}
.prof .meta{font-size:11.5px;color:var(--dim);}
.prof .shapes{display:flex;gap:10px;margin-top:8px;}
.prof .shapes svg{height:44px;width:auto;max-width:80px;}
.fontrow{display:flex;gap:14px;align-items:baseline;border-bottom:1px dashed
  var(--line);padding:7px 2px;}
.fontrow .name{width:220px;font-size:12.5px;color:var(--dim);flex:none;}
.fontrow .sample{font-size:21px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;}
footer{color:var(--dim);font-size:12.5px;margin-top:70px;
  border-top:1px solid var(--line);padding-top:16px;}
"""



# Research-backed additions: preserve existing palette IDs and application identities.
STYLES['cyberpunk']['tokens']['radius'] = '0px'
EXEC['high-fashion']['scale_rem'] = ['10rem', '1.5rem', '1.125rem']
PROFILES['high-fashion']['proportion'] = 'Didone display reaches 160px against 18px reading text; captions remain legible. One image or original fashion plate dominates the spread. Off-centre crops, folios and hairline dividers replace decorative cards.'
PROFILES['high-fashion']['imagery'] += ' The portable starter uses an original vector fashion plate as a licensed local fallback; replace it with owned campaign photography when available. A small decorative icon is never a campaign image.'
PROFILES['cyberpunk']['composition'] += ' Use an asymmetric signal console: a compressed status rail, large sector map, chamfered controls and dense telemetry. Keep long reading text in sentence case.'
PROFILES['nordic']['color'] = 'The existing nordic-frost palette is the polar-night application mode, not a definition of Scandinavian design. The nordic-daylight page uses frost, slate ink, pale timber and quiet blue. Warm material and useful proportions matter more than desaturation; the movement also includes vivid textiles.'
PROFILES['nordic']['gradients'] = []
PROFILES['nordic']['moves'] = ['Use a horizontal object catalogue with generous practical space', 'Stage pale timber, matte ceramic and a layered lamp in lateral daylight', 'Use quiet humanist typography and functional labels', 'Keep polar-night colours for established applications; use the named daylight mode for interiors']
STYLES['bauhaus'] = dict(label='Bauhaus / Workshop Modernism',font="'Inter',sans-serif",mono="'JetBrains Mono',monospace",tokens=dict(bg='#f2eee4',bg2='#e8e1d2',surface='#fffdf6',accent='#b42e23',accent2='#23539b',text='#191919',muted='#57534c',border='#292723',radius='0px',shadow='none',**{'surface-glass':'#fffdf6'}))
EXEC['bauhaus'] = dict(EXEC['swiss-international'],ratio=1.414,sizes=4,base=17,weights=(400,700),gutter=24,accents=3,forbid=['gradient','glass','shadow','texture'])
STYLES['art-nouveau'] = dict(label='Art Nouveau / Botanical Line',font="'Lora',serif",mono="'JetBrains Mono',monospace",tokens=dict(bg='#f2e9d5',bg2='#e3d5b8',surface='#faf3e2',accent='#405840',accent2='#914d37',text='#27382c',muted='#5b5947',border='#887957',radius='2px',shadow='none',**{'surface-glass':'#faf3e2'}))
EXEC['art-nouveau'] = dict(EXEC['dark-academia'],ratio=1.414,base=18,weights=(400,600),align='center',elevation='none',accents=2,forbid=['gradient','glass','chrome','bounce','neon'])
PALETTES.extend([
 dict(id='workshop-primary',style='bauhaus',name='Bauhaus — Workshop Study',colors=['#f2eee4','#191919','#b42e23','#23539b','#e1af32','#57534c'],tags=['bauhaus','workshop','geometric','functional','poster']),
 dict(id='botanical-lithograph',style='art-nouveau',name='Art Nouveau — Botanical Lithograph',colors=['#f2e9d5','#27382c','#405840','#914d37','#887957','#e3d5b8'],tags=['art-nouveau','whiplash','botanical','lithograph','ornament'])])
PROFILES['bauhaus'] = dict(label='Bauhaus / Workshop Modernism',style='bauhaus',palette='workshop-primary',
 vibe='A workshop, not a colour theme: asymmetric typography, measured geometric studies and useful objects. Form, material and making occupy the same page.',
 era='1919–1933; contemporary workshop interpretation',
 origins='The Bauhaus combined art and craft with industrial production. This profile draws on workshop pedagogy, typography and material studies rather than treating primary-colour shapes as the whole movement.',
 composition='Asymmetric poster with a huge workshop number, a colour-and-form study, orthogonal rules and a functional course index. Type shares the geometry of the objects.',
 proportion='A clear modular grid; broad margins; a display headline several steps above the text. Geometric elements act as compositional masses, not scattered confetti.',
 color='Warm stock and black structure; limited red, blue and ochre areas. These are one documented study palette, not a claim that all Bauhaus work used primaries.',
 light='Flat print light; no emissive effects, glass, atmospheric bloom or floating shadows.',
 type='Inter for practical text and Sora for geometric display; asymmetric flush-left setting, upright type and visible numerals.',
 materiality='Paper, ink, steel, wood and woven studies. The web interpretation keeps the flatness of a printed workshop sheet.',
 motion='Brief geometric translation or a direct state change. Never use animation as surface decoration.',
 imagery='Original geometric and material studies; object diagrams and owned workshop photographs.',
 voice='Concise, functional and concrete: workshop, material, exercise, edition. Name the useful action before adding a poetic description.',sound='Quiet by default; no automatic audio. If a project needs sound, make the action explicit and keep the reading space free from continuous effects.',space='Design studios, practical courses, architecture, furniture and cultural programmes where the relation between an object, its material and its construction matters.',
 kinship='Shares systematic alignment with Swiss International, but lets geometric experiments and object studies lead. Memphis / Avant Basic is a later postmodern reaction, with decorative collisions instead of this functional order.',
 hierarchy='Composition and type > geometric form > useful information > colour. The grid should remain legible when the colour study is removed.',
 canon='Bauhaus-Archiv teaching studies; Herbert Bayer typography; workshop objects and the MoMA Bauhaus collection.',
 adaptation='Ink on warm stock; each coloured shape is decorative and carries no small text. The layout collapses into a single reading column on phones.',
 fonts=dict(display='Sora',body='Inter',files=['sora-600.woff2','inter-400.woff2']),textures=[],gloss='None: flat printed colour on warm stock. Keep edges precise and use adjacent shapes for contrast rather than bevels, reflected light or a digital sheen.',shapes=['workshop-study'],patterns=[],gradients=[],techniques=['text-balance-wrap'],
 moves=['Compose with the grid rather than decorate it','Give a functional numeral real scale','Keep geometric masses balanced but asymmetric','Make the workshop index usable'],
 rules='DO use useful information, experimental form and precise alignment. DO NOT reduce the movement to red/yellow/blue circles or import glossy UI furniture.',failure='If the shapes could be removed without changing the composition, they have become decoration.')
PROFILES['art-nouveau'] = dict(label='Art Nouveau / Botanical Line',style='art-nouveau',palette='botanical-lithograph',
 vibe='A botanical print grown into a page: sinuous stems, elongated lettering, warm paper and a continuous ornamental frame.',
 era='c. 1883–1914; contemporary botanical-poster interpretation',
 origins='An international movement across architecture, applied arts and graphic design. Natural forms and the whiplash line link the page to ironwork, stained glass, textiles and turn-of-the-century posters.',
 composition='A vertical framed poster. One botanical plate rises through the centre; the headline, curved border and folio belong to the same contour system.',
 proportion='Long vertical proportions and an organic continuous frame. Keep the reading column narrow and the decorative border outside the text.',
 color='Warm lithographic stock, deep botanical green, dried terracotta and muted brass. Flat colour fields keep the print character.',
 light='Even paper light. Depth comes from overlapping contour lines, never glass or a digital glow.',
 type='Fraunces for expressive serif titles, Lora for reading. The local fonts are practical modern companions, not claims to be historical Art Nouveau typefaces.',
 materiality='Lithographic paper, botanical ink, stained-glass partitions and curved metalwork translated into SVG line.',
 motion='A slow clipped botanical reveal if used; the complete illustration remains present with reduced motion.',
 imagery='Original iris stems and whiplash curves. Use licensed botanical prints and owned photographs when extending the collection.',
 voice='Poetic but specific: an exhibition title, a botanical name, a season. Keep practical information direct and let one lyrical line carry the atmosphere.',sound='Quiet by default; no automatic audio. If a project needs sound, make the action explicit and keep the reading space free from continuous effects.',space='Botanical exhibitions, cultural events, perfumery, book arts and decorative-arts collections.',
 kinship='Art Deco is angular, stepped and geometric; this profile grows from organic curves. Organic Tech is functional and contemporary rather than a framed print.',
 hierarchy='Continuous botanical line > image silhouette > lettering > limited print colour.',
 canon='V&A whiplash examples, Guimard ironwork, Horta interiors and Mucha poster composition; study rather than copy their artworks.',
 adaptation='Text sits on an opaque paper plane. Borders simplify on phones and never crowd the reading column.',
 fonts=dict(display='Fraunces',body='Lora',files=['fraunces-600.woff2','lora-400.woff2']),textures=['paper'],gloss='None: flat lithographic stock with visible ink contours. Let overlapping lines create depth; a glass panel or chrome highlight would break the printed character.',shapes=['iris-whiplash'],patterns=[],gradients=[],techniques=['text-balance-wrap'],
 moves=['Let one organic line frame the composition','Extend botanical stems into the continuous page border','Keep colour flat and botanical','Protect a quiet opaque text field'],
 rules='DO connect ornament to the page structure. DO NOT use a stepped Deco sunburst, generic floating blobs or a modern glass card.',failure='If the border could belong to Art Deco without changing anything, the organic line has been lost.')


# Original reusable scene assets. Reference by ID; no remote media is needed.
SHAPES.update({'reading-room': {'profile': 'dark-academia',
                  'tags': ['scene', 'library', 'gothic', 'lamplight'],
                  'svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 840" role="img" '
                         'aria-label="A candlelit reading room with Gothic windows, shelves, a '
                         'shaded lamp and an open book"><defs><radialGradient '
                         'id="study-light"><stop stop-color="#665038"/><stop offset="1" '
                         'stop-color="#201812"/></radialGradient><linearGradient id="study-window" '
                         'x2="0" y2="1"><stop stop-color="#65716b"/><stop offset="1" '
                         'stop-color="#292e29"/></linearGradient></defs><rect width="720" '
                         'height="840" fill="url(#study-light)"/><path d="M35 700V100Q360-75 685 '
                         '100V700" fill="none" stroke="#806744" stroke-width="2"/><path d="M60 '
                         '700V120Q360-30 660 120V700" fill="none" stroke="#806744"/><path d="M275 '
                         '460V140Q360-18 445 140V460Z" fill="url(#study-window)" stroke="#96876f" '
                         'stroke-width="7"/><path d="M360 45V460M275 260H445M275 375H445M290 '
                         '150Q360 30 430 150M297 190Q360 60 423 190" fill="none" stroke="#96876f" '
                         'stroke-width="3"/><rect x="72" y="136" width="13" height="74" rx="1" '
                         'fill="#3e4a36"/><path d="M74 145h9M74 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="88" y="119" width="13" height="91" rx="1" '
                         'fill="#8c3838"/><path d="M90 128h9M90 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="104" y="102" width="13" height="108" rx="1" '
                         'fill="#49372a"/><path d="M106 111h9M106 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="120" y="129" width="13" height="81" rx="1" '
                         'fill="#62503b"/><path d="M122 138h9M122 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="136" y="112" width="13" height="98" rx="1" '
                         'fill="#3e4a36"/><path d="M138 121h9M138 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="152" y="95" width="13" height="115" rx="1" '
                         'fill="#8c3838"/><path d="M154 104h9M154 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="168" y="122" width="13" height="88" rx="1" '
                         'fill="#49372a"/><path d="M170 131h9M170 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="184" y="105" width="13" height="105" rx="1" '
                         'fill="#62503b"/><path d="M186 114h9M186 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="200" y="132" width="13" height="78" rx="1" '
                         'fill="#3e4a36"/><path d="M202 141h9M202 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><path d="M62 213h166" stroke="#8e7149" '
                         'stroke-width="6"/><rect x="72" y="263" width="13" height="87" rx="1" '
                         'fill="#3e4a36"/><path d="M74 272h9M74 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="88" y="246" width="13" height="104" rx="1" '
                         'fill="#8c3838"/><path d="M90 255h9M90 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="104" y="273" width="13" height="77" rx="1" '
                         'fill="#49372a"/><path d="M106 282h9M106 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="120" y="256" width="13" height="94" rx="1" '
                         'fill="#62503b"/><path d="M122 265h9M122 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="136" y="239" width="13" height="111" rx="1" '
                         'fill="#3e4a36"/><path d="M138 248h9M138 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="152" y="266" width="13" height="84" rx="1" '
                         'fill="#8c3838"/><path d="M154 275h9M154 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="168" y="249" width="13" height="101" rx="1" '
                         'fill="#49372a"/><path d="M170 258h9M170 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="184" y="276" width="13" height="74" rx="1" '
                         'fill="#62503b"/><path d="M186 285h9M186 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="200" y="259" width="13" height="91" rx="1" '
                         'fill="#3e4a36"/><path d="M202 268h9M202 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><path d="M62 353h166" stroke="#8e7149" '
                         'stroke-width="6"/><rect x="72" y="390" width="13" height="100" rx="1" '
                         'fill="#3e4a36"/><path d="M74 399h9M74 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="88" y="373" width="13" height="117" rx="1" '
                         'fill="#8c3838"/><path d="M90 382h9M90 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="104" y="400" width="13" height="90" rx="1" '
                         'fill="#49372a"/><path d="M106 409h9M106 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="120" y="383" width="13" height="107" rx="1" '
                         'fill="#62503b"/><path d="M122 392h9M122 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="136" y="410" width="13" height="80" rx="1" '
                         'fill="#3e4a36"/><path d="M138 419h9M138 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="152" y="393" width="13" height="97" rx="1" '
                         'fill="#8c3838"/><path d="M154 402h9M154 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="168" y="376" width="13" height="114" rx="1" '
                         'fill="#49372a"/><path d="M170 385h9M170 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="184" y="403" width="13" height="87" rx="1" '
                         'fill="#62503b"/><path d="M186 412h9M186 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="200" y="386" width="13" height="104" rx="1" '
                         'fill="#3e4a36"/><path d="M202 395h9M202 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><path d="M62 493h166" stroke="#8e7149" '
                         'stroke-width="6"/><rect x="500" y="136" width="13" height="74" rx="1" '
                         'fill="#3e4a36"/><path d="M502 145h9M502 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="516" y="119" width="13" height="91" rx="1" '
                         'fill="#8c3838"/><path d="M518 128h9M518 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="532" y="102" width="13" height="108" rx="1" '
                         'fill="#49372a"/><path d="M534 111h9M534 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="548" y="129" width="13" height="81" rx="1" '
                         'fill="#62503b"/><path d="M550 138h9M550 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="564" y="112" width="13" height="98" rx="1" '
                         'fill="#3e4a36"/><path d="M566 121h9M566 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="580" y="95" width="13" height="115" rx="1" '
                         'fill="#8c3838"/><path d="M582 104h9M582 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="596" y="122" width="13" height="88" rx="1" '
                         'fill="#49372a"/><path d="M598 131h9M598 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="612" y="105" width="13" height="105" rx="1" '
                         'fill="#62503b"/><path d="M614 114h9M614 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="628" y="132" width="13" height="78" rx="1" '
                         'fill="#3e4a36"/><path d="M630 141h9M630 201h9" stroke="#b08d4f" '
                         'stroke-width="1"/><path d="M490 213h166" stroke="#8e7149" '
                         'stroke-width="6"/><rect x="500" y="263" width="13" height="87" rx="1" '
                         'fill="#3e4a36"/><path d="M502 272h9M502 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="516" y="246" width="13" height="104" rx="1" '
                         'fill="#8c3838"/><path d="M518 255h9M518 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="532" y="273" width="13" height="77" rx="1" '
                         'fill="#49372a"/><path d="M534 282h9M534 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="548" y="256" width="13" height="94" rx="1" '
                         'fill="#62503b"/><path d="M550 265h9M550 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="564" y="239" width="13" height="111" rx="1" '
                         'fill="#3e4a36"/><path d="M566 248h9M566 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="580" y="266" width="13" height="84" rx="1" '
                         'fill="#8c3838"/><path d="M582 275h9M582 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="596" y="249" width="13" height="101" rx="1" '
                         'fill="#49372a"/><path d="M598 258h9M598 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="612" y="276" width="13" height="74" rx="1" '
                         'fill="#62503b"/><path d="M614 285h9M614 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="628" y="259" width="13" height="91" rx="1" '
                         'fill="#3e4a36"/><path d="M630 268h9M630 341h9" stroke="#b08d4f" '
                         'stroke-width="1"/><path d="M490 353h166" stroke="#8e7149" '
                         'stroke-width="6"/><rect x="500" y="390" width="13" height="100" rx="1" '
                         'fill="#3e4a36"/><path d="M502 399h9M502 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="516" y="373" width="13" height="117" rx="1" '
                         'fill="#8c3838"/><path d="M518 382h9M518 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="532" y="400" width="13" height="90" rx="1" '
                         'fill="#49372a"/><path d="M534 409h9M534 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="548" y="383" width="13" height="107" rx="1" '
                         'fill="#62503b"/><path d="M550 392h9M550 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="564" y="410" width="13" height="80" rx="1" '
                         'fill="#3e4a36"/><path d="M566 419h9M566 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="580" y="393" width="13" height="97" rx="1" '
                         'fill="#8c3838"/><path d="M582 402h9M582 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="596" y="376" width="13" height="114" rx="1" '
                         'fill="#49372a"/><path d="M598 385h9M598 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="612" y="403" width="13" height="87" rx="1" '
                         'fill="#62503b"/><path d="M614 412h9M614 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><rect x="628" y="386" width="13" height="104" rx="1" '
                         'fill="#3e4a36"/><path d="M630 395h9M630 481h9" stroke="#b08d4f" '
                         'stroke-width="1"/><path d="M490 493h166" stroke="#8e7149" '
                         'stroke-width="6"/><path d="M0 650L720 618V840H0Z" fill="#2c221a"/><path '
                         'd="M0 650L720 618" stroke="#b08d4f" stroke-width="3"/><ellipse cx="360" '
                         'cy="730" rx="180" ry="42" fill="#201812"/><path d="M220 667Q295 641 360 '
                         '671Q425 642 504 660L490 760Q420 740 360 773Q292 745 232 770Z" '
                         'fill="#e9ddc8" stroke="#b08d4f" stroke-width="2"/><path d="M360 '
                         '672V770M248 687Q300 670 342 690M250 705Q302 690 343 707M253 724Q302 710 '
                         '342 726M379 691Q425 675 477 682M379 710Q425 694 475 700M379 730Q423 715 '
                         '471 720" fill="none" stroke="#96876f" stroke-width="2"/><path d="M562 '
                         '476V658M534 662H591" stroke="#b08d4f" stroke-width="7"/><path d="M508 '
                         '480Q560 420 614 480L601 519H521Z" fill="#3e4a36" stroke="#b08d4f" '
                         'stroke-width="3"/><ellipse cx="561" cy="518" rx="40" ry="7" '
                         'fill="#c1ac77"/><path d="M99 595L169 582L175 628L105 640Z" '
                         'fill="#8c3838" stroke="#b08d4f"/><path d="M120 607l39-7" '
                         'stroke="#b08d4f"/><path d="M0 815H720" stroke="#b08d4f"/><text x="42" '
                         'y="807" fill="#b08d4f" font-family="serif" font-size="14" '
                         'letter-spacing="4">THE READING ROOM / PLATE I</text></svg>'},
 'night-city-feed': {'profile': 'cyberpunk',
                     'tags': ['scene', 'night', 'city', 'telemetry'],
                     'svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 840" '
                            'role="img" aria-label="A dense retrofitted night city with emissive '
                            'signage, rain, cables and a diagnostic overlay"><rect width="720" '
                            'height="840" fill="#0d0221"/><circle cx="560" cy="190" r="126" '
                            'fill="#ff2a6d" opacity=".1"/><path d="M0 110H720M0 320H720M0 '
                            '530H720M180 0V840M360 0V840M540 0V840" stroke="#194d65" '
                            'stroke-width="1"/><path d="M20 700V360l29.0-25H107V700Z" '
                            'fill="#01012b" stroke="#194d65" stroke-width="2"/><rect x="55" '
                            'y="380" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="78" y="380" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="32" y="413" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="55" y="413" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="32" y="446" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="78" '
                            'y="446" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="55" y="479" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="78" y="479" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="32" y="512" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="55" y="512" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="32" '
                            'y="545" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="78" y="545" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="55" y="578" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="78" y="578" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="32" y="611" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="55" '
                            'y="611" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="32" y="644" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="78" y="644" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><path d="M110 '
                            '700V205l26.666666666666668-25H190V700Z" fill="#01012b" '
                            'stroke="#194d65" stroke-width="2"/><rect x="122" y="225" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="145" y="225" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="122" '
                            'y="258" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="168" y="258" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="145" y="291" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="168" y="291" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="122" y="324" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="145" '
                            'y="324" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="122" y="357" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="168" y="357" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="145" y="390" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="168" y="390" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="122" '
                            'y="423" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="145" y="423" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="122" y="456" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="168" y="456" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="145" y="489" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="168" '
                            'y="489" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="122" y="522" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="145" y="522" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="122" y="555" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="168" y="555" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="145" '
                            'y="588" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="168" y="588" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="122" y="621" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="145" y="621" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><path d="M205 '
                            '700V135l38.333333333333336-25H320V700Z" fill="#01012b" '
                            'stroke="#194d65" stroke-width="2"/><rect x="217" y="155" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="263" y="155" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="286" '
                            'y="155" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="240" y="188" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="263" y="188" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="217" y="221" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="240" y="221" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="286" '
                            'y="221" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="217" y="254" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="263" y="254" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="286" y="254" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="240" y="287" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="263" '
                            'y="287" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="217" y="320" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="240" y="320" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="286" y="320" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="217" y="353" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="263" '
                            'y="353" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="286" y="353" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="240" y="386" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="263" y="386" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="217" y="419" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="240" '
                            'y="419" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="286" y="419" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="217" y="452" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="263" y="452" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="286" y="452" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="240" '
                            'y="485" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="263" y="485" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="217" y="518" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="240" y="518" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="286" y="518" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="217" '
                            'y="551" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="263" y="551" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="286" y="551" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="240" y="584" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="263" y="584" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="217" '
                            'y="617" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="240" y="617" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="286" y="617" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><path d="M330 700V285l28.0-25H414V700Z" '
                            'fill="#01012b" stroke="#194d65" stroke-width="2"/><rect x="365" '
                            'y="305" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="388" y="305" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="342" y="338" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="365" y="338" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="342" y="371" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="388" '
                            'y="371" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="365" y="404" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="388" y="404" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="342" y="437" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="365" y="437" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="342" '
                            'y="470" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="388" y="470" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="365" y="503" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="388" y="503" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="342" y="536" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="365" '
                            'y="536" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="342" y="569" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="388" y="569" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="365" y="602" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="388" y="602" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="342" '
                            'y="635" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="365" y="635" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><path d="M425 700V75l36.666666666666664-25H535V700Z" '
                            'fill="#01012b" stroke="#194d65" stroke-width="2"/><rect x="437" '
                            'y="95" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="460" y="95" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="506" y="95" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="437" y="128" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="483" y="128" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="506" '
                            'y="128" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="460" y="161" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="483" y="161" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="437" y="194" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="460" y="194" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="506" '
                            'y="194" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="437" y="227" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="483" y="227" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="506" y="227" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="460" y="260" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="483" '
                            'y="260" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="437" y="293" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="460" y="293" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="506" y="293" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="437" y="326" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="483" '
                            'y="326" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="506" y="326" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="460" y="359" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="483" y="359" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="437" y="392" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="460" '
                            'y="392" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="506" y="392" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="437" y="425" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="483" y="425" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="506" y="425" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="460" '
                            'y="458" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="483" y="458" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="437" y="491" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="460" y="491" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="506" y="491" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="437" '
                            'y="524" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="483" y="524" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="506" y="524" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="460" y="557" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="483" y="557" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="437" '
                            'y="590" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="460" y="590" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="506" y="590" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="437" y="623" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="483" y="623" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="506" '
                            'y="623" width="8" height="13" fill="#05d9e8" opacity=".5"/><path '
                            'd="M550 700V235l25.0-25H625V700Z" fill="#01012b" stroke="#194d65" '
                            'stroke-width="2"/><rect x="562" y="255" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="608" y="255" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="585" y="288" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="608" '
                            'y="288" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="562" y="321" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="585" y="321" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="562" y="354" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="608" y="354" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="585" '
                            'y="387" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="608" y="387" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="562" y="420" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="585" y="420" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="562" y="453" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="608" '
                            'y="453" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="585" y="486" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="608" y="486" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="562" y="519" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="585" y="519" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="562" '
                            'y="552" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="608" y="552" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="585" y="585" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="608" y="585" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="562" y="618" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="585" '
                            'y="618" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="562" y="651" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="608" y="651" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><path d="M635 '
                            '700V155l26.666666666666668-25H715V700Z" fill="#01012b" '
                            'stroke="#194d65" stroke-width="2"/><rect x="670" y="175" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="693" y="175" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="647" '
                            'y="208" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="670" y="208" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="647" y="241" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="693" y="241" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="670" y="274" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="693" '
                            'y="274" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="647" y="307" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="670" y="307" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="647" y="340" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="693" y="340" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="670" '
                            'y="373" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="693" y="373" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="647" y="406" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="670" y="406" width="8" '
                            'height="13" fill="#05d9e8" opacity=".5"/><rect x="647" y="439" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="693" '
                            'y="439" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="670" y="472" width="8" height="13" fill="#05d9e8" '
                            'opacity=".5"/><rect x="693" y="472" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><rect x="647" y="505" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="670" y="505" '
                            'width="8" height="13" fill="#05d9e8" opacity=".5"/><rect x="647" '
                            'y="538" width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect '
                            'x="693" y="538" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="670" y="571" width="8" height="13" '
                            'fill="#05d9e8" opacity=".5"/><rect x="693" y="571" width="8" '
                            'height="13" fill="#ff2a6d" opacity=".5"/><rect x="647" y="604" '
                            'width="8" height="13" fill="#ff2a6d" opacity=".5"/><rect x="670" '
                            'y="604" width="8" height="13" fill="#05d9e8" opacity=".5"/><rect '
                            'x="647" y="637" width="8" height="13" fill="#ff2a6d" '
                            'opacity=".5"/><rect x="693" y="637" width="8" height="13" '
                            'fill="#ff2a6d" opacity=".5"/><path d="M0 706L720 690V840H0Z" '
                            'fill="#01012b"/><path d="M0 790L430 690M300 840L470 690M720 780L530 '
                            '690" stroke="#05d9e8" opacity=".35"/><g stroke="#194d65" '
                            'stroke-width="5" fill="none"><path d="M0 140Q350 350 720 70M0 225Q370 '
                            '400 720 245"/></g><path d="M465 155h48v208h-48Z" '
                            'fill="#ff2a6d"/><text x="489" y="189" fill="#0d0221" '
                            'font-family="monospace" font-weight="bold" font-size="25" '
                            'text-anchor="middle"><tspan x="489">N</tspan><tspan x="489" '
                            'dy="33">E</tspan><tspan x="489" dy="33">T</tspan><tspan x="489" '
                            'dy="33">0</tspan><tspan x="489" dy="33">7</tspan></text><rect x="80" '
                            'y="390" width="195" height="48" fill="#05d9e8"/><text x="94" y="423" '
                            'fill="#01012b" font-family="monospace" font-size="28" '
                            'font-weight="bold">AFTER HOURS</text><g stroke="#d1f7ff" '
                            'stroke-width="1" opacity=".18"><path d="M0 0l-16 52"/><path d="M83 '
                            '119l-16 52"/><path d="M166 238l-16 52"/><path d="M249 357l-16 '
                            '52"/><path d="M332 476l-16 52"/><path d="M415 595l-16 52"/><path '
                            'd="M498 714l-16 52"/><path d="M581 833l-16 52"/><path d="M664 112l-16 '
                            '52"/><path d="M27 231l-16 52"/><path d="M110 350l-16 52"/><path '
                            'd="M193 469l-16 52"/><path d="M276 588l-16 52"/><path d="M359 707l-16 '
                            '52"/><path d="M442 826l-16 52"/><path d="M525 105l-16 52"/><path '
                            'd="M608 224l-16 52"/><path d="M691 343l-16 52"/><path d="M54 462l-16 '
                            '52"/><path d="M137 581l-16 52"/><path d="M220 700l-16 52"/><path '
                            'd="M303 819l-16 52"/><path d="M386 98l-16 52"/><path d="M469 217l-16 '
                            '52"/><path d="M552 336l-16 52"/><path d="M635 455l-16 52"/><path '
                            'd="M718 574l-16 52"/><path d="M81 693l-16 52"/><path d="M164 812l-16 '
                            '52"/><path d="M247 91l-16 52"/><path d="M330 210l-16 52"/><path '
                            'd="M413 329l-16 52"/><path d="M496 448l-16 52"/><path d="M579 567l-16 '
                            '52"/><path d="M662 686l-16 52"/><path d="M25 805l-16 52"/></g><path '
                            'd="M32 32h55M32 32v55M688 32h-55M688 32v55M32 808h55M32 808v-55M688 '
                            '808h-55M688 808v-55" fill="none" stroke="#05d9e8" '
                            'stroke-width="3"/><g fill="#d1f7ff" font-family="monospace" '
                            'font-size="14"><text x="48" y="64">SECTOR_07 / OPTICAL '
                            'FEED</text><text x="48" y="775">LINK 98.4% // '
                            'ENCRYPTED</text></g><path d="M44 745H676" stroke="#ff2a6d"/><path '
                            'd="M535 658v60m-30-30h60" stroke="#05d9e8" stroke-width="2"/></svg>'},
 'couture-silhouette': {'profile': 'high-fashion',
                        'tags': ['scene', 'fashion', 'campaign', 'illustration'],
                        'svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 840" '
                               'role="img" aria-label="Original monochrome fashion illustration of '
                               'a sculptural coat, staged as a campaign plate"><rect width="720" '
                               'height="840" fill="#dedbd5"/><path d="M505 0H720V840H132Z" '
                               'fill="#c8c6c0"/><path d="M555 0H720V840H335Z" '
                               'fill="#b4b2ac"/><path d="M0 765H720" stroke="#8e8a82"/><ellipse '
                               'cx="355" cy="765" rx="176" ry="13" fill="#8d8a83"/><path d="M341 '
                               '122q-20-62 17-78q45-10 52 35q-1 34-32 46l5 48-54 6Z" '
                               'fill="#b4a284"/><path d="M340 97q-24-39-1-63q18-23 50-6q25 8 24 '
                               '43l-17-9-7 18-22-7-6 28Z" fill="#141414"/><path d="M330 150L278 '
                               '184L247 359L213 640L290 657L318 441L360 641L458 633L417 349L424 '
                               '191L381 154L358 227Z" fill="#141414"/><path d="M278 185L233 '
                               '220L172 445L202 465L283 316M422 193L453 220L503 431L477 450L411 '
                               '322" fill="#292828"/><path d="M331 153L358 228L302 292L317 '
                               '214ZM380 154L358 228L399 292L397 210Z" fill="#f7f4ee"/><path '
                               'd="M358 228L359 620M278 337L313 320M398 320L424 337" '
                               'stroke="#7e7b75" stroke-width="2"/><path d="M302 651L293 766L311 '
                               '772L343 655M382 641L421 764L441 758L418 636" fill="#b4a284"/><path '
                               'd="M293 756L277 780L319 780L313 761M421 752L417 780L461 780L438 '
                               '750" fill="#141414"/><path d="M173 444l-8 24q12 22 25 3l12-17M479 '
                               '443l6 26q20 14 24-9l-7-30" fill="#b4a284"/><path d="M50 55H90M50 '
                               '55V95M670 785H630M670 785V745" stroke="#f7f4ee" fill="none"/><text '
                               'x="54" y="818" fill="#141414" font-family="serif" font-size="14" '
                               'letter-spacing="5">SILHOUETTE / ORIGINAL FASHION '
                               'PLATE</text></svg>'},
 'daylight-objects': {'profile': 'nordic',
                      'tags': ['scene', 'interior', 'timber', 'lamp'],
                      'svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 840" '
                             'role="img" aria-label="A quiet daylight interior with an original '
                             'timber chair, layered pendant lamp and matte ceramic vessel"><rect '
                             'width="720" height="840" fill="#eceff4"/><path d="M0 590H720V840H0Z" '
                             'fill="#d3c6ac"/><path d="M0 590L720 584M0 674H720M0 760H720M110 '
                             '590L80 840M365 590L369 840M615 590L660 840" stroke="#b8a58a"/><path '
                             'd="M70 60H310V430H70Z" fill="#d8e2e8"/><path d="M190 60V430M70 '
                             '243H310" stroke="#f8fafb" stroke-width="10"/><path d="M70 430L310 '
                             '430L600 700L140 700Z" fill="#f2eee4" opacity=".6"/><path d="M488 '
                             '0V197" stroke="#4c566a" stroke-width="3"/><path d="M422 198Q488 138 '
                             '554 198Z" fill="#f8fafb" stroke="#b8c1c7"/><path d="M404 217Q488 162 '
                             '572 217Z" fill="#f8fafb" stroke="#b8c1c7"/><path d="M430 237Q488 195 '
                             '546 237Z" fill="#f8fafb" stroke="#b8c1c7"/><path d="M195 540Q180 450 '
                             '211 422L355 405Q402 423 380 532Z" fill="#bda17c"/><path d="M207 '
                             '435Q293 470 372 423M207 463Q293 492 374 454M210 489Q293 513 373 482" '
                             'fill="none" stroke="#d7c3a3" stroke-width="4"/><path d="M196 540L375 '
                             '531L395 576L183 588Z" fill="#88a39e"/><path d="M205 582L176 745M366 '
                             '576L409 730M220 548L242 707M349 548L332 701" stroke="#a78a65" '
                             'stroke-width="12"/><ellipse cx="550" cy="601" rx="87" ry="20" '
                             'fill="#d8dee9"/><path d="M472 601v15q80 38 156-4v-11Z" '
                             'fill="#aeb8bb"/><path d="M498 617L486 742M603 617L618 742" '
                             'stroke="#4c566a" stroke-width="5"/><path d="M524 525Q510 550 525 '
                             '591Q548 608 570 589Q585 551 570 525Z" fill="#e6dfd0"/><ellipse '
                             'cx="547" cy="525" rx="23" ry="6" fill="#b8ad98"/><path d="M548 '
                             '525Q532 471 559 411M548 501Q578 490 584 465M548 474Q525 463 519 442" '
                             'fill="none" stroke="#758364" stroke-width="3"/><text x="42" y="802" '
                             'fill="#4c566a" font-family="sans-serif" font-size="14" '
                             'letter-spacing="3">OBJECTS FOR EVERYDAY LIFE / 01</text></svg>'},
 'workshop-study': {'profile': 'bauhaus',
                    'tags': ['scene', 'geometry', 'workshop'],
                    'svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 840" '
                           'role="img" aria-label="An original asymmetrical workshop study in '
                           'geometric form and measured colour"><rect width="720" height="840" '
                           'fill="#e8e1d2"/><path d="M60 60H660V780H60Z" fill="none" '
                           'stroke="#191919"/><circle cx="421" cy="276" r="178" '
                           'fill="#b42e23"/><path d="M100 470L363 128L363 470Z" '
                           'fill="#23539b"/><path d="M250 433H592V690H250Z" '
                           'fill="#e1af32"/><circle cx="250" cy="562" r="129" '
                           'fill="#191919"/><path d="M60 690H660M592 60V780M60 433H660" '
                           'stroke="#191919" stroke-width="2"/><g font-family="sans-serif" '
                           'fill="#191919"><text x="83" y="111" font-size="23">FORM / '
                           'MATERIAL</text><text x="83" y="750" font-size="21">STUDY 01 — WORKSHOP '
                           'EDITION</text></g></svg>'},
 'iris-whiplash': {'profile': 'art-nouveau',
                   'tags': ['scene', 'botanical', 'iris', 'whiplash'],
                   'svg': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 840" '
                          'role="img" aria-label="An original iris botanical plate with a '
                          'continuous whiplash border"><rect width="720" height="840" '
                          'fill="#f2e9d5"/><path d="M48 800V130Q48 40 140 40H580Q672 40 672 '
                          '130V800Z" fill="none" stroke="#887957" stroke-width="2"/><circle '
                          'cx="360" cy="278" r="198" fill="#e3d5b8"/><circle cx="360" cy="278" '
                          'r="180" fill="none" stroke="#887957"/><g fill="none" stroke="#405840" '
                          'stroke-width="4"><path d="M80 800C125 535 20 610 110 370S140 110 82 '
                          '40M640 800C595 535 700 610 610 370S580 110 638 40M96 800C170 590 49 600 '
                          '140 367S190 128 103 40M624 800C550 590 671 600 580 367S530 128 617 '
                          '40"/><path d="M325 800Q378 572 360 275M354 687Q232 640 219 474M358 '
                          '570Q458 480 497 335M328 762Q441 704 465 570"/></g><g '
                          'fill="#405840"><path d="M326 797Q228 646 243 548Q325 665 326 797M348 '
                          '738Q465 618 481 489Q377 575 348 738M360 621Q289 532 292 417Q358 500 360 '
                          '621"/></g><g fill="#914d37" stroke="#887957" stroke-width="2"><path '
                          'd="M360 289Q254 278 275 203Q319 178 351 246Q324 152 362 132Q402 155 377 '
                          '245Q423 163 458 208Q467 271 378 289Q422 309 391 346Q357 329 360 289Q325 '
                          '352 299 317Q296 283 360 289Z"/><path d="M497 345Q444 323 455 278Q486 '
                          '264 495 314Q495 252 524 257Q553 285 520 328Q563 308 565 339Q543 367 511 '
                          '352Z"/></g><g fill="#887957"><circle cx="360" cy="284" r="12"/><circle '
                          'cx="507" cy="339" r="8"/></g><path d="M160 785Q360 745 560 785" '
                          'fill="none" stroke="#887957" stroke-width="2"/></svg>'}})
PROFILES['dark-academia']['hero_asset'] = 'reading-room'
PROFILES['cyberpunk']['hero_asset'] = 'night-city-feed'
PROFILES['high-fashion']['hero_asset'] = 'couture-silhouette'
PROFILES['nordic']['hero_asset'] = 'daylight-objects'
PROFILES['bauhaus']['hero_asset'] = 'workshop-study'
PROFILES['art-nouveau']['hero_asset'] = 'iris-whiplash'

PROFILES['nordic']['modes'] = {'daylight': dict(bg='#f4f3ed',bg2='#e7e7df',surface='#ffffff',text='#29332d',muted='#5b6258',accent='#3c605b',accent2='#bda17c',border='#bec5ba',**{'on-accent':'#ffffff','surface-glass':'#ffffff'})}
PALETTES.append(dict(id='nordic-daylight',style='nordic',name='Nordic — Daylight Objects',colors=['#f4f3ed','#e7e7df','#29332d','#3c605b','#bda17c','#5b6258'],tags=['nordic','scandinavian','daylight','timber','matte']))

STYLE_RESEARCH = "# Distinct styles: evidence and implementation\n\nResearch date: 2026-10-18. Local source: `wikipedia_en_all_maxi_2026-02`, served by the user's Ultra-PC Kiwix library. Eight canonical articles were read locally, with additional institutional web research. The interpretations below are design decisions based on those sources; they are not claims that a contemporary web page is a historical artifact.\n\n## What was weak\n\nThe earlier previews reused a heading, one small motif and a button. Many full-page starters reused the same three feature cards and stock copy. Changing the palette and font did not expose the profile's composition, material or imagery. The atlas now uses complete pages and labels palette/system registers separately from visual styles. Its grayscale control lets the user inspect structure without color.\n\n## Dark Academia\n\nLocal Wikipedia describes literature, libraries, Collegiate Gothic architecture, dark wood, candlelight and cluttered scholarly interiors. Bulaitis's research connects the aesthetic to cultivated nostalgia and imagined academic spaces. This supports an inhabited reading room rather than a uniform brown dashboard.\n\nImplemented: `scholar-folio`, original `reading-room` SVG, double-rule manuscript framing, italic introduction, a reading index, drop cap and handwritten marginal note. No faux quotations, institution crests or copied historical artworks.\n\n## Cyberpunk\n\nLocal Wikipedia connects technological sophistication with social decay. BFI describes Blade Runner's grungy industrial city, rain, deep shadows and film-noir composition. These references support density, retrofitted structure and emissive signage rather than decorative cyan buttons on roomy cards.\n\nImplemented: `signal-console`, original `night-city-feed` SVG, status rail, chamfered controls, dense telemetry and a compact channel list. Existing dark palette remains; decorative rain and scanlines do not obscure labels or reading text.\n\n## High Fashion\n\nThe local Brodovitch article establishes the editorial lineage. MoMA's HTF Didot record explains the revival of Bazaar's earlier art direction and the typeface's extreme thick/thin contrast and display purpose. We use the already licensed local Bodoni Moda as a practical Didone companion, without claiming it is Didot.\n\nImplemented: `atelier-spread`, monumental display, portrait-format `couture-silhouette` art, an asymmetric campaign composition, hairlines and a boxless look index. The original fashion illustration is an offline fallback, clearly identified. Owned campaign photography remains the best extension when a project has it; a decorative icon is not a substitute for campaign art direction.\n\n## Nordic / Scandinavian Modern\n\nLocal Wikipedia emphasizes simplicity, function, household objects and democratic design; it also records vivid textiles. Designmuseum Danmark's material research emphasizes natural materials and practical experimentation. Scandinavian design cannot be defined solely as a cold desaturated terminal palette.\n\nImplemented: `nordic-catalog`, original `daylight-objects` interior, practical material index and a named `daylight` token mode. Existing `nordic-frost` application colors remain the default for existing software. The daylight mode is selected only by the named web composition. No claim that all Nordic design is pale, minimal or colorless.\n\n## Stronger alternatives\n\n- **Bauhaus / Workshop Modernism** (`bauhaus`): asymmetric modular poster, functional large numerals and an original form study. MoMA describes a laboratory connecting form studies to applied arts. Bauhaus Dessau cautions against reducing the movement to primary-color clichés. Our red/blue/ochre study is one palette, not the definition of the school.\n- **Art Nouveau / Botanical Line** (`art-nouveau`): vertical botanical plate, continuous organic frame and whiplash line. V&A ties this line to natural forms across the decorative arts. Distinguish it from Art Deco's symmetry, steps and fan geometry.\n- **Avant Basic** remains available as a contemporary Memphis-influenced direction. The local Memphis article provides the lineage; it is not silently renamed to imply that the two are identical.\n- **Swiss International** keeps asymmetric grids, functional type and flush-left text. It remains distinct from fashion's image-led composition and Bauhaus workshop studies.\n\n## Selection guidance\n\nThe atlas labels **20 visual styles** and **7 system/color registers**. Neutral, Hi-Contrast, Pastel, Earthy, Jewel, Ultraviolet and Ember remain useful; they are not presented as seven distinct historical movements. Preserve established application identities when using these registers. For a new project seeking a stronger language, begin with a visual style and its composition, art IDs and profile rules; choose effects afterwards.\n\nStart with `web/STYLE-INDEX.md` or `assets web context style/<id>`. The compact context lists the selected layout, art IDs and files. CSS, SVG and typography stay local, so research and rendering are not repeated in cloud prompts.\n\n## Asset provenance\n\n`reading-room`, `night-city-feed`, `couture-silhouette`, `daylight-objects`, `workshop-study` and `iris-whiplash` are original SVG geometry authored for this vault. Research links are references, not downloaded artwork or font licenses. Existing locally vendored font licenses remain attached to portable exports.\n\n## Sources\n\n### dark-academia\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Dark_academia)\n- [Institutional reference](https://pure-oai.bham.ac.uk/ws/portalfiles/portal/278801182/os-10894-bulaitis_1_.pdf)\n\n### cyberpunk\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Cyberpunk)\n- [Institutional reference](https://www.bfi.org.uk/features/blade-runner)\n\n### high-fashion\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Alexey_Brodovitch)\n- [Institutional reference](https://www.moma.org/collection/works/139304)\n\n### nordic\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Scandinavian_design)\n- [Institutional reference](https://designmuseum.dk/en/exhibition/matters/)\n\n### bauhaus\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Bauhaus)\n- [Institutional reference](https://www.moma.org/calendar/galleries/5388)\n- [Institutional reference](https://bauhaus-dessau.de/en/adidas/)\n\n### art-nouveau\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Art_Nouveau)\n- [Institutional reference](https://www.vam.ac.uk/articles/the-whiplash/)\n\n### swiss-international\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/International_Typographic_Style)\n\n### avant-basic\n\n- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Memphis_Group)\n"
STYLE_SOURCES = {'art-nouveau': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Art_Nouveau',
                 'https://www.vam.ac.uk/articles/the-whiplash/'],
 'avant-basic': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Memphis_Group'],
 'bauhaus': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Bauhaus',
             'https://www.moma.org/calendar/galleries/5388',
             'https://bauhaus-dessau.de/en/adidas/'],
 'cyberpunk': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Cyberpunk',
               'https://www.bfi.org.uk/features/blade-runner'],
 'dark-academia': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Dark_academia',
                   'https://pure-oai.bham.ac.uk/ws/portalfiles/portal/278801182/os-10894-bulaitis_1_.pdf'],
 'high-fashion': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Alexey_Brodovitch',
                  'https://www.moma.org/collection/works/139304'],
 'nordic': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Scandinavian_design',
            'https://designmuseum.dk/en/exhibition/matters/'],
 'swiss-international': ['http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/International_Typographic_Style']}
for _style, _links in STYLE_SOURCES.items():
    PROFILES[_style]['sources'] = _links
PROFILES['dark-academia']['origins'] = 'An internet aesthetic around literature, idealized scholarship and collegiate spaces, documented locally as emerging on Tumblr in 2015. It reworks older architecture, clothing, books and academic imagery through modern popular culture; it is not a historical architectural movement.'
PROFILES['high-fashion']['rules'] = 'DO give one campaign image or original fashion plate real scale, set Didone display against legible reading text, use precise folios and cut surplus elements. DO NOT add gradient type, rounded cards, glow or decorative UI chrome.'

def _esc(s: str) -> str:
    import html as _h
    return _h.escape(s, quote=True)


def _demo_style_card(key: str, s: dict) -> str:
    from . import webassets
    direction=webassets.STYLE_DESIGNS[key]
    return (f'<div class="cell"><iframe class="style-preview" title="{_esc(key)} preview" '
            f'loading="lazy" sandbox="allow-same-origin" src="web/styles/{_esc(key)}/index.html"></iframe>'
            f'<div class="lbl"><b>{key}</b> · <code>assets kit {key}</code><br>'
            f'{_esc(direction["kind"])} · <a href="web/styles/{_esc(key)}/index.html">Full design specimen ↗</a></div></div>')


def _demo_profile_card(pid: str, p: dict) -> str:
    pal = find_palette(p.get("palette", ""))
    t = STYLES.get(p["style"], {}).get("tokens", {})
    acc = t.get("accent", "#4ba3e3")
    sws = "".join(f'<i style="background:{c}"></i>' for c in
                  (pal["colors"] if pal else []))
    shapes = "".join(
        f'<span style="color:{acc}">{SHAPES[s]["svg"]}</span>'
        for s in p.get("shapes", [])[:3] if s in SHAPES)
    fonts = ", ".join(v for k, v in p.get("fonts", {}).items() if k != "files")
    return (
        f'<div class="cell prof" style="--pa:{acc}">'
        f'<b>{_esc(p["label"])}</b> <code>{pid}</code>'
        f'<div class="era">{_esc(p.get("era", ""))}</div>'
        f'<div class="vibe">{_esc(p.get("vibe", "")[:170])}…</div>'
        f'<div class="sw" style="height:22px">{sws}</div>'
        f'<div class="meta">fonts: {_esc(fonts)} · gloss: '
        f'{_esc(p.get("gloss", "")[:60])}…</div>'
        f'<div class="shapes">{shapes}</div>'
        f'<div class="lbl">full brief: <code>assets profile {pid}</code> · '
        f'<a style="color:var(--acc)" href="profiles/{pid}.md">profiles/{pid}.md</a>'
        f'</div></div>')


def _demo_layout_cell(key: str, v: dict) -> str:
    doc = ("<!DOCTYPE html><style>body{margin:0;font:15px/1.5 'Segoe UI',"
           "sans-serif;color:#222;background:#fff}</style>" + v["html"])
    return (f'<div class="cell"><div class="thumb">'
            f'<iframe loading="lazy" srcdoc="{_esc(doc)}"></iframe></div>'
            f'<div class="lbl"><b>{key}</b> — {_esc(v.get("best_for", ""))}'
            f'</div></div>')


def _write_demo() -> None:
    """Generate demo.html from the vault data itself — every style, profile,
    palette, gradient, pattern, layout, shape and font, with live visual
    examples. Runs inside sync(), so the demo can never lag the vault."""
    from datetime import datetime
    L: list[str] = []
    counts = {"styles": len(STYLES), "profiles": len(PROFILES),
              "palettes": len(PALETTES), "gradients": len(GRADIENTS),
              "patterns": len(PATTERNS), "layouts": len(LAYOUTS),
              "shapes": len(SHAPES), "fonts": len(list(FONT_DIR.glob("*.woff2")))}
    nav = " · ".join(f'<a href="#{k}">{k} {v}</a>' for k, v in counts.items())
    L.append("<!DOCTYPE html><html><head><meta charset='utf-8'>"
             "<meta name='viewport' content='width=device-width,initial-scale=1'>"
             "<title>Ultra-PC Design Vault — live demo</title>"
             "<link rel='stylesheet' href='fonts/fonts.css'>"
             f"<style>{_DEMO_CSS}\n.style-preview{{width:100%;height:250px;border:0;}}"
             "</style></head><body>")
    L.append(f"<header><b>Ultra-PC Design Vault</b>{nav}"
             "<a href='showcase.html'>Profile showcase</a>"
             "<a href='web/index.html'>Modern web playground ↗</a></header><main>")

    L.append(f'<h2 id="styles">Styles &amp; Themes <small>{len(STYLES)} — '
             'each card rendered from its own tokens</small></h2>'
             '<p class="hint">Every card below is drawn live from that '
             'style’s token set — <code>assets kit &lt;id&gt;</code> '
             'writes the full stylesheet.</p><div class="grid g-style">')
    L += [_demo_style_card(k, s) for k, s in STYLES.items()]
    L.append("</div>")

    L.append(f'<h2 id="profiles">Design Profiles <small>{len(PROFILES)} '
             'archetype collections</small></h2>'
             '<p class="hint">Full design-language briefs: 20 narrative '
             'sections each. Swatches, fonts and signature shapes shown; '
             '<code>assets profile &lt;id&gt;</code> prints everything.</p>'
             '<div class="grid g-prof">')
    L += [_demo_profile_card(pid, p) for pid, p in PROFILES.items()]
    L.append("</div>")

    L.append(f'<h2 id="palettes">Palettes <small>{len(PALETTES)}</small></h2>'
             '<div class="grid g-pal">')
    for p in PALETTES:
        sws = "".join(f'<i style="background:{c}"></i>' for c in p["colors"])
        L.append(f'<div class="cell"><div class="sw">{sws}</div>'
                 f'<div class="lbl"><b>{_esc(p["name"])}</b> '
                 f'<code>{p["id"]}</code></div>'
                 f'<div class="hexes">{" ".join(p["colors"])}</div></div>')
    L.append("</div>")

    L.append(f'<h2 id="gradients">Gradients <small>{len(GRADIENTS)}</small>'
             '</h2><div class="grid g-tile">')
    for k, g in GRADIENTS.items():
        L.append(f'<div class="cell"><div class="tile" '
                 f'style="background:{g["css"]}"></div>'
                 f'<div class="lbl"><b>{k}</b> · {g["style"]}</div></div>')
    L.append("</div>")

    pat_css = "\n".join(v["code"] for v in PATTERNS.values())
    L.append(f'<style>{pat_css}</style>')
    L.append(f'<h2 id="patterns">Patterns <small>{len(PATTERNS)}</small></h2>'
             '<div class="grid g-tile">')
    for k, v in PATTERNS.items():
        m = re.search(r"\.([\w-]+)", v["code"])
        cls = m.group(1) if m else ""
        L.append(f'<div class="cell"><div class="tile {cls}"></div>'
                 f'<div class="lbl"><b>{k}</b> — {_esc(v["desc"][:46])}</div>'
                 f'</div>')
    L.append("</div>")

    L.append(f'<h2 id="layouts">Layouts <small>{len(LAYOUTS)} — live scaled '
             'previews</small></h2><div class="grid g-layout">')
    L += [_demo_layout_cell(k, v) for k, v in LAYOUTS.items()]
    L.append("</div>")

    L.append(f'<h2 id="shapes">Shapes <small>{len(SHAPES)} signature motifs'
             '</small></h2><p class="hint">currentColor SVGs — shown in '
             'their profile’s accent.</p><div class="grid g-shape">')
    for k, v in SHAPES.items():
        prof = PROFILES.get(v.get("profile", ""), {})
        acc = STYLES.get(prof.get("style", ""), {}).get(
            "tokens", {}).get("accent", "#4ba3e3")
        L.append(f'<div class="cell"><div class="shapebox" '
                 f'style="color:{acc}">{v["svg"]}</div>'
                 f'<div class="lbl"><b>{k}</b><br>{v.get("profile", "")}'
                 f'</div></div>')
    L.append("</div>")

    L.append(f'<h2 id="fonts">Fonts <small>{len(list(FONT_DIR.glob("*.woff2")))} vendored faces'
             '</small></h2>')
    for stem, (family, weight, note) in FONT_MAP.items():
        if not (FONT_DIR / f"{stem}.woff2").exists():
            continue
        L.append(f'<div class="fontrow"><div class="name">{family} '
                 f'{weight}<br><span style="font-size:10.5px">{_esc(note)}'
                 f'</span></div><div class="sample" style="font-family:'
                 f"'{family}';font-weight:{weight}\">The quick brown fox "
                 f'jumps over 13 lazy dogs — 0123456789</div></div>')

    L.append(f"<footer>Generated by <code>assets sync</code> on "
             f"{datetime.now():%Y-%m-%d %H:%M} — this page is rebuilt from "
             "the vault data on every sync, so anything added to the vault "
             "appears here automatically. Open anytime: "
             "<code>ultra assets demo</code></footer></main></body></html>")
    DEMO.write_text("\n".join(L), encoding="utf-8")


def _write_showcase() -> None:
    """Compare complete profile compositions, including a grayscale structure view."""
    from . import webassets
    SHOWCASE.write_text(webassets.style_gallery(prefix='web/styles/',fonts='fonts/fonts.css',vault='web/index.html',research='STYLE-RESEARCH.md'),encoding='utf-8')


def cmd_demo() -> int:
    """(Re)build the live demo page from vault data and open it."""
    _write_demo()
    print(f"Demo rebuilt from vault data -> {DEMO}")
    core.open_in_os(DEMO)
    return 0


# --------------------------------------------------------------------------- #
#  Sync curated content to disk + build manifest + catalog
# --------------------------------------------------------------------------- #

def _ensure_dirs() -> None:
    for d in (ASSETS_DIR, PALETTE_DIR, CSS_DIR, ANIM_DIR, FONT_DIR, LIB_DIR,
              GRAD_DIR, PATTERN_DIR, ART_DIR, LAYOUT_DIR, TECH_DIR, CREATIVE_DIR,
              ASCII_DIR, NATIVE_DIR, PROFILE_DIR, SHAPES_DIR, EXPORT_DIR):
        d.mkdir(parents=True, exist_ok=True)


# Vendored font files -> (CSS family name, weight, which style it suits)
FONT_MAP = {
    "inter-400": ("Inter", 400, "neutral / body text everywhere"),
    "inter-700": ("Inter", 700, "neutral / bold headings"),
    "space-grotesk-400": ("Space Grotesk", 400, "mono / vaporwave body"),
    "space-grotesk-600": ("Space Grotesk", 600, "neutral display"),
    "dm-sans-400": ("DM Sans", 400, "ember body"),
    "fraunces-400": ("Fraunces", 400, "jewel body"),
    "quicksand-400": ("Quicksand", 400, "pastel body"),
    "space-grotesk-500": ("Space Grotesk", 500, "modern display headings"),
    "jetbrains-mono-400": ("JetBrains Mono", 400, "code / cyberpunk mono"),
    "orbitron-700": ("Orbitron", 700, "cyberpunk / sci-fi headings"),
    "vt323-400": ("VT323", 400, "retro CRT terminal"),
    "press-start-2p-400": ("Press Start 2P", 400, "Y2K / 8-bit arcade"),
    "quicksand-500": ("Quicksand", 500, "rounded / friendly / pastel body"),
    "poppins-600": ("Poppins", 600, "geometric / friendly headings"),
    "playfair-display-700": ("Playfair Display", 700, "elegant serif display / editorial"),
    "lora-400": ("Lora", 400, "readable serif body / editorial"),
    "fraunces-600": ("Fraunces", 600, "fancy serif display / jewel"),
    "dm-sans-500": ("DM Sans", 500, "clean geometric sans / neutral"),
    "bebas-neue-400": ("Bebas Neue", 400, "condensed bold headline"),
    "sora-600": ("Sora", 600, "modern display / tech"),
    "archivo-black-400": ("Archivo Black", 400, "heavy display / brutalist"),
    "caveat-400": ("Caveat", 400, "handwriting / playful accent"),
    "fira-code-400": ("Fira Code", 400, "mono w/ ligatures / code"),
    "righteous-400": ("Righteous", 400, "retro rounded display / Y2K"),
    # wave 3 — design-profile display faces
    "shrikhand-400": ("Shrikhand", 400, "avant-basic / groovy bubble display"),
    "fredoka-500": ("Fredoka", 500, "avant-basic body / frutiger-metro display"),
    "bodoni-moda-700": ("Bodoni Moda", 700, "high-fashion Didone masthead"),
    "permanent-marker-400": ("Permanent Marker", 400, "skate hand-marker accent"),
    "bangers-400": ("Bangers", 400, "skate/pop loud display"),
    "poiret-one-400": ("Poiret One", 400, "art-deco tall geometric display"),
    "cinzel-600": ("Cinzel", 600, "art-deco/mosaic engraved roman"),
    "alfa-slab-one-400": ("Alfa Slab One", 400, "2000s-preppy varsity slab"),
    "pacifico-400": ("Pacifico", 400, "preppy script accent"),
}


def _write_fonts_css() -> list[dict]:
    """Emit @font-face rules for whatever woff2 files are vendored. Returns a
    list describing each so the catalog can list them."""
    if not FONT_DIR.exists():
        return []
    found: list[dict] = []
    blocks: list[str] = ["/* Vendored open fonts (OFL). @import or <link> this "
                         "file, then use the family names below. */\n"]
    for f in sorted(FONT_DIR.glob("*.woff2")):
        stem = f.stem
        family, weight, use = FONT_MAP.get(
            stem, (stem.replace("-", " ").title(), 400, ""))
        blocks.append(
            f"@font-face {{\n"
            f"  font-family: '{family}';\n"
            f"  font-style: normal;\n"
            f"  font-weight: {weight};\n"
            f"  font-display: swap;\n"
            f"  src: url('./{f.name}') format('woff2');\n"
            f"}}")
        found.append({"file": f.name, "family": family, "weight": weight, "use": use})
    (FONT_DIR / "fonts.css").write_text("\n".join(blocks) + "\n", encoding="utf-8")
    return found


def _scan_libraries() -> list[dict]:
    """Discover vendored OSS libraries on disk (added by the downloader)."""
    libs: list[dict] = []
    if not LIB_DIR.exists():
        return libs
    for p in sorted(LIB_DIR.rglob("*")):
        if p.is_file() and p.suffix.lower() in (".css", ".js", ".woff2", ".ttf", ".otf"):
            libs.append({"path": str(p.relative_to(ASSETS_DIR)),
                         "bytes": p.stat().st_size})
    return libs


def _relative_luminance(hex_color: str) -> float:
    """WCAG relative luminance, used to tell a light style from a dark one."""
    r, g, b = (c / 255 for c in _hex_rgb(hex_color))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def is_reversed(style: str) -> bool:
    """True when the style sets light type on a dark field."""
    return _relative_luminance(STYLES[style]["tokens"]["bg"]) < 0.5


def _leading(style: str) -> float:
    """Line height, computed rather than stored.

    Two rules from typographic practice, both relationships rather than
    constants: leading tracks the measure (a wide column needs more of it, a
    narrow one can give some back), and reversed text — light on dark — needs
    more again, because the glyphs bloom optically against the dark field.
    A flat `line-height: 1.6` for all 25 styles gets both wrong at the edges.
    """
    e = EXEC[style]
    lead = 1.5 + (e["measure"] - 66) * 0.006      # 66 cpl is the hinge
    if is_reversed(style):
        lead += 0.08
    if e["base"] >= 18:                            # large text needs less
        lead -= 0.04
    return round(min(1.85, max(1.35, lead)), 3)


def type_scale(style: str) -> list[str]:
    """The style's permitted type sizes, largest first.

    `sizes` is a budget, not a suggestion: Swiss gets three steps because its
    profile says three, and a generator that wants a fourth has to change the
    profile first.
    """
    e = EXEC[style]
    if "scale_rem" in e:
        return list(e["scale_rem"])
    base, ratio, n = e["base"], e["ratio"], e["sizes"]
    steps = [base * (ratio ** i) for i in range(n - 1, -1, -1)]
    return [f"{round(s / 16, 3)}rem" for s in steps]


def _shadow_for(style: str) -> str:
    """Elevation rendered from the declared model, not copied between styles."""
    e = EXEC[style]
    model, accent = e["elevation"], STYLES[style]["tokens"]["accent"]
    r, g, b = _hex_rgb(accent)
    return {
        "none":  "none",
        "flat":  f"0 0 0 1px {STYLES[style]['tokens']['border']}",
        "soft":  "0 8px 24px rgba(0,0,0,0.18)",
        "hard":  f"{e['border'] + 2}px {e['border'] + 2}px 0 0 "
                 f"{STYLES[style]['tokens']['text']}",
        "glow":  f"0 0 24px rgba({r},{g},{b},0.45)",
    }[model]


def _sheen_for(style: str) -> str:
    """Surface sheen by gloss level — the thing that separates a matte Swiss
    plane from a wet Y2K chrome bubble, and which `--surface-glass` alone
    could never express."""
    return {
        0: "none",
        1: "linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0))",
        2: "linear-gradient(180deg, rgba(255,255,255,0.28), rgba(255,255,255,0) 60%)",
        3: "linear-gradient(180deg, rgba(255,255,255,0.65), rgba(255,255,255,0.08) 45%,"
           " rgba(255,255,255,0) 60%)",
    }[EXEC[style]["gloss"]]


def _tokens_css(style: str) -> str:
    """The style's full token surface: colour, type, grid, motion, material.

    The colour block is what this used to be. Everything after it exists so a
    page can be built to the profile's actual claims instead of just its
    palette.
    """
    s, e = STYLES[style], EXEC[style]
    prof = profile_for(style) or {}
    fonts = prof.get("fonts", {})
    body = fonts.get("body", "Segoe UI")
    display = fonts.get("display", body)
    sizes = type_scale(style)
    lines = [f":root {{  /* {s['label']} */",
             "  /* --- type ------------------------------------------------ */",
             f"  --font: '{body}', {s['font']};",
             f"  --font-display: '{display}', {s['font']};",
             f"  --mono: {s['mono']};",
             f"  --base: {e['base']}px;",
             f"  --ratio: {e['ratio']};",
             f"  --leading: {_leading(style)};",
             f"  --tracking: {e['tracking']};",
             f"  --measure: {e['measure']}ch;",
             f"  --weight-body: {e['weights'][0]};",
             f"  --weight-strong: {e['weights'][-1]};",
             f"  --case: {e['case']};"]
    for i, sz in enumerate(sizes):
        lines.append(f"  --size-{i}: {sz};")
    # one step below body, for captions and badges — without it every
    # component reaches for a hardcoded 0.8rem and leaves the scale behind
    small = max(16 if style == "hi-contrast" else 0, e["base"] / e["ratio"])
    lines.append(f"  --size-sm: {round(small / 16, 3)}rem;")
    lines += ["  /* --- colour ---------------------------------------------- */"]
    for k, v in s["tokens"].items():
        if k in ("radius", "shadow"):
            continue
        lines.append(f"  --{k}: {v};")
    t = s["tokens"]
    on_accent = max(("#000000", "#ffffff"), key=lambda c: _contrast(c, t["accent"]))
    lines.append(f"  --on-accent: {on_accent};")
    lines += ["  /* --- grid ------------------------------------------------ */",
              f"  --columns: {e['columns']};",
              f"  --gutter: {e['gutter']}px;",
              f"  --align: {e['align']};",
              "  /* --- material -------------------------------------------- */",
              f"  --radius: {s['tokens']['radius']};",
              f"  --border-width: {e['border']}px;",
              f"  --gloss: {e['gloss']};",
              f"  --sheen: {_sheen_for(style)};",
              f"  --shadow: {_shadow_for(style)};",
              "  /* --- motion ---------------------------------------------- */",
              f"  --dur: {e['dur']}ms;",
              f"  --ease: {e['ease']};",
              f"  --travel: {e['travel']}px;",
              "}"]
    return "\n".join(lines)


def _write_exports() -> None:
    """Machine-usable exports: JSON (any language) + a Python module so
    tkinter/Python apps (incl. Ultra-PC's own theme) can import the colors."""
    pal = {p["id"]: p["colors"] for p in PALETTES}
    tok = {k: v["tokens"] for k, v in STYLES.items()}
    # The executable half: type scale, grid, motion and material, plus the
    # derived values, so a consumer gets the whole design decision and not
    # just the colours.
    ex = {k: {**v, "weights": list(v["weights"]),
              "leading": _leading(k), "sizes_rem": type_scale(k),
              "reversed": is_reversed(k)} for k, v in EXEC.items()}
    (EXPORT_DIR / "palettes.json").write_text(
        json.dumps({"palettes": pal, "styles": tok, "exec": ex,
                    "gradients": {k: v["css"] for k, v in GRADIENTS.items()}},
                   indent=2), encoding="utf-8")
    py = ['"""Auto-generated by `python ultra.py assets sync`.',
          'Ultra-PC color library for Python / tkinter use.',
          'Do not edit by hand — edit ultrapc/assets.py then re-sync."""',
          "", f"PALETTES = {pal!r}", "", f"STYLES = {tok!r}", "",
          f"EXEC = {ex!r}", "",
          "def palette(name):",
          '    """Return a palette\'s hex list by id (e.g. "nordic-frost")."""',
          "    return PALETTES[name]", "",
          "def tokens(style):",
          '    """Return a style\'s design-token dict (e.g. "earthy")."""',
          "    return STYLES[style]", "",
          "def decisions(style):",
          '    """Type scale, grid, motion and material for a style."""',
          "    return EXEC[style]", ""]
    (EXPORT_DIR / "palettes.py").write_text("\n".join(py), encoding="utf-8")


def sync() -> dict:
    """Write curated content to disk and regenerate manifest + catalog."""
    _ensure_dirs()

    for p in PALETTES:
        (PALETTE_DIR / f"{p['id']}.json").write_text(
            json.dumps(p, indent=2), encoding="utf-8")

    for name, s in CSS_SNIPPETS.items():
        header = f"/* {name} — {s['desc']}  [style: {s['style']}] */\n"
        (CSS_DIR / f"{name}.css").write_text(header + s["css"] + "\n",
                                             encoding="utf-8")

    for name, a in ANIMATIONS.items():
        ext = "js" if a["kind"] == "js" else "css"
        header = (f"/* {name} — {a['desc']}  [style: {a['style']}] */\n")
        (ANIM_DIR / f"{name}.{ext}").write_text(header + a["code"] + "\n",
                                                encoding="utf-8")

    for style in STYLES:
        (CSS_DIR / f"tokens-{style}.css").write_text(
            _tokens_css(style) + "\n", encoding="utf-8")

    for name, g in GRADIENTS.items():
        (GRAD_DIR / f"{name}.css").write_text(
            f"/* {name} — [style: {g['style']}] */\n"
            f".grad-{name} {{ background: {g['css']}; }}\n", encoding="utf-8")

    for name, p in PATTERNS.items():
        ext = "svg" if p["kind"] == "svg" else "css"
        (PATTERN_DIR / f"{name}.{ext}").write_text(
            f"/* {name} — {p['desc']} */\n" if ext == "css"
            else f"<!-- {name} — {p['desc']} -->\n", encoding="utf-8")
        with (PATTERN_DIR / f"{name}.{ext}").open("a", encoding="utf-8") as fh:
            fh.write(p["code"] + "\n")

    for name, a in SVG_ART.items():
        (ART_DIR / f"{name}.svg").write_text(
            f"<!-- {name} — {a['desc']} -->\n" + a["code"] + "\n", encoding="utf-8")

    for name, t in TECHNIQUES.items():
        (TECH_DIR / f"{name}.css").write_text(
            f"/* {name} — {t['desc']}  [{t['cat']}] */\n" + t["code"] + "\n",
            encoding="utf-8")

    for name, cr in CREATIVE.items():
        (CREATIVE_DIR / f"{name}.html").write_text(
            f"<!-- {name} — {cr['desc']}  [{cr['cat']}]  lib: {cr['lib']} -->\n"
            + cr["code"].replace('src="libraries/', 'src="../libraries/').replace('href="libraries/', 'href="../libraries/') + "\n", encoding="utf-8")

    for name, lay in LAYOUTS.items():
        (LAYOUT_DIR / f"{name}.html").write_text(
            f"<!-- {name} — {lay['desc']}  (best for: {lay['best_for']}) -->\n"
            + lay["html"] + "\n", encoding="utf-8")

    for name, art in ASCII_ART.items():
        (ASCII_DIR / f"{name}.txt").write_text(art["art"].strip("\n") + "\n",
                                               encoding="utf-8")

    for name, rec in NATIVE.items():
        (NATIVE_DIR / f"{name}.py").write_text(
            f'"""{name} — {rec["desc"]}  [native/tkinter · '
            f'module: ultrapc/nativeui.py]"""\n' + rec["code"] + "\n",
            encoding="utf-8")

    for name, sh in SHAPES.items():
        (SHAPES_DIR / f"{name}.svg").write_text(sh["svg"].strip() + "\n",
                                                encoding="utf-8")

    for name, p in PROFILES.items():
        pal = next((x for x in PALETTES if x["id"] == p["palette"]), None)
        lines = [f"# {p['label']}  (design profile: `{name}`)", ""]
        if p.get("era"):
            lines += [f"**Era:** {p['era']}", ""]
        lines += [f"*{p['vibe']}*", ""]
        for head, key in (("Origins", "origins"),
                          ("Composition & space", "composition"),
                          ("Proportion & measure", "proportion"),
                          ("Color logic", "color"),
                          ("Light", "light"),
                          ("Typography", "type"),
                          ("Materiality & finish", "materiality"),
                          ("Motion & rhythm", "motion"),
                          ("Imagery", "imagery"),
                          ("Voice (copy & tone)", "voice"),
                          ("Sound", "sound"),
                          ("Where it lives", "space"),
                          ("Kinship (family tree)", "kinship"),
                          ("Hierarchy of power", "hierarchy"),
                          ("Canon (study these)", "canon"),
                          ("Adaptation (modes & accessibility)", "adaptation")):
            if p.get(key):
                lines += [f"## {head}", "", p[key], ""]
        if p.get("moves"):
            lines += ["## Signature moves", ""]
            lines += [f"{i}. {mv}" for i, mv in enumerate(p["moves"], 1)]
            lines += [""]
        lines += ["## Components (this vault)", "",
                  f"- **tokens/style**: `{p['style']}` "
                  f"(`assets kit {p['style']}` for a full stylesheet)",
                  f"- **palette**: `{p['palette']}`"
                  + (f" — {' '.join(pal['colors'])}" if pal else ""),
                  f"- **fonts**: " + ", ".join(f"{k}: {v}" for k, v in
                                               p["fonts"].items() if k != "files"),
                  f"- **textures (native)**: {', '.join(p['textures'])}",
                  f"- **gloss**: {p['gloss']}",
                  f"- **shapes**: {', '.join(p['shapes'])}",
                  f"- **patterns**: {', '.join(p['patterns']) or '—'}",
                  f"- **techniques (fx)**: {', '.join(p['techniques'])}",
                  "", f"**Rules:** {p['rules']}", ""]
        if p.get("failure"):
            lines += [f"**You've lost the plot when:** {p['failure']}", ""]
        if p.get('hero_asset'):
            lines += ['## Reusable composition', '', 'Hero art: `'+p['hero_asset']+'` (original local SVG). Preview: `web/styles/'+p['style']+'/index.html`.', '']
        if p.get('modes'):
            lines += ['Named modes: '+', '.join('`'+key+'`' for key in p['modes'])+'. Existing applications retain the default mode.', '']
        if p.get('sources'):
            lines += ['## Research references', '', *['- '+url for url in p['sources']], '', 'Interpretation and selection notes: `STYLE-RESEARCH.md`.', '']
        (PROFILE_DIR / f"{name}.md").write_text("\n".join(lines),
                                                encoding="utf-8")

    (ASSETS_DIR/'STYLE-RESEARCH.md').write_text(STYLE_RESEARCH,encoding='utf-8')
    fonts = _write_fonts_css()
    _write_exports()
    _write_demo()          # the live demo page — rebuilt from data every sync
    _write_showcase()

    manifest = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "root": "assets-vault",
        "counts": {"fonts": len(fonts), "libraries": len(_scan_libraries()),
                   "palettes": len(PALETTES), "css": len(CSS_SNIPPETS),
                   "animations": len(ANIMATIONS), "styles": len(STYLES),
                   "gradients": len(GRADIENTS), "patterns": len(PATTERNS),
                   "svg_art": len(SVG_ART), "layouts": len(LAYOUTS),
                   "techniques": len(TECHNIQUES), "creative": len(CREATIVE),
                   "ascii_art": len(ASCII_ART), "native": len(NATIVE),
                   "profiles": len(PROFILES), "shapes": len(SHAPES)},
        "styles": {k: v["tokens"] for k, v in STYLES.items()},
        "exec": {k: {**v, "weights": list(v["weights"]),
                     "leading": _leading(k), "sizes_rem": type_scale(k),
                     "reversed": is_reversed(k)} for k, v in EXEC.items()},
        "palettes": [{"id": p["id"], "name": p["name"], "style": p["style"],
                      "colors": p["colors"], "tags": p["tags"]} for p in PALETTES],
        "css": [{"id": k, "style": v["style"], "tags": v["tags"], "desc": v["desc"]}
                for k, v in CSS_SNIPPETS.items()],
        "animations": [{"id": k, "kind": v["kind"], "style": v["style"],
                        "tags": v["tags"], "desc": v["desc"]}
                       for k, v in ANIMATIONS.items()],
        "gradients": [{"id": k, "style": v["style"], "tags": v["tags"],
                       "css": v["css"]} for k, v in GRADIENTS.items()],
        "patterns": [{"id": k, "kind": v["kind"], "tags": v["tags"],
                      "desc": v["desc"]} for k, v in PATTERNS.items()],
        "svg_art": [{"id": k, "tags": v["tags"], "desc": v["desc"]}
                    for k, v in SVG_ART.items()],
        "layouts": [{"id": k, "best_for": v["best_for"], "desc": v["desc"]}
                    for k, v in LAYOUTS.items()],
        "techniques": [{"id": k, "cat": v["cat"], "tags": v["tags"],
                        "desc": v["desc"]} for k, v in TECHNIQUES.items()],
        "creative": [{"id": k, "cat": v["cat"], "lib": v["lib"],
                      "tags": v["tags"], "desc": v["desc"]}
                     for k, v in CREATIVE.items()],
        "ascii_art": [{"id": k, "tags": v["tags"], "desc": v["desc"]}
                      for k, v in ASCII_ART.items()],
        "native": [{"id": k, "tags": v["tags"], "desc": v["desc"]}
                   for k, v in NATIVE.items()],
        "profiles": [{"id": k, "label": v["label"], "style": v["style"],
                      "palette": v["palette"], "shapes": v["shapes"]}
                     for k, v in PROFILES.items()],
        "shapes": [{"id": k, "profile": v["profile"], "tags": v["tags"]}
                   for k, v in SHAPES.items()],
        "fonts": fonts,
        "libraries": _scan_libraries(),
    }
    from . import webassets
    manifest["web"] = webassets.sync()
    manifest["counts"]["web_assets"] = manifest["web"]["assets"]
    manifest["counts"]["web_packs"] = manifest["web"]["packs"]
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_catalog(manifest)
    core.log("assets", f"synced {manifest['counts']}", "SUCCESS")
    return manifest


def _write_catalog(manifest: dict) -> None:
    """The human/Claude-readable DESIGN-SYSTEM.md — read this before building UI."""
    L: list[str] = []
    L.append("# Ultra-PC Design System — offline asset vault\n")
    L.append("> Curated palettes, gradients, patterns, CSS, and animations so "
             "apps look polished by default.\n> **The user requires aesthetics to come from this vault, not model defaults.**\n> **Consult this before building "
             "any UI.** Query from the repository root:\n")
    L.append("```\npython ultra.py assets palettes [query]   # color palettes\n"
             "python ultra.py assets gradients [query]  # ready CSS gradients\n"
             "python ultra.py assets patterns [query]   # SVG/CSS backgrounds\n"
             "python ultra.py assets art [query]        # SVG icons/dividers/heroes\n"
             "python ultra.py assets layouts [query]    # page-structure templates\n"
             "python ultra.py assets fx [query]         # advanced CSS techniques\n"
             "python ultra.py assets creative [query]   # shaders/3D/motion/generative (beyond CSS)\n"
             "python ultra.py assets native [query]     # tkinter/PIL desktop-app depth (NOT web)\n"
             "python ultra.py assets css [query]        # CSS snippets/components\n"
             "python ultra.py assets anim [query]       # animations (incl. text FX)\n"
             "python ultra.py assets kit <style> [dir]  # full themed stylesheet\n"
             "python ultra.py assets show <id>          # print an asset to paste\n"
             "python ultra.py assets scaffold <dir> --style <name>\n"
             "python ultra.py assets check [style]      # audit kits against their profiles\n```\n")
    L.append("**To save tokens: reference an asset by id and run `assets show "
             "<id>` (or copy from the on-disk files) instead of regenerating "
             "colors/gradients/SVG/CSS from scratch.** Everything here is "
             "already tuned — pick, don't re-derive.\n")
    L.append("Vault root: `assets-vault/` (relative to the repository root)  ·  Python/tkinter import: "
             "`exports/palettes.py` · JSON: `exports/palettes.json` · "
             "regenerate: `python ultra.py assets sync`\n")

    L.append("## Modern web production assets\n")
    L.append("For motion, color effects, transparency, responsive compositions and working interactions, "
             "start with **`web/MODEL-INDEX.md`**. It is a compact ID/path index, not source code. "
             "The interactive local browser is `web/index.html`.\n")
    L.append("```sh\npython ultra.py assets web packs\n"
             "python ultra.py assets web search glass --style ultraviolet\n"
             "python ultra.py assets web context luminous-product\n"
             "python ultra.py assets web build luminous-product ./my-site\n"
             "python ultra.py assets web build glass-command ./workspace --zip\n"
             "python ultra.py assets web gallery\n```\n")
    L.append(f"{manifest['counts']['web_assets']} working modules · {manifest['counts']['web_packs']} complete page packs · native browser runtime · "
             "local fonts · no CDN or cloud call. Use the compact context command and the "
             "generated AI-BRIEF.md in model prompts; reuse the emitted CSS/JS files. "
             "Knobs, compatibility constraints, static fallbacks and cleanup are documented per asset.\n")
    L.append("## Distinct visual languages\n")
    L.append("Compare `web/styles/index.html` (or `showcase.html`), use the grayscale structure check, and read `web/STYLE-INDEX.md`. The atlas distinguishes 20 visual styles from 7 useful system/color registers. Research and source links: `STYLE-RESEARCH.md`.\n")
    L.append("## Styles / design tokens\n")
    L.append("Each style ships a `tokens-<style>.css` `:root` block — colour, "
             "**and** the type scale, grid, motion and material decisions its "
             "profile describes. Start from these rather than inventing "
             "sizes, leading or easing.\n")
    L.append("| style | bg · accent · text | type | grid | material | motion |")
    L.append("|---|---|---|---|---|---|")
    for k, v in STYLES.items():
        t, e = v["tokens"], EXEC[k]
        L.append(
            f"| **{v['label']}** (`{k}`) "
            f"| `{t['bg']}` `{t['accent']}` `{t['text']}` "
            f"| {e['sizes']} sizes @ {e['ratio']} · {e['measure']}ch · "
            f"lead {_leading(k)} "
            f"| {e['columns']} col / {e['gutter']}px · {e['align']} "
            f"| gloss {e['gloss']} · {e['elevation']} · r{t['radius']} "
            f"| {e['dur']}ms {e['ease']} |")
    L.append("")
    L.append("Each style also declares what it refuses, and "
             "`assets check` fails the build when a kit breaks its own rule:\n")
    for k in STYLES:
        if EXEC[k]["forbid"]:
            L.append(f"- `{k}` refuses: {', '.join(EXEC[k]['forbid'])}")
    L.append("")
    L.append("Leading is computed, not stored: it tracks the measure and adds "
             "a step for reversed (light-on-dark) text, so a wide dark column "
             "is not set at the same line height as a narrow light one.\n")

    L.append("## Palettes\n")
    _cur = None
    for p in PALETTES:
        if p["style"] != _cur:
            _cur = p["style"]
            L.append(f"\n_{_cur}_")
        L.append(f"- **{p['name']}** (`{p['id']}`) — "
                 f"{' '.join(p['colors'])}  · _{', '.join(p['tags'])}_")
    L.append("")

    L.append("## Gradients  (paste value into `background:`)\n")
    for k, v in GRADIENTS.items():
        L.append(f"- **{k}** ({v['style']}) — `{v['css']}`")
    L.append("")

    L.append("## Background patterns\n")
    for k, v in PATTERNS.items():
        L.append(f"- **{k}** ({v['kind']}) — {v['desc']}")
    L.append("")

    L.append("## SVG art  (icons, dividers, hero illustrations)\n")
    for k, v in SVG_ART.items():
        L.append(f"- **{k}** — {v['desc'].split('.')[0]}.")
    L.append("")

    L.append("## Advanced CSS techniques  (kill the generic-AI look)\n")
    L.append("The moves that make frontends look intricate/artistic instead of "
             "default: layered depth, real texture, custom shapes, blend/filter "
             "compositing, scroll-driven motion. `assets show <id>` for full code.\n")
    _tc = None
    for k, v in TECHNIQUES.items():
        if v["cat"] != _tc:
            _tc = v["cat"]
            L.append(f"\n_{_tc}_")
        L.append(f"- **{k}** — {v['desc']}")
    L.append("")

    L.append("## Creative coding  (beyond CSS — shaders, 3D, motion, generative)\n")
    L.append("For visuals CSS can't reach. Vendored libs live in `libraries/`; "
             "`assets show <id>` prints the full recipe.\n")
    _cc = None
    for k, v in CREATIVE.items():
        if v["cat"] != _cc:
            _cc = v["cat"]
            L.append(f"\n_{_cc}_")
        L.append(f"- **{k}** ({v['lib']}) — {v['desc']}")
    L.append("")

    L.append("## Web layout templates  (page structure / orientation)\n")
    L.append("Token-driven page skeletons — pick the arrangement, pair with a "
             "style's `kit`. `assets show <id>` prints the full HTML.\n")
    for k, v in LAYOUTS.items():
        L.append(f"- **{k}** — {v['desc']}  · _best for: {v['best_for']}_")
    L.append("")

    L.append("## CLI art  (make terminal tools look cool)\n")
    L.append("Reusable module `ultrapc/cliart.py` — `banner(text, font=)` with "
             "**two title fonts** (`block` = thick, `thin` = fine box-drawing / "
             "intricate title cards), `box()`, `gradient()`/`rainbow()` truecolor, "
             "`rule()`, `Spinner`, `progress()`, `loadbar()` animated gradient bar. "
             "Run `python ultra.py assets cli` for a live demo, "
             "`assets banner --font thin \"TEXT\"` for a banner. Ultra-PC's own "
             "boot splash uses `ui.hero()` (thin font) + `ui.boot()` loading bars. "
             "Static pieces:\n")
    for k, v in ASCII_ART.items():
        L.append(f"- **{k}** — {v['desc']}")
    L.append("")

    L.append("## Native / desktop UI  (tkinter + PIL — the vault for Python apps)\n")
    L.append("**CSS and SVG do not render in tkinter.** For native GUI depth use "
             "the self-contained module `ultrapc/nativeui.py` (copy it into any "
             "project — it has fallback tokens, no other deps beyond Pillow). It "
             "renders glass cards, gel buttons, glossy header bars, full-window "
             "scenes and an animated splash, all **style-swappable** by the same "
             "style names as the web vault (frutiger-aero, cyberpunk, pastel, "
             "mono, nordic, …). `assets show native/<id>` prints the recipe; "
             "`assets native preview <style>` renders a static PNG look; "
             "`assets native demo <style>` opens a live window.\n")
    for k, v in NATIVE.items():
        L.append(f"- **{k}** — {v['desc']}  · _{', '.join(v['tags'])}_")
    L.append("")

    L.append("## Design Profiles  (full archetype collections)\n")
    L.append("A profile bundles everything that belongs to one design "
             "language: tokens, palette, fonts, textures + gloss treatment, "
             "signature shapes, matching patterns/fx, and do/don't rules — "
             "researched from design-education sources. "
             "`assets profiles` lists them; `assets profile <id>` prints the "
             "whole collection; `assets kit <style>` themes a page in one "
             "shot; shapes live in `shapes/*.svg` (currentColor).\n")
    for k, v in PROFILES.items():
        L.append(f"- **{k}** ({v['label']}) — {v['vibe'][:110]}…  "
                 f"· shapes: _{', '.join(v['shapes'])}_")
    L.append("")

    L.append("## CSS snippets & components\n")
    for k, v in CSS_SNIPPETS.items():
        L.append(f"- **{k}** ({v['style']}) — {v['desc']}  · _{', '.join(v['tags'])}_")
    L.append("")

    L.append("## Animations  (text-first)\n")
    for k, v in ANIMATIONS.items():
        L.append(f"- **{k}** ({v['kind']}, {v['style']}) — {v['desc']}")
    L.append("")

    fonts = manifest.get("fonts", [])
    L.append("## Fonts (offline, OFL)\n")
    if fonts:
        L.append("Link `fonts/fonts.css`, then use the family name:\n")
        for f in fonts:
            L.append(f"- **{f['family']}** ({f['weight']}) — {f['use']}  "
                     f"·  `fonts/{f['file']}`")
    else:
        L.append("_None vendored yet._")
    L.append("")

    libs = manifest.get("libraries", [])
    L.append("## Vendored libraries (offline)\n")
    if libs:
        for lib in libs:
            L.append(f"- `{lib['path']}`  ({lib['bytes']//1024} KB)")
    else:
        L.append("_None vendored yet — run the assets downloader to add "
                 "Animate.css, fonts, particles, etc._")
    L.append("")
    CATALOG.write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------- #
#  Lookups
# --------------------------------------------------------------------------- #

def _match(query: str, *fields: str) -> bool:
    if not query:
        return True
    q = query.lower()
    return any(q in (f or "").lower() for f in fields)


def find_palette(pid: str) -> dict | None:
    for p in PALETTES:
        if p["id"] == pid:
            return p
    return None


# Which vendored font families suit each style (for the kit + guidance):
# (body font, display/heading font).
STYLE_FONTS = {
    "frutiger-aero": ("Inter", "Poppins"),
    "vaporwave": ("Space Grotesk", "Righteous"),
    "cyberpunk": ("JetBrains Mono", "Orbitron"),
    "neutral": ("Inter", "Space Grotesk"),
    "pastel": ("Quicksand", "Poppins"),
    "earthy": ("Lora", "Fraunces"),
    "editorial": ("Lora", "Playfair Display"),
    "mono": ("Space Grotesk", "Archivo Black"),
    "jewel": ("Fraunces", "Playfair Display"),
    "nordic": ("Inter", "Sora"),
    "golden-archive": ("Fraunces", "Playfair Display"),
    "ultraviolet": ("Sora", "Space Grotesk"),
    "ember": ("DM Sans", "Bebas Neue"),
    "hi-contrast": ("Inter", "Archivo Black"),
    "avant-basic": ("Fredoka", "Shrikhand"),
    "organic-tech": ("DM Sans", "Sora"),
    "high-fashion": ("Lora", "Bodoni Moda"),
    "skate-culture": ("Inter", "Bangers"),
    "mosaic": ("Lora", "Cinzel"),
    "art-deco": ("Poppins", "Poiret One"),
    "frutiger-metro": ("Poppins", "Fredoka"),
    "preppy-2000s": ("Lora", "Alfa Slab One"),
    "y2k-chrome": ("Space Grotesk", "Orbitron"),
    "dark-academia": ("Lora", "Playfair Display"),
    "bauhaus": ("Inter", "Sora"),
    "art-nouveau": ("Lora", "Fraunces"),
    "swiss-international": ("Inter", "Inter"),
}


def theme_colors(style: str = "frutiger-aero") -> dict:
    """Tk-ready hex colors for a style — used to theme Ultra-PC's own windows
    from the same single source of truth. Only solid-hex tokens (skips the
    rgba glass token). Falls back to frutiger-aero for unknown styles."""
    toks = STYLES.get(style, STYLES["frutiger-aero"])["tokens"]
    return {k: v for k, v in toks.items()
            if isinstance(v, str) and v.startswith("#")}


# --------------------------------------------------------------------------- #
#  CLI commands (headless — used by the assistant and the menu)
# --------------------------------------------------------------------------- #

def cmd_palettes(query: str = "") -> int:
    hits = [p for p in PALETTES
            if _match(query, p["id"], p["name"], p["style"], " ".join(p["tags"]))]
    if not hits:
        print(f"No palettes match '{query}'."); return 1
    for p in hits:
        print(f"\n  {p['name']}  ({p['id']}, {p['style']})")
        print(f"  {_swatches(p['colors'])}")
        print("  " + "  ".join(p["colors"]))
        print(f"  \x1b[2m{', '.join(p['tags'])}\x1b[0m")
    print(f"\n  {len(hits)} palette(s). `assets show <id>` for tokens/CSS vars.")
    return 0


def cmd_css(query: str = "") -> int:
    hits = [(k, v) for k, v in CSS_SNIPPETS.items()
            if _match(query, k, v["style"], v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No CSS snippets match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<22} [{v['style']}]  {v['desc']}")
    print(f"\n  {len(hits)} snippet(s). `assets show {hits[0][0]}` to print one.")
    return 0


def cmd_anim(query: str = "") -> int:
    hits = [(k, v) for k, v in ANIMATIONS.items()
            if _match(query, k, v["style"], v["desc"], v["kind"], " ".join(v["tags"]))]
    if not hits:
        print(f"No animations match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<20} [{v['kind']:<3} · {v['style']}]  {v['desc']}")
    print(f"\n  {len(hits)} animation(s). `assets show {hits[0][0]}` to print one.")
    return 0


def cmd_show(asset_id: str) -> int:
    """Print a single asset ready to paste — palette (as CSS vars + Python),
    CSS snippet, or animation."""
    if asset_id.startswith("web/"):
        from . import webassets
        return webassets.handle(["context",asset_id[4:]])
    if "/" in asset_id or ":" in asset_id:
        group, key = re.split(r"[/:]", asset_id, maxsplit=1)
        if group == "style" and key in STYLES:
            print(_tokens_css(key)); return 0
        if group == "profile" and key in PROFILES:
            return cmd_profiles(key)
        groups = {"native": (NATIVE, "code"), "css": (CSS_SNIPPETS, "css"),
                  "fx": (TECHNIQUES, "code"), "shape": (SHAPES, "svg"),
                  "creative": (CREATIVE, "code"), "layout": (LAYOUTS, "html"),
                  "anim": (ANIMATIONS, "code"), "art": (SVG_ART, "code")}
        if group in groups:
            collection, field = groups[group]
            if key in collection:
                print(collection[key][field]); return 0
        print(f"Unknown qualified asset '{asset_id}'."); return 1
    p = find_palette(asset_id)
    if p:
        print(f"/* {p['name']} — {p['style']} */")
        print(":root {")
        for i, c in enumerate(p["colors"]):
            print(f"  --c{i + 1}: {c};")
        print("}")
        print("\n# Python / tkinter:")
        print(f"{asset_id.replace('-', '_')} = {p['colors']!r}")
        return 0
    if asset_id in CSS_SNIPPETS:
        v = CSS_SNIPPETS[asset_id]
        print(f"/* {asset_id} — {v['desc']} */")
        print(v["css"]); return 0
    if asset_id in ANIMATIONS:
        v = ANIMATIONS[asset_id]
        print(f"/* {asset_id} — {v['desc']}  [{v['kind']}] */")
        print(v["code"]); return 0
    if asset_id in GRADIENTS:
        v = GRADIENTS[asset_id]
        print(f"/* {asset_id} — {v['style']} */")
        print(f".grad-{asset_id} {{ background: {v['css']}; }}"); return 0
    if asset_id in PATTERNS:
        v = PATTERNS[asset_id]
        print(f"/* {asset_id} — {v['desc']}  [{v['kind']}] */")
        print(v["code"]); return 0
    if asset_id in SVG_ART:
        v = SVG_ART[asset_id]
        print(f"<!-- {asset_id} — {v['desc']} -->")
        print(v["code"]); return 0
    if asset_id in NATIVE:
        v = NATIVE[asset_id]
        print(f"# {asset_id} — {v['desc']}  [native/tkinter]")
        print(v["code"]); return 0
    if asset_id in SHAPES:
        v = SHAPES[asset_id]
        print(f"<!-- {asset_id} — shape for the '{v['profile']}' profile; "
              "uses currentColor -->")
        print(v["svg"].strip()); return 0
    if asset_id in PROFILES:
        return cmd_profiles(asset_id)
    if asset_id in LAYOUTS:
        v = LAYOUTS[asset_id]
        print(f"<!-- {asset_id} — {v['desc']}  (best for: {v['best_for']}) -->")
        print(v["html"]); return 0
    if asset_id in TECHNIQUES:
        v = TECHNIQUES[asset_id]
        print(f"/* {asset_id} — {v['desc']}  [{v['cat']}] */")
        print(v["code"]); return 0
    if asset_id in CREATIVE:
        v = CREATIVE[asset_id]
        print(f"<!-- {asset_id} — {v['desc']}  [{v['cat']}]  lib: {v['lib']} -->")
        print(v["code"]); return 0
    if asset_id in ASCII_ART:
        print(ASCII_ART[asset_id]["art"].strip("\n")); return 0
    if asset_id in STYLES:
        print(_tokens_css(asset_id)); return 0
    print(f"Unknown asset id '{asset_id}'. Try: assets palettes | gradients | "
          "patterns | art | layouts | css | anim")
    return 1


def cmd_layouts(query: str = "") -> int:
    hits = [(k, v) for k, v in LAYOUTS.items()
            if _match(query, k, v["desc"], v["best_for"])]
    if not hits:
        print(f"No layouts match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<22} {v['desc']}")
        print(f"  {'':<22} \x1b[2mbest for: {v['best_for']}\x1b[0m")
    print(f"\n  {len(hits)} layout(s). `assets show {hits[0][0]}` for full HTML.")
    return 0


def cmd_fx(query: str = "") -> int:
    hits = [(k, v) for k, v in TECHNIQUES.items()
            if _match(query, k, v["cat"], v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No techniques match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<24} [{v['cat']:<6}] {v['desc']}")
    print(f"\n  {len(hits)} technique(s). `assets show {hits[0][0]}` for full code.")
    return 0


def cmd_showcase() -> int:
    """Open the generated profile showcase in the default browser."""
    if not SHOWCASE.exists():
        print(f"Showcase not found at {SHOWCASE}."); return 1
    print(f"Opening {SHOWCASE} …")
    core.open_in_os(SHOWCASE)
    return 0


def cmd_creative(query: str = "") -> int:
    hits = [(k, v) for k, v in CREATIVE.items()
            if _match(query, k, v["cat"], v["lib"], v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No creative recipes match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<20} [{v['cat']:<10}] {v['desc']}")
        print(f"  {'':<20} \x1b[2mlib: {v['lib']}\x1b[0m")
    print(f"\n  {len(hits)} recipe(s). `assets show {hits[0][0]}` for full code.")
    return 0


def cmd_native(query: str = "") -> int:
    """Native/desktop UI recipes. Subforms:
       native                → list recipes
       native <query>        → filter recipes
       native preview <style> [out.png]  → render a static look-preview
       native demo <style>   → open a live sample window."""
    parts = query.split()
    if parts and parts[0] == "preview":
        style = parts[1] if len(parts) > 1 else "frutiger-aero"
        out = parts[2] if len(parts) > 2 else f"native-{style}.png"
        try:
            from . import nativeui
            p = nativeui.preview(style, out)
            print(f"Rendered native preview ({style}) -> {p}")
            core.open_in_os(p)
        except Exception as exc:
            print(f"preview failed: {exc}"); return 1
        return 0
    if parts and parts[0] == "demo":
        style = parts[1] if len(parts) > 1 else "frutiger-aero"
        try:
            from . import nativeui
            print(f"Opening live {style} demo window…")
            nativeui.demo(style)
        except Exception as exc:
            print(f"demo failed: {exc}"); return 1
        return 0
    hits = [(k, v) for k, v in NATIVE.items()
            if _match(query, k, v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No native recipes match '{query}'."); return 1
    print("Native / desktop UI recipes (tkinter/PIL — module: ultrapc/nativeui.py):\n")
    for k, v in hits:
        print(f"  {k:<16} {v['desc']}")
    print(f"\n  {len(hits)} recipe(s). `assets show native/{hits[0][0]}` for code.")
    print("  `assets native preview <style>`  render a look · "
          "`assets native demo <style>`  live window")
    return 0


def cmd_profiles(query: str = "") -> int:
    """List design profiles, or print one profile's full collection (swatches,
    fonts, textures, gloss, shapes, fx) when `query` names a profile id."""
    import textwrap

    def _sec(label: str, text: str) -> None:
        wrapped = textwrap.fill(text, width=76, initial_indent="    ",
                                subsequent_indent="    ")
        print(f"  \x1b[1m{label}\x1b[0m\n{wrapped}")

    q = query.strip().lower()
    if q in PROFILES:
        p = PROFILES[q]
        pal = find_palette(p["palette"])
        print(f"\n{p['label']}  —  design profile `{q}`")
        if p.get("era"):
            print(f"  \x1b[2m{p['era']}\x1b[0m")
        print("  " + "─" * 74)
        _sec("essence", p["vibe"])
        for label, key in (("origins", "origins"),
                           ("composition & space", "composition"),
                           ("proportion & measure", "proportion"),
                           ("color logic", "color"),
                           ("light", "light"),
                           ("typography", "type"),
                           ("materiality & finish", "materiality"),
                           ("motion & rhythm", "motion"),
                           ("imagery", "imagery"),
                           ("voice (copy & tone)", "voice"),
                           ("sound", "sound"),
                           ("where it lives", "space"),
                           ("kinship (family tree)", "kinship"),
                           ("hierarchy of power", "hierarchy"),
                           ("canon (study these)", "canon"),
                           ("adaptation (modes & a11y)", "adaptation")):
            if p.get(key):
                _sec(label, p[key])
        if p.get("moves"):
            print("  \x1b[1msignature moves\x1b[0m")
            for i, mv in enumerate(p["moves"], 1):
                print(f"    {i}. {mv}")
        print("  " + "─" * 74)
        if pal:
            print(f"  palette      : {_swatches(pal['colors'])}  "
                  f"({p['palette']})")
        print(f"  tokens/style : {p['style']}   "
              f"(`assets kit {p['style']}` = full stylesheet)")
        print("  fonts        : " + ", ".join(
            f"{k} = {v}" for k, v in p["fonts"].items() if k != "files"))
        print(f"  textures     : {', '.join(p['textures'])}   (nativeui)")
        print(f"  gloss        : {p['gloss']}")
        print(f"  shapes       : {', '.join(p['shapes'])}   "
              "(`assets show <shape>`)")
        print(f"  patterns     : {', '.join(p['patterns']) or '—'}")
        print(f"  fx           : {', '.join(p['techniques'])}")
        print(f"\n  rules: {p['rules']}")
        if p.get("failure"):
            print(f"  \x1b[2mlost the plot when: {p['failure']}\x1b[0m")
        return 0
    hits = [(k, v) for k, v in PROFILES.items()
            if _match(query, k, v["label"], v["vibe"], " ".join(v["shapes"]))]
    if not hits:
        print(f"No profiles match '{query}'."); return 1
    print("Design profiles (archetype collections — tokens + palette + fonts "
          "+ textures + gloss + shapes):\n")
    for k, v in hits:
        print(f"  {k:<16} {v['vibe'][:96]}…")
    print(f"\n  {len(hits)} profile(s). `assets profile <id>` for the full "
          "collection · `assets kit <id>` for its stylesheet")
    return 0


def cmd_shapes(query: str = "") -> int:
    hits = [(k, v) for k, v in SHAPES.items()
            if _match(query, k, v["profile"], " ".join(v["tags"]))]
    if not hits:
        print(f"No shapes match '{query}'."); return 1
    print("Signature shapes (SVG, currentColor — per design profile):\n")
    for k, v in hits:
        print(f"  {k:<16} [{v['profile']}]  {', '.join(v['tags'])}")
    print(f"\n  {len(hits)} shape(s). `assets show {hits[0][0]}` prints the "
          f"SVG · files in {SHAPES_DIR}")
    return 0


def cmd_ascii(query: str = "") -> int:
    hits = [(k, v) for k, v in ASCII_ART.items()
            if _match(query, k, v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No ASCII art match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<16} {v['desc']}")
    print(f"\n  {len(hits)} piece(s). `assets show {hits[0][0]}` to print one.")
    return 0


def cmd_cli() -> int:
    """Live demo of the cliart terminal-art toolkit."""
    try:
        from . import cliart
    except Exception as exc:
        print(f"cliart unavailable: {exc}"); return 1
    cliart.demo()
    print("\nImport it in your tools:  from ultrapc import cliart")
    return 0


def cmd_banner(text: str, font: str = "thin") -> int:
    from . import cliart
    print(cliart.banner(text or "ULTRA", "#2b8fd6", "#96cd6e", font=font))
    return 0


def cmd_gradients(query: str = "") -> int:
    hits = [(k, v) for k, v in GRADIENTS.items()
            if _match(query, k, v["style"], " ".join(v["tags"]))]
    if not hits:
        print(f"No gradients match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<16} [{v['style']:<12}]  {v['css']}")
    print(f"\n  {len(hits)} gradient(s). `assets show {hits[0][0]}` to print one.")
    return 0


def cmd_patterns(query: str = "") -> int:
    hits = [(k, v) for k, v in PATTERNS.items()
            if _match(query, k, v["kind"], v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No patterns match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<18} [{v['kind']:<3}]  {v['desc']}")
    print(f"\n  {len(hits)} pattern(s). `assets show {hits[0][0]}` to print one.")
    return 0


def cmd_art(query: str = "") -> int:
    hits = [(k, v) for k, v in SVG_ART.items()
            if _match(query, k, v["desc"], " ".join(v["tags"]))]
    if not hits:
        print(f"No SVG art match '{query}'."); return 1
    for k, v in hits:
        print(f"  {k:<16}  {v['desc'].split('.')[0]}.")
    print(f"\n  {len(hits)} item(s). `assets show {hits[0][0]}` to print one.")
    return 0


def _fill_columns(css: str, columns: int) -> str:
    """Bake the style's column count into the grid rules.

    CSS `repeat()` requires a literal integer — a `var()` repetition count is
    not substituted, and the track list silently collapses instead of
    erroring. The kit is generated per style, so the literal is known here.
    """
    if columns == 12:
        return css
    return (css.replace("repeat(12, minmax(0, 1fr))",
                        f"repeat({columns}, minmax(0, 1fr))")
               .replace("100% / 12", f"100% / {columns}"))


def profile_for(style: str) -> dict | None:
    """The PROFILES entry that governs `style`, if one has been written."""
    return next((v for v in PROFILES.values() if v["style"] == style), None)


def kit_plan(style: str) -> dict:
    """Decide what belongs in this style's kit — before writing any CSS.

    The old assembler gave all 25 styles the same five components, the same
    base rules and a gradient whether or not the style allowed one; twelve of
    the thirteen profiled styles ended up contradicting their own profile.
    Everything here is read from the style's own declarations instead.
    """
    e = EXEC[style]
    prof = profile_for(style) or {}
    forbid = set(e["forbid"])

    # A gradient only if the profile names one. An empty `gradients: []` is a
    # statement, not a gap to fill with a default.
    declared = [g for g in prof.get("gradients", []) if g in GRADIENTS]
    gradient = declared[0] if declared else None
    if gradient is None and "gradient" not in forbid and not prof:
        gradient = "mono-fade" if style in ("mono", "editorial") else None

    glass_ok = e["gloss"] >= 2 and "glass" not in forbid
    components = ["type-scale", "grid-system",
                  "navbar-glass" if glass_ok else "navbar-solid",
                  "hero-centered" if e["align"] == "center" else "hero-flush",
                  "feature-card", "badge-pill", "input-field"]
    if e["gloss"] >= 3 and "glass" not in forbid:
        components.insert(-3, "aqua-gel-button")
    if e["elevation"] == "glow" and "neon" not in forbid:
        components.insert(-3, "neon-glow")

    # The profile's own technique picks, which nothing used to emit.
    techniques = [t for t in prof.get("techniques", []) if t in TECHNIQUES]

    animations = []
    if e["travel"] > 0 and e["dur"] > 0:
        animations.append("fade-in-up")
    animations += [k for k, v in ANIMATIONS.items()
                   if v["style"] == style and v["kind"] == "css"][:1]

    fonts = prof.get("fonts")
    fonts = ((fonts["body"], fonts["display"]) if fonts
             else STYLE_FONTS.get(style, ("Inter", "Space Grotesk")))

    pal = prof.get("palette") or next(
        (p["id"] for p in PALETTES if p["style"] == style), None)

    return {"style": style, "palette": pal, "gradient": gradient,
            "fonts": fonts, "components": components,
            "techniques": techniques, "animations": animations,
            "patterns": [p for p in prof.get("patterns", []) if p in PATTERNS],
            "shapes": prof.get("shapes", []), "forbid": sorted(forbid)}


def _kit_css(style: str) -> tuple[str, dict]:
    """Assemble a full themed stylesheet for `style` from the vault pieces.
    Returns (css_text, chosen) where chosen names the picks."""
    e = EXEC[style]
    plan = kit_plan(style)
    grad = plan["gradient"]

    parts = ["/* ============================================================",
             f"   {STYLES[style]['label']} kit — generated by Ultra-PC assets",
             f"   palette: {plan['palette'] or '(none)'}   "
             f"gradient: {grad or '(none — this style forbids one)'}",
             f"   fonts: {plan['fonts'][0]} (body) / {plan['fonts'][1]} (display)",
             "   Load fonts/fonts.css locally; assets scaffold copies fonts and licenses.",
             f"   type: {e['sizes']} sizes at {e['ratio']}  ·  measure "
             f"{e['measure']}ch  ·  leading {_leading(style)}",
             f"   material: gloss {e['gloss']}  ·  {e['elevation']} elevation  "
             f"·  {e['accents']} accent(s)",
             f"   refuses: {', '.join(plan['forbid'])}",
             "   ============================================================ */",
             "", _tokens_css(style), "",
             "/* --- base --- */",
             "* { box-sizing: border-box; margin: 0; }",
             ".btn {",
             "  padding: 0.7rem 1.5rem; cursor: pointer;",
             "  border: var(--border-width) solid var(--border);",
             "  border-radius: var(--radius);",
             "  font: inherit; font-weight: var(--weight-strong);",
             "  text-transform: var(--case); letter-spacing: var(--tracking);",
             "  background: var(--accent); background-image: var(--sheen);",
             "  color: var(--on-accent);",
             "  transition: filter var(--dur) var(--ease),",
             "              transform var(--dur) var(--ease);",
             "}",
             ".btn:hover { filter: brightness(1.08); }",
             ".btn:active { transform: translateY(calc(var(--travel) * 0.15)); }",
             ""]

    for mode, values in (profile_for(style) or {}).get('modes', {}).items():
        parts += ['/* --- named profile mode: '+mode+' --- */',
                  'body[data-uv-mode="'+mode+'"] { '+''.join('--'+key+':'+value+';' for key,value in values.items())+'background:var(--bg);color:var(--text); }']
    character = {
        'dark-academia': '.card,.uv-card{border:3px double var(--accent);border-radius:2px;}.btn{border:3px double var(--accent);border-radius:2px;}blockquote{border-inline-start:1px solid var(--accent);padding-inline-start:2em;font-style:italic;}',
        'cyberpunk': '.card,.uv-card{border-radius:0;border-inline-start:3px solid var(--accent);}.btn{border-radius:0;clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,10px 100%,0 calc(100% - 10px));}',
        'high-fashion': '.card,.uv-card{background:transparent;border-radius:0;border-width:0 0 1px;box-shadow:none;}.btn{background:transparent;color:var(--text);border:0;border-bottom:1px solid var(--text);border-radius:0;box-shadow:none;letter-spacing:.15em;}',
        'nordic': '.card,.uv-card{box-shadow:none;padding:2rem;}.btn{border-radius:4px;box-shadow:none;}',
    }.get(style)
    if character: parts += ['/* --- profile character --- */', character]

    if grad:
        fg, ratio = _on_gradient_fg(style, grad)
        scrim = hero_scrim(style, grad)
        parts.append(f"/* --- gradient util ({grad}) --- */")
        if scrim:
            r, g, b = _hex_rgb(STYLES[style]["tokens"]["bg"])
            wash = f"rgba({r},{g},{b},{scrim})"
            parts += [f"/* No single foreground survives this gradient's "
                      f"range, so the hero lays a {scrim} wash of --bg over",
                      "   it and sets type on that — the gradient still "
                      "reads, the copy still does too. */",
                      f".hero-bg {{",
                      f"  background: linear-gradient({wash}, {wash}), "
                      f"{GRADIENTS[grad]['css']};",
                      f"  color: var(--text);",
                      f"}}"]
        else:
            parts += [f"/* Foreground picked against the gradient's own stops "
                      f"({ratio}:1), not inherited: a profile can name a light",
                      "   gradient under a dark palette, and the hero copy "
                      "then disappears into it. */",
                      f".hero-bg {{ background: {GRADIENTS[grad]['css']}; "
                      f"color: {fg}; }}"]
        parts += [".hero-bg h1, .hero-bg h2, .hero-bg p { color: inherit; }", ""]
    else:
        parts += ["/* --- hero field: flat by rule, not by omission --- */",
                  ".hero-bg { background: var(--bg2); }", ""]

    for cid in plan["components"]:
        parts += [f"/* --- {cid} --- */",
                  _fill_columns(CSS_SNIPPETS[cid]["css"], e["columns"]), ""]
    for tid in plan["techniques"]:
        parts += [f"/* --- technique: {tid} — {TECHNIQUES[tid]['desc']} --- */",
                  TECHNIQUES[tid]["code"], ""]
    for aid in plan["animations"]:
        if aid in ANIMATIONS:
            parts += [f"/* --- animation: {aid} --- */",
                      ANIMATIONS[aid]["code"], ""]
    parts += ["/* --- interaction and motion preferences --- */",
              ":where(a, button, input, select, textarea, summary, [tabindex]):focus-visible {",
              "  outline: 3px solid var(--accent); outline-offset: 3px;",
              "}",
              "button, .btn { min-height: 44px; min-width: 44px; }",
              "h1, h2, h3 { font-family: var(--font-display); }",
              "@media (prefers-reduced-motion: reduce) {",
              "  *, *::before, *::after { animation: none !important;",
              "    transition: none !important; scroll-behavior: auto !important; }",
              "}", ""]
    return "\n".join(parts), plan


def cmd_kit(style: str = "frutiger-aero", write: str | None = None) -> int:
    """Print (or write) a complete themed stylesheet in one shot — tokens +
    base + gradient + components + animation. Paste-and-go."""
    if style not in STYLES:
        print(f"Unknown style '{style}'. Choose: {', '.join(STYLES)}"); return 2
    css, chosen = _kit_css(style)
    if write:
        out = Path(write).expanduser()
        if out.is_dir() or write.endswith(("/", "\\")):
            out = out / f"theme-{style}.css"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(css + "\n", encoding="utf-8")
        print(f"Wrote {style} kit -> {out}")
        print(f"  palette {chosen['palette']} · gradient {chosen['gradient']} · "
              f"fonts {chosen['fonts'][0]}/{chosen['fonts'][1]}")
    else:
        print(css)
    return 0


# --------------------------------------------------------------------------- #
#  Fidelity check  —  does the generated CSS obey the profile that describes it?
# --------------------------------------------------------------------------- #
#  The profiles are confident prose: "a gradient here is not a choice, it is a
#  scandal", "two sizes of one grotesque", "ONE signal red". Prose cannot fail
#  a build, so the kits drifted from it silently. These rules give each claim a
#  detector, so a style that stops matching its own description says so.

#  forbid-token -> (regex over the generated CSS, what the violation means)
FORBID_PATTERNS: dict[str, tuple[str, str]] = {
    "glass":       (r"backdrop-filter\s*:", "frosted glass"),
    # Centring the composition — not centring a glyph inside its own 44px box.
    "center":      (r"text-align\s*:\s*center", "centred text"),
    "radius":      (r"border-radius\s*:\s*(?!0)(?!var\(--radius)[0-9]", "a rounded corner"),
    "neon":        (r"(?:text-shadow|box-shadow)[^;]*\b0 0 \d{2,}px", "a neon glow"),
    "texture":     (r"url\(\s*[\"']?data:image/(?:png|jpeg)", "a raster texture"),
    "bevel":       (r"border-style\s*:\s*(?:outset|ridge|groove)", "a bevel"),
    "bounce":      (r"cubic-bezier\([^)]*,\s*1\.[1-9]", "an overshoot/bounce easing"),
}


def _decl_values(css: str, prop: str) -> list[tuple[str, int]]:
    """Every value assigned to `prop`, with its line number.

    Shadows are checked on the value rather than by regex over the whole
    sheet: `inset` is an underline or a rim light, `none` is a refusal, and
    only the rest is elevation lifting something off the page. A lookahead
    can be talked out of that distinction by backtracking; reading the value
    cannot.
    """
    out = []
    for m in re.finditer(rf"(?<![\w-]){re.escape(prop)}\s*:\s*([^;{{}}]+)", css):
        out.append((m.group(1).strip(), css[:m.start()].count("\n") + 1))
    return out


#  Properties where a gradient paints colour. A gradient in `mask-image` sets
#  opacity instead — it is how an edge is faded — and several profiles ask for
#  exactly that while also refusing decorative blends. Both can be true.
_PAINT_PROPS = ("background", "background-image", "border-image",
                "border-image-source", "list-style-image")


def _is_hard_stop(fragment: str) -> bool:
    """True when a gradient's stops are an edge rather than a blend.

    `radial-gradient(currentColor 30%, transparent 31%)` is a halftone dot:
    the colour changes over one percent, which the eye reads as a drawn
    circle. Patterns like that are geometry, and a style that refuses soft
    colour transitions has no argument with them. Conservative on purpose —
    a gradient with no explicit stop positions is always treated as a blend.
    """
    stops, depth, cur = [], 0, ""
    for ch in fragment:                          # split on top-level commas
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            stops.append(cur); cur = ""
        else:
            cur += ch
    stops.append(cur)
    # drop a leading angle/shape argument — it is not a colour stop
    if stops and not re.search(r"#|rgb|hsl|currentColor|transparent|\b[a-z]+\s*\d*%",
                               stops[0].split()[0] if stops[0].split() else ""):
        stops = stops[1:]
    # Stops may be positioned in % or in absolute units; compare within one
    # unit only, since 1% and 1px are not the same distance.
    runs, units = [], set()
    for s in stops:
        found = re.findall(r"(\d+(?:\.\d+)?)(%|px|rem|em)", s)
        runs.append([float(v) for v, u in found])
        units |= {u for _, u in found}
    if len(runs) < 2 or any(not r for r in runs) or len(units) != 1:
        return False                             # unpositioned or mixed: a blend
    tol = 2 if units == {"%"} else 1             # 2% of the run, or 1px
    return all(runs[i + 1][0] - runs[i][-1] <= tol for i in range(len(runs) - 1))


def _gradient_violations(css: str) -> list[tuple[str, int]]:
    """Soft colour blends in `css`.

    `repeating-*` and hard-stop stop lists draw checkerboards, grid overlays
    and halftone screens rather than blends, so a style that bans gradients
    keeps those.
    """
    hits = []
    for prop in _PAINT_PROPS:
        for val, line in _decl_values(css, prop):
            for m in re.finditer(
                    r"(?<!repeating-)\b(linear|radial|conic)-gradient\(", val):
                depth, i = 0, m.end() - 1
                while i < len(val):                 # the matching close paren
                    depth += (val[i] == "(") - (val[i] == ")")
                    if depth == 0:
                        break
                    i += 1
                if not _is_hard_stop(val[m.end():i]):
                    hits.append((m.group(1) + "-gradient(...)", line))
    return hits


def _gradient_stops(gid: str) -> list[str]:
    """The hex colour stops a gradient paints with."""
    return re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}", GRADIENTS[gid]["css"])


def _composite(fg: str, bg: str, alpha: float) -> str:
    """`fg` laid over `bg` at `alpha`, as a hex colour."""
    a, b = _hex_rgb(fg), _hex_rgb(bg)
    return "#%02x%02x%02x" % tuple(
        round(a[i] * alpha + b[i] * (1 - alpha)) for i in range(3))


def _on_gradient_fg(style: str, gid: str) -> tuple[str, float]:
    """Pick the foreground that stays legible across a gradient's whole run.

    Scored on the worst stop, not the average: text has to survive the end of
    the sweep as well as the start.
    """
    t = STYLES[style]["tokens"]
    stops = _gradient_stops(gid) or [t["bg"]]
    best = max((t["text"], t["bg"], "#ffffff", "#111111"),
               key=lambda c: min(_contrast(c, s) for s in stops))
    return best, round(min(_contrast(best, s) for s in stops), 2)


def hero_scrim(style: str, gid: str) -> float:
    """How much scrim the hero needs over `gid`, as an alpha in 0..0.9.

    A mesh of bright blobs over a dark base has no single legible foreground —
    light type dies on the blobs, dark type dies on the base. The fix is the
    one print and film already use: lay a wash of the style's own background
    over the art and set type on that. Returns the lightest scrim that clears
    AA, so the gradient stays as visible as legibility allows; 0.0 when the
    gradient needs none.
    """
    t = STYLES[style]["tokens"]
    stops = _gradient_stops(gid)
    if not stops or _on_gradient_fg(style, gid)[1] >= 4.5:
        return 0.0
    for alpha in (i / 20 for i in range(8, 19)):          # 0.40 .. 0.90
        worst = min(_contrast(t["text"], _composite(t["bg"], s, alpha))
                    for s in stops)
        if worst >= 4.5:
            return round(alpha, 2)
    return 0.9


def _shadow_violations(css: str, kind: str) -> list[tuple[str, int]]:
    """Real drop shadows in `css`, filtered to the kind a style forbids."""
    hits = []
    for val, line in _decl_values(css, "box-shadow"):
        v = val.lower()
        if v.startswith("none") or "inset" in v:
            continue
        if v.startswith("var(--shadow"):        # resolves to the style's own
            continue                            # declared elevation model
        # Zero offset and zero blur is a ring — a focus indicator or a
        # hairline rule — not something lifted off the page. Flat styles keep
        # their focus rings; banning those would trade a rule for an a11y bug.
        lengths = []
        for tok in v.split():
            m = re.fullmatch(r"(-?[\d.]+)(?:px|rem|em)?", tok)
            if not m:
                break                           # first colour token ends the run
            lengths.append(float(m.group(1)))
        if len(lengths) >= 3 and not any(lengths[:3]):
            continue
        alpha = re.search(r"rgba\([^)]*?([01]?\.\d+)\s*\)", v)
        a = float(alpha.group(1)) if alpha else None
        if kind == "shadow":
            hits.append((val, line))
        elif kind == "softshadow" and a is not None and a <= 0.25:
            hits.append((val, line))
        elif kind == "harshshadow" and a is not None and a >= 0.6:
            hits.append((val, line))
    return hits


def _is_achromatic(colour: str) -> bool:
    """True for whites, blacks and greys at any alpha.

    A white sheen or a black scrim is a lightness operation, not a palette
    choice — it composites correctly over any style. Only a literal with a
    hue in it has been smuggled in from somewhere else.
    """
    c = colour.strip().lower()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) != 6:
            return False
        return h[0:2] == h[2:4] == h[4:6]
    m = re.match(r"rgba?\(([^)]*)\)", c)
    if not m:
        return False
    parts = [x.strip() for x in m.group(1).replace("/", " ").split(",")]
    nums = []
    for x in parts[:3]:
        nums += [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", x)]
    return len(nums) >= 3 and nums[0] == nums[1] == nums[2]


def _contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two hex colours."""
    la, lb = _relative_luminance(a), _relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def check_style(style: str) -> list[tuple[str, str, str]]:
    """Audit one style. Returns (level, rule, detail) — level is FAIL or WARN."""
    e, out = EXEC[style], []
    prof = profile_for(style)
    css, plan = _kit_css(style)
    body = css[css.index("/* --- base --- */"):]   # skip the :root declarations

    # 1. the style's own refusals, as written in EXEC["forbid"]
    for token in e["forbid"]:
        if token == "gradient":
            for val, line in _gradient_violations(body):
                out.append(("FAIL", "forbids gradient",
                            f"{val} at kit line ~{line}"))
            continue
        if token in ("shadow", "softshadow", "harshshadow"):
            for val, line in _shadow_violations(body, token):
                out.append(("FAIL", f"forbids {token}",
                            f"box-shadow: {val} at kit line ~{line}"))
            continue
        pat = FORBID_PATTERNS.get(token)
        if not pat:
            continue
        m = re.search(pat[0], body)
        if m:
            line = body[:m.start()].count("\n") + 1
            out.append(("FAIL", f"forbids {token}",
                        f"{pat[1]} at kit line ~{line}"))

    # 2. the gradient declaration in the profile is binding
    if prof is not None:
        declared = prof.get("gradients", [])
        if not declared and plan["gradient"]:
            out.append(("FAIL", "gradient", "profile declares none, kit emits "
                        f"{plan['gradient']}"))
        elif declared and plan["gradient"] not in declared:
            out.append(("FAIL", "gradient", f"profile declares "
                        f"{'/'.join(declared)}, kit emits {plan['gradient']}"))
        # 3. the profile's technique picks should actually ship
        missing = [t for t in prof.get("techniques", [])
                   if t in TECHNIQUES and t not in plan["techniques"]]
        if missing:
            out.append(("WARN", "techniques", "declared but not emitted: "
                        + ", ".join(missing)))
    else:
        out.append(("WARN", "profile", "no profile written for this style — "
                    "EXEC values are unverified against prose"))

    # 4. the type-size budget is a budget. Comparing the emitted --size-N
    #    tokens to EXEC would only ever confirm the generator agrees with
    #    itself; what matters is whether the kit's own CSS sets sizes that
    #    bypass the scale, which is how "three sizes, no more" quietly becomes
    #    nine.
    emitted = len(re.findall(r"--size-\d+:", css))
    if emitted != e["sizes"]:
        out.append(("FAIL", "type sizes",
                    f"budget is {e['sizes']}, tokens emit {emitted}"))
    offscale = {v for v, _ in _decl_values(body, "font-size")
                if "var(--size-" not in v and "var(--base" not in v
                and v not in ("inherit", "1em", "1rem")}
    if offscale:
        out.append(("WARN", "type scale",
                    f"{len(offscale)} font-size(s) bypass the scale: "
                    + "; ".join(sorted(offscale)[:3])))

    # 5. the measure has to reach the text, not just the token block
    if not re.search(r"max-width:[^;]*var\(--measure", css):
        out.append(("WARN", "measure", "--measure is declared but never applied"))

    # 6. a hero gradient has to carry the style's own text colour. A profile
    #    can name a gradient that simply does not work under its palette —
    #    gold-hour is a light field, and art-deco sets near-white type — and
    #    nothing downstream would notice until the hero copy vanished.
    if plan["gradient"]:
        fg, ratio = _on_gradient_fg(style, plan["gradient"])
        scrim = hero_scrim(style, plan["gradient"])
        if ratio < 4.5 and scrim:
            t = STYLES[style]["tokens"]
            worst = min(_contrast(t["text"], _composite(t["bg"], s, scrim))
                        for s in _gradient_stops(plan["gradient"]))
            lvl = "NOTE" if worst >= 4.5 else "FAIL"
            out.append((lvl, "gradient legibility",
                        f"{plan['gradient']} needs a {scrim} scrim to carry "
                        f"text ({round(worst, 2)}:1 with it)"))
        elif ratio < 4.5:
            out.append(("FAIL", "gradient legibility",
                        f"no foreground clears AA over {plan['gradient']} "
                        f"(best is {fg} at {ratio}:1)"))
        elif _contrast(STYLES[style]["tokens"]["text"],
                       min(_gradient_stops(plan["gradient"]) or ["#000000"],
                           key=lambda s: _contrast(
                               STYLES[style]["tokens"]["text"], s))) < 4.5:
            out.append(("NOTE", "gradient legibility",
                        f"--text cannot sit on {plan['gradient']}; the hero "
                        f"overrides it with {fg} ({ratio}:1)"))

    # 7. legibility is not a style choice
    t = STYLES[style]["tokens"]
    ratio = _contrast(t["text"], t["bg"])
    if ratio < 4.5:
        out.append(("FAIL", "contrast", f"text on bg is {ratio}:1, below AA 4.5"))
    muted = _contrast(t["muted"], t["bg"])
    if muted < 4.5:
        out.append(("WARN", "contrast", f"muted on bg is {muted}:1, below AA 4.5"))

    # 8. hardcoded colour literals cannot adapt to the style including them.
    #    This is how a white glass navbar ends up on a dark palette with
    #    inherited white text — the component simply never asked what style
    #    it was in. A literal inside a var() fallback is fine.
    allowed = {t: TECHNIQUES[t]["literals"] for t in plan["techniques"]
               if "literals" in TECHNIQUES[t]}
    exempt = set()
    for t in allowed:
        exempt |= set(re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}\b|rgba?\([^)]*\)",
                                 TECHNIQUES[t]["code"]))
    # The gradient utility is the gradient's own definition — colour data the
    # profile chose by name — so it is not a component ignoring its tokens.
    scanned = re.sub(r"/\* --- gradient util.*?(?=/\* --- )", "", body,
                     flags=re.S)
    literals = set()
    for prop in ("background", "background-color", "color", "border-color",
                 "background-image", "border", "border-bottom", "fill"):
        for val, _ in _decl_values(scanned, prop):
            stripped = re.sub(r"var\([^)]*\)", "", val)
            literals |= set(re.findall(
                r"#(?:[0-9a-fA-F]{3}){1,2}\b|rgba?\([^)]*\)", stripped))
    literals = {c for c in literals
                if not _is_achromatic(c) and c not in exempt}
    if literals:
        out.append(("WARN", "hardcoded colour",
                    f"{len(literals)} literal(s) ignore the tokens: "
                    + ", ".join(sorted(literals)[:3])))
    for tid, why in sorted(allowed.items()):
        out.append(("NOTE", f"literals in {tid}", why))

    # 9. one accent means one accent
    if (e["accents"] == 1 and not _is_achromatic(t["accent"])
            and not _is_achromatic(t["accent2"]) and t["accent2"].lower() not in (
            t["text"].lower(), t["border"].lower(), t["muted"].lower())):
        out.append(("WARN", "accent budget",
                    f"declares 1 accent but accent2 ({t['accent2']}) is a "
                    "distinct colour"))
    return out


def check_resources() -> list[tuple[str, str, str]]:
    """Verify offline availability and the retained dependency fingerprints."""
    import hashlib
    issues = []
    missing = [stem + ".woff2" for stem in FONT_MAP
               if not (FONT_DIR / (stem + ".woff2")).exists()]
    if missing:
        issues.append(("FAIL", "offline fonts", f"{len(missing)} missing faces; "
                       "restore with tools/vendor_design_assets.py"))
    refs = {ref for recipe in CREATIVE.values()
            for ref in re.findall(r'(?:src|href)=["\'](libraries/[^"\']+)', recipe["code"])}
    missing_libs = [ref for ref in sorted(refs) if not (ASSETS_DIR / ref).exists()]
    if missing_libs:
        issues.append(("FAIL", "offline libraries", ", ".join(missing_libs)))
    for page in (DEMO, SHOWCASE):
        if not page.exists():
            issues.append(("FAIL", "gallery", f"missing {page.name}; run assets sync"))
            continue
        for ref in re.findall(r'(?:src|href)=["\']([^"\']+)', page.read_text(encoding="utf-8")):
            if not ref.startswith(("#", "http:", "https:", "data:")) and not (page.parent / ref).exists():
                issues.append(("FAIL", "local link", f"{page.name} -> {ref}"))
    lock = ASSETS_DIR / "dependencies.lock.json"
    if not lock.exists():
        issues.append(("FAIL", "dependency inventory", "missing dependencies.lock.json"))
    else:
        try:
            packages = json.loads(lock.read_text(encoding="utf-8"))["packages"]
            if not packages:
                raise ValueError("empty dependency inventory")
            for package in packages:
                for entry in package["files"]:
                    path = ASSETS_DIR / entry["path"]
                    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                        issues.append(("FAIL", "dependency integrity", entry["path"]))
        except (KeyError, ValueError, TypeError, OSError) as exc:
            issues.append(("FAIL", "dependency inventory", str(exc)))
    from . import webassets
    issues.extend(webassets.audit())
    return issues


def cmd_check(query: str = "") -> int:
    """Audit every style's kit against the profile that describes it."""
    styles = [s for s in STYLES if not query or _match(query, s)]
    fails = warns = notes = 0
    for s in styles:
        issues = check_style(s)
        f = sum(1 for lv, _, _ in issues if lv == "FAIL")
        w = sum(1 for lv, _, _ in issues if lv == "WARN")
        n = sum(1 for lv, _, _ in issues if lv == "NOTE")
        fails += f; warns += w; notes += n
        mark = "FAIL" if f else ("warn" if w else "ok")
        print(f"{mark:>5}  {s}")
        glyph = {"FAIL": "x", "WARN": "!", "NOTE": "-"}
        for lv, rule, detail in issues:
            print(f"         {glyph.get(lv, '?')} {rule}: {detail}")
    resources = check_resources()
    if resources:
        print(" FAIL  offline resources")
        for level,rule,detail in resources:
            fails += level == "FAIL"
            warns += level == "WARN"
            print(f"         x {rule}: {detail}")
    else:
        print("   ok  offline resources · fonts, libraries, licenses and local links")
    print(f"\n{len(styles)} styles · {fails} failures · {warns} warnings "
          f"· {notes} reviewed exceptions")
    return 1 if fails else 0


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "app"


def cmd_scaffold(target: str, style: str = "frutiger-aero") -> int:
    """Create a portable starter from the checked profile kit."""
    import shutil
    if style not in STYLES:
        print(f"Unknown style '{style}'. Choose: {', '.join(STYLES)}"); return 2
    out = Path(target).expanduser()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        print(f"Refusing to overwrite an existing starter in {out}"); return 2
    out.mkdir(parents=True, exist_ok=True)
    css, plan = _kit_css(style)
    title = out.name.replace("-", " ").replace("_", " ").title()
    prof = profile_for(style)
    font_link = ""
    if (FONT_DIR / "fonts.css").exists():
        shutil.copytree(FONT_DIR, out / "fonts", dirs_exist_ok=True)
        if (ASSETS_DIR / "licenses").exists():
            shutil.copytree(ASSETS_DIR / "licenses", out / "licenses", dirs_exist_ok=True)
        font_link = '<link rel="stylesheet" href="fonts/fonts.css">'
    motif = "".join(SHAPES[x]["svg"] for x in prof.get("shapes", [])[:1])
    css += ("\n.starter { max-width: var(--measure); margin: 8vh auto; padding: 2rem; }"
            "\n.starter p { margin-block: 1.5rem; }"
            "\n.starter-motif { width: 96px; color: var(--accent); margin-bottom: 2rem; }"
            "\n.starter-motif svg { width: 100%; height: auto; }\n")
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{_esc(title)}</title>{font_link}'
            '<link rel="stylesheet" href="styles.css"></head><body>'
            f'<main class="starter"><div class="starter-motif">{motif}</div>'
            f'<h1>{_esc(title)}</h1><p>Your next idea starts here.</p>'
            '<button class="btn" type="button">Get started</button></main></body></html>')
    (out / "styles.css").write_text(css, encoding="utf-8")
    (out / "index.html").write_text(html, encoding="utf-8")
    (out / "DESIGN.md").write_text(
        f"# {prof['label']}\n\nProfile: `{style}` · Palette: `{plan['palette']}`\n\n"
        + prof["rules"] + "\n\nSource: Ultra-PC assets-vault. Change tokens and assets "
        "through the profile; retain this project's own identity.\n", encoding="utf-8")
    print(f"Scaffolded '{style}' starter into {out}")
    return 0


def cmd_status() -> int:
    for ln in _status_lines():
        print(ln)
    return 0


def _status_lines() -> list[str]:
    lines = [f"Assets vault: {ASSETS_DIR}"]
    lines.append(f"  exists: {ASSETS_DIR.exists()}   manifest: {MANIFEST.exists()}")
    lines.append(f"  curated: {len(PALETTES)} palettes, {len(GRADIENTS)} gradients, "
                 f"{len(PATTERNS)} patterns, {len(SVG_ART)} SVG art, "
                 f"{len(LAYOUTS)} layouts, {len(TECHNIQUES)} techniques, "
                 f"{len(CREATIVE)} creative-coding, {len(CSS_SNIPPETS)} CSS, "
                 f"{len(ANIMATIONS)} animations, {len(STYLES)} styles")
    lines.append(f"  CLI art: {len(ASCII_ART)} ASCII pieces + cliart toolkit "
                 "(banner/box/gradient/spinner/progress)")
    lines.append(f"  native/desktop: {len(NATIVE)} tkinter/PIL recipes + nativeui "
                 "toolkit (glass cards, gel buttons, header bars, splash)")
    libs = _scan_libraries()
    total = sum(l["bytes"] for l in libs)
    lines.append(f"  vendored fonts: {len(list(FONT_DIR.glob('*.woff2')))} faces")
    lines.append(f"  vendored libraries: {len(libs)} files ({total // 1024} KB)")
    lines.append(f"  catalog: {CATALOG if CATALOG.exists() else '(run: assets sync)'}")
    return lines


# --------------------------------------------------------------------------- #
#  Menu integration (GUI-facing)
# --------------------------------------------------------------------------- #

def _tool_check(ctx=None) -> None:
    cmd_check()


def _tool_browse_palettes(ctx=None) -> None:
    ui.title_bar("Design Assets — Palettes")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_palettes(q)
    ui.pause()


def _tool_browse_css(ctx=None) -> None:
    ui.title_bar("Design Assets — CSS snippets")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_css(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_browse_gradients(ctx=None) -> None:
    ui.title_bar("Design Assets — Gradients")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_gradients(q)
    ui.pause()


def _tool_browse_patterns(ctx=None) -> None:
    ui.title_bar("Design Assets — Background patterns / SVG")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_patterns(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_browse_anim(ctx=None) -> None:
    ui.title_bar("Design Assets — Animations")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_anim(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_browse_art(ctx=None) -> None:
    ui.title_bar("Design Assets — SVG art (icons, dividers, heroes)")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_art(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_browse_layouts(ctx=None) -> None:
    ui.title_bar("Design Assets — Web layout templates")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_layouts(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_demo(ctx=None) -> None:
    ui.title_bar("Design Assets — Live Vault Demo")
    ui.info("One page, every style/profile/palette/gradient/pattern/layout/"
            "shape/font — regenerated from the vault data on every sync.")
    cmd_demo()
    ui.pause()


def _tool_profiles(ctx=None) -> None:
    ui.title_bar("Design Assets — Design Profiles (archetypes)")
    ui.info("Full collections per design language: tokens + palette + fonts "
            "+ textures + gloss + signature shapes + rules.")
    print()
    cmd_profiles("")
    print()
    pid = ui.prompt("open which profile? (blank = skip)").strip()
    if pid:
        print()
        cmd_profiles(pid)
    ui.pause()


def _tool_browse_fx(ctx=None) -> None:
    ui.title_bar("Design Assets — Advanced CSS techniques")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_fx(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_browse_creative(ctx=None) -> None:
    ui.title_bar("Design Assets — Creative coding (shaders, 3D, motion)")
    q = ui.prompt("filter (blank = all)").strip()
    print()
    cmd_creative(q)
    print()
    sid = ui.prompt("show which id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_cli_art(ctx=None) -> None:
    ui.title_bar("Design Assets — CLI art toolkit")
    cmd_cli()
    print()
    txt = ui.prompt("make a banner? type text (blank = skip)").strip()
    if txt:
        print()
        cmd_banner(txt)
    ui.pause()


def _tool_native(ctx=None) -> None:
    ui.title_bar("Design Assets — Native / desktop UI (tkinter + PIL)")
    ui.info("Depth for Python GUI apps — glass cards, gel buttons, glossy "
            "headers, animated splash. Module: ultrapc/nativeui.py")
    print()
    cmd_native("")
    print()
    styles = list(STYLES)
    if ui.ask_yesno("Render a static look-preview (PNG) of a style?"):
        items = [(str(i + 1), STYLES[s]["label"]) for i, s in enumerate(styles)]
        choice = ui.menu("Pick a style", "to preview", items, "Cancel")
        if choice.isdigit() and 1 <= int(choice) <= len(styles):
            cmd_native(f"preview {styles[int(choice) - 1]}")
            ui.pause(); return
    if ui.ask_yesno("Open a LIVE demo window of a style?"):
        items = [(str(i + 1), STYLES[s]["label"]) for i, s in enumerate(styles)]
        choice = ui.menu("Pick a style", "to demo", items, "Cancel")
        if choice.isdigit() and 1 <= int(choice) <= len(styles):
            cmd_native(f"demo {styles[int(choice) - 1]}")
            ui.pause(); return
    sid = ui.prompt("show which recipe id? (blank = skip)").strip()
    if sid:
        print()
        cmd_show(sid)
    ui.pause()


def _tool_showcase(ctx=None) -> None:
    ui.title_bar("Design Assets — Showcase page")
    ui.info("Full profile examples generated from the same checked theme kits.")
    cmd_showcase()
    ui.dim(str(SHOWCASE))
    ui.pause()


def _tool_kit(ctx=None) -> None:
    ui.title_bar("Design Assets — Theme kit (full stylesheet)")
    styles = list(STYLES)
    items = [(str(i + 1), STYLES[s]["label"]) for i, s in enumerate(styles)]
    choice = ui.menu("Pick a style", "for the kit", items, "Cancel")
    if not choice.isdigit() or not (1 <= int(choice) <= len(styles)):
        return
    style = styles[int(choice) - 1]
    if ui.ask_yesno("Save the kit to a .css file? (No = print here)"):
        dest = ui.ask_directory("Choose where to save the kit")
        if dest:
            cmd_kit(style, write=str(Path(dest)))
            ui.pause(); return
    print()
    cmd_kit(style)
    ui.pause()


def _tool_scaffold(ctx=None) -> None:
    ui.title_bar("Design Assets — Scaffold a starter project")
    dest = ui.ask_directory("Choose where to create the starter")
    if not dest:
        ui.warn("Cancelled."); ui.pause(); return
    styles = list(STYLES)
    items = [(str(i + 1), STYLES[s]["label"]) for i, s in enumerate(styles)]
    choice = ui.menu("Pick a style", "for the scaffold", items, "Cancel")
    if not choice.isdigit() or not (1 <= int(choice) <= len(styles)):
        return
    style = styles[int(choice) - 1]
    name = ui.ask_string("Project folder name", initial="my-app") or "my-app"
    out = Path(dest) / _slug(name)
    cmd_scaffold(str(out), style)
    if ui.ask_yesno(f"Created starter in\n{out}\n\nOpen the folder?"):
        core.open_in_os(out)
    ui.pause()


def _tool_sync(ctx=None) -> None:
    ui.title_bar("Design Assets — Sync vault")
    m = sync()
    ui.ok(f"Wrote {m['counts']} to {ASSETS_DIR}")
    ui.dim(f"Catalog: {CATALOG}")
    if ui.ask_yesno("Open the design-system catalog?"):
        core.open_in_os(CATALOG)
    ui.pause()


def _tool_status(ctx=None) -> None:
    ui.title_bar("Design Assets — Status")
    for ln in _status_lines():
        print("  " + ln)
    ui.pause()


def _tool_web(ctx=None) -> None:
    from . import webassets
    webassets.handle(["gallery"])


def register() -> core.Category:
    cat = core.Category("assets", "Design & Art Assets")
    cat.add("web", "Modern web playground (motion, color, glass, layouts)", _tool_web)
    cat.add("palettes", "Browse color palettes", _tool_browse_palettes)
    cat.add("gradients", "Browse gradients", _tool_browse_gradients)
    cat.add("patterns", "Browse background patterns", _tool_browse_patterns)
    cat.add("art", "Browse SVG art (icons, dividers, heroes)", _tool_browse_art)
    cat.add("layouts", "Browse web layout templates", _tool_browse_layouts)
    cat.add("fx", "Advanced CSS techniques (un-generic your UI)", _tool_browse_fx)
    cat.add("creative", "Creative coding (shaders, 3D, motion, generative)", _tool_browse_creative)
    cat.add("native", "Native/desktop UI depth (tkinter + PIL)", _tool_native)
    cat.add("profiles", "Design profiles (archetype collections)", _tool_profiles)
    cat.add("showcase", "Open the profile showcase (browser)", _tool_showcase)
    cat.add("demo", "Open the live vault demo (auto-generated, everything)", _tool_demo)
    cat.add("css", "Browse CSS snippets & components", _tool_browse_css)
    cat.add("anim", "Browse animations (text FX, backgrounds)", _tool_browse_anim)
    cat.add("cli", "CLI art toolkit (banners, boxes, spinners)", _tool_cli_art)
    cat.add("kit", "Generate a full theme kit (one stylesheet)", _tool_kit)
    cat.add("scaffold", "Scaffold a good-looking starter project", _tool_scaffold)
    cat.add("check", "Audit each style's kit against its profile", _tool_check)
    cat.add("sync", "Sync vault to disk + rebuild catalog", _tool_sync)
    cat.add("status", "Vault status", _tool_status)
    return cat


# --------------------------------------------------------------------------- #
#  CLI dispatch (called from ultra.py handle_cli)
# --------------------------------------------------------------------------- #

def handle(argv: list[str]) -> int:
    """`argv` is everything after `assets`. Returns an exit code."""
    if not argv:
        for ln in _status_lines():
            print(ln)
        print("\nsubcommands: palettes | gradients | patterns | art | layouts | "
              "fx | creative | native | profiles | shapes | css | anim | ascii | "
              "web | cli | banner <text> | kit <style> [dir] | show <id> | "
              "scaffold <dir> [--style s] | check [style] | sync | status")
        return 0
    sub = argv[0].lower()
    rest = argv[1:]
    if sub == "web":
        from . import webassets
        return webassets.handle(rest)
    if sub == "palettes":
        return cmd_palettes(" ".join(rest))
    if sub in ("gradients", "grad"):
        return cmd_gradients(" ".join(rest))
    if sub in ("patterns", "pat"):
        return cmd_patterns(" ".join(rest))
    if sub == "art":
        return cmd_art(" ".join(rest))
    if sub in ("layouts", "layout"):
        return cmd_layouts(" ".join(rest))
    if sub in ("fx", "techniques", "tech"):
        return cmd_fx(" ".join(rest))
    if sub in ("creative", "cc"):
        return cmd_creative(" ".join(rest))
    if sub == "showcase":
        return cmd_showcase()
    if sub == "demo":
        return cmd_demo()
    if sub in ("native", "nui", "desktop"):
        return cmd_native(" ".join(rest))
    if sub in ("profiles", "profile", "archetypes"):
        return cmd_profiles(" ".join(rest))
    if sub in ("shapes", "shape", "motifs"):
        return cmd_shapes(" ".join(rest))
    if sub == "ascii":
        return cmd_ascii(" ".join(rest))
    if sub == "cli":
        return cmd_cli()
    if sub == "banner":
        font = "thin"
        words = []
        i = 0
        while i < len(rest):
            if rest[i] == "--font" and i + 1 < len(rest):
                font = rest[i + 1]; i += 2
            else:
                words.append(rest[i]); i += 1
        return cmd_banner(" ".join(words), font=font)
    if sub in ("check", "audit", "lint"):
        return cmd_check(" ".join(rest))
    if sub == "css":
        return cmd_css(" ".join(rest))
    if sub == "anim":
        return cmd_anim(" ".join(rest))
    if sub == "kit":
        if not rest:
            print(f"usage: assets kit <style> [dir]\nstyles: {', '.join(STYLES)}")
            return 2
        return cmd_kit(rest[0], write=rest[1] if len(rest) > 1 else None)
    if sub == "show":
        if not rest:
            print("usage: assets show <id>"); return 2
        return cmd_show(rest[0])
    if sub == "scaffold":
        if not rest:
            print("usage: assets scaffold <dir> [--style <name>]"); return 2
        style = "frutiger-aero"
        target = None
        i = 0
        while i < len(rest):
            if rest[i] == "--style" and i + 1 < len(rest):
                style = rest[i + 1]; i += 2
            else:
                target = rest[i]; i += 1
        if not target:
            print("usage: assets scaffold <dir> [--style <name>]"); return 2
        return cmd_scaffold(target, style)
    if sub == "sync":
        m = sync()
        print(f"Synced {m['counts']} to {ASSETS_DIR}")
        print(f"Catalog: {CATALOG}")
        return 0
    if sub == "status":
        return cmd_status()
    print(f"Unknown assets subcommand '{sub}'."); return 2
