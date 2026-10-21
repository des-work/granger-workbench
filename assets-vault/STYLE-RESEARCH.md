# Distinct styles: evidence and implementation

Research date: 2026-10-18. Local source: `wikipedia_en_all_maxi_2026-02`, served by the user's Ultra-PC Kiwix library. Eight canonical articles were read locally, with additional institutional web research. The interpretations below are design decisions based on those sources; they are not claims that a contemporary web page is a historical artifact.

## What was weak

The earlier previews reused a heading, one small motif and a button. Many full-page starters reused the same three feature cards and stock copy. Changing the palette and font did not expose the profile's composition, material or imagery. The atlas now uses complete pages and labels palette/system registers separately from visual styles. Its grayscale control lets the user inspect structure without color.

## Dark Academia

Local Wikipedia describes literature, libraries, Collegiate Gothic architecture, dark wood, candlelight and cluttered scholarly interiors. Bulaitis's research connects the aesthetic to cultivated nostalgia and imagined academic spaces. This supports an inhabited reading room rather than a uniform brown dashboard.

Implemented: `scholar-folio`, original `reading-room` SVG, double-rule manuscript framing, italic introduction, a reading index, drop cap and handwritten marginal note. No faux quotations, institution crests or copied historical artworks.

## Cyberpunk

Local Wikipedia connects technological sophistication with social decay. BFI describes Blade Runner's grungy industrial city, rain, deep shadows and film-noir composition. These references support density, retrofitted structure and emissive signage rather than decorative cyan buttons on roomy cards.

Implemented: `signal-console`, original `night-city-feed` SVG, status rail, chamfered controls, dense telemetry and a compact channel list. Existing dark palette remains; decorative rain and scanlines do not obscure labels or reading text.

## High Fashion

The local Brodovitch article establishes the editorial lineage. MoMA's HTF Didot record explains the revival of Bazaar's earlier art direction and the typeface's extreme thick/thin contrast and display purpose. We use the already licensed local Bodoni Moda as a practical Didone companion, without claiming it is Didot.

Implemented: `atelier-spread`, monumental display, portrait-format `couture-silhouette` art, an asymmetric campaign composition, hairlines and a boxless look index. The original fashion illustration is an offline fallback, clearly identified. Owned campaign photography remains the best extension when a project has it; a decorative icon is not a substitute for campaign art direction.

## Nordic / Scandinavian Modern

Local Wikipedia emphasizes simplicity, function, household objects and democratic design; it also records vivid textiles. Designmuseum Danmark's material research emphasizes natural materials and practical experimentation. Scandinavian design cannot be defined solely as a cold desaturated terminal palette.

Implemented: `nordic-catalog`, original `daylight-objects` interior, practical material index and a named `daylight` token mode. Existing `nordic-frost` application colors remain the default for existing software. The daylight mode is selected only by the named web composition. No claim that all Nordic design is pale, minimal or colorless.

## Stronger alternatives

- **Bauhaus / Workshop Modernism** (`bauhaus`): asymmetric modular poster, functional large numerals and an original form study. MoMA describes a laboratory connecting form studies to applied arts. Bauhaus Dessau cautions against reducing the movement to primary-color clichés. Our red/blue/ochre study is one palette, not the definition of the school.
- **Art Nouveau / Botanical Line** (`art-nouveau`): vertical botanical plate, continuous organic frame and whiplash line. V&A ties this line to natural forms across the decorative arts. Distinguish it from Art Deco's symmetry, steps and fan geometry.
- **Avant Basic** remains available as a contemporary Memphis-influenced direction. The local Memphis article provides the lineage; it is not silently renamed to imply that the two are identical.
- **Swiss International** keeps asymmetric grids, functional type and flush-left text. It remains distinct from fashion's image-led composition and Bauhaus workshop studies.

## Selection guidance

The atlas labels **20 visual styles** and **7 system/color registers**. Neutral, Hi-Contrast, Pastel, Earthy, Jewel, Ultraviolet and Ember remain useful; they are not presented as seven distinct historical movements. Preserve established application identities when using these registers. For a new project seeking a stronger language, begin with a visual style and its composition, art IDs and profile rules; choose effects afterwards.

Start with `web/STYLE-INDEX.md` or `assets web context style/<id>`. The compact context lists the selected layout, art IDs and files. CSS, SVG and typography stay local, so research and rendering are not repeated in cloud prompts.

## Asset provenance

`reading-room`, `night-city-feed`, `couture-silhouette`, `daylight-objects`, `workshop-study` and `iris-whiplash` are original SVG geometry authored for this vault. Research links are references, not downloaded artwork or font licenses. Existing locally vendored font licenses remain attached to portable exports.

## Sources

### dark-academia

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Dark_academia)
- [Institutional reference](https://pure-oai.bham.ac.uk/ws/portalfiles/portal/278801182/os-10894-bulaitis_1_.pdf)

### cyberpunk

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Cyberpunk)
- [Institutional reference](https://www.bfi.org.uk/features/blade-runner)

### high-fashion

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Alexey_Brodovitch)
- [Institutional reference](https://www.moma.org/collection/works/139304)

### nordic

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Scandinavian_design)
- [Institutional reference](https://designmuseum.dk/en/exhibition/matters/)

### bauhaus

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Bauhaus)
- [Institutional reference](https://www.moma.org/calendar/galleries/5388)
- [Institutional reference](https://bauhaus-dessau.de/en/adidas/)

### art-nouveau

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Art_Nouveau)
- [Institutional reference](https://www.vam.ac.uk/articles/the-whiplash/)

### swiss-international

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/International_Typographic_Style)

### avant-basic

- [Local Wikipedia](http://127.0.0.1:4386/content/wikipedia_en_all_maxi_2026-02/Memphis_Group)
