# signal-console

A chamfered city-feed console with status rail, live-signal readouts and dense sector index.

Category: layout · Cost: low · Default profile: cyberpunk
Flags: none

Load `web/core.css`, `web/runtime.js`, and `web/effects/signal-console.css` / `.js`.
Use `web/snippets/signal-console.html` as the markup. Preview: `web/demos/signal-console/index.html`.
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
