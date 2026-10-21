# anchor-tip

An anchored contextual tip with focus, pointer and Escape paths, bounded inside the viewport.

Category: interaction · Cost: low · Default profile: ultraviolet
Flags: none

Load `web/core.css`, `web/runtime.js`, and `web/effects/anchor-tip.css` / `.js`.
Use `web/snippets/anchor-tip.html` as the markup. Preview: `web/demos/anchor-tip/index.html`.
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
