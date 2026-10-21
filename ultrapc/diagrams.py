"""Diagrams — render educational flowcharts, trees, concept maps, and plots from
tiny text specs, LOCALLY. The token win: instead of hand-drawing ~1-3k tokens of
SVG, the assistant writes a ~10-line spec and Ultra-PC renders a clean PNG you
keep for study.

    python ultra.py diagram flow spec.mmd -o out.png     # Mermaid-style flowchart
    python ultra.py diagram plot code.py -o out.png      # matplotlib figure
    python ultra.py diagram templates                    # list starter specs
    python ultra.py diagram new flowchart out.mmd        # write a template to edit

Renders with matplotlib + networkx (no Graphviz binary needed). If the Graphviz
`dot` binary is on PATH, `diagram dot spec.dot` uses it for pro-grade layout.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from . import core

# --------------------------------------------------------------------------- #
#  Mermaid-style flowchart parsing  (a compact subset I can write cheaply)
# --------------------------------------------------------------------------- #

_ARROW = re.compile(r"\s*(-\.->|-->|==>|---)\s*")
_EDGELBL = re.compile(r"^\|([^|]*)\|\s*")
_NODE = re.compile(r"^([A-Za-z0-9_]+)\s*(\[\[.*?\]\]|\(\(.*?\)\)|\(\[.*?\]\)|"
                   r"\[.*?\]|\{.*?\}|\(.*?\))?")


def _shape_of(bracket: str) -> tuple[str, str]:
    """Return (shape, label) from a bracketed node decl."""
    if not bracket:
        return "box", ""
    b = bracket
    if b.startswith("{"):
        return "diamond", b[1:-1]
    if b.startswith("(("):
        return "circle", b[2:-2]
    if b.startswith("(["):
        return "stadium", b[2:-2]
    if b.startswith("(") and not b.startswith("(["):
        return "round", b[1:-1]
    if b.startswith("[["):
        return "subroutine", b[2:-2]
    return "box", b[1:-1]


def parse_flow(spec: str):
    """-> (direction, nodes{id:{label,shape}}, edges[(a,b,label)])."""
    direction = "TD"
    nodes: dict[str, dict] = {}
    edges: list[tuple] = []

    def node(expr: str) -> str:
        m = _NODE.match(expr.strip())
        if not m:
            nid = expr.strip().strip('"')
            nodes.setdefault(nid, {"label": nid, "shape": "box"})
            return nid
        nid, bracket = m.group(1), m.group(2) or ""
        shape, label = _shape_of(bracket)
        if nid not in nodes:
            nodes[nid] = {"label": label or nid, "shape": shape}
        elif label:
            nodes[nid].update({"label": label, "shape": shape})
        return nid

    for raw in spec.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        low = line.lower()
        if low.startswith(("flowchart", "graph")):
            m = re.search(r"\b(TD|TB|LR|RL|BT)\b", line, re.I)
            if m:
                direction = m.group(1).upper()
            continue
        # split into edge segments across arrows on one line
        parts = _ARROW.split(line)
        if len(parts) >= 3:
            i = 0
            while i + 2 < len(parts):
                left, right = parts[i], parts[i + 2]
                lbl_m = _EDGELBL.match(right)
                elabel = ""
                if lbl_m:
                    elabel = lbl_m.group(1).strip()
                    right = right[lbl_m.end():]
                a, b = node(left), node(right)
                edges.append((a, b, elabel))
                i += 2
        else:
            node(line)
    return direction, nodes, edges


# --------------------------------------------------------------------------- #
#  Layered layout (top-down / left-right) with barycenter ordering
# --------------------------------------------------------------------------- #

def _layers(nodes, edges):
    """Always produce a clean layered (top-down) layout. Cycles are broken for
    layering (their back-edges are still drawn, as curves)."""
    import networkx as nx
    g = nx.DiGraph()
    g.add_nodes_from(nodes)
    g.add_edges_from((a, b) for a, b, _ in edges)
    if not g.number_of_edges():
        pos = nx.spring_layout(g, seed=7, k=1.6) if g.number_of_nodes() else {}
        return {n: (p[0] * 7, p[1] * 7) for n, p in pos.items()}, False

    # break cycles so we can layer (remove one edge per cycle found)
    dag = g.copy()
    while True:
        try:
            cyc = nx.find_cycle(dag, orientation="original")
        except nx.NetworkXNoCycle:
            break
        dag.remove_edge(cyc[-1][0], cyc[-1][1])

    depth = {}
    for n in nx.topological_sort(dag):
        preds = list(dag.predecessors(n))
        depth[n] = 0 if not preds else max(depth[p] for p in preds) + 1
    layers: dict[int, list] = {}
    for n, d in depth.items():
        layers.setdefault(d, []).append(n)
    # barycenter passes (both directions) to reduce edge crossings
    order = {n: i for lyr in layers.values() for i, n in enumerate(lyr)}
    for _ in range(6):
        for d in sorted(layers)[1:]:
            layers[d].sort(key=lambda n: sum(order[p] for p in dag.predecessors(n))
                           / max(1, dag.in_degree(n)))
            for i, n in enumerate(layers[d]):
                order[n] = i
    pos = {}
    for d, row in layers.items():
        span = max(1, len(row) - 1)
        for i, n in enumerate(row):
            pos[n] = ((i - span / 2) * 4.2, -d * 2.6)
    return pos, True


_STYLE = {"box": "#2b8fd6", "round": "#00a3e0", "stadium": "#0f766e",
          "diamond": "#e0b04a", "circle": "#7c3aed", "subroutine": "#4e9638"}


def render_flow(spec: str, out: str, direction_override: str = "",
                title: str = "") -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse, FancyArrowPatch

    direction, nodes, edges = parse_flow(spec)
    direction = direction_override or direction
    pos, layered = _layers(nodes, edges)
    if direction in ("LR", "RL"):                # rotate for left-right flow
        pos = {n: (-y, -x) for n, (x, y) in pos.items()}
    if direction in ("RL", "BT"):
        pos = {n: (-x, -y) for n, (x, y) in pos.items()}

    fig, ax = plt.subplots(figsize=(11, 8))
    ax.axis("off")

    def draw_node(nid):
        x, y = pos[nid]
        info = nodes[nid]
        label = info["label"].replace("<br>", "\n").replace("\\n", "\n")
        shape = info["shape"]
        color = _STYLE.get(shape, "#2b8fd6")
        w = max(1.1, 0.28 * max(len(l) for l in label.split("\n")) + 0.5)
        h = 0.62 + 0.42 * (label.count("\n"))
        if shape == "diamond":
            pts = [(x, y + h), (x + w, y), (x, y - h), (x - w, y)]
            ax.add_patch(Polygon(pts, closed=True, facecolor=color,
                                 edgecolor="white", linewidth=1.5, zorder=2))
        elif shape == "circle":
            ax.add_patch(Ellipse((x, y), w * 1.7, h * 1.9, facecolor=color,
                                 edgecolor="white", linewidth=1.5, zorder=2))
        else:
            style = "round,pad=0.1,rounding_size=0.5" if shape in ("round", "stadium") \
                else "round,pad=0.1,rounding_size=0.12"
            ax.add_patch(FancyBboxPatch((x - w, y - h / 1.4), 2 * w, 2 * h / 1.4,
                                        boxstyle=style, facecolor=color,
                                        edgecolor="white", linewidth=1.5, zorder=2))
        ax.text(x, y, label, ha="center", va="center", color="white",
                fontsize=10, fontweight="bold", zorder=3)

    for nid in nodes:
        draw_node(nid)
    for a, b, elabel in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        back = y2 >= y1 - 0.1                     # loops / same-level edges: curve
        rad = 0.28 if back else 0.03
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                     mutation_scale=15, color="#5a7a90" if back else "#4a6577",
                     lw=1.5, shrinkA=20, shrinkB=20, zorder=1,
                     linestyle="--" if back else "-",
                     connectionstyle=f"arc3,rad={rad}"))
        if elabel:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, elabel, fontsize=8.5,
                    color="#0b3c5d", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="#eaf6ff", ec="none"), zorder=4)
    xs = [p[0] for p in pos.values()] or [0]
    ys = [p[1] for p in pos.values()] or [0]
    ax.set_xlim(min(xs) - 3, max(xs) + 3)
    ax.set_ylim(min(ys) - 2, max(ys) + 2)
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", color="#0b3c5d")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
#  Matplotlib code -> figure  (charts, math, function plots)
# --------------------------------------------------------------------------- #

def render_plot(code: str, out: str) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    ns = {"plt": plt, "np": np, "__name__": "__diagram__"}
    exec(code, ns)                               # user's own machine; their spec
    fig = plt.gcf()
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close("all")
    return out


# --------------------------------------------------------------------------- #
#  Optional Graphviz DOT (pro layout) if the binary is present
# --------------------------------------------------------------------------- #

def render_dot(dot_source: str, out: str, fmt: str = "png") -> str | None:
    exe = shutil.which("dot")
    if not exe:
        return None
    p = subprocess.run([exe, f"-T{fmt}", "-o", out], input=dot_source.encode(),
                       capture_output=True)
    return out if p.returncode == 0 else None


# --------------------------------------------------------------------------- #
#  Educational templates
# --------------------------------------------------------------------------- #

TEMPLATES: dict[str, dict] = {
    "flowchart": {"kind": "flow", "desc": "Process flowchart with a decision.",
        "spec": """flowchart TD
  A([Start]) --> B[Gather inputs]
  B --> C{Valid?}
  C -->|yes| D[Process]
  C -->|no| E[Show error]
  E --> B
  D --> F([Done])"""},
    "tree": {"kind": "flow", "desc": "Hierarchy / taxonomy tree.",
        "spec": """flowchart TD
  Root[Living things] --> A[Animals]
  Root --> B[Plants]
  A --> A1[Vertebrates]
  A --> A2[Invertebrates]
  B --> B1[Flowering]
  B --> B2[Non-flowering]"""},
    "concept-map": {"kind": "flow", "desc": "Concept map (relationships).",
        "spec": """flowchart LR
  P((Photosynthesis)) -->|needs| L[Light]
  P -->|needs| W[Water]
  P -->|needs| C[CO2]
  P -->|makes| G[Glucose]
  P -->|makes| O[Oxygen]"""},
    "cycle": {"kind": "flow", "desc": "Cyclic process.",
        "spec": """flowchart LR
  A[Plan] --> B[Do]
  B --> C[Check]
  C --> D[Act]
  D --> A"""},
    "sequence-steps": {"kind": "flow", "desc": "Linear step sequence.",
        "spec": """flowchart LR
  S1([Read]) --> S2([Understand]) --> S3([Apply]) --> S4([Review])"""},
    "function-plot": {"kind": "plot", "desc": "Plot math function(s).",
        "spec": """x = np.linspace(-6, 6, 400)
