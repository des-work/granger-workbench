# Vaporwave / Y2K  (design profile: `vaporwave`)

**Era:** music and aesthetic from c. 2010-2012; peak 2015; permanent as reference

*A shopping mall at 3am rendered on a machine from 1996: hot pink and cyan, a Greco-Roman bust, fullwidth letterforms, VHS tracking error. Nostalgic for a corporate future that was advertised and never delivered.*

## Origins

Emerged as an ironic variant of chillwave around 2010-11 — Chuck Person's Eccojams Vol. 1, Ferraro's Far Side Virtual, and Floral Shoppe, which set the blueprint — built from chopped-and-screwed samples of smooth jazz, lounge and elevator music. Visually it pulls 1990s web design, glitch art, anime, Greco-Roman statuary, Memphis geometry and 3D-rendered objects, and generally keeps its source material between Japan's 1980s boom and the dot-com crash.

## Composition & space

Centred and symmetrical in a way that feels like a default rather than a decision — the aesthetic of a template nobody customised. Objects float on a grid plane, elements are spaced too evenly, and the composition is allowed to look like a screensaver.

## Proportion & measure

Display type enormous and letterspaced to 0.12em, body type small and plain beneath it — the gap between them is the joke. A 1.414 scale, 60ch measures, 2px borders. Fullwidth characters stretch a word until it stops being a word and becomes a logo.

## Color logic

Hot pink and cyan as the governing pair over a deep indigo night, with acid green and electric violet in support. Saturation stays high and the hues stay adjacent enough to vibrate. Nothing is muted and nothing is corporate — the irony only works at full intensity.

## Light

Sunset gradients and CRT bloom, with no physical logic whatsoever: a grid plane glows at the horizon, objects cast no shadows, and the light source is wherever the gradient says it is. Chrome reflects a sky that does not exist.

## Typography

A geometric or grotesque display face set wide (Righteous), with fullwidth Unicode for titles and a plain system sans beneath. Japanese characters appear as texture rather than language — which is part of the critique and worth being deliberate about.

## Materiality & finish

VHS tape degradation, chrome, marble, mall tile, CRT phosphor, early 3D with visible polygons. Everything looks mass-produced and slightly degraded, as though recovered from a format nobody archived properly.

## Motion & rhythm

Slow, floating, unhurried — 600ms drifts, a bust rotating at a pace nobody asked for, scanlines rolling. Motion is ambient rather than responsive, and the signature effect is tracking error rather than easing.

## Imagery

Classical statuary, palm trees, early 3D renders, dolphins, Windows 95 chrome, empty malls and pools, product shots of obsolete hardware. The rule is that everything depicted was once aspirational and is now landfill.

## Voice (copy & tone)

Fragmentary and affectless, often in fullwidth caps, sometimes in a language the author doesn't speak. Copy reads like advertising stripped of its product — the tone of a slogan with nothing left to sell.

## Sound

Slowed and reverb-drenched: lounge jazz pitched down, mall ambience, a sample looped past the point of function. Interface sounds are startup chimes from operating systems that no longer boot.

## Where it lives

Music releases and cover art, streaming overlays, event pages and merch, retro-gaming and emulation, creative portfolios — anywhere the audience is in on the reference.

## Kinship (family tree)

`cyberpunk`'s nostalgic twin — identical palette, opposite tense: one mourns a past future, the other dreads a near one. Shares `y2k-chrome`'s materials and `avant-basic`'s Memphis geometry, since vaporwave borrowed from Memphis directly. Don't confuse with synthwave, which plays the 80s straight; vaporwave is always at least partly a critique.

## Hierarchy of power

Palette > nostalgia-object > typography > glitch > layout. Composition is deliberately the least considered layer, because the style's whole posture is that someone assembled this quickly and meant it anyway.

## Canon (study these)

Study: Floral Shoppe's cover, Far Side Virtual, early Geocities and Windows 95 interfaces, Memphis Milano catalogues, and any mall photographed after closing.

## Adaptation (modes & accessibility)

Near-white on indigo runs 15:1, but the neon accents sit at 3-4:1 and must stay display-only. Hero gradients here span bright blobs over a dark base, so the kit scrims them rather than hoping — text over a vaporwave gradient needs the wash. No light mode: this style is nocturnal by definition. Reduced motion removes the drift and keeps the colour.

## Signature moves

1. Set the title fullwidth and letterspaced past legibility
2. Float one classical or 3D object with no shadow at all
3. Lay a glowing horizon grid under the whole composition
4. Let tracking error and scanlines sit over the hero

## Components (this vault)

- **tokens/style**: `vaporwave` (`assets kit vaporwave` for a full stylesheet)
- **palette**: `vaporwave-sunset` — #ff71ce #b967ff #01cdfe #05ffa1 #fffb96 #2d1b4e #1a1a2e
- **fonts**: display: Righteous, body: Space Grotesk
- **textures (native)**: scanlines, starfield, grain, mesh
- **gloss**: high and fake — chrome type, wet plastic, a specular highlight on a sphere that has no light to reflect. The gloss is explicitly a render artifact rather than a material property, and looking artificial is the point.
- **shapes**: chrome-blob, lens-flare, orbit-rings, checker-wave
- **patterns**: grid, checkerboard, noise-texture
- **techniques (fx)**: chromatic-aberration, crt-screen, holographic-conic, rotating-text-ring, turbulence-bg

**Rules:** DO centre things, oversize and letterspace the display type, and keep saturation at maximum. DON'T mute the palette or tidy the layout into something tasteful — restraint reads as a brand trying to borrow the look.

**You've lost the plot when:** Fails when a brand uses it sincerely — the aesthetic is about corporate emptiness, so deploying it to sell something collapses the joke. Fails also when cleaned up: a tasteful, well-aligned, slightly-pink page has removed everything that made it vaporwave.
