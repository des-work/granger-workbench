"""Executed by Blender, not regular Python, to open a pcstudio OBJ for editing."""

import sys
from pathlib import Path

import bpy


def main():
    path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    if not path.is_file() or path.suffix.lower() != ".obj":
        raise ValueError("Expected an existing OBJ file")
    default_cube = bpy.data.objects.get("Cube")
    if default_cube:
        bpy.data.objects.remove(default_cube, do_unlink=True)
    bpy.ops.wm.obj_import(filepath=str(path), forward_axis="Y", up_axis="Z")
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    found = False
    for device in prefs.devices:
        device.use = device.type == "OPTIX"
        found |= device.use
    if found:
        scene.cycles.device = "GPU"
    print(f"PCSTUDIO_IMPORTED {path} cycles={scene.cycles.device}")


if __name__ == "__main__":
    main()
