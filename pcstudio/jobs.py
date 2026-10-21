"""Bounded local builders with persistent, verifiable job results. No shell commands."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
from .config import ULTRA_ROOT, BUILD_MODEL

ROOT = Path(__file__).resolve().parents[1]
JOBS = Path(os.environ.get("PCSTUDIO_JOBS", ROOT / "output/pcstudio/jobs"))
TERMSTAGE = Path(os.environ.get("PCSTUDIO_TERMSTAGE_ROOT", ROOT / "optional/termstage"))
MODEL = BUILD_MODEL
KINDS = ("model", "animation", "terminal-animation")


def _write(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def _alive(pid):
    try:
        os.kill(int(pid), 0)
        # A crashed child can remain a zombie until its parent reaps it.
        stat = Path(f"/proc/{pid}/stat")
        return not (stat.exists() and stat.read_text().rsplit(") ", 1)[1].startswith("Z"))
    except (OSError, ValueError, TypeError):
        return False


def _design(subject, kind):
    script = ULTRA_ROOT / "integrations/design_assets.py"
    result = subprocess.run([sys.executable, "-B", str(script), "--context", subject],
                            capture_output=True, text=True, timeout=12)
    context = json.loads(result.stdout)
    if result.returncode or context.get("status") != "ok" or not context.get("styles"):
        raise RuntimeError("Ultra-PC vault unavailable; ask before selecting an outside aesthetic")
    if kind == "terminal-animation" and context.get("selection") != "named_profiles":
        result = subprocess.run([sys.executable, "-B", str(script), "--context", "style/mono"],
                                capture_output=True, text=True, timeout=12)
        context = json.loads(result.stdout)
        if result.returncode or context.get("status") != "ok" or not context.get("styles"):
            raise RuntimeError("Ultra-PC terminal profile unavailable")
    # Keep only compact references, never implementation code. Existing Termstage
    # assets retain their palette/art; this directs new artwork rather than rebranding.
    style = context["styles"][0]
    return {k: style[k] for k in ("style", "profile", "palette", "tokens", "art", "colors", "rules") if k in style}


def status(job_id):
    if not re.fullmatch(r"[0-9a-f]{32}", str(job_id)):
        raise ValueError("Use the job_id returned by pc_build")
    path = JOBS / job_id / "job.json"
    result = json.loads(path.read_text())
    if result["status"] == "queued" and not result.get("pid") and (datetime.now(timezone.utc) - datetime.fromisoformat(result["created"])).total_seconds() > 30:
        result = {**result, "status": "failed", "error": "Build launch was interrupted before a worker was recorded."}
    if result["status"] in ("queued", "running") and result.get("pid") and not _alive(result["pid"]):
        # Worker may have atomically published its final result after our first read.
        result = json.loads(path.read_text())
        if result["status"] in ("queued", "running"):
            result = {**result, "status": "failed", "error": "Builder exited before confirming completion; inspect the job log."}
    # Always check the artifacts again; a missing file cannot be reported as built.
    if result["status"] == "complete" and not all(Path(p).is_file() and Path(p).stat().st_size for p in result.get("artifacts", [])):
        result = {**result, "status": "failed", "error": "A recorded output file is missing or empty."}
    if result["status"] == "failed":
        log = path.with_name("build.log")
        result["log_tail"] = log.read_text(errors="replace")[-2000:] if log.exists() else ""
    return result


def start(kind, subject, *, template=None, frames=48, width=640, height=480, fps=24):
    subject = str(subject).strip()
    if kind not in KINDS:
        raise ValueError("Choose model, animation (3D MP4), or terminal-animation (Termstage)")
    if not 2 <= len(subject) <= 2000:
        raise ValueError("Describe what the result should show (2 to 2000 characters)")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (frames, width, height, fps)):
        raise ValueError("Frame count, size and fps must be integers")
    if not (2 <= frames <= 240 and 128 <= width <= 1280 and 128 <= height <= 1280 and 1 <= fps <= 60) or width % 2 or height % 2:
        raise ValueError("Use 2–240 frames, even dimensions 128–1280, and 1–60 fps")
    if template is not None and template not in ("turntable", "orbit", "bounce", "tumble", "assemble"):
        raise ValueError("Unknown animation template")
    design = _design(subject, kind)
    JOBS.mkdir(parents=True, exist_ok=True)
    with (JOBS / ".start.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for path in JOBS.glob("*/job.json"):
            previous = status(path.parent.name)
            if previous["status"] in ("queued", "running"):
                return {"status": "busy", "job_id": previous["job_id"], "message": "A local build is already running. Check pc_job before starting another."}
        job_id = uuid.uuid4().hex
        folder = JOBS / job_id
        folder.mkdir()
        result = {"job_id": job_id, "status": "queued", "kind": kind, "subject": subject,
                  "created": datetime.now(timezone.utc).isoformat(), "model": MODEL,
                  "design": design,
                  "options": dict(template=template, frames=frames, width=width, height=height, fps=fps),
                  "directory": str(folder), "artifacts": []}
        _write(folder / "job.json", result)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        env["PCSTUDIO_JOBS"] = str(JOBS)
        try:
            with (folder / "build.log").open("w") as log:
                process = subprocess.Popen([sys.executable, "-B", "-m", "pcstudio.jobs", "--run", job_id],
                                           env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                           start_new_session=True, cwd=ROOT)
            result["pid"] = process.pid
            # Parent publishes PID before releasing the worker's file lock.
            _write(folder / "job.json", result)
        except OSError as exc:
            result.update(status="failed", error=str(exc))
            _write(folder / "job.json", result)
        return result


def run(job_id):
    from . import cli, animate
    path = JOBS / job_id / "job.json"
    with (JOBS / ".start.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        job = json.loads(path.read_text())
        job.update(status="running", pid=os.getpid())
        _write(path, job)
    folder = path.parent
    try:
        design_path = folder / "design-context.json"
        _write(design_path, job["design"])
        subject = (job["subject"] + "\nLocal Ultra-PC visual references: " + json.dumps(job["design"], separators=(",", ":"))
                   + ". Use these aesthetic references for new art. Preserve existing Termstage asset identity, "
                   "the requested subject and requested animation; do not add UI text, frames or borders.")
        if job["kind"] == "model":
            mesh = folder / "model.obj"
            cli.model_command(argparse.Namespace(scene=None, prompt=subject, image=None, model=MODEL, output=mesh))
            # The mesh is useful even when the optional GPU preview is unavailable.
            artifacts = [str(mesh), str(mesh.with_suffix(".json"))]
            try:
                preview = folder / "preview.png"
                cli.render3d_command(argparse.Namespace(mesh=mesh, output=preview))
                artifacts.append(str(preview))
            except Exception as exc:
                job["preview_error"] = str(exc)
            job["limitation"] = "Editable primitive blockout; not a sculpted mesh or photogrammetry."
        elif job["kind"] == "animation":
            report = animate.build(subject, model=MODEL, out_dir=folder, palette=job["design"].get("colors"), **job["options"])
            if report.get("error") or not report.get("video"):
                raise RuntimeError(report.get("error", "Animation produced no video"))
            artifacts = [report["video"], report["spec"], str(folder / "report.json")]
            job["limitation"] = "Primitive 3D scene using a supported motion template."
        else:
            if str(TERMSTAGE) not in sys.path:
                sys.path.insert(0, str(TERMSTAGE))
            from termstage.ai import generate
            from termstage.scene import save_scene
            from termstage.cli import export_player
            terminal_design = {k: v for k, v in job["design"].items() if k not in ("colors", "rules")}
            terminal_subject = (job["subject"] + "\nLocal Ultra-PC profile references: " + json.dumps(terminal_design)
                                + ". Preserve existing library artwork and colors. Use only terminal color names "
                                "default, black, red, green, yellow, blue, magenta, cyan, white. No hex colors. "
                                "Effects must be none, reveal or blink. Keep a short, simple animated scene.")
            from .terminal_build import library_scene, UnsupportedSubject
            try:
                scene = library_scene(job["subject"], MODEL, job["design"], plan_path=folder / "direction.json")
                job["builder"] = "Termstage local library composition"
            except UnsupportedSubject:
                scene = generate(terminal_subject, model=MODEL, timeout=180)
                job["builder"] = "Termstage local custom artwork generation"
            target = folder / "scene.json"
            save_scene(scene, target)
            player = folder / "animation.pyz"
            export_player(scene, player)
            artifacts = [str(target), str(player)]
            job["limitation"] = "Animated terminal art with a portable player; not a video file."
        artifacts.append(str(design_path))
        if not all(Path(p).is_file() and Path(p).stat().st_size for p in artifacts):
            raise RuntimeError("Builder did not produce every required output")
        job.update(status="complete", artifacts=artifacts)
    except BaseException as exc:
        job.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    job["finished"] = datetime.now(timezone.utc).isoformat()
    _write(path, job)


def intent(heard):
    match = re.match(r"^(?:(?:can|could|would|will) you\s+|let'?s\s+)?(?:please\s+)?(?:make|create|build|generate|render)\s+(?:me\s+)?(?:(?:a|an|some)\s+)?((?:(?:simple|rough|editable|short|3d|2d|terminal|blender)\s+)*)(model|animation|scene|art)\b(.*)", heard.strip(), re.I)
    if not match:
        return None
    modifiers, noun, rest = (s.lower() if i < 2 else s for i, s in enumerate(match.groups()))
    if noun == "model" and not re.search(r"\b3d\b", modifiers) and re.search(r"\b(classify|predict|train|training|dataset|regression|neural|machine learning|language)\b", rest, re.I):
        return None
    kind = "model" if noun == "model" else "animation" if re.search(r"\b(3d|blender)\b", modifiers + " " + rest, re.I) else "terminal-animation"
    rest = re.sub(r"\s+in\s+(?:blender|term\s*stage)\s*[.!?]*$", "", rest, flags=re.I)
    rest = re.sub(r"^\s*(?:of|about|for|showing)\s+", "", rest, flags=re.I).strip(" .!?")
    return {"kind": kind, "subject": rest}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    run(p.parse_args().run)
