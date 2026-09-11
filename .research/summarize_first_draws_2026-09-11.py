"""Read-only admission review of every planned first proposal, including failures.

Run against the unchanged calibration checkout. Full trajectories/receipts stay
private; the output contains scalar metrics, source bindings and file hashes.
This operator review does not certify tasks or rewrite historical evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--reference", type=float, required=True)
    parser.add_argument("--expected-worlds", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repository.resolve()
    sys.path.insert(0, str(root))
    from scripts.task_campaign import read_plan, replay
    from sle.algorithms.common import runtime_source_sha256, task_contract_sha256, task_package_sha256
    from sle.registry import find_task

    require(math.isfinite(args.reference) and args.reference > 0, "positive finite reference required")
    require(args.expected_worlds > 0, "positive world count required")
    plan = read_plan(args.plan)
    require(plan["kind"] == "calibration" and plan["budgets"] == [1], "first-draw budget-1 plan required")
    require(plan["feedback_modes"] == ["selection_blind"], "selection-blind plan required")
    fresh_replay = replay(plan)
    supplied_replay = read(args.replay)
    require(all(supplied_replay.get(key) == value for key, value in fresh_replay.items()),
            "independent replay differs from supplied replay artifact")
    git = lambda *a: subprocess.check_output(["git", "-c", "core.commitGraph=false", "-C", str(root), *a], text=True).strip()
    require(not git("status", "--porcelain"), "calibration source must remain clean")
    require(git("rev-parse", "HEAD") == plan["source_provenance"]["git_revision"], "source revision changed")
    binding = plan["bindings"]
    spec = find_task(binding["task_id"], include_uncertified=True)
    for key, value in {"task_package_sha256": task_package_sha256(spec),
                       "task_contract_sha256": task_contract_sha256(spec),
                       "runtime_source_sha256": runtime_source_sha256()}.items():
        require(binding[key] == value, "current source differs: " + key)

    results = []
    files = []
    totals = {key: 0 for key in ("input_tokens", "output_tokens", "total_tokens")}
    usage_complete = True
    for cell in plan["cells"]:
        directory = Path(cell["workdir"])
        if not (directory / "trajectory.jsonl").is_file():
            usage_complete = False
            results.append({"seed_label": cell["seed"], "status": "missing_trajectory",
                            "events": [{}, {"reference_reached": None, "scientific_score": None}]})
            continue
        require(directory.stat().st_mode & 0o077 == 0, "run directory is not private")
        events = [json.loads(line) for line in (directory / "trajectory.jsonl").read_text().splitlines() if line.strip()]
        if len(events) < 2:
            usage_complete = False
            results.append({"seed_label": cell["seed"], "status": "first_proposal_unavailable",
                            "trajectory_sha256": sha((directory / "trajectory.jsonl").read_bytes()),
                            "events": [{}, {"reference_reached": None, "scientific_score": None}]})
            continue
        require(len(events) == 2 and [e["step"] for e in events] == [0, 1], "unexpected proposal horizon")
        manifest = read(directory / "run_manifest.json")
        for key in ("task_id", "task_package_sha256", "task_contract_sha256", "runtime_source_sha256", "llm_condition_sha256"):
            require(manifest[key] == binding[key], "manifest binding differs: " + key)
        event_reviews = []
        for event in events:
            metrics = event.get("metrics") or {}
            request_id = (event.get("algorithm_metadata") or {}).get("evaluation_request_id")
            receipt_hash = None
            if request_id:
                request_path = directory / "evaluation_ledger/requests" / (request_id + ".json")
                receipt_path = directory / "evaluation_ledger/receipts" / (request_id + ".json")
                request_doc, receipt = read(request_path), read(receipt_path)
                request = request_doc["request"]
                require(sha(canonical(request)) == request_id == request_doc["request_sha256"], "request content binding differs")
                require(receipt["request_id"] == request_id == receipt["request_sha256"], "receipt request binding differs")
                require(receipt["metrics_sha256"] == sha(canonical(metrics)) and receipt["metrics"] == metrics,
                        "trajectory metrics differ from durable receipt")
                require(request["step"] == event["step"] and request["candidate_sha256"] == event["candidate_sha256"],
                        "candidate/step differs from request")
                for key in ("task_id", "task_package_sha256", "task_contract_sha256", "runtime_source_sha256"):
                    require(request[key] == binding[key], "request source binding differs: " + key)
                require(request["evaluator_timeout_seconds"] == plan["timeout_s"], "evaluation timeout differs")
                require(receipt_path.stat().st_mode & 0o077 == 0, "receipt is not private")
                receipt_hash = sha(receipt_path.read_bytes())
            rows = metrics.get("per_instance") or []
            all_worlds_valid = (len(rows) == args.expected_worlds and
                               all(r.get("valid") in (True, 1, 1.0) for r in rows) and
                               metrics.get("feasibility_rate") == 1 and event.get("valid") is True)
            score = event.get("score")
            meaningful = (all_worlds_valid and request_id is not None and type(score) in (int, float)
                          and math.isfinite(score) and score != -1e18)
            event_reviews.append({"step": event["step"], "candidate_sha256": event.get("candidate_sha256"),
                                  "request_id": request_id, "receipt_file_sha256": receipt_hash,
                                  "full_metrics_sha256": sha(canonical(metrics)),
                                  "per_instance_sha256": sha(canonical(rows)),
                                  "observed_worlds": len(rows),
                                  "valid_worlds": sum(r.get("valid") in (True, 1, 1.0) for r in rows),
                                  "all_worlds_valid": all_worlds_valid,
                                  "scientific_score": score if meaningful else None,
                                  "error_sha256": sha(str(event["error"]).encode()) if event.get("error") else None,
                                  "scalar_metrics": {k: v for k, v in metrics.items() if type(v) in (int, float, bool)}})
        first = event_reviews[1]
        archived_candidates = read(directory / "checkpoint.json").get("evaluated_candidates", [])
        archived_first = [row for row in archived_candidates if row.get("step") == 1]
        if events[1].get("candidate_sha256") is not None:
            require(len(archived_first) == 1, "first candidate source was not retained")
            require(sha(archived_first[0]["program"].encode()) == first["candidate_sha256"],
                    "retained candidate source hash differs")
        first["reference_reached"] = (first["scientific_score"] >= args.reference
                                       if first["scientific_score"] is not None else None)
        usage = events[1].get("llm") or {}
        for key in totals:
            if type(usage.get(key)) is int and usage[key] >= 0:
                totals[key] += usage[key]
            else:
                usage_complete = False
        retained = []
        for name in ("solution.py", "best_program.py"):
            path = directory / name
            if path.is_file() and sha(path.read_bytes()) == first["candidate_sha256"]:
                retained.append(name)
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                require(path.stat().st_mode & 0o077 == 0, "private run contains a readable file")
                files.append({"path": str(path.relative_to(Path(plan["workdir"]))), "sha256": sha(path.read_bytes())})
        results.append({"seed_label": cell["seed"], "model_condition": {
                            k: manifest["llm_condition"].get(k) for k in
                            ("model", "wire", "reasoning_effort", "temperature", "max_output_tokens", "timeout_seconds")},
                        "events": event_reviews, "retained_first_proposal_files": retained, "usage": usage,
                        "trajectory_sha256": sha((directory / "trajectory.jsonl").read_bytes()),
                        "manifest_sha256": sha((directory / "run_manifest.json").read_bytes())})
    hits = sum(r["events"][1]["reference_reached"] is True for r in results)
    unavailable = sum(r["events"][1]["reference_reached"] is None for r in results)
    result = {"schema_version": 1, "task_id": binding["task_id"], "bindings": binding,
              "source_revision": git("rev-parse", "HEAD"), "source_unchanged": True,
              "plan_sha256": plan["plan_sha256"], "plan_file_sha256": sha(args.plan.read_bytes()),
              "replay_file_sha256": sha(args.replay.read_bytes()),
              "campaign_replay_status": fresh_replay["status"],
              "campaign_cell_status_counts": fresh_replay["cell_status_counts"],
              "reviewer_script_sha256": sha(Path(__file__).read_bytes()), "reference_score": args.reference,
              "expected_worlds_per_evaluation": args.expected_worlds,
              "scheduled_first_proposals": len(results), "valid_complete_first_proposals": len(results) - unavailable,
              "first_proposals_reaching_reference": hits,
              "criterion_D16": "failed" if hits else "incomplete" if unavailable else "passed_comparison_only",
              "model_reported_usage": totals if usage_complete else None, "usage_available_for_all_events": usage_complete,
              "scientific_certification": "not_assessed", "trusted_frozen_evidence": False,
              "interpretation": "A first proposal is judged only when all expected worlds are valid. Failed/partial proposals remain in the denominator and never establish difficulty. A passing comparison is not external scientific certification. Seed labels do not control provider randomness. No oracle or model calls were made by this reviewer.",
              "cells": results, "private_artifact_file_hashes": files}
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    args.output.chmod(0o600)
    print(json.dumps({k: result[k] for k in ("task_id", "criterion_D16", "scheduled_first_proposals", "valid_complete_first_proposals", "first_proposals_reaching_reference", "model_reported_usage")}))


if __name__ == "__main__":
    main()
