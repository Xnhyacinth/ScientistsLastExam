"""Invariants for DiscreteOptimization/MiplibPrimalIncumbent."""
from __future__ import annotations

import importlib.util
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks" / "Engineering" / "MiplibPrimalIncumbent"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR = _load("mip_evaluator", TASK / "verification" / "evaluator.py")
BASELINE = _load("mip_baseline", TASK / "solution.py")


class MiplibPrimalTests(unittest.TestCase):
    def test_parser_rejects_unsupported_mps_sections(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.mps"
            path.write_text("NAME bad\nROWS\n N cost\n L row\nCOLUMNS\n x cost 1 row 1\nRHS\n rhs row 2\nRANGES\n range row 1\nENDATA\n")
            with self.assertRaisesRegex(ValueError, "RANGES"):
                EVALUATOR._parse_mps(path)

    def test_vendored_hashes_and_dimensions_match(self):
        for row in EVALUATOR.INSTANCES:
            model = EVALUATOR._load_model(row)
            self.assertEqual(len(model["columns"]), row["n_variables"], row["name"])
            self.assertEqual(len(model["rhs"]), row["n_constraints"], row["name"])

    def test_baseline_is_feasible_and_scores_exactly_zero(self):
        result = EVALUATOR.evaluate(BASELINE.improve_primal)
        self.assertEqual(result["valid"], 1.0)
        self.assertEqual(result["feasibility_rate"], 1.0)
        self.assertEqual(result["combined_score"], 0.0)

    def test_binary_upper_bounds_are_enforced(self):
        result = EVALUATOR.evaluate(lambda p: [2] + [0] * (p["n_variables"] - 1))
        self.assertEqual(result["valid"], 0.0)
        self.assertIn("upper bound", result["per_instance"][0]["reason"])

    def test_one_queen_is_a_feasible_improvement(self):
        result = EVALUATOR.evaluate(lambda p: [1] + [0] * (p["n_variables"] - 1))
        self.assertEqual(result["valid"], 1.0)
        self.assertAlmostEqual(result["combined_score"], 0.006649, places=6)

    def test_log_gap_scale_from_measured_objectives(self):
        row = EVALUATOR.INSTANCES[0]
        expected = {
            0: 0.0,
            1: 0.006649288648997573,
            35: 0.5175105162781473,
            36: 0.5666065223658276,
            37: 0.6266951775221132,
            38: 0.7041629275170906,
            39: 0.8133475887610566,
            40: 1.0,
        }
        for queens, want in expected.items():
            with self.subTest(queens=queens):
                got = EVALUATOR._instance_score(row, float(-queens))
                self.assertAlmostEqual(got, want, places=9)
        self.assertLess(EVALUATOR._instance_score(row, -36.0), 0.70)
        last_queen = EVALUATOR._instance_score(row, -40.0) - EVALUATOR._instance_score(row, -39.0)
        first_queen = EVALUATOR._instance_score(row, -1.0)
        self.assertGreater(last_queen, first_queen)

    def test_greedy_two_exchange_probe_replays_on_the_log_gap_ruler(self):
        probe = _load(
            "mip_local_search", TASK / "references" / "local_search_probe.py"
        )
        result = EVALUATOR.evaluate(probe.improve_primal)
        self.assertEqual(result["valid"], 1.0)
        self.assertEqual(result["feasibility_rate"], 1.0)
        row = result["per_instance"][0]
        self.assertTrue(row["valid"])
        objective = float(row["objective"])
        queens = int(round(-objective))
        self.assertGreaterEqual(queens, 36)
        self.assertLess(queens, 40)
        self.assertAlmostEqual(result["combined_score"], row["instance_score"], places=6)
        self.assertAlmostEqual(result["combined_score"], 0.704163, places=6)
        # Linear q/40 would put 36 queens at 0.90; the log-gap ruler does not.
        self.assertLess(
            EVALUATOR._instance_score(EVALUATOR.INSTANCES[0], -36.0), 0.70
        )
        self.assertLess(result["combined_score"], 1.0)

    def test_malformed_submissions_score_zero_without_raising(self):
        cases = {
            "none": lambda problem: None,
            "empty": lambda problem: [],
            "raises": lambda problem: (_ for _ in ()).throw(RuntimeError("boom")),
            "too_short": lambda problem: [0],
            "too_long": lambda problem: [0] * (problem["n_variables"] + 1),
            "floats": lambda problem: [0.0] * problem["n_variables"],
            "booleans": lambda problem: [False] * problem["n_variables"],
            "dict": lambda problem: {0: 1},
            "string": lambda problem: "0" * problem["n_variables"],
            "mixed": lambda problem: [0, 1.2] + [0] * (problem["n_variables"] - 2),
            "none_entry": lambda problem: [None] * problem["n_variables"],
            "nested": lambda problem: [[0]] * problem["n_variables"],
        }
        self.assertGreaterEqual(len(cases), 10)
        for name, candidate in cases.items():
            with self.subTest(candidate=name):
                result = EVALUATOR.evaluate(candidate)
                self.assertEqual(result["combined_score"], 0.0)
                self.assertEqual(result["valid"], 0.0)


if __name__ == "__main__":
    unittest.main()
