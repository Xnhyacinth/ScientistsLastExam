"""CLI bridge for tasks supported by ``sle eval`` and its candidate sandbox.

Never import candidates here. Legacy in-process oracle/CandidateProxy wrappers
must first migrate to that trusted protocol. The public file/stdout contain only
search-visible metrics. Full metrics are discarded unless the operator supplies
an explicit private sidecar directory outside the proposal agent's workspace.

Task-local wrappers launch this file using only the standard library, preserving
an explicit TASK_ID and EVAL_TIMEOUT_S. Exit 2 means evaluation infrastructure
failed: no score file or stdout score is produced, including on import failure.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SENSITIVE_MARKERS = ("API_KEY", "AUTHORIZATION", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def child_environment(root):
    environment = {k: v for k, v in os.environ.items()
                   if not any(marker in k.upper() for marker in SENSITIVE_MARKERS)}
    environment["PYTHONPATH"] = str(root)
    environment.pop("SLE_TRUSTED_EVAL_LOG", None)
    return environment


def _private_directory(value, candidate, output):
    """No implicit sidecar beside public files; an operator must explicitly opt in.

    Reject the known proposal/public roots, including symlink aliases. The operator
    remains responsible for not mounting any other private directory in their agent.
    """
    if value is None:
        return None
    directory = Path(value).resolve()
    for public_root in (candidate.parent.resolve(), output.parent.resolve()):
        if os.path.commonpath((str(directory), str(public_root))) == str(public_root):
            raise ValueError("trusted metrics directory overlaps a public workspace")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if directory.stat().st_mode & 0o077:
        raise ValueError("trusted metrics directory must be private (mode 0700)")
    return directory


def _atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name, dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, allow_nan=False, indent=2)
            handle.write("\n")
        os.replace(temporary, str(path))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(task_id: str, root: Path, timeout: float, argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--metrics-out", required=True)
    parser.add_argument("--full-metrics-dir")
    parser.add_argument("--timeout", type=float, default=timeout)
    args = parser.parse_args(argv)
    output = Path(args.metrics_out).absolute()
    candidate = Path(args.candidate).resolve()
    trusted = None
    stage = "initialization"
    diagnostic = {}
    try:
        # Never let a failed attempt leave a previous candidate's usable score.
        output.unlink(missing_ok=True)
        trusted = _private_directory(args.full_metrics_dir, candidate, output)
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        root = root.resolve()
        sys.path.insert(0, str(root))
        # Delayed imports keep package initialization failures on the no-score path.
        stage = "loading trusted evaluation support"
        from sle.metric_visibility import search_visible_metrics, store_full_metrics

        environment = child_environment(root)
        stage = "launching trusted evaluation"
        done = subprocess.run(
            [sys.executable, "-m", "sle", "eval", "--task", task_id,
             "--allow-uncertified", "--candidate", str(candidate),
             "--timeout", str(args.timeout)],
            cwd=str(root), capture_output=True, text=True,
            timeout=args.timeout + 120, env=environment,
        )
        diagnostic.update(returncode=done.returncode, stderr=(done.stderr or "")[-4000:])
        if done.returncode:
            raise RuntimeError("trusted evaluation exited %d" % done.returncode)
        stage = "reading trusted evaluation result"
        result = json.loads(done.stdout)
        if not isinstance(result, dict):
            raise ValueError("metrics must be a JSON object")
        diagnostic["metrics"] = result
        if result.get("infrastructure_failure"):
            raise RuntimeError("trusted evaluator reported infrastructure failure")
        # Defensive validation for alternate/future trusted CLI implementations.
        for key in ("combined_score", "valid"):
            value = result.get(key)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("metrics require a finite numeric %s" % key)
        if result["valid"] not in (0, 1):
            raise ValueError("valid must be zero or one")
        if "raw_score" in result:
            value = result["raw_score"]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("raw_score must be finite and numeric")
        # Reject non-finite nested values as an infrastructure fault as well.
        json.dumps(result, allow_nan=False)
        result.setdefault("raw_score", result["combined_score"])
        public = search_visible_metrics(result)
        stage = "persisting trusted metrics"
        if trusted is not None:
            if candidate.is_file():
                store_full_metrics(trusted, candidate, result)
            else:
                _atomic_json(trusted / "last_missing_candidate.json", result)
        stage = "writing public metrics"
        _atomic_json(output, public)
        print(json.dumps(public, default=str, allow_nan=False))
        return 0
    except Exception as exc:
        diagnostic.update(stage=stage, exception_type=type(exc).__name__, message=str(exc))
        try:
            output.unlink(missing_ok=True)
            if trusted is not None:
                # Malformed JSON may contain NaN; a text rendering is private and bounded.
                diagnostic["metrics"] = repr(diagnostic.get("metrics"))[:8000]
                _atomic_json(trusted / "last_infrastructure_failure.json", diagnostic)
        except (OSError, TypeError, ValueError):
            pass
        # Only controlled text reaches the search harness; traceback/source/env
        # from contributed trusted code is never a public diagnostic string.
        print("evaluation infrastructure failure during " + stage, file=sys.stderr)
        return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--timeout", type=float, required=True)
    args, remaining = parser.parse_known_args(argv)
    return run(args.task, args.root, args.timeout, remaining)


if __name__ == "__main__":
    raise SystemExit(main())
