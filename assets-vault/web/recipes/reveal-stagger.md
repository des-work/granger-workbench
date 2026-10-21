# reveal-stagger

Sequenced entrances with an observer fallback and no hidden content before JS.

Category: motion · Cost: low · Default profile: ultraviolet
Flags: motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/reveal-stagger.css` / `.js`.
Use `web/snippets/reveal-stagger.html` as the markup. Preview: `web/demos/reveal-stagger/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "distance": 28,
  "duration": 650,
  "stagger": 100
}
```

Bounds: {"distance":{"default":28,"min":0,"max":80,"unit":"","css":null},"duration":{"default":650,"min":100,"max":1600,"unit":"","css":null},"stagger":{"default":100,"min":0,"max":300,"unit":"","css":null}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.
