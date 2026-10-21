"""[3] Math & Science — an offline WolframAlpha-lite.

Safe expression evaluator, unit converter, base/number converter,
prime factorization, and quick statistics.
"""

from __future__ import annotations

import ast
import math
import operator

from . import core, ui

# --------------------------------------------------------------------------- #
#  Safe expression evaluator
# --------------------------------------------------------------------------- #

_BIN_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_NAMES.update({"pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
               "abs": abs, "round": round, "min": min, "max": max, "sum": sum})


def safe_eval(expr: str):
    """Evaluate a math expression without exec/eval risk."""
    node = ast.parse(expr, mode="eval").body

    def ev(n):
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float, complex)):
                return n.value
            raise ValueError("only numbers allowed")
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN_OPS:
            return _BIN_OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _UNARY_OPS:
            return _UNARY_OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Name):
            if n.id in _NAMES:
                return _NAMES[n.id]
            raise ValueError(f"unknown name: {n.id}")
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name) and n.func.id in _NAMES and callable(_NAMES[n.func.id]):
                return _NAMES[n.func.id](*[ev(a) for a in n.args])
            raise ValueError("unknown or disallowed function")
        if isinstance(n, ast.Tuple):
            return tuple(ev(e) for e in n.elts)
        if isinstance(n, ast.List):
            return [ev(e) for e in n.elts]
        raise ValueError("unsupported expression")

    return ev(node)


def calculator(ctx=None) -> None:
    ui.clear(); ui.title_bar("Calculator", "safe scientific expression evaluator")
    ui.dim("Functions: sqrt, sin, cos, tan, log, log10, exp, factorial, gcd, "
           "hypot, degrees, radians ...")
    ui.dim("Constants: pi, e, tau.   Type 'q' to leave.")
    print()
    while True:
        expr = ui.prompt("calc> ")
        if not expr or expr.lower() in ("q", "quit", "exit"):
            return
        try:
            result = safe_eval(expr)
            ui.status_line("OK", f"{expr} = {result}")
        except Exception as exc:
            ui.err(f"{exc}")


# --------------------------------------------------------------------------- #
#  Unit converter
# --------------------------------------------------------------------------- #

# base units: meter, kilogram, second, kelvin(offset handled), byte
_UNITS = {
    "length": {"mm": 0.001, "cm": 0.01, "m": 1, "km": 1000,
               "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344},
    "mass":   {"mg": 1e-6, "g": 0.001, "kg": 1, "t": 1000,
               "oz": 0.0283495, "lb": 0.453592, "st": 6.35029},
    "data":   {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3,
               "tb": 1024**4, "kbit": 128, "mbit": 128*1024},
    "speed":  {"mps": 1, "kmh": 1/3.6, "mph": 0.44704, "kn": 0.514444},
    "time":   {"s": 1, "min": 60, "h": 3600, "day": 86400, "week": 604800},
}


def _convert_temp(val, frm, to):
    frm, to = frm.lower(), to.lower()
    c = {"c": val, "f": (val - 32) / 1.8, "k": val - 273.15}.get(frm)
    if c is None:
        raise ValueError("temp units: c, f, k")
    return {"c": c, "f": c * 1.8 + 32, "k": c + 273.15}[to]


def unit_convert(ctx=None) -> None:
    ui.clear(); ui.title_bar("Unit Converter", "length / mass / data / speed / time / temp")
    cats = ", ".join(_UNITS) + ", temp"
    ui.dim(f"Format: <value> <from> <to>   e.g.  5 mi km   |   72 f c")
    ui.dim(f"Known units: {cats}")
    print()
    while True:
        line = ui.prompt("convert> ")
        if not line or line.lower() in ("q", "quit", "exit"):
            return
        parts = line.split()
        if len(parts) != 3:
            ui.err("need: value from to"); continue
        try:
            val = float(parts[0]); frm, to = parts[1].lower(), parts[2].lower()
        except ValueError:
            ui.err("first token must be a number"); continue
        if frm in ("c", "f", "k") and to in ("c", "f", "k"):
            try:
                ui.status_line("OK", f"{val} {frm} = {_convert_temp(val, frm, to):.4g} {to}")
            except Exception as exc:
                ui.err(str(exc))
            continue
        found = None
        for name, table in _UNITS.items():
            if frm in table and to in table:
                found = table; break
        if not found:
            ui.err("units not in the same known category"); continue
        result = val * found[frm] / found[to]
        ui.status_line("OK", f"{val} {frm} = {result:.6g} {to}")


# --------------------------------------------------------------------------- #
#  Base / number converter
# --------------------------------------------------------------------------- #

def base_convert(ctx=None) -> None:
    ui.clear(); ui.title_bar("Base Converter", "dec / hex / oct / bin")
    ui.dim("Enter a number with prefix (0x, 0o, 0b) or plain decimal. 'q' to leave.")
    print()
    while True:
        s = ui.prompt("number> ")
        if not s or s.lower() in ("q", "quit", "exit"):
            return
        try:
            n = int(s, 0) if any(s.lower().startswith(p) for p in ("0x", "0o", "0b")) else int(s)
        except ValueError:
            ui.err("could not parse"); continue
        ui.status_line("OK", f"DEC {n}   HEX 0x{n:X}   OCT 0o{n:o}   BIN 0b{n:b}")


# --------------------------------------------------------------------------- #
#  Prime factorization
# --------------------------------------------------------------------------- #

def _factorize(n: int) -> list[int]:
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d); n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append(n)
    return factors


