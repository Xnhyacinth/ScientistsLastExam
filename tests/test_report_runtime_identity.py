"""Scientific reports must never pool or select across evaluator runtimes."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]

ANALYZERS = (
    "analyze_alloy_hardness_calibrations.py",
    "analyze_calorimeter_v2_calibrations.py",
    "analyze_catalyst_deactivation_lab_calibrations.py",
    "analyze_demographic_sfs_v2_calibrations.py",
    "analyze_diffraction_grating_calibrations.py",
    "analyze_electrolyte_conductivity_design_calibrations.py",
    "analyze_force_field_hypothesis_calibrations.py",
    "analyze_photovoltaic_tandem_calibrations.py",
    "analyze_prospective_meta_analysis_calibrations.py",
    "analyze_qcm_raw_pipeline_calibrations.py",
)


def load_report(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location("runtime_identity_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CalibrationRuntimeIdentityTests(unittest.TestCase):
    def test_each_calibration_analyzer_binds_and_singletons_the_trusted_runtime(self):
        for name in ANALYZERS:
            with self.subTest(analyzer=name):
                source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
                self.assertIn('manifest.get("trusted_evaluator_runtime")', source)
                self.assertIn("verification = verify_run(workdir)", source)
                self.assertIn('record["trusted_evaluator_runtime_sha256"]', source)
                self.assertIn("trusted_runtimes =", source)
                self.assertIn('"input_trusted_evaluator_runtime_equivalent"', source)
                self.assertIn("len(trusted_runtimes) == 1", source)
                self.assertIn("None not in trusted_runtimes", source)


class CandidateSelectorTests(unittest.TestCase):
    def _exercise(self, script: str):
        module = load_report(script)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, package, score in (
                ("old-package", "old", 0.99),
                ("unverified", "current", 0.90),
                ("verified-current", "current", 0.50),
            ):
                run = root / name
                run.mkdir()
                (run / "run_manifest.json").write_text(json.dumps({
                    "task_id": "T/X",
                    "task_package_sha256": package,
                    "runtime_source_sha256": "source",
                    "trusted_evaluator_runtime": {
                        "fingerprint_sha256": "trusted",
                    },
                }), encoding="utf-8")
                (run / "summary.json").write_text(json.dumps({
                    "best_score": score,
                }), encoding="utf-8")
                (run / "best_program.py").write_text("PASS = True\n", encoding="utf-8")

            spec = SimpleNamespace(task_dir=root / "task")

            def verify(path, **_kwargs):
                if Path(path).name == "unverified":
                    raise ValueError("tampered")
                return {"verified": True}

            with patch.object(module, "find_task", return_value=spec), \
                    patch.object(module, "task_package_sha256", return_value="current"), \
                    patch.object(module, "runtime_source_sha256", return_value="source"), \
                    patch.object(module, "resolve_trusted_runtime", return_value=SimpleNamespace(
                        fingerprint_sha256="trusted"
                    )), patch.object(module, "verify_run", side_effect=verify):
                selected = module._best_candidate("T/X", root)
            self.assertEqual(selected, root / "verified-current" / "best_program.py")

    def test_difficulty_ladder_uses_only_current_verified_runs(self):
        self._exercise("report_difficulty_ladder.py")

    def test_hidden_axis_report_uses_only_current_verified_runs(self):
        self._exercise("report_saturation_hidden_axes.py")


if __name__ == "__main__":
    unittest.main()
