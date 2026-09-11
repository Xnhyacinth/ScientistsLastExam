"""Replay the recorded incumbent for analysis without selecting on sealed metrics."""
from __future__ import annotations

import json
import math
from pathlib import Path


def _score(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("trajectory score must be a finite number")
    return float(value)


def read_events(path: Path) -> list[dict]:
    """Read a trace without silently dropping corrupt lines."""
    events = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError("%s:%d: invalid trajectory JSON" % (path, number)) from exc
    return events


def trajectory_selection_evidence(events: list[dict]) -> dict:
    """Keep historical score-based reconstruction distinct from recorded selection.

    Legacy traces remain readable for diagnosis; absence of acceptance is never
    presented as proof that an artifact was accepted before the time limit.
    """
    missing = [row.get("step") for row in events
               if isinstance(row, dict) and row.get("step") != 0 and "accepted" not in row]
    return {"status": "legacy_inferred" if missing else "recorded",
            "missing_acceptance_steps": missing,
            "endpoint": "incumbent",
            "legacy_rule": "strict_score_improvement" if missing else None}


def read_incumbents(path: Path) -> list[dict]:
    """Return the selected artifact at every step, including the baseline.

    Modern traces record acceptance explicitly (a late result may be valid but not
    accepted). Legacy traces without that field use strict score improvement.
    """
    try:
        return incumbent_events(read_events(path))
    except ValueError as exc:
        raise ValueError("%s: %s" % (path, exc)) from exc


def incumbent_events(events: list[dict]) -> list[dict]:
    """Replay an in-memory batch snapshot using the same selection rule."""
    incumbent = None
    selected = []
    for step, event in enumerate(events):
        if not isinstance(event, dict) or event.get("step") != step:
            raise ValueError("trajectory steps must be contiguous from baseline zero")
        valid = event.get("valid")
        if valid not in (True, False, 0, 1):
            raise ValueError("trajectory validity must be boolean")
        score = _score(event.get("score"))
        metrics = event.get("metrics")
        if metrics is not None and not isinstance(metrics, dict):
            raise ValueError("trajectory metrics must be an object at step %d" % step)
        if metrics and "combined_score" in metrics and _score(metrics["combined_score"]) != score:
            raise ValueError("score differs from metrics.combined_score at step %d" % step)
        if step == 0:
            if not valid:
                raise ValueError("trajectory baseline must be valid")
            incumbent = event
        else:
            accepted = event.get("accepted", bool(valid and score > _score(incumbent["score"])))
            if not isinstance(accepted, bool):
                raise ValueError("trajectory acceptance must be boolean")
            if accepted:
                if not valid or score <= _score(incumbent["score"]):
                    raise ValueError("accepted proposal must strictly improve the incumbent")
                incumbent = event
        if "best_score" in event and _score(event["best_score"]) != _score(incumbent["score"]):
            raise ValueError("recorded best score differs from the selected artifact")
        selected.append(incumbent)
    return selected
