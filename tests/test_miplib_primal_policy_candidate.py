from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from _sandbox_tools import skip_unless_sandbox

from sle.rpc_codec import MAX_ARRAY_BYTES
from sle.secure_eval import trusted_evaluate

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks" / "Engineering" / "MIPLIBPrimalPolicy"
PRIVATE_DATA = TASK / "verification" / "private_data"
ASSETS_AVAILABLE = all(
    (PRIVATE_DATA / filename).is_file()
    for filename in (
        "comp12-2idx-baseline.sol.gz",
        "comp12-2idx-reference.sol.gz",
        "scpk4-baseline.sol.gz",
        "scpk4-reference.sol.gz",
    )
)


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


EVALUATOR = _module("miplib_primal_policy_evaluator", TASK / "verification" / "evaluator.py")
BASELINE = _module("miplib_primal_policy_baseline", TASK / "solution.py")
REFERENCE = _module(
    "miplib_primal_policy_reference",
    TASK / "verification" / "reference_policy.py",
)
REPLAY = _module(
    "miplib_primal_policy_replay",
    TASK / "verification" / "official_checker_replay.py",
)
PUBLIC_HEURISTIC = _module(
    "miplib_primal_policy_public_heuristic",
    TASK / "references" / "public_coordinate_descent.py",
)


