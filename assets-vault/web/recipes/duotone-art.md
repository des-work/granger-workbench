# duotone-art

A two-color art treatment using profile accents and a composited SVG motif.

Category: color · Cost: low · Default profile: ultraviolet
Flags: gradient

Load `web/core.css`, `web/runtime.js`, and `web/effects/duotone-art.css` / `.js`.
Use `web/snippets/duotone-art.html` as the markup. Preview: `web/demos/duotone-art/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{}
```

Bounds: {}
Fallback: Two solid profile colors; no external image is required.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
