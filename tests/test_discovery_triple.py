"""Discovery-axis reports must find both supported run directory layouts."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "scripts/report_discovery_triple.py"
    spec = importlib.util.spec_from_file_location("discovery_triple", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DiscoveryTripleLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    @staticmethod
    def write_run(directory: Path, condition: str) -> None:
        directory.mkdir(parents=True)
        (directory / "run_manifest.json").write_text(json.dumps({
            "task_id": "Mathematics/SequenceLawRecovery",
            "feedback_mode": "normal",
            "seed": 0,
            "llm_condition": {"model": "hy3-ioa"},
            "llm_condition_sha256": condition,
            "task_package_sha256": "task-package",
            "runtime_source_sha256": "runtime-source",
        }), encoding="utf-8")
        (directory / "trajectory.jsonl").write_text(json.dumps({"step": 0, "valid": True, "score": 0.0}) + "\n" + json.dumps({
            "step": 1,
            "valid": True,
            "score": 0.5,
            "metrics": {
                "combined_score": 0.5,
                "heldout_mechanism_score": 0.4,
                "heldout_false_discovery_rate": 0.1,
                "heldout_unsupported_refusal_rate": 0.8,
                "heldout_discovery_coverage": 0.7,
            },
        }) + "\n", encoding="utf-8")

    def test_shallow_cohort_and_nested_batch_layouts_are_both_discovered(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            self.write_run(root / "cohort/cell", "condition-shallow")
            self.write_run(
                root / "batch/Mathematics__SequenceLawRecovery/greedy_rewrite/normal/seed_0",
                "condition-nested",
            )
            output = Path(tmp) / "triple.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.module.main(["--runs", str(root), "--output", str(output)])
            rows = [
                row for row in json.loads(output.read_text(encoding="utf-8"))["rows"]
                if row.get("status") == "ok"
                and row.get("task") == "Mathematics/SequenceLawRecovery"
            ]
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            {row["llm_condition_sha256"] for row in rows},
            {"condition-shallow", "condition-nested"},
        )

    def test_legacy_manifest_model_is_recovered_from_the_condition_registry(self):
        document = {
            "task_id": "Mathematics/SequenceLawRecovery",
            "llm_condition_sha256": "legacy-condition",
            "task_package_sha256": "task-package",
            "runtime_source_sha256": "runtime-source",
        }
        with patch.object(
            self.module, "known_conditions", return_value={"legacy-condition": "hy3-ioa"}
        ):
            identity = self.module.run_identity(document)
        self.assertIsNotNone(identity)
        self.assertEqual(identity[1], "hy3-ioa")


class DiscoveryMetricContractTests(unittest.TestCase):
    def test_heldout_axes_never_fall_back_to_development(self):
        module = load_module()
        metrics = {"heldout_mechanism_score": 0.3,
                   "heldout_correct_refusal_rate": 0.2,
                   "development_correct_refusal_rate": 0.9,
                   "development_discovery_coverage": 0.8}
        axes = module.extract(metrics)
        self.assertEqual(axes["refusal"]["value"], 0.2)
        self.assertIsNone(axes["coverage"]["value"])
        self.assertEqual(axes["coverage"]["status"], "published_on_other_split")
        self.assertEqual(axes["coverage"]["split"], "development")
        self.assertEqual(axes["coverage"]["key"], "development_discovery_coverage")

    def test_unprefixed_mechanism_is_published_on_other_split_not_missing(self):
        module = load_module()
        metrics = {
            "mechanism_score": 0.55,
            "development_false_discovery_rate": 0.1,
            "development_unsupported_refusal_rate": 0.8,
            "development_discovery_coverage": 0.7,
        }
        heldout = module.extract(metrics, "heldout")
        self.assertEqual(heldout["mechanism"]["status"], "published_on_other_split")
        self.assertEqual(heldout["mechanism"]["key"], "mechanism_score")
        self.assertEqual(heldout["mechanism"]["split"], "unsplit")
        self.assertIsNone(heldout["mechanism"]["value"])
        self.assertEqual(heldout["fdr"]["status"], "published_on_other_split")
        self.assertEqual(heldout["fdr"]["split"], "development")
        development = module.extract(metrics, "development")
        self.assertEqual(development["mechanism"]["status"], "published_on_other_split")
        self.assertEqual(development["fdr"]["value"], 0.1)
        unsplit = module.extract(metrics, "unsplit")
        self.assertEqual(unsplit["mechanism"]["value"], 0.55)
        self.assertEqual(unsplit["fdr"]["status"], "published_on_other_split")
        self.assertEqual(unsplit["refusal"]["status"], "published_on_other_split")
        truly_absent = module.extract({"combined_score": 0.1}, "heldout")
        self.assertIsNone(truly_absent["mechanism"])
        self.assertIsNone(truly_absent["fdr"])

    def test_baseline_metrics_survive_late_unaccepted_improvement(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            rows = [
                {"step": 0, "valid": True, "score": 0.6,
                 "metrics": {"combined_score": 0.6, "heldout_mechanism_score": 0.4}},
                {"step": 1, "valid": True, "score": 0.9, "accepted": False,
                 "metrics": {"combined_score": 0.9, "heldout_mechanism_score": 0.8}},
            ]
            (directory / "trajectory.jsonl").write_text("\n".join(map(json.dumps, rows)))
            self.assertEqual(module.best_metrics(directory)["heldout_mechanism_score"], 0.4)

    def test_seeds_are_not_selected_by_maximum_score(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for seed in (0, 1):
                directory = root / str(seed)
                DiscoveryTripleLayoutTests.write_run(directory, "same-condition")
                path = directory / "run_manifest.json"
                manifest = json.loads(path.read_text())
                manifest["seed"] = seed
                path.write_text(json.dumps(manifest))
            output = root / "report.json"
            with contextlib.redirect_stdout(io.StringIO()):
                module.main(["--runs", str(root), "--output", str(output)])
            rows = [r for r in json.loads(output.read_text())["rows"] if r["status"] == "ok"]
            self.assertEqual(len(rows), 2)
            self.assertEqual({r["seed"] for r in rows}, {0, 1})


class DeclaredMetricTests(unittest.TestCase):
    def test_actual_cards_distinguish_fpr_and_fdr_and_zero_claims(self):
        import yaml
        module = load_module()
        imu = yaml.safe_load((ROOT / "benchmarks/Engineering/IMUBiasCalibration/TASK_CARD.yaml").read_text())["metric_contract"]
        amoc = yaml.safe_load((ROOT / "benchmarks/EarthScience/AMOCTippingRefusal/TASK_CARD.yaml").read_text())["metric_contract"]
        metrics = {"heldout_false_discovery_rate": 0.0, "heldout_false_discovery_denominator": 0}
        fdr = module.extract(metrics, contract=imu)["fdr"]
        fpr = module.extract(metrics, contract=amoc)["fdr"]
        self.assertEqual(fdr["estimand"], "false_discovery_rate")
        self.assertEqual(fdr["status"], "zero_denominator")
        self.assertIsNone(fdr["value"])
        self.assertEqual(fpr["estimand"], "false_positive_rate")
        self.assertNotEqual(fdr["denominator"], fpr["denominator"])
