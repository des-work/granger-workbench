"""status-dot — Glowing status light: ok / warn / err / off — with .set_state() for live dashboards.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
dot = nui.StatusDot(parent, "ok", style="frutiger-aero"); dot.pack()
dot.set_state("warn")   # ok=accent2 · warn=amber · err=red · off=muted