class MIPLIBPrimalPolicyTests(unittest.TestCase):
    def test_frozen_sources_and_licenses_match_manifest(self):
        manifest = json.loads(
            (TASK / "references" / "source_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        for artifact in manifest["artifacts"]:
            path = TASK / artifact["path"]
            self.assertTrue(path.is_file(), artifact["path"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                artifact["sha256"],
                artifact["path"],
            )
        for artifact in manifest["external_solution_assets"]:
            path = TASK / artifact["path"]
            if path.is_file():
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    artifact["sha256"],
                    artifact["path"],
                )
        attribution = (TASK / "references" / "DATA_LICENSE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("CC BY-SA 4.0", attribution)
        self.assertIn("Matias Sørensen", attribution)
        self.assertIn("Shunji Umetani", attribution)

    @unittest.skipUnless(ASSETS_AVAILABLE, "run references/fetch_solution_assets.py")
    def test_frozen_baseline_and_reference_solutions_replay_exactly(self):
        expected = {
            "comp12-2idx": (11863, 16803, 391, 277),
            "scpk4": (100000, 2000, 327, 318),
        }
        for name, (n_vars, n_rows, baseline_obj, reference_obj) in expected.items():
            with self.subTest(name=name):
                model = EVALUATOR._load_model(name)
                baseline = EVALUATOR._load_frozen_assignment(name, "baseline")
                reference = EVALUATOR._load_frozen_assignment(name, "reference")
                self.assertEqual(model["num_variables"], n_vars)
                self.assertEqual(model["num_constraints"], n_rows)
                self.assertEqual(
                    EVALUATOR._check_assignment(model, baseline), baseline_obj
                )
                self.assertEqual(
                    EVALUATOR._check_assignment(model, reference), reference_obj
                )

    @unittest.skipUnless(ASSETS_AVAILABLE, "run references/fetch_solution_assets.py")
    def test_baseline_scores_zero_and_reference_scores_one(self):
        baseline = EVALUATOR.evaluate(BASELINE.improve_primal)
        reference = EVALUATOR.evaluate(REFERENCE.improve_primal)
        self.assertEqual(baseline["valid"], 1.0)
        self.assertEqual(baseline["combined_score"], 0.0)
        self.assertEqual(reference["valid"], 1.0)
        self.assertEqual(reference["combined_score"], 1.0)
        self.assertEqual(
            [row["objective"] for row in reference["per_instance"]],
            [277, 318],
        )

    @unittest.skipUnless(ASSETS_AVAILABLE, "run references/fetch_solution_assets.py")
    def test_public_input_heuristic_is_feasible_but_not_a_positive_onramp(self):
        result = EVALUATOR.evaluate(PUBLIC_HEURISTIC.improve_primal)
        self.assertEqual(result["valid"], 1.0)
        self.assertEqual(result["combined_score"], 0.0)

    @skip_unless_sandbox("bwrap")
    @unittest.skipUnless(ASSETS_AVAILABLE, "run references/fetch_solution_assets.py")
    def test_baseline_crosses_the_real_candidate_rpc_boundary(self):
        result = trusted_evaluate(
            TASK,
            TASK / "solution.py",
            "improve_primal",
            "uncapped",
            300.0,
        )
        self.assertEqual(result["combined_score"], 0.0)
        self.assertEqual(result["valid"], 1.0)

    @unittest.skipUnless(ASSETS_AVAILABLE, "run references/fetch_solution_assets.py")
    def test_candidate_receives_reusable_sparse_problem_not_reference(self):
        observed = []

        def policy(problem):
            observed.append({
                "keys": set(problem),
                "shape": (
                    len(problem["row_ptr"]),
                    len(problem["column_indices"]),
                ),
            })
            return problem["incumbent"].copy()

        result = EVALUATOR.evaluate(policy)
        self.assertEqual(result["combined_score"], 0.0)
        self.assertEqual(result["valid"], 1.0)
        self.assertEqual(len(observed), 2)
        for row in observed:
            self.assertNotIn("reference", row["keys"])
            self.assertNotIn("reference_objective", row["keys"])
            self.assertGreater(row["shape"][0], 1)
            self.assertGreater(row["shape"][1], 1)

    def test_every_payload_array_fits_the_candidate_rpc_limit(self):
        array_fields = (
            "objective",
            "lower_bounds",
            "upper_bounds",
            "rhs",
            "row_ptr",
            "column_indices",
            "coefficients",
        )
        for name in ("comp12-2idx", "scpk4"):
            with self.subTest(name=name):
                model = EVALUATOR._load_model(name)
                sizes = [model[field].nbytes for field in array_fields]
                self.assertTrue(all(size <= MAX_ARRAY_BYTES for size in sizes))
                self.assertLess(sum(sizes), 32 * 1024 * 1024)

    def test_frozen_artifact_failures_are_infrastructure_errors(self):
        with patch.object(
            EVALUATOR, "_load_model", side_effect=ValueError("hash differs")
        ), self.assertRaisesRegex(ValueError, "hash differs"):
            EVALUATOR.evaluate(BASELINE.improve_primal)

    @unittest.skipUnless(ASSETS_AVAILABLE, "run references/fetch_solution_assets.py")
    def test_invalid_assignment_types_and_infeasible_values_score_zero(self):
        policies = (
            lambda problem: [0] * (problem["num_variables"] - 1),
            lambda problem: np.full(problem["num_variables"], 0.5),
            lambda problem: np.ones(problem["num_variables"], dtype=bool),
            lambda problem: np.zeros(problem["num_variables"], dtype=np.int64),
        )
        for policy in policies:
            with self.subTest(policy=policy):
                result = EVALUATOR.evaluate(policy)
                self.assertEqual(result["combined_score"], 0.0)
                self.assertEqual(result["valid"], 0.0)
                self.assertTrue(all(
                    row["valid"] is False for row in result["per_instance"]
                ))

    def test_score_is_not_clipped_above_reference(self):
        self.assertGreater(EVALUATOR._normalized(276, 391, 277), 1.0)
        card = (TASK / "TASK_CARD.yaml").read_text(encoding="utf-8")
        self.assertIn("fixed MILPs have finite objective ranges", card)

    def test_checker_parser_rejects_failed_checks_even_with_exit_zero(self):
        failed = (
            "Read MPS: 1\nRead SOL: 1\n"
            "Check SOL: Integrality 1 Constraints 0 Objective 1\n"
        )
        passed = (
            "Read MPS: 1\nRead SOL: 1\n"
            "Check SOL: Integrality 1 Constraints 1 Objective 1\n"
        )
        self.assertFalse(REPLAY.checker_accepted(0, failed))
        self.assertTrue(REPLAY.checker_accepted(0, passed))
        self.assertFalse(REPLAY.checker_accepted(1, passed))

    @unittest.skipUnless(
        os.environ.get("MIPLIB_SOLCHECKER") and ASSETS_AVAILABLE,
        "set MIPLIB_SOLCHECKER to replay the patched native checker",
    )
    def test_optional_patched_checker_replay(self):
        checker = Path(os.environ["MIPLIB_SOLCHECKER"])
        for name in ("comp12-2idx", "scpk4"):
            for kind in ("baseline", "reference"):
                with self.subTest(name=name, kind=kind):
                    completed = REPLAY.run_checker(
                        checker,
                        TASK / "verification" / "data" / (name + ".mps.gz"),
                        TASK / "verification" / "private_data"
                        / (name + "-" + kind + ".sol.gz"),
                    )
                    self.assertTrue(
                        REPLAY.checker_accepted(
                            completed.returncode, completed.stdout
                        ),
                        completed.stdout + completed.stderr,
                    )


if __name__ == "__main__":
    unittest.main()
