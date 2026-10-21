# canvas-hero

An immersive, centered canvas hero followed by an offset feature grid.

Category: layout · Cost: low · Default profile: vaporwave
Flags: center

Load `web/core.css`, `web/runtime.js`, and `web/effects/canvas-hero.css` / `.js`.
Use `web/snippets/canvas-hero.html` as the markup. Preview: `web/demos/canvas-hero/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{}
```

Bounds: {}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
