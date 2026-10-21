"""toggle-switch — Keyboard-accessible on/off switch with the profile's material and corner treatment.  [native/tkinter · module: ultrapc/nativeui.py]"""
from ultrapc import nativeui as nui
sw = nui.Toggle(parent, on=True, command=lambda on: print(on),
                style="frutiger-aero")
sw.pack()
