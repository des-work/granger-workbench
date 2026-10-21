# noise-film

A static, low-opacity film texture with an opaque fallback and no repeating paint loop.

Category: color · Cost: low · Default profile: golden-archive
Flags: texture

Load `web/core.css`, `web/runtime.js`, and `web/effects/noise-film.css` / `.js`.
Use `web/snippets/noise-film.html` as the markup. Preview: `web/demos/noise-film/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "opacity": 0.055
}
```

Bounds: {"opacity":{"default":0.055,"min":0,"max":0.16,"unit":"","css":"--uv-noise"}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
