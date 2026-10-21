"""Render an animation from a validated spec. Static, tested bpy - no
generated code. Only the spec data varies.

Invoked as:
    blender -b --factory-startup --python blender_animate.py -- spec.json outdir

Spec shape (already validated by animate.py):
    {"template": "turntable", "frames": 48, "width": 640, "height": 480,
     "objects": [{"kind": "box", "name": "body", "position": [x,y,z],
                  "size": [x,y,z], "color": [r,g,b]}]}
"""

import json
import math
import sys

import bpy
from mathutils import Vector

TEMPLATES = ("turntable", "orbit", "bounce", "tumble", "assemble")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials):
        for item in list(block):
            block.remove(item)


def add_object(spec):
    kind, size = spec["kind"], spec["size"]
    position = Vector(spec["position"])
    if kind == "box":
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=position)
    elif kind == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=position)
    else:  # cone
        bpy.ops.mesh.primitive_cone_add(radius1=0.5, depth=1, location=position)
    obj = bpy.context.object
    obj.name = spec["name"]
    obj.scale = Vector(size)
    colour = spec.get("color") or [0.6, 0.6, 0.65]
    material = bpy.data.materials.new(f"{spec['name']}_mat")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*colour, 1.0)
        shader.inputs["Roughness"].default_value = 0.45
    obj.data.materials.append(material)
    return obj


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner)
              for obj in objects for corner in obj.bound_box]
    mins = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    maxs = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return mins, maxs, (mins + maxs) / 2, max((maxs - mins).length, 0.5)


def add_floor(centre, mins, extent, color=None):
    bpy.ops.mesh.primitive_plane_add(size=max(extent * 6, 4),
                                     location=(centre.x, centre.y, mins.z - 0.02))
    floor = bpy.context.object
    floor.name = "floor"
    material = bpy.data.materials.new("floor_mat")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*(color or (0.22, 0.24, 0.27)), 1.0)
        shader.inputs["Roughness"].default_value = 0.8
    floor.data.materials.append(material)
    return floor


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_camera(centre, extent):
    bpy.ops.object.camera_add(location=centre + Vector((1.5, -2.2, 1.2)) * extent)
    camera = bpy.context.object
    aim(camera, centre)
    bpy.context.scene.camera = camera
    return camera


def add_lights(centre, extent):
    bpy.ops.object.light_add(type="AREA", location=centre + Vector((-1.0, -1.4, 2.2)) * extent)
    key = bpy.context.object
    key.data.energy = 900 * max(extent, 1)
    key.data.size = extent * 2.5
    aim(key, centre)
    bpy.ops.object.light_add(type="SUN", location=centre + Vector((2.0, 1.5, 2.5)) * extent)
    fill = bpy.context.object
    fill.data.energy = 2.0
    aim(fill, centre)


def pivot_for(objects, centre):
    """Parent every object to one empty, so a template animates the whole
    subject by moving a single transform."""
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=centre)
    pivot = bpy.context.object
    pivot.name = "pivot"
    for obj in objects:
        obj.parent = pivot
        obj.matrix_parent_inverse = pivot.matrix_world.inverted()
    return pivot


def linear(target):
    """Templates read better as constant motion; the default bezier ease
    makes a looping turntable visibly stutter at the seam."""
    if target.animation_data and target.animation_data.action:
        for curve in target.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"


def apply_template(name, pivot, camera, centre, extent, objects, last):
    if name == "turntable":
        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=1)
        pivot.rotation_euler = (0, 0, math.radians(360))
        pivot.keyframe_insert(data_path="rotation_euler", frame=last)
        linear(pivot)
    elif name == "tumble":
        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=1)
        pivot.rotation_euler = (math.radians(360), 0, math.radians(360))
        pivot.keyframe_insert(data_path="rotation_euler", frame=last)
        linear(pivot)
    elif name == "orbit":
        radius = extent * 2.6
        height = centre.z + extent * 1.1
        steps = 8
        for step in range(steps + 1):
            angle = 2 * math.pi * step / steps
            frame = 1 + round((last - 1) * step / steps)
            camera.location = (centre.x + radius * math.cos(angle),
                               centre.y + radius * math.sin(angle), height)
            aim(camera, centre)
            camera.keyframe_insert(data_path="location", frame=frame)
            camera.keyframe_insert(data_path="rotation_euler", frame=frame)
        linear(camera)
    elif name == "bounce":
        lift = extent * 0.8
        base = pivot.location.copy()
        keys = ((1, 0.0), (1 + (last - 1) // 2, lift), (last, 0.0))
        for frame, offset in keys:
            pivot.location = (base.x, base.y, base.z + offset)
            pivot.keyframe_insert(data_path="location", frame=frame)
    elif name == "assemble":
        for index, obj in enumerate(objects):
            final = obj.location.copy()
            angle = 2 * math.pi * index / max(len(objects), 1)
            start = final + Vector((math.cos(angle), math.sin(angle), 1.0)) * extent * 1.8
            obj.location = start
            obj.keyframe_insert(data_path="location", frame=1)
            obj.location = final
            obj.keyframe_insert(data_path="location", frame=max(2, last - 4))


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    spec = json.loads(open(arguments[0], encoding="utf-8").read())
    out_dir = arguments[1]

    template = spec.get("template", "turntable")
    if template not in TEMPLATES:
        template = "turntable"
    frames = int(spec.get("frames", 48))
    last = max(2, frames)

    clear_scene()
    objects = [add_object(item) for item in spec["objects"]]
    mins, maxs, centre, extent = bounds(objects)
    add_floor(centre, mins, extent, spec.get("background"))
    camera = add_camera(centre, extent)
    add_lights(centre, extent)
    pivot = pivot_for(objects, centre)
    apply_template(template, pivot, camera, centre, extent, objects, last)

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = last
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = int(spec.get("width", 640))
    scene.render.resolution_y = int(spec.get("height", 480))
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = f"{out_dir}/frame_"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (*(spec.get("background") or (0.05, 0.06, 0.08)), 1.0)
    bpy.ops.render.render(animation=True)
    print(f"PCSTUDIO_ANIMATED template={template} frames={last} engine={scene.render.engine}")


if __name__ == "__main__":
    main()
