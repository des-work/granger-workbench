# Ember  (design profile: `ember`)

**Era:** a deliberate warm-dark register; current in tooling since c. 2016

*A dark room with a fire in it: near-black browns carrying orange and amber heat, warm shadows, and light that comes from one low source. A dark theme that feels inhabited rather than switched off.*

## Origins

Not a historical movement but a deliberate correction — most dark interfaces are built on blue-grey, which reads as clinical and makes long sessions feel colder than they are. This one takes its reference from combustion: the forge, the hearth, the kiln, where everything visible is lit by the work itself. The colour logic is literal, since a heated material really does run from deep red through orange to yellow-white, and that ramp is the palette.

## Composition & space

Grounded and bottom-weighted, with warmth concentrated where the attention should be and the edges falling away into dark. Generous margins, a single clear focus, and a layout that behaves like a room with one lamp rather than a page with many panels.

## Proportion & measure

A 1.333 scale over four steps at 16px, 68ch measure, 24px gutters, 10px radius. Nothing is cramped: the dark ground swallows tight spacing and makes a dense layout read as muddy, so padding runs a step looser than it would on a light field.

## Color logic

Charred brown and near-black as the ground — warm, never blue — with the heat ramp from deep rust through orange to amber doing all the accent work. Cool colours are excluded on principle: a single blue in here reads as a bug report.

## Light

One low warm source, falling off fast. Glow is tight around hot elements and the rest of the field sits genuinely dark. Shadows are warm brown rather than neutral grey, which is the detail that separates this from an ordinary dark theme.

## Typography

A clean humanist sans for text (DM Sans) under a condensed display face (Bebas Neue) for headings — industrial signage rather than decoration. Heading weight is heavy, text weight is normal, and the contrast between them carries hierarchy without any colour change.

## Materiality & finish

Forged and blackened steel, firebrick, cast iron, charcoal, leather apron, soot on stone. Surfaces are matte and slightly rough; what shines is hot metal, and it shines because of its temperature rather than its finish.

## Motion & rhythm

Warm and organic — 350ms with a soft settle, plus slow ambient flicker on anything glowing, kept under about five percent so it reads as a flame and not as a fault. Nothing snaps; heat does not move in steps.

## Imagery

Low-light process photography — metal being worked, sparks, kilns, hands and tools — shot warm with deep shadows. Subjects are lit by the thing they are making. No flat studio lighting anywhere.

## Voice (copy & tone)

Direct, physical and a little blunt, with verbs that describe making: forge, temper, cut, finish. Confident without the luxury register — this is craft that is proud of effort rather than of price.

## Sound

Fire, bellows, hammer on anvil, the hiss of a quench. Interface sounds are low and warm with a soft attack; nothing bright or digital survives contact with this palette.

## Where it lives

Developer tools that want warmth, maker and workshop brands, barbecue and coffee roasting, gaming and streaming overlays, fitness and strength training, and any dark product tired of looking like a terminal.

## Kinship (family tree)

The warm answer to `cyberpunk` and `ultraviolet`, which are both cool and emissive; shares `earthy`'s pigment family seen at night. `golden-archive` is this palette cooled and sent to a museum. Don't confuse with a red error state — here the orange is the light source, not a warning.

## Hierarchy of power

Warmth of the ground > the single light source > the heat ramp > typography > space. If the dark is blue rather than brown, everything above it fails and the page becomes an ordinary dark theme with orange buttons.

## Canon (study these)

Study: forge and foundry photography, Rembrandt's lit interiors, blackbody colour temperature charts, Japanese sumi-e firelight, and the warmer end of terminal themes like Gruvbox.

## Adaptation (modes & accessibility)

Warm white on charred brown runs 14:1, with the heat accents clearing AA for large text and small amber marks. Keep the brown warm when darkening further. There is no faithful light mode — the premise is a light source in darkness — so ship `earthy` as the daylight companion, since it is the same pigment family at noon.

## Signature moves

1. Build the ground from warm brown-black, never blue-black
2. Light from one low source and let the edges fall away
3. Run every accent along the rust-orange-amber heat ramp
4. Tint shadows warm and flicker the glow under five percent

## Components (this vault)

- **tokens/style**: `ember` (`assets kit ember` for a full stylesheet)
- **palette**: `ember-forge` — #140d0a #241511 #2a1a14 #4d2e1f #ff6b35 #ffc15e #ffefe2
- **fonts**: display: Bebas Neue, body: DM Sans
- **textures (native)**: grain, carbon, brushed
- **gloss**: low and hot — matte everywhere except where something is glowing, and there the brightness is temperature rather than reflection. A cool specular highlight would imply a lamp in the room, which contradicts the single-source premise.
- **shapes**: flame-line, burst-sticker, stepped-frame
- **patterns**: noise-texture, diagonal-stripes
- **techniques (fx)**: svg-soft-glow, grain-overlay, spotlight-hover, layered-shadows

**Rules:** DO keep the dark warm and brown, light from one low source, and run accents along the heat ramp. DON'T introduce a cool hue, don't use neutral grey shadows, and don't let the orange read as an error colour.

**You've lost the plot when:** Fails the moment a cool colour enters — one blue link and the fire goes out. Fails also by over-lighting: if the whole field glows there is no darkness for the heat to sit in, and the result is an orange page rather than a lit room.
