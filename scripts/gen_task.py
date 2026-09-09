#!/usr/bin/env python3
"""Batch task generator for Frontier-Science.

Creates the full directory structure + contract files for a task from a compact spec dict.
Usage:
    from scripts.gen_task import create_task
    create_task({
        "domain": "Physics",
        "task": "HarmonicOscillatorControl",
        "difficulty": "hard",        # hard | flagship only
        "oracle_type": "physical_sim",
        "score_mode": "clipped",
        "eval_time_seconds": 5,
        "science_metric": "...",
        "reference_baseline": "...",
        "reference_sota": "...",
        "citation": "...",
        "entrypoint": "solve",         # function name agent must implement
        "task_md": "...",              # full Task.md content
        "baseline_code": "...",        # full solution.py content
        "evaluator_code": "...",       # full verification/evaluator.py content
        "constraints": "...",          # constraints.txt content
    })
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from sle.benchmark_layout import discipline_for_domain  # noqa: E402

DEFAULT_EVAL_TIME_SECONDS = 100

RUN_EVAL_TEMPLATE = '''"""Black-box eval entrypoint for {task}.

A thin wrapper over the trusted evaluation path (`python -m sle eval`), which loads the oracle in
a supervised trusted subprocess and runs the candidate in the Bubblewrap sandbox over a typed
JSON-RPC boundary. Do NOT import the candidate into this process: the oracle lives here, so an
in-process import is a way for candidate code to run unsandboxed whenever anyone reaches for the
convenience. The harness never uses this file; external harnesses do, through `eval_command.txt`,
so it keeps that contract and loses the shortcut.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

INVALID = -1e18
TASK_ID = "{task_id}"
ROOT = Path(__file__).resolve().parents[4]
EVAL_TIMEOUT_S = {eval_timeout}

