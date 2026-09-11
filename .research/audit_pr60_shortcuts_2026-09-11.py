"""Run only the three preselected PR60 candidates through the current sandbox."""
from __future__ import annotations

import argparse
import ast
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

BASE = "68eac7248d30ca9a9f986cdfc4b4c07ee9cddf2e"
TASK_HEAD = "dbc2182268a44b26e383cc950457fd5f7d5aa8d1"
TASK = ROOT / "benchmarks/EarthScience/AquiferPumpingInference"
AUDIT = ROOT / ".research/pr60_shortcut_candidates_2026-09-11"


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(value).hexdigest()


def sources():
    return {str(path.relative_to(TASK)): digest(path.read_bytes())
            for path in sorted(TASK.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts}


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def factory(source):
    node = next(node for node in ast.parse(source).body
                if isinstance(node, ast.FunctionDef) and node.name == "_candidate")
    return ast.get_source_segment(source, node)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()
    private = args.private_root.resolve()
    if private == ROOT or ROOT in private.parents:
        raise ValueError("private evidence must be outside checkout")
    private.mkdir(mode=0o700, parents=True, exist_ok=True)
    private.chmod(0o700)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if revision != BASE:
        raise ValueError("wrong integration source revision")
    expected = json.loads((ROOT / ".research/pr60_task_sources_2026-09-11.json").read_text())
    if sources() != expected:
        raise ValueError("task differs from the frozen PR60 archive")
    provenance = json.loads((AUDIT / "source_provenance.json").read_text())
    reference = (TASK / "verification/reference_solver.py").read_bytes()
    original_probe = (TASK / "verification/shortcut_probe.py").read_text()
    derived = (AUDIT / "disclosed_residual_probe.py").read_bytes()
    if not (derived.startswith(reference)
            and factory(derived.decode()) == factory(original_probe)
            and digest(factory(original_probe).encode()) == provenance["factory_source_sha256"]
            and digest(derived) == provenance["candidate_sha256"]
            and digest(reference) == provenance["reference_source_sha256"]):
        raise ValueError("derived candidate differs from its exact helper/factory provenance")
    # PR60's only required loader addition. Do not replace the layout file,
    # which on the PR branch also lacks a main-branch Microbiology entry.
    if "Hydrology" in benchmark_layout.DOMAIN_DISCIPLINES:
        raise ValueError("unexpected pre-existing Hydrology mapping")
    benchmark_layout.DOMAIN_DISCIPLINES["Hydrology"] = "EarthScience"
    spec = load_task_spec(TASK)
    candidates = {
        "baseline": TASK / "solution.py",
        "reference": TASK / "verification/reference_solver.py",
        "disclosed_residual_probe": AUDIT / "disclosed_residual_probe.py",
    }
    frozen_candidates = {name: path.read_bytes() for name, path in candidates.items()}
    report = {
        "schema_version": 1,
        "scope": "fixed disclosed strategy replay; no grid, model call or heldout selection",
        "task_head": TASK_HEAD, "integration_head": BASE,
        "task_id": spec.task_id,
        "runtime_source_sha256": runtime_source_sha256(),
        "task_package_sha256": task_package_sha256(spec),
        "task_source_hashes": expected,
        "loader_adapter": "PR60 Hydrology -> EarthScience mapping in memory only; no runtime file change",
        "derivation": provenance,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": sys.version, "executable": sys.executable,
                    "platform": platform.platform(), "numpy": np.__version__, "scipy": scipy.__version__,
                    "thread_environment": {key: os.environ.get(key) for key in (
                        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}},
        "timeout_seconds": 300.0, "candidate_order": list(candidates),
        "repeats_per_candidate": 2,
        "candidate_plan_sha256": {name: digest(source) for name, source in frozen_candidates.items()},
        "oracle_output_scope": "oracle exposes aggregate metrics only, no per-world records",
        "candidates": {},
    }
    public = ROOT / ".research/pr60_shortcut_review_2026-09-11.json"
    write_json(public, report)
    for name, source in frozen_candidates.items():
        record = {"source_path": str(candidates[name].relative_to(ROOT)),
                  "candidate_sha256": digest(source), "runs": []}
        report["candidates"][name] = record
        full = []
        for repeat in range(1, 3):
            with tempfile.TemporaryDirectory(prefix="sle_pr60_candidate_") as temporary:
                candidate = Path(temporary) / "solution.py"
                candidate.write_bytes(source)
                started = time.monotonic()
                metrics = evaluate_candidate(spec, candidate, timeout_s=300.0)
                elapsed = time.monotonic() - started
            write_json(private / ("%s_%d.json" % (name, repeat)), metrics)
            if metrics.get("infrastructure_failure"):
                raise RuntimeError("infrastructure failure for " + name)
            full.append(metrics)
            record["runs"].append({"repeat": repeat, "wall_seconds": elapsed,
                                   "metrics": metrics, "full_metrics_sha256": digest(metrics)})
            write_json(public, report)
            print(json.dumps({"candidate": name, "repeat": repeat, "seconds": round(elapsed, 3),
                              "valid": metrics.get("valid"),
                              "dev": metrics.get("development_combined_score"),
                              "heldout": metrics.get("heldout_combined_score")}), flush=True)
        record["full_metrics_repeat_identical"] = full[0] == full[1]
        write_json(public, report)
    if sources() != expected:
        raise ValueError("task changed during evaluation")
    report["completed_evaluations"] = 6
    report["all_repeats_identical"] = all(row["full_metrics_repeat_identical"] for row in report["candidates"].values())
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(public, report)


if __name__ == "__main__":
    main()
