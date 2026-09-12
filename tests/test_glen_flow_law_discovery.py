"""Discovery-contract pins for GlenFlowLawDiscovery."""
from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TASK = ROOT / "benchmarks/EarthScience/GlenFlowLawDiscovery"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GlenFlowLawDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = _load(TASK / "verification/evaluator.py", "glen_oracle")
        cls.baseline = _load(TASK / "solution.py", "glen_baseline")
        cls.reference = _load(
            TASK / "verification/reference_flow.py", "glen_reference"
        )

    def test_glen_exponent_is_a_world_parameter(self):
        spec = {"kind": "glen", "A": 2e-7, "n": 2.7}
        observed = math.log(self.evaluator.true_speed(spec, 200) / self.evaluator.true_speed(spec, 20)) / math.log(10)
        self.assertAlmostEqual(observed, 2.7)

    def test_glen_is_cubic_and_sliding_curves_the_log_log_slope(self):
        glen = {"kind": "glen", "A": 2.0e-7}
        newtonian = {"kind": "newtonian", "A": 0.012}
        sliding = {"kind": "sliding", "A": 1.0e-5, "C": 0.05}
        taus = (20.0, 80.0, 200.0)
        def slope(spec, left, right):
            y_left = math.log(self.evaluator.true_speed(spec, left))
            y_right = math.log(self.evaluator.true_speed(spec, right))
            return (y_right - y_left) / (math.log(right) - math.log(left))
        self.assertAlmostEqual(slope(glen, *taus[:2]), 3.0, places=6)
        self.assertAlmostEqual(slope(newtonian, *taus[:2]), 1.0, places=6)
        self.assertGreater(
            abs(slope(sliding, taus[1], taus[2]) - slope(sliding, taus[0], taus[1])),
            0.4,
        )

    def test_gbs_is_a_supported_power_law_near_n_1_8(self):
        spec = {"kind": "gbs", "A": 1.0e-5, "n": 1.8}
        observed = math.log(self.evaluator.true_speed(spec, 200) / self.evaluator.true_speed(spec, 20)) / math.log(10)
        self.assertAlmostEqual(observed, 1.8)
        self.assertIn("gbs", self.evaluator.SUPPORTED)
        self.assertIn("gbs", self.evaluator.PUBLIC_PROBLEM["family_names"])

    def test_stress_dependent_n_curves_log_log_for_a_different_reason_than_sliding(self):
        spec = {
            "kind": "variable_n", "A": 1.5e-7, "n0": 3.0, "k": 0.20,
            "tau0": 63.245553203367585, "activation_temperature": 5600.0,
        }
        lo, hi = self.evaluator.TAU_BOUNDS
        mid = math.sqrt(lo * hi)
        y = [math.log(self.evaluator.true_speed(spec, tau)) for tau in (lo, mid, hi)]
        curvature = (y[2] - 2 * y[1] + y[0]) / math.log(mid / lo)
        self.assertGreater(curvature, 0.1)
        self.assertLess(curvature, 0.3)
        self.assertNotIn("variable_n", self.evaluator.SUPPORTED)
        local = math.log(self.evaluator.true_speed(spec, 200) / self.evaluator.true_speed(spec, 80)) / math.log(200 / 80)
        self.assertGreater(abs(local - 3.0), 0.1)

    def test_former_weak_sliding_worlds_have_resolvable_curvature(self):
        lo, hi = self.evaluator.TAU_BOUNDS
        mid = math.sqrt(lo * hi)
        for worlds in [self.evaluator.DEVELOPMENT_WORLDS, self.evaluator.HELDOUT_WORLDS]:
            spec = next(w for w in worlds if w["seed"] in (72003,82003))
            y = [math.log(self.evaluator.true_speed(spec,tau)) for tau in (lo,mid,hi)]
            curvature = (y[2] - 2*y[1] + y[0]) / math.log(mid/lo)
            self.assertGreater(curvature, 0.1)
            self.assertLess(curvature, 0.3)

    def test_sliding_carries_the_same_arrhenius_factor_as_creep(self):
        spec = {"kind": "sliding", "A": 1.0e-5, "C": 0.05, "activation_temperature": 4800.0}
        ratio_low = self.evaluator.true_speed(spec, 20, 265) / self.evaluator.true_speed(spec, 20, 245)
        ratio_high = self.evaluator.true_speed(spec, 200, 265) / self.evaluator.true_speed(spec, 200, 245)
        self.assertAlmostEqual(ratio_low, ratio_high, places=12)
        glen = {"kind": "glen", "A": 2.0e-7, "n": 3.0, "activation_temperature": 4800.0}
        self.assertAlmostEqual(
            ratio_low,
            self.evaluator.true_speed(glen, 100, 265) / self.evaluator.true_speed(glen, 100, 245),
            places=12,
        )

    def test_temperature_response_and_parameter_denominators_are_reported(self):
        metrics = self.evaluator.evaluate(self.reference.identify_flow_law)
        self.assertEqual(metrics["development_supported_count"], 5)
        self.assertEqual(metrics["development_unsupported_count"], 6)
        spec = self.evaluator.DEVELOPMENT_WORLDS[0]
        self.assertGreater(self.evaluator.true_speed(spec,100,265), self.evaluator.true_speed(spec,100,245))

    def test_full_abstention_is_valid_and_scores_zero(self):
        metrics = self.evaluator.evaluate(
            lambda _problem, _measure: {"abstain": True}
        )
        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["combined_score"], 0.0)
        self.assertEqual(metrics["development_correct_refusal_rate"], 1.0)
        self.assertEqual(metrics["development_discovery_coverage"], 0.0)

    def test_the_newtonian_baseline_is_valid_and_below_the_reference(self):
        baseline = self.evaluator.evaluate(self.baseline.identify_flow_law)
        reference = self.evaluator.evaluate(self.reference.identify_flow_law)
        self.assertEqual(baseline["valid"], 1.0)
        self.assertEqual(reference["valid"], 1.0)
        self.assertLess(baseline["combined_score"], reference["combined_score"])
        self.assertEqual(baseline["combined_score"], 0.0)
        self.assertEqual(baseline["development_false_discovery_rate"], 1.0)
        self.assertGreater(reference["combined_score"], 0.3)
        self.assertGreater(reference["development_signal_recovery_rate"], 0.5)
        self.assertEqual(reference["development_false_discovery_rate"], 0.0)
        self.assertEqual(reference["development_correct_refusal_rate"], 1.0)
        self.assertEqual(reference["development_discovery_coverage"], 1.0)

    def test_complete_reference_recovers_the_public_gbs_family(self):
        reference = self.evaluator.evaluate(self.reference.identify_flow_law)
        gbs_rows = [row for row in reference["per_instance"] if row["kind"] == "gbs"]
        self.assertGreaterEqual(len(gbs_rows), 3)
        for row in gbs_rows:
            self.assertGreater(row["mechanism_score"], 0.8)
            self.assertFalse(row["abstained"])

    def test_blanket_refusal_does_not_claim_perfect_confidence_calibration(self):
        result = self.evaluator.evaluate(lambda *_: {"abstain": True, "confidence": 0.0})
        self.assertEqual(result["development_confidence_calibration"], 6 / 11)
        self.assertEqual(result["heldout_confidence_calibration"], 5 / 8)

    def test_reference_meets_difficulty_admission_band(self):
        # Keep the original scientific gate. The draft must remain blocked until a
        # substantive redesign passes it, independently of functional correctness.
        reference = self.evaluator.evaluate(self.reference.identify_flow_law)
        self.assertGreater(reference["combined_score"], 0.3)
        self.assertLess(reference["combined_score"], 0.8)

    def test_malformed_submissions_score_zero_without_raising(self):
        metrics = self.evaluator.evaluate(lambda *_args: {"abstain": True, "confidence": 1.1})
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_published_mechanism_scores_have_six_decimal_precision(self):
        result = self.evaluator.evaluate(self.reference.identify_flow_law)
        for key in ("combined_score", "development_mechanism_score", "heldout_mechanism_score"):
            self.assertEqual(result[key], round(result[key], 6))

    def test_one_malformed_development_world_invalidates_submission(self):
        calls = 0
        def candidate(problem, measure):
            nonlocal calls
            calls += 1
            if calls == 1:
                return {"abstain": True, "confidence": 1.1}
            return self.reference.identify_flow_law(problem, measure)
        result = self.evaluator.evaluate(candidate)
        self.assertEqual(result["valid"], 0.0)
        self.assertEqual(result["combined_score"], 0.0)

    def test_this_is_not_an_amoc_fold_or_a_wall_closure(self):
        from sle.registry import find_task
        spec = find_task("Glaciology/GlenFlowLawDiscovery", include_uncertified=True)
        amoc = find_task("Oceanography/AMOCTippingRefusal", include_uncertified=True)
        wall = find_task("Turbulence/WallClosureDiscovery", include_uncertified=True)
        self.assertEqual(spec.entrypoint, "identify_flow_law")
        self.assertNotEqual(spec.task_dir, amoc.task_dir)
        self.assertNotEqual(spec.task_dir, wall.task_dir)


if __name__ == "__main__":
    unittest.main()
