"""Contract tests for open-vocabulary reaction-network discovery."""
from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/Chemistry/OpenVocabularyReactionNetworkDiscovery"
sys.path.insert(0, str(ROOT))

from sle.evaluate import evaluate_candidate
from sle.frontier import load_frozen_wave
from sle.spec import load_task_spec


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _permuted_graph(graph):
    order = list(reversed(range(len(graph["atoms"]))))
    old_to_new = {old: new for new, old in enumerate(order)}
    return {
        "atoms": [graph["atoms"][old] for old in order],
        "bonds": [
            [old_to_new[int(left)], old_to_new[int(right)], int(bond_order)]
            for left, right, bond_order in graph["bonds"]
        ],
    }


class OpenVocabularyReactionNetworkDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = _load(TASK / "verification/evaluator.py", "open_network_oracle")
        cls.baseline = _load(TASK / "solution.py", "open_network_baseline")

    def test_always_abstain_is_valid_and_normalized_to_exactly_zero(self):
        result = self.evaluator.evaluate(self.baseline.discover_reaction_network)
        self.assertEqual(result["valid"], 1.0)
        self.assertEqual(result["combined_score"], 0.0)
        self.assertEqual(result["development_mechanism_score"], 0.0)
        self.assertEqual(result["development_correct_refusal_rate"], 1.0)
        self.assertEqual(result["development_calibrated_refusal_score"], 1.0)
        self.assertEqual(result["development_attempted_discovery_rate"], 0.0)

    def test_truth_blind_enumeration_witness_recovers_networks_without_false_edges(self):
        first = self.evaluator.evaluate(self.evaluator._reference_policy)
        second = self.evaluator.evaluate(self.evaluator._reference_policy)
        self.assertEqual(first, second)
        self.assertEqual(first["valid"], 1.0)
        self.assertAlmostEqual(first["combined_score"], 1.0, places=12)
        self.assertAlmostEqual(first["development_mechanism_recovery"], 1.0, places=12)
        self.assertEqual(first["development_false_discovery_rate"], 0.0)
        self.assertEqual(first["development_correct_refusal_rate"], 1.0)
        self.assertEqual(first["development_calibrated_refusal_score"], 1.0)
        self.assertEqual(first["development_attempted_discovery_rate"], 1.0)

    def test_probe_accepts_a_constructed_species_not_presented_as_a_candidate(self):
        saw_novel_probe = []

        def probe_novel_then_decline(problem, probe):
            self.assertNotIn("candidate_species", problem)
            self.assertNotIn("candidate_reactions", problem)
            seed_key = self.evaluator._canonical_graph(problem["seed_species"][0])
            graphs = self.evaluator._enumerate_species_graphs(problem["atom_inventory"])
            novel = next(
                graph for key, graph in graphs.items()
                if key != seed_key and self.evaluator._bond_exchange(seed_key, key)[0]
            )
            response = probe({"reactant": problem["seed_species"][0], "product": novel})
            saw_novel_probe.append(response["status"])
            return {"abstain": True, "confidence": 0.0}

        result = self.evaluator.evaluate(probe_novel_then_decline)
        self.assertEqual(result["valid"], 1.0)
        self.assertTrue(saw_novel_probe)
        self.assertGreater(result["development_mean_probe_calls"], 0.0)

    def test_isomorphic_species_duplicates_fail_closed(self):
        def duplicate_species(problem, _probe):
            seed = problem["seed_species"][0]
            return {
                "species": [seed, _permuted_graph(seed)],
                "reactions": [{
                    "reactant": 0,
                    "product": 1,
                    "activation_energy": 60.0,
                }],
                "abstain": False,
                "confidence": 0.5,
            }

        result = self.evaluator.evaluate(duplicate_species)
        self.assertEqual(result["valid"], 0.0)
        self.assertEqual(result["combined_score"], 0.0)
        self.assertTrue(all(not row["valid"] for row in result["per_instance"]))

    def test_elementary_edge_is_invariant_to_joint_repeated_atom_mapping(self):
        left = "C,C,N,O|001101"
        right = "C,C,N,O|010110"
        self.assertTrue(self.evaluator._bond_exchange(left, right)[0])

    def test_fdr_uses_claimed_edges_as_its_denominator(self):
        calls = {"count": 0}
        first_spec = self.evaluator.DEVELOPMENT_SPECS[0]
        graphs, truth = self.evaluator._truth(first_spec)
        false_edge = next(
            (left, right)
            for left in graphs for right in graphs
            if left != right
            and self.evaluator._bond_exchange(left, right)[0]
            and (left, right) not in truth
        )

        def one_false_claim_then_decline(_problem, _probe):
            calls["count"] += 1
            if calls["count"] > 1:
                return {"abstain": True, "confidence": 0.0}
            left, right = false_edge
            return {
                "species": [graphs[left], graphs[right]],
                "reactions": [{
                    "reactant": 0, "product": 1, "activation_energy": 50.0,
                }],
                "abstain": False,
                "confidence": 0.1,
            }

        result = self.evaluator.evaluate(one_false_claim_then_decline)
        self.assertEqual(result["development_claimed_edge_count"], 1.0)
        self.assertEqual(result["development_false_discovery_rate"], 1.0)

    def test_candidate_session_is_reset_between_every_world(self):
        class StatefulCandidate:
            def __init__(self):
                self.calls = 0
                self.resets = 0

            def __call__(self, _problem, _probe):
                self.calls += 1
                return {"abstain": True, "confidence": 0.0}

            def reset_session(self):
                self.resets += 1

        candidate = StatefulCandidate()
        self.evaluator.evaluate(candidate)
        self.assertEqual(candidate.calls, 11)
        self.assertEqual(candidate.resets, 10)

    def test_bad_candidates_never_escape_or_receive_credit(self):
        bad_candidates = (
            lambda *_args: None,
            lambda *_args: {"abstain": "yes", "confidence": 0.0},
            lambda *_args: {"abstain": True, "confidence": math.nan},
        )

        def raises(*_args):
            raise RuntimeError("candidate bug")

        for candidate in (*bad_candidates, raises):
            with self.subTest(candidate=candidate):
                result = self.evaluator.evaluate(candidate)
                self.assertEqual(result["valid"], 0.0)
                self.assertEqual(result["combined_score"], 0.0)

    def test_a_caught_probe_budget_violation_still_fails_closed(self):
        def catches_violation(problem, probe):
            seed_key = self.evaluator._canonical_graph(problem["seed_species"][0])
            graphs = self.evaluator._enumerate_species_graphs(problem["atom_inventory"])
            novel = next(
                graph for key, graph in graphs.items()
                if key != seed_key and self.evaluator._bond_exchange(seed_key, key)[0]
            )
            proposal = {"reactant": problem["seed_species"][0], "product": novel}
            for _ in range(problem["probe_budget"] + 1):
                try:
                    probe(proposal)
                except ValueError:
                    pass
            return {"abstain": True, "confidence": 0.0}

        result = self.evaluator.evaluate(catches_violation)
        self.assertEqual(result["valid"], 0.0)
        self.assertEqual(result["combined_score"], 0.0)

    def test_verified_edges_emit_canonical_frontier_records(self):
        result = self.evaluator.evaluate(self.evaluator._reference_policy)
        records = result["frontier_records"]
        self.assertTrue(records)
        self.assertEqual(len(records), len({row["canonical_id"] for row in records}))
        self.assertTrue(all(
            row["canonical_id"].startswith(
                "sle/open-vocabulary-reaction-network/edge/v1:sha256:"
            )
            for row in records
        ))

    def test_frontier_identity_ignores_acquisition_seed_only(self):
        canonicalizer = self.evaluator._CANONICALIZER
        base = {
            "favoured_pair": ["C", "N"],
            "barrier_offset": -2.0,
            "barrier_limit": 56.0,
            "seed_index": 0,
        }
        other_seed = {**base, "seed_index": 17}
        edge = ("C,C,N,O|001101", "C,C,N,O|010110")
        self.assertEqual(
            canonicalizer.canonical_reaction_id(base, *edge),
            canonicalizer.canonical_reaction_id(other_seed, *edge),
        )

    def test_machine_readable_panel_is_the_evaluator_source(self):
        panel = json.loads((
            TASK / "frontier_eval/contracts/evaluation_panel_v1.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(self.evaluator.ATOM_INVENTORY, tuple(panel["grammar"]["atom_inventory"]))
        self.assertEqual(self.evaluator.PROBE_BUDGET, panel["resource_limits"]["probe_calls_per_world"])
        self.assertEqual(
            [dict(spec) for spec in self.evaluator.WORLD_SPECS],
            [
                {**row, "favoured_pair": tuple(row["favoured_pair"])}
                for row in panel["worlds"]
            ],
        )

    def test_standalone_runner_keeps_oracle_out_of_candidate_modules(self):
        candidate_source = '''
import sys


def discover_reaction_network(problem, probe):
    leaked = any(
        name == "evaluator"
        or "/verification/evaluator.py" in str(getattr(module, "__file__", ""))
        for name, module in sys.modules.items()
    )
    result = {"abstain": True, "confidence": 0.0}
    if leaked:
        result["oracle_leak"] = True
    return result
'''
        with TemporaryDirectory() as temporary_directory:
            candidate_path = Path(temporary_directory) / "candidate.py"
            metrics_path = Path(temporary_directory) / "metrics.json"
            candidate_path.write_text(candidate_source, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(TASK / "frontier_eval/run_eval.py"),
                    "--candidate",
                    str(candidate_path),
                    "--metrics-out",
                    str(metrics_path),
                ],
                cwd=TASK,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.assertEqual(metrics["valid"], 1.0)
            self.assertEqual(metrics["combined_score"], 0.0)

    def test_wave_hashes_load_and_baseline_uses_isolated_candidate_protocol(self):
        spec = load_task_spec(TASK)
        wave = load_frozen_wave(spec)
        self.assertEqual(wave.wave_id, "open-graph-edge-discovery-v1")
        metrics = evaluate_candidate(spec, TASK / "solution.py", timeout_s=20)
        self.assertNotIn("infrastructure_failure", metrics)
        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["combined_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
