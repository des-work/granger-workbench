"""Compact direction of real Termstage artwork; keep sprite code out of prompts."""
import json
import math
from pathlib import Path


class UnsupportedSubject(ValueError):
    pass


def library_scene(subject, model, design, plan_path=None):
    from termstage import ai
    from termstage.library import asset_layer, prompt_catalog
    from termstage.scene import validate_scene
    from . import cli

    catalog = prompt_catalog(subject, limit=16)
    names = [line.split(" (", 1)[0] for line in catalog.splitlines()]
    if not names:
        raise ValueError("No local terminal artwork is available")
    number = {"type": "number", "minimum": 0, "maximum": 1}
    layer_schema = {
            "type": "object", "additionalProperties": False,
            "properties": {"asset": {"type": "string", "enum": names}, "x": number, "y": number,
                           "motion": {"type": "string", "enum": ["still", "left", "right", "up", "down", "bounce"]}},
            "required": ["asset", "x", "y", "motion"]}
    moving_subject = {**layer_schema, "properties": {**layer_schema["properties"],
                       "motion": {"type": "string", "enum": ["left", "right", "up", "down", "bounce"]}}}
    schema = {"type": "object", "additionalProperties": False, "required": ["supported", "subject", "background"], "properties": {
        "supported": {"type": "boolean"}, "subject": moving_subject,
        "background": {"type": "array", "minItems": 0, "maxItems": 5, "items": layer_schema}}}
    prompt = ("Direct a short animated terminal scene using only these actual local assets. "
              "Return JSON with a moving subject and 0-3 background layers. x,y are normalized positions from 0 to 1. "
              "The subject is the main thing the user asks to animate; background elements support it. Do not add captions, borders or filler. "
              "Preserve each asset's original art and colors. If these assets cannot depict the main requested subject, "
              "return supported=false; do not substitute a different subject. Otherwise supported=true. Local vault profile: " + design["style"]
              + ". Request: " + subject + "\nAsset catalog:\n" + catalog)
    plan = json.loads(cli.ask_ollama(prompt, model=model, json_output=schema))
    if plan_path:
        Path(plan_path).write_text(json.dumps(plan, indent=2) + "\n")
    if plan.get("supported") is not True:
        raise UnsupportedSubject("The local artwork library cannot depict the requested subject")
    layers = []
    for i, item in enumerate(plan["background"] + [plan["subject"]]):
        if item.get("asset") not in names or len(layers) >= 6:
            raise ValueError("The director selected an unavailable local asset")
        for coordinate in ("x", "y"):
            value = item.get(coordinate)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Invalid normalized artwork placement")
        layer = asset_layer(item["asset"], f"layer-{i+1}")
        w = max(len(row) for frame in layer["frames"] for row in frame)
        h = max(map(len, layer["frames"]))
        xmax, ymax = max(0, 80-w), max(0, 24-h)
        x, y = round(item["x"] * xmax), round(item["y"] * ymax)
        layer.update(x=x, y=y, parallax=1)
        motion = item["motion"]
        dx, dy = {"still": (0,0), "left": (-16,0), "right": (16,0), "up": (0,-4), "down": (0,4), "bounce": (0,-4)}[motion]
        if motion != "still":
            # Travel toward available space when the requested direction starts
            # against an edge. Motion always keeps at least part of the asset visible.
            if dx and not 0 <= x+dx <= xmax: x = max(0, min(xmax, x-dx))
            if dy and not 0 <= y+dy <= ymax: y = max(0, min(ymax, y-dy))
            tx, ty = max(0,min(xmax,x+dx)), max(0,min(ymax,y+dy))
            layer.update(x=x,y=y,motion=[dict(time=0,x=x,y=y),dict(time=2 if motion=='bounce' else 4,x=tx,y=ty)])
            if motion == "bounce":layer["motion"].append(dict(time=4,x=x,y=y))
        layers.append(layer)
    scene = validate_scene(dict(version=2, name=subject[:100], width=80, height=24,
                                duration=4, fps=20, mode="inline", loop=True, layers=layers))
    if not any(layer["motion"] or len(layer["frames"]) > 1 for layer in scene["layers"]):
        raise ValueError("The director returned a static scene instead of animation")
    return ai.check_draft(scene)