# The task id is written in, where the previous template derived everything from __file__.
# That is deliberate - `sle eval` needs the registered id, not a path - but it means a wrapper
# copied to a neighbouring task keeps pointing at the task it came from, and scores the new
# candidate against the old oracle without complaining. The directory name is the second half
# of the id, so the copy is cheap to catch here rather than in whoever reads the numbers.
_expected_task = Path(__file__).resolve().parents[1].name
if TASK_ID.split("/")[-1] != _expected_task:
    raise SystemExit(
        "TASK_ID %r does not name this directory (%r); this wrapper was copied from another"
        " task and would score against that task's oracle" % (TASK_ID, _expected_task))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--metrics-out", required=True)
    parser.add_argument("--timeout", type=float, default=EVAL_TIMEOUT_S)
    args = parser.parse_args()
    metrics = {{"combined_score": INVALID, "valid": 0.0}}
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "sle", "eval", "--task", TASK_ID, "--allow-uncertified",
             "--candidate", str(Path(args.candidate).resolve()), "--timeout", str(args.timeout)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=args.timeout + 120,
            env={{**os.environ, "PYTHONPATH": str(ROOT)}})
        if completed.returncode != 0:
            raise RuntimeError("sle eval exited %d: %s" % (
                completed.returncode, (completed.stderr or "").strip()[-500:]))
        result = json.loads(completed.stdout)
        metrics.update(result)
        metrics.setdefault("raw_score", result.get("combined_score"))
    except Exception as exc:  # noqa: BLE001 - a broken evaluation is reported, not raised
        metrics["error_message"] = "%s: %s" % (type(exc).__name__, exc)
    Path(args.metrics_out).write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    print(json.dumps({{k: metrics.get(k) for k in ("combined_score", "valid")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

METADATA_TEMPLATE = """domain: {domain}
task: {task}
difficulty: {difficulty}
oracle_type: {oracle_type}
score_mode: {score_mode}
gpu_required: false
eval_time_seconds: {eval_time_seconds}
science_metric: {science_metric}
reference_baseline: "{reference_baseline}"
reference_sota: "{reference_sota}"
citation: "{citation}"
"""


def create_task(spec: dict, repo: Path = REPO) -> Path:
    domain = spec["domain"]
    task = spec["task"]
    difficulty = str(spec.get("difficulty", "")).strip().lower()
    if difficulty not in {"hard", "flagship"}:
        raise ValueError(
            "Frontier-Science tasks must be PhD/expert difficulty: "
            "set difficulty to 'hard' or 'flagship'."
        )
    discipline = discipline_for_domain(domain)
    requested_discipline = spec.get("discipline")
    if requested_discipline not in {None, discipline}:
        raise ValueError(
            "Domain %r belongs to discipline %r, not %r."
            % (domain, discipline, requested_discipline)
        )
    task_dir = repo / "benchmarks" / discipline / task
    eval_dir = task_dir / "frontier_eval"
    ver_dir = task_dir / "verification"

    for d in [eval_dir, ver_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Task.md
    (task_dir / "Task.md").write_text(spec["task_md"], encoding="utf-8")

    # solution.py
    (task_dir / "solution.py").write_text(spec["baseline_code"], encoding="utf-8")

    # verification/evaluator.py
    (ver_dir / "evaluator.py").write_text(spec["evaluator_code"], encoding="utf-8")

    # frontier_eval contract files
    entrypoint = spec.get("entrypoint", "solve")
    # The wrapper timeout is a review quantity set by how hard the task is, so a spec may name
    # it outright. The fallback reproduces what the 66 existing wrappers already do (64 of them
    # exactly): three times the expected evaluation, floored at the repository's usual 300 s.
    # `eval_time_seconds` is defaulted once, here, so metadata.yaml and run_eval.py cannot
    # disagree about it - an earlier draft let one fall back to empty and the other to 300.
    eval_time_seconds = int(spec.get("eval_time_seconds") or DEFAULT_EVAL_TIME_SECONDS)
    spec = {**spec, "eval_time_seconds": eval_time_seconds}
    eval_timeout = int(spec.get("eval_timeout_s")
                       or max(300, 3 * eval_time_seconds))
    (eval_dir / "run_eval.py").write_text(
        RUN_EVAL_TEMPLATE.format(
            task=task, task_id="%s/%s" % (domain, task),
            eval_timeout=eval_timeout,
        ), encoding="utf-8")
    (eval_dir / "metadata.yaml").write_text(
        METADATA_TEMPLATE.format(**{k: spec.get(k, "") for k in
            ["domain","task","difficulty","oracle_type","score_mode",
             "eval_time_seconds","science_metric","reference_baseline",
             "reference_sota","citation"]}), encoding="utf-8")
    (eval_dir / "initial_program.txt").write_text("solution.py\n", encoding="utf-8")
    (eval_dir / "candidate_destination.txt").write_text("solution.py\n", encoding="utf-8")
    (eval_dir / "entrypoint.txt").write_text(entrypoint + "\n", encoding="utf-8")
    (eval_dir / "eval_command.txt").write_text(
        "{python} frontier_eval/run_eval.py --candidate {candidate} --metrics-out {metrics}\n",
        encoding="utf-8")
    (eval_dir / "constraints.txt").write_text(
        spec.get("constraints", f"1) Only edit solution.py. Keep the {entrypoint}() signature.\n"
                 "2) numpy/scipy/stdlib only. CPU, seconds. No network.\n"
                 "3) Do not read verification/ or frontier_eval/.\n"),
        encoding="utf-8")
    (eval_dir / "agent_files.txt").write_text(
        "Task.md\nsolution.py\nfrontier_eval/constraints.txt\n", encoding="utf-8")
    (eval_dir / "readonly_files.txt").write_text(
        "Task.md\nverification\nfrontier_eval\n", encoding="utf-8")

    return task_dir


if __name__ == "__main__":
    print("Import and call create_task(spec_dict) to generate a task.")
