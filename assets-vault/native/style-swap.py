"""style-swap — Re-theme the whole native UI by changing one string — every generator reads the style's tokens.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
# styles: frutiger-aero · cyberpunk · golden-archive · pastel · mono · nordic · …
for style in ("frutiger-aero", "cyberpunk", "golden-archive"):
    nui.preview(style, f"look-{style}.png")   # static PNG look-preview, no GUI
# in a live app just pass style= to Card / GelButton / HeaderBar / run_splash
