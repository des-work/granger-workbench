# split-lines

A clipped headline entrance with a single accessible label and readable static text.

Category: motion · Cost: low · Default profile: ultraviolet
Flags: motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/split-lines.css` / `.js`.
Use `web/snippets/split-lines.html` as the markup. Preview: `web/demos/split-lines/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "duration": 900
}
```

Bounds: {"duration":{"default":900,"min":200,"max":1800,"unit":"","css":null}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
