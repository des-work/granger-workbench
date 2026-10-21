"""Probabilistic network Monte Carlo: graph structure plus uncertain events.

Example spec::

    {"directed": true,
     "nodes": [{"id": "Firewall", "entry": true, "p_fail": 0.05},
               {"id": "Database", "critical": true}],
     "edges": [{"source": "Firewall", "target": "Database",
                "p_propagate": 0.4}]}

Specs may be dictionaries, JSON strings, or JSON file paths. Nodes are strings,
integers, or dictionaries with ``id``, ``entry``, ``critical``, ``p_fail`` and
optional ``label`` fields. Edges are dictionaries with ``source``, ``target``
and ``p_propagate`` (default 1), or [source, target, probability] sequences.
Probabilities must be finite numbers in [0, 1]; duplicate nodes/edges are errors.
Endpoints omitted from ``nodes`` receive default node attributes.

Directed graphs are the default. Directed roots and undirected isolated nodes
are inferred as entry points only when ``entry`` is omitted. Explicit False is
always respected. Non-isolated undirected nodes need explicit entry flags.
Only entry nodes can seed a cascade, independently with ``p_fail`` (default 0).
Every newly compromised node attempts each outgoing connection once. Undirected
connections can propagate in either direction, with independent attempts.

``top_paths`` records one actual first-arrival BFS ancestry chain per critical
node hit per trial, including its entry node. This is a sample of causal paths,
not an enumeration of every possible path. Path rates may sum above the overall
critical rate when several critical nodes are reached in one trial.

All public simulations accept an optional integer seed without changing global
random state. Defense rankings share the same sampled entry failures and live
connections across every scenario in a trial. Removing nodes or blocking edges
cannot introduce new entry points or increase risk in these paired comparisons.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass
import json
import math
from numbers import Real
from pathlib import Path
import random


def _node_id(value, location: str):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{location} must be a string or integer node id")
    return value


def _probability(value, location: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{location} must be a finite probability in [0, 1]")
    if not 0 <= value <= 1:
        raise ValueError(f"{location} must be a finite probability in [0, 1]")
    return float(value)


def _boolean(value, location: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{location} must be a boolean")
    return value


def load_spec(spec: dict | str | Path) -> dict:
    """Validate and normalize a spec without modifying the caller's data."""
    if isinstance(spec, Path):
        spec = json.loads(spec.read_text(encoding="utf-8"))
    elif isinstance(spec, str):
        if not spec.strip():
            raise ValueError("graph spec cannot be empty")
        try:
            decoded = json.loads(spec)
        except json.JSONDecodeError:
            if spec.lstrip().startswith(("{", "[", '"')):
                raise
            decoded = json.loads(Path(spec).read_text(encoding="utf-8"))
        spec = decoded
    if not isinstance(spec, dict):
        raise ValueError("graph spec must be a JSON object")

    directed = _boolean(spec.get("directed", True), "directed")
    nodes, edges = spec.get("nodes", []), spec.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("nodes and edges must be lists")

    normalized_nodes, node_ids = [], set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            node = {"id": node}
        if "id" not in node:
            raise ValueError(f"nodes[{i}] requires an id")
        nid = _node_id(node["id"], f"nodes[{i}].id")
        if nid in node_ids:
            raise ValueError(f"duplicate node id: {nid!r}")
        node_ids.add(nid)
        normalized = {
            **node, "id": nid,
            "critical": _boolean(node.get("critical", False), f"nodes[{i}].critical"),
            "p_fail": _probability(node.get("p_fail", 0), f"nodes[{i}].p_fail"),
            "label": node.get("label", str(nid)),
        }
        if "entry" in node:
            normalized["entry"] = _boolean(node["entry"], f"nodes[{i}].entry")
        normalized_nodes.append(normalized)

    normalized_edges, edge_ids = [], set()
    for i, edge in enumerate(edges):
        if isinstance(edge, dict):
            if "source" not in edge or "target" not in edge:
                raise ValueError(f"edges[{i}] requires source and target")
            u, v, p = edge["source"], edge["target"], edge.get("p_propagate", 1)
            extra = edge
        elif isinstance(edge, (list, tuple)) and len(edge) in (2, 3):
            u, v = edge[:2]
            p, extra = edge[2] if len(edge) == 3 else 1, {}
        else:
            raise ValueError(f"edges[{i}] must be an object or a 2/3-item sequence")
        u = _node_id(u, f"edges[{i}].source")
        v = _node_id(v, f"edges[{i}].target")
        key = (u, v) if directed else frozenset((u, v))
        if key in edge_ids:
            raise ValueError(f"duplicate edge: {u!r} -> {v!r}; parallel edges are unsupported")
        edge_ids.add(key)
        normalized_edges.append({
            **extra, "source": u, "target": v,
            "p_propagate": _probability(p, f"edges[{i}].p_propagate"),
        })
        for nid in (u, v):
            if nid not in node_ids:
                node_ids.add(nid)
                normalized_nodes.append({
                    "id": nid, "critical": False, "p_fail": 0.0, "label": str(nid),
                })
    return {**spec, "directed": directed, "nodes": normalized_nodes, "edges": normalized_edges}


