# Ultraviolet  (design profile: `ultraviolet`)

**Era:** spectral since Newton 1672; the dominant dark-mode register since c. 2018

*Indigo depth with violet and electric blue blooming out of it: the short end of the spectrum, treated as a mood. Dark but not grim, synthetic but not neon — closer to a nebula than to a nightclub.*

## Origins

Violet is the shortest visible wavelength, roughly 380 to 450 nanometres, and one of the seven colours Newton named when he divided the spectrum in 1672. It is a spectral colour in a way purple is not — purple is a mixture, violet is a single wavelength — which is why screens render it slightly beyond what pigment can do. Historically it carried Tyrian purple's expense and the robes of emperors, bishops and professors; one European study found violet is the colour most associated with extravagance, individualism and ambiguity, which is a fair description of how it behaves in an interface.

## Composition & space

Spacious and vertical, built around a glowing focal point with everything else receding into the field. Layers are separated by luminosity rather than by borders. The layout breathes — crowding kills the sense of depth the palette exists to create.

## Proportion & measure

A 1.333 scale over four steps, 68ch measure, 24px gutters, 12px radius. Headings can run large because the dark field will carry them. Borders stay at 1px: structure should be felt rather than drawn, with glow doing the separating.

## Color logic

Deep indigo and near-black violet as the field, with electric violet, periwinkle and a cool magenta blooming through it. Saturation is high but lightness stays low except at the focal point — the effect depends on most of the screen staying dark.

## Light

Emissive and volumetric: large soft glows behind content, as though light were passing through a medium rather than falling on a surface. No hard shadows and no single source — the field itself is faintly luminous, the way a nebula is.

## Typography

A geometric sans with generous counters (Sora) above a neutral grotesque (Space Grotesk), set at normal tracking. The type stays plain on purpose: when the background is doing this much, a characterful typeface competes and both lose.

## Materiality & finish

Nothing solid — ionised gas, blacklight, dyed acrylic, deep-dyed velvet seen under UV. Surfaces are translucent rather than reflective, and depth comes from layers of light rather than from texture.

## Motion & rhythm

Slow drifts and long fades — 400ms, easing out over a distance, with ambient movement in the background that never resolves. Glows pulse slowly rather than flashing. Motion should feel atmospheric, like weather in the field.

## Imagery

Astrophotography, long exposures, light through smoke, macro of iridescent surfaces, abstract volumetric renders. Nothing brightly lit, nothing with a hard edge, and almost nothing with a horizon.

## Voice (copy & tone)

Confident and slightly elevated, favouring the abstract noun — vision, signal, depth. It suits products making a claim about intelligence or scale, and it needs watching: the register slides into vagueness faster than any other style here.

## Sound

Deep pads, long reverb tails, sub-bass that is felt rather than heard, a single bell held and allowed to decay. Interface sounds are soft and slightly detuned.

## Where it lives

AI and data products, music and audio tools, crypto and fintech with a futurist posture, conference and launch identities, premium dark-mode marketing sites.

## Kinship (family tree)

`cyberpunk` without the grime and the hostility — same darkness, but atmospheric rather than dystopian. Shares `golden-archive`'s cosmic scale with violet in place of gold, and `jewel`'s depth with light instead of pigment. Don't confuse with `vaporwave`: there is no irony in this one, which is both its strength and its risk.

## Hierarchy of power

Darkness of the field > the glow > space > typography > accent. The field must be genuinely dark and genuinely indigo; violet on grey is a tinted dark theme and reads as one.

## Canon (study these)

Study: Hubble and Webb imagery, Pantone's 2018 Ultra Violet, James Turrell's light installations, Blade Runner 2049's interiors, and the dark-mode launch pages of the last few years of AI products.

## Adaptation (modes & accessibility)

Lavender-white on indigo runs 15:1, and reversed text at a 68ch measure takes the leading step the computation already adds. The violet accent clears AA for large text only. There is no good light mode — inverted, the glow has nothing to glow against — so pair it with `neutral` rather than inverting it.

## Signature moves

1. Keep the field deep indigo and let most of it stay dark
2. Separate layers with volumetric glow instead of borders
3. Place one bloom behind the focal element and nothing else
4. Set plain type and let the background carry the character

## Components (this vault)

- **tokens/style**: `ultraviolet` (`assets kit ultraviolet` for a full stylesheet)
- **palette**: `ultraviolet-bloom` — #0a0618 #150e2e #1a1238 #3c2f6e #8a70ff #c77dff #ece7ff
- **fonts**: display: Sora, body: Space Grotesk
- **textures (native)**: starfield, mesh, grain
- **gloss**: moderate but emissive — nothing reflects, things glow. A highlight means a light source behind the surface rather than a lamp in front of it, so sheen is soft, wide and coloured rather than white.
- **shapes**: constellation-path, gold-disk, orbit-rings
- **patterns**: noise-texture, dots
- **techniques (fx)**: aurora-blur, svg-soft-glow, mesh-gradient-svg, oklch-gradients, scroll-reveal

**Rules:** DO keep the field dark and indigo, separate layers with glow, and leave the typography plain. DON'T add a warm accent, don't flatten the field to grey, and don't let the copy drift into atmosphere with no claim in it.

**You've lost the plot when:** Fails by becoming generic — this is the most imitated dark register in software, and without a specific idea underneath it reads as a template. Fails technically when the field lightens toward grey, at which point the glow has nothing to bloom against and the depth collapses.
