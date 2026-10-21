# Ultra-PC Design System — offline asset vault

> Curated palettes, gradients, patterns, CSS, and animations so apps look polished by default.
> **The user requires aesthetics to come from this vault, not model defaults.**
> **Consult this before building any UI.** Query from the repository root:

```
python ultra.py assets palettes [query]   # color palettes
python ultra.py assets gradients [query]  # ready CSS gradients
python ultra.py assets patterns [query]   # SVG/CSS backgrounds
python ultra.py assets art [query]        # SVG icons/dividers/heroes
python ultra.py assets layouts [query]    # page-structure templates
python ultra.py assets fx [query]         # advanced CSS techniques
python ultra.py assets creative [query]   # shaders/3D/motion/generative (beyond CSS)
python ultra.py assets native [query]     # tkinter/PIL desktop-app depth (NOT web)
python ultra.py assets css [query]        # CSS snippets/components
python ultra.py assets anim [query]       # animations (incl. text FX)
python ultra.py assets kit <style> [dir]  # full themed stylesheet
python ultra.py assets show <id>          # print an asset to paste
python ultra.py assets scaffold <dir> --style <name>
python ultra.py assets check [style]      # audit kits against their profiles
```

**To save tokens: reference an asset by id and run `assets show <id>` (or copy from the on-disk files) instead of regenerating colors/gradients/SVG/CSS from scratch.** Everything here is already tuned — pick, don't re-derive.

Vault root: `assets-vault/` (relative to the repository root)  ·  Python/tkinter import: `exports/palettes.py` · JSON: `exports/palettes.json` · regenerate: `python ultra.py assets sync`

## Modern web production assets

For motion, color effects, transparency, responsive compositions and working interactions, start with **`web/MODEL-INDEX.md`**. It is a compact ID/path index, not source code. The interactive local browser is `web/index.html`.

```sh
python ultra.py assets web packs
python ultra.py assets web search glass --style ultraviolet
python ultra.py assets web context luminous-product
python ultra.py assets web build luminous-product ./my-site
python ultra.py assets web build glass-command ./workspace --zip
python ultra.py assets web gallery
```

46 working modules · 15 complete page packs · native browser runtime · local fonts · no CDN or cloud call. Use the compact context command and the generated AI-BRIEF.md in model prompts; reuse the emitted CSS/JS files. Knobs, compatibility constraints, static fallbacks and cleanup are documented per asset.

## Distinct visual languages

Compare `web/styles/index.html` (or `showcase.html`), use the grayscale structure check, and read `web/STYLE-INDEX.md`. The atlas distinguishes 20 visual styles from 7 useful system/color registers. Research and source links: `STYLE-RESEARCH.md`.

## Styles / design tokens

Each style ships a `tokens-<style>.css` `:root` block — colour, **and** the type scale, grid, motion and material decisions its profile describes. Start from these rather than inventing sizes, leading or easing.

| style | bg · accent · text | type | grid | material | motion |
|---|---|---|---|---|---|
| **Frutiger Aero** (`frutiger-aero`) | `#ceecff` `#257dbc` `#0b3c5d` | 5 sizes @ 1.25 · 64ch · lead 1.488 | 12 col / 24px · left | gloss 3 · soft · r16px | 320ms cubic-bezier(.25,.8,.25,1) |
| **Vaporwave / Y2K** (`vaporwave`) | `#1a1a2e` `#ff71ce` `#fdf5ff` | 4 sizes @ 1.414 · 60ch · lead 1.544 | 12 col / 24px · center | gloss 2 · glow · r14px | 600ms cubic-bezier(.4,0,.6,1) |
| **Neon / Cyberpunk** (`cyberpunk`) | `#0d0221` `#05d9e8` `#d1f7ff` | 4 sizes @ 1.333 · 72ch · lead 1.616 | 12 col / 16px · left | gloss 1 · glow · r0px | 90ms steps(3,end) |
| **Neutral** (`neutral`) | `#0f172a` `#3b82f6` `#e2e8f0` | 5 sizes @ 1.25 · 68ch · lead 1.592 | 12 col / 24px · left | gloss 1 · soft · r12px | 200ms cubic-bezier(.4,0,.2,1) |
| **Pastel** (`pastel`) | `#fff0f6` `#d664a0` `#5b4a63` | 4 sizes @ 1.25 · 62ch · lead 1.476 | 12 col / 24px · left | gloss 2 · soft · r20px | 300ms cubic-bezier(.25,.8,.25,1) |
| **Earthy** (`earthy`) | `#f5efe6` `#c1440e` `#3b2f2a` | 4 sizes @ 1.25 · 66ch · lead 1.5 | 12 col / 24px · left | gloss 0 · soft · r8px | 300ms cubic-bezier(.3,.7,.3,1) |
| **Editorial** (`editorial`) | `#ffffff` `#e11d2a` `#111111` | 4 sizes @ 1.414 · 68ch · lead 1.472 | 12 col / 28px · left | gloss 0 · flat · r2px | 180ms cubic-bezier(.2,0,.2,1) |
| **Mono / Brutalist** (`mono`) | `#0a0a0a` `#ffffff` `#f5f5f5` | 4 sizes @ 1.333 · 72ch · lead 1.616 | 12 col / 0px · left | gloss 0 · hard · r0px | 0ms steps(1,end) |
| **Jewel** (`jewel`) | `#14213d` `#d4af37` `#f8f4e8` | 4 sizes @ 1.414 · 66ch · lead 1.58 | 12 col / 28px · left | gloss 2 · soft · r12px | 400ms cubic-bezier(.22,1,.36,1) |
| **Nordic** (`nordic`) | `#2e3440` `#88c0d0` `#eceff4` | 4 sizes @ 1.25 · 68ch · lead 1.592 | 12 col / 24px · left | gloss 1 · soft · r10px | 220ms cubic-bezier(.4,0,.2,1) |
| **Golden Archive** (`golden-archive`) | `#04070f` `#d9b453` `#e8e2d0` | 4 sizes @ 1.618 · 66ch · lead 1.58 | 12 col / 32px · center | gloss 1 · glow · r6px | 700ms cubic-bezier(.22,1,.36,1) |
| **Ultraviolet** (`ultraviolet`) | `#0a0618` `#8a70ff` `#ece7ff` | 4 sizes @ 1.333 · 68ch · lead 1.592 | 12 col / 24px · left | gloss 2 · glow · r12px | 400ms cubic-bezier(.2,.8,.2,1) |
| **Ember** (`ember`) | `#140d0a` `#ff6b35` `#ffefe2` | 4 sizes @ 1.333 · 68ch · lead 1.592 | 12 col / 24px · left | gloss 2 · glow · r10px | 350ms cubic-bezier(.3,.7,.3,1) |
| **Hi-Contrast** (`hi-contrast`) | `#000000` `#ffe600` `#ffffff` | 3 sizes @ 1.5 · 60ch · lead 1.504 | 12 col / 24px · left | gloss 0 · flat · r4px | 100ms linear |
| **Avant Basic** (`avant-basic`) | `#f6e7ee` `#d81b7a` `#3a2038` | 4 sizes @ 1.618 · 58ch · lead 1.452 | 12 col / 20px · left | gloss 0 · hard · r20px | 450ms cubic-bezier(.34,1.56,.64,1) |
| **Organic Tech** (`organic-tech`) | `#edeee4` `#52704a` `#262e22` | 4 sizes @ 1.25 · 64ch · lead 1.488 | 12 col / 28px · left | gloss 1 · soft · r24px | 520ms cubic-bezier(.34,1.2,.64,1) |
| **High Fashion** (`high-fashion`) | `#f7f4ee` `#141414` `#121212` | 3 sizes @ 1.618 · 70ch · lead 1.524 | 12 col / 40px · left | gloss 0 · none · r0px | 800ms cubic-bezier(.16,1,.3,1) |
| **Skate Culture** (`skate-culture`) | `#141518` `#ff5c1f` `#f1efe8` | 4 sizes @ 1.5 · 64ch · lead 1.568 | 12 col / 16px · left | gloss 0 · hard · r8px | 140ms steps(2,end) |
| **Mosaic** (`mosaic`) | `#f1ece0` `#16697a` `#2b2721` | 4 sizes @ 1.333 · 64ch · lead 1.488 | 12 col / 12px · left | gloss 1 · flat · r6px | 260ms cubic-bezier(.3,.7,.3,1) |
| **Art Deco** (`art-deco`) | `#12100c` `#d4af37` `#f0e7d0` | 4 sizes @ 1.618 · 64ch · lead 1.568 | 12 col / 28px · center | gloss 2 · hard · r2px | 380ms cubic-bezier(.2,.9,.3,1) |
| **Frutiger Metro** (`frutiger-metro`) | `#ffffff` `#c81e82` `#22303b` | 4 sizes @ 1.333 · 64ch · lead 1.488 | 12 col / 20px · left | gloss 1 · flat · r16px | 250ms cubic-bezier(.1,.9,.2,1) |
| **2000s Preppy** (`preppy-2000s`) | `#f7f2e6` `#1e3a67` `#23304b` | 4 sizes @ 1.333 · 62ch · lead 1.476 | 12 col / 20px · center | gloss 2 · soft · r12px | 260ms cubic-bezier(.34,1.3,.64,1) |
| **Y2K Chrome** (`y2k-chrome`) | `#eef2f7` `#2e5fd0` `#1a2333` | 4 sizes @ 1.414 · 60ch · lead 1.464 | 12 col / 20px · center | gloss 3 · glow · r22px | 280ms cubic-bezier(.34,1.56,.64,1) |
| **Dark Academia** (`dark-academia`) | `#201812` `#b08d4f` `#e9ddc8` | 4 sizes @ 1.414 · 68ch · lead 1.552 | 12 col / 32px · left | gloss 0 · soft · r4px | 420ms cubic-bezier(.25,.8,.3,1) |
| **Swiss International** (`swiss-international`) | `#ffffff` `#d0021b` `#111111` | 3 sizes @ 1.5 · 66ch · lead 1.5 | 12 col / 24px · left | gloss 0 · none · r0px | 120ms linear |
| **Bauhaus / Workshop Modernism** (`bauhaus`) | `#f2eee4` `#b42e23` `#191919` | 4 sizes @ 1.414 · 66ch · lead 1.5 | 12 col / 24px · left | gloss 0 · none · r0px | 120ms linear |
| **Art Nouveau / Botanical Line** (`art-nouveau`) | `#f2e9d5` `#405840` `#27382c` | 4 sizes @ 1.414 · 68ch · lead 1.472 | 12 col / 32px · center | gloss 0 · none · r2px | 420ms cubic-bezier(.25,.8,.3,1) |

