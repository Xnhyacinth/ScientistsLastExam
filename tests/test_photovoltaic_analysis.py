"""Source compatibility gates use archived record fixtures without model calls.

Raw bytes are independently checked by audit_historical_records on a data host;
these tests never turn fixture records into newly trusted scientific evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from scripts import analyze_photovoltaic_tandem_calibrations as analysis
from scripts.audit_historical_records import ARCHIVES


@pytest.fixture
def archived_records(monkeypatch):
    relative, expected = ARCHIVES["photovoltaic_tandem"]
    payload = (analysis.ROOT / relative).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == expected
    records = json.loads(payload)["records"]
    monkeypatch.setattr(analysis, "_load_model", lambda label, _: copy.deepcopy(records[label]))
    return records


def test_history_comparison_uses_conservative_supported_git_scope():
    assert "sle" in analysis.TASK_RUNTIME_SCOPE
    assert "benchmarks/Chemistry/PhotovoltaicTandemDesign" in analysis.TASK_RUNTIME_SCOPE
    assert "requirements-upstream.txt" in analysis.TASK_RUNTIME_SCOPE
    assert not any(":(glob)" in path for path in analysis.TASK_RUNTIME_SCOPE)
    assert analysis._source_changes(
        analysis.CALIBRATION_SOURCE_REVISION, analysis.INPUT_SOURCE_REVISION,
    ) == []


def test_current_drift_cannot_inherit_historical_compatibility(archived_records):
    report = analysis.analyze()
    assert report["calibration_to_model_task_runtime_source_equivalent"] is True
    assert report["calibration_to_model_task_runtime_source_changes"] == []
    assert report["model_to_analysis_task_runtime_source_equivalent"] is False
    assert "sle/protocol.py" in report["model_to_analysis_task_runtime_source_changes"]
    migration = report["model_to_analysis_task_runtime_source_migration"]
    assert migration["accepted"] is False
    assert migration["checks"]["report_hash_matches"] is True
    assert migration["checks"]["runtime_change_scope_matches"] is False
    assert migration["checks"]["current_runtime_hashes_match"] is False
    assert report["input_task_runtime_source_equivalent"] is False
    assert report["execution_passed"] is report["trusted_evidence"] is report["passed"] is False
    assert all(record["integrity_passed"] for record in report["records"].values())


def test_historical_drift_is_still_rejected_when_current_sources_match(archived_records, monkeypatch):
    monkeypatch.setattr(analysis, "_source_changes", lambda left, right:
                        ["sle/protocol.py"] if left == analysis.CALIBRATION_SOURCE_REVISION else [])
    report = analysis.analyze()
    assert report["calibration_to_model_task_runtime_source_equivalent"] is False
    assert report["model_to_analysis_task_runtime_source_equivalent"] is True
    assert report["execution_passed"] is report["trusted_evidence"] is report["passed"] is False


def test_original_record_gate_is_not_replaced_by_runtime_gate(archived_records, monkeypatch):
    archived_records["budget_one"]["integrity_passed"] = False
    monkeypatch.setattr(analysis, "_source_changes", lambda left, right: [])
    report = analysis.analyze()
    assert report["input_task_runtime_source_equivalent"] is True
    assert report["execution_passed"] is report["trusted_evidence"] is report["passed"] is False
