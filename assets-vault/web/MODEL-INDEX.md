# Compact web asset index

Start with `web/STYLE-INDEX.md` when choosing a visual language. Pick IDs; assemble locally.

`ultra assets web packs` · `ultra assets web search glass` · `ultra assets web context luminous-product`
`ultra assets web build luminous-product ./site`

| ID | Category | What it does |
|---|---|---|
| reveal-stagger | motion | Sequenced entrances with an observer fallback and no hidden content before JS. |
| scroll-progress | motion | A reading-progress rail driven by native scroll timelines, with a measured fallback. |
| scroll-depth | motion | A restrained depth shift with a scroll-linked timeline and JS fallback. |
| magnetic-button | motion | A pointer-responsive CTA with bounded travel and a still keyboard/touch state. |
| tilt-card | motion | A shallow, bounded 3D tilt that follows a fine pointer. |
| shared-transition | motion | Shared-element transitions between two real content states, with immediate fallback. |
| split-lines | motion | A clipped headline entrance with a single accessible label and readable static text. |
| ambient-marquee | motion | A looping text band with pause controls; duplicates are hidden from assistive technology. |
| flip-grid | motion | Animated grid reordering using measured first/last positions rather than layout thrashing. |
| sticky-morph | motion | A navigation band that condenses while scrolling; scroll-state styling enhances a JS fallback. |
| aurora-field | color | Three drifting light fields behind an opaque text plane; no animated blur repaint. |
| prism-border | color | A moving conic edge around a solid surface, with a static border fallback. |
| iridescent-surface | color | A pointer-lit foil surface with a bounded, decorative sheen. |
| gradient-type | color | Perceptual gradient display type with solid readable fallback. |
| blend-spotlights | color | Local colored spotlights that follow a pointer behind an isolated content plane. |
| shader-flow | color | A small original WebGL light-flow background with capped pixel density and no texture downloads. |
| noise-film | color | A static, low-opacity film texture with an opaque fallback and no repeating paint loop. |
| duotone-art | color | A two-color art treatment using profile accents and a composited SVG motif. |
| oklch-ramp | color | A perceptual accent ramp that upgrades from sRGB only when supported. |
| glass-panel | transparency | A real frosted surface with readable inner text and a solid fallback. |
| glass-dock | transparency | A compact, floating navigation dock with actual backdrop blur and explicit focus states. |
| acrylic-card | transparency | Tinted acrylic, a thin specular edge, and a solid text scrim. |
| glass-stack | transparency | Three offset translucent sheets with one live blur layer to bound rendering cost. |
| glass-popover | transparency | A frosted popover that opens by click or keyboard and closes with Escape. |
| edge-fade | transparency | A content rail with soft masked edges and a non-masked fallback. |
| product-bento | layout | An asymmetric product hero and responsive bento collection with container-aware tiles. |
| editorial-split | layout | Large editorial typography, an offset motif and a boxless numbered reading sequence. |
| story-rail | layout | A pinned exhibit opposite a long, numbered chapter rail; folds into a normal reading flow on mobile. |
| overlap-gallery | layout | A dimensional hero followed by a horizontally snapped gallery that remains keyboard-scrollable. |
| product-focus | layout | One large product artifact, a sticky specification panel and clear comparison details. |
| app-panels | layout | A useful application shell with a sticky navigation column, compact hero and adaptive workspace tiles. |
| canvas-hero | layout | An immersive, centered canvas hero followed by an offset feature grid. |
| fluid-magazine | layout | An information-led magazine composition with a wide lead and aligned supporting columns. |
| command-menu | interaction | A searchable command dialog with arrow keys, Enter, Escape and a scoped ⌘/Ctrl-K shortcut. |
| morph-tabs | interaction | Keyboard-accessible tabs with measured content transitions and stable panel IDs. |
| hover-preview | interaction | A work list with a pointer/focus preview and click-to-select support for touch. |
| scrollspy | interaction | A section index that follows visible chapters and preserves normal anchor navigation. |
| media-lightbox | interaction | An artifact lightbox with native modal focus management, Escape and a no-JS inline artifact. |
| anchor-tip | interaction | An anchored contextual tip with focus, pointer and Escape paths, bounded inside the viewport. |
| spotlight-grid | interaction | A soft pointer-following highlight across a responsive card grid. |
| scholar-folio | layout | A candlelit library frontispiece, annotated manuscript and double-ruled reading index. |
| signal-console | layout | A chamfered city-feed console with status rail, live-signal readouts and dense sector index. |
| atelier-spread | layout | A fashion campaign spread with monumental Didone type, a portrait plate and minimal look index. |
| nordic-catalog | layout | A daylight object catalogue, horizontal material index and practical product notes; polar-night mode remains available. |
| geometric-poster | layout | An asymmetric workshop poster with large functional numerals and a measured colour study. |
| botanical-plate | layout | A framed botanical exhibition poster whose border and lettering share a continuous organic line. |

## Complete page packs

- `luminous-product`: ultraviolet / product-bento
- `glass-command`: y2k-chrome / app-panels
- `aero-showcase`: frutiger-aero / overlap-gallery
- `kinetic-editorial`: high-fashion / atelier-spread
- `museum-scroll`: golden-archive / story-rail
- `precision-saas`: neutral / product-bento
- `chromatic-lab`: vaporwave / canvas-hero
- `signal-publication`: swiss-international / fluid-magazine
- `organic-studio`: organic-tech / overlap-gallery
- `jewel-product`: jewel / product-focus
- `candlelit-library`: dark-academia / scholar-folio
- `night-city-console`: cyberpunk / signal-console
- `nordic-daylight`: nordic / nordic-catalog
- `workshop-modern`: bauhaus / geometric-poster
- `botanical-exhibition`: art-nouveau / botanical-plate

The context command returns IDs, paths, parameters and an assembly command. It does not include source code.
A model needs filesystem tools or the exported folder to use local files; pasting full code into a chat loses that benefit.