Each style also declares what it refuses, and `assets check` fails the build when a kit breaks its own rule:

- `frutiger-aero` refuses: grunge, flat
- `vaporwave` refuses: muted, corporate
- `cyberpunk` refuses: pastel, softshadow, serif
- `neutral` refuses: neon
- `pastel` refuses: neon, harshshadow
- `earthy` refuses: neon, glass, chrome
- `editorial` refuses: gradient, glass, neon
- `mono` refuses: gradient, glass, radius, softshadow
- `jewel` refuses: neon, pastel
- `nordic` refuses: neon, gloss3
- `golden-archive` refuses: neon, bounce
- `ultraviolet` refuses: beige, flat
- `ember` refuses: cool, pastel
- `hi-contrast` refuses: gradient, glass, shadow, texture, lowcontrast
- `avant-basic` refuses: gradient, beige, minimal
- `organic-tech` refuses: sharpcorner, neon, grid-rigid
- `high-fashion` refuses: gradient, glass, shadow, bounce, neon
- `skate-culture` refuses: glass, pastel, polish
- `mosaic` refuses: gradient, glass
- `art-deco` refuses: organic, grunge, pastel
- `frutiger-metro` refuses: skeuomorph, bevel, texture
- `preppy-2000s` refuses: grunge, dark
- `y2k-chrome` refuses: matte, muted
- `dark-academia` refuses: neon, glass, chrome, bounce
- `swiss-international` refuses: gradient, glass, shadow, center, texture
- `bauhaus` refuses: gradient, glass, shadow, texture
- `art-nouveau` refuses: gradient, glass, chrome, bounce, neon

Leading is computed, not stored: it tracks the measure and adds a step for reversed (light-on-dark) text, so a wide dark column is not set at the same line height as a narrow light one.

## Palettes


_frutiger-aero_
- **Frutiger Aero — Sky** (`frutiger-aero-sky`) — #2b8fd6 #60b2f0 #ceecff #eaf6ff #ffffff #96cd6e #4e9638 #0b3c5d  · _aqua, glossy, nature, optimistic, clean_
- **Frutiger Aero — Aqua Gloss** (`frutiger-aqua-gloss`) — #00a3e0 #38c6f4 #8fe3ff #d6f6ff #ffffff #0077b6 #023e8a  · _water, gel, bubbles, shine_
- **Frutiger Aero — Nature Tech** (`frutiger-nature-tech`) — #7ac74f #a8e063 #d9f2b4 #eafbe0 #ffffff #2b8fd6 #1b6ca8  · _eco, leaf, fresh, edutainment_

_vaporwave_
- **Vaporwave — Sunset** (`vaporwave-sunset`) — #ff71ce #b967ff #01cdfe #05ffa1 #fffb96 #2d1b4e #1a1a2e  · _neon, pastel, 80s, retro, gradient_
- **Y2K — Chrome & Bubblegum** (`y2k-chrome`) — #c0c6d0 #e8ecf3 #ff5fa2 #7b6cff #5ff0ff #20123a #ffffff  · _y2k, chrome, metallic, millennium, shine_
- **Vaporwave — Miami Nights** (`miami-nights`) — #ff2e97 #00e5ff #8a2be2 #ffcf40 #0f1b3d #071130  · _synthwave, teal, magenta, palm, dusk_

_cyberpunk_
- **Cyberpunk — Night City** (`cyberpunk-night`) — #0d0221 #01012b #ff2a6d #05d9e8 #d1f7ff #f9f002 #7700ff  · _neon, dark, hacker, high-contrast, glow_
- **Neon — Terminal Green** (`neon-terminal`) — #000000 #0a1a0a #00ff41 #00d4aa #39ff14 #0affef  · _matrix, crt, mono, hacker_
- **Neon — Synthwave Grid** (`synthwave-grid`) — #ff006e #fb5607 #ffbe0b #8338ec #3a86ff #12002b  · _synthwave, grid, sunset, outrun_

