# acrylic-card

Tinted acrylic, a thin specular edge, and a solid text scrim.

Category: transparency · Cost: medium · Default profile: frutiger-aero
Flags: glass, gradient

Load `web/core.css`, `web/runtime.js`, and `web/effects/acrylic-card.css` / `.js`.
Use `web/snippets/acrylic-card.html` as the markup. Preview: `web/demos/acrylic-card/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "opacity": 0.8,
  "blur": 20
}
```

Bounds: {"opacity":{"default":0.8,"min":0.56,"max":0.98,"unit":"","css":"--uv-alpha"},"blur":{"default":20,"min":0,"max":32,"unit":"px","css":"--uv-blur"}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.

Implementation references: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/backdrop-filter
