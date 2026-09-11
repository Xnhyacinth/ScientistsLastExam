"""Fixed PR73 candidates through the integrated secure evaluator; no grid search.

Only trusted aggregate metrics are written to the public JSON. Per-world records
remain in an explicitly selected private directory outside the checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import scipy
from sle import benchmark_layout
from sle.algorithms.common import runtime_source_sha256, task_package_sha256
from sle.evaluate import evaluate_candidate
from sle.spec import load_task_spec

BASE = "bfd62be68723fa50e477eaca789a95989ab878ed"
TASK_HEAD = "c0d1f3e2419c4dc334587dcf1be4b9777bf632be"
TASK = ROOT / "benchmarks/Biology/NeuralReportAttribution"


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(value).hexdigest()


def task_sources():
    return {
        str(path.relative_to(TASK)): digest(path.read_bytes())
        for path in sorted(TASK.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def atomically_write(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def denominators(metrics):
    result = {}
    for split in ("development", "heldout"):
        rows = [row for row in metrics["per_instance"] if row["split"] == split]
        result[split] = {
            "world_count": len(rows),
            "mechanism_utility_sum": sum(row["mechanism"] for row in rows),
            "mechanism_utility_mean": sum(row["mechanism"] for row in rows) / len(rows),
            "false_claim_count": sum(row["false_claim"] for row in rows),
            "positive_claim_count": sum(row["claim"] for row in rows),
            "correct_refusal_count": sum(row["correct_refusal"] for row in rows),
            "refusal_world_count": sum(row["kind"] == "unsupported" for row in rows),
            "supported_claim_count": sum(row["claim"] for row in rows if row["kind"] in ("recurrent", "report_only")),
            "supported_world_count": sum(row["kind"] in ("recurrent", "report_only") for row in rows),
            "null_correct_count": sum(row["model"] == "none" for row in rows if row["kind"] == "none"),
            "null_world_count": sum(row["kind"] == "none" for row in rows),
            "valid_world_count": sum(row["valid"] for row in rows),
            "experiment_units_sum": sum(row["units"] for row in rows),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()
    private = args.private_root.resolve()
    if private == ROOT or ROOT in private.parents:
        raise ValueError("private records must live outside the checkout")
    private.mkdir(mode=0o700, parents=True, exist_ok=True)
    private.chmod(0o700)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if revision != BASE:
        raise ValueError("wrong integration source revision")
    expected = json.loads((ROOT / ".research/pr73_task_sources_2026-09-11.json").read_text())
    if task_sources() != expected:
        raise ValueError("PR73 task bytes differ from the frozen head archive")
    # PR73 introduces this one taxonomy mapping. Keep bfd62be's runtime files
    # unchanged; add the same mapping in memory solely for load_task_spec.
    if "Neuroscience" in benchmark_layout.DOMAIN_DISCIPLINES:
        raise ValueError("unexpected pre-existing Neuroscience taxonomy mapping")
    benchmark_layout.DOMAIN_DISCIPLINES["Neuroscience"] = "Biology"
    spec = load_task_spec(TASK)
    public_path = ROOT / ".research/pr73_shortcut_review_2026-09-11.json"
    report = {
        "schema_version": 1,
        "scope": "fixed candidate sandbox audit; not model calibration or a shortcut search",
        "task_head": TASK_HEAD,
        "integration_head": BASE,
        "runtime_source_sha256": runtime_source_sha256(),
        "task_package_sha256": task_package_sha256(spec),
        "task_source_hashes": expected,
        "loader_adapter": "PR73's Neuroscience -> Biology mapping added in memory; no runtime file changes",
        "task_id": spec.task_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": sys.version, "executable": sys.executable,
                    "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
                    "thread_environment": {key: os.environ.get(key) for key in (
                        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}},
        "timeout_seconds": 300.0,
        "candidate_order": ["baseline", "reference", "algebraic_default", "published_grid_winner"],
        "repeats_per_candidate": 2,
        "candidates": {},
    }
    sources = {
        "baseline": TASK / "solution.py",
        "reference": TASK / "verification/reference_fit.py",
        "algebraic_default": TASK / "verification/algebraic_probe.py",
        "published_grid_winner": ROOT / ".research/pr73_shortcut_candidates_2026-09-11/published_grid_winner.py",
    }
    for name, path in sources.items():
        source = path.read_bytes()
        record = {"source_path": str(path.relative_to(ROOT)), "candidate_sha256": digest(source), "runs": []}
        if name in ("algebraic_default", "published_grid_winner"):
            record["frozen_config"] = ([.25, .3, .15, 1., 1.] if name == "algebraic_default" else [.13, .35, .08, .9, 1.])
        if name == "published_grid_winner":
            record["config_source"] = "PR73 c0d1f3e2 references/known_best.md section 4; historical development-only grid winner; no new selection"
        report["candidates"][name] = record
        full_runs = []
        for repeat in range(1, 3):
            with tempfile.TemporaryDirectory(prefix="sle_pr73_candidate_") as temporary:
                candidate = Path(temporary) / "solution.py"
                candidate.write_bytes(source)
                started = time.monotonic()
                metrics = evaluate_candidate(spec, candidate, timeout_s=300.0)
                elapsed = time.monotonic() - started
            if metrics.get("infrastructure_failure") or "per_instance" not in metrics:
                atomically_write(private / (name + "_failure.json"), metrics)
                raise RuntimeError("secure evaluation did not return scientific metrics: " + name)
            atomically_write(private / ("%s_%d.json" % (name, repeat)), metrics)
            full_runs.append(metrics)
            record["runs"].append({
                "repeat": repeat, "wall_seconds": elapsed,
                "metrics": {key: value for key, value in metrics.items() if key != "per_instance"},
                "full_metrics_sha256": digest(metrics),
                "per_instance_sha256": digest(metrics["per_instance"]),
                "denominators": denominators(metrics),
            })
            atomically_write(public_path, report)
            print(json.dumps({"candidate": name, "repeat": repeat, "seconds": round(elapsed, 3),
                              "dev": metrics["development_mechanism_score"],
                              "heldout": metrics["heldout_mechanism_score"]}), flush=True)
        record["full_metrics_repeat_identical"] = full_runs[0] == full_runs[1]
        atomically_write(public_path, report)
    if task_sources() != expected:
        raise ValueError("task sources changed during evaluation")
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["completed_evaluations"] = sum(len(row["runs"]) for row in report["candidates"].values())
    report["all_repeats_identical"] = all(row["full_metrics_repeat_identical"] for row in report["candidates"].values())
    atomically_write(public_path, report)


if __name__ == "__main__":
    main()