_neutral_
- **Neutral — Ink & Glass** (`ink-and-glass`) — #0f172a #1e293b #334155 #94a3b8 #e2e8f0 #f8fafc #ffffff  · _neutral, ui, slate, readable_
- **Neutral — Warm Sand** (`warm-sand`) — #1c1917 #44403c #78716c #d6d3d1 #f5f5f4 #fafaf9 #ffffff  · _neutral, warm, paper, cozy_

_pastel_
- **Pastel — Dream** (`pastel-dream`) — #ffd1dc #ffe5b4 #c7ceea #b5ead7 #e2f0cb #fff5e1 #6d5d6e  · _soft, light, airy, kawaii, calm_
- **Pastel — Cotton Candy** (`cotton-candy`) — #ffafcc #ffc8dd #bde0fe #a2d2ff #cdb4db #ffffff  · _pink, blue, sweet, bubbly, light_

_earthy_
- **Earthy — Terracotta Clay** (`terracotta-clay`) — #c1440e #e07856 #e6a57e #d9c5a0 #8a9a5b #f5efe6 #3b2f2a  · _terracotta, warm, muted, organic, artisan_
- **Earthy — Sage & Stone** (`sage-stone`) — #7d8c5c #a3b18a #cbd5c0 #dad7cd #8d8177 #f4f1ea #40483a  · _sage, green, muted, calm, natural_
- **Earthy — Desert Sunset** (`desert-sunset`) — #e07a5f #f2cc8f #e6b89c #cd9777 #81574a #3d405b  · _desert, warm, dusty, rose, adobe_
- **Earthy — Autumn Warmth** (`autumn-warmth`) — #6f1d1b #99582a #bb9457 #dda15e #e9c46a #f4ede4 #432818  · _autumn, rust, mustard, burgundy, cozy_
- **Earthy — Coastal Calm** (`coastal-calm`) — #264653 #2a9d8f #8ab17d #e9c46a #e76f51 #f4f1de  · _coastal, teal, sand, balanced, friendly_
- **Earthy — Retro 70s** (`retro-70s`) — #a44a3f #d68c45 #e0b04a #6b8e5a #4a6d7c #f0e6d2  · _retro, avocado, harvest-gold, vintage, warm_

_editorial_
- **Editorial — Ink on Paper** (`editorial-ink`) — #111111 #2b2b2b #6b6b6b #cfcfcf #f2f2f2 #ffffff #e11d2a  · _minimal, editorial, monochrome, magazine, clean_
- **Editorial — Swiss Minimal** (`swiss-minimal`) — #000000 #ffffff #ff3b30 #0a84ff #f2f2f7 #8e8e93  · _swiss, grid, minimal, bold, functional_

_mono_
- **Mono — Noir** (`mono-noir`) — #0a0a0a #262626 #525252 #a3a3a3 #d4d4d4 #f5f5f5 #ffffff  · _monochrome, brutalist, high-contrast, dark, stark_
- **Mono — Ivory & Charcoal** (`ivory-charcoal`) — #1a1a1a #3d3d3d #767676 #b8b3aa #e8e4dc #faf8f3  · _monochrome, warm-grey, soft, elegant_

_jewel_
- **Jewel — Royal** (`jewel-royal`) — #14213d #1b2a4a #5f0f40 #0f766e #7c3aed #d4af37 #f8f4e8  · _jewel, gold, luxe, deep, sophisticated_
- **Jewel — Forest Botanical** (`forest-botanical`) — #081c15 #1b4332 #2d6a4f #40916c #74c69d #b7e4c7 #d8f3dc  · _forest, green, deep, botanical, rich_

_nordic_
- **Nordic — Frost** (`nordic-frost`) — #2e3440 #3b4252 #4c566a #88c0d0 #a3be8c #d8dee9 #eceff4  · _nordic, muted, cool, hygge, calm_

_golden-archive_
- **Golden Archive — Voyager Record** (`golden-archive`) — #04070f #0a1224 #0b101f #5a4b2c #d9b453 #f2dc9b #e8e2d0  · _gold, space, museum, dark, archive, voyager, starfield, engraved_

_ultraviolet_
- **Ultraviolet — Bloom** (`ultraviolet-bloom`) — #0a0618 #150e2e #1a1238 #3c2f6e #8a70ff #c77dff #ece7ff  · _violet, indigo, electric, dark, complement, neon_

_ember_
- **Ember — Forge** (`ember-forge`) — #140d0a #241511 #2a1a14 #4d2e1f #ff6b35 #ffc15e #ffefe2  · _orange, warm, dark, fire, complement, charcoal_

_hi-contrast_
- **Hi-Contrast — Signal** (`signal-contrast`) — #000000 #0d0d0d #101010 #ffe600 #c7c7c7 #ffffff  · _contrast, accessibility, black, yellow, aaa, bold_

_avant-basic_
- **Avant Basic — Playhouse** (`avant-play`) — #f6e7ee #d81b7a #5438dc #f3a712 #7fc243 #3a2038 #fffaf5  · _avant-basic, checkerboard, squiggle, retro, maximalist, memphis_

_organic-tech_
- **Organic Tech — Living Earth** (`living-earth`) — #edeee4 #dfe4d2 #52704a #8ba888 #a5643a #d9c8a9 #262e22  · _organic, biomorphic, sage, moss, clay, calm, biophilic_

_high-fashion_
- **High Fashion — Runway** (`runway-ivory`) — #f7f4ee #ffffff #141414 #8e7747 #b4a284 #6b665c #d8d2c5  · _fashion, editorial, luxury, ivory, black, champagne, vogue_

_skate-culture_
- **Skate Culture — Grip Tape** (`grip-tape`) — #141518 #1f2125 #ff5c1f #ffd23f #e63946 #989fa8 #f1efe8  · _skate, street, grunge, sticker, asphalt, urban_

_mosaic_
- **Mosaic — Trencadís** (`trencadis`) — #f1ece0 #16697a #a8442c #d9a441 #4a7c59 #6f6a5b #2b2721  · _mosaic, terrazzo, tile, gaudi, stained-glass, fragments_

_art-deco_
- **Art Deco — Gatsby** (`gatsby-gold`) — #12100c #d4af37 #2f9e77 #25567b #8c2f39 #99907a #f0e7d0  · _art-deco, gold, gatsby, sunburst, geometric, 1920s, luxury_

_frutiger-metro_
- **Frutiger Metro — Bloom** (`metro-bloom`) — #ffffff #c81e82 #8ec400 #00a5cf #f97a00 #7a3fb8 #22303b  · _frutiger-metro, vector, bloom, flat, 2000s, vivid_

_y2k-chrome_
- **Y2K — Millennium Chrome** (`millennium-chrome`) — #eef2f7 #dfe7f2 #8fa5bc #2e5fd0 #7de0e6 #c9b8e8 #1a2333  · _y2k, chrome, silver, futurism, millennium, blob_

_dark-academia_
- **Dark Academia — Candlelit Study** (`candlelit-study`) — #201812 #2c221a #8c3838 #3e4a36 #b08d4f #96876f #e9ddc8  · _academia, walnut, oxblood, brass, parchment, scholarly, moody_

_swiss-international_
- **Swiss — Signal Red** (`swiss-signal`) — #ffffff #f2f2f2 #d9d9d9 #595959 #111111 #d0021b #0a4d8c  · _swiss, grid, helvetica, red, objective, modernist_

