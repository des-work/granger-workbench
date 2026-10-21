"""themed-window — A complete themed desktop window (header + glass card + gel button + landing splash), style-swappable.  [native/tkinter · module: ultrapc/nativeui.py]"""
import tkinter as tk
from ultrapc import nativeui as nui      # self-contained; copy this file into your project

STYLE = "frutiger-aero"                   # or cyberpunk, pastel, mono, nordic, ...
t = nui.tokens(STYLE)

root = tk.Tk(); root.geometry("860x600"); root.configure(bg=t["bg"])
bg = tk.Label(root, bd=0); bg.place(x=0, y=0, relwidth=1, relheight=1)
_scene = nui.ImageTk.PhotoImage(nui.scene(860, 600, STYLE)); bg.configure(image=_scene)

hdr = nui.HeaderBar(root, style=STYLE); hdr.pack(fill="x")
card = nui.Card(root, style=STYLE, accent=(nui._rgb(t["accent2"]), nui._rgb(t["accent"])))
card.pack(fill="both", expand=True, padx=24, pady=20)
tk.Label(card.body, text="Hello", bg=t["surface"], fg=t["text"],
         font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=16)
nui.GelButton(card.body, "Go", lambda: None, style=STYLE, bg=t["surface"]).pack(padx=16)

root.after(150, lambda: nui.run_splash(root, on_done=lambda: None,
                                       title="My App", subtitle="offline", style=STYLE))
root.mainloop()
