# product-focus

One large product artifact, a sticky specification panel and clear comparison details.

Category: layout · Cost: low · Default profile: jewel
Flags: none

Load `web/core.css`, `web/runtime.js`, and `web/effects/product-focus.css` / `.js`.
Use `web/snippets/product-focus.html` as the markup. Preview: `web/demos/product-focus/index.html`.
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
