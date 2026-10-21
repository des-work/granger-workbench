# Golden Archive  (design profile: `golden-archive`)

**Era:** born 2026 in this vault; ancestry 1977 (Voyager record)

*This vault's homegrown aesthetic: a starlit museum for human knowledge. Deep-space navy, engraved gold, thin artifact frames with halos, constellation paths between exhibits, plaques in italic serif — the Voyager Golden Record as an interface language.*

## Origins

Born 2026-07-04 in this vault's Ultra Archive gallery, designed to exhibit 6.8 million Wikipedia images. Its ancestry: the Voyager Golden Record (1977, Sagan and Drake's offline backup of humanity), museum plaque conventions, star atlases and planetarium graphics.

## Composition & space

Exhibits descend a Z-path linked by dashed constellation lines, one artifact per wall segment with real air around it. Chrome stays pinned and minimal at the top. Depth is parallax — far stars, mid ghosts, foreground artifacts — a corridor, not a page.

## Proportion & measure

Frames thin (1-2px gold) with a 10-16px halo; plaques ~64px under any artifact; catalog numbers six hex characters; parallax ratios near 0.12/0.45/1.0; gaps between exhibits of 0.5-1.5 artifact heights so each gets its wall.

## Color logic

Deep-space navy grounds with gold as the ONLY metal — #d9b453 rising to #f2dc9b highlights — parchment for text, starlight blue-grey for whispers. Jewel accents are deliberately absent: gold is alone because the artifacts provide all other color.

## Light

Starlight and halo: pinpoint speculars, soft gold glow around frames, nebula washes at 5-10% alpha. The room stays dark on purpose — light never floods, so every artifact reads as the brightest thing near it.

## Typography

The plaque voice: bold small-cap sans for titles, italic serif (Georgia/Fraunces) for captions, counts and provenance. Gold for headings, parchment for body, starlight for metadata. Engraved, never printed-loud.

## Materiality & finish

Void, gold leaf, museum glass, engraved brass plaques; film-fine grain over the dark. Every surface is matte except the gold, which is polished — one material gets to shine and it earned it in 1977.

## Motion & rhythm

Drift and parallax: layers scroll at different rates, stars wrap slowly, artifacts glide in and settle. A lightbox blooms out of its exhibit and returns to it. Nothing bounces — this is a museum, not an arcade.

## Imagery

The artifacts themselves — any image becomes imagery once framed in thin gold on the void. Between them: star fields, the grooved gold disk, engraved pictograms in the Voyager manner.

## Voice (copy & tone)

Curatorial reverence with quiet wonder: '6,840,001 artifacts preserved · offline.' Plaques state catalog, collection, dimensions, source — facts as poetry. The museum never exclaims; the collection is the exclamation.

## Sound

Planetarium hush: sub-bass room tone, one soft chime on interaction, the faint tick of a rotating record. Silence is the default state and every sound must justify breaking it.

## Where it lives

The Ultra Archive gallery (its birthplace), knowledge and backup tools, personal wikis, library software, portfolio 'collections' pages — any surface whose job is to EXHIBIT rather than to sell.

## Kinship (family tree)

`art-deco`'s cosmic sibling — both gold-on-dark, but deco is urban theatre and the archive is deep-space quiet. Cousin of `dark-academia` (both sanctify knowledge: academia by candlelight, archive by starlight). Child of this vault itself. Don't confuse with generic dark-luxury: the archive is scientific, not indulgent.

## Hierarchy of power

The void > gold discipline > the artifact > plaque typography > constellation connective tissue. Darkness carries it: brighten the room and the museum becomes a banner ad.

## Canon (study these)

Study: the Voyager Golden Record etching and its cover diagram, NASA/JPL mission patches, Uranometria star plates, museum label conventions, Cosmos title cards — and this vault's own gallery.py, where the style was born.

## Adaptation (modes & accessibility)

Contrast-audited at birth: gold on navy ~10:1, parchment body ~15:1, starlight metadata ~5:1. Light mode is 'the catalog print': parchment field, navy ink, gold rules — a printed museum catalog. Reduced motion: freeze the parallax; the hush survives stillness perfectly.

## Signature moves

1. Frame anything in thin gold with a soft halo on near-black
2. Plaque beneath: small-cap title, gold catalog line, italic source
3. Link elements with dashed gold constellation lines and node dots
4. One grooved gold disk as the seal — the record still spinning

## Components (this vault)

- **tokens/style**: `golden-archive` (`assets kit golden-archive` for a full stylesheet)
- **palette**: `golden-archive` — #04070f #0a1224 #0b101f #5a4b2c #d9b453 #f2dc9b #e8e2d0
- **fonts**: display: Playfair Display, body: Fraunces
- **textures (native)**: starfield, grain
- **gloss**: polished gold only: gel treatment reserved for gold elements (nativeui's golden-archive does this natively); everything else stays void-matte so the gold means something
- **shapes**: gold-disk, constellation-path, stepped-frame
- **patterns**: topographic
- **techniques (fx)**: gradient-border-mask, svg-soft-glow, grain-overlay

**Rules:** DO frame everything in thin gold with a halo, plaque every artifact, connect with constellation lines. DON'T add a second metal or jewel tones, brighten the void, or let chrome outshine the collection.

**You've lost the plot when:** Lost when the room brightens, a second metal arrives, or exhibits crowd each other off the wall. And if the plaques start selling instead of cataloguing, it's not an archive anymore — it's a storefront in a dark theme.
