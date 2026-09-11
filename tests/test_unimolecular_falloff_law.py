"""Discovery-contract pins for UnimolecularFalloffLaw.

The public score is mechanism, normalised so that declining every world is exactly zero.
Two-channel and negative-order worlds are unsupported. A textbook Lindemann claim
therefore scores zero even when the rate is actually Lindemann-like, because those worlds
are published as discoveries on the unsupported set too.
"""
from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TASK = ROOT / "benchmarks/Chemistry/UnimolecularFalloffLaw"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UnimolecularFalloffLawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = _load(TASK / "verification/evaluator.py", "falloff_oracle")
        cls.baseline = _load(TASK / "solution.py", "falloff_baseline")
        cls.reference = _load(
            TASK / "verification/reference_falloff.py", "falloff_reference"
        )

    def test_troe_suppresses_the_mid_falloff_relative_to_lindemann(self):
        lindemann = {
            "kind": "lindemann",
            "A_inf": 2.4e7,
            "E_inf": 2100.0,
            "A0": 4.8e9,
            "E0": 900.0,
        }
        troe = dict(lindemann, kind="troe", Fcent=0.42)
        k_l = self.evaluator.true_k(lindemann, 300.0, 0.03)
        k_t = self.evaluator.true_k(troe, 300.0, 0.03)
        self.assertGreater(k_l, k_t)
        self.assertGreater(self.evaluator.true_k(lindemann, 300.0, 100.0), k_l)

    def test_full_abstention_is_valid_and_scores_zero(self):
        metrics = self.evaluator.evaluate(
            lambda _problem, _measure: {"abstain": True}
        )
        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["combined_score"], 0.0)
        self.assertEqual(metrics["development_correct_refusal_rate"], 1.0)
        self.assertEqual(metrics["development_discovery_coverage"], 0.0)

    def test_the_arrhenius_baseline_is_valid_and_below_the_reference(self):
        baseline = self.evaluator.evaluate(self.baseline.identify_falloff)
        reference = self.evaluator.evaluate(self.reference.identify_falloff)
        self.assertEqual(baseline["valid"], 1.0)
        self.assertEqual(reference["valid"], 1.0)
        self.assertLess(baseline["combined_score"], reference["combined_score"])
        self.assertEqual(baseline["combined_score"], 0.0)
        self.assertEqual(baseline["development_false_discovery_rate"], 1.0)
        self.assertEqual(reference["development_false_discovery_rate"], 0.0)
        self.assertGreater(reference["development_signal_recovery_rate"], 0.5)
        self.assertGreater(reference["development_correct_refusal_rate"], 0.99)

    def test_malformed_submissions_score_zero_without_raising(self):
        metrics = self.evaluator.evaluate(lambda *_args: {"abstain": True, "confidence": 1.1})
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_reference_fits_fcent_from_noiseless_pressure_observations(self):
        base = next(w for w in self.evaluator.DEVELOPMENT_WORLDS if w["kind"] == "troe")
        for fcent in (0.25, 0.65):
            with self.subTest(fcent=fcent):
                world = dict(base, Fcent=fcent)
                calls = []
                def measure(temperature, pressure):
                    calls.append((temperature, pressure))
                    return math.log(self.evaluator.true_k(world, temperature, pressure))
                result = self.reference.identify_falloff(self.evaluator.public_problem(), measure)
                self.assertFalse(result["abstain"])
                self.assertAlmostEqual(result["Fcent"], fcent, places=3)
                self.assertLessEqual(len(calls), self.evaluator.MEASURE_BUDGET)

    def test_full_curve_fit_beats_the_three_assay_counterexample_on_both_splits(self):
        probe = _load(TASK / "references/three_assay_probe.py", "three_assay_probe")
        cheap = self.evaluator.evaluate(probe.identify_falloff)
        full = self.evaluator.evaluate(self.reference.identify_falloff)
        for key in ("combined_score", "heldout_mechanism_score"):
            self.assertGreater(full[key], cheap[key] + 0.05)
        self.assertEqual(full["development_false_discovery_rate"], 0.0)
        self.assertEqual(full["heldout_false_discovery_rate"], 0.0)

    def test_the_measurement_budget_is_not_free(self):
        """The same curve-fit estimator must score worse when the assay budget is cut.

        Compare the reference at reduced ``measure_budget_calls`` against the full
        budget, averaged over several noise panels (world seeds). A frozen panel
        can hide a near-tie.
        """
        reduced, full = 8, self.evaluator.MEASURE_BUDGET
        panels = tuple(range(0, 24, 2))
        reduced_dev, reduced_held, full_dev, full_held = [], [], [], []
        for offset in panels:
            cheap = self._reference_at_budget(reduced, offset)
            rich = self._reference_at_budget(full, offset)
            reduced_dev.append(cheap["combined_score"])
            reduced_held.append(cheap["heldout_mechanism_score"])
            full_dev.append(rich["combined_score"])
            full_held.append(rich["heldout_mechanism_score"])
        mean_reduced_dev = sum(reduced_dev) / len(reduced_dev)
        mean_full_dev = sum(full_dev) / len(full_dev)
        mean_reduced_held = sum(reduced_held) / len(reduced_held)
        mean_full_held = sum(full_held) / len(full_held)
        self.assertLess(
            mean_reduced_dev,
            mean_full_dev - 0.04,
            "cutting the reference budget does not lower mean development score: "
            "reduced mean=%.4f full mean=%.4f reduced=%s full=%s"
            % (mean_reduced_dev, mean_full_dev, reduced_dev, full_dev),
        )
        self.assertLess(
            mean_reduced_held,
            mean_full_held - 0.08,
            "cutting the reference budget does not lower mean held-out score: "
            "reduced mean=%.4f full mean=%.4f reduced=%s full=%s"
            % (mean_reduced_held, mean_full_held, reduced_held, full_held),
        )

    def _reference_at_budget(self, budget, seed_offset):
        ev = self.evaluator
        original_budget = ev.PUBLIC_PROBLEM["measure_budget_calls"]
        original_dev = ev.DEVELOPMENT_WORLDS
        original_held = ev.HELDOUT_WORLDS
        try:
            ev.PUBLIC_PROBLEM["measure_budget_calls"] = int(budget)
            ev.DEVELOPMENT_WORLDS = tuple(
                dict(spec, seed=int(spec["seed"]) + int(seed_offset))
                for spec in original_dev
            )
            ev.HELDOUT_WORLDS = tuple(
                dict(spec, seed=int(spec["seed"]) + int(seed_offset))
                for spec in original_held
            )
            return ev.evaluate(self.reference.identify_falloff)
        finally:
            ev.PUBLIC_PROBLEM["measure_budget_calls"] = original_budget
            ev.DEVELOPMENT_WORLDS = original_dev
            ev.HELDOUT_WORLDS = original_held

    def test_the_public_high_pressure_wall_is_still_falloff(self):
        log_pr_1bar = []
        lo, hi = self.evaluator.WALL_PR_RANGE
        for world in list(self.evaluator.DEVELOPMENT_WORLDS) + list(self.evaluator.HELDOUT_WORLDS):
            if world["kind"] not in self.evaluator.SUPPORTED:
                continue
            with self.subTest(seed=world["seed"], kind=world["kind"]):
                kinf = self.evaluator.k_inf(world, 300.0)
                k_wall = self.evaluator.true_k(world, 300.0, 100.0)
                pr_wall = self.evaluator.k0_m(world, 300.0, 100.0) / kinf
                self.assertGreaterEqual(pr_wall, lo)
                self.assertLessEqual(pr_wall, hi)
                self.assertLess(k_wall / kinf, 0.85)
                self.assertGreater(k_wall / kinf, 0.10)
                log_pr_1bar.append(math.log(
                    self.evaluator.k0_m(world, 300.0, 1.0) / kinf
                ))
        rounded = [round(value, 8) for value in log_pr_1bar]
        self.assertEqual(
            len(rounded),
            len(set(rounded)),
            "in-family worlds share log Pr(300 K, 1 bar): %s" % (log_pr_1bar,),
        )

    def test_measurement_noise_is_keyed_by_temperature_and_pressure(self):
        spec = self.evaluator.DEVELOPMENT_WORLDS[0]
        first = self.evaluator._Lab(spec)
        second = self.evaluator._Lab(spec)
        high = first.measure(300.0, 100.0)
        repeat = first.measure(300.0, 100.0)
        low = second.measure(300.0, 1.0e-3)
        high_reordered = second.measure(300.0, 100.0)
        self.assertEqual(high, repeat)
        self.assertEqual(high, high_reordered)
        self.assertNotEqual(high, low)


if __name__ == "__main__":
    unittest.main()