def _build_graph(spec: dict):
    """Return a NetworkX graph and normalized node/edge attribute mappings."""
    spec = load_spec(spec)
    try:
        import networkx as nx
    except ImportError as exc:
        raise RuntimeError("networkx is not installed") from exc

    graph = nx.DiGraph() if spec["directed"] else nx.Graph()
    node_attrs, edge_attrs, explicit_entries = {}, {}, set()
    for node in spec["nodes"]:
        nid = node["id"]
        if "entry" in node:
            explicit_entries.add(nid)
        attrs = {k: v for k, v in node.items() if k != "id"}
        attrs.setdefault("entry", False)
        node_attrs[nid] = attrs
        graph.add_node(nid, **attrs)
    for edge in spec["edges"]:
        u, v, p = edge["source"], edge["target"], edge["p_propagate"]
        graph.add_edge(u, v, p_propagate=p)
        edge_attrs[(u, v)] = p
    for nid, attrs in node_attrs.items():
        degree = graph.in_degree(nid) if graph.is_directed() else graph.degree(nid)
        if nid not in explicit_entries and degree == 0:
            attrs["entry"] = graph.nodes[nid]["entry"] = True
    return graph, node_attrs, edge_attrs


@dataclass(frozen=True)
class _Network:
    nodes: tuple
    entries: tuple
    critical: frozenset
    adjacency: tuple
    live_template: bytes
    uncertain_arcs: tuple
    edges: tuple


def _compile(spec) -> _Network:
    """Build NetworkX once, then use indexed adjacency in the simulation loop."""
    graph, attrs, edges = _build_graph(spec)
    nodes = tuple(graph.nodes)
    indices = {nid: i for i, nid in enumerate(nodes)}
    adjacency, probabilities = [[] for _ in nodes], []
    for edge_index, ((u, v), p) in enumerate(edges.items()):
        adjacency[indices[u]].append((indices[v], len(probabilities), edge_index))
        probabilities.append(p)
        if not graph.is_directed() and u != v:
            adjacency[indices[v]].append((indices[u], len(probabilities), edge_index))
            probabilities.append(p)
    return _Network(
        nodes=nodes,
        entries=tuple((indices[n], a["p_fail"]) for n, a in attrs.items() if a["entry"]),
        critical=frozenset(indices[n] for n, a in attrs.items() if a["critical"]),
        adjacency=tuple(tuple(neighbors) for neighbors in adjacency),
        live_template=bytes(p == 1 for p in probabilities),
        uncertain_arcs=tuple((i, p) for i, p in enumerate(probabilities) if 0 < p < 1),
        edges=tuple(edges),
    )


def _rng(trials: int, seed: int | None) -> random.Random:
    if isinstance(trials, bool) or not isinstance(trials, int) or trials <= 0:
        raise ValueError("trials must be a positive integer")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise ValueError("seed must be an integer or None")
    return random.Random(seed)


def _sample(network: _Network, rng: random.Random):
    # Draw every uncertain event before traversing, so intervention scenarios
    # share exactly the same potential events even when their BFS orders differ.
    seeds = [n for n, p in network.entries if p == 1 or (p > 0 and rng.random() < p)]
    if not seeds:
        return seeds, b""
    live = bytearray(network.live_template)
    for arc, p in network.uncertain_arcs:
        live[arc] = rng.random() < p
    return seeds, live


