# story-rail

A pinned exhibit opposite a long, numbered chapter rail; folds into a normal reading flow on mobile.

Category: layout · Cost: low · Default profile: golden-archive
Flags: none

Load `web/core.css`, `web/runtime.js`, and `web/effects/story-rail.css` / `.js`.
Use `web/snippets/story-rail.html` as the markup. Preview: `web/demos/story-rail/index.html`.
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
