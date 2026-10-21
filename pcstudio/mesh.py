"""Small, dependency-free OBJ mesh exporter for editable blockout assets."""

from __future__ import annotations

import math
from pathlib import Path


KINDS = {"box", "sphere", "cylinder", "cone"}


def scene_schema(*, animation=False):
    vector = {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3}
    properties = {"kind": {"type": "string", "enum": sorted(KINDS)}, "name": {"type": "string"},
                  "position": vector, "size": {**vector, "items": {"type": "number", "exclusiveMinimum": 0}}}
    if animation:
        properties["color"] = {**vector, "items": {"type": "number", "minimum": 0, "maximum": 1}}
    item = {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
    schema = {"type": "object", "properties": {"objects": {"type": "array", "items": item, "minItems": 1, "maxItems": 24 if animation else 64}},
              "required": ["objects"], "additionalProperties": False}
    if animation:
        schema["properties"]["template"] = {"type": "string", "enum": ["turntable", "orbit", "bounce", "tumble", "assemble"]}
        schema["required"].append("template")
    return schema


def validate_scene(scene: dict) -> list[dict]:
    if not isinstance(scene, dict) or not isinstance(scene.get("objects"), list):
        raise ValueError("Scene must contain an objects list")
    objects = scene["objects"]
    if not 1 <= len(objects) <= 64:
        raise ValueError("Scene needs 1 to 64 objects")
    clean = []
    for number, obj in enumerate(objects, 1):
        if not isinstance(obj, dict) or obj.get("kind") not in KINDS:
            raise ValueError(f"Object {number} needs kind box, sphere, cylinder, or cone")
        name = str(obj.get("name", f"object_{number}"))[:64]
        name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name) or f"object_{number}"
        position = obj.get("position", [0, 0, 0])
        size = obj.get("size", [1, 1, 1])
        if not isinstance(position, list) or not isinstance(size, list) or len(position) != 3 or len(size) != 3:
            raise ValueError(f"Object {number} needs three-element position and size lists")
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) or abs(x) > 1000 for x in position):
            raise ValueError(f"Object {number} has an invalid position")
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0 or x > 1000 for x in size):
            raise ValueError(f"Object {number} has an invalid size")
        clean.append({"kind": obj["kind"], "name": name, "position": position, "size": size})
    return clean


def _shape(kind: str):
    if kind == "box":
        vertices = [(x, y, z) for z in (-.5, .5) for y in (-.5, .5) for x in (-.5, .5)]
        faces = [(1, 2, 4, 3), (5, 7, 8, 6), (1, 5, 6, 2),
                 (3, 4, 8, 7), (1, 3, 7, 5), (2, 6, 8, 4)]
        return vertices, faces
    segments = 16
    if kind == "sphere":
        rings = 8
        vertices = [(0, 0, -.5)]
        for ring in range(1, rings):
            phi = -math.pi / 2 + math.pi * ring / rings
            vertices += [(.5 * math.cos(phi) * math.cos(2 * math.pi * i / segments),
                          .5 * math.cos(phi) * math.sin(2 * math.pi * i / segments),
                          .5 * math.sin(phi)) for i in range(segments)]
        vertices.append((0, 0, .5))
        faces = [tuple([1, 2 + i, 2 + (i + 1) % segments]) for i in range(segments)]
        for ring in range(rings - 2):
            a = 2 + ring * segments
            b = a + segments
            faces += [(a + i, b + i, b + (i + 1) % segments, a + (i + 1) % segments)
                      for i in range(segments)]
        top = len(vertices)
        faces += [(top, 2 + (rings - 2) * segments + (i + 1) % segments,
                   2 + (rings - 2) * segments + i) for i in range(segments)]
        return vertices, faces
    bottom = [(.5 * math.cos(2 * math.pi * i / segments),
               .5 * math.sin(2 * math.pi * i / segments), -.5) for i in range(segments)]
    if kind == "cone":
        return bottom + [(0, 0, .5)], [tuple(range(segments, 0, -1))] + [
            (i + 1, (i + 1) % segments + 1, segments + 1) for i in range(segments)]
    top = [(x, y, .5) for x, y, _ in bottom]
    return bottom + top, [tuple(range(segments, 0, -1)),
                          tuple(range(segments + 1, 2 * segments + 1))] + [
        (i + 1, (i + 1) % segments + 1, (i + 1) % segments + 1 + segments, i + 1 + segments)
        for i in range(segments)]


def write_obj(scene: dict, destination: Path) -> Path:
    objects = validate_scene(scene)
    destination = Path(destination)
    lines = ["# pcstudio editable blockout mesh"]
    offset = 0
    for obj in objects:
        vertices, faces = _shape(obj["kind"])
        lines.append(f"o {obj['name']}")
        for vertex in vertices:
            values = [vertex[i] * obj["size"][i] + obj["position"][i] for i in range(3)]
            lines.append("v " + " ".join(f"{value:.6f}" for value in values))
        for face in faces:
            lines.append("f " + " ".join(str(index + offset) for index in face))
        offset += len(vertices)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
