"""header-bar — Profile-aware title bar: matte for flat styles, polished where allowed, bubbles for Aero.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
hdr = nui.HeaderBar(root, height=56, style="cyberpunk")
hdr.pack(fill="x", side="top")
hdr.bind("<Configure>", lambda e: (hdr._redraw(e),
    hdr.create_text(20, 28, anchor="w", text="My App", fill="white",
                    font=("Segoe UI", 15, "bold"))), add="+")