def prime_factor(ctx=None) -> None:
    ui.clear(); ui.title_bar("Prime Factorization", "factor & primality")
    print()
    while True:
        s = ui.prompt("integer> ")
        if not s or s.lower() in ("q", "quit", "exit"):
            return
        try:
            n = int(s)
        except ValueError:
            ui.err("integer required"); continue
        if n < 2:
            ui.err("need n >= 2"); continue
        f = _factorize(n)
        if len(f) == 1:
            ui.status_line("OK", f"{n} is PRIME")
        else:
            from collections import Counter
            pretty = " x ".join(f"{p}^{e}" if e > 1 else str(p)
                                for p, e in sorted(Counter(f).items()))
            ui.status_line("OK", f"{n} = {pretty}")


# --------------------------------------------------------------------------- #
#  Quick statistics
# --------------------------------------------------------------------------- #

def statistics_tool(ctx=None) -> None:
    ui.clear(); ui.title_bar("Quick Statistics", "mean / median / stdev / more")
    ui.dim("Enter numbers separated by spaces or commas. 'q' to leave.")
    print()
    import statistics as st
    while True:
        s = ui.prompt("data> ")
        if not s or s.lower() in ("q", "quit", "exit"):
            return
        try:
            data = [float(x) for x in s.replace(",", " ").split()]
        except ValueError:
            ui.err("numbers only"); continue
        if not data:
            continue
        r = core.Report("Quick Statistics")
        r.section(f"n = {len(data)}")
        r.line(f"  sum      {sum(data):.6g}")
        r.line(f"  min/max  {min(data):.6g} / {max(data):.6g}")
        r.line(f"  range    {max(data) - min(data):.6g}")
        r.line(f"  mean     {st.mean(data):.6g}")
        r.line(f"  median   {st.median(data):.6g}")
        if len(data) > 1:
            r.line(f"  stdev    {st.stdev(data):.6g}  (sample)")
            r.line(f"  variance {st.variance(data):.6g}")
        try:
            r.line(f"  mode     {st.mode(data):.6g}")
        except Exception:
            pass
        print()
        for ln in r.lines[7:]:  # skip header
            ui.info(ln.strip())
        print()


# --------------------------------------------------------------------------- #
#  Registration
# --------------------------------------------------------------------------- #

def register() -> core.Category:
    cat = core.Category("math", "Math & Science")
    cat.add("calc", "Scientific calculator", calculator)
    cat.add("units", "Unit converter", unit_convert)
    cat.add("base", "Base converter (dec/hex/oct/bin)", base_convert)
    cat.add("prime", "Prime factorization & primality", prime_factor)
    cat.add("stats", "Quick statistics", statistics_tool)
    return cat
