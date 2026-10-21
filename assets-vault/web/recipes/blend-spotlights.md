# blend-spotlights

Local colored spotlights that follow a pointer behind an isolated content plane.

Category: color · Cost: medium · Default profile: ultraviolet
Flags: gradient

Load `web/core.css`, `web/runtime.js`, and `web/effects/blend-spotlights.css` / `.js`.
Use `web/snippets/blend-spotlights.html` as the markup. Preview: `web/demos/blend-spotlights/index.html`.
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
