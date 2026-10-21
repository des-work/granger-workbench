# Local design brief

Use the Ultra-PC `dark-academia` profile and `scholar-folio` layout.
Selected effects: noise-film, reveal-stagger, scroll-progress.

The site is already assembled. Edit the words, links, and content in `index.html`.
Reuse the CSS/JS files under `assets/web/`; do not regenerate those effects or
paste their full source into model context. `design.json` records IDs and knob
values. To change motion or material, use the selected asset's documented knobs.
Preserve the project's identity and the profile's constraints.

Fonts and licenses are local. No package install, CDN, API call, or bundler is
needed to run this output. Use `assets/web/manifest.json` to discover additional
local modules; read only the files needed for a real code change. Module controls
are set in `data-uv-config`. Motion honors the reader's preferences; use
`UltraWeb.setMotion(true)` to pause it. Add `data-uv-solid` on `<html>` for opaque
surfaces. User content must remain readable with either preference.
