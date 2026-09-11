from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scripts.audit_historical_records import (
    ARCHIVE_REVISION, ARCHIVES, RECORD_LABELS, audit_archive,
)
from sle.protocol import compact_trajectory_snapshot

ROOT = Path(__file__).resolve().parents[1]


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return _digest(path)


@pytest.fixture
def archive(tmp_path):
    run = tmp_path / "runs" / "example"
    run.mkdir(parents=True)
    for name in ("best_program.py", "solution.py"):
        (run / name).write_text("def solve(): return 1\n")
    event = {
        "schema_version": 2, "step": 0, "oracle_calls": 1, "budget_units": 1,
        "score": 0.0, "best_score": 0.0, "wall_seconds": 0.0,
        "cumulative_wall_seconds": 0.0, "valid": True, "accepted": True,
        "candidate_sha256": _digest(run / "best_program.py"), "parent_sha256": None,
        "metrics": {"combined_score": 0.0},
    }
    (run / "trajectory.jsonl").write_text(json.dumps(event) + "\n")
    manifest_hash = _json(run / "run_manifest.json", {"task_id": "fixture"})
    batch = {"runs": [{
        "workdir": "/original/host/runs/example",
        "trajectory_snapshot": compact_trajectory_snapshot(run / "trajectory.jsonl"),
    }]}
    batch_hash = _json(tmp_path / "experiments/batch.json", batch)
    calibration_hash = _json(tmp_path / "experiments/calibration.json", {"fixture": True})
    record = {
        "report": "experiments/batch.json", "report_sha256": batch_hash,
        "trajectory_sha256": _digest(run / "trajectory.jsonl"),
        "run_manifest_sha256": manifest_hash,
        "selected_candidate_sha256": _digest(run / "best_program.py"),
        "terminal_proposal_sha256": _digest(run / "solution.py"),
    }
    document = {
        "execution_passed": True, "passed": True, "trusted_evidence": True,
        "source_provenance": {"source_tree_dirty": False, "source_changes": []},
        "task_calibration": {
            "report": "experiments/calibration.json", "report_sha256": calibration_hash,
        },
        "records": {label: record.copy() for label in RECORD_LABELS},
    }
    relative = "experiments/archive.json"
    return tmp_path, relative, _json(tmp_path / relative, document)


def test_complete_bytes_are_separate_from_current_scientific_trust(archive):
    report = audit_archive(*archive)
    assert report["status"] == "passed"
    assert report["passed_run_count"] == report["expected_run_count"] == 3
    assert report["current_runtime_compatibility"] == "not_assessed"
    assert report["trusted_evidence"] is False
    assert report["scientific_admission"] == "not_assessed"
    assert all(row["unbound_files"] == ["checkpoint.json", "summary.json"]
               for row in report["records"].values())


@pytest.mark.parametrize("relative", [
    "experiments/archive.json", "experiments/calibration.json", "experiments/batch.json",
    "runs/example/trajectory.jsonl", "runs/example/run_manifest.json",
    "runs/example/best_program.py", "runs/example/solution.py",
])
def test_every_original_hash_binding_rejects_changed_bytes(archive, relative):
    root, _, _ = archive
    with (root / relative).open("a") as handle:
        handle.write("\n")
    assert audit_archive(*archive)["status"] == "failed"


def test_missing_raw_record_is_missing_with_fixed_denominator(archive):
    (archive[0] / "runs/example/trajectory.jsonl").unlink()
    report = audit_archive(*archive)
    assert report["status"] == "missing"
    assert report["expected_run_count"] == 3
    assert report["passed_run_count"] == 0
    assert all(row["checks"]["trajectory.jsonl"]["status"] == "missing"
               for row in report["records"].values())


def test_rewriting_batch_projection_cannot_replace_archived_hash(archive):
    root = archive[0]
    trajectory = root / "runs/example/trajectory.jsonl"
    event = json.loads(trajectory.read_text())
    event["metrics"]["combined_score"] = 0.5
    trajectory.write_text(json.dumps(event) + "\n")
    batch_path = root / "experiments/batch.json"
    batch = json.loads(batch_path.read_text())
    batch["runs"][0]["trajectory_snapshot"] = compact_trajectory_snapshot(trajectory)
    _json(batch_path, batch)
    report = audit_archive(*archive)
    assert report["status"] == "failed"
    assert all(row["checks"]["batch_report_sha256"]["status"] == "failed"
               for row in report["records"].values())


def test_omitted_required_digest_is_not_treated_as_unbound_success(archive):
    root, relative, _ = archive
    path = root / relative
    document = json.loads(path.read_text())
    del document["records"]["budget_one"]["run_manifest_sha256"]
    report = audit_archive(root, relative, _json(path, document))
    assert report["status"] == "failed"
    assert report["passed_run_count"] == 2


def test_frozen_analysis_pins_match_the_original_committed_bytes():
    for relative, expected in ARCHIVES.values():
        original = subprocess.check_output(["git", "show", ARCHIVE_REVISION + ":" + relative], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == expected
        assert _digest(ROOT / relative) == expected
