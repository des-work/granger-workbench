# ambient-marquee

A looping text band with pause controls; duplicates are hidden from assistive technology.

Category: motion · Cost: low · Default profile: ultraviolet
Flags: motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/ambient-marquee.css` / `.js`.
Use `web/snippets/ambient-marquee.html` as the markup. Preview: `web/demos/ambient-marquee/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "speed": 1
}
```

Bounds: {"speed":{"default":1,"min":0.3,"max":2,"unit":"","css":"--uv-speed"}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
