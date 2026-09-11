#!/usr/bin/env python3
"""Paired normal/selection_blind scores for one frozen batch and proposal prefix.

Average seeds within tasks, then tasks within discipline/form/score-mode cells.
A missing, failed, short or incompatible run leaves the fixed-cohort estimate
unavailable. Discovery axes are not folded into these search-objective scores.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.batch_evolve import planned_run_cells  # noqa: E402
from scripts.reporting_trajectory import incumbent_events  # noqa: E402


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def _endpoint(run, config, definition, budget):
    manifest = run.get("evidence_identity") or {}
    expected = {"task_id": run["task"], "algorithm": run["algorithm"],
                "feedback_mode": run["feedback_mode"], "seed": run["seed"],
                "task_package_sha256": definition.get("task_package_sha256"),
                "runtime_source_sha256": config.get("runtime_source_sha256"),
                "llm_condition_sha256": config.get("llm_condition_sha256")}
    for field, value in expected.items():
        if value is None or (field.endswith("sha256") and not value) or manifest.get(field) != value:
            raise ValueError("missing or mismatched " + field)
    snapshot = run.get("trajectory_snapshot") or {}
    if snapshot.get("schema_version") != 2:
        raise ValueError("requires trajectory snapshot schema 2")
    events = snapshot.get("events") or []
    if len(events) < budget + 1:
        raise ValueError("trajectory shorter than requested budget")
    # A prefix is chosen before analysis; later events never choose its incumbent.
    events = events[:budget + 1]
    if any(e.get("budget_units") != index + 1 for index, e in enumerate(events)):
        raise ValueError("trajectory budget units must be contiguous from baseline")
    selected = incumbent_events(events)
    scores = [float(event["score"]) for event in selected]
    result = {"baseline": scores[0], "score": scores[-1], "gain": scores[-1] - scores[0],
              "auc": statistics.mean(scores),
              "oracle_calls": _number(events[-1].get("oracle_calls")),
              "wall_seconds": _number(events[-1].get("cumulative_wall_seconds"))}
    for field in ("input_tokens", "output_tokens", "total_tokens", "estimated_cost_usd"):
        # The baseline evaluates the supplied program and makes no model call.
        values = [_number((e.get("llm") or {}).get(field)) for e in events[1:]]
        result[field] = sum(values) if all(v is not None for v in values) else None
    return result


def _means(rows):
    return {field: (statistics.mean(row[field] for row in rows)
                    if all(row[field] is not None for row in rows) else None)
            for field in rows[0]}


def build_report(document: dict, proposal_budget: int | None = None) -> dict:
    config = document["config"]
    definitions = config.get("task_definitions")
    if not isinstance(definitions, dict) or set(definitions) != set(config["tasks"]):
        raise ValueError("requires frozen task_definitions for the entire planned cohort")
    for definition in definitions.values():
        if (not definition.get("discipline") or definition.get("form") not in ("optimization", "discovery")
                or not definition.get("score_mode")):
            raise ValueError("incomplete task classification")
    planned = planned_run_cells(config)
    if not {"normal", "selection_blind"}.issubset(config["feedback_modes"]):
        raise ValueError("plan requires both normal and selection_blind")
    budget = config["budget"] if proposal_budget is None else proposal_budget
    if isinstance(budget, bool) or not isinstance(budget, int) or not 0 <= budget <= config["budget"]:
        raise ValueError("proposal budget must be within the frozen plan")
    latest = {}
    for run in document.get("runs") or []:
        key = (run["task"], run["algorithm"], run["feedback_mode"], run["seed"])
        if key not in planned:
            raise ValueError("observed run is outside the fixed plan")
        latest[key] = run
    tasks = []
    for algorithm in config["algorithms"]:
        for task in config["tasks"]:
            definition = definitions[task]
            row = {"task": task, "algorithm": algorithm,
                   **{k: definition[k] for k in ("discipline", "form", "score_mode")},
                   "planned_pairs": len(config["seeds"]), "paired_n": 0,
                   "scheduled_runs": 2 * len(config["seeds"]), "successful_runs": 0,
                   "missing_runs": 0, "failed_runs": 0, "invalid_runs": 0, "diagnostics": []}
            pairs = []
            for seed in config["seeds"]:
                arms = {}
                for mode in ("normal", "selection_blind"):
                    run = latest.get((task, algorithm, mode, seed))
                    if run is None:
                        row["missing_runs"] += 1
                        continue
                    if run.get("error") or run.get("protocol_incomplete"):
                        row["failed_runs"] += 1
                        continue
                    try:
                        arms[mode] = _endpoint(run, config, definition, budget)
                    except (ValueError, TypeError, KeyError) as exc:
                        row["invalid_runs"] += 1
                        row["diagnostics"].append({"seed": seed, "mode": mode, "error": str(exc)})
                    else:
                        row["successful_runs"] += 1
                if len(arms) == 2:
                    if arms["normal"]["baseline"] != arms["selection_blind"]["baseline"]:
                        row["diagnostics"].append({"seed": seed, "error": "paired baselines differ"})
                        continue
                    pair = {mode + "_" + k: value for mode, values in arms.items() for k, value in values.items()}
                    pair["delta"] = arms["normal"]["score"] - arms["selection_blind"]["score"]
                    pair["delta_auc"] = arms["normal"]["auc"] - arms["selection_blind"]["auc"]
                    pairs.append(pair)
            row["paired_n"] = len(pairs)
            row["completion_rate"] = row["successful_runs"] / row["scheduled_runs"]
            row["metrics"] = _means(pairs) if len(pairs) == row["planned_pairs"] else None
            tasks.append(row)
    groups = {}
    for row in tasks:
        key = tuple(row[k] for k in ("algorithm", "discipline", "form", "score_mode"))
        groups.setdefault(key, []).append(row)
    disciplines = []
    for key, rows in sorted(groups.items()):
        group = dict(zip(("algorithm", "discipline", "form", "score_mode"), key))
        group.update(task_count=len(rows), tasks=[r["task"] for r in rows])
        for field in ("planned_pairs", "paired_n", "scheduled_runs", "successful_runs",
                      "missing_runs", "failed_runs", "invalid_runs"):
            group[field] = sum(row[field] for row in rows)
        group["completion_rate"] = group["successful_runs"] / group["scheduled_runs"]
        group["metrics"] = (_means([row["metrics"] for row in rows])
                            if all(row["metrics"] is not None for row in rows) else None)
        disciplines.append(group)
    return {"schema_version": 1, "model": (config.get("llm") or {}).get("model"),
            "llm_condition_sha256": config.get("llm_condition_sha256"),
            "runtime_source_sha256": config.get("runtime_source_sha256"),
            "proposal_budget": budget, "budget_units_including_baseline": budget + 1,
            "attempt_count": len(document.get("runs") or []),
            "scope": "paired search-objective scores; seeds within tasks then equally weighted tasks; fixed denominators",
            "cost_scope": "selected prefix of latest attempts; excludes failed/superseded attempt costs",
            "evidence_scope": document.get("evidence_scope", "unrecorded"),
            "trust_status": document.get("trust_status", "unrecorded"),
            "inference": "descriptive estimates only; local seed labels do not establish shared provider draws",
            "tasks": tasks, "disciplines": disciplines}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--proposal-budget", type=int)
    args = parser.parse_args(argv)
    report = build_report(json.loads(args.input.read_text()), args.proposal_budget)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print("report:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
