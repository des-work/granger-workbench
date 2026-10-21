# shared-transition

Shared-element transitions between two real content states, with immediate fallback.

Category: motion · Cost: low · Default profile: ultraviolet
Flags: motion

Load `web/core.css`, `web/runtime.js`, and `web/effects/shared-transition.css` / `.js`.
Use `web/snippets/shared-transition.html` as the markup. Preview: `web/demos/shared-transition/index.html`.
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

Implementation references: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using
