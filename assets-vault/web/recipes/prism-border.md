# prism-border

A moving conic edge around a solid surface, with a static border fallback.

Category: color · Cost: low · Default profile: ultraviolet
Flags: gradient, motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/prism-border.css` / `.js`.
Use `web/snippets/prism-border.html` as the markup. Preview: `web/demos/prism-border/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "speed": 1
}
```

Bounds: {"speed":{"default":1,"min":0.2,"max":2,"unit":"","css":"--uv-speed"}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
