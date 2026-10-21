# High Contrast  (design profile: `hi-contrast`)

**Era:** safety-colour logic from the 1960s; WCAG since 1999; permanent

*Legibility as the entire design: pure black, pure white, and a signal yellow that can be read across a car park at dusk. Not a theme so much as a floor — the version of an interface that still works when nothing else does.*

## Origins

Takes its logic from high-visibility safety equipment, where conspicuity is regulated rather than styled: fluorescent yellow and orange are the standard colours under ISO 20471, and studies of motorcyclists found roughly a third of collisions might have been avoided by reflective or fluorescent clothing. Transfer that to software and the argument is identical — being seen is a safety property.

## Composition & space

Simple, linear, generously spaced: one column where possible, large hit areas, obvious grouping, and no layout that depends on noticing a subtle alignment. Reading order and DOM order agree, because a screen reader is a first-class user of this layout.

## Proportion & measure

18px base and nothing smaller than 16px anywhere. Three sizes on a 1.5 scale so the jumps are unmistakable; borders 2px so they survive a bad monitor; targets at least 44px square; focus rings 3px with a 2px offset so they never sit on top of the thing they indicate.

## Color logic

Black field, white type, one saturated signal — and every pair checked, not estimated. Colour never carries meaning alone: a state is a colour plus an icon plus a word, because a palette is useless to the eight percent of men who cannot separate two of its hues.

## Light

None. Shadows are unreliable at low vision and invisible in forced-colours mode, so separation comes from borders and space. If a layer matters, it gets a 2px edge rather than a blur that may not render.

## Typography

A humanist grotesque with open apertures and unambiguous characters — the 1, l and I must be distinguishable, as must 0 and O. Normal weight for body, bold for emphasis, no italics for anything long, and no letterspaced lowercase. Line length stays at 60ch so returns are easy to track.

## Materiality & finish

Enamel sign, road marking, reflective tape, moulded switch. The reference objects are all things designed to be found by someone who is tired, rushed, or in bad light — which is also the honest description of most users.

## Motion & rhythm

Minimal by default and removable entirely: everything under 100ms, linear, no parallax and no autoplay. `prefers-reduced-motion` is honoured as a hard stop, not a reduction, because for some users motion is nausea rather than delight.

## Imagery

Pictograms over illustration, and every one paired with a label. High-contrast line work at a heavy stroke; no low-contrast decorative photography behind text, ever. If an image carries information, that information also exists as text.

## Voice (copy & tone)

Short sentences, concrete verbs, plain words — the reading level is a design parameter. Instructions say what to do rather than what not to do, errors name the fix, and nothing depends on a metaphor the reader has to decode.

## Sound

Distinct and optional: different confirmations for success and failure so the two are not merely louder versions of each other, every one duplicated visually and in text. Nothing is audio-only, because the user may not have sound at all.

## Where it lives

Government services, healthcare, transport and ticketing, emergency and safety interfaces, kiosk and field equipment, and the accessible mode of everything else — plus any product that intends to pass a WCAG audit rather than argue with one.

## Kinship (family tree)

`swiss-international` with the aesthetics removed and the legibility kept, and the floor beneath `neutral` and `mono`. Direct opposite of `pastel`, which spends its whole contrast budget on mood. Don't confuse it with ugliness: constraint this tight is a design problem, not an excuse.

## Hierarchy of power

Contrast > target size > type size > focus visibility > reading order > everything else. Any trade that costs contrast has been lost before it was made.

## Canon (study these)

Study: WCAG 2.2 and the AAA 7:1 threshold, the GOV.UK Design System, ISO 20471 safety colours, Windows High Contrast and forced-colours mode, and the NHS and US Web design systems.

## Adaptation (modes & accessibility)

White on black is 21:1 and the signal yellow clears AAA. Light mode is the same system inverted at the same ratios. It must survive 200% zoom, 400% reflow, forced-colours, and a monochrome display — and if it does, it is the one style here that is never wrong to ship.

## Signature moves

1. Check every colour pair against 7:1 before shipping it
2. Give every state a colour, an icon and a word
3. Put a 3px focus ring with a 2px offset on everything
4. Separate layers with 2px borders rather than shadow

## Components (this vault)

- **tokens/style**: `hi-contrast` (`assets kit hi-contrast` for a full stylesheet)
- **palette**: `signal-contrast` — #000000 #0d0d0d #101010 #ffe600 #c7c7c7 #ffffff
- **fonts**: display: Archivo Black, body: Inter
- **textures (native)**: stripes
- **gloss**: zero, and not as taste — a sheen lowers local contrast and can erase a glyph for a low-vision reader. Flat colour is the only finish, and the one decorative liberty is a hazard stripe used as a rule.
- **shapes**: signal-dot, crossbar-arrow, stencil-arrow
- **patterns**: diagonal-stripes
- **techniques (fx)**: field-sizing-auto, text-balance-wrap, has-relational, popover-api

**Rules:** DO check every pair against AAA, pair colour with text and shape, and make focus unmissable. DON'T place text on an image, convey state by hue alone, or go below 16px for anything a person has to read.

**You've lost the plot when:** Fails the moment a designer 'softens' it — a grey placeholder, a thin weight, a tasteful low-contrast caption, and the one property it exists for is gone. It also fails by being treated as a toggle bolted on at the end rather than the baseline the rest is tested against.
