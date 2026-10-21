"""divider-ramp — Fading accent divider + color utilities: ramp() tint→shade scales and harmony() complement/analogous/triadic — stop hand-picking 'a lighter accent'.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
nui.Divider(parent, width=320, style="jewel").pack(fill="x", pady=8)
shades = nui.ramp("#d4af37", 7)          # ['#f6ecd1', …, '#241d09']
mates = nui.harmony("#d4af37")           # complement / analogous / triadic
