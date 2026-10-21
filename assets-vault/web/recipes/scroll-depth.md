# scroll-depth

A restrained depth shift with a scroll-linked timeline and JS fallback.

Category: motion · Cost: low · Default profile: ultraviolet
Flags: motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/scroll-depth.css` / `.js`.
Use `web/snippets/scroll-depth.html` as the markup. Preview: `web/demos/scroll-depth/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "distance": 35
}
```

Bounds: {"distance":{"default":35,"min":0,"max":90,"unit":"px","css":"--uv-depth-distance"}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.

Implementation references: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations
