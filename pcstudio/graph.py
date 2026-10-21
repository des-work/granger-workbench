"""NetworkX graph analysis for pcstudio.

Graph spec format (dict or JSON string/file):
    {
        "directed": false,          # optional, default false
        "nodes": ["A", "B", ...],   # optional; inferred from edges if omitted
        "edges": [
            ["A", "B"],             # unweighted
            ["B", "C", 2.5]         # weighted (third element = weight)
        ]
    }

Nodes and edge endpoints can be strings or integers.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


# ── lazy import ───────────────────────────────────────────────────────────────

def _nx():
    try:
        import networkx as nx
        return nx
    except ImportError:
        raise RuntimeError(
            "networkx is not installed. "
            "Run: python -m pip install networkx"
        )


# ── graph I/O ─────────────────────────────────────────────────────────────────

def load(spec: dict | str | Path):
    """Return a networkx Graph or DiGraph from a spec dict, JSON string, or file path."""
    nx = _nx()

    if isinstance(spec, Path):
        path = spec
        if path.suffix == ".graphml":
            return nx.read_graphml(path)
        if path.suffix == ".gexf":
            return nx.read_gexf(path)
        spec = json.loads(path.read_text(encoding="utf-8"))
    elif isinstance(spec, str) and not spec.lstrip().startswith("{"):
        path = Path(spec)
        if path.suffix == ".graphml":
            return nx.read_graphml(path)
        if path.suffix == ".gexf":
            return nx.read_gexf(path)
        spec = json.loads(path.read_text(encoding="utf-8"))
    elif isinstance(spec, str):
        spec = json.loads(spec)

    directed = spec.get("directed", False)
    G = nx.DiGraph() if directed else nx.Graph()

    for node in spec.get("nodes", []):
        if isinstance(node, dict):
            nid = node["id"]
            G.add_node(nid, **{k: v for k, v in node.items() if k != "id"})
        else:
            G.add_node(node)

    for edge in spec.get("edges", []):
        if isinstance(edge, dict):
            u, v = edge["source"], edge["target"]
            attrs = {k: v for k, v in edge.items() if k not in ("source", "target")}
            G.add_edge(u, v, **attrs)
        elif len(edge) >= 3:
            G.add_edge(edge[0], edge[1], weight=edge[2])
        else:
            G.add_edge(edge[0], edge[1])

    return G


def to_spec(G) -> dict:
    """Serialize a networkx graph back to the spec dict format."""
    nx = _nx()
    spec = {"directed": G.is_directed(), "nodes": list(G.nodes()),
            "edges": [[u, v] for u, v in G.edges()]}
    if nx.is_weighted(G):
        spec["edges"] = [[u, v, d.get("weight", 1)] for u, v, d in G.edges(data=True)]
    return spec


# ── analyses ──────────────────────────────────────────────────────────────────

def info(G) -> dict:
    """Basic structural statistics."""
    nx = _nx()
    degrees = [d for _, d in G.degree()]
    result: dict = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "directed": G.is_directed(),
        "weighted": nx.is_weighted(G),
        "density": round(nx.density(G), 6),
        "avg_degree": round(sum(degrees) / len(degrees), 4) if degrees else 0,
        "max_degree": max(degrees) if degrees else 0,
        "min_degree": min(degrees) if degrees else 0,
        "self_loops": nx.number_of_selfloops(G),
    }
    if not G.is_directed():
        result["connected"] = nx.is_connected(G)
        if result["connected"] and G.number_of_nodes() > 0:
            result["diameter"] = nx.diameter(G)
            result["radius"] = nx.radius(G)
            result["avg_clustering"] = round(nx.average_clustering(G), 6)
        else:
            comps = list(nx.connected_components(G))
            result["components"] = len(comps)
            result["largest_component"] = max(len(c) for c in comps) if comps else 0
    else:
        result["weakly_connected"] = nx.is_weakly_connected(G)
        result["strongly_connected"] = nx.is_strongly_connected(G)
        result["is_dag"] = nx.is_directed_acyclic_graph(G)
    return result


def centrality(G, top: int = 10) -> dict:
    """Degree, betweenness, closeness, eigenvector, and PageRank centrality."""
    nx = _nx()

    def _top(d: dict, k: int) -> list:
        return [[n, round(v, 6)] for n, v in sorted(d.items(), key=lambda x: -x[1])[:k]]

    result: dict = {
        "degree":      _top(nx.degree_centrality(G), top),
        "betweenness": _top(nx.betweenness_centrality(G), top),
        "closeness":   _top(nx.closeness_centrality(G), top),
    }
    try:
        result["eigenvector"] = _top(nx.eigenvector_centrality(G, max_iter=500), top)
    except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
        result["eigenvector"] = None
    try:
        result["pagerank"] = _top(nx.pagerank(G), top)
    except nx.NetworkXError:
        result["pagerank"] = None
    return result


def shortest_path(G, source, target) -> dict:
    """Shortest path between two nodes."""
    nx = _nx()
    try:
        if nx.is_weighted(G):
            path = nx.dijkstra_path(G, source, target)
            length = nx.dijkstra_path_length(G, source, target)
        else:
            path = nx.shortest_path(G, source, target)
            length = len(path) - 1
        return {"found": True, "path": path, "length": length, "hops": len(path) - 1}
    except nx.NetworkXNoPath:
        return {"found": False, "error": f"No path between {source!r} and {target!r}"}
    except nx.NodeNotFound as exc:
        return {"found": False, "error": str(exc)}


def all_pairs_shortest_path_lengths(G) -> dict:
    """Average and distribution of shortest path lengths (for connected graphs)."""
    nx = _nx()
    if G.number_of_nodes() > 500:
        raise ValueError("Graph too large for all-pairs BFS (> 500 nodes); use shortest_path instead")
    lengths = []
    for source, paths in nx.shortest_path_length(G):
        for target, length in paths.items():
            if source != target:
                lengths.append(length)
    if not lengths:
        return {"avg_path_length": None, "diameter": None}
    return {
        "avg_path_length": round(statistics.mean(lengths), 4),
        "diameter": max(lengths),
        "radius": min(lengths),
        "stdev": round(statistics.stdev(lengths), 4) if len(lengths) > 1 else 0.0,
    }


def mst(G) -> dict:
    """Minimum spanning tree or forest (undirected only)."""
    nx = _nx()
    if G.is_directed():
        raise ValueError("MST requires an undirected graph")
    T = nx.minimum_spanning_tree(G)
    total = sum(d.get("weight", 1) for _, _, d in T.edges(data=True))
    return {
        "nodes": T.number_of_nodes(),
        "edges": T.number_of_edges(),
        "total_weight": round(total, 6),
        "edges_list": [[u, v, round(d.get("weight", 1), 6)] for u, v, d in T.edges(data=True)],
    }


def communities(G) -> dict:
    """Greedy modularity community detection."""
    nx = _nx()
    from networkx.algorithms.community import greedy_modularity_communities, modularity
    Gu = G.to_undirected() if G.is_directed() else G
    comms = list(greedy_modularity_communities(Gu))
    mod = modularity(Gu, comms)
    return {
        "count": len(comms),
        "modularity": round(mod, 6),
        "communities": [sorted(c) for c in sorted(comms, key=len, reverse=True)],
        "sizes": [len(c) for c in sorted(comms, key=len, reverse=True)],
    }


def cycles(G) -> dict:
    """Find cycles. Simple cycles for directed graphs; cycle basis for undirected."""
    nx = _nx()
    if G.is_directed():
        found = list(nx.simple_cycles(G))
    else:
        found = nx.cycle_basis(G)
    return {
        "count": len(found),
        "has_cycles": len(found) > 0,
        "cycles": found[:20],
        "note": "Showing first 20" if len(found) > 20 else None,
    }


def topological_sort(G) -> dict:
    """Topological ordering for DAGs."""
    nx = _nx()
    if not G.is_directed():
        raise ValueError("Topological sort requires a directed graph")
    if not nx.is_directed_acyclic_graph(G):
        cycle = next(iter(nx.simple_cycles(G)), None)
        raise ValueError(f"Graph has cycles — topological sort undefined. Example cycle: {cycle}")
    order = list(nx.topological_sort(G))
    layers = list(nx.topological_generations(G))
    return {
        "order": order,
        "nodes": len(order),
        "layers": [sorted(layer) for layer in layers],
        "layer_count": len(layers),
    }


def node_info(G, node) -> dict:
    """Degree, neighbors, and local clustering for one node."""
    nx = _nx()
    if node not in G:
        raise ValueError(f"Node {node!r} is not in the graph")
    result: dict = {
        "node": node,
        "degree": G.degree(node),
        "attributes": dict(G.nodes[node]),
    }
    if G.is_directed():
        result["in_degree"]  = G.in_degree(node)
        result["out_degree"] = G.out_degree(node)
        result["predecessors"] = list(G.predecessors(node))
        result["successors"]   = list(G.successors(node))
    else:
        result["neighbors"] = list(G.neighbors(node))
        result["clustering"] = round(nx.clustering(G, node), 6)
    edge_weights = [d.get("weight") for _, _, d in G.edges(node, data=True)
                    if d.get("weight") is not None]
    if edge_weights:
        result["edge_weight_sum"] = round(sum(edge_weights), 6)
        result["edge_weight_avg"] = round(sum(edge_weights) / len(edge_weights), 6)
    return result


def describe(G) -> str:
    """One-paragraph human-readable summary for Granger to speak."""
    nx = _nx()
    n, e = G.number_of_nodes(), G.number_of_edges()
    kind = "directed" if G.is_directed() else "undirected"
    d = nx.density(G)
    parts = [f"The graph has {n} node{'s' if n != 1 else ''} and {e} edge{'s' if e != 1 else ''} ({kind}, density {d:.3f})."]
    if not G.is_directed() and nx.is_connected(G):
        parts.append(f"It is connected with diameter {nx.diameter(G)} and average clustering {nx.average_clustering(G):.3f}.")
    elif not G.is_directed():
        comps = nx.number_connected_components(G)
        parts.append(f"It has {comps} connected components.")
    else:
        parts.append("It is " + ("a DAG." if nx.is_directed_acyclic_graph(G) else "not acyclic."))
    degs = sorted([d for _, d in G.degree()], reverse=True)
    if degs:
        parts.append(f"Highest-degree node: {max(G.degree(), key=lambda x: x[1])[0]} (degree {degs[0]}).")
    return " ".join(parts)


# ── quick graph builder from text description ─────────────────────────────────

def from_edge_list(edges_str: str, directed: bool = False):
    """Build a graph from a compact edge-list string.

    Formats accepted (one edge per line or comma-separated):
        A -> B          directed edge
        A -- B          undirected edge
        A - B           undirected edge
        A -> B : 2.5    weighted
        A, B            simple pair
    """
    nx = _nx()
    G = nx.DiGraph() if directed else nx.Graph()
    import re
    for token in re.split(r"[,\n]+", edges_str):
        token = token.strip()
        if not token:
            continue
        m = re.match(r"^(.+?)\s*(?:->|--|-)?\s*(.+?)(?:\s*:\s*([0-9.]+))?$", token)
        if not m:
            continue
        u, v, w = m.group(1).strip(), m.group(2).strip(), m.group(3)
        if w is not None:
            G.add_edge(u, v, weight=float(w))
        else:
            G.add_edge(u, v)
    return G
