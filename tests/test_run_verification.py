from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sle.algorithms.common import atomic_write_text
from sle.evaluation_ledger import EvaluationLedger
from sle.protocol import (
    TrajectoryEvent,
    append_event,
    load_trajectory,
    sha256_text,
    summarize_trajectory,
)
from sle.run_verification import verify_run


class RunVerificationTests(unittest.TestCase):
    def _run(self, root: Path) -> str:
        program = "def solve():\n    return 1\n"
        candidate_hash = sha256_text(program)
        manifest = {
            "schema_version": 1,
            "algorithm": "greedy_rewrite",
            "task_id": "ScientificComputing/Example",
            "task_contract_sha256": "a" * 64,
            "task_package_sha256": "b" * 64,
            "runtime_source_sha256": "c" * 64,
            "seed": 0,
            "feedback_mode": "normal",
        }
        atomic_write_text(root / "run_manifest.json", json.dumps(manifest) + "\n")
        receipt = EvaluationLedger(root).evaluate_once(
            {
                "kind": "baseline",
                **{key: manifest[key] for key in (
                    "task_id", "task_contract_sha256", "task_package_sha256",
                    "runtime_source_sha256",
                )},
                "step": 0,
                "candidate_sha256": candidate_hash,
            },
            lambda: {"combined_score": 0.25, "valid": 1.0},
        )
        event = TrajectoryEvent(
            step=0,
            oracle_calls=1,
            score=0.25,
            best_score=0.25,
            valid=True,
            accepted=True,
            wall_seconds=receipt["evaluation_wall_seconds"],
            cumulative_wall_seconds=receipt["evaluation_wall_seconds"],
            candidate_sha256=candidate_hash,
            parent_sha256=None,
            budget_units=1,
            metrics=receipt["metrics"],
            algorithm_metadata={"evaluation_request_id": receipt["request_id"]},
        )
        append_event(root / "trajectory.jsonl", event)
        summary = summarize_trajectory([event.to_dict()], budget=1)
        summary.update({
            "algorithm": "greedy_rewrite",
            "task_id": manifest["task_id"],
            "seed": 0,
            "feedback_mode": "normal",
            "budget": 0,
            "baseline_score": 0.25,
            "evaluation_ledger_snapshot": EvaluationLedger(root).snapshot(),
        })
        atomic_write_text(root / "summary.json", json.dumps(summary) + "\n")
        atomic_write_text(root / "best_program.py", program)
        return str(receipt["request_id"])

    def _proposal(self, root: Path, *, score: float, accepted: bool) -> str:
        parent = (root / "best_program.py").read_text(encoding="utf-8")
        program = "def solve():\n    return 2\n"
        candidate_hash = sha256_text(program)
        prompt_hash = "f" * 64
        receipt = EvaluationLedger(root).evaluate_once(
            {
                "kind": "proposal",
                "task_id": "ScientificComputing/Example",
                "task_contract_sha256": "a" * 64,
                "task_package_sha256": "b" * 64,
                "runtime_source_sha256": "c" * 64,
                "step": 1,
                "candidate_sha256": candidate_hash,
                "parent_sha256": sha256_text(parent),
                "prompt_sha256": prompt_hash,
            },
            lambda: {"combined_score": score, "valid": 1.0},
        )
        best_score = score if accepted else 0.25
        prior_cumulative = float(
            load_trajectory(root / "trajectory.jsonl")[-1]["cumulative_wall_seconds"]
        )
        append_event(
            root / "trajectory.jsonl",
            TrajectoryEvent(
                step=1,
                oracle_calls=2,
                score=score,
                best_score=best_score,
                valid=True,
                accepted=accepted,
                wall_seconds=receipt["evaluation_wall_seconds"],
                cumulative_wall_seconds=(
                    prior_cumulative + receipt["evaluation_wall_seconds"]
                ),
                candidate_sha256=candidate_hash,
                parent_sha256=sha256_text(parent),
                budget_units=2,
                metrics=receipt["metrics"],
                algorithm_metadata={
                    "evaluation_request_id": receipt["request_id"],
                    "prompt_sha256": prompt_hash,
                    "completed_after_active_wall_horizon": False,
                },
            ),
        )
        events = load_trajectory(root / "trajectory.jsonl")
        summary = summarize_trajectory(events, budget=2)
        prior = json.loads((root / "summary.json").read_text(encoding="utf-8"))
        prior.update(summary)
        prior["budget"] = 1
        prior["evaluation_ledger_snapshot"] = EvaluationLedger(root).snapshot()
        atomic_write_text(root / "summary.json", json.dumps(prior) + "\n")
        if accepted:
            atomic_write_text(root / "best_program.py", program)
        return program

    def test_verifies_complete_content_bound_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            self.assertTrue(verify_run(root)["verified"])

    def test_rejects_hand_edited_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            summary["best_score"] = 99.0
            (root / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "summary accounting"):
                verify_run(root)

    def test_rejects_receipt_not_referenced_by_the_trajectory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            EvaluationLedger(root).evaluate_once(
                {
                    "kind": "proposal",
                    "task_id": "ScientificComputing/Example",
                    "task_contract_sha256": "a" * 64,
                    "task_package_sha256": "b" * 64,
                    "runtime_source_sha256": "c" * 64,
                    "step": 1,
                    "candidate_sha256": "d" * 64,
                    "parent_sha256": "e" * 64,
                    "prompt_sha256": "f" * 64,
                },
                lambda: {"combined_score": 0.5, "valid": 1.0},
            )
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            summary["evaluation_ledger_snapshot"] = EvaluationLedger(root).snapshot()
            (root / "summary.json").write_text(
                json.dumps(summary) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "outside the trajectory"):
                verify_run(root)

    def test_rejects_event_score_that_differs_from_receipt_metrics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            event = json.loads(
                (root / "trajectory.jsonl").read_text(encoding="utf-8").strip()
            )
            event["score"] = 0.75
            event["best_score"] = 0.75
            (root / "trajectory.jsonl").write_text(
                json.dumps(event) + "\n", encoding="utf-8"
            )
            rebuilt = summarize_trajectory([event], budget=1)
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            summary.update(rebuilt)
            (root / "summary.json").write_text(
                json.dumps(summary) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "evaluation receipts"):
                verify_run(root)

    def test_rejects_improving_receipt_marked_not_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            self._proposal(root, score=0.5, accepted=False)
            with self.assertRaisesRegex(ValueError, "incumbent state"):
                verify_run(root)

    def test_rejects_oracle_counter_smaller_than_receipt_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            self._proposal(root, score=0.5, accepted=True)
            events = load_trajectory(root / "trajectory.jsonl")
            events[1]["oracle_calls"] = 1
            (root / "trajectory.jsonl").write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            summary.update(summarize_trajectory(events, budget=2))
            (root / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "accounting differs"):
                verify_run(root)

    def test_equal_score_candidate_cannot_replace_incumbent_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            proposal = self._proposal(root, score=0.25, accepted=False)
            atomic_write_text(root / "best_program.py", proposal)
            with self.assertRaisesRegex(ValueError, "replayed incumbent"):
                verify_run(root)

    def test_summary_cannot_redefine_the_frozen_proposal_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            self._proposal(root, score=0.5, accepted=True)
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            summary["budget"] = 0
            (root / "summary.json").write_text(
                json.dumps(summary) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "smaller than its trajectory"):
                verify_run(root)

    def test_release_verification_binds_external_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._run(root)
            with self.assertRaisesRegex(ValueError, "externally expected budget"):
                verify_run(root, expected_budget=1)


if __name__ == "__main__":
    unittest.main()
