import contextlib
import copy
import io
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pcstudio import easy, mcp, netmc


def chain(probability=1):
    return {
        "nodes": [{"id": "entry", "entry": True, "p_fail": probability},
                  "bridge", {"id": "critical", "critical": True}],
        "edges": [["entry", "bridge"], ["bridge", "critical"]],
    }


def exact_risk(spec, blocked_node=None, blocked_edge=None):
    """Independent small-world enumeration, without the simulation's helpers."""
    nodes = {node["id"]: node for node in spec["nodes"]}
    entries = [(n, a["p_fail"]) for n, a in nodes.items() if a.get("entry")]
    arcs = [(i, e["source"], e["target"], e["p_propagate"])
            for i, e in enumerate(spec["edges"])]
    if not spec.get("directed", True):
        arcs += [(i, v, u, p) for i, u, v, p in arcs if u != v]
    probabilities = [p for _, p in entries] + [p for _, _, _, p in arcs]
    risk = 0
    for bits in itertools.product((False, True), repeat=len(probabilities)):
        weight = 1
        for bit, p in zip(bits, probabilities):
            weight *= p if bit else 1 - p
        reached = {n for (n, _), bit in zip(entries, bits) if bit and n != blocked_node}
        active = [(u, v) for (i, u, v, _), bit in zip(arcs, bits[len(entries):])
                  if bit and i != blocked_edge and blocked_node not in (u, v)]
        while True:
            expanded = reached | {v for u, v in active if u in reached}
            if expanded == reached:
                break
            reached = expanded
        if any(nodes[n].get("critical") for n in reached):
            risk += weight
    return risk


class SpecTests(unittest.TestCase):
    def test_dict_json_and_path_inputs_are_equivalent_and_unchanged(self):
        spec = chain()
        original = copy.deepcopy(spec)
        expected = netmc.simulate(spec, 20, seed=4)
        self.assertEqual(spec, original)
        self.assertEqual(netmc.simulate(json.dumps(spec), 20, seed=4), expected)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "graph.json"
            path.write_text(json.dumps(spec), encoding="utf-8")
            for source in (path, str(path)):
                self.assertEqual(netmc.simulate(source, 20, seed=4), expected)

    def test_normalization_is_idempotent_and_retains_metadata(self):
        spec = chain()
        spec["title"] = "Example"
        spec["nodes"][0]["cost"] = 5
        normalized = netmc.load_spec(spec)
        self.assertEqual(netmc.load_spec(normalized), normalized)
        self.assertEqual(normalized["title"], "Example")
        self.assertEqual(normalized["nodes"][0]["cost"], 5)

    def test_implicit_endpoints_get_default_attributes(self):
        result = netmc.simulate({"nodes": [{"id": 1, "p_fail": 1}],
                                 "edges": [[1, "sink"]]}, 5, seed=0)
        self.assertEqual(result["per_node"], {1: 1, "sink": 1})

    def test_explicit_false_entry_is_not_inferred(self):
        spec = chain()
        spec["nodes"][0]["entry"] = False
        result = netmc.simulate(spec, 10, seed=0)
        self.assertEqual(result["entry_nodes"], [])
        self.assertEqual(result["critical_hits"], 0)

    def test_only_omitted_entry_flags_are_inferred(self):
        spec = chain()
        del spec["nodes"][0]["entry"]
        self.assertEqual(netmc.simulate(spec, 5)["critical_rate"], 1)
        spec["directed"] = False
        self.assertEqual(netmc.simulate(spec, 5)["entry_nodes"], [])
        spec["nodes"].append({"id": "isolated", "p_fail": 1})
        self.assertEqual(netmc.simulate(spec, 5)["entry_nodes"], ["isolated"])

    def test_invalid_specs_fail_with_value_errors(self):
        specs = [None, [], "[]", "null", "true", "42", "", {"nodes": {}},
                 {"edges": None}, {"directed": "false"}, {"nodes": [{}]},
                 {"nodes": [None]}, {"nodes": [True]}, {"nodes": [["A"]]},
                 {"nodes": ["A", {"id": "A"}]}, {"edges": [{}]},
                 {"edges": [["A"]]}, {"edges": ["AB"]},
                 {"edges": [["A", "B", 1, "extra"]]},
                 {"edges": [[[], "B"]]}, {"nodes": [{"id": "A", "entry": "false"}]},
                 {"nodes": [{"id": "A", "critical": 1}]},
                 {"edges": [["A", "B"], ["A", "B"]]},
                 {"directed": False, "edges": [["A", "B"], ["B", "A"]]}]
        for spec in specs:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                netmc.simulate(spec, 5)

    def test_invalid_probabilities_are_rejected_at_nodes_and_edges(self):
        for p in (-0.1, 1.1, float("nan"), float("inf"), -float("inf"), "0.5", None, True):
            for spec in ({"nodes": [{"id": "A", "p_fail": p}]},
                         {"edges": [["A", "B", p]]}):
                with self.subTest(p=p, spec=spec), self.assertRaisesRegex(ValueError, "probability"):
                    netmc.simulate(spec, 5)

    def test_trials_and_seed_are_validated_by_all_operations(self):
        for operation in (netmc.simulate, netmc.defense_impact, netmc.edge_hardening):
            for trials in (0, -1, True, 1.5, "10", None):
                with self.subTest(operation=operation, trials=trials), self.assertRaisesRegex(ValueError, "trials"):
                    operation({}, trials)
            for seed in (False, 1.5, "5"):
                with self.subTest(operation=operation, seed=seed), self.assertRaisesRegex(ValueError, "seed"):
                    operation({}, 5, seed=seed)


