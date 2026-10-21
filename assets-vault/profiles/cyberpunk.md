# Neon / Cyberpunk  (design profile: `cyberpunk`)

**Era:** literary movement from 1982; a permanent interface dialect since

*Film noir with the lights replaced by signage: wet black streets, magenta and cyan bleeding into the dark, monospace everywhere, and an interface that looks like it was built by someone who did not have permission. High tech, visibly low life.*

## Origins

The literary movement of the early 1980s — Gibson, Sterling, Blade Runner's production design — set in a near-future post-industrial dystopia rather than a galactic one, with plots turning on AI, hackers and megacorporations. Much of its atmosphere is borrowed straight from film noir, and its governing proverb is Gibson's: the street finds its own uses for things. That last part is the design brief.

## Composition & space

Dense and layered like a HUD: panels overlapping, readouts in the corners, data where a magazine would put white space. Alignment is tight and technical, but the layers are allowed to stack and occlude — the screen is a surface someone has been working on, not a page someone composed. Use an asymmetric signal console: a compressed status rail, large sector map, chamfered controls and dense telemetry. Keep long reading text in sentence case.

## Proportion & measure

Small, dense type at a 15px base on a 1.333 scale, 72ch measures, 16px gutters. Chrome is thin — 1px borders, hairline rules — so the glow has something precise to bloom against. Labels run uppercase with 0.04em tracking at caption size.

## Color logic

Near-black grounds — true void, not grey — carrying hot magenta and electric cyan as the primary pair, with acid green reserved for terminal states. The accents are allowed to be the only chroma on screen; everything structural is black, and nothing is pastel.

## Light

Everything is emissive. There is no ambient light at all: surfaces are lit only by the signs on them, so glow is the entire lighting model — tight bloom around text, a halo on focus, a dim pulse on anything live. Soft shadows are wrong here, because nothing is being lit from outside.

## Typography

Monospace as the default voice (JetBrains Mono), because the fiction is that you are closer to the machine than you should be, with a wide geometric display face (Orbitron) for titling. Uppercase labels, tabular figures, visible cursors. No serif ever — a serif implies an institution.

## Materiality & finish

Wet asphalt, scratched acrylic, CRT phosphor, anodised metal, cable looms and gaffer tape. Everything is either mass-produced and worn or hand-modified and ugly; the two states together are the texture of the genre.

## Motion & rhythm

Fast and glitchy: 90ms steps rather than smooth curves, scanline drift, occasional RGB split on state change, text that decodes rather than fades. Motion should feel like a signal arriving through interference, never like an animation someone tuned.

## Imagery

Rain-lit streets, kanji and katakana signage, wireframes and point clouds, surveillance crops, exploded diagrams of hardware. People appear as silhouettes against light sources. Anything photographic gets pushed toward two channels and a lot of black.

## Voice (copy & tone)

Terse, technical, slightly hostile: system output rather than copywriting. Status over reassurance — 'LINK DOWN', not 'Something went wrong'. Jargon is allowed to stand unexplained, because the fiction is that you belong here.

## Sound

Rain and distant traffic as room tone, modem handshakes, relay clicks, a synth pad holding one chord too long. Interface sounds are short, dry and slightly clipped — a confirmation should sound like a switch, not a chime.

## Where it lives

Security and network tooling, terminals and developer surfaces, game UI and overlays, music and streaming for electronic genres, hardware dashboards — anywhere looking technical is part of the value.

## Kinship (family tree)

`vaporwave`'s harder sibling: same neon, opposite politics — vaporwave is nostalgic and ironic, cyberpunk is near-future and sincere. Shares `ultraviolet`'s dark field with more aggression and less elegance; `mono` is this style with the power cut. Don't confuse with synthwave, which is a sunset and a sports car, not a tenement and a deadline.

## Hierarchy of power

Darkness > emissive accent > monospace density > glow > glitch. The void has to be genuinely dark first; neon on charcoal is just a dark theme with a hobby.

## Canon (study these)

Study: Blade Runner and 2049's signage, Ghost in the Shell's interface plates, Gibson's Neuromancer, Syd Mead's concept work, and the HUDs in Deus Ex and Cyberpunk 2077.

## Adaptation (modes & accessibility)

Pale cyan on void runs 15:1, and the 72ch measure takes extra leading because reversed text blooms. Magenta is display-only at around 4:1 — never body copy. There is no light mode: inverted, this becomes a different style entirely, so ship `neutral` instead. Reduced motion must kill the glitch, which is a seizure risk, and keep only the glow.

## Signature moves

1. Start from true void, not charcoal, and let signs light it
2. Bloom the accent instead of shadowing the surface
3. Set labels in uppercase monospace with wide tracking
4. Snap state changes in steps so they read as interference

## Components (this vault)

- **tokens/style**: `cyberpunk` (`assets kit cyberpunk` for a full stylesheet)
- **palette**: `cyberpunk-night` — #0d0221 #01012b #ff2a6d #05d9e8 #d1f7ff #f9f002 #7700ff
- **fonts**: display: Orbitron, body: JetBrains Mono
- **textures (native)**: scanlines, carbon, grain
- **gloss**: low but emissive — surfaces are matte and the light comes from inside them. What reads as shine is bloom around a lit element, so a highlight only ever appears where something is switched on.
- **shapes**: grid-marks, signal-dot, crossbar-arrow
- **patterns**: grid, graph-paper, noise-texture
- **techniques (fx)**: crt-screen, chromatic-aberration, hud-plate, svg-soft-glow, scroll-scrub-sequence

**Rules:** DO make the black genuinely black, let the accents emit, and keep the type monospaced and dense. DON'T use a soft drop shadow, a pastel, or a serif — each one imports a politeness the genre doesn't have.

**You've lost the plot when:** Fails as cosplay the moment the neon is decoration rather than light — a pink heading on a grey card is not this. Fails also by prettiness: cyberpunk is grimy and overloaded, and a clean, well-spaced version of it is just a dark theme with cyan buttons.

## Reusable composition

Hero art: `night-city-feed` (original local SVG). Preview: `web/styles/cyberpunk/index.html`.

## Research references

- http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Cyberpunk
- https://www.bfi.org.uk/features/blade-runner

Interpretation and selection notes: `STYLE-RESEARCH.md`.
