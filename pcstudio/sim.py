"""Monte Carlo simulation engine for pcstudio. Stdlib-only; numpy optional for speed."""

from __future__ import annotations
from .config import BUILD_MODEL, OLLAMA_BASE

import json
import math
import random
import statistics
from typing import Callable


# ── core runner ───────────────────────────────────────────────────────────────

def run(sample_fn: Callable[[], float], trials: int = 10_000) -> dict:
    """Run sample_fn() `trials` times and return summary statistics."""
    try:
        import numpy as np
        results = [sample_fn() for _ in range(trials)]
        arr = np.array(results, dtype=float)
        return {
            "trials": trials,
            "mean": float(arr.mean()),
            "stdev": float(arr.std(ddof=1)),
            "min": float(arr.min()),
            "max": float(arr.max()),
            "median": float(np.median(arr)),
            "p5": float(np.percentile(arr, 5)),
            "p95": float(np.percentile(arr, 95)),
        }
    except ImportError:
        results = [sample_fn() for _ in range(trials)]
        s = sorted(results)
        return {
            "trials": trials,
            "mean": statistics.mean(results),
            "stdev": statistics.stdev(results) if trials > 1 else 0.0,
            "min": s[0],
            "max": s[-1],
            "median": statistics.median(results),
            "p5": s[max(0, int(trials * 0.05))],
            "p95": s[min(trials - 1, int(trials * 0.95))],
        }


# ── built-in simulations ───────────────────────────────────────────────────────

def estimate_pi(trials: int = 100_000) -> dict:
    """Estimate π by sampling random points in the unit square."""
    inside = sum(1 for _ in range(trials)
                 if random.random() ** 2 + random.random() ** 2 <= 1.0)
    estimate = 4 * inside / trials
    err = abs(estimate - math.pi)
    return {
        "trials": trials,
        "estimate": estimate,
        "actual": math.pi,
        "absolute_error": err,
        "relative_error_pct": 100 * err / math.pi,
        "description": f"π ≈ {estimate:.6f}  (actual {math.pi:.6f}, error {err:.6f})",
    }


_OPS: dict[str, Callable[[int, int], bool]] = {
    ">=": lambda a, b: a >= b,
    ">":  lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    "<":  lambda a, b: a < b,
    "==": lambda a, b: a == b,
}


def dice_probability(dice: int = 2, sides: int = 6, target: int = 7,
                     op: str = ">=", trials: int = 50_000) -> dict:
    """P(sum of `dice` d`sides` `op` `target`)."""
    if op not in _OPS:
        raise ValueError(f"Unknown operator '{op}'; use one of {list(_OPS)}")
    compare = _OPS[op]
    hits = sum(
        1 for _ in range(trials)
        if compare(sum(random.randint(1, sides) for _ in range(dice)), target)
    )
    p = hits / trials
    return {
        "trials": trials,
        "dice": dice, "sides": sides, "target": target, "op": op,
        "probability": p,
        "percent": round(p * 100, 2),
        "description": f"P({dice}d{sides} {op} {target}) ≈ {p:.4f}  ({p * 100:.2f}%)",
    }


def coin_flips(flips: int = 10, heads: int = 5, op: str = ">=",
               trials: int = 50_000) -> dict:
    """P(heads-count `op` `heads` in `flips` fair coin flips)."""
    if op not in _OPS:
        raise ValueError(f"Unknown operator '{op}'; use one of {list(_OPS)}")
    compare = _OPS[op]
    hits = sum(
        1 for _ in range(trials)
        if compare(sum(random.randint(0, 1) for _ in range(flips)), heads)
    )
    p = hits / trials
    return {
        "trials": trials,
        "flips": flips, "heads": heads, "op": op,
        "probability": p,
        "percent": round(p * 100, 2),
        "description": f"P(heads {op} {heads} in {flips} flips) ≈ {p:.4f}  ({p * 100:.2f}%)",
    }


