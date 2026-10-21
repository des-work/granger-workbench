# aurora-field

Three drifting light fields behind an opaque text plane; no animated blur repaint.

Category: color · Cost: medium · Default profile: ultraviolet
Flags: gradient, motion, organic

Load `web/core.css`, `web/runtime.js`, and `web/effects/aurora-field.css` / `.js`.
Use `web/snippets/aurora-field.html` as the markup. Preview: `web/demos/aurora-field/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "speed": 1,
  "intensity": 1
}
```

Bounds: {"speed":{"default":1,"min":0.2,"max":2,"unit":"","css":"--uv-speed"},"intensity":{"default":1,"min":0.2,"max":1.4,"unit":"","css":"--uv-intensity"}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
