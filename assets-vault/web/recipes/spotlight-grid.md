# spotlight-grid

A soft pointer-following highlight across a responsive card grid.

Category: interaction · Cost: low · Default profile: ultraviolet
Flags: gradient

Load `web/core.css`, `web/runtime.js`, and `web/effects/spotlight-grid.css` / `.js`.
Use `web/snippets/spotlight-grid.html` as the markup. Preview: `web/demos/spotlight-grid/index.html`.
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
