"""gel-button — Filled action button with profile-specific material, corners, typography and enabled states.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
btn = nui.GelButton(parent, "Ask ▸", on_click, width=120, height=44,
                    style="frutiger-aero")
btn.pack()
btn.set_text("…"); btn.set_enabled(False)   # while busy
