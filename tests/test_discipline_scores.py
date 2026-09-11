"""Fixed-cohort discipline summaries may not silently discard unobserved cells."""
import copy
import unittest

from scripts.report_discipline_scores import build_report


def fixture():
    tasks = {"T/A": {"discipline": "Physics", "form": "optimization", "score_mode": "uncapped",
                     "task_package_sha256": "package-a"},
             "T/B": {"discipline": "Physics", "form": "discovery", "score_mode": "clipped",
                     "task_package_sha256": "package-b"}}
    config = {"tasks": list(tasks), "task_definitions": tasks, "algorithms": ["greedy_rewrite"],
              "feedback_modes": ["normal", "selection_blind"], "seeds": [0, 1], "budget": 2,
              "runtime_source_sha256": "runtime", "llm_condition_sha256": "condition",
              "llm": {"model": "fixture"}}
    runs = []
    for task in tasks:
        for mode in config["feedback_modes"]:
            for seed in config["seeds"]:
                endpoint = 0.8 if mode == "normal" else 0.6
                events = []
                for step, score in enumerate([0.4, endpoint, 0.99]):
                    selected = 0.4 if step == 0 else endpoint
                    events.append({"step": step, "valid": True, "score": score,
                                   "accepted": step == 1, "best_score": selected,
                                   "budget_units": step + 1, "oracle_calls": step + 1,
                                   "cumulative_wall_seconds": (step + 1) * 2,
                                   "llm": {} if step == 0 else {"total_tokens": 10, "estimated_cost_usd": 0.01}})
                runs.append({"task": task, "algorithm": "greedy_rewrite", "feedback_mode": mode,
                             "seed": seed, "baseline": 0.4, "best": endpoint,
                             "evidence_identity": {"task_id": task, "algorithm": "greedy_rewrite",
                                 "feedback_mode": mode, "seed": seed,
                                 "task_package_sha256": tasks[task]["task_package_sha256"],
                                 "runtime_source_sha256": "runtime", "llm_condition_sha256": "condition"},
                             "trajectory_snapshot": {"schema_version": 2, "events": events}})
    return {"config": config, "runs": runs}


class DisciplineScoreTests(unittest.TestCase):
    def test_separate_forms_and_paired_incumbent_gain_at_fixed_prefix(self):
        result = build_report(fixture(), proposal_budget=1)
        self.assertEqual(len(result["disciplines"]), 2)
        for row in result["disciplines"]:
            self.assertEqual(row["paired_n"], 2)
            self.assertEqual(row["planned_pairs"], 2)
            self.assertAlmostEqual(row["metrics"]["delta"], 0.2)
            self.assertAlmostEqual(row["metrics"]["normal_gain"], 0.4)
            self.assertAlmostEqual(row["metrics"]["normal_auc"], 0.6)
            self.assertEqual(row["metrics"]["normal_total_tokens"], 10)
            self.assertEqual(row["metrics"]["normal_wall_seconds"], 4)

    def test_missing_arm_keeps_fixed_denominator_and_does_not_impute_score(self):
        document = fixture()
        document["runs"].pop()
        result = build_report(document)
        row = next(r for r in result["disciplines"] if r["form"] == "discovery")
        self.assertEqual(row["planned_pairs"], 2)
        self.assertEqual(row["paired_n"], 1)
        self.assertIsNone(row["metrics"])
        self.assertEqual(row["missing_runs"], 1)
        self.assertEqual(row["completion_rate"], 0.75)

    def test_changed_runtime_or_condition_cannot_enter_pair(self):
        for field in ("runtime_source_sha256", "llm_condition_sha256", "task_package_sha256"):
            with self.subTest(field=field):
                document = fixture()
                document["runs"][0]["evidence_identity"][field] = "different"
                result = build_report(document)
                self.assertIsNone(result["tasks"][0]["metrics"])
                self.assertEqual(result["tasks"][0]["invalid_runs"], 1)

    def test_latest_failed_retry_is_not_replaced_with_best_historical_attempt(self):
        document = fixture()
        retry = copy.deepcopy(document["runs"][0])
        retry["error"] = "provider outage"
        document["runs"].append(retry)
        result = build_report(document)
        self.assertIsNone(result["tasks"][0]["metrics"])
        self.assertEqual(result["tasks"][0]["failed_runs"], 1)
        self.assertEqual(result["attempt_count"], 9)

    def test_legacy_classification_and_out_of_range_prefix_are_rejected(self):
        document = fixture()
        del document["config"]["task_definitions"]
        with self.assertRaisesRegex(ValueError, "task_definitions"):
            build_report(document)
        with self.assertRaisesRegex(ValueError, "budget"):
            build_report(fixture(), proposal_budget=3)
