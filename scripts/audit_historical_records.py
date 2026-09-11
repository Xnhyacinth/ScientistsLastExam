#!/usr/bin/env python3
"""Check archived bytes independently of compatibility with today's evaluator.

The pins identify the committed historical analyses at f9c05b6. Their records
anchor the original batch reports and raw artifacts. This does not execute an
oracle, approve a migration, or produce current scientific evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.repo_paths import resolve_run_workdir  # noqa: E402
from sle.protocol import compact_trajectory_snapshot  # noqa: E402

ARCHIVE_REVISION = "f9c05b65b100e0b7d6acabbf16e64602fb73eea9"
ARCHIVES = {
    "alloy_hardness": (
        "experiments/alloy_hardness_v1_calibration_analysis_2026-07-26.json",
        "1e77deab1183825a5296341dbae74cade911e8b1a4aea2832aa9f5279b9c2c50",
    ),
    "calorimeter_v2": (
        "experiments/calorimeter_v2_calibration_analysis_2026-07-25.json",
        "d6a09d7500d59652a229dae55112fb01edc7e0cfc405e1eff1bce356d2f5f888",
    ),
    "rans_v2": (
        "experiments/rans_v2_calibration_analysis_2026-07-24.json",
        "bf4357b7e543492f27973249fb96cb94a714296cf3542c2d9f9f395dd165be7e",
    ),
    "demographic_sfs_v2": (
        "experiments/demographic_sfs_v2_calibration_analysis_2026-07-25.json",
        "88950cd4d3b99c55ca6810a3c2c9d9c0471109fadd2ed817416d3753383222c0",
    ),
    "diffraction_grating": (
        "experiments/diffraction_grating_v2_calibration_analysis_2026-07-26_v2.json",
        "c5bfe01b7a6d63f69720e1763f625577c938dc467a9c5e153b0885302260ac4e",
    ),
    "electrolyte_conductivity": (
        "experiments/electrolyte_conductivity_design_calibration_analysis_2026-07-25.json",
        "2f3fa9d7b0d57375ddfa1f5699129421fae3931895f6f6e3b3d8894db864bb31",
    ),
    "force_field_hypothesis": (
        "experiments/force_field_hypothesis_v2_calibration_analysis_2026-07-26.json",
        "1f5f6af3e437eb949f3a5075673ba1122ef61f9fffc2b4734b9d2d160d171360",
    ),
    "protein_stability": (
        "experiments/protein_stability_design_calibration_analysis_2026-07-25.json",
        "a8086d7525413782be2d833781615984d76c53558fd8e985ad0f863c15547f27",
    ),
    "photovoltaic_tandem": (
        "experiments/photovoltaic_tandem_v1_calibration_analysis_2026-07-25.json",
        "e938f0bc635ec1569a2276a9041995ee957eeb89248db008dc5a48a5e8658607",
    ),
    "prospective_meta_analysis": (
        "experiments/prospective_meta_analysis_calibration_analysis_2026-07-25.json",
        "d288ad58e4fbf88ebe6d8e89f1c5875a7a07b209b69094de74ee6334f7397c43",
    ),
}
RECORD_LABELS = {"budget_one", "normal_budget_three", "blind_budget_three"}


def _file(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("archive reference must be repository-relative")
    return root / path


def _hash_check(path: Path, expected: Any) -> dict[str, Any]:
    if not isinstance(expected, str) or len(expected) != 64:
        return {"status": "failed", "reason": "missing_sha256_binding"}
    if not path.is_file():
        return {"status": "missing", "path": str(path), "expected_sha256": expected}
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "status": "passed" if actual == expected else "failed",
        "path": str(path), "expected_sha256": expected, "actual_sha256": actual,
    }


def _result(checks: dict[str, Any]) -> str:
    statuses = {value["status"] for value in checks.values()}
    if "failed" in statuses:
        return "failed"
    return "missing" if "missing" in statuses else "passed"


def audit_archive(root: Path, relative: str, expected_sha256: str) -> dict[str, Any]:
    """Audit only originally hash-bound files; missing files are never passed.

    The anchor is checked before following any references. Intermediate sources
    that were never retained and files without an original digest remain outside
    the claim. Callers must obtain the anchor from reviewed source control.
    """
    root = Path(root).absolute()
    archive = _file(root, relative)
    checks: dict[str, Any] = {"archive_sha256": _hash_check(archive, expected_sha256)}
    result: dict[str, Any] = {
        "schema_version": 1, "archive": relative,
        "integrity_scope": "originally_hash_bound_files_and_trajectory_projection",
        "current_runtime_compatibility": "not_assessed",
        "trusted_evidence": False, "scientific_admission": "not_assessed",
        "expected_run_count": 3, "passed_run_count": 0,
        "checks": checks, "records": {},
    }
    if checks["archive_sha256"]["status"] != "passed":
        result["status"] = _result(checks)
        return result
    document = json.loads(archive.read_text(encoding="utf-8"))
    provenance = document.get("source_provenance") or {}
    records = document.get("records") or {}
    clean = (
        document.get("execution_passed") is True
        and document.get("trusted_evidence") is True
        and document.get("passed") is True
        and provenance.get("source_tree_dirty") is False
        and provenance.get("source_changes") == []
    )
    checks["original_analysis_clean"] = {"status": "passed" if clean else "failed"}
    checks["record_set"] = {
        "status": "passed" if set(records) == RECORD_LABELS else "failed",
    }
    calibration = document.get("task_calibration") or {}
    checks["calibration_report_sha256"] = _hash_check(
        _file(root, calibration.get("report", "")), calibration.get("report_sha256"),
    )
    for label, record in records.items():
        batch_path = _file(root, record["report"])
        row_checks = {"batch_report_sha256": _hash_check(batch_path, record.get("report_sha256"))}
        row: dict[str, Any] = {"checks": row_checks, "unbound_files": []}
        result["records"][label] = row
        if row_checks["batch_report_sha256"]["status"] == "passed":
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
            runs = batch.get("runs") or []
            if len(runs) != 1 or runs[0].get("error"):
                row_checks["single_successful_run"] = {"status": "failed"}
            else:
                run = runs[0]
                workdir = resolve_run_workdir(run["workdir"], root)
                bindings = {
                    "trajectory.jsonl": record.get("trajectory_sha256"),
                    "run_manifest.json": record.get("run_manifest_sha256"),
                    "best_program.py": record.get("best_program_sha256") or record.get("selected_candidate_sha256"),
                    "solution.py": record.get("terminal_program_sha256") or record.get("terminal_proposal_sha256"),
                }
                for filename, field in (("checkpoint.json", "checkpoint_sha256"), ("summary.json", "summary_sha256")):
                    if field in record:
                        bindings[filename] = record[field]
                    else:
                        row["unbound_files"].append(filename)
                for filename, expected in bindings.items():
                    row_checks[filename] = _hash_check(workdir / filename, expected)
                if row_checks["trajectory.jsonl"]["status"] == "passed":
                    try:
                        expected = run.get("trajectory_snapshot") or {}
                        actual = compact_trajectory_snapshot(
                            workdir / "trajectory.jsonl", schema_version=expected.get("schema_version", 1),
                        )
                        row_checks["trajectory_projection"] = {
                            "status": "passed" if actual == expected else "failed",
                        }
                    except (ValueError, KeyError, TypeError) as exc:
                        row_checks["trajectory_projection"] = {"status": "failed", "reason": str(exc)}
        row["status"] = _result(row_checks)
    result["passed_run_count"] = sum(row["status"] == "passed" for row in result["records"].values())
    result["status"] = _result({**checks, **{
        "run:" + name: {"status": row["status"]} for name, row in result["records"].items()
    }})
    return result


def audit_named(name: str, root: Path = ROOT) -> dict[str, Any]:
    result = audit_archive(root, *ARCHIVES[name])
    result["archive_anchor_revision"] = ARCHIVE_REVISION
    result["task"] = name
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["all", *ARCHIVES], default="all")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    names = ARCHIVES if args.task == "all" else [args.task]
    reports = [audit_named(name, args.root) for name in names]
    print(json.dumps({"schema_version": 1, "reports": reports}, indent=2, allow_nan=False))
    statuses = {report["status"] for report in reports}
    return 1 if "failed" in statuses else 2 if "missing" in statuses else 0


if __name__ == "__main__":
    raise SystemExit(main())
