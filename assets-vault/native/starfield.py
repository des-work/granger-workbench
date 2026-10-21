"""starfield — Deep-space backdrop (as shipped in the Ultra Archive): accent-tinted nebula + glowing stars, themed by style.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
space = nui.starfield(1200, 780, "golden-archive")   # or cyberpunk, nordic…
# tile two of these and scroll them slowly for a parallax hall