def _cascade(network: _Network, seeds, live, *, blocked_node=None,
             blocked_edge=None, trace=False, stop_at_critical=False):
    seen = {n for n in seeds if n != blocked_node}
    queue = collections.deque(n for n in seeds if n != blocked_node)
    parents = dict.fromkeys(seen) if trace else None
    while queue:
        node = queue.popleft()
        if stop_at_critical and node in network.critical:
            break
        for target, arc, edge in network.adjacency[node]:
            if (target == blocked_node or target in seen or edge == blocked_edge
                    or not live[arc]):
                continue
            seen.add(target)
            queue.append(target)
            if parents is not None:
                parents[target] = node
    return seen, parents


def _ordered(nodes):
    """Sort string/integer ids without comparing unlike types."""
    return sorted(nodes, key=lambda n: (isinstance(n, str), n))


def _wilson_interval(hits: int, trials: int) -> list[float]:
    """95% Wilson score interval, including meaningful bounds at 0/100% hits."""
    z = 1.959963984540054
    p = hits / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return [round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)]


def simulate(spec: dict | str | Path, trials: int = 100_000, *,
             seed: int | None = None) -> dict:
    """Run cascades; return node rates, causal paths and a Wilson risk interval.

    ``top_critical_outcomes`` retains the joint critical-node-set frequencies
    separately from actual ``top_paths``. Both rates use all trials as denominator.
    Repeat a run with identical spec, trials and seed for reproducible results.
    """
    rng = _rng(trials, seed)
    network = _compile(spec)
    hit_counts = [0] * len(network.nodes)
    critical_hits = total_compromised = 0
    path_counts, outcome_counts = collections.Counter(), collections.Counter()

    for _ in range(trials):
        compromised, parents = _cascade(network, *_sample(network, rng), trace=True)
        for node in compromised:
            hit_counts[node] += 1
        critical = compromised & network.critical
        critical_hits += bool(critical)
        total_compromised += len(compromised)
        if critical:
            outcome_counts[tuple(sorted(critical))] += 1
            for target in sorted(critical):
                path, node = [], target
                while node is not None:
                    path.append(node)
                    node = parents[node]
                path_counts[tuple(reversed(path))] += 1

    def summarize(counts):
        return [{"nodes": [network.nodes[n] for n in path], "count": count,
                 "rate": round(count / trials, 6)}
                for path, count in counts.most_common(10)]

    return {
        "trials": trials, "seed": seed, "critical_hits": critical_hits,
        "critical_rate": round(critical_hits / trials, 6),
        "critical_rate_pct": round(100 * critical_hits / trials, 3),
        "critical_rate_ci95": _wilson_interval(critical_hits, trials),
        "expected_compromised": round(total_compromised / trials, 4),
        "per_node": {n: round(hit_counts[i] / trials, 6) for i, n in enumerate(network.nodes)},
        "top_paths": summarize(path_counts),
        "top_critical_outcomes": summarize(outcome_counts),
        "critical_nodes": _ordered(network.nodes[i] for i in network.critical),
        "entry_nodes": _ordered(network.nodes[i] for i, _ in network.entries),
    }


def _defense_counts(network, trials, rng, candidates, *, edges=False):
    baseline_hits, hardened_hits = 0, [0] * len(candidates)
    if not network.critical:
        return baseline_hits, hardened_hits
    for _ in range(trials):
        seeds, live = _sample(network, rng)
        baseline, _ = _cascade(network, seeds, live, stop_at_critical=True)
        if network.critical.isdisjoint(baseline):
            # Hardening only removes reachable nodes: it cannot create a hit.
            continue
        baseline_hits += 1
        for i, candidate in enumerate(candidates):
            compromised, _ = _cascade(
                network, seeds, live, stop_at_critical=True,
                blocked_edge=candidate if edges else None,
                blocked_node=None if edges else candidate,
            )
            hardened_hits[i] += not network.critical.isdisjoint(compromised)
    return baseline_hits, hardened_hits


def _impact(baseline_hits: int, hardened_hits: int, trials: int) -> dict:
    # Subtract counts before rounding; tiny reductions must not become negative
    # or disappear because separately rounded estimates were subtracted.
    prevented = baseline_hits - hardened_hits
    return {
        "baseline_rate": round(baseline_hits / trials, 6),
        "hardened_rate": round(hardened_hits / trials, 6),
        "risk_reduction": round(prevented / trials, 6),
        "risk_reduction_pct": round(100 * prevented / trials, 3),
        "relative_reduction_pct": round(100 * prevented / baseline_hits, 2) if baseline_hits else 0.0,
    }