plt.plot(x, np.sin(x), label='sin(x)')
plt.plot(x, np.cos(x), label='cos(x)')
plt.axhline(0, color='gray', lw=.6); plt.axvline(0, color='gray', lw=.6)
plt.title('Trig functions'); plt.legend(); plt.grid(alpha=.3)"""},
    "bar-chart": {"kind": "plot", "desc": "Labelled bar chart.",
        "spec": """cats = ['Mon','Tue','Wed','Thu','Fri']
vals = [12, 19, 7, 15, 22]
plt.bar(cats, vals, color='#2b8fd6')
plt.title('Study minutes'); plt.ylabel('minutes')
for i,v in enumerate(vals): plt.text(i, v+0.3, str(v), ha='center')"""},
}


# --------------------------------------------------------------------------- #
#  Artistic "dark technical tutorial" SVG diagrams (glow, color-coded nodes,
#  labeled connectors, commit graphs). Built from tiny specs so these polished,
#  non-generic educational diagrams are cheap to produce.
# --------------------------------------------------------------------------- #

EDU = {  # the style palette — the "required information" to reproduce the look
    "bg": "#0d1b2a", "panel": "#0f1e30", "border": "#21344a",
    "text": "#c9d6e0", "muted": "#8aa0b4", "heading": "#f0883e",
    "orange": "#f0883e", "yellow": "#e0b04a", "green": "#3fb950",
    "purple": "#a371f7", "blue": "#58a6ff", "red": "#f85149", "gray": "#7a8ca0",
}
_FONT = "font-family='Segoe UI,system-ui,sans-serif'"


def _edu_defs() -> str:
    m = []
    for name in ("orange", "yellow", "green", "purple", "blue", "red", "gray"):
        c = EDU[name]
        m.append(f"<marker id='ar-{name}' markerWidth='9' markerHeight='9' "
                 f"refX='6' refY='3' orient='auto'><path d='M0,0 L6,3 L0,6 Z' "
                 f"fill='{c}'/></marker>")
        m.append(f"<filter id='glow-{name}' x='-60%' y='-60%' width='220%' "
                 f"height='220%'><feDropShadow dx='0' dy='0' stdDeviation='5' "
                 f"flood-color='{c}' flood-opacity='0.55'/></filter>")
    return "<defs>" + "".join(m) + "</defs>"


def _panel(w: int, h: int) -> str:
    return (f"<rect x='6' y='6' width='{w-12}' height='{h-12}' rx='16' "
            f"fill='{EDU['bg']}' stroke='{EDU['border']}' stroke-width='1.5'/>")


def edu_flow(nodes, arrows=None, return_label=None, caption=None, title=None) -> str:
    """Box-flow diagram (the 'three areas' style): nodes = [(title, subtitle,
    color), ...]; arrows = labels between consecutive nodes; return_label draws a
    labelled arrow looping back from last to first."""
    C, step, n = EDU, 290, len(nodes)
    w = 120 + n * 180 + (n - 1) * 110
    ny = 150 + (34 if title else 0)
    h = ny + 100 + (74 if return_label else 20) + (34 if caption else 0)
    cx = lambda i: 60 + 90 + i * step
    p = [f"<svg viewBox='0 0 {w} {h}' xmlns='http://www.w3.org/2000/svg' {_FONT}>",
         _edu_defs(), _panel(w, h)]
    if title:
        p.append(f"<text x='34' y='42' fill='{C['heading']}' font-size='19' "
                 f"font-weight='700'>{title}</text>")
    for i, (t, sub, color) in enumerate(nodes):
        col = C.get(color, C["orange"])
        x = cx(i) - 90
        p.append(f"<g filter='url(#glow-{color})'><rect x='{x}' y='{ny}' "
                 f"width='180' height='95' rx='14' fill='{C['bg']}' "
                 f"stroke='{col}' stroke-width='2'/></g>")
        p.append(f"<text x='{cx(i)}' y='{ny+42}' text-anchor='middle' fill='{col}' "
                 f"font-size='16' font-weight='700'>{t}</text>")
        if sub:
            p.append(f"<text x='{cx(i)}' y='{ny+66}' text-anchor='middle' "
                     f"fill='{C['muted']}' font-size='12.5'>{sub}</text>")
    ay = ny + 47
    for i, lbl in enumerate(arrows or []):
        x1, x2 = cx(i) + 90, cx(i + 1) - 90
        p.append(f"<line x1='{x1+4}' y1='{ay}' x2='{x2-2}' y2='{ay}' "
                 f"stroke='{C['orange']}' stroke-width='2.5' marker-end='url(#ar-orange)'/>")
        p.append(f"<text x='{(x1+x2)//2}' y='{ay-11}' text-anchor='middle' "
                 f"fill='{C['muted']}' font-size='12'>{lbl}</text>")
    if return_label:
        lx, rx, yb = cx(0), cx(n - 1), ny + 140
        p.append(f"<path d='M{rx},{ny+98} L{rx},{yb} L{lx},{yb} L{lx},{ny+98}' "
                 f"fill='none' stroke='{C['gray']}' stroke-width='2' marker-end='url(#ar-gray)'/>")
        p.append(f"<text x='{(lx+rx)//2}' y='{yb+22}' text-anchor='middle' "
                 f"fill='{C['muted']}' font-size='12.5' font-style='italic'>{return_label}</text>")
    if caption:
        p.append(f"<text x='{w//2}' y='{h-16}' text-anchor='middle' "
                 f"fill='{C['muted']}' font-size='12.5' font-style='italic'>{caption}</text>")
    p.append("</svg>")
    return "".join(p)


def edu_commit_graph(main, branches=None, caption=None, title=None) -> str:
    """Git-style commit graph. main = number of commits on the main line; each
    branch = {"from": commit_index, "commits": k, "label": str, "color":,
    "merge": bool}. Circles are color-coded nodes; a merge adds a joining node."""
    C = EDU
    branches = branches or []
    x0, dx, ymain = 90, 120, 130 + (34 if title else 0)
    yb = ymain + 110
    w = max(x0 + main * dx + 160,
            x0 + max((b["from"] + b["commits"]) for b in branches) * dx + 160
            if branches else 0)
    h = yb + 90 + (30 if caption else 0)
    p = [f"<svg viewBox='0 0 {int(w)} {int(h)}' xmlns='http://www.w3.org/2000/svg' {_FONT}>",
         _edu_defs(), _panel(int(w), int(h))]
    if title:
        p.append(f"<text x='34' y='42' fill='{C['heading']}' font-size='19' font-weight='700'>{title}</text>")

    def node(x, y, color):
        return (f"<circle cx='{x}' cy='{y}' r='13' fill='{C['bg']}' "
                f"stroke='{C[color]}' stroke-width='3' filter='url(#glow-{color})'/>")

    mx = [x0 + i * dx for i in range(main)]
    for i in range(main - 1):
        p.append(f"<line x1='{mx[i]}' y1='{ymain}' x2='{mx[i+1]}' y2='{ymain}' "
                 f"stroke='{C['gray']}' stroke-width='2'/>")
    for b in branches:
        col = b.get("color", "purple")
        fx = mx[b["from"]]
        bx = [fx + (j + 1) * dx for j in range(b["commits"])]
        pts = [(fx, ymain)] + [(x, yb) for x in bx]
        for a, c in zip(pts, pts[1:]):
            p.append(f"<line x1='{a[0]}' y1='{a[1]}' x2='{c[0]}' y2='{c[1]}' "
                     f"stroke='{C['gray']}' stroke-width='2'/>")
        for x in bx:
            p.append(node(x, yb, col))
        if b.get("merge"):
            my = mx[-1] + dx
            p.append(f"<line x1='{bx[-1]}' y1='{yb}' x2='{my}' y2='{ymain}' stroke='{C['gray']}' stroke-width='2'/>")
            p.append(f"<line x1='{mx[-1]}' y1='{ymain}' x2='{my}' y2='{ymain}' stroke='{C['gray']}' stroke-width='2'/>")
            p.append(node(my, ymain, "orange"))
            p.append(f"<text x='{my+22}' y='{ymain+5}' fill='{C['muted']}' font-size='13'>merge commit</text>")
        if b.get("label"):
            p.append(f"<text x='{bx[-1]+24}' y='{yb+5}' fill='{C['muted']}' font-size='13'>{b['label']}</text>")
    for x in mx:
        p.append(node(x, ymain, "green"))
    p.append(f"<text x='{mx[-1]+24}' y='{ymain+5}' fill='{C['muted']}' font-size='13'>main</text>")
    if caption:
        p.append(f"<text x='{int(w)//2}' y='{int(h)-16}' text-anchor='middle' fill='{C['muted']}' font-size='12.5' font-style='italic'>{caption}</text>")
    p.append("</svg>")
    return "".join(p)


def edu_network(nodes, edges, layout="spring", directed=False, pos=None,
                legend=None, caption=None, title=None, edge_labels=True) -> str:
    """Node-link graph in the artistic style — network topology, web/knowledge
    graphs, mind-webs. nodes = [(id, label, color), ...]; edges = [(a,b) or
    (a,b,label)]. layout ∈ spring|circular|shell|kamada|spectral, or pass an
    explicit `pos` = {id:(x,y)}. `legend` = {label:color} draws a key."""
    import networkx as nx
    C = EDU
    G = (nx.DiGraph if directed else nx.Graph)()
    info = {}
    for nd in nodes:
        nid = nd[0] if isinstance(nd, (list, tuple)) else nd
        label = nd[1] if isinstance(nd, (list, tuple)) and len(nd) > 1 else nid
        color = nd[2] if isinstance(nd, (list, tuple)) and len(nd) > 2 else "blue"
        info[nid] = {"label": str(label), "color": color}
        G.add_node(nid)
    elist = []
    for e in edges:
        G.add_edge(e[0], e[1])
        elist.append((e[0], e[1], e[2] if len(e) > 2 else ""))

    if pos is None:
        lay = {
            "spring": lambda: nx.spring_layout(G, seed=7, k=2.2, iterations=120),
            "circular": lambda: nx.circular_layout(G),
            "shell": lambda: nx.shell_layout(G),
            "kamada": lambda: (nx.kamada_kawai_layout(G) if G.number_of_edges()
                               else nx.spring_layout(G, seed=7)),
            "spectral": lambda: nx.spectral_layout(G),
        }
        pos = lay.get(layout, lay["spring"])()

    W, H = 920, 580
    top = 62 if title else 44
    botpad = 60 + (26 if caption else 0)
    xs = [p[0] for p in pos.values()] or [0]
    ys = [p[1] for p in pos.values()] or [0]
    rx, ry = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    sx = lambda x: 90 + (x - min(xs)) / rx * (W - 180)
    sy = lambda y: top + (max(ys) - y) / ry * (H - top - botpad)
    P = {n: (sx(p[0]), sy(p[1])) for n, p in pos.items()}

    p = [f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' {_FONT}>",
         _edu_defs(), _panel(W, H)]
    if title:
        p.append(f"<text x='34' y='42' fill='{C['heading']}' font-size='19' font-weight='700'>{title}</text>")
    # edges first (under nodes)
    for a, b, lbl in elist:
        (x1, y1), (x2, y2) = P[a], P[b]
        end = " marker-end='url(#ar-gray)'" if directed else ""
        p.append(f"<line x1='{x1:.0f}' y1='{y1:.0f}' x2='{x2:.0f}' y2='{y2:.0f}' "
                 f"stroke='{C['gray']}' stroke-width='1.8' stroke-opacity='0.7'{end}/>")
        if lbl and edge_labels:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            p.append(f"<rect x='{mx-len(lbl)*3.4-4:.0f}' y='{my-9:.0f}' width='{len(lbl)*6.8+8:.0f}' height='18' rx='4' fill='{C['bg']}' opacity='0.85'/>")
            p.append(f"<text x='{mx:.0f}' y='{my+4:.0f}' text-anchor='middle' fill='{C['muted']}' font-size='11'>{lbl}</text>")
    # nodes
    for nid, (x, y) in P.items():
        col = C.get(info[nid]["color"], C["blue"])
        p.append(f"<circle cx='{x:.0f}' cy='{y:.0f}' r='15' fill='{C['bg']}' "
                 f"stroke='{col}' stroke-width='3' filter='url(#glow-{info[nid]['color']})'/>")
        p.append(f"<text x='{x:.0f}' y='{y+32:.0f}' text-anchor='middle' fill='{C['text']}' font-size='12.5'>{info[nid]['label']}</text>")
    if legend:
        ly = top + 6
        for lab, color in legend.items():
            col = C.get(color, color)
            p.append(f"<circle cx='{W-150}' cy='{ly}' r='7' fill='{C['bg']}' stroke='{col}' stroke-width='3'/>")
            p.append(f"<text x='{W-136}' y='{ly+4}' fill='{C['muted']}' font-size='12'>{lab}</text>")
            ly += 24
    if caption:
        p.append(f"<text x='{W//2}' y='{H-16}' text-anchor='middle' fill='{C['muted']}' font-size='12.5' font-style='italic'>{caption}</text>")
    p.append("</svg>")
    return "".join(p)


def _topology_pos():
    """Hierarchical core/distribution/access positions for a network topology."""
    return {"core": (0, 2),
            "d1": (-1.4, 1), "d2": (1.4, 1),
            "a1": (-2.2, 0), "a2": (-0.8, 0), "a3": (0.8, 0), "a4": (2.2, 0)}


EDU_TEMPLATES = {
    "git-three-areas": lambda: edu_flow(
        [("Working Directory", "your actual files", "orange"),
         ("Staging Area", '("the index")', "yellow"),
         ("Repository", ".git — the history", "green")],
        arrows=["git add", "git commit"],
        return_label="git checkout / restore (bring a past version back)",
        title="The three areas", caption="Files flow left→right; checkout brings history back."),
    "git-branch": lambda: edu_commit_graph(
        4, [{"from": 2, "commits": 2, "label": "feature", "color": "purple"}],
        title="Branches", caption="A branch diverges at a commit; both lines grow independently."),
    "git-merge": lambda: edu_commit_graph(
        3, [{"from": 1, "commits": 2, "label": "feature", "color": "purple", "merge": True}],
        title="Three-way merge", caption="Both lines diverged, so Git makes a merge commit (two parents)."),
    "pipeline": lambda: edu_flow(
        [("Input", "raw data", "blue"), ("Process", "transform", "yellow"),
         ("Output", "result", "green")], arrows=["parse", "render"],
        title="Pipeline", caption="A simple three-stage pipeline."),

    # ---- network / node-link graphs -------------------------------------- #
    "net-topology": lambda: edu_network(
        [("core", "Core router", "orange"),
         ("d1", "Switch A", "blue"), ("d2", "Switch B", "blue"),
         ("a1", "Host 1", "green"), ("a2", "Host 2", "green"),
         ("a3", "Host 3", "green"), ("a4", "Host 4", "green")],
        [("core", "d1"), ("core", "d2"), ("d1", "a1"), ("d1", "a2"),
         ("d2", "a3"), ("d2", "a4")],
        pos=_topology_pos(), title="Network topology",
        legend={"core": "orange", "switch": "blue", "host": "green"},
        caption="Core → distribution switches → access hosts."),
    "net-star": lambda: edu_network(
        [("H", "Hub", "orange")] + [(f"n{i}", f"Node {i}", "blue") for i in range(1, 7)],
        [("H", f"n{i}") for i in range(1, 7)], layout="shell",
        title="Star / hub-and-spoke", caption="One hub, many spokes."),
    "net-mesh": lambda: edu_network(
        [(c, c, "purple") for c in "ABCDEF"],
        [("A", "B"), ("A", "C"), ("B", "C"), ("B", "D"), ("C", "E"),
         ("D", "E"), ("D", "F"), ("E", "F"), ("A", "F")],
        layout="kamada", title="Mesh network",
        caption="Peer-to-peer mesh — many redundant paths."),
    "web-graph": lambda: edu_network(
        [("core", "Machine Learning", "orange"),
         ("s", "Supervised", "blue"), ("u", "Unsupervised", "blue"),
         ("r", "Reinforcement", "blue"),
         ("cls", "Classification", "green"), ("reg", "Regression", "green"),
         ("clu", "Clustering", "green"), ("dr", "Dim. reduction", "green")],
        [("core", "s", "type"), ("core", "u", "type"), ("core", "r", "type"),
         ("s", "cls"), ("s", "reg"), ("u", "clu"), ("u", "dr")],
        layout="spring", title="Concept web",
        caption="A knowledge/web graph of related concepts."),
}


def render_edu(name: str, out: str) -> str:
    svg = EDU_TEMPLATES[name]()
    Path(out).expanduser().write_text(svg, encoding="utf-8")
    return out


def cmd_edu(name: str = "", out: str = "diagram.svg") -> int:
    if not name or name == "list":
        print("Artistic educational diagram templates (dark/glow style):")
        for k in EDU_TEMPLATES:
            print(f"  {k}")
        print("\n  diagram edu <name> -o out.svg   (open the .svg in a browser)")
        print("  These use edu_flow()/edu_commit_graph() — I build custom ones "
              "from a tiny spec.")
        return 0
    if name not in EDU_TEMPLATES:
        print(f"Unknown edu template '{name}'. Options: {', '.join(EDU_TEMPLATES)}")
        return 2
    if out.lower().endswith(".png"):
        out = out[:-4] + ".svg"
    p = render_edu(name, out)
    print(f"Rendered artistic diagram -> {p}")
    core.open_in_os(p)
    return 0


# --------------------------------------------------------------------------- #
#  Commands
# --------------------------------------------------------------------------- #

def _read_spec(src: str) -> str:
    if src == "-":
        import sys
        return sys.stdin.read()
    return Path(src).expanduser().read_text(encoding="utf-8")


def cmd_flow(src: str, out: str, direction="", title="") -> int:
    try:
        spec = _read_spec(src)
        p = render_flow(spec, out, direction, title)
        print(f"Rendered flowchart -> {p}")
        core.open_in_os(p)
        return 0
    except Exception as exc:
        print(f"Flow render failed: {exc}"); return 1


def cmd_plot(src: str, out: str) -> int:
    try:
        p = render_plot(_read_spec(src), out)
        print(f"Rendered plot -> {p}")
        core.open_in_os(p)
        return 0
    except Exception as exc:
        print(f"Plot render failed: {exc}"); return 1


def cmd_dot(src: str, out: str) -> int:
    r = render_dot(_read_spec(src), out)
    if r is None:
        print("Graphviz 'dot' not found on PATH. Install it, or use "
              "'diagram flow' (matplotlib, no binary needed)."); return 1
    print(f"Rendered DOT -> {r}"); core.open_in_os(r); return 0


def cmd_templates() -> int:
    for k, v in TEMPLATES.items():
        print(f"  {k:<16} [{v['kind']:<4}] {v['desc']}")
    print("\n  `diagram new <name> <out>` to write one, then edit + render.")
    return 0


def cmd_new(name: str, out: str) -> int:
    t = TEMPLATES.get(name)
    if not t:
        print(f"Unknown template '{name}'. Options: {', '.join(TEMPLATES)}"); return 2
    Path(out).expanduser().write_text(t["spec"] + "\n", encoding="utf-8")
    how = "diagram flow" if t["kind"] == "flow" else "diagram plot"
    print(f"Wrote {name} template -> {out}\nRender with:  python ultra.py {how} {out} -o out.png")
    return 0


# --------------------------------------------------------------------------- #
#  Menu + dispatch
# --------------------------------------------------------------------------- #

def _tool_from_template(ctx=None) -> None:
    from . import ui
    ui.title_bar("Diagrams — render an educational diagram")
    names = list(TEMPLATES)
    items = [(str(i + 1), f"{n}  ({TEMPLATES[n]['desc']})") for i, n in enumerate(names)]
    choice = ui.menu("Pick a template", "then edit + render", items, "Cancel")
    if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
        return
    name = names[int(choice) - 1]
    dest = ui.ask_save_file("Save the rendered diagram as", ".png")
    if not dest:
        ui.pause(); return
    t = TEMPLATES[name]
    try:
        if t["kind"] == "flow":
            render_flow(t["spec"], dest)
        else:
            render_plot(t["spec"], dest)
        ui.ok(f"Rendered -> {dest}")
        core.open_in_os(dest)
    except Exception as exc:
        ui.err(f"Render failed: {exc}")
    ui.pause()


def _tool_edu(ctx=None) -> None:
    from . import ui
    ui.title_bar("Diagrams — artistic educational (dark/glow, Git-style)")
    names = list(EDU_TEMPLATES)
    items = [(str(i + 1), n) for i, n in enumerate(names)]
    choice = ui.menu("Pick a template", "renders a styled .svg", items, "Cancel")
    if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
        return
    name = names[int(choice) - 1]
    dest = ui.ask_save_file("Save the diagram as", ".svg")
    if not dest:
        ui.pause(); return
    render_edu(name, dest)
    ui.ok(f"Rendered -> {dest}")
    core.open_in_os(dest)
    ui.pause()


def register() -> core.Category:
    cat = core.Category("diagrams", "Diagrams (flowcharts & plots)")
    cat.add("template", "Render a diagram from a template", _tool_from_template)
    cat.add("edu", "Artistic educational diagram (dark/glow)", _tool_edu)
    return cat


def handle(argv: list[str]) -> int | None:
    if not argv or argv[0].lower() != "diagram":
        return None
    rest = argv[1:]
    out = "diagram.png"
    pos = []
    i = 0
    direction = title = ""
    while i < len(rest):
        a = rest[i]
        if a in ("-o", "--out") and i + 1 < len(rest):
            out = rest[i + 1]; i += 2; continue
        if a == "--dir" and i + 1 < len(rest):
            direction = rest[i + 1]; i += 2; continue
        if a == "--title" and i + 1 < len(rest):
            title = rest[i + 1]; i += 2; continue
        pos.append(a); i += 1
    if not pos:
        print("usage: diagram <flow|plot|dot|templates|new> ...")
        return 2
    sub = pos[0].lower()
    if sub == "flow":
        return cmd_flow(pos[1] if len(pos) > 1 else "-", out, direction, title)
    if sub == "plot":
        return cmd_plot(pos[1] if len(pos) > 1 else "-", out)
    if sub == "dot":
        return cmd_dot(pos[1] if len(pos) > 1 else "-", out)
    if sub == "edu":
        return cmd_edu(pos[1] if len(pos) > 1 else "", out)
    if sub == "templates":
        return cmd_templates()
    if sub == "new":
        if len(pos) < 3:
            print("usage: diagram new <template> <out.mmd>"); return 2
        return cmd_new(pos[1], pos[2])
    print(f"Unknown diagram subcommand '{sub}'."); return 2


# --------------------------------------------------------------------------- #
#  DaVinci Ink â€” hand-drawn diagram style: parchment, iron-gall ink, red
#  chalk, a hairline of gold.  Companion to the vault's `davinci-codex`
#  tokens.  Same data specs as edu_flow / edu_network, so any diagram can be
#  re-rendered in either voice by swapping the function name.
# --------------------------------------------------------------------------- #

INK = {
    "paper": "#f2e9d2", "ink": "#3a2c1a", "chalk": "#96412e",
    "sepia": "#6d5940", "gold": "#a8842f", "slate": "#46617a",
    "olive": "#5b6b3a", "plum": "#6b4a6e",
}
# EDU color names -> ink equivalents, so existing specs port unchanged
_INK_MAP = {"orange": "chalk", "red": "chalk", "yellow": "gold",
            "green": "olive", "purple": "plum", "blue": "slate",
            "gray": "sepia"}
_INK_FONT = "font-family='Ink Free,Segoe Print,Bradley Hand,cursive'"


def _ink_col(name: str) -> str:
    return INK.get(name, INK.get(_INK_MAP.get(name, ""), INK["ink"]))


def _ink_rng(*vals):
    import random
    return random.Random(int(sum(abs(v) * (13 + 7 * i)
                                 for i, v in enumerate(vals))) & 0xFFFFFF)


def _rough_seg(x1, y1, x2, y2, rng, amp=1.6):
    """One wobbly stroke from A to B: subdivided quadratic path with small
    perpendicular jitter â€” the hand never draws a ruler-straight line."""
    import math
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy) or 1
    n = max(2, int(dist / 26))
    nx, ny = -dy / dist, dx / dist
    pts = []
    for i in range(1, n):
        t = i / n
        off = rng.uniform(-amp, amp)
        pts.append((x1 + dx * t + nx * off, y1 + dy * t + ny * off))
    d = f"M{x1:.1f},{y1:.1f} "
    prev = (x1, y1)
    for q in pts:
        mx_, my_ = (prev[0] + q[0]) / 2, (prev[1] + q[1]) / 2
        d += f"Q{prev[0]:.1f},{prev[1]:.1f} {mx_:.1f},{my_:.1f} "
        prev = q
    d += f"L{x2:.1f},{y2:.1f}"
    return d


def _ink_line(x1, y1, x2, y2, color, width=1.8, amp=1.6):
    """Double-stroked rough line (the second, fainter pass sells the sketch)."""
    rng = _ink_rng(x1, y1, x2, y2)
    d1 = _rough_seg(x1, y1, x2, y2, rng, amp)
    d2 = _rough_seg(x1, y1, x2, y2, rng, amp)
    return (f"<path d='{d1}' fill='none' stroke='{color}' "
            f"stroke-width='{width}' stroke-linecap='round'/>"
            f"<path d='{d2}' fill='none' stroke='{color}' "
            f"stroke-width='{width * 0.55:.2f}' stroke-opacity='0.45' "
            f"stroke-linecap='round'/>")


def _ink_circle(cx, cy, r, color, width=2.0, fill=None):
    """Rough circle: two overshooting elliptical arcs at slightly different
    radii/rotations â€” the compass slipped, charmingly."""
    import math
    rng = _ink_rng(cx, cy, r)
    out = []
    if fill:
        out.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' "
                   f"fill='{fill}'/>")
    for rr, op in ((1.0, 1.0), (0.965, 0.5)):
        a0 = rng.uniform(0, 6.28)
        rx_ = r * rr * rng.uniform(0.97, 1.03)
        ry_ = r * rr * rng.uniform(0.97, 1.03)
        rot = rng.uniform(-8, 8)
        x0 = cx + rx_ * math.cos(a0)
        y0 = cy + ry_ * math.sin(a0)
        x1 = cx + rx_ * math.cos(a0 + 6.15)
        y1 = cy + ry_ * math.sin(a0 + 6.15)
        out.append(f"<path d='M{x0:.1f},{y0:.1f} A{rx_:.1f},{ry_:.1f} {rot:.0f} 1 1 "
                   f"{x1:.1f},{y1:.1f}' fill='none' stroke='{color}' "
                   f"stroke-width='{width}' stroke-opacity='{op}' "
                   f"stroke-linecap='round'/>")
    return "".join(out)


def _ink_rect(x, y, w, h, color, width=1.8):
    return (_ink_line(x, y, x + w, y, color, width)
            + _ink_line(x + w, y - 1, x + w, y + h + 1, color, width)
            + _ink_line(x + w + 1, y + h, x - 1, y + h, color, width)
            + _ink_line(x, y + h + 1, x, y - 1, color, width))


def _ink_arrowhead(x, y, angle, color, size=9.0):
    import math
    a1, a2 = angle + 2.62, angle - 2.62
    return (_ink_line(x, y, x + size * math.cos(a1), y + size * math.sin(a1),
                      color, 1.6, 0.8)
            + _ink_line(x, y, x + size * math.cos(a2), y + size * math.sin(a2),
                        color, 1.6, 0.8))


def _ink_arrow(x1, y1, x2, y2, color, width=1.8):
    import math
    return (_ink_line(x1, y1, x2, y2, color, width)
            + _ink_arrowhead(x2, y2, math.atan2(y2 - y1, x2 - x1), color))


def _ink_panel(w, h):
    """Paper ground, rough ink border, straight gold hairline just inside."""
    return (f"<rect x='0' y='0' width='{w}' height='{h}' fill='{INK['paper']}'/>"
            f"<rect x='14' y='14' width='{w-28}' height='{h-28}' fill='none' "
            f"stroke='{INK['gold']}' stroke-width='0.8' stroke-opacity='0.8'/>"
            + _ink_rect(8, 8, w - 16, h - 16, INK["ink"], 1.6))


def _ink_text(x, y, s, color, size=15, anchor="middle", weight="", style=""):
    from xml.sax.saxutils import escape
    w = " font-weight='600'" if weight else ""
    st = f" font-style='{style}'" if style else ""
    return (f"<text x='{x:.0f}' y='{y:.0f}' text-anchor='{anchor}' "
            f"fill='{color}' font-size='{size}'{w}{st}>{escape(str(s))}</text>")


def ink_flow(nodes, arrows=None, return_label=None, caption=None, title=None) -> str:
    """Hand-drawn box-flow: same spec as edu_flow.  nodes = [(title, subtitle,
    color)]; arrows = labels between consecutive nodes; return_label loops
    last -> first underneath."""
    step, n = 290, len(nodes)
    w = 120 + n * 180 + (n - 1) * 110
    ny = 150 + (34 if title else 0)
    h = ny + 104 + (78 if return_label else 24) + (36 if caption else 0)
    cx = lambda i: 60 + 90 + i * step
    p = [f"<svg viewBox='0 0 {w} {h}' xmlns='http://www.w3.org/2000/svg' {_INK_FONT}>",
         _ink_panel(w, h)]
    if title:
        p.append(_ink_text(38, 52, title, INK["ink"], 21, "start", weight=True))
        p.append(_ink_line(38, 60, 38 + len(title) * 9.5, 62, INK["chalk"], 1.4))
    for i, (t, sub, color) in enumerate(nodes):
        col = _ink_col(color)
        x = cx(i) - 90
        p.append(_ink_rect(x, ny, 180, 95, col, 2.0))
        p.append(_ink_text(cx(i), ny + 42, t, INK["ink"], 16.5, weight=True))
        if sub:
            p.append(_ink_text(cx(i), ny + 68, sub, INK["sepia"], 13.5,
                               style="italic"))
    ay = ny + 47
    arrows = arrows or []
    for i in range(n - 1):
        x1, x2 = cx(i) + 92, cx(i + 1) - 92
        p.append(_ink_arrow(x1, ay, x2, ay, INK["sepia"], 1.8))
        if i < len(arrows) and arrows[i]:
            p.append(_ink_text((x1 + x2) / 2, ay - 12, arrows[i], INK["chalk"], 14))
    if return_label:
        yb = ny + 95 + 40
        p.append(_ink_line(cx(n - 1), ny + 97, cx(n - 1), yb, INK["sepia"], 1.6))
        p.append(_ink_line(cx(n - 1), yb, cx(0), yb, INK["sepia"], 1.6))
        p.append(_ink_arrow(cx(0), yb, cx(0), ny + 99, INK["sepia"], 1.6))
        p.append(_ink_text((cx(0) + cx(n - 1)) / 2, yb + 22, return_label,
                           INK["chalk"], 14, style="italic"))
    if caption:
        p.append(_ink_text(w // 2, h - 22, caption, INK["sepia"], 14,
                           style="italic"))
    p.append("</svg>")
    return "".join(p)


def ink_network(nodes, edges, layout="spring", directed=False, pos=None,
                legend=None, caption=None, title=None, edge_labels=True) -> str:
    """Hand-drawn node-link graph: same spec as edu_network.  Labels may
    contain a newline for a second, smaller line."""
    import math
    import networkx as nx
    G = (nx.DiGraph if directed else nx.Graph)()
    info = {}
    for nd in nodes:
        nid = nd[0] if isinstance(nd, (list, tuple)) else nd
        label = nd[1] if isinstance(nd, (list, tuple)) and len(nd) > 1 else nid
        color = nd[2] if isinstance(nd, (list, tuple)) and len(nd) > 2 else "ink"
        info[nid] = {"label": str(label), "color": color}
        G.add_node(nid)
    elist = []
    for e in edges:
        G.add_edge(e[0], e[1])
        elist.append((e[0], e[1], e[2] if len(e) > 2 else ""))
    if pos is None:
        lay = {
            "spring": lambda: nx.spring_layout(G, seed=7, k=2.2, iterations=120),
            "circular": lambda: nx.circular_layout(G),
            "shell": lambda: nx.shell_layout(G),
            "kamada": lambda: (nx.kamada_kawai_layout(G) if G.number_of_edges()
                               else nx.spring_layout(G, seed=7)),
            "spectral": lambda: nx.spectral_layout(G),
        }
        pos = lay.get(layout, lay["spring"])()
    W, H = 920, 580
    top = 70 if title else 48
    botpad = 64 + (28 if caption else 0)
    xs = [p[0] for p in pos.values()] or [0]
    ys = [p[1] for p in pos.values()] or [0]
    rx, ry = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    sx = lambda x: 95 + (x - min(xs)) / rx * (W - 190)
    sy = lambda y: top + (max(ys) - y) / ry * (H - top - botpad)
    P = {n: (sx(p[0]), sy(p[1])) for n, p in pos.items()}
    p = [f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg' {_INK_FONT}>",
         _ink_panel(W, H)]
    if title:
        p.append(_ink_text(38, 52, title, INK["ink"], 21, "start", weight=True))
        p.append(_ink_line(38, 60, 38 + len(title) * 9.5, 62, INK["chalk"], 1.4))
    R = 17
    for a, b, lbl in elist:
        (x1, y1), (x2, y2) = P[a], P[b]
        ang = math.atan2(y2 - y1, x2 - x1)
        xa, ya = x1 + R * math.cos(ang), y1 + R * math.sin(ang)
        xb, yb = x2 - (R + 3) * math.cos(ang), y2 - (R + 3) * math.sin(ang)
        if directed:
            p.append(_ink_arrow(xa, ya, xb, yb, INK["sepia"], 1.5))
        else:
            p.append(_ink_line(xa, ya, xb, yb, INK["sepia"], 1.5))
        if lbl and edge_labels:
            mx_, my_ = (x1 + x2) / 2, (y1 + y2) / 2
            p.append(f"<rect x='{mx_-len(lbl)*3.8-4:.0f}' y='{my_-11:.0f}' "
                     f"width='{len(lbl)*7.6+8:.0f}' height='20' "
                     f"fill='{INK['paper']}' opacity='0.9'/>")
            p.append(_ink_text(mx_, my_ + 4, lbl, INK["chalk"], 12.5))
    for nid, (x, y) in P.items():
        col = _ink_col(info[nid]["color"])
        p.append(_ink_circle(x, y, R, col, 2.2, fill=INK["paper"]))
        lines = info[nid]["label"].split("\n")
        p.append(_ink_text(x, y + R + 20, lines[0], INK["ink"], 14.5, weight=True))
        for j, extra in enumerate(lines[1:], 1):
            p.append(_ink_text(x, y + R + 20 + j * 17, extra, INK["sepia"], 12.5,
                               style="italic"))
    if legend:
        ly = top + 8
        for lab, color in legend.items():
            p.append(_ink_circle(W - 150, ly, 8, _ink_col(color), 1.8,
                                 fill=INK["paper"]))
            p.append(_ink_text(W - 136, ly + 4, lab, INK["sepia"], 12.5, "start"))
            ly += 26
    if caption:
        p.append(_ink_text(W // 2, H - 20, caption, INK["sepia"], 14,
                           style="italic"))
    p.append("</svg>")
    return "".join(p)

