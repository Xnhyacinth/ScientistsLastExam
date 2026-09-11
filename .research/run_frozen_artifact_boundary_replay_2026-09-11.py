"""Fixed sandbox replays for the two cohort tasks whose world boundaries changed.

Run once at main3069479 and once at the integration revision. Each retained
artifact is evaluated twice with 300 seconds; no new model or selected program.
Full metrics stay private. Compare their hashes before declaring compatibility.
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

TASKS = ("StructuralEngineering/TrussWeightMinimization", "Thermodynamics/HeatExchangerDesign")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--expected-revision", required=True)
    parser.add_argument("--artifact-pack", type=Path, required=True)
    parser.add_argument("--expected-pack-sha256", required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.repository.resolve()
    sys.path.insert(0, str(root))
    from sle.algorithms.common import runtime_source_sha256, task_contract_sha256, task_package_sha256
    from sle.evaluate import evaluate_candidate
    from sle.registry import find_task
    import numpy, scipy
    git = lambda *a: subprocess.check_output(["git", "-c", "core.commitGraph=false", "-C", str(root), *a], text=True).strip()
    if git("rev-parse", "HEAD") != args.expected_revision or git("status", "--porcelain"):
        raise ValueError("fixed clean scientific source required")
    if (sys.platform, sys.version_info[:2], numpy.__version__, scipy.__version__) != ("linux", (3, 8), "1.24.4", "1.10.1"):
        raise ValueError("fixed Linux scientific environment required")
    if any(os.environ.get(k) != "1" for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")):
        raise ValueError("numerical threads must all equal one")
    payload = args.artifact_pack.read_bytes()
    if sha(payload) != args.expected_pack_sha256:
        raise ValueError("artifact pack differs from the predetermined immutable input")
    document = json.loads(payload)
    if document.get("purpose") != "portable_fixed_artifacts_for_frozen_seven_task_measurement_health_preflight":
        raise ValueError("unexpected artifact pack")
    sources = []
    for task in TASKS:
        rows = [row for row in document["artifacts"] if row["task"] == task]
        if len(rows) != 1:
            raise ValueError("expected exactly one fixed artifact per task")
        row = rows[0]
        code = row["source"].encode()
        if sha(code) != row["candidate_sha256"] or len(code) != row["candidate_utf8_bytes"]:
            raise ValueError("artifact source content differs")
        sources.append((find_task(task, include_uncertified=True), code))
    private = args.private_root.resolve()
    if private == root or root in private.parents:
        raise ValueError("private root must be outside source checkout")
    os.umask(0o077)
    private.mkdir(mode=0o700, exist_ok=False)
    bindings = {spec.task_id: {"task_package_sha256": task_package_sha256(spec),
                              "task_contract_sha256": task_contract_sha256(spec), "candidate_sha256": sha(code)}
                for spec, code in sources}
    plan = {"source_revision": args.expected_revision, "runtime_source_sha256": runtime_source_sha256(),
            "artifact_pack_sha256": sha(payload), "tasks": bindings, "timeout_s": 300,
            "planned_calls": 4, "model_calls": 0, "repeats": 2,
            "reviewer_script_sha256": sha(Path(__file__).read_bytes())}
    write_new(private / "plan.json", plan)
    records = []
    for spec, code in sources:
        candidate = private / (spec.task_id.replace("/", "__") + ".py")
        with candidate.open("xb") as stream:
            stream.write(code)
        for repeat in (1, 2):
            tick = time.monotonic()
            metrics = evaluate_candidate(spec, candidate, timeout_s=300)
            raw = private / (spec.task_id.replace("/", "__") + "_%s.json" % repeat)
            write_new(raw, metrics)
            row = {"task": spec.task_id, "repeat": repeat, "wall_seconds": time.monotonic() - tick,
                   "full_metrics_sha256": sha(canonical(metrics)), "file_sha256": sha(raw.read_bytes()),
                   "per_instance_sha256": sha(canonical(metrics.get("per_instance", []))),
                   "scalar_metric_count": sum(type(v) in (int, float, bool, str) for v in metrics.values()),
                   "scalar_metrics": {k: v for k, v in metrics.items() if type(v) in (int, float, bool)}}
            records.append(row)
            write_new(private / ("receipt_%02d.json" % len(records)), row)
            print(spec.task_id, repeat, metrics.get("valid"), metrics.get("combined_score"), flush=True)
    unchanged = (git("rev-parse", "HEAD") == args.expected_revision and not git("status", "--porcelain")
                 and runtime_source_sha256() == plan["runtime_source_sha256"]
                 and all(task_package_sha256(spec) == bindings[spec.task_id]["task_package_sha256"] for spec, code in sources))
    valid = all(row["scalar_metrics"].get("valid") == 1 and not row["scalar_metrics"].get("infrastructure_failure") for row in records)
    repeated = all(len({row["full_metrics_sha256"] for row in records if row["task"] == task}) == 1 for task in TASKS)
    result = {"schema_version": 1, "scope": "fixed retained artifact sandbox replay, not new model or general equivalence",
              "plan": plan, "plan_sha256": sha(canonical(plan)), "records": records,
              "source_unchanged": unchanged, "all_valid": valid, "repeat_identical": repeated,
              "passed": unchanged and valid and repeated and len(records) == 4}
    write_new(private / "public-replay-review.json", result)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
