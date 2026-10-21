"""splash — Animated landing overlay: glass title card + gradient loading bar + rising bubbles, then reveals the app.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
# after building your window, before mainloop:
root.after(150, lambda: nui.run_splash(
    root, on_done=lambda: entry.focus_set(),
    title="My App", subtitle="offline · local", style="frutiger-aero"))
root.mainloop()
