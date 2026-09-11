"""Trusted evaluator entrypoints used by optional upstream search frameworks.

The framework process may write candidate programs, but every score still crosses the
same :func:`evaluate_candidate` boundary and therefore uses the isolated candidate
sandbox plus trusted oracle process.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sle.evaluate import CREDENTIAL_MARKERS, INVALID_SCORE, evaluate_candidate
from sle.metric_visibility import (
    EvaluationInfrastructureError, require_healthy_evaluations, require_scientific_result,
    search_visible_metrics, store_full_metrics, store_infrastructure_failure,
)
from sle.registry import find_task


TASK_ID = ""
TIMEOUT_S = 300.0
FULL_METRICS_DIR = ""


def configure(task_id: str, timeout_s: float, full_metrics_dir: str = "") -> None:
    global TASK_ID, TIMEOUT_S, FULL_METRICS_DIR
    TASK_ID = str(task_id)
    TIMEOUT_S = float(timeout_s)
    FULL_METRICS_DIR = str(full_metrics_dir or "")


def write_configured_wrapper(path: Path, task_id: str, timeout_s: float,
                             full_metrics_dir: Path | None = None) -> Path:
    """Write a per-run wrapper without credentials or mutable process-global routing."""
    repository = str(ROOT)
    source = (
        "import sys\n"
        "sys.path.insert(0, %r)\n"
        "from sle.upstream_evaluator import configure, evaluate, main, shinka_main\n"
        "configure(%r, %r, %r)\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n"
    ) % (repository, str(task_id), float(timeout_s),
         str(Path(full_metrics_dir).resolve()) if full_metrics_dir else "")
    path = Path(path)
    path.write_text(source, encoding="utf-8")
    return path


def evaluate(program_path: str) -> dict[str, Any]:
    if not TASK_ID:
        raise RuntimeError("upstream evaluator is not configured")
    sensitive = {}
    for key in tuple(os.environ):
        normalized = key.upper()
        if any(marker in normalized for marker in CREDENTIAL_MARKERS):
            sensitive[key] = os.environ.pop(key)
    try:
        spec = find_task(TASK_ID, include_uncertified=True)
        if FULL_METRICS_DIR:
            require_healthy_evaluations(Path(FULL_METRICS_DIR))
        candidate = Path(program_path).resolve()
        full_metrics = evaluate_candidate(spec, candidate, timeout_s=TIMEOUT_S)
        require_scientific_result(full_metrics)
        if FULL_METRICS_DIR:
            store_full_metrics(Path(FULL_METRICS_DIR), candidate, full_metrics)
        return search_visible_metrics(full_metrics)
    except Exception as exc:
        if FULL_METRICS_DIR:
            store_infrastructure_failure(Path(FULL_METRICS_DIR), {
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "metrics": locals().get("full_metrics"),
            })
        # Optional frameworks sometimes turn exception tracebacks into model feedback.
        # The private marker retains the cause; exception chaining would reopen that channel.
        raise EvaluationInfrastructureError("trusted evaluation infrastructure failure") from None
    finally:
        os.environ.update(sensitive)


def shinka_main(program_path: str, results_dir: str) -> int:
    results = Path(results_dir).resolve()
    results.mkdir(parents=True, exist_ok=True)
    for name in ("metrics.json", "correct.json"):
        (results / name).unlink(missing_ok=True)
    try:
        metrics = evaluate(program_path)
    except Exception:  # The framework must not count trusted faults as invalid candidates.
        print("trusted evaluation infrastructure failure", file=sys.stderr)
        return 2
    correct = float(metrics.get("valid", 0.0)) >= 1.0
    (results / "metrics.json").write_text(
        json.dumps(metrics, allow_nan=False, indent=2) + "\n", encoding="utf-8"
    )
    (results / "correct.json").write_text(
        json.dumps({"correct": correct, "error": metrics.get("error_message", "")}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args, _ = parser.parse_known_args(argv)
    return shinka_main(args.program_path, args.results_dir)


if __name__ == "__main__":
    raise SystemExit(main())
