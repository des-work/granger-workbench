# magnetic-button

A pointer-responsive CTA with bounded travel and a still keyboard/touch state.

Category: motion · Cost: low · Default profile: ultraviolet
Flags: motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/magnetic-button.css` / `.js`.
Use `web/snippets/magnetic-button.html` as the markup. Preview: `web/demos/magnetic-button/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "strength": 0.14
}
```

Bounds: {"strength":{"default":0.14,"min":0,"max":0.3,"unit":"","css":null}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
