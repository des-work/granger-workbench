# command-menu

A searchable command dialog with arrow keys, Enter, Escape and a scoped ⌘/Ctrl-K shortcut.

Category: interaction · Cost: low · Default profile: ultraviolet
Flags: none

Load `web/core.css`, `web/runtime.js`, and `web/effects/command-menu.css` / `.js`.
Use `web/snippets/command-menu.html` as the markup. Preview: `web/demos/command-menu/index.html`.
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
