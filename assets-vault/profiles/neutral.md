# Neutral  (design profile: `neutral`)

**Era:** minimalist roots from the 1960s; the software default since c. 2014

*The modern product default, done properly: a slate ramp, one blue that means 'act', generous space and nothing with an opinion of its own. Deliberately quiet so the data, the document or the dashboard can be the loud thing.*

## Origins

Descends from post-war minimalism — Judd, Agnes Martin, Flavin, Andre — which set out to reduce art to its essentials and put the object and the viewer's experience ahead of the artist's mediation. Software inherited exactly that argument: the interface should not be the thing you notice. Swiss method, American product management, a decade of design systems.

## Composition & space

A 12-column grid with real alignment and a consistent vertical rhythm; content in cards or sections of predictable width. Asymmetry where it helps scanning, symmetry where it helps comparison. Nothing overlaps, nothing bleeds, nothing surprises — the layout is infrastructure.

## Proportion & measure

A gentle 1.25 scale across five steps, because product UI needs many sizes that stay close together rather than few that shout. Measure 68ch for prose, narrower in a sidebar. Spacing runs on a 4px base; radius 12px; a card's padding is always a multiple of the gutter.

## Color logic

A full slate ramp from near-black to near-white doing almost all the work, with a single blue accent for primary action and semantic green/amber/red reserved strictly for state. Saturation stays low enough that a chart's own colours are the most colourful thing on screen.

## Light

A soft, diffuse, single top light — enough to separate a card from its background and nothing more. Elevation is a tool for layering, not for drama: four steps at most, each meaning a different distance from the page.

## Typography

One humanist grotesque across the whole system (Inter here) at three weights, with tabular figures everywhere numbers align. Tracking tightens slightly as size grows. If a second family appears it is a monospace for code, and it earns its place by being code.

## Materiality & finish

Nothing — and that is the position. No paper, no glass, no metal; surfaces are just planes at different elevations. The honesty here is admitting a screen is a screen, which is why the style survives redesigns that skeuomorphic systems do not.

## Motion & rhythm

Short, functional, 200ms on a standard ease. Motion explains a relationship — where a panel came from, what changed — and then gets out of the way. Nothing bounces, nothing overshoots, and anything over 300ms needs to justify the wait.

## Imagery

Sparse: product screenshots, abstract geometry, illustration kept to a thin consistent line. Photography is used for people and rarely for mood. Icons are a single stroke weight and sit on a 24px grid without exception.

## Voice (copy & tone)

Plain, second-person, present tense: 'Connect your account.' Error messages say what happened and what to do next. No exclamation marks, no personality bolted on in microcopy — the product is a tool and the tone respects the user's time.

## Sound

Near-silent. A short soft tick for confirmation, a quieter one for dismissal, nothing for routine success. The absence is intentional: this is a style people have open for eight hours.

## Where it lives

SaaS dashboards, admin panels, documentation, developer tools, internal software, settings screens — anywhere the interface will be used daily by someone who did not choose it and cannot escape it.

## Kinship (family tree)

`swiss-international`'s pragmatic descendant: same grid, looser rules, a second accent allowed for state. Shares the restraint of `nordic` without the warmth, and of `editorial` without the serif. `hi-contrast` is where it goes when accessibility stops being a checkbox. Don't confuse quiet with empty — a dense dashboard is still this style.

## Hierarchy of power

Grid > typographic scale > spacing rhythm > elevation > the single accent > colour semantics. Get the spacing wrong and no palette will rescue it; get it right and almost any palette works.

## Canon (study these)

Study: the Material and Human Interface guidelines, GitHub Primer, Stripe and Linear's product surfaces, Tufte on data-ink, and the slate ramps in Tailwind and Radix.

## Adaptation (modes & accessibility)

Built dark here — slate on near-black at 13:1, with the muted grey at 7:1. The light inversion is the same system with the ramp reversed and is equally canonical. Because hierarchy comes from spacing and weight rather than hue, it survives colour-blind use and forced-colours mode unchanged.

## Signature moves

1. Set the 4px spacing base and never break it
2. One blue for action; green, amber and red only for state
3. Separate layers with elevation, not with borders and colour
4. Tabular figures anywhere two numbers sit above each other

## Components (this vault)

- **tokens/style**: `neutral` (`assets kit neutral` for a full stylesheet)
- **palette**: `ink-and-glass` — #0f172a #1e293b #334155 #94a3b8 #e2e8f0 #f8fafc #ffffff
- **fonts**: display: Space Grotesk, body: Inter
- **textures (native)**: grain
- **gloss**: almost none — a 1-level sheen at most on a primary button, and only to signal that it is the thing to press. Any glassmorphism belongs to `frutiger-aero`, which is a different argument about what a screen should pretend to be.
- **shapes**: grid-marks, signal-dot
- **patterns**: dots, grid
- **techniques (fx)**: container-query, subgrid-align, has-relational, light-dark-fn, color-mix-theming

**Rules:** DO run everything off one spacing base, keep one accent for action, and use colour only for state. DON'T decorate, don't let a marketing gradient into the product surface, and don't invent a size that isn't on the scale.

**You've lost the plot when:** Fails by blandness when nobody makes a decision — the style tolerates restraint but punishes indifference, and an unconsidered neutral page is just grey. Also fails by creeping accents: the fifth brand colour turns a system into a swatch library.
