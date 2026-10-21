# iridescent-surface

A pointer-lit foil surface with a bounded, decorative sheen.

Category: color · Cost: low · Default profile: y2k-chrome
Flags: gradient, glass

Load `web/core.css`, `web/runtime.js`, and `web/effects/iridescent-surface.css` / `.js`.
Use `web/snippets/iridescent-surface.html` as the markup. Preview: `web/demos/iridescent-surface/index.html`.
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