class SimulationTests(unittest.TestCase):
    def test_deterministic_chain_has_full_causal_paths(self):
        result = netmc.simulate(chain(), 10, seed=2)
        self.assertEqual(result["critical_hits"], 10)
        self.assertEqual(result["expected_compromised"], 3)
        self.assertEqual(result["top_paths"], [{"nodes": ["entry", "bridge", "critical"],
                                                "count": 10, "rate": 1}])
        self.assertEqual(result["top_critical_outcomes"][0]["nodes"], ["critical"])
        self.assertIn("entry → bridge → critical", netmc.describe(result))

    def test_zero_probabilities_and_empty_network(self):
        for spec in ({}, chain(0), {**chain(), "edges": [["entry", "bridge", 0]]}):
            result = netmc.simulate(spec, 10, seed=0)
            self.assertEqual(result["critical_rate"], 0)
            self.assertEqual(result["top_paths"], [])
        self.assertEqual(netmc.simulate({}, 5)["per_node"], {})
        self.assertNotIn("most frequently", netmc.describe(netmc.simulate(chain(0), 5)))

    def test_undirected_edges_work_in_both_orientations(self):
        for edge in (["entry", "critical"], ["critical", "entry"]):
            spec = {"directed": False,
                    "nodes": [{"id": "entry", "entry": True, "p_fail": 1},
                              {"id": "critical", "critical": True}], "edges": [edge]}
            result = netmc.simulate(spec, 5, seed=0)
            self.assertEqual(result["critical_rate"], 1)
            self.assertEqual(result["top_paths"][0]["nodes"], ["entry", "critical"])
            self.assertEqual(netmc.edge_hardening(spec, 5)["top_defense"]["hardened_rate"], 0)

    def test_cycles_and_self_loops_do_not_repeat_nodes(self):
        spec = chain()
        spec["edges"] += [["critical", "entry"], ["bridge", "bridge"]]
        result = netmc.simulate(spec, 20)
        self.assertEqual(result["expected_compromised"], 3)
        self.assertEqual(result["top_paths"][0]["nodes"], ["entry", "bridge", "critical"])

    def test_multiple_entry_and_critical_nodes_preserve_causal_chains(self):
        spec = {"nodes": [{"id": 7, "entry": True, "p_fail": 1, "critical": True},
                          {"id": "root", "entry": True, "p_fail": 1},
                          {"id": "sink", "critical": True}],
                "edges": [[7, "sink"], ["root", "sink"]]}
        result = netmc.simulate(spec, 4)
        self.assertEqual(result["critical_nodes"], [7, "sink"])
        self.assertEqual(result["entry_nodes"], [7, "root"])
        self.assertEqual([p["nodes"] for p in result["top_paths"]], [[7], [7, "sink"]])
        self.assertEqual(result["top_critical_outcomes"][0]["nodes"], [7, "sink"])

    def test_seed_reproducibility_and_global_rng_isolation(self):
        spec = chain(0.37)
        state = random.getstate()
        for operation in (netmc.simulate, netmc.defense_impact, netmc.edge_hardening):
            self.assertEqual(operation(spec, 100, seed=9), operation(spec, 100, seed=9))
            operation(spec, 5)
            self.assertEqual(random.getstate(), state)

    def test_estimate_matches_analytic_probability_for_independent_routes(self):
        spec = {"nodes": [{"id": "root", "entry": True, "p_fail": 0.8}, "a", "b",
                          {"id": "sink", "critical": True}],
                "edges": [["root", "a", 0.5], ["a", "sink", 0.4],
                          ["root", "b", 0.3], ["b", "sink", 0.6]]}
        result = netmc.simulate(spec, 30_000, seed=91)
        self.assertAlmostEqual(result["critical_rate"], 0.8 * (1 - (1 - 0.5 * 0.4) * (1 - 0.3 * 0.6)), delta=0.01)
        self.assertAlmostEqual(result["expected_compromised"], sum(result["per_node"].values()), delta=0.0001)
        paths = {tuple(path["nodes"]) for path in result["top_paths"]}
        self.assertEqual(paths, {("root", "a", "sink"), ("root", "b", "sink")})

    def test_confidence_interval_handles_zero_and_all_hits(self):
        zero = netmc.simulate(chain(0), 100)["critical_rate_ci95"]
        one = netmc.simulate(chain(), 100)["critical_rate_ci95"]
        self.assertEqual(zero[0], 0)
        self.assertGreater(zero[1], 0)
        self.assertEqual(one[1], 1)
        self.assertLess(one[0], 1)
        self.assertAlmostEqual(zero[1], 0.036993, places=6)


