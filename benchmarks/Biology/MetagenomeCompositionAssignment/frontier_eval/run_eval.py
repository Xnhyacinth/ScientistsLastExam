"""Task-local black-box entrypoint for metagenome composition evaluation.

The candidate is evaluated only through ``python -m sle eval``, which keeps it
inside the repository's candidate sandbox. This wrapper publishes the small
selection allowlist and discards held-out and per-world diagnostics instead of
placing them beside the searcher's metrics file.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sle.evaluate import CREDENTIAL_MARKERS
from sle.metric_visibility import SEARCH_VISIBLE_KEYS


TASK_ID = "Microbiology/MetagenomeCompositionAssignment"
EVAL_TIMEOUT_S = 600.0
SENSITIVE_MARKERS = frozenset((
    *CREDENTIAL_MARKERS,
    "SECRET",
    "PASSWORD",
    "CREDENTIAL",
))
TRUSTED_DIAGNOSTICS_ENV = "SLE_TRUSTED_EVAL_LOG"
EXPECTED_TASK_DIR = Path(__file__).resolve().parents[1].name
if TASK_ID.rsplit("/", 1)[-1] != EXPECTED_TASK_DIR:
    raise SystemExit("TASK_ID does not match this task directory")


def _child_environment():
    environment = {
        key: value
        for key, value in os.environ.items()
        if not any(marker in key.upper() for marker in SENSITIVE_MARKERS)
    }
    environment.pop(TRUSTED_DIAGNOSTICS_ENV, None)
    environment["PYTHONPATH"] = str(ROOT)
    return environment


def _clear_output(path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return False
    return True


def _write_public_metrics(path, metrics):
    rendered = json.dumps(metrics, indent=2, default=str, allow_nan=False) + "\n"
    temporary = path.with_name(".%s.%d.tmp" % (path.name, os.getpid()))
    try:
        temporary.write_text(rendered, encoding="utf-8")
        os.replace(str(temporary), str(path))
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _write_trusted_failure(stage, completed=None, error=None):
    """Append private failure detail when the trusted driver requests a log."""
    destination = os.environ.get(TRUSTED_DIAGNOSTICS_ENV)
    if not destination:
        return
    record = {"stage": stage}
    if completed is not None:
        record["returncode"] = getattr(completed, "returncode", None)
        stderr = getattr(completed, "stderr", "") or ""
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        record["stderr_tail"] = str(stderr)[-4000:]
        stdout = getattr(completed, "stdout", "") or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        record["stdout_tail"] = str(stdout)[-4000:]
    if error is not None:
        record["error"] = "%s: %s" % (type(error).__name__, error)
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(destination, flags, 0o600)
        try:
            rendered = json.dumps(record, default=str, allow_nan=False) + "\n"
            os.write(descriptor, rendered.encode("utf-8"))
        finally:
            os.close(descriptor)
    except OSError:
        # Diagnostics must never change the public evaluation result.
        return


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--metrics-out", required=True)
    parser.add_argument("--timeout", type=float, default=EVAL_TIMEOUT_S)
    args = parser.parse_args(argv)
    output = Path(args.metrics_out).resolve()
    if not _clear_output(output):
        print("evaluation output could not be cleared", file=sys.stderr)
        return 2
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        print("evaluation timeout must be positive and finite", file=sys.stderr)
        return 2

    command = [
        sys.executable,
        "-m",
        "sle",
        "eval",
        "--task",
        TASK_ID,
        "--allow-uncertified",
        "--candidate",
        str(Path(args.candidate).resolve()),
        "--timeout",
        str(args.timeout),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=args.timeout + 120.0,
            env=_child_environment(),
        )
        if completed.returncode:
            _write_trusted_failure("child_process", completed=completed)
            print(
                "trusted evaluation infrastructure failed (exit %d)"
                % completed.returncode,
                file=sys.stderr,
            )
            return 2
        result = json.loads(completed.stdout)
        if not isinstance(result, dict):
            raise ValueError("trusted metrics are not an object")
        if result.get("infrastructure_failure"):
            _write_trusted_failure("reported_infrastructure_failure", completed=completed)
            print("trusted evaluation infrastructure failed", file=sys.stderr)
            return 2
        for key in ("combined_score", "valid"):
            value = result.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("trusted metrics require finite " + key)
        result.setdefault("raw_score", result["combined_score"])
        public = {key: result[key] for key in SEARCH_VISIBLE_KEYS if key in result}
        _write_public_metrics(output, public)
        print(json.dumps(public, default=str, allow_nan=False))
        return 0
    except (json.JSONDecodeError, OSError, subprocess.TimeoutExpired, ValueError) as error:
        _clear_output(output)
        _write_trusted_failure("wrapper_exception", completed=locals().get("completed"), error=error)
        print("trusted evaluation infrastructure failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