def birthday_problem(people: int | None = None, target_prob: float = 0.5,
                     trials: int = 50_000) -> dict:
    """
    people given: P(at least one shared birthday in a group of N).
    people absent: smallest N where that probability >= target_prob.
    """
    def _shared(n: int) -> bool:
        seen: set[int] = set()
        for _ in range(n):
            day = random.randint(1, 365)
            if day in seen:
                return True
            seen.add(day)
        return False

    if people is not None:
        hits = sum(1 for _ in range(trials) if _shared(people))
        p = hits / trials
        return {
            "trials": trials,
            "people": people,
            "probability": p,
            "percent": round(p * 100, 2),
            "description": f"P(shared birthday, {people} people) ≈ {p:.4f}  ({p * 100:.2f}%)",
        }

    for n in range(2, 100):
        hits = sum(1 for _ in range(trials) if _shared(n))
        p = hits / trials
        if p >= target_prob:
            return {
                "trials": trials,
                "people_needed": n,
                "probability": p,
                "target": target_prob,
                "description": f"Need {n} people for P(shared birthday) ≥ {target_prob:.0%}: got {p:.4f}",
            }
    return {"trials": trials, "people_needed": None,
            "description": "No group up to 99 people reaches the target probability."}


def normal_probability(mean: float = 0.0, stdev: float = 1.0,
                       lower: float | None = None, upper: float | None = None,
                       trials: int = 100_000) -> dict:
    """P(lower ≤ X ≤ upper) where X ~ N(mean, stdev)."""
    if lower is None and upper is None:
        raise ValueError("Provide at least one of --lower or --upper")
    hits = sum(
        1 for _ in range(trials)
        if (lower is None or random.gauss(mean, stdev) >= lower)
        and (upper is None or random.gauss(mean, stdev) <= upper)
    )
    # recompute cleanly to avoid two separate gauss calls per trial skewing things
    def _in(x: float) -> bool:
        return (lower is None or x >= lower) and (upper is None or x <= upper)
    hits = sum(1 for _ in range(trials) if _in(random.gauss(mean, stdev)))
    p = hits / trials
    rng = (f"[{lower}, {upper}]" if lower is not None and upper is not None
           else f">= {lower}" if upper is None else f"<= {upper}")
    return {
        "trials": trials,
        "distribution": f"N({mean}, {stdev})",
        "range": rng,
        "probability": p,
        "percent": round(p * 100, 2),
        "description": f"P(X ∈ {rng}) for N({mean}, {stdev}) ≈ {p:.4f}  ({p * 100:.2f}%)",
    }


def random_walk(steps: int = 100, trials: int = 10_000) -> dict:
    """Average final Euclidean distance from origin after N steps in 2D."""
    tau = 2 * math.pi
    distances = []
    for _ in range(trials):
        x = y = 0.0
        for _ in range(steps):
            a = random.uniform(0, tau)
            x += math.cos(a)
            y += math.sin(a)
        distances.append(math.sqrt(x * x + y * y))
    mean_d = statistics.mean(distances)
    theory = math.sqrt(steps)
    return {
        "trials": trials,
        "steps": steps,
        "mean_distance": mean_d,
        "theoretical_expected": theory,
        "stdev": statistics.stdev(distances),
        "description": f"Mean distance after {steps} steps: {mean_d:.3f}  (√{steps} = {theory:.3f})",
    }


def buffon_needle(trials: int = 100_000) -> dict:
    """Estimate π via Buffon's needle (needle length = line spacing = 1)."""
    tau = 2 * math.pi
    crosses = sum(
        1 for _ in range(trials)
        if abs(math.cos(random.uniform(0, tau))) >= random.uniform(0, 1)
    )
    if crosses == 0:
        raise RuntimeError("No needle crossings recorded (try more trials)")
    estimate = 2 * trials / crosses
    err = abs(estimate - math.pi)
    return {
        "trials": trials,
        "crossings": crosses,
        "estimate": estimate,
        "actual": math.pi,
        "absolute_error": err,
        "relative_error_pct": 100 * err / math.pi,
        "description": f"Buffon π ≈ {estimate:.6f}  (error {err:.6f})",
    }


