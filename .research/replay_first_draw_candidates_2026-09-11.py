"""Re-evaluate the three retained first proposals after documentation-only task edits.

Fixed plan: each original candidate twice, no model calls or candidate selection.
Full results stay private; every complete metric must equal its original receipt.
This establishes compatibility for those artifacts, not fresh model evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sle.algorithms.common import runtime_source_sha256, task_contract_sha256, task_package_sha256
from sle.evaluate import evaluate_candidate
from sle.registry import find_task


def digest(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-plan", type=Path, required=True)
    parser.add_argument("--original-review", type=Path, required=True)
    parser.add_argument("--expected-revision", required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()
    git = lambda *a: subprocess.check_output(["git", "-c", "core.commitGraph=false", "-C", str(ROOT), *a], text=True).strip()
    if git("rev-parse", "HEAD") != args.expected_revision or git("status", "--porcelain"):
        raise ValueError("fixed clean source revision required")
    import numpy, scipy
    if (sys.platform, sys.version_info[:2], numpy.__version__, scipy.__version__) != ("linux", (3, 8), "1.24.4", "1.10.1"):
        raise ValueError("fixed Linux scientific environment required")
    if any(os.environ.get(k) != "1" for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")):
        raise ValueError("numerical thread limits must all be one")
    from scripts.task_campaign import read_plan
    original = read_plan(args.original_plan)
    review = read(args.original_review)
    if (review["criterion_D16"] != "passed_comparison_only" or review["plan_sha256"] != original["plan_sha256"]
            or review["valid_complete_first_proposals"] != 3 or len(original["cells"]) != 3
            or review["bindings"] != original["bindings"]):
        raise ValueError("complete reviewed three-draw comparison required")
    task = original["bindings"]["task_id"]
    spec = find_task(task, include_uncertified=True)
    runtime = runtime_source_sha256()
    if runtime != original["bindings"]["runtime_source_sha256"]:
        raise ValueError("runtime source changed; this documentation-only plan does not cover it")
    task_path = spec.task_dir.relative_to(ROOT).as_posix()
    changed = git("diff", "--name-only", review["source_revision"], "HEAD", "--", task_path).splitlines()
    permitted = {task_path + "/TASK_CARD.yaml", task_path + "/references/known_best.md"}
    if not set(changed) <= permitted:
        raise ValueError("scientific or agent-visible task files changed")
    sources = []
    for cell in original["cells"]:
        directory = Path(cell["workdir"])
        events = [json.loads(line) for line in (directory / "trajectory.jsonl").read_text().splitlines() if line.strip()]
        if len(events) != 2 or events[1]["valid"] is not True:
            raise ValueError("unexpected first proposal")
        first = events[1]
        reviewed = next(row for row in review["cells"] if row["seed_label"] == cell["seed"])["events"][1]
        if (reviewed["candidate_sha256"] != first["candidate_sha256"]
                or reviewed["full_metrics_sha256"] != digest(first["metrics"])):
            raise ValueError("original first proposal differs from the completed admission review")
        archive = [row for row in read(directory / "checkpoint.json")["evaluated_candidates"] if row["step"] == 1]
        if len(archive) != 1:
            raise ValueError("missing retained candidate")
        code = archive[0]["program"].encode()
        if hashlib.sha256(code).hexdigest() != first["candidate_sha256"]:
            raise ValueError("retained candidate source differs")
        request_id = first["algorithm_metadata"]["evaluation_request_id"]
        receipt_path = directory / "evaluation_ledger/receipts" / (request_id + ".json")
        receipt = read(receipt_path)
        if hashlib.sha256(receipt_path.read_bytes()).hexdigest() != reviewed["receipt_file_sha256"]:
            raise ValueError("original receipt changed since admission review")
        if receipt["metrics_sha256"] != digest(first["metrics"]) or receipt["metrics"] != first["metrics"]:
            raise ValueError("original metrics differ from receipt")
        sources.append((cell["seed"], code, first["candidate_sha256"], receipt["metrics"]))
    private = args.private_root.resolve()
    if private == ROOT or ROOT in private.parents:
        raise ValueError("private root must be outside source checkout")
    os.umask(0o077)
    private.mkdir(mode=0o700, parents=False, exist_ok=False)
    plan = {"source_revision": args.expected_revision, "task_id": task,
            "task_package_sha256": task_package_sha256(spec), "task_contract_sha256": task_contract_sha256(spec),
            "runtime_source_sha256": runtime, "original_model_plan_sha256": original["plan_sha256"],
            "documentation_files_changed": changed, "model_calls": 0, "planned_evaluations": 6,
            "timeout_s": original["timeout_s"], "candidates": [
                {"seed_label": seed, "candidate_sha256": code_hash, "original_full_metrics_sha256": digest(metrics)}
                for seed, code, code_hash, metrics in sources]}
    write_new(private / "replay-plan.json", plan)
    records = []
    for seed, code, code_hash, previous_metrics in sources:
        candidate = private / ("candidate_%s.py" % seed)
        with candidate.open("xb") as stream:
            stream.write(code)
        candidate.chmod(0o600)
        for repeat in (1, 2):
            tick = time.monotonic()
            metrics = evaluate_candidate(spec, candidate, timeout_s=original["timeout_s"])
            raw = private / ("full_metrics_%s_%s.json" % (seed, repeat))
            write_new(raw, metrics)
            row = {"seed_label": seed, "repeat": repeat, "candidate_sha256": code_hash,
                   "full_metrics_sha256": digest(metrics), "full_metrics_file_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
                   "matches_original_full_metrics": metrics == previous_metrics,
                   "wall_seconds": time.monotonic() - tick,
                   "scalar_metrics": {k: v for k, v in metrics.items() if type(v) in (int, float, bool)}}
            records.append(row)
            write_new(private / ("receipt_%s_%s.json" % (seed, repeat)), row)
            print(seed, repeat, metrics.get("valid"), metrics.get("combined_score"), row["matches_original_full_metrics"], flush=True)
    unchanged = (task_package_sha256(spec) == plan["task_package_sha256"] and runtime_source_sha256() == runtime
                 and git("rev-parse", "HEAD") == args.expected_revision and not git("status", "--porcelain"))
    passed = unchanged and len(records) == 6 and all(row["matches_original_full_metrics"] for row in records)
    report = {"schema_version": 1, "plan": plan, "plan_sha256": digest(plan), "records": records,
              "source_unchanged": unchanged, "passed": passed, "model_calls": 0,
              "scope": "retained-artifact compatibility only; no fresh draw, certification or new difficulty sample"}
    write_new(private / "public-replay-review.json", report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
