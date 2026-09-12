"""Certificate pins for AffineLoopRankingCertificate."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TASK = ROOT / "benchmarks/ComputerScience/AffineLoopRankingCertificate"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AffineLoopRankingCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = _load(TASK / "verification/evaluator.py", "ranking_oracle")
        cls.baseline = _load(TASK / "solution.py", "ranking_baseline")
        cls.reference = _load(
            TASK / "verification/reference_ranking.py", "ranking_reference"
        )
        cls.probe = _load(TASK / "references/inverse_column_probe.py", "inverse_probe")
        cls.lp = _load(TASK / "references/phase_lp_probe.py", "affine_ranking_lp")

    def test_lp_execution_failure_is_not_infeasibility_evidence(self):
        instance = self.evaluator.INSTANCES[0]
        transitions = self.evaluator._parse_transitions(instance["transitions"], instance["dimension"])
        with patch.object(self.lp, "linprog", return_value=SimpleNamespace(
                success=False, message="iteration limit", status=1)):
            with self.assertRaisesRegex(RuntimeError, "iteration limit"):
                self.lp.exact_maximum_delta(transitions)

    def test_public_instances_do_not_disclose_the_score_one_optimum(self):
        for instance in self.evaluator.INSTANCES:
            published = self.evaluator.public_instance(instance)
            self.assertNotIn("score_one_quality", published)
            self.assertNotIn("optimal_delta", published)
            self.assertNotIn("n_levels", published)

    def test_progressing_guards_are_overcomplete_and_not_coordinate_axes(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            depth = len(instance["transitions"])
            width = n // depth
            inner = instance["transitions"][0]
            guards = self.evaluator._parse_guards(inner["guards"], n)
            self.assertGreater(len(guards), width)
            for slope, _ in guards:
                ones = sum(1 for item in slope if item == 1)
                zeros = sum(1 for item in slope if item == 0)
                self.assertFalse(ones == 1 and zeros == n - 1 and sum(slope) == 1)

    def test_progressing_blocks_are_mixed_sign_and_not_identity(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            inner = instance["transitions"][0]
            a = self.evaluator._matrix(inner["A"], "A", n, n)
            self.assertTrue(any(a[i][j] != int(i == j) for i in range(n) for j in range(n)))
            self.assertTrue(any(a[i][j] < 0 for i in range(n) for j in range(n)))

    def test_instances_are_not_one_ranking_complete(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            transitions = self.evaluator._parse_transitions(instance["transitions"], n)
            witness = self.lp.exact_maximum_delta(transitions)
            self.assertEqual(witness["delta"], 0)
            self.assertEqual(witness["upper_bound"], 0)

    def test_inverse_column_enum_does_not_reach_score_one(self):
        reference = self.evaluator.evaluate(self.reference.build_ranking)
        metrics = self.evaluator.evaluate(self.probe.build_ranking)
        self.assertNotEqual(metrics["combined_score"], 1.0)
        self.assertLess(metrics["combined_score"], reference["combined_score"])
        self.assertLess(metrics["feasibility_rate"], 1.0)

    def test_one_ranking_farkas_lp_does_not_reach_score_one(self):
        reference = self.evaluator.evaluate(self.reference.build_ranking)

        def lp_ranking(instance):
            return self.lp.one_ranking_as_lex(instance, self.evaluator)

        metrics = self.evaluator.evaluate(lp_ranking)
        self.assertLess(metrics["combined_score"], 1.0)
        self.assertLess(metrics["combined_score"], reference["combined_score"])
        self.assertNotEqual(metrics["combined_score"], 1.0)

    def test_hidden_ceiling_matches_the_verified_phase_lex_ranking(self):
        metrics = self.evaluator.evaluate(self.lp.phase_lex_ranking)
        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["feasibility_rate"], 1.0)
        self.assertEqual(metrics["combined_score"], 1.0)
        for row, instance in zip(metrics["per_instance"], self.evaluator.INSTANCES):
            self.assertEqual(row["proven_quality"], list(instance["score_one_quality"]))

    def test_floats_are_rejected_and_score_zero(self):
        def floats(instance):
            dimension = int(instance["dimension"])
            n_guards = len(instance["transitions"][0]["guards"])
            return {
                "components": [{
                    "r": [1.0] + [0.0] * (dimension - 1),
                    "s": 0.0,
                    "delta": 0.0001,
                }],
                "decrease_index": [0] * len(instance["transitions"]),
                "nonneg_lambdas": [[[1.0] + [0.0] * (n_guards - 1)]],
                "decrease_lambdas": [[[0.0] * n_guards]],
            }

        metrics = self.evaluator.evaluate(floats)
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_uniform_search_ablation_is_below_the_reference(self):
        def uniform_honest(instance):
            depth, width = self.reference._levels(instance)
            decrease_index = list(range(depth - 1, -1, -1))
            chosen = []
            for level in range(depth):
                ranking = self.reference._block_vector(
                    depth, width, level, [Fraction(1, width)] * width)
                t_index = next(i for i, active in enumerate(decrease_index) if active == level)
                witness = self.reference._honest_delta(
                    ranking, instance["transitions"][t_index])
                chosen.append({"r": ranking, **witness})
            components = [{
                "r": [[x.numerator, x.denominator] for x in item["r"]],
                "s": [item["s"].numerator, item["s"].denominator],
                "delta": [item["delta"].numerator, item["delta"].denominator],
            } for item in chosen]
            nonneg = []
            decrease = []
            for t_index, trans in enumerate(instance["transitions"]):
                active = decrease_index[t_index]
                lam_row = []
                mu_row = []
                for level in range(depth):
                    if level > active:
                        zeros = [[0, 1]] * len(trans["guards"])
                        lam_row.append(zeros)
                        mu_row.append(zeros)
                        continue
                    witness = self.reference._honest_delta(chosen[level]["r"], trans)
                    lam_row.append([[x.numerator, x.denominator] for x in witness["lam"]])
                    mu_row.append([[x.numerator, x.denominator] for x in witness["mu"]])
                nonneg.append(lam_row)
                decrease.append(mu_row)
            return {
                "components": components,
                "decrease_index": decrease_index,
                "nonneg_lambdas": nonneg,
                "decrease_lambdas": decrease,
            }

        ablation = self.evaluator.evaluate(uniform_honest)
        reference = self.evaluator.evaluate(self.reference.build_ranking)
        self.assertEqual(ablation["valid"], 1.0)
        self.assertEqual(reference["valid"], 1.0)
        self.assertLess(ablation["combined_score"], reference["combined_score"])
        self.assertGreater(ablation["combined_score"], 0.5)
        self.assertLess(reference["combined_score"], 1.0)

    def test_uniform_baseline_is_valid_and_below_the_reference(self):
        baseline = self.evaluator.evaluate(self.baseline.build_ranking)
        reference = self.evaluator.evaluate(self.reference.build_ranking)
        self.assertEqual(baseline["valid"], 1.0)
        self.assertEqual(reference["valid"], 1.0)
        self.assertLess(baseline["combined_score"], reference["combined_score"])
        self.assertEqual(baseline["combined_score"], 0.0)
        self.assertGreater(reference["combined_score"], 0.5)
        self.assertLess(reference["combined_score"], 1.0)

    def test_valid_requires_every_instance(self):
        def fail_last(instance):
            if instance["name"] == self.evaluator.INSTANCES[-1]["name"]:
                return {"components": []}
            return self.baseline.build_ranking(instance)

        metrics = self.evaluator.evaluate(fail_last)
        self.assertGreater(metrics["feasibility_rate"], 0.0)
        self.assertLess(metrics["feasibility_rate"], 1.0)
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_malformed_submissions_score_zero_without_raising(self):
        metrics = self.evaluator.evaluate(lambda *_args: "not a mapping")
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_this_is_not_a_packing_bell_or_capacity_certificate(self):
        from sle.registry import find_task
        spec = find_task(
            "ScientificComputing/AffineLoopRankingCertificate", include_uncertified=True
        )
        packing = find_task("DiscreteGeometry/SpherePackingCertificate", include_uncertified=True)
        bell = find_task("QuantumFoundations/BellBoundCertificate", include_uncertified=True)
        shannon = find_task("InformationTheory/ShannonCapacityCertificate", include_uncertified=True)
        graph = find_task("Algorithm/GraphFromDistances", include_uncertified=True)
        self.assertEqual(spec.entrypoint, "build_ranking")
        self.assertNotEqual(spec.task_id, packing.task_id)
        self.assertNotEqual(spec.task_id, bell.task_id)
        self.assertNotEqual(spec.task_id, shannon.task_id)
        self.assertNotEqual(spec.task_dir, graph.task_dir)


if __name__ == "__main__":
    unittest.main()
