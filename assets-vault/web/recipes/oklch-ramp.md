# oklch-ramp

A perceptual accent ramp that upgrades from sRGB only when supported.

Category: color · Cost: low · Default profile: ultraviolet
Flags: none

Load `web/core.css`, `web/runtime.js`, and `web/effects/oklch-ramp.css` / `.js`.
Use `web/snippets/oklch-ramp.html` as the markup. Preview: `web/demos/oklch-ramp/index.html`.
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

Implementation references: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/color-mix
