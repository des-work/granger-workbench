# tilt-card

A shallow, bounded 3D tilt that follows a fine pointer.

Category: motion · Cost: low · Default profile: ultraviolet
Flags: motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/tilt-card.css` / `.js`.
Use `web/snippets/tilt-card.html` as the markup. Preview: `web/demos/tilt-card/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "angle": 7
}
```

Bounds: {"angle":{"default":7,"min":0,"max":14,"unit":"","css":null}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
