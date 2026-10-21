# shader-flow

A small original WebGL light-flow background with capped pixel density and no texture downloads.

Category: color · Cost: high · Default profile: ultraviolet
Flags: gradient, organic, motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/shader-flow.css` / `.js`.
Use `web/snippets/shader-flow.html` as the markup. Preview: `web/demos/shader-flow/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "speed": 0.6,
  "intensity": 1
}
```

Bounds: {"speed":{"default":0.6,"min":0.1,"max":1.5,"unit":"","css":null},"intensity":{"default":1,"min":0.1,"max":1,"unit":"","css":"--uv-intensity"}}
Fallback: A solid profile background; one still frame for reduced motion.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
