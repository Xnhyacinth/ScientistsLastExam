"""Behavioral tests for process-to-microstructure-to-property design."""
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
TASK = ROOT / "benchmarks/Chemistry/ProcessMicrostructurePropertyDesign"
sys.path.insert(0, str(ROOT))

from sle.evaluate import evaluate_candidate
from sle.frontier import load_frozen_wave
from sle.spec import load_task_spec


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProcessMicrostructurePropertyDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = _load(TASK / "verification/evaluator.py", "process_structure_oracle")
        cls.baseline = _load(TASK / "solution.py", "process_structure_baseline")

    def test_shipped_process_archive_is_legal_and_normalized_to_zero(self):
        result = self.evaluator.evaluate(self.baseline.design_process_archive)
        self.assertEqual(result["valid"], 1.0)
        self.assertAlmostEqual(result["combined_score"], 0.0, places=12)
        self.assertEqual(result["development_feasibility_rate"], 1.0)

    def test_more_verified_pareto_points_can_earn_strict_continuous_gain(self):
        def intermediate(problem):
            reference = self.evaluator._reference_policy(problem)["processes"]
            return {"processes": reference[:8]}

        baseline = self.evaluator.evaluate(self.baseline.design_process_archive)
        middle = self.evaluator.evaluate(intermediate)
        reference = self.evaluator.evaluate(self.evaluator._reference_policy)
        self.assertGreater(middle["combined_score"], baseline["combined_score"])
        self.assertGreater(reference["combined_score"], middle["combined_score"])
        self.assertAlmostEqual(reference["combined_score"], 1.0, places=12)

    def test_sealed_process_and_material_shifts_are_reported_separately(self):
        result = self.evaluator.evaluate(self.evaluator._reference_policy)
        self.assertIn("development_shifted_hypervolume_score", result)
        self.assertIn("heldout_hypervolume_score", result)
        self.assertIn("heldout_shifted_hypervolume_score", result)
        self.assertTrue(all(
            len(row["raw_shifted_hypervolumes"]) == 3
            for row in result["per_instance"]
        ))
        self.assertTrue(any(
            any(abs(value - row["raw_hypervolume"]) > 1.0e-12
                for value in row["raw_shifted_hypervolumes"])
            for row in result["per_instance"]
        ))
        self.assertEqual(result["combined_score"], result["development_hypervolume_score"])

    def test_artifact_must_be_a_manufacturable_process_not_an_image(self):
        def image_artifact(problem):
            processes = [dict(row) for row in self.evaluator._weak_archive(problem)]
            processes[0]["microstructure_image"] = [[0.0, 1.0], [1.0, 0.0]]
            return {"processes": processes}

        result = self.evaluator.evaluate(image_artifact)
        self.assertEqual(result["valid"], 0.0)
        self.assertEqual(result["combined_score"], 0.0)

    def test_nonfinite_out_of_bounds_and_exceptions_fail_closed(self):
        def nonfinite(problem):
            rows = [dict(row) for row in self.evaluator._weak_archive(problem)]
            rows[0]["anneal_time"] = math.nan
            return {"processes": rows}

        def out_of_bounds(problem):
            rows = [dict(row) for row in self.evaluator._weak_archive(problem)]
            rows[0]["draw_ratio"] = 100.0
            return {"processes": rows}

        def raises(_problem):
            raise RuntimeError("candidate bug")

        def duplicates(problem):
            row = dict(self.evaluator._weak_archive(problem)[0])
            return {"processes": [dict(row) for _ in range(4)]}

        for candidate in (
            lambda _problem: None, nonfinite, out_of_bounds, duplicates, raises
        ):
            with self.subTest(candidate=candidate):
                result = self.evaluator.evaluate(candidate)
                self.assertEqual(result["valid"], 0.0)
                self.assertEqual(result["combined_score"], 0.0)

    def test_manufacturing_resolution_deduplicates_near_identical_recipes(self):
        def near_duplicates(problem):
            rows = [dict(row) for row in self.evaluator._weak_archive(problem)]
            rows[1] = dict(rows[0])
            rows[1]["blend_fraction_b"] += 0.001
            return {"processes": rows}

        result = self.evaluator.evaluate(near_duplicates)
        self.assertEqual(result["valid"], 0.0)
        self.assertEqual(result["combined_score"], 0.0)

    def test_simple_high_b_corner_no_longer_dominates_reference(self):
        def high_b_corner(_problem):
            return {"processes": [
                {
                    "blend_fraction_b": value,
                    "anneal_temperature": 0.45,
                    "anneal_time": 0.5,
                    "cooling_rate": 4.0,
                    "draw_ratio": 1.0,
                }
                for value in (0.82, 0.83, 0.84, 0.85)
            ]}

        corner = self.evaluator.evaluate(high_b_corner)
        reference = self.evaluator.evaluate(self.evaluator._reference_policy)
        self.assertLess(corner["combined_score"], reference["combined_score"])

    def test_candidate_session_is_reset_between_every_world(self):
        evaluator = self.evaluator

        class StatefulCandidate:
            def __init__(self):
                self.calls = 0
                self.resets = 0

            def __call__(self, problem):
                self.calls += 1
                return {"processes": evaluator._weak_archive(problem)}

            def reset_session(self):
                self.resets += 1

        candidate = StatefulCandidate()
        self.evaluator.evaluate(candidate)
        self.assertEqual(candidate.calls, 6)
        self.assertEqual(candidate.resets, 5)

    def test_raw_hypervolume_emits_a_quantized_archive_frontier_record(self):
        result = self.evaluator.evaluate(self.evaluator._reference_policy)
        self.assertEqual(len(result["frontier_records"]), 1)
        record = result["frontier_records"][0]
        self.assertEqual(record["value"], result["development_raw_hypervolume"])
        self.assertIn(":panel:sha256:", record["canonical_id"])

    def test_frontier_record_requires_legal_heldout_transfer(self):
        def development_only(problem):
            modulus_b = problem["constituent_properties"]["reduced_modulus"][1]
            if modulus_b in (6.0, 4.7):
                return None
            return self.evaluator._reference_policy(problem)

        result = self.evaluator.evaluate(development_only)

        self.assertEqual(result["valid"], 1.0)
        self.assertAlmostEqual(result["combined_score"], 1.0, places=12)
        self.assertEqual(result["heldout_feasibility_rate"], 0.0)
        self.assertEqual(result["frontier_records"], [])

    def test_machine_readable_panel_is_the_evaluator_source(self):
        panel = json.loads((
            TASK / "frontier_eval/contracts/evaluation_panel_v1.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(self.evaluator.PROCESS_FIELDS, tuple(panel["process_fields"]))
        self.assertEqual(
            self.evaluator.HYPERVOLUME_REFERENCE_POINT,
            tuple(panel["hypervolume_reference_point"]),
        )
        self.assertEqual(
            [dict(world) for world in self.evaluator.WORLDS],
            panel["worlds"],
        )
        self.assertEqual(
            [dict(shift) for shift in self.evaluator.SHIFT_SPECS],
            panel["shift_specs"],
        )
        self.assertEqual(self.evaluator.MODEL_PARAMETERS, panel["model_parameters"])
        self.assertEqual(self.evaluator.BASELINE_POLICY, panel["baseline_policy"])
        self.assertEqual(self.evaluator.REFERENCE_POLICY, panel["reference_policy"])
        self.assertEqual(
            self.evaluator.FRONTIER_PROMOTION,
            panel["frontier_promotion"],
        )

    def test_standalone_runner_keeps_oracle_out_of_candidate_modules(self):
        candidate_source = '''
import sys


def design_process_archive(problem):
    leaked = any(
        name == "evaluator"
        or "/verification/evaluator.py" in str(getattr(module, "__file__", ""))
        for name, module in sys.modules.items()
    )
    bounds = problem["bounds"]
    low, high = bounds["blend_fraction_b"]
    processes = [
        {
            "blend_fraction_b": low + index / 3.0 * (high - low),
            "anneal_temperature": bounds["anneal_temperature"][1],
            "anneal_time": bounds["anneal_time"][0],
            "cooling_rate": bounds["cooling_rate"][1],
            "draw_ratio": bounds["draw_ratio"][0],
        }
        for index in range(4)
    ]
    result = {"processes": processes}
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
        self.assertEqual(wave.wave_id, "reduced-process-property-pareto-v1")
        self.assertEqual(
            wave.cells["process-property-pareto-hypervolume"]["reference_value"],
            self.evaluator._anchors()["development"]["reference"],
        )
        metrics = evaluate_candidate(spec, TASK / "solution.py", timeout_s=20)
        self.assertNotIn("infrastructure_failure", metrics)
        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["combined_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
