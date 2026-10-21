"""Portable Blender preview renderer for pcstudio OBJ assets."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    source, destination = map(lambda value: Path(value).resolve(), arguments[:2])
    if not source.is_file() or source.suffix.lower() != ".obj":
        raise ValueError("Expected an existing OBJ file")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.wm.obj_import(filepath=str(source), forward_axis="Y", up_axis="Z")
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not objects:
        raise ValueError("OBJ contained no mesh objects")

    wood = bpy.data.materials.new("Warm wood")
    wood.diffuse_color = (0.44, 0.24, 0.12, 1)
    wood.use_nodes = True
    wood.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = wood.diffuse_color
    for obj in objects:
        obj.data.materials.clear()
        obj.data.materials.append(wood)
        bevel = obj.modifiers.new("Soft edges", "BEVEL")
        bevel.width = 0.01
        bevel.segments = 2

    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    mins = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    maxs = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (mins + maxs) / 2
    extent = max((maxs - mins).length, 0.5)

    bpy.ops.mesh.primitive_plane_add(size=max(extent * 5, 4), location=(center.x, center.y, mins.z - .025))
    floor = bpy.context.object
    floor.name = "Preview floor"
    mat = bpy.data.materials.new("Backdrop")
    mat.diffuse_color = (0.72, 0.77, 0.79, 1)
    floor.data.materials.append(mat)

    bpy.ops.object.camera_add(location=center + Vector((1.25, -1.65, .95)) * extent)
    camera = bpy.context.object
    direction = center - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = extent * 1.65
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=center + Vector((-.7, -1.1, 1.9)) * extent)
    light = bpy.context.object
    light.data.energy = 700 * extent
    light.data.shape = "DISK"
    light.data.size = extent * 2
    light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    preferences = bpy.context.preferences.addons["cycles"].preferences
    preferences.compute_device_type = "OPTIX"
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type == "OPTIX"
    if any(device.use for device in preferences.devices):
        scene.cycles.device = "GPU"
    scene.cycles.samples = 24
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(destination)
    scene.world.color = (0.38, 0.38, 0.38)
    bpy.ops.render.render(write_still=True)
    print(f"PCSTUDIO_RENDERED {destination} device={scene.cycles.device}")


if __name__ == "__main__":
    main()
