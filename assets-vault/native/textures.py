"""textures — Ten themed backdrop textures — grain, brushed metal, carbon weave, CRT scanlines, halftone, diagonal stripes, mesh gradient, starfield, paper — one dispatcher, any style.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
# kinds: nui.TEXTURES = grain brushed carbon scanlines halftone stripes mesh starfield paper
img = nui.texture("scanlines", 900, 620, "cyberpunk")
img = nui.vignette(img, 0.3)                      # optional edge-darken finisher
bg = nui.ImageTk.PhotoImage(img)
tk.Label(root, image=bg, bd=0).place(x=0, y=0)    # keep the reference!
