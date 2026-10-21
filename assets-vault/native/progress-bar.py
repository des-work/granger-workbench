"""progress-bar — Profile-aware progress bar; bounded .set(0..1), visible small values, optional gloss.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
bar = nui.ProgressBar(parent, width=280, height=14, style="frutiger-aero")
bar.pack(); bar.set(0.66)
