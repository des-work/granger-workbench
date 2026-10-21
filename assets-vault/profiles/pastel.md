# Pastel  (design profile: `pastel`)

**Era:** colour family long-standing; a UI default in waves since c. 2016

*High value, low saturation, and air: lilac, butter, mint and baby blue on a blush field, with soft corners and nothing with a hard edge. Reads as gentle and a little nostalgic — an interface that is trying not to raise anyone's pulse.*

## Origins

A colour family before it was a style: pastels sit high in value and low to medium in saturation, and take their name from the drawing medium, whose sticks were historically less saturated than paints made from the same pigment. The effect is documented rather than fashionable — pastels are used in healthcare to reduce anxiety and in classrooms to help concentration, which is why the palette keeps returning whenever software decides it has been shouting.

## Composition & space

Open and airy with large soft shapes, rounded cards and plenty of gap. Nothing is dense; the layout is allowed to be a little sparse because crowding destroys the calm the palette is doing all this work to produce. Centred headings are acceptable here in a way they are not elsewhere.

## Proportion & measure

A gentle 1.25 scale over four steps, 62ch measure, 20px radius and very generous padding. Everything is slightly larger and slightly further apart than strictly necessary, which is the mechanism by which the style feels unhurried rather than merely pale.

## Color logic

Blush, lilac, mint, periwinkle, peach and butter, all held near the same high value so none of them dominates — the palette is a chord, not a hierarchy. The risk is structural: when everything is light, contrast has to be bought back deliberately in the text colours.

## Light

Diffuse and shadowless, like an overcast morning through a net curtain. Shadows are wide, soft and tinted with the hue beneath them rather than grey. No hard light anywhere — a crisp shadow would introduce the drama the style is avoiding.

## Typography

A rounded geometric sans (Quicksand) with a friendly companion (Poppins) above, set loose and never heavy. Weights stay at 400 and 600; a black weight would break the softness. Letterforms with circular bowls do most of the work of making the thing feel kind.

## Materiality & finish

Matte paper, sugar paper, frosted acrylic, soft cotton, macaron glaze. Surfaces are smooth and slightly powdery — the tactile reference is chalk rather than plastic, which is what keeps the palette from reading as childish.

## Motion & rhythm

Slow and floating: 300ms with a soft settle, small distances, gentle scale rather than translation. Nothing arrives abruptly. Motion here should feel like something drifting down rather than snapping into place.

## Imagery

Soft-focus photography in flat light, simple rounded illustration, gradient blobs, nothing high-contrast. Subjects are shot against pale grounds with no deep shadow, and anything with a hard black in it will fight the whole page.

## Voice (copy & tone)

Warm, encouraging and low-pressure; short friendly sentences without exclamation-mark enthusiasm. The tone reassures rather than persuades, which suits the contexts the palette is clinically used in.

## Sound

Soft mallets, felt piano, gentle pads with slow attacks. Nothing percussive or bright; confirmations are a quiet rounded tone. The sound design has the same brief as the colour — lower the heart rate.

## Where it lives

Wellness and mental-health products, children's and education software, healthcare onboarding, beauty and lifestyle, journalling and habit apps — anywhere the user may arrive anxious.

## Kinship (family tree)

`frutiger-aero` with the gloss removed and the optimism kept. The exact inverse of `hi-contrast`, which spends its contrast budget on legibility where this spends it on mood — and the tension between those two is this style's central problem. Cousin of `avant-basic`, which uses similar hues at full volume. Don't confuse pale with weak: this is a deliberate low-arousal palette.

## Hierarchy of power

Value range > spacing > soft form > typography > accent. Because the hues are nearly equal in weight, hierarchy has to come from space and size rather than colour — which is the discipline most pastel designs skip.

## Canon (study these)

Study: colour-theory treatments of value and saturation, healthcare and paediatric interior palettes, Wes Anderson's production design, Japanese stationery, and macaron photography done properly.

## Adaptation (modes & accessibility)

This is the style most likely to fail an audit: the plum text holds 8:1 on blush, but the muted secondary sits near 4:1 and needs darkening before it carries anything. Accents are decorative, never text. A dark mode means deep plum grounds with the pastels as accents — the same chord played low.

## Signature moves

1. Hold every hue at the same value so none dominates
2. Darken the text until it clears AA, then stop adjusting
3. Round the corners and widen the gaps past comfortable
4. Tint the shadow with the hue beneath it, never grey

## Components (this vault)

- **tokens/style**: `pastel` (`assets kit pastel` for a full stylesheet)
- **palette**: `pastel-dream` — #ffd1dc #ffe5b4 #c7ceea #b5ead7 #e2f0cb #fff5e1 #6d5d6e
- **fonts**: display: Poppins, body: Quicksand
- **textures (native)**: grain, mesh
- **gloss**: soft and low — a 2-level sheen like the glaze on a macaron: present enough to suggest a surface, far too diffuse to produce a highlight. Chrome or wet gloss would snap the whole mood.
- **shapes**: blob-cell, bloom-flower, gloss-orb
- **patterns**: dots, blob
- **techniques (fx)**: aurora-blur, squircle-corners, gooey, layered-shadows

**Rules:** DO keep every hue at the same high value, buy contrast back in the text, and give everything room. DON'T let an accent carry text, don't introduce a hard black, and don't crowd — a dense pastel layout is just washed out.

**You've lost the plot when:** Fails accessibility first and hardest — pale on pale is the single most common way this style ships broken. Fails aesthetically when it goes saccharine: without the discipline of equal values and real text contrast it stops reading as calm and starts reading as a nursery.