_preppy-2000s_
- **2000s Preppy — Mall Prep** (`mall-prep`) — #f7f2e6 #1e3a67 #c22f6d #2b7a3d #7fb2e5 #d9c04a #23304b  · _preppy, 2000s, argyle, polo, navy, collegiate_

_bauhaus_
- **Bauhaus — Workshop Study** (`workshop-primary`) — #f2eee4 #191919 #b42e23 #23539b #e1af32 #57534c  · _bauhaus, workshop, geometric, functional, poster_

_art-nouveau_
- **Art Nouveau — Botanical Lithograph** (`botanical-lithograph`) — #f2e9d5 #27382c #405840 #914d37 #887957 #e3d5b8  · _art-nouveau, whiplash, botanical, lithograph, ornament_

_nordic_
- **Nordic — Daylight Objects** (`nordic-daylight`) — #f4f3ed #e7e7df #29332d #3c605b #bda17c #5b6258  · _nordic, scandinavian, daylight, timber, matte_

## Gradients  (paste value into `background:`)

- **aurora** (pastel) — `linear-gradient(135deg, #8ec5fc 0%, #e0c3fc 100%)`
- **cotton-candy** (pastel) — `linear-gradient(135deg, #ffafbd 0%, #ffc3a0 100%)`
- **peachy** (pastel) — `linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)`
- **mint-fresh** (pastel) — `linear-gradient(135deg, #a8ff78 0%, #78ffd6 100%)`
- **sunset-warm** (vaporwave) — `linear-gradient(135deg, #ff6a00 0%, #ee0979 100%)`
- **purple-haze** (vaporwave) — `linear-gradient(135deg, #7f00ff 0%, #e100ff 100%)`
- **gold-hour** (earthy) — `linear-gradient(135deg, #f7971e 0%, #ffd200 100%)`
- **forest-mist** (jewel) — `linear-gradient(135deg, #134e5e 0%, #71b280 100%)`
- **ocean-deep** (nordic) — `linear-gradient(135deg, #2b5876 0%, #4e4376 100%)`
- **royal-jewel** (jewel) — `linear-gradient(135deg, #141e30 0%, #243b55 100%)`
- **mono-fade** (mono) — `linear-gradient(135deg, #232526 0%, #414345 100%)`
- **cyber-glow** (cyberpunk) — `linear-gradient(135deg, #0d0221 0%, #ff2a6d 50%, #05d9e8 100%)`
- **mesh-vibrant** (vaporwave) — `radial-gradient(at 20% 20%, #ff71ce 0px, transparent 50%), radial-gradient(at 80% 0%, #01cdfe 0px, transparent 50%), radial-gradient(at 0% 80%, #05ffa1 0px, transparent 50%), radial-gradient(at 80% 100%, #b967ff 0px, transparent 50%), #1a1a2e`
- **ultraviolet-nebula** (ultraviolet) — `radial-gradient(at 75% 15%, rgba(199,125,255,0.25) 0px, transparent 50%), radial-gradient(at 15% 80%, rgba(138,112,255,0.30) 0px, transparent 55%), linear-gradient(160deg, #0a0618 0%, #150e2e 100%)`
- **ember-heat** (ember) — `radial-gradient(at 50% 110%, rgba(255,107,53,0.35) 0px, transparent 60%), radial-gradient(at 85% 20%, rgba(255,193,94,0.12) 0px, transparent 45%), linear-gradient(180deg, #140d0a 0%, #241511 100%)`
- **archive-space** (golden-archive) — `radial-gradient(at 72% 8%, rgba(217,180,83,0.13) 0px, transparent 45%), radial-gradient(at 18% 85%, rgba(32,42,92,0.55) 0px, transparent 55%), linear-gradient(180deg, #04070f 0%, #0a1224 100%)`
- **mesh-pastel** (pastel) — `radial-gradient(at 27% 37%, #ffd1dc 0px, transparent 45%), radial-gradient(at 97% 21%, #c7ceea 0px, transparent 40%), radial-gradient(at 52% 99%, #b5ead7 0px, transparent 40%), radial-gradient(at 10% 90%, #ffe5b4 0px, transparent 40%), #fff5e1`

## Background patterns

- **dots** (css) — Polka-dot grid. Change color/size via the two values.
- **grid** (css) — Thin line grid.
- **graph-paper** (css) — Layered minor+major grid (graph paper).
- **diagonal-stripes** (css) — 45° candy stripes.
- **checkerboard** (css) — Soft checkerboard via conic-gradient.
- **noise-texture** (css) — Film-grain overlay (SVG feTurbulence data-URI). Put on a positioned parent; tweak opacity to taste.
- **wave-divider** (svg) — Wave section divider. Set a color via `fill`/currentColor; place at the bottom of a section.
- **blob** (svg) — Organic blob shape — decorative accent behind content.
- **topographic** (svg) — Concentric contour lines — subtle map-like texture.

## SVG art  (icons, dividers, hero illustrations)

- **icon-set** — 16 stroke icons as a hidden <symbol> sprite.
- **divider-tilt** — Straight tilted section divider.
- **divider-curve** — Smooth concave curve divider.
- **divider-zigzag** — Zigzag divider edge.
- **hero-blobs** — Two soft overlapping blobs — decorative hero backdrop.
- **hero-landscape** — Layered geometric hills/mountains scene — clean generic hero art.
- **hero-grid** — Synthwave sun + perspective grid horizon — retro/cyberpunk hero.

## Advanced CSS techniques  (kill the generic-AI look)

The moves that make frontends look intricate/artistic instead of default: layered depth, real texture, custom shapes, blend/filter compositing, scroll-driven motion. `assets show <id>` for full code.


_color_
- **animated-gradient-border** — Rotating conic-gradient border via @property (Houdini). The signature 'this isn't a default template' border.
- **aurora-blur** — Soft drifting aurora — 3 blurred color blobs behind content. Replaces the flat one-gradient hero.
- **hue-rotate-text** — Smoothly cycle a heading's hue with an animated custom property.

