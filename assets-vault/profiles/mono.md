# Mono / Brutalist  (design profile: `mono`)

**Era:** nybrutalism 1950; Banham's essay 1955; the web revival from c. 2014

*Raw structure, visible: hard edges, no radius, a hairline grid you are meant to see, black and white with one colour used like a warning label. The page admits it is a document made of boxes and refuses to pretend otherwise.*

## Origins

Architectural brutalism, read literally. Hans Asplund coined nybrutalism in 1950 for Villa Göth; Alison Smithson used 'new brutalism' in 1953 and stated the intention plainly — to have the structure exposed entirely, without interior finishes wherever practicable. Reyner Banham's 1955 essay tied it to béton brut and art brut, raw concrete and raw art. Web brutalism took the ethic and dropped the concrete.

## Composition & space

Boxes with visible borders, flush alignment, and deliberate collisions. The grid is exposed rather than implied — rules run to the page edge, sections butt against each other with no softening margin, and an element that overlaps does so obviously and on purpose.

## Proportion & measure

Zero radius everywhere; 2px borders; a 1.333 scale across four steps. Measure runs long at 72ch because density is the point and comfort is not the brief. Gutters collapse to nothing where two blocks should read as one slab.

## Color logic

Near-black and bone white carrying everything, with one colour used sparingly and bluntly — closer to a stencilled warning than to a brand accent. No tints, no mid-greys doing diplomacy: a thing is foreground or it is background.

## Light

None, and the absence is the statement. Depth comes from hard offset blocks — a solid shadow with no blur, which reads as a second slab rather than as light. A soft shadow here is a finish, and finishes are what this style refuses.

## Typography

A grotesque or a monospace set tight, with a heavy display cut (Archivo Black) for anything that shouts. Uppercase for labels, system defaults worn proudly, and no optical nicety that would smooth the page. Text may run to the edge; comfort is not owed.

## Materiality & finish

Béton brut: poured concrete with the board marks left in, exposed I-beams, unpainted brick, raw steel. The digital translation is the unstyled element — the default border, the browser's own control, the visible seam where two systems meet.

## Motion & rhythm

Instant or stepped. No easing curves, no fades: state changes snap, because an eased transition is a finish applied to a movement. Where something must move it moves in one hard increment, like a mechanical counter.

## Imagery

Harsh black-and-white, high-grain, halftone or dithered to one bit; screenshots left unretouched; diagrams drawn in the same 2px stroke as the borders. Nothing is colour-graded, because grading is flattery.

## Voice (copy & tone)

Blunt, declarative, lowercase or caps with nothing in between. No onboarding warmth, no apology, no exclamation — the copy tells you what the thing is and lets you decide. Honesty here extends to admitting what the product does not do.

## Sound

Mechanical: a relay click, a key thunk, a printer step. Nothing tonal and nothing designed to feel pleasant; sound confirms that a mechanism moved and that is its whole job.

## Where it lives

Portfolios and studio sites, zines and small-press publishing, developer tools that want to look unmarketed, art and music releases, and any product whose position is that it is not trying to charm you.

## Kinship (family tree)

`swiss-international` gone dark and angry — same grid, opposite manners. Shares `hi-contrast`'s black-and-white economy with none of its duty of care, and `editorial`'s density with none of its serif courtesy. Don't confuse with lazy: brutalism is exposed structure, which requires there to be structure.

## Hierarchy of power

Structure > contrast > typography > density > the one accent. If the skeleton isn't worth exposing, this style has nothing to work with and becomes mere ugliness.

## Canon (study these)

Study: the Smithsons' Hunstanton School, Le Corbusier's Unité d'habitation, Goldfinger's Trellick Tower, Banham's 'The New Brutalism: Ethic or Aesthetic?', brutalistwebsites, and Wim Crouwel's harder grids.

## Adaptation (modes & accessibility)

Bone on near-black runs 17:1 and the long 72ch measure gets extra leading because reversed text needs it. Light mode is the same slab inverted — and arguably more period-correct, since the concrete it refers to is grey. Reduced motion costs nothing here: there was no motion to remove.

## Signature moves

1. Square every corner and set borders to a visible 2px
2. Offset a hard unblurred shadow so it reads as a second slab
3. Run a rule or a block of text clean off the page edge
4. Snap state changes with no easing and no fade

## Components (this vault)

- **tokens/style**: `mono` (`assets kit mono` for a full stylesheet)
- **palette**: `mono-noir` — #0a0a0a #262626 #525252 #a3a3a3 #d4d4d4 #f5f5f5 #ffffff
- **fonts**: display: Archivo Black, body: Space Grotesk
- **textures (native)**: carbon, halftone
- **gloss**: zero, as a matter of ethics rather than taste — gloss is a finish and the whole argument is that finishes conceal structure. The only permitted highlight is the white of the paper showing through a halftone.
- **shapes**: stencil-arrow, grid-marks, crossbar-arrow
- **patterns**: grid, diagonal-stripes, noise-texture
- **techniques (fx)**: pixel-art-shadow, stroke-text, halftone-dots, cut-corner-button

**Rules:** DO expose the grid, keep every corner square, and let elements collide. DON'T round anything, don't blur a shadow, and don't ease a transition — each of those is a finish, and finishes are the thing being refused.

**You've lost the plot when:** Fails when it is costume — raw type over a soft gradient, or a 'brutalist' page with rounded cards underneath. Fails equally by becoming unusable: exposed structure is still structure, and a page nobody can navigate is not austere, just broken.
