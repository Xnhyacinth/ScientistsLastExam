"""Certificate pins for AffineLoopRankingCertificate."""
from __future__ import annotations

import importlib.util
import sys
import unittest
import json
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

    def test_instances_require_state_dependent_decrease(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            a = self.evaluator._matrix(instance["A"], "A", n, n)
            self.assertTrue(any(a[i][j] != int(i == j) for i in range(n) for j in range(n)))

    def test_axis_enumeration_cannot_certify_the_coupled_transition(self):
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            guards = self.evaluator._parse_guards(instance["guards"], n)
            a = self.evaluator._matrix(instance["A"], "A", n, n)
            b = self.evaluator._vector(instance["b"], "b", n)
            for j in range(n):
                r = [Fraction(i == j) for i in range(n)]
                mu = [r[k] - sum(a[i][k] * r[i] for i in range(n)) for k in range(n)]
                holds, _ = self.evaluator.certificate_holds(guards, a, b, r, Fraction(0), Fraction(1,10000), r, mu)
                self.assertFalse(holds)

    def test_exact_optima_have_nonzero_decrease_certificates(self):
        witnesses = json.loads((TASK / "references/known_optima.json").read_text())
        metrics = self.evaluator.evaluate(lambda p: witnesses[p["name"]])
        self.assertEqual(metrics["feasibility_rate"], 1.0)
        self.assertEqual(metrics["combined_score"], 1.0)
        for witness in witnesses.values():
            self.assertTrue(any(Fraction(*x) > 0 for x in witness["decrease_lambdas"]))

    def test_score_one_is_the_exact_farkas_lp_optimum(self):
        def solve(matrix, rhs):
            work = [list(row) + [value] for row, value in zip(matrix, rhs)]
            n = len(rhs)
            for k in range(n):
                pivot = next(i for i in range(k,n) if work[i][k])
                work[k], work[pivot] = work[pivot], work[k]
                scale = work[k][k]
                work[k] = [value / scale for value in work[k]]
                for i in range(n):
                    if i != k:
                        scale = work[i][k]
                        work[i] = [x - scale*y for x,y in zip(work[i],work[k])]
            return [row[-1] for row in work]
        for instance in self.evaluator.INSTANCES:
            n = instance["dimension"]
            a = self.evaluator._matrix(instance["A"], "A", n,n)
            b = self.evaluator._vector(instance["b"], "b", n)
            m = [[Fraction(i == j)-a[j][i] for j in range(n)] for i in range(n)]
            objective = [1-sum(row)-shift for row,shift in zip(a,b)]
            rays = [solve(m,[Fraction(i == j) for i in range(n)]) for j in range(n)]
            self.assertTrue(all(x >= 0 for ray in rays for x in ray))
            bounds = [sum(x*c for x,c in zip(ray,objective))/sum(ray) for ray in rays]
            self.assertEqual(max(bounds), Fraction(*instance["optimal_delta"]))

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
        self.assertGreater(reference["combined_score"], 0.5)
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
