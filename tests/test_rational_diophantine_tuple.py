from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "benchmarks" / "Mathematics" / "RationalDiophantineTuple"
sys.path.insert(0, str(ROOT))

from scripts.audit_tasks import _task_card_issues  # noqa: E402
from sle.evaluate import evaluate_candidate  # noqa: E402
from sle.spec import load_task_spec  # noqa: E402


def _load(relative_path: str, module_name: str):
    path = TASK_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load %s" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RationalDiophantineTupleTests(unittest.TestCase):
    def test_factory_quadruple_is_valid_and_scores_zero(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_evaluator")
        baseline = _load("solution.py", "rational_tuple_baseline")

        metrics = evaluator.evaluate(baseline.construct_tuple)

        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["tuple_size"], 4)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_published_sextuple_recomputes_the_reference_score(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_reference")

        witness = evaluator._reference_witness()
        valid, size, reason = evaluator.verify_tuple(witness)
        metrics = evaluator.evaluate(lambda: witness)

        self.assertTrue(valid, reason)
        self.assertEqual(size, 6)
        self.assertEqual(metrics["reference_size"], 6)
        self.assertEqual(metrics["combined_score"], 1.0)

    def test_equivalent_fraction_spellings_do_not_pad_cardinality(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_dedup")
        padded = [[1, 1], [3, 1], [8, 1], [120, 1], [2, 2], [6, 2]]

        valid, size, reason = evaluator.verify_tuple(padded)
        metrics = evaluator.evaluate(lambda: padded)

        self.assertTrue(valid, reason)
        self.assertEqual(size, 4)
        self.assertEqual(metrics["combined_score"], 0.0)

    def test_oracle_rejects_non_squares_without_float_approximation(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_exactness")

        valid, _size, reason = evaluator.verify_tuple([[1, 2], [1, 3]])

        self.assertFalse(valid)
        self.assertIn("not a rational square", reason)

    def test_score_is_uncapped_beyond_the_reference(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_uncapped")

        self.assertEqual(evaluator._normalized(6.0, 4.0, 6.0), 1.0)
        self.assertGreater(evaluator._normalized(7.0, 4.0, 6.0), 1.0)
        self.assertEqual(evaluator._normalized(3.0, 4.0, 6.0), 0.0)

    def test_malformed_and_excessive_outputs_fail_closed(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_limits")
        cases = [
            None,
            "1/2",
            [[1.0, 2], [3, 4]],
            [[True, 1], [3, 1]],
            [[1, 0], [3, 1]],
            [[0, 1], [3, 1]],
            [[10**1001, 1], [3, 1]],
            [[1, 1]] * (evaluator.MAX_ENTRIES + 1),
        ]
        for candidate in cases:
            with self.subTest(candidate_type=type(candidate).__name__):
                metrics = evaluator.evaluate(lambda candidate=candidate: candidate)
                self.assertEqual(metrics["valid"], 0.0)
                self.assertEqual(metrics["combined_score"], 0.0)

        metrics = evaluator.evaluate(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertEqual(metrics["valid"], 0.0)
        self.assertEqual(metrics["combined_score"], 0.0)

        total_too_large = [[10**999 + index, 1] for index in range(16)]
        valid, _size, reason = evaluator.verify_tuple(total_too_large)
        self.assertFalse(valid)
        self.assertIn("total integer digits", reason)

    def test_baseline_evaluation_is_deterministic(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_determinism")
        baseline = _load("solution.py", "rational_tuple_deterministic_baseline")

        self.assertEqual(
            evaluator.evaluate(baseline.construct_tuple),
            evaluator.evaluate(baseline.construct_tuple),
        )

    def test_package_contract_is_complete_and_machine_readable(self):
        required = (
            "Task.md",
            "TASK_CARD.yaml",
            "solution.py",
            "verification/evaluator.py",
            "frontier_eval/agent_files.txt",
            "frontier_eval/candidate_destination.txt",
            "frontier_eval/constraints.txt",
            "frontier_eval/entrypoint.txt",
            "frontier_eval/eval_command.txt",
            "frontier_eval/initial_program.txt",
            "frontier_eval/metadata.yaml",
            "frontier_eval/readonly_files.txt",
            "frontier_eval/run_eval.py",
            "frontier_eval/wave.yaml",
            "frontier_eval/contracts/tuple_canonicalizer_v1.py",
            "frontier_eval/contracts/evidence_predicate_v1.py",
            "frontier_eval/contracts/evaluation_panel_v1.json",
            "references/known_best.md",
        )
        self.assertEqual([name for name in required if not (TASK_DIR / name).is_file()], [])
        self.assertEqual(_task_card_issues(TASK_DIR / "TASK_CARD.yaml"), [])

        spec = load_task_spec(TASK_DIR)
        self.assertEqual(spec.task_id, "Mathematics/RationalDiophantineTuple")
        self.assertEqual(spec.entrypoint, "construct_tuple")
        self.assertEqual(spec.metadata["scientific_role"], "optimization")
        self.assertEqual(spec.metadata["score_mode"], "uncapped")
        self.assertEqual(
            spec.metadata["task_family_id"],
            "Mathematics/RationalDiophantineTuple",
        )

    def test_valid_tuple_emits_one_canonical_frontier_record(self):
        evaluator = _load("verification/evaluator.py", "rational_tuple_frontier")
        witness = evaluator._reference_witness()

        first = evaluator.evaluate(lambda: witness)
        equivalent = evaluator.evaluate(
            lambda: list(reversed(witness)) + [[22, 384]]
        )

        self.assertEqual(len(first["frontier_records"]), 1)
        self.assertEqual(first["frontier_records"], equivalent["frontier_records"])
        self.assertEqual(first["frontier_records"][0]["value"], 6.0)

    def test_baseline_runs_through_the_isolated_candidate_protocol(self):
        spec = load_task_spec(TASK_DIR)

        metrics = evaluate_candidate(spec, TASK_DIR / "solution.py", timeout_s=20)

        self.assertNotIn("infrastructure_failure", metrics)
        self.assertEqual(metrics["valid"], 1.0)
        self.assertEqual(metrics["tuple_size"], 4)
        self.assertEqual(metrics["combined_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