class DefenseTests(unittest.TestCase):
    def test_chain_hardening_blocks_critical_outcome(self):
        for operation, ranked in ((netmc.defense_impact, "ranked_defenses"),
                                  (netmc.edge_hardening, "ranked_edges")):
            result = operation(chain(), 10, seed=0)
            self.assertEqual(len(result[ranked]), 2)
            for row in result[ranked]:
                self.assertEqual(row["hardened_rate"], 0)
                self.assertEqual(row["risk_reduction"], 1)
                self.assertEqual(row["relative_reduction_pct"], 100)

    def test_removing_a_node_does_not_create_a_new_entry(self):
        spec = chain()
        spec["nodes"][1] = {"id": "bridge", "p_fail": 1}
        result = netmc.defense_impact(spec, 50, seed=5)
        entry = next(row for row in result["ranked_defenses"] if row["node"] == "entry")
        self.assertEqual(entry["hardened_rate"], 0)

    def test_paired_samples_give_exactly_zero_impact_for_unrelated_nodes_and_edges(self):
        spec = chain(0.43)
        spec["nodes"] += [{"id": "unrelated", "entry": True, "p_fail": 0.6}, "dead_end"]
        spec["edges"] += [["unrelated", "dead_end", 0.3]]
        baseline = netmc.simulate(spec, 400, seed=23)["critical_rate"]
        for operation, ranked in ((netmc.defense_impact, "ranked_defenses"),
                                  (netmc.edge_hardening, "ranked_edges")):
            result = operation(spec, 400, seed=23)
            self.assertEqual(result["baseline_critical_rate"], baseline)
            for row in result[ranked]:
                self.assertGreaterEqual(row["risk_reduction"], 0)
                identifier = row.get("node", row.get("source"))
                if identifier in ("unrelated", "dead_end"):
                    self.assertEqual(row["risk_reduction"], 0)
                    self.assertEqual(row["hardened_rate"], baseline)

    def test_rankings_match_exact_enumeration_with_alternate_routes(self):
        for directed in (True, False):
            spec = {"directed": directed,
                    "nodes": [{"id": "root", "entry": True, "p_fail": 0.7},
                              {"id": "bridge"}, {"id": "sink", "critical": True}],
                    "edges": [{"source": "root", "target": "bridge", "p_propagate": 0.6},
                              {"source": "bridge", "target": "sink", "p_propagate": 0.5},
                              {"source": "root", "target": "sink", "p_propagate": 0.2}]}
            baseline = exact_risk(spec)
            nodes = netmc.defense_impact(spec, 15_000, seed=8)
            self.assertAlmostEqual(nodes["baseline_critical_rate"], baseline, delta=0.015)
            for row in nodes["ranked_defenses"]:
                expected = exact_risk(spec, blocked_node=row["node"])
                self.assertAlmostEqual(row["hardened_rate"], expected, delta=0.015)
            edges = netmc.edge_hardening(spec, 15_000, seed=8)
            for row in edges["ranked_edges"]:
                i = next(i for i, e in enumerate(spec["edges"])
                         if (e["source"], e["target"]) == (row["source"], row["target"]))
                self.assertAlmostEqual(row["hardened_rate"], exact_risk(spec, blocked_edge=i), delta=0.015)

    def test_no_critical_nodes_or_candidates_have_honest_summaries(self):
        spec = {"nodes": [{"id": "A", "p_fail": 1}], "edges": [["A", "B"]]}
        for operation in (netmc.defense_impact, netmc.edge_hardening):
            self.assertIn("no tested defense reduced", netmc.describe_defense(operation(spec, 10)))
            self.assertIsNone(operation({}, 5)["top_defense"])
            self.assertEqual(netmc.describe_defense(operation({}, 5)), "No defenses to evaluate.")
        self.assertEqual(netmc.defense_impact({"nodes": [{"id": "A", "critical": True}]}, 5)["nodes_tested"], 0)