def defense_impact(spec: dict | str | Path, trials: int = 20_000, *,
                   seed: int | None = None) -> dict:
    """Rank non-critical nodes by risk reduction when completely removed.

    Entry flags are fixed from the original graph, and every candidate uses
    paired random samples. Memory use is independent of the number of trials.
    """
    rng = _rng(trials, seed)
    network = _compile(spec)
    candidates = [n for n in range(len(network.nodes)) if n not in network.critical]
    baseline, hardened = _defense_counts(network, trials, rng, candidates)
    entries = {n for n, _ in network.entries}
    results = [{"node": network.nodes[n], "is_entry": n in entries,
                **_impact(baseline, hits, trials)}
               for n, hits in zip(candidates, hardened)]
    results.sort(key=lambda row: -row["risk_reduction"])
    return {
        "trials_per_node": trials, "seed": seed, "nodes_tested": len(results),
        "baseline_critical_rate": round(baseline / trials, 6),
        "ranked_defenses": results, "top_defense": results[0] if results else None,
    }


def edge_hardening(spec: dict | str | Path, trials: int = 20_000, *,
                   seed: int | None = None) -> dict:
    """Rank connections by risk reduction when blocked (both ways if undirected)."""
    rng = _rng(trials, seed)
    network = _compile(spec)
    candidates = list(range(len(network.edges)))
    baseline, hardened = _defense_counts(network, trials, rng, candidates, edges=True)
    results = [{"edge": f"{u} → {v}", "source": u, "target": v,
                **_impact(baseline, hits, trials)}
               for (u, v), hits in zip(network.edges, hardened)]
    results.sort(key=lambda row: -row["risk_reduction"])
    return {
        "trials_per_edge": trials, "seed": seed, "edges_tested": len(results),
        "baseline_critical_rate": round(baseline / trials, 6),
        "ranked_edges": results, "top_defense": results[0] if results else None,
    }


def describe(results: dict) -> str:
    """Plain prose Granger can speak from a simulate() result dict."""
    cr, trials = results["critical_rate_pct"], results["trials"]
    parts = [f"After {trials:,} simulated trials, a critical node was compromised in {cr:.1f}% of runs."]
    interval = results.get("critical_rate_ci95")
    if interval:
        parts.append(f"The 95% confidence interval is {100 * interval[0]:.1f}% to {100 * interval[1]:.1f}%.")
    crit = results.get("critical_nodes", [])
    if crit:
        parts.append(f"The critical nodes being tracked are {', '.join(str(n) for n in crit)}.")
    per_node = results.get("per_node", {})
    if per_node and any(per_node.values()):
        hottest = max(per_node, key=per_node.get)
        parts.append(f"The most frequently compromised node was {hottest}, hit in {per_node[hottest] * 100:.1f}% of trials.")
    parts.append(f"On average, {results.get('expected_compromised', 0):.1f} nodes were compromised per trial.")
    top = results.get("top_paths", [])
    if top:
        path = top[0]
        parts.append(f"The most common recorded path to a critical node was {' → '.join(str(n) for n in path['nodes'])}, occurring in {path['rate'] * 100:.1f}% of runs.")
    return " ".join(parts)


def describe_defense(results: dict) -> str:
    """Plain prose from a defense_impact() or edge_hardening() result."""
    baseline = results.get("baseline_critical_rate", 0) * 100
    top = results.get("top_defense")
    if not top:
        return "No defenses to evaluate."
    if top["risk_reduction"] <= 0:
        return (f"With a baseline critical-outcome rate of {baseline:.1f}%, "
                "no tested defense reduced the critical-outcome rate in these trials.")
    action = f"hardening {top['node']}" if "node" in top else f"blocking the edge {top['edge']}"
    return (f"With a baseline critical-outcome rate of {baseline:.1f}%, {action} "
            f"reduces it to {top['hardened_rate'] * 100:.1f}% — "
            f"a {top['relative_reduction_pct']:.0f}% relative reduction. "
            "That is the highest-impact defense observed in these trials.")
