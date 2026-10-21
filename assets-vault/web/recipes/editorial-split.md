# editorial-split

Large editorial typography, an offset motif and a boxless numbered reading sequence.

Category: layout · Cost: low · Default profile: high-fashion
Flags: none

Load `web/core.css`, `web/runtime.js`, and `web/effects/editorial-split.css` / `.js`.
Use `web/snippets/editorial-split.html` as the markup. Preview: `web/demos/editorial-split/index.html`.
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
