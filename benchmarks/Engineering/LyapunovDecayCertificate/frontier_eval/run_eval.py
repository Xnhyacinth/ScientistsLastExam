"""Black-box eval entrypoint for LyapunovDecayCertificate.

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
TASK_ID = "ControlTheory/LyapunovDecayCertificate"
ROOT = Path(__file__).resolve().parents[4]
EVAL_TIMEOUT_S = 300

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
    metrics = {"combined_score": INVALID, "valid": 0.0}
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "sle", "eval", "--task", TASK_ID, "--allow-uncertified",
             "--candidate", str(Path(args.candidate).resolve()), "--timeout", str(args.timeout)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=args.timeout + 120,
            env={**os.environ, "PYTHONPATH": str(ROOT)})
        if completed.returncode != 0:
            raise RuntimeError("sle eval exited %d: %s" % (
                completed.returncode, (completed.stderr or "").strip()[-500:]))
        result = json.loads(completed.stdout)
        metrics.update(result)
        metrics.setdefault("raw_score", result.get("combined_score"))
    except Exception as exc:  # noqa: BLE001 - a broken evaluation is reported, not raised
        metrics["error_message"] = "%s: %s" % (type(exc).__name__, exc)
    Path(args.metrics_out).write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: metrics.get(k) for k in ("combined_score", "valid")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
