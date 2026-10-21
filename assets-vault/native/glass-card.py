"""glass-card — Glass panel with drop shadow + gradient surface + sheen. Pack content into `card.body`.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
card = nui.Card(parent, style="frutiger-aero", radius=18, pad=14,
                accent=(nui._rgb("#96cd6e"), nui._rgb("#2b8fd6")))  # accent optional
card.pack(fill="both", expand=True, padx=20, pady=16)
# put widgets inside card.body (its bg matches the style surface):
tk.Label(card.body, text="…", bg=nui.tokens("frutiger-aero")["surface"]).pack()
