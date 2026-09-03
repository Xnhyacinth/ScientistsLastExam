"""Fail-closed verification for completed search-run artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .evaluation_ledger import EvaluationLedger, RunLease
from .protocol import load_trajectory, sha256_text, summarize_trajectory

INVALID_SCORE = -1.0e18


IDENTITY_FIELDS = (
    "task_id",
    "task_contract_sha256",
    "task_package_sha256",
    "runtime_source_sha256",
    "task_family_id",
    "wave_id",
    "wave_manifest_sha256",
)


def _document(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("run lacks a valid %s" % label) from exc
    if not isinstance(value, dict):
        raise ValueError("run %s must be an object" % label)
    return value


def _verify_run_unlocked(
    root: Path, *, expected_budget: int | None = None
) -> dict[str, Any]:
    manifest = _document(root / "run_manifest.json", "run_manifest.json")
    summary = _document(root / "summary.json", "summary.json")
    try:
        events = load_trajectory(root / "trajectory.jsonl")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("run lacks a valid trajectory.jsonl") from exc
    budget = summary.get("budget")
    if (
        isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget < 0
        or budget < max(int(event["step"]) for event in events)
    ):
        raise ValueError("run summary budget is smaller than its trajectory")
    if expected_budget is not None and (
        isinstance(expected_budget, bool)
        or not isinstance(expected_budget, int)
        or expected_budget < 0
        or budget != expected_budget
    ):
        raise ValueError("run summary budget differs from the externally expected budget")
    rebuilt = summarize_trajectory(events, budget=budget + 1)
    if any(summary.get(key) != value for key, value in rebuilt.items()):
        raise ValueError("run summary accounting differs from trajectory")
    for key in ("task_id", "algorithm", "seed", "feedback_mode"):
        if summary.get(key) != manifest.get(key):
            raise ValueError("run summary %s differs from manifest" % key)

    if manifest.get("algorithm") == "greedy_rewrite":
        ledger = EvaluationLedger(root)
        verified_request_ids = []
        verified_receipts = {}
        expected_oracle_calls = 0
        incumbent_hash = None
        incumbent_score = INVALID_SCORE
        horizon = (manifest.get("protocol") or {}).get("active_wall_horizon_s")
        baseline_receipt_score = None
        for event in events:
            metadata = event.get("algorithm_metadata") or {}
            request_id = metadata.get("evaluation_request_id")
            if not event.get("candidate_sha256"):
                if request_id is not None:
                    raise ValueError("no-code event unexpectedly has an evaluation receipt")
                expected_score, expected_valid = INVALID_SCORE, False
            else:
                bound = ledger.require_bound_record(request_id)
                request = bound["request"]
                receipt = bound["receipt"]
                expected_oracle_calls += 1
                verified_request_ids.append(str(request_id))
                verified_receipts[str(request_id)] = str(receipt["metrics_sha256"])
                for key in IDENTITY_FIELDS:
                    if key in manifest and request.get(key) != manifest.get(key):
                        raise ValueError("evaluation receipt %s differs from manifest" % key)
                expected_kind = "baseline" if int(event["step"]) == 0 else "proposal"
                event_metrics = receipt.get("metrics") or {}
                try:
                    expected_score = float(
                        event_metrics.get("combined_score", INVALID_SCORE)
                    )
                    expected_valid = float(event_metrics.get("valid", 0.0)) >= 1.0
                except (TypeError, ValueError) as exc:
                    raise ValueError("evaluation receipt has invalid score metrics") from exc
                if not math.isfinite(expected_score):
                    expected_score, expected_valid = INVALID_SCORE, False
                if not (
                    request.get("kind") == expected_kind
                    and request.get("step") == int(event["step"])
                    and request.get("candidate_sha256") == event["candidate_sha256"]
                    and request.get("parent_sha256") == event.get("parent_sha256")
                    and (
                        int(event["step"]) == 0
                        or request.get("prompt_sha256") == metadata.get("prompt_sha256")
                    )
                    and event_metrics == (event.get("metrics") or {})
                ):
                    raise ValueError("evaluation receipt differs from trajectory event")
            if not (
                int(event.get("oracle_calls", -1)) == expected_oracle_calls
                and int(event.get("budget_units", -1)) == int(event["step"]) + 1
                and float(event.get("score")) == expected_score
                and bool(event.get("valid")) == expected_valid
            ):
                raise ValueError("trajectory accounting differs from evaluation receipts")
            if int(event["step"]) == 0:
                if not expected_valid:
                    raise ValueError("completed run has an invalid baseline receipt")
                expected_accepted = True
                incumbent_hash = str(event["candidate_sha256"])
                incumbent_score = expected_score
                baseline_receipt_score = expected_score
            else:
                after_horizon = bool(
                    horizon is not None
                    and float(event["cumulative_wall_seconds"]) > float(horizon)
                )
                if bool(metadata.get("completed_after_active_wall_horizon")) != after_horizon:
                    raise ValueError("trajectory cutoff state differs from frozen protocol")
                expected_accepted = bool(
                    expected_valid
                    and expected_score > incumbent_score
                    and not after_horizon
                )
                if expected_accepted:
                    incumbent_hash = str(event["candidate_sha256"])
                    incumbent_score = expected_score
            if not (
                bool(event.get("accepted")) == expected_accepted
                and float(event.get("best_score")) == incumbent_score
            ):
                raise ValueError("trajectory incumbent state differs from receipt replay")
        ledger_snapshot = ledger.snapshot()
        expected_ids = sorted(verified_request_ids)
        if not (
            ledger_snapshot.get("request_ids") == expected_ids
            and ledger_snapshot.get("receipt_ids") == expected_ids
            and ledger_snapshot.get("open_request_ids") == []
        ):
            raise ValueError("evaluation ledger contains requests outside the trajectory")
        if summary.get("evaluation_ledger_snapshot") != ledger_snapshot:
            raise ValueError("evaluation ledger snapshot differs from summary")
        if float(summary.get("baseline_score")) != baseline_receipt_score:
            raise ValueError("summary baseline score differs from baseline receipt")
    else:
        verified_request_ids = []
        verified_receipts = {}
        incumbent_hash = None

    best_path = root / "best_program.py"
    try:
        best_hash = sha256_text(best_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError("run lacks best_program.py") from exc
    best_score = float(summary.get("best_score"))
    if int(events[-1].get("budget_units", -1)) > budget + 1:
        raise ValueError("trajectory exceeds the frozen proposal budget")
    if manifest.get("algorithm") == "greedy_rewrite" and best_hash != incumbent_hash:
        raise ValueError("best program differs from replayed incumbent")
    if manifest.get("algorithm") != "greedy_rewrite" and not any(
        event.get("candidate_sha256") == best_hash and bool(event.get("valid"))
        and float(event.get("score")) == best_score for event in events
    ):
        raise ValueError("best program is not bound to a best-scoring trajectory event")
    return {
        "verified": True,
        "task_id": manifest.get("task_id"),
        "algorithm": manifest.get("algorithm"),
        "event_count": len(events),
        "best_program_sha256": best_hash,
        "verified_request_ids": sorted(verified_request_ids),
        "verified_receipt_metrics_sha256": dict(sorted(verified_receipts.items())),
    }


def verify_run(
    workdir: Path,
    *,
    acquire_lease: bool = True,
    expected_budget: int | None = None,
) -> dict[str, Any]:
    """Rebuild a run and verify summary, receipt, counter, and incumbent state."""

    root = Path(workdir).resolve()
    if not acquire_lease:
        return _verify_run_unlocked(root, expected_budget=expected_budget)
    with RunLease(root):
        return _verify_run_unlocked(root, expected_budget=expected_budget)
