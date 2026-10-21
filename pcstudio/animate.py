"""Text to a rendered Blender animation, headless.

The model never writes code. It picks a motion template and describes the
subject as primitives; `blender_animate.py` - static, tested bpy - does the
building and rendering. Generated bpy was tried first and produced
confident nonsense (`light_add(type="SONE")`, keyframes past frame_end), so
the only thing crossing the model boundary here is validated data.

Object validation is shared with `pc make` (mesh.validate_scene), and the
primitive vocabulary is the same: box, sphere, cylinder, cone.

The bpy in `blender_animate.py` came from the local `blender-mcp` Hermes
skill's reference (keyframe_insert, frame_start/end, render(animation=True)).
That skill is where the idioms were learned - it is NOT a runtime dependency,
and this does not use its MCP transport: blender-mcp drives a live Blender
through an addon needing "Connect to Claude" clicked in the viewport every
session, which no voice assistant can ask for mid-sentence.

EEVEE, not Cycles: a 48-frame Cycles sequence is minutes of GPU time, EEVEE
renders these in about 0.1s a frame. Stills stay on Cycles/OptiX
(blender_render.py).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import cli
from .mesh import validate_scene, scene_schema

TEMPLATES = {
    "turntable": "the whole subject spins once around its vertical axis",
    "orbit": "the subject stays still and the camera circles it",
    "bounce": "the subject rises and settles back down",
    "tumble": "the subject rolls end over end",
    "assemble": "the parts fly in from outside and settle into place",
}

ANIMATE_SCRIPT = Path(__file__).with_name("blender_animate.py")

PROMPT = """Describe a short 3D animation of: {subject}

Return only JSON shaped like:
{{"template": "turntable",
  "objects": [{{"kind": "box", "name": "body", "position": [0,0,0.4],
                "size": [1.2,0.8,0.5], "color": [0.8,0.15,0.15]}}]}}

Pick "template" from exactly these, choosing the motion that best suits the
subject:
{templates}

Rules for objects:
- kind must be box, sphere, cylinder, or cone. 1 to 24 objects.
- Build the subject from separate parts. A rocket is a cone nose on a
  cylinder body with fins; don't collapse it into one shape.
- position [x,y,z] and size [x,y,z] are metres. Z is UP.
- position is the CENTRE of the part. A part centred at z with height
  size[2] spans z - size[2]/2 to z + size[2]/2. Stack parts by that maths so
  they actually touch: a 1.0-tall body centred at z=0.5 ends at z=1.0, so a
  0.4-tall nose on top is centred at z=1.2. Floating gaps look broken.
- Upright things are tall in Z: a rocket body is size [0.4,0.4,1.6], NOT
  [0.4,1.6,0.4]. Flat surfaces are small in Z, like a tabletop [1.6,0.8,0.08].
- The subject sits on the ground: its lowest part starts at z=0.
- color is [r,g,b], each 0 to 1.
- No extra fields, no commentary, no markdown.

