# glass-stack

Three offset translucent sheets with one live blur layer to bound rendering cost.

Category: transparency · Cost: medium · Default profile: ultraviolet
Flags: glass

Load `web/core.css`, `web/runtime.js`, and `web/effects/glass-stack.css` / `.js`.
Use `web/snippets/glass-stack.html` as the markup. Preview: `web/demos/glass-stack/index.html`.
All visual tokens come from the chosen vault profile. `data-uv-config` accepts:

```json
{
  "opacity": 0.8,
  "blur": 20
}
```

Bounds: {"opacity":{"default":0.8,"min":0.56,"max":0.98,"unit":"","css":"--uv-alpha"},"blur":{"default":20,"min":0,"max":32,"unit":"px","css":"--uv-blur"}}
Fallback: Static, readable content remains available.
The runtime mounts once per element, cleans listeners/observers on unmount, and
pauses continuous JS work off screen or when the page is hidden. Reduced motion
keeps content visible. Read this recipe only when tuning the asset; use its ID
and file paths in cloud prompts.

Implementation references: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/backdrop-filter
