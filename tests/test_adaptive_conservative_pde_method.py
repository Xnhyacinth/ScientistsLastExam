from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sle.evaluate import evaluate_candidate
from sle.frontier import load_frozen_wave
from sle.registry import find_task


ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "benchmarks" / "ComputerScience" / "AdaptiveConservativePDEMethod"


def _load(name: str, path: Path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


class AdaptiveConservativePDEMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluator = _load(
            "adaptive_conservative_pde_evaluator",
            TASK_DIR / "verification" / "evaluator.py",
        )
        cls.baseline = _load("adaptive_conservative_pde_baseline", TASK_DIR / "solution.py")
        cls.reference = _load(
            "adaptive_conservative_pde_reference",
            TASK_DIR / "verification" / "reference_method.py",
        )

    def test_baseline_and_reference_are_exact_score_anchors(self) -> None:
        baseline = self.evaluator.evaluate(self.baseline.design_finite_volume_method)
        reference = self.evaluator.evaluate(self.reference.design_finite_volume_method)

        self.assertEqual(baseline["valid"], 1.0)
        self.assertAlmostEqual(baseline["combined_score"], 0.0, places=12)
        self.assertEqual(reference["valid"], 1.0)
        self.assertAlmostEqual(reference["combined_score"], 1.0, places=12)
        self.assertGreater(
            reference["development_accuracy_score"],
            baseline["development_accuracy_score"],
        )
        self.assertGreater(
            reference["development_raw_utility"], baseline["development_raw_utility"]
        )
        self.assertLess(reference["development_max_conservation_error"], 1.0e-10)
        self.assertEqual(len(reference["frontier_records"]), 1)

    def test_a_nontrivial_legal_method_can_score_above_reference(self) -> None:
        stronger = {
            "reconstruction": "muscl",
            "limiter": "van_leer",
            "riemann_solver": "godunov",
            "time_integrator": "ssprk3",
            "cells": 192,
            "cfl": 0.78,
            "sensor_threshold": 0.34,
            "shock_blend": 0.72,
            "flux_dissipation": 1.0,
        }

        metrics = self.evaluator.evaluate(lambda _problem: dict(stronger))

        self.assertEqual(metrics["valid"], 1.0)
        self.assertGreater(metrics["combined_score"], 1.0)
        self.assertGreater(metrics["development_raw_utility"], metrics["reference_utility"])

    def test_periodic_and_open_cases_obey_discrete_flux_balance(self) -> None:
        problem = self.evaluator._public_problem()
        method = self.evaluator._normalize_method(
            self.reference.design_finite_volume_method(problem), problem
        )

        for world in self.evaluator._load_panel()["worlds"]:
            result = self.evaluator._run_world(method, world)
            self.assertLess(result["conservation_error"], 1.0e-10, world["id"])
            self.assertTrue(math.isfinite(result["l1_error"]), world["id"])

    def test_malformed_invalid_and_overbudget_methods_fail_closed(self) -> None:
        problem = self.evaluator._public_problem()
        valid = self.baseline.design_finite_volume_method(problem)
        cases = [
            lambda _problem: None,
            lambda _problem: {**valid, "unknown": 1},
            lambda _problem: {**valid, "cells": True},
            lambda _problem: {**valid, "cfl": float("nan")},
            lambda _problem: {**valid, "limiter": "unlimited"},
            lambda _problem: {
                **valid,
                "reconstruction": "muscl",
                "riemann_solver": "godunov",
                "time_integrator": "ssprk3",
                "cells": 192,
                "cfl": 0.08,
            },
        ]

        for candidate in cases:
            with self.subTest(candidate=candidate):
                metrics = self.evaluator.evaluate(candidate)
                self.assertEqual(metrics["valid"], 0.0)
                self.assertEqual(metrics["combined_score"], 0.0)
                self.assertEqual(metrics["frontier_records"], [])

    def test_evaluation_is_deterministic(self) -> None:
        first = self.evaluator.evaluate(self.reference.design_finite_volume_method)
        second = self.evaluator.evaluate(self.reference.design_finite_volume_method)
        self.assertEqual(first, second)

    def test_candidate_proxy_sessions_are_reset_between_panel_worlds(self) -> None:
        source = """
import os
import numpy as np

COUNTER = 0

def design_finite_volume_method(problem):
    global COUNTER
    COUNTER += 1
    marker = '/tmp/adaptive-pde-state-marker'
    leaked = COUNTER != 1 or os.path.exists(marker) or hasattr(np, '_adaptive_pde_marker')
    with open(marker, 'w', encoding='utf-8') as handle:
        handle.write('state')
    np._adaptive_pde_marker = True
    method = {
        'reconstruction': 'constant',
        'limiter': 'minmod',
        'riemann_solver': 'rusanov',
        'time_integrator': 'euler',
        'cells': 32,
        'cfl': 0.45,
        'sensor_threshold': 0.5,
        'shock_blend': 1.0,
        'flux_dissipation': 1.15,
    }
    if leaked:
        method['leaked_state'] = True
    return method
"""
        spec = find_task(
            "ScientificComputing/AdaptiveConservativePDEMethod",
            include_uncertified=True,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as handle:
            handle.write(source)
            handle.flush()
            metrics = evaluate_candidate(spec, Path(handle.name), timeout_s=90)

        self.assertEqual(metrics["valid"], 1.0)
        self.assertAlmostEqual(metrics["combined_score"], 0.0, places=12)
        self.assertEqual(metrics["candidate_world_call_count"], 7)

    def test_standalone_runner_does_not_import_candidate_into_oracle_process(self) -> None:
        source = """
import sys

def design_finite_volume_method(problem):
    leaked = 'evaluator' in sys.modules or any(
        'verification/evaluator.py' in str(getattr(module, '__file__', ''))
        for module in tuple(sys.modules.values())
    )
    method = {
        'reconstruction': 'constant',
        'limiter': 'minmod',
        'riemann_solver': 'rusanov',
        'time_integrator': 'euler',
        'cells': 32,
        'cfl': 0.45,
        'sensor_threshold': 0.5,
        'shock_blend': 1.0,
        'flux_dissipation': 1.15,
    }
    if leaked:
        method['same_process_oracle'] = True
    return method
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.py"
            metrics_path = root / "metrics.json"
            candidate.write_text(source, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(TASK_DIR / "frontier_eval" / "run_eval.py"),
                    "--candidate",
                    str(candidate),
                    "--metrics-out",
                    str(metrics_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(metrics["valid"], 1.0, metrics)
        self.assertAlmostEqual(metrics["combined_score"], 0.0, places=12)
        self.assertEqual(metrics["candidate_world_call_count"], 7)

    def test_wave_contract_hashes_and_frontier_record_bind_to_method(self) -> None:
        spec = find_task(
            "ScientificComputing/AdaptiveConservativePDEMethod",
            include_uncertified=True,
        )
        wave = load_frozen_wave(spec)
        self.assertIsNotNone(wave)
        assert wave is not None
        self.assertEqual(
            wave.task_family_id, "ScientificComputing/AdaptiveConservativePDEMethod"
        )
        self.assertEqual(wave.wave_id, "scalar-law-panel-v1")

        metrics = self.evaluator.evaluate(self.reference.design_finite_volume_method)
        problem = self.evaluator._public_problem()
        method = self.evaluator._normalize_method(
            self.reference.design_finite_volume_method(problem), problem
        )
        expected_id = self.evaluator._canonical_method_id(method)
        record = metrics["frontier_records"][0]
        self.assertEqual(record["canonical_id"], expected_id)
        self.assertAlmostEqual(record["value"], metrics["development_raw_utility"])

        contract = wave.cells["conservative-scalar-law-method"]["semantic_contract"]
        for path_key, hash_key in (
            ("canonicalizer_path", "canonicalizer_sha256"),
            ("evidence_predicate_path", "evidence_predicate_sha256"),
            ("evaluation_panel_path", "evaluation_panel_sha256"),
        ):
            data = (TASK_DIR / contract[path_key]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), contract[hash_key])


if __name__ == "__main__":
    unittest.main()