Worked example - a rocket on a pad, parts touching, tall in Z:
{{"template": "turntable", "objects": [
  {{"kind":"cylinder","name":"pad","position":[0,0,0.05],"size":[1.4,1.4,0.1],"color":[0.3,0.3,0.32]}},
  {{"kind":"cylinder","name":"body","position":[0,0,0.9],"size":[0.5,0.5,1.6],"color":[0.9,0.9,0.92]}},
  {{"kind":"cone","name":"nose","position":[0,0,1.9],"size":[0.5,0.5,0.4],"color":[0.85,0.2,0.2]}},
  {{"kind":"box","name":"fin_a","position":[0.3,0,0.3],"size":[0.25,0.06,0.4],"color":[0.85,0.2,0.2]}},
  {{"kind":"box","name":"fin_b","position":[-0.3,0,0.3],"size":[0.25,0.06,0.4],"color":[0.85,0.2,0.2]}}
]}}"""


def plan(subject: str, *, model: str) -> dict:
    """Ask for a template + parts, then validate hard. Anything the model
    gets wrong is corrected or rejected here rather than reaching Blender."""
    raw = cli.ask_ollama(
        PROMPT.format(subject=subject,
                      templates="\n".join(f"  {k} - {v}" for k, v in TEMPLATES.items())),
        model=model, json_output=scene_schema(animation=True))
    if not raw:
        raise RuntimeError("the model returned nothing")
    spec = json.loads(raw)
    template = spec.get("template")
    if template not in TEMPLATES:
        template = "turntable"
    objects = validate_scene(spec)  # raises on anything malformed
    for clean, original in zip(objects, spec["objects"]):
        colour = original.get("color")
        if (isinstance(colour, list) and len(colour) == 3
                and all(isinstance(c, (int, float)) for c in colour)):
            clean["color"] = [min(1.0, max(0.0, float(c))) for c in colour]
    return {"template": template, "objects": objects}


def render(spec: dict, out_dir: Path, *, frames: int, width: int, height: int,
           timeout: int = 900) -> subprocess.CompletedProcess:
    blender = (str(cli.PORTABLE_BLENDER) if cli.PORTABLE_BLENDER.is_file()
               else shutil.which("blender"))
    if not blender:
        raise RuntimeError("Blender is not available")
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    spec_path = out_dir / "spec.json"
    spec_path.write_text(json.dumps({**spec, "frames": frames,
                                     "width": width, "height": height},
                                    indent=2) + "\n", encoding="utf-8")
    return subprocess.run(
        [blender, "-b", "--factory-startup", "--python", str(ANIMATE_SCRIPT),
         "--", str(spec_path), str(frames_dir)],
        text=True, capture_output=True, timeout=timeout)


def encode(frames_dir: Path, video: Path, fps: int = 24) -> bool:
    """Frames to mp4. False when nothing rendered, so the caller can say so
    rather than point at a video that isn't there."""
    if not sorted(frames_dir.glob("frame_*.png")):
        return False
    done = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps),
         "-pattern_type", "glob", "-i", str(frames_dir / "frame_*.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
        text=True, capture_output=True, timeout=600)
    return done.returncode == 0 and video.is_file()


def build(subject: str, *, model: str, out_dir: Path, frames: int = 48,
          width: int = 640, height: int = 480, fps: int = 24, template: str | None = None,
          palette: dict | None = None) -> dict:
    """Plan, render, encode. The returned report always names the spec, so a
    failed render is still inspectable and re-runnable by hand."""
    if template is not None and template not in TEMPLATES:
        raise ValueError("Unknown animation template")
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = plan(subject, model=model)
    if template is not None:
        spec["template"] = template
    if palette:
        def rgb(key):
            color = palette[key]
            if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise ValueError("Vault palette colors must be six-digit hex values")
            return [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        colors = [rgb("text"), rgb("accent")]
        spec["background"] = rgb("bg")
        for i, obj in enumerate(spec["objects"]):
            obj["color"] = spec["background"] if "pad" in obj["name"].lower() else colors[i % 2]
    result = render(spec, out_dir, frames=frames, width=width, height=height)
    frames_dir = out_dir / "frames"
    rendered = len(sorted(frames_dir.glob("frame_*.png")))
    video = out_dir / "animation.mp4"
    ok = encode(frames_dir, video, fps=fps) if result.returncode == 0 and rendered == frames else False
    report = {"subject": subject, "template": spec["template"],
              "parts": len(spec["objects"]), "spec": str(out_dir / "spec.json"),
              "frames_rendered": rendered, "video": str(video) if ok else None}
    if not ok:
        tail = (result.stderr or result.stdout or "").strip().splitlines()[-8:]
        report["error"] = (f"Rendered {rendered}/{frames} frames; Blender exit {result.returncode}; video not confirmed. "
                           + ("\n".join(tail) if result.returncode else "Check frame count and video encoder."))
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    return report
