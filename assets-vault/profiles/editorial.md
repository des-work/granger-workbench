# Editorial  (design profile: `editorial`)

**Era:** modern form from the 1850s; digital since the mid-1990s; permanent

*The page as argument: a column grid, a serif that can carry 4,000 words, one red that means 'read this first', and white space measured in column inches rather than sprinkled. Journalism's own design language — built to be read, at speed, by someone standing up.*

## Origins

Nineteenth-century newspapers were densely packed vertical type with a stack of headlines per article, and the craft grew out of fixing that: layout dummies that specified column widths before a typesetter set a word, copy measured in column inches, headline sizes chosen as both letter size and space budget. Paste-up replaced typesetting, direct-to-plate replaced paste-up, InDesign replaced the drawing board — and the column grid survived all three.

## Composition & space

Columns first, everything else negotiated against them. Asymmetric by default, with a dominant element per spread and a clear second; rules and white gutters do the dividing so boxes don't have to. The eye is given one entrance and a route, never a menu of equals.

## Proportion & measure

Measure 60-70ch for the long read, 40-50ch when the page runs multi-column. A 1.414 scale gives four unmistakable steps — deck, standfirst, body, caption — and hairline rules stay at exactly 1px. Drop caps run three lines; pull quotes take a column and a half and never full width.

## Color logic

Black ink on white stock, a grey for secondary matter, and one editorial red reserved for signal — section marks, breaking flags, the live link. Colour is a wayfinding system here, not a mood: if a second accent appears, the reader now has two things to decode instead of one.

## Light

Flat page light, no modelled depth. What dimensionality exists comes from the photography and from the tonal step between body grey and headline black. A drop shadow on a news page reads as a banner ad and is treated as one.

## Typography

An old-style or transitional serif for the body (Lora here) with real italics and true small caps, against a display cut with tighter fit (Playfair Display) for heads. Tabular figures in tables, oldstyle in running text. Hierarchy comes from size, weight and position — never from colour alone.

## Materiality & finish

Newsprint and coated magazine stock: ink that gains slightly, paper with a visible tooth, a fold that the layout respects. The material fact is that this was printed and someone paid per page — every element justifies its inches.

## Motion & rhythm

Minimal and functional. Content arrives, it does not perform: short cross-fades, a sticky masthead that shrinks, progress along the read. If an element animates it is because the reader's position changed, not because the page wanted attention.

## Imagery

Documentary photography with captions that add fact rather than repeat the headline; information graphics that could run without the article. Images are cropped decisively and sized by importance — a half-column mugshot and a full-bleed opener are both editorial decisions, visible as such.

## Voice (copy & tone)

Declarative, sourced, front-loaded: the first sentence carries the news and the rest supports it. Subheads are navigational rather than witty. Adjectives survive only when a fact is underneath them, and the byline takes the credit so the design doesn't have to.

## Sound

Essentially silent — the rustle of a turned broadsheet, a pen on a crossword. Interface sound is limited to a single soft confirmation; a news page that chimes at you has mistaken itself for a notification.

## Where it lives

Newspapers and magazines, long-form online, annual reports, documentation, research publication, any product whose core object is an article — plus every blog that wants to be believed before it is read.

## Kinship (family tree)

`swiss-international` stripped of its dogma and given a serif: same grid discipline, warmer and willing to use ornament when it aids reading. Parent of `neutral`'s layout logic; daylight cousin of `dark-academia`, which shares the serif but adds shadow and sentiment. Don't confuse with minimalism: an editorial page is dense, just organised.

## Hierarchy of power

Grid > typographic hierarchy > white space > the red signal > imagery > ornament. If a reader can't find the start of the article in one second, nothing further down this list will save the page.

## Canon (study these)

Study: the Times and Guardian redesigns, National Geographic and The Economist's grids, Harper's and The New Yorker's text pages, Edward Tufte on information density, and any newspaper front page from before colour printing.

## Adaptation (modes & accessibility)

Black on white is 21:1 and the grey secondary holds 7:1; the editorial red clears AA for text but belongs on small signal elements. Dark mode inverts to a warm off-black with paper-white type and needs a step more leading, since reversed text blooms. The grid is ratio-based, so a phone gets the same system at one column.

## Signature moves

1. Build the column grid and let the gutters divide the page
2. Sink a three-line drop cap to mark the true start
3. Set one pull quote at a column and a half, never full width
4. Reserve the red for signal; everything else is ink and grey

## Components (this vault)

- **tokens/style**: `editorial` (`assets kit editorial` for a full stylesheet)
- **palette**: `editorial-ink` — #111111 #2b2b2b #6b6b6b #cfcfcf #f2f2f2 #ffffff #e11d2a
- **fonts**: display: Playfair Display, body: Lora
- **textures (native)**: paper
- **gloss**: none — this is ink on stock. The only shine permitted is a coated-paper sheen in a photograph of the magazine, never in the interface itself; a gloss here reads as advertising.
- **shapes**: editorial-rule, hairline-frame
- **patterns**: graph-paper
- **techniques (fx)**: dropcap-initial-letter, shape-outside-wrap, text-balance-wrap, scroll-progress-bar

**Rules:** DO set a real column grid, lead with the news, rule rather than box, and caption every image with a fact. DON'T centre body copy, letterspace lowercase, or introduce a second accent colour — the red already means something.

**You've lost the plot when:** Fails by decoration, by centring, and by the second accent colour. It fails hardest when the content is thin: editorial design is a system for organising a lot of information, and over three paragraphs it just looks like a newspaper costume.
