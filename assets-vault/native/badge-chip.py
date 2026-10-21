"""badge-chip — Pill badges/chips in four kinds: accent, accent2, outline, surface.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
for kind in ("accent", "accent2", "outline", "surface"):
    nui.Chip(parent, "beta", style="nordic", kind=kind).pack(side="left", padx=4)
