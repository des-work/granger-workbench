"""contrast-tools — WCAG contrast math for native UIs: measure ratios, pick readable ink, auto-fix a color until it passes — check, don't guess.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
nui.contrast("#77809a", "#04070f")        # -> ratio 1..21 (AA body 4.5, AAA 7)
nui.on_color("#d9b453")                    # -> '#000000' or '#ffffff' (best ink)
safe = nui.ensure_contrast("#8a70ff", "#150e2e", ratio=4.5)  # nudged until it passes
# every vault style is smoke-tested to: text/bg >= 4.5, accent/bg + muted/bg >= 3.0