class IntegrationTests(unittest.TestCase):
    def test_network_cli_outputs_valid_json_and_seeded_summary(self):
        graph = json.dumps(chain(0.4))
        command = ["sim", "network", "--graph", graph, "--trials", "100", "--seed", "6"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(easy.main(command), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result, netmc.simulate(graph, 100, seed=6))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(easy.main(command + ["--speak"]), 0)
        self.assertEqual(out.getvalue().strip(), netmc.describe(result))

    def test_defense_cli_commands_pass_seed(self):
        for command, operation in (("defend", netmc.defense_impact), ("harden", netmc.edge_hardening)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(easy.main(["sim", command, "--graph", json.dumps(chain(0.4)),
                                           "--trials", "100", "--seed", "6"]), 0)
            payload = out.getvalue()[out.getvalue().index("{"):]
            self.assertEqual(json.loads(payload), operation(chain(0.4), 100, seed=6))

    def test_mcp_exposes_seed_and_propagates_results(self):
        tool = next(t for t in mcp.TOOLS if t["name"] == "pc_netmc")
        self.assertEqual(tool["inputSchema"]["properties"]["seed"], {"type": "integer"})
        for operation, run in (("simulate", netmc.simulate), ("defend", netmc.defense_impact),
                               ("harden", netmc.edge_hardening)):
            result = mcp._mcp_netmc(operation, graph_spec=json.dumps(chain(0.4)), trials=100, seed=6)
            self.assertTrue(result.pop("description"))
            self.assertEqual(result, run(chain(0.4), 100, seed=6))

    def test_mcp_invalid_requests_return_protocol_errors(self):
        for args in ({"trials": 0}, {"trials": -1}, {"seed": "no"},
                     {"graph_file": "other.json"}, {"graph_spec": "[]"}):
            message = {"method": "tools/call", "params": {"name": "pc_netmc", "arguments": {
                "operation": "simulate", "graph_spec": json.dumps(chain()), **args}}}
            result = mcp.rpc(message)
            self.assertTrue(result.get("isError"), result)
            self.assertIn("ValueError", result["content"][0]["text"])

    def test_real_stdio_mcp_returns_seeded_network_result(self):
        message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "pc_netmc", "arguments": {"operation": "simulate",
                "graph_spec": json.dumps(chain()), "trials": 100, "seed": 3}}}
        result = subprocess.run([sys.executable, "-B", "-m", "pcstudio.mcp"],
                                cwd=Path(__file__).resolve().parents[2],
                                input=json.dumps(message) + "\n", capture_output=True,
                                text=True, check=True, timeout=20)
        reply = json.loads(result.stdout)
        payload = json.loads(reply["result"]["content"][0]["text"])
        self.assertEqual(payload["critical_rate"], 1)
        self.assertEqual(payload["seed"], 3)
        self.assertIn("description", payload)


if __name__ == "__main__":
    unittest.main()
