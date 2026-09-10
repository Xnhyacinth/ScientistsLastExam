"""Certificate pins for AffineLoopRankingCertificate."""
from __future__ import annotations

import importlib.util
import sys
import unittest
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
        cls.lp = _load(ROOT / "tests/affine_ranking_lp.py", "affine_ranking_lp")

    def test_public_instances_do_not_disclose_the_score_one_optimum(self):
        for instance in self.evaluator.INSTANCES:
            published = self.evaluator.public_instance(instance)
            self.assertNotIn("optimal_delta", published)
            self.assertNotIn("nonneg_lambdas", published)
            self.assertNotIn("decrease_lambdas", published)

    def test_guards_are_overcomplete_and_not_coordinate_axes(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            guards = self.evaluator._parse_guards(instance["guards"], n)
            self.assertGreater(len(guards), n)
            for slope, _ in guards:
                ones = sum(1 for item in slope if item == 1)
                zeros = sum(1 for item in slope if item == 0)
                self.assertFalse(ones == 1 and zeros == n - 1 and sum(slope) == 1)

    def test_instances_require_state_dependent_decrease(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            a = self.evaluator._matrix(instance["A"], "A", n, n)
            self.assertTrue(any(a[i][j] != int(i == j) for i in range(n) for j in range(n)))
            self.assertTrue(any(a[i][j] < 0 for i in range(n) for j in range(n)))

    def test_inverse_of_i_minus_at_is_not_a_nonnegative_simplex(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            a = self.evaluator._matrix(instance["A"], "A", n, n)
            matrix = [[Fraction(i == j) - a[j][i] for j in range(n)] for i in range(n)]
            inverse = [row[:] + [Fraction(i == j) for j in range(n)]
                       for i, row in enumerate(matrix)]
            for k in range(n):
                pivot = next(i for i in range(k, n) if inverse[i][k])
                inverse[k], inverse[pivot] = inverse[pivot], inverse[k]
                scale = inverse[k][k]
                inverse[k] = [value / scale for value in inverse[k]]
                for i in range(n):
                    if i != k:
                        scale = inverse[i][k]
                        inverse[i] = [x - scale * y for x, y in zip(inverse[i], inverse[k])]
            self.assertTrue(any(inverse[i][n + j] < 0 for i in range(n) for j in range(n)))

    def test_farkas_multipliers_are_not_unique_functions_of_r(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            m = len(instance["guards"])
            r = [Fraction(1, n)] * n
            pairwise = [Fraction(1, 2 * n)] * n + [Fraction(0)] * (m - n)
            rotated = [Fraction(0)] * n + [Fraction(1, 3 * n)] * n
            self.assertNotEqual(pairwise, rotated)
            guards = self.evaluator._parse_guards(instance["guards"], n)
            self.assertTrue(self.evaluator._farkas(r, Fraction(0), guards, pairwise))
            self.assertTrue(self.evaluator._farkas(r, Fraction(0), guards, rotated))

    def test_axis_enumeration_cannot_certify_the_coupled_transition(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            m = len(instance["guards"])
            guards = self.evaluator._parse_guards(instance["guards"], n)
            a = self.evaluator._matrix(instance["A"], "A", n, n)
            b = self.evaluator._vector(instance["b"], "b", n)
            for j in range(n):
                r = [Fraction(i == j) for i in range(n)]
                lam = r + [Fraction(0)] * (m - n)
                mu = [r[k] - sum(a[i][k] * r[i] for i in range(n)) for k in range(n)]
                mu = mu + [Fraction(0)] * (m - n)
                holds, _ = self.evaluator.certificate_holds(
                    guards, a, b, r, Fraction(0), Fraction(1, 10000), lam, mu
                )
                self.assertFalse(holds)

    def test_inverse_column_enum_does_not_reach_score_one(self):
        reference = self.evaluator.evaluate(self.reference.build_ranking)
        metrics = self.evaluator.evaluate(self.probe.build_ranking)
        self.assertNotEqual(metrics["combined_score"], 1.0)
        self.assertLess(metrics["combined_score"], reference["combined_score"])
        self.assertLess(metrics["feasibility_rate"], 1.0)

    def test_stored_optima_match_an_independent_exact_farkas_lp(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            guards = self.evaluator._parse_guards(instance["guards"], n)
            a = self.evaluator._matrix(instance["A"], "A", n, n)
            b = self.evaluator._vector(instance["b"], "b", n)
            witness = self.lp.exact_maximum_delta(guards, a, b)
            self.assertEqual(witness["delta"], Fraction(*instance["optimal_delta"]))
            holds, reason = self.evaluator.certificate_holds(
                guards, a, b, witness["r"], witness["s"], witness["delta"],
                witness["nonneg_lambdas"], witness["decrease_lambdas"],
            )
            self.assertTrue(holds, reason)
            self.assertTrue(any(x > 0 for x in witness["decrease_lambdas"]))

        def lp_ranking(instance):
            hidden = next(item for item in self.evaluator.INSTANCES
                           if item["name"] == instance["name"])
            n = hidden["dimension"]
            guards = self.evaluator._parse_guards(hidden["guards"], n)
            a = self.evaluator._matrix(hidden["A"], "A", n, n)
            b = self.evaluator._vector(hidden["b"], "b", n)
            witness = self.lp.exact_maximum_delta(guards, a, b)
            ratio = lambda x: [x.numerator, x.denominator]
            return {
                "r": [ratio(x) for x in witness["r"]],
                "s": ratio(witness["s"]),
                "delta": ratio(witness["delta"]),
                "nonneg_lambdas": [ratio(x) for x in witness["nonneg_lambdas"]],
                "decrease_lambdas": [ratio(x) for x in witness["decrease_lambdas"]],
            }

        metrics = self.evaluator.evaluate(lp_ranking)
        self.assertEqual(metrics["feasibility_rate"], 1.0)
        self.assertEqual(metrics["combined_score"], 1.0)

    def test_floats_are_rejected_and_score_zero(self):
        def floats(instance):
            dimension = int(instance["dimension"])
            n_guards = len(instance["guards"])
            return {
                "r": [1.0] + [0.0] * (dimension - 1),
                "s": 0.0,
                "delta": 0.0001,
                "nonneg_lambdas": [1.0] + [0.0] * (n_guards - 1),
                "decrease_lambdas": [0.0] * n_guards,
            }

        metrics = self.evaluator.evaluate(floats)
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_uniform_baseline_is_valid_and_below_the_reference(self):
        baseline = self.evaluator.evaluate(self.baseline.build_ranking)
        reference = self.evaluator.evaluate(self.reference.build_ranking)
        self.assertEqual(baseline["valid"], 1.0)
        self.assertEqual(reference["valid"], 1.0)
        self.assertLess(baseline["combined_score"], reference["combined_score"])
        self.assertEqual(baseline["combined_score"], 0.0)
        self.assertGreater(reference["combined_score"], 0.3)
        self.assertLess(reference["combined_score"], 0.8)

    def test_malformed_submissions_score_zero_without_raising(self):
        metrics = self.evaluator.evaluate(lambda *_args: "not a mapping")
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_this_is_not_a_lyapunov_ode_or_a_distance_graph(self):
        from sle.registry import find_task
        spec = find_task(
            "ScientificComputing/AffineLoopRankingCertificate", include_uncertified=True
        )
        graph = find_task("Algorithm/GraphFromDistances", include_uncertified=True)
        self.assertEqual(spec.entrypoint, "build_ranking")
        self.assertNotEqual(spec.task_id, "ControlTheory/LyapunovDecayCertificate")
        self.assertNotEqual(spec.task_dir, graph.task_dir)


if __name__ == "__main__":
    unittest.main()