# ── AI-assisted: parse a description into a template call ─────────────────────

_CLASSIFY_PROMPT = """\
You are a Monte Carlo simulation classifier. Given a user's description of a simulation,
return ONLY a JSON object (no markdown, no prose) with these fields:
  "template": one of "pi", "dice", "coin", "birthday", "normal", "walk", "buffon"
  "params": object with zero or more of these keys depending on template:
    dice:     dice (int), sides (int), target (int), op (str, one of >=/>/<=/</==)
    coin:     flips (int), heads (int), op (str)
    birthday: people (int or null), target_prob (float)
    normal:   mean (float), stdev (float), lower (float or null), upper (float or null)
    walk:     steps (int)
    pi/buffon: (no params)

If the description doesn't map to any template, set "template" to "unknown".

Description: """

_TEMPLATE_FNS = {
    "pi":       lambda p, t: estimate_pi(t),
    "buffon":   lambda p, t: buffon_needle(t),
    "dice":     lambda p, t: dice_probability(**{k: p[k] for k in p if k in
                    {"dice", "sides", "target", "op"}}, trials=t),
    "coin":     lambda p, t: coin_flips(**{k: p[k] for k in p if k in
                    {"flips", "heads", "op"}}, trials=t),
    "birthday": lambda p, t: birthday_problem(**{k: p[k] for k in p if k in
                    {"people", "target_prob"}}, trials=t),
    "normal":   lambda p, t: normal_probability(**{k: p[k] for k in p if k in
                    {"mean", "stdev", "lower", "upper"}}, trials=t),
    "walk":     lambda p, t: random_walk(**{k: p[k] for k in p if k in {"steps"}}, trials=t),
}

TEMPLATES = list(_TEMPLATE_FNS)


def simulate_from_description(description: str, trials: int = 50_000,
                               model: str = BUILD_MODEL) -> dict:
    """Ask Ollama to classify the description, then run the right template."""
    from urllib import request as _req, error as _err
    import base64 as _b64

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": _CLASSIFY_PROMPT + description}],
        "stream": False,
        "think": False,
        "format": "json",
        "options": {"num_ctx": 2048, "num_predict": 256},
    }).encode()
    try:
        with _req.urlopen(
            _req.Request(OLLAMA_BASE + "/api/chat", data=payload,
                         headers={"Content-Type": "application/json"}), timeout=60
        ) as resp:
            raw = json.load(resp)["message"]["content"].strip()
    except (_err.HTTPError, OSError) as exc:
        raise RuntimeError(f"Ollama unavailable: {exc}") from exc

    try:
        spec = json.loads(raw)
    except ValueError as exc:
        raise RuntimeError(f"Model returned non-JSON: {raw[:200]}") from exc

    template = spec.get("template", "unknown")
    if template == "unknown" or template not in _TEMPLATE_FNS:
        raise ValueError(
            f"Could not map '{description}' to a known template. "
            f"Try one of: {', '.join(TEMPLATES)}"
        )
    params = spec.get("params") or {}
    result = _TEMPLATE_FNS[template](params, trials)
    result["template_used"] = template
    result["params_used"] = params
    return result


# ── ASCII histogram ────────────────────────────────────────────────────────────

def ascii_histogram(values: list[float], width: int = 50, bins: int = 20) -> str:
    if not values:
        return "(no data)"
    lo, hi = min(values), max(values)
    if lo == hi:
        return f"All values = {lo}"
    step = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - lo) / step), bins - 1)
        counts[idx] += 1
    peak = max(counts)
    lines = []
    for i, c in enumerate(counts):
        bar = int(c / peak * width)
        label = f"{lo + i * step:8.3f}"
        lines.append(f"{label} | {'█' * bar}")
    return "\n".join(lines)