_depth_
- **layered-shadows** — Stacked shadows that fake real light falloff — far softer/richer than one hard drop shadow (the #1 generic tell).
- **neumorphism** — Soft-UI dual light/dark shadow so elements extrude from the bg.
- **text-3d-extrude** — Extruded 3D text via a stack of offset shadows.
- **tilt-3d** — Perspective tilt on hover — pairs with the spotlight-hover JS.
- **spotlight-hover** — Radial glow that follows the cursor across a card (CSS + 4 lines JS).

_shape_
- **clip-path-shapes** — Break the rectangle — diagonal sections, hexagons, arrows via clip-path.
- **blob-morph** — Organic blob that slowly morphs — great as a decorative mask/backdrop.
- **mask-fade-reveal** — Gradient masks: fade edges, and knock an image out through text.
- **scroll-mask-wipe** — A mask that wipes open as the element scrolls into view (no JS).

_filter_
- **gooey** — Gooey merge filter — blobs/menu items melt together (SVG filter + CSS).
- **grain-overlay** — Film-grain over the whole page — instant analog richness. Default STATIC (free); the animated variant repaints a 2x-viewport fixed layer ~7x/sec and visibly janks pages that also use blurs/filters.
- **duotone** — Duotone any image into two brand colors (SVG feColorMatrix map).
- **chromatic-aberration** — RGB-split chromatic aberration on hover — subtle digital-glitch edge.
- **liquid-hover** — Turbulence + displacement for a liquid/heat-haze distortion on hover.
- **blend-duotone-bg** — Layer color over imagery with blend modes (multiply/overlay/screen) for editorial compositing instead of flat overlays.

_motion_
- **scroll-reveal** — Fade + rise as elements enter the viewport — pure CSS scroll-driven animation, no IntersectionObserver.
- **scroll-parallax** — Real parallax bound to scroll progress (no JS, no jank).
- **infinite-marquee** — Seamless infinite marquee (duplicate the track for the loop).
- **view-transitions** — Smooth morphing transitions between DOM states (View Transitions API).

_type_
- **stroke-text** — Outlined (hollow) display type — huge headings without a fill.
- **variable-font-anim** — Animate a variable font's weight/width for living, kinetic type.

_color_
- **oklch-gradients** — Interpolate gradients in oklch so the midpoint stays vivid — no muddy gray middle you get from sRGB blends.
- **color-mix-theming** — Derive hovers, tints, and borders from ONE brand var with color-mix() — no separate shade tokens to maintain.
- **holographic-conic** — Spinning iridescent/holographic sheen from an animated conic gradient.
- **progress-ring** — Conic progress ring with a masked hole and a smoothly animatable %.

_depth_
- **glass-layered** — Proper frosted glass: blur+saturate, a top sheen, and a light inner border — not just a translucent white box.
- **gradient-border-mask** — A REAL gradient border (any radius) via mask-composite — no padding-box hack, content keeps its own background.
- **pixel-art-shadow** — Draw pixel art with box-shadow (one shadow = one pixel), scaled up.

_layout_
- **anchor-tooltip** — Tether a tooltip/popover to an element with CSS anchor positioning — no JS positioning math.
- **container-query** — Style a component by ITS OWN width, not the viewport — real reusable responsive components.
- **subgrid-align** — Make card internals (title/body/footer) line up ACROSS cards with subgrid.
- **scroll-snap-carousel** — A snappy horizontal carousel with zero JS.
- **sticky-stack-cards** — Cards that pin and stack under each other as you scroll (the 'deck' effect).

_filter_
- **svg-soft-glow** — Soft bloom/neon glow around anything (SVG blur + merge filter).
- **halftone-dots** — Comic/print halftone dot texture over a fill (blend a dot grid).

_motion_
- **scroll-scrub-sequence** — Scrub a hero animation to scroll position (zoom/pan a background as you scroll) — scroll-timeline, no JS.
- **staggered-reveal** — A list whose items reveal one-by-one as each enters view (natural stagger, no per-item JS delays).
- **sticky-shrink-header** — Header that condenses + frosts as you scroll — driven by scroll progress, not a JS scroll listener.
- **card-flip-3d** — 3D flip card (front/back) on hover.
- **elastic-ease** — Springy overshoot with the new linear() easing — bouncy motion without a physics lib.
- **sheen-sweep** — A light sheen that sweeps across a card/button on hover (glossy).

_interaction_
- **has-relational** — Style a parent from its children/state with :has() — quantity queries, form validity, active card, all with no JS.
- **css-only-accordion** — Accessible accordion/disclosure with zero JS using <details>.

_type_
- **text-on-path** — Flow text along a curved SVG path — badges, seals, kinetic headers.

_color_
- **relative-color-syntax** — Derive tints/shades/alpha from ONE color with Relative Color Syntax — generate a whole ramp from a single brand var.
- **light-dark-fn** — Automatic light/dark values with the light-dark() function — one declaration, both modes, no media query.
- **mesh-gradient-svg** — True smooth mesh gradient (SVG) — richer than layered radials.

_depth_
- **squircle-corners** — Apple-style squircle corners with corner-shape: superellipse (smoother than border-radius).
- **emboss-letterpress** — Letterpress/emboss text — carved into or raised off the surface.

_shape_
- **shape-outside-wrap** — Wrap paragraph text around a circle/blob — real magazine flow.
- **clip-path-animate** — Animate clip-path to wipe/morph a reveal (transition or keyframes).

_interaction_
- **popover-api** — Native Popover API — menus/tooltips/dialogs with top-layer + backdrop and zero JS.
- **field-sizing-auto** — Auto-growing inputs/textareas with field-sizing: content — no JS resize hack.
- **css-tabs** — Pure-CSS tabs (radio inputs + :has) — no JavaScript.

_filter_
- **crt-screen** — Full CRT monitor look — scanlines + vignette + subtle flicker.
- **turbulence-bg** — Living organic background (marble / clouds / smoke) via animated SVG feTurbulence.
- **frosted-noise** — Realistic frosted glass = backdrop blur + a faint noise grain on top.

_motion_
- **scroll-progress-bar** — A reading-progress bar that fills with page scroll — pure CSS scroll-timeline.
- **parallax-layers** — Multi-depth parallax — background/mid/foreground move at different speeds, all scroll-driven.
- **text-line-reveal** — Reveal a heading line-by-line (each line rises out of a clip) as it enters view.
- **rotating-text-ring** — Circular text badge that slowly rotates (each letter positioned around a ring).

_type_
- **dropcap-initial-letter** — Real drop cap with initial-letter — sinks the first letter across N lines like print.
- **text-balance-wrap** — Pro typographic line-breaking: balanced headlines, no orphans in body copy.

_filter_
- **houdini-paint** — Procedural backgrounds with the CSS Paint API (Houdini worklet) — draw anything (confetti, waves, noise) as a CSS background.

_depth_
- **hud-plate** — The anti-bubble card: cut-corner plate (clip-path) with an accent notch strip, hairline inset edge, drop-shadow depth that follows the shape, and a corner-cut morph on hover. Use INSTEAD of rounded 'glass bubble' cards — the #1 generic-AI-site tell.

_shape_
- **cut-corner-button** — Sharp cut-corner CTA — replaces the default 999px pill button (the other generic-AI tell). Uppercase display type, clipped corners, drop-shadow depth.

_layout_
- **editorial-float** — Boxless floating text section — a glowing spine rule + ghost stroke-word backdrop + a larger lede paragraph instead of wrapping prose in yet another rounded card. Use for manifesto/about/narrative sections, especially near the top of the page.

## Creative coding  (beyond CSS — shaders, 3D, motion, generative)

For visuals CSS can't reach. Vendored libs live in `libraries/`; `assets show <id>` prints the full recipe.


_shader_
- **shader-gradient-bg** ((none — raw WebGL)) — Full-screen animated GLSL fragment-shader background (GPU). Swap the fragment for aurora/plasma/noise — this is the un-templatey hero backdrop CSS can't do.

_3d_
- **three-hero** (three.min.js) — Three.js hero: a faceted metallic solid with real lighting. Swap geometry/material for glass, torus knots, etc.
- **three-particles** (three.min.js) — Three.js drifting 3D particle field (Points).

_motion_
- **lottie-player** (lottie.min.js) — Play a designer-made After Effects animation (Lottie JSON) — pro motion for near-zero effort. Grab .json files from lottiefiles.com.
- **anime-timeline** (anime.min.js) — Anime.js timeline with staggered entrance — sequencing CSS can't do.
- **motion-spring** (motion.min.js) — Motion One spring physics — natural, bouncy entrances (tiny lib).
- **svg-line-draw** (anime.min.js) — Self-drawing SVG lines/logos (animate stroke) — signature intro move.

_generative_
- **p5-flow-field** (p5.min.js) — Generative flow-field background (Perlin-noise particle streams) — endlessly unique, alive.
- **rough-sketch** (rough.js) — Hand-drawn / sketchy shapes (Rough.js) — the literal opposite of clean AI-generic. Great for playful, editorial, or zine looks.
- **matter-physics** (matter.min.js) — Draggable 2D physics playground (Matter.js) — bouncy, tactile UI toys.

_color_
- **chroma-palette** (chroma.min.js) — Generate a full perceptual color ramp from a few seed colors (bezier + corrected lightness) instead of hand-picking every stop.
- **chroma-contrast** (chroma.min.js) — Pick guaranteed-readable text colors and enforce WCAG AA contrast programmatically — no more failing color combos.
- **chroma-data-scale** (chroma.min.js) — Map data values to colors with a perceptual (lab) scale — proper heatmaps/choropleths, not a rainbow.
- **color-harmonies** (chroma.min.js) — Derive complementary / triadic / analogous palettes from one hue.

_tokens_
- **open-props-use** (open-props.min.css) — Use Open Props — a huge ready set of CSS variables (shadows, easings, gradients, sizes) so you never hand-tune those again.
- **style-dictionary-tokens** ((Node: style-dictionary)) — Single source of design tokens (JSON) → build to CSS vars / JS / iOS / Android. The pro way to keep one theme across platforms.

## Web layout templates  (page structure / orientation)

Token-driven page skeletons — pick the arrangement, pair with a style's `kit`. `assets show <id>` prints the full HTML.

- **single-column** — One centered, measure-limited column. The most readable layout.  · _best for: blogs, docs, articles, long-form reading_
- **hero-cta** — Full-viewport hero: big headline, subcopy, primary + ghost CTA.  · _best for: SaaS / product landing pages_
- **z-pattern** — Alternating left/right rows guide the eye in a Z — image ⇄ text.  · _best for: landing pages with a few key points_
- **f-pattern** — Left-aligned headings + text blocks matching natural F-scan reading.  · _best for: content-heavy / news / scannable pages_
- **split-screen** — 50/50 vertical split — two panels of equal weight side by side.  · _best for: portfolios, two equal choices, product vs pricing_
- **sidebar-app** — Fixed left sidebar + fluid content — the classic app shell.  · _best for: web apps, docs with nav, settings_
- **card-grid** — Responsive auto-fit card grid — columns adapt to width.  · _best for: galleries, catalogs, dashboards, blog indexes_
- **bento-grid** — Trendy 'bento box' grid — mixed-size tiles in one frame.  · _best for: modern landing feature sections, overviews_
- **magazine** — Asymmetric multi-column with a lead story — magazine feel.  · _best for: editorial homepages, publications_
- **full-screen-sections** — Scroll-snap sections that each fill the viewport.  · _best for: storytelling scroll sites, product tours_
- **dashboard** — Topbar + sidebar + content metric grid — full admin shell.  · _best for: admin panels, analytics, back-office_
- **masonry** — Uneven-height items packed in balanced columns (CSS columns).  · _best for: image walls, Pinterest-style feeds_

## CLI art  (make terminal tools look cool)

Reusable module `ultrapc/cliart.py` — `banner(text, font=)` with **two title fonts** (`block` = thick, `thin` = fine box-drawing / intricate title cards), `box()`, `gradient()`/`rainbow()` truecolor, `rule()`, `Spinner`, `progress()`, `loadbar()` animated gradient bar. Run `python ultra.py assets cli` for a live demo, `assets banner --font thin "TEXT"` for a banner. Ultra-PC's own boot splash uses `ui.hero()` (thin font) + `ui.boot()` loading bars. Static pieces:

- **robot** — Little robot mascot.
- **ultra-bot** — Detailed glossy Ultra-PC monitor-bot logo (neofetch-style).
- **cat** — Sleeping cat.
- **computer** — Desktop computer.
- **rocket** — Rocket, for launches.
- **trophy** — Trophy, for PASS/success.
- **divider-stars** — Star divider line.
- **divider-wave** — Wave divider line.
- **arrow-banner** — Arrow header rule.

## Native / desktop UI  (tkinter + PIL — the vault for Python apps)

**CSS and SVG do not render in tkinter.** For native GUI depth use the self-contained module `ultrapc/nativeui.py` (copy it into any project — it has fallback tokens, no other deps beyond Pillow). It renders glass cards, gel buttons, glossy header bars, full-window scenes and an animated splash, all **style-swappable** by the same style names as the web vault (frutiger-aero, cyberpunk, pastel, mono, nordic, …). `assets show native/<id>` prints the recipe; `assets native preview <style>` renders a static PNG look; `assets native demo <style>` opens a live window.

- **themed-window** — A complete themed desktop window (header + glass card + gel button + landing splash), style-swappable.  · _window, skeleton, tkinter, app_
- **glass-card** — Glass panel with drop shadow + gradient surface + sheen. Pack content into `card.body`.  · _card, glass, depth, shadow, panel_
- **gel-button** — Filled action button with profile-specific material, corners, typography and enabled states.  · _button, glossy, gel, aqua_
- **header-bar** — Profile-aware title bar: matte for flat styles, polished where allowed, bubbles for Aero.  · _header, title-bar, glossy_
- **splash** — Animated landing overlay: glass title card + gradient loading bar + rising bubbles, then reveals the app.  · _splash, landing, loading, animation_
- **style-swap** — Re-theme the whole native UI by changing one string — every generator reads the style's tokens.  · _theme, style, tokens, recolor_
- **textures** — Ten themed backdrop textures — grain, brushed metal, carbon weave, CRT scanlines, halftone, diagonal stripes, mesh gradient, starfield, paper — one dispatcher, any style.  · _texture, backdrop, background, surface, grain_
- **starfield** — Deep-space backdrop (as shipped in the Ultra Archive): accent-tinted nebula + glowing stars, themed by style.  · _space, stars, nebula, backdrop, archive_
- **scanlines-crt** — CRT scanlines + phosphor glow — terminals, HUDs, retro-tech panels.  · _crt, retro, terminal, hud, scanlines_
- **brushed-metal** — Brushed-metal panel: horizontal streak noise + soft sheen.  · _metal, brushed, industrial, texture_
- **mesh-gradient** — Multi-point mesh gradient (the trendy blurry-blob hero), drawn from the style's accent family automatically.  · _mesh, blob, hero, gradient, backdrop_
- **neon-button** — Outline-glow button (hover brightens the halo) — the dark-style counterpart to the gel button.  · _button, neon, glow, outline, dark_
- **progress-bar** — Profile-aware progress bar; bounded .set(0..1), visible small values, optional gloss.  · _progress, loading, bar, gradient_
- **toggle-switch** — Keyboard-accessible on/off switch with the profile's material and corner treatment.  · _toggle, switch, checkbox, setting_
- **badge-chip** — Pill badges/chips in four kinds: accent, accent2, outline, surface.  · _badge, chip, pill, tag, label_
- **status-dot** — Glowing status light: ok / warn / err / off — with .set_state() for live dashboards.  · _status, indicator, light, glow, health_
- **plaque** — Engraved museum plaque strip (born in the Ultra Archive) — dark surface, accent hairline; put caption text on top.  · _plaque, caption, museum, engraved, archive_
- **contrast-tools** — WCAG contrast math for native UIs: measure ratios, pick readable ink, auto-fix a color until it passes — check, don't guess.  · _contrast, wcag, accessibility, readable, a11y_
- **divider-ramp** — Fading accent divider + color utilities: ramp() tint→shade scales and harmony() complement/analogous/triadic — stop hand-picking 'a lighter accent'.  · _divider, hairline, ramp, color, harmony_

## Design Profiles  (full archetype collections)

A profile bundles everything that belongs to one design language: tokens, palette, fonts, textures + gloss treatment, signature shapes, matching patterns/fx, and do/don't rules — researched from design-education sources. `assets profiles` lists them; `assets profile <id>` prints the whole collection; `assets kit <style>` themes a page in one shot; shapes live in `shapes/*.svg` (currentColor).

- **avant-basic** (Avant Basic) — 2019-22 Instagram/Shein-era maximalism reviving Memphis and the 60s-70s: warped checkerboards, squiggles, soli…  · shapes: _squiggle, daisy, checker-wave, diamond-star, arch-window_
- **organic-tech** (Organic Tech) — Biomorphic + biophilic: shapes that read as cells, water or pebbles; the 'living earth' palette (sage, moss, c…  · shapes: _blob-cell, pebble-stack, leaf-vein_
- **high-fashion** (High Fashion) — Editorial luxury: ivory field, ink-black Didone serifs at huge scale contrast, hairline rules, champagne accen…  · shapes: _hairline-frame, editorial-rule_
- **skate-culture** (Skate Culture) — Deck art + sticker bombing + zine grunge: asphalt darks under safety orange and hazard yellow, distressed text…  · shapes: _burst-sticker, flame-line, stencil-arrow_
- **mosaic** (Mosaic) — Tessellation as a design language: terrazzo chips, Gaudí trencadís crackle, stained-glass panes with visible g…  · shapes: _terrazzo-chips, trencadis-pane, tessera-band_
- **art-deco** (Art Deco) — 1920s-40s controlled opulence: black + gold + jewel tones, graduated sunbursts (rays tighter at the center), s…  · shapes: _sunburst, deco-fan, stepped-frame, chevron-band_
- **frutiger-metro** (Frutiger Metro) — Frutiger Aero's flat 2D sibling (mid-2000s vector culture): loud magenta/lime/aqua/orange color blocks, bloom …  · shapes: _bloom-flower, metro-dots, swoosh-ribbon_
- **preppy-2000s** (2000s Preppy) — Mall-era collegiate (Abercrombie/Hollister/AE): polo navy + pink + kelly green on cream, argyle and gingham, c…  · shapes: _argyle-tile, gingham-tile, crest-shield, ribbon-banner_
- **frutiger-aero** (Frutiger Aero) — 2004-13 techno-optimist humanism: glossy water, glass, grass and sky. Bubbles rise, koi drift, interfaces floa…  · shapes: _aqua-bubbles, gloss-orb, grass-swoosh_
- **y2k-chrome** (Y2K Chrome) — 1997-2003 millennium futurism: liquid chrome, silver everything, translucent candy plastic, lens flares and bl…  · shapes: _chrome-blob, lens-flare, orbit-rings_
- **dark-academia** (Dark Academia) — Candlelit scholarship: oxblood and walnut, brass and parchment, annotated margins, plaster casts and rain agai…  · shapes: _wax-seal, open-book, laurel-corner_
- **swiss-international** (Swiss International) — The International Typographic Style: objective white space, a mathematical grid, one neo-grotesque family, one…  · shapes: _grid-marks, signal-dot, crossbar-arrow_
- **golden-archive** (Golden Archive) — This vault's homegrown aesthetic: a starlit museum for human knowledge. Deep-space navy, engraved gold, thin a…  · shapes: _gold-disk, constellation-path, stepped-frame_
- **editorial** (Editorial) — The page as argument: a column grid, a serif that can carry 4,000 words, one red that means 'read this first',…  · shapes: _editorial-rule, hairline-frame_
- **neutral** (Neutral) — The modern product default, done properly: a slate ramp, one blue that means 'act', generous space and nothing…  · shapes: _grid-marks, signal-dot_
- **hi-contrast** (High Contrast) — Legibility as the entire design: pure black, pure white, and a signal yellow that can be read across a car par…  · shapes: _signal-dot, crossbar-arrow, stencil-arrow_
- **mono** (Mono / Brutalist) — Raw structure, visible: hard edges, no radius, a hairline grid you are meant to see, black and white with one …  · shapes: _stencil-arrow, grid-marks, crossbar-arrow_
- **cyberpunk** (Neon / Cyberpunk) — Film noir with the lights replaced by signage: wet black streets, magenta and cyan bleeding into the dark, mon…  · shapes: _grid-marks, signal-dot, crossbar-arrow_
- **vaporwave** (Vaporwave / Y2K) — A shopping mall at 3am rendered on a machine from 1996: hot pink and cyan, a Greco-Roman bust, fullwidth lette…  · shapes: _chrome-blob, lens-flare, orbit-rings, checker-wave_
- **nordic** (Nordic) — Long winter light handled well: muted blue-greys, pale wood, generous space and nothing shouting. Calm without…  · shapes: _pebble-stack, leaf-vein, grid-marks_
- **earthy** (Earthy) — Clay, rust, olive and sand: a palette taken from fired pottery and dry landscape, set in a warm serif with ple…  · shapes: _pebble-stack, leaf-vein, blob-cell_
- **pastel** (Pastel) — High value, low saturation, and air: lilac, butter, mint and baby blue on a blush field, with soft corners and…  · shapes: _blob-cell, bloom-flower, gloss-orb_
- **jewel** (Jewel) — Deep saturated colour over dark grounds: emerald, sapphire, garnet and old gold, lit like a display case. Luxu…  · shapes: _gold-disk, stepped-frame, laurel-corner_
- **ultraviolet** (Ultraviolet) — Indigo depth with violet and electric blue blooming out of it: the short end of the spectrum, treated as a moo…  · shapes: _constellation-path, gold-disk, orbit-rings_
- **ember** (Ember) — A dark room with a fire in it: near-black browns carrying orange and amber heat, warm shadows, and light that …  · shapes: _flame-line, burst-sticker, stepped-frame_
- **bauhaus** (Bauhaus / Workshop Modernism) — A workshop, not a colour theme: asymmetric typography, measured geometric studies and useful objects. Form, ma…  · shapes: _workshop-study_
- **art-nouveau** (Art Nouveau / Botanical Line) — A botanical print grown into a page: sinuous stems, elongated lettering, warm paper and a continuous ornamenta…  · shapes: _iris-whiplash_

## CSS snippets & components

- **grid-system** (neutral) — The actual grid. Several profiles call the grid their first move and then had nothing to build it with. Columns and gutter come from the style's tokens.  · _grid, layout, columns, structure_
- **type-scale** (neutral) — Binds the computed type scale, leading and measure to real elements, so the style's size budget is what the page uses.  · _type, scale, measure, leading_
- **navbar-solid** (swiss-international) — Matte navigation bar for styles that forbid glass. Same job as navbar-glass with no backdrop-filter and no translucency.  · _navbar, header, matte, sticky, flat_
- **hero-flush** (swiss-international) — Asymmetric flush-left hero on the grid — the counterpart to hero-centered for styles whose rule is 'never centre'.  · _hero, landing, flush-left, asymmetric, grid_
- **glass-card** (frutiger-aero) — Frosted-glass panel with blur, inner sheen, and soft border.  · _glassmorphism, card, frosted_
- **aqua-gel-button** (frutiger-aero) — Glossy Frutiger-Aero gel button with top highlight sheen.  · _button, glossy, gel, 3d_
- **neon-glow** (cyberpunk) — Neon glow for text and outlined buttons (uses currentColor).  · _neon, glow, text, button_
- **vaporwave-bg** (vaporwave) — Vaporwave hero: sunset gradient with a perspective grid floor.  · _background, gradient, grid, hero_
- **crt-scanlines** (cyberpunk) — CRT scanline + flicker overlay. Put over any container.  · _crt, retro, overlay, scanlines_
- **animated-gradient-bg** (neutral) — Slowly-shifting multi-color gradient background.  · _background, gradient, animated_
- **elevation-shadows** (neutral) — A 5-step soft shadow elevation scale (utility classes).  · _shadow, elevation, tokens, depth_
- **gradient-text** (vaporwave) — Gradient-filled heading text (clip to text).  · _text, gradient, heading_
- **navbar-glass** (neutral) — Sticky frosted-glass top navigation bar.  · _navbar, header, glass, sticky_
- **hero-centered** (neutral) — Centered hero section with fluid headline.  · _hero, landing, layout, headline_
- **feature-card** (neutral) — Lifting feature card with an accent icon chip. Uses your tokens.  · _card, feature, hover, grid_
- **badge-pill** (neutral) — Accent-tinted pill badge (auto-colors from --accent).  · _badge, tag, pill, label_
- **input-field** (neutral) — Text input with an accent focus ring. Uses your tokens.  · _form, input, field, focus_

## Animations  (text-first)

- **typewriter** (css, neutral) — Typewriter reveal with a blinking caret (single line).
- **glitch-text** (css, cyberpunk) — RGB-split glitch on text. Set data-text to the same string.
- **neon-flicker** (css, cyberpunk) — Neon sign flicker — irregular blinks then steady glow.
- **gradient-text-shift** (css, vaporwave) — Animated gradient sweeping through heading text.
- **wave-text** (css, neutral) — Per-letter bobbing wave. Wrap each letter in <span> and set delays.
- **float** (css, frutiger-aero) — Gentle floating bob — great for glossy icons/bubbles.
- **pulse-glow** (css, cyberpunk) — Breathing glow to draw attention to a button/badge.
- **fade-in-up** (css, neutral) — Standard entrance: fade + rise. Add to elements on load.
- **shimmer** (css, neutral) — Skeleton-loading shimmer sweep.
- **bubbles-js** (js, frutiger-aero) — Rising translucent bubbles on a <canvas id='bubbles'> — Frutiger Aero.
- **matrix-rain-js** (js, cyberpunk) — Falling green code rain on a <canvas id='matrix'>.
- **starfield-js** (js, vaporwave) — Warp starfield flying toward the viewer on <canvas id='stars'>.

## Fonts (offline, OFL)

Link `fonts/fonts.css`, then use the family name:

- **Alfa Slab One** (400) — 2000s-preppy varsity slab  ·  `fonts/alfa-slab-one-400.woff2`
- **Archivo Black** (400) — heavy display / brutalist  ·  `fonts/archivo-black-400.woff2`
- **Bangers** (400) — skate/pop loud display  ·  `fonts/bangers-400.woff2`
- **Bebas Neue** (400) — condensed bold headline  ·  `fonts/bebas-neue-400.woff2`
- **Bodoni Moda** (700) — high-fashion Didone masthead  ·  `fonts/bodoni-moda-700.woff2`
- **Caveat** (400) — handwriting / playful accent  ·  `fonts/caveat-400.woff2`
- **Cinzel** (600) — art-deco/mosaic engraved roman  ·  `fonts/cinzel-600.woff2`
- **DM Sans** (400) — ember body  ·  `fonts/dm-sans-400.woff2`
- **DM Sans** (500) — clean geometric sans / neutral  ·  `fonts/dm-sans-500.woff2`
- **Fira Code** (400) — mono w/ ligatures / code  ·  `fonts/fira-code-400.woff2`
- **Fraunces** (400) — jewel body  ·  `fonts/fraunces-400.woff2`
- **Fraunces** (600) — fancy serif display / jewel  ·  `fonts/fraunces-600.woff2`
- **Fredoka** (500) — avant-basic body / frutiger-metro display  ·  `fonts/fredoka-500.woff2`
- **Inter** (400) — neutral / body text everywhere  ·  `fonts/inter-400.woff2`
- **Inter** (700) — neutral / bold headings  ·  `fonts/inter-700.woff2`
- **JetBrains Mono** (400) — code / cyberpunk mono  ·  `fonts/jetbrains-mono-400.woff2`
- **Lora** (400) — readable serif body / editorial  ·  `fonts/lora-400.woff2`
- **Orbitron** (700) — cyberpunk / sci-fi headings  ·  `fonts/orbitron-700.woff2`
- **Pacifico** (400) — preppy script accent  ·  `fonts/pacifico-400.woff2`
- **Permanent Marker** (400) — skate hand-marker accent  ·  `fonts/permanent-marker-400.woff2`
- **Playfair Display** (700) — elegant serif display / editorial  ·  `fonts/playfair-display-700.woff2`
- **Poiret One** (400) — art-deco tall geometric display  ·  `fonts/poiret-one-400.woff2`
- **Poppins** (600) — geometric / friendly headings  ·  `fonts/poppins-600.woff2`
- **Press Start 2P** (400) — Y2K / 8-bit arcade  ·  `fonts/press-start-2p-400.woff2`
- **Quicksand** (400) — pastel body  ·  `fonts/quicksand-400.woff2`
- **Quicksand** (500) — rounded / friendly / pastel body  ·  `fonts/quicksand-500.woff2`
- **Righteous** (400) — retro rounded display / Y2K  ·  `fonts/righteous-400.woff2`
- **Shrikhand** (400) — avant-basic / groovy bubble display  ·  `fonts/shrikhand-400.woff2`
- **Sora** (600) — modern display / tech  ·  `fonts/sora-600.woff2`
- **Space Grotesk** (400) — mono / vaporwave body  ·  `fonts/space-grotesk-400.woff2`
- **Space Grotesk** (500) — modern display headings  ·  `fonts/space-grotesk-500.woff2`
- **Space Grotesk** (600) — neutral display  ·  `fonts/space-grotesk-600.woff2`
- **VT323** (400) — retro CRT terminal  ·  `fonts/vt323-400.woff2`

## Vendored libraries (offline)

- `libraries/animate.min.css`  (70 KB)
- `libraries/anime.min.js`  (16 KB)
- `libraries/chroma.min.js`  (45 KB)
- `libraries/lottie.min.js`  (298 KB)
- `libraries/matter.min.js`  (81 KB)
- `libraries/motion.min.js`  (24 KB)
- `libraries/open-props.min.css`  (26 KB)
- `libraries/p5.min.js`  (1010 KB)
- `libraries/rough.js`  (27 KB)
- `libraries/three.min.js`  (654 KB)
