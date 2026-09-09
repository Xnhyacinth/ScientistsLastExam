from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import unittest

import numpy as np

TASK = Path(__file__).resolve().parents[1]/"benchmarks/Engineering/IMUBiasCalibration"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IMUBiasCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = load("imu_eval", TASK/"verification/evaluator.py")
        cls.reference = load("imu_ref", TASK/"verification/reference_solver.py")
        cls.baseline = load("imu_base", TASK/"solution.py")

    def test_reference_deterministic_and_baseline_zero(self):
        first = self.oracle.evaluate(self.reference.infer_imu)
        self.assertEqual(first, self.oracle.evaluate(self.reference.infer_imu))
        self.assertEqual(first["valid"], 1)
        self.assertGreater(first["combined_score"], 0)
        self.assertGreater(first["heldout_combined_score"], 0)
        base = self.oracle.evaluate(self.baseline.infer_imu)
        self.assertEqual(base["valid"], 1)
        self.assertEqual(base["combined_score"], 0)
        self.assertEqual(base["heldout_combined_score"], 0)

    def test_budget_design_and_nonorthogonality_are_material(self):
        full = self.oracle.evaluate(self.reference.infer_imu)
        for options in ({"measurement_limit": 6}, {"measurement_limit": 12},
                        {"central_only": True}, {"sequential": True}, {"diagonal_only": True}):
            ablated = self.oracle.evaluate(lambda p, m: self.reference._infer_imu(p, m, **options))
            self.assertEqual(ablated["valid"], 1)
            for metric in ("combined_score", "heldout_combined_score"):
                self.assertGreater(full[metric]-ablated[metric], .02)

    def test_every_fault_diagnostic_matters_in_both_splits(self):
        full = self.oracle.evaluate(self.reference.infer_imu)
        for fault in self.oracle.FAULTS:
            ablated = self.oracle.evaluate(lambda p, m: self.reference._infer_imu(p, m, disabled_faults=(fault,)))
            for metric in ("combined_score", "heldout_combined_score"):
                self.assertGreater(full[metric]-ablated[metric], .01)

    def test_world_families_do_not_leak_through_public_problem(self):
        for worlds in (self.oracle.DEVELOPMENT_WORLDS, self.oracle.HELDOUT_WORLDS):
            self.assertEqual({s["kind"] for s in worlds}, {"supported", *self.oracle.FAULTS})
        for fault in self.oracle.FAULTS:
            self.assertEqual(self.oracle.public_problem({"seed": 913, "kind": fault}),
                             self.oracle.public_problem({"seed": 913, "kind": "supported"}))

    def test_twelve_parameter_model_and_independent_prediction(self):
        spec = {"seed": 77, "kind": "supported"}
        world, problem = self.oracle._world(spec), self.oracle.public_problem(spec)
        setting = problem["prediction_settings"][0]
        expected = world["matrix"]@(self.oracle.GRAVITY*np.array(setting["orientation"])) + world["bias"] + world["drift"]*(setting["temperature_c"]-25)
        np.testing.assert_allclose(self.oracle._clean(world, setting), expected)
        self.assertEqual(np.count_nonzero(np.tril(world["matrix"], -1)), 0)
        design = self.reference._features(problem, problem["settings"])
        self.assertEqual(np.linalg.matrix_rank(design), design.shape[1])

    def test_budget_charged_repeats_noisy_and_overrun_sticky(self):
        spec = {"seed": 5, "kind": "supported"}
        problem = self.oracle.public_problem(spec)
        campaign = self.oracle._Campaign(self.oracle._world(spec), problem)
        one, two = campaign(0), campaign(0)
        self.assertEqual(campaign.calls, 2)
        self.assertNotEqual(one["accel_mps2"], two["accel_mps2"])
        for _ in range(problem["measurement_budget"]-2):
            campaign(0)
        with self.assertRaises(RuntimeError):
            campaign(0)
        self.assertTrue(campaign.violated)
        def overspend(p, measure):
            answer = self.baseline.infer_imu(p, measure)
            ids = []
            for _ in range(p["measurement_budget"]+1):
                try:
                    ids.append(measure(0)["query_id"])
                except RuntimeError:
                    pass
            answer["evidence_ids"] = ids
            return answer
        result = self.oracle.evaluate(overspend)
        self.assertEqual(result["valid"], 0)
        self.assertEqual(result["combined_score"], 0)

    def test_invalid_settings_fail_closed_even_when_caught(self):
        for setting in (-1, True, 1.5, 100000, "0"):
            def bad(p, measure):
                try:
                    measure(setting)
                except ValueError:
                    pass
                return self.baseline.infer_imu(p, measure)
            self.assertEqual(self.oracle.evaluate(bad)["valid"], 0)

    def test_fault_matrix(self):
        mutations = [("bias_mps2", [0, 0]), ("bias_mps2", [0, 0, float("nan")]),
                     ("temperature_drift_mps2_per_c", [0, float("inf"), 0]),
                     ("prediction_accel_mps2", [0, 0, 0]), ("confidence", True),
                     ("confidence", -1), ("confidence", float("nan")), ("abstain", 1),
                     ("diagnosis", []), ("diagnosis", "fake"), ("evidence_ids", ["fake"]),
                     ("evidence_ids", [["q001"]]), ("fault_axis", 5), ("extra", 1),
                     ("calibration_matrix", [[1, 0, 0], [.1, 1, 0], [0, 0, 1]])]
        for key, value in mutations:
            def bad(p, measure):
                return {**self.baseline.infer_imu(p, measure), key: value}
            with self.subTest(key=key, value=value):
                result = self.oracle.evaluate(bad)
                self.assertEqual(result["valid"], 0)
                self.assertEqual(result["combined_score"], 0)
        for output in ({}, None, [], "bad"):
            result = self.oracle.evaluate(lambda p, m: output)
            self.assertEqual(result["valid"], 0)
            self.assertEqual(result["combined_score"], 0)

    def test_blanket_refusal_for_any_diagnosis_is_zero(self):
        for diagnosis in self.oracle.VALID_DIAGNOSES:
            for axis in range(3):
                def refuse(p, m):
                    result = self.baseline.infer_imu(p, m)
                    result.update(abstain=True, diagnosis=diagnosis,
                                  fault_axis=axis if diagnosis in self.oracle.FAULTS else None)
                    return result
                result = self.oracle.evaluate(refuse)
                self.assertEqual(result["valid"], 1)
                self.assertEqual(result["combined_score"], 0)
                self.assertEqual(result["heldout_combined_score"], 0)
                self.assertEqual(result["attempted_discovery"], 0)

    def test_mechanism_quality_is_not_composite_and_denominators_include_misses(self):
        empty = {"kind": "supported", "valid": True, "abstained": False,
                 "mechanism_correct": True, "matrix_score": .6, "science_score": .8,
                 "bias_score": 1, "drift_score": 1, "prediction_score": 1,
                 "combined_score": .8, "correct_refusal": False, "false_discovery": False,
                 "fault_axis_correct": False, "measurements_used": 3, "confidence_calibration_score": 1}
        rows = [empty, {**empty, "abstained": True, "mechanism_correct": False, "matrix_score": 0},
                {**empty, "valid": False, "abstained": True, "mechanism_correct": False, "matrix_score": 0},
                {**empty, "kind": "thermal_nonlinearity", "false_discovery": True},
                {**empty, "kind": "axis_misalignment", "abstained": True, "correct_refusal": True}]
        result = self.oracle._summary(rows)
        self.assertAlmostEqual(result["mechanism_score"], .2)
        self.assertEqual(result["mechanism_denominator"], 3)
        self.assertEqual(result["discovery_coverage"], 1/3)
        self.assertEqual(result["discovery_denominator"], 3)
        self.assertEqual(result["false_discovery_rate"], 1/2)
        self.assertEqual(result["false_discovery_denominator"], 2)
        self.assertEqual(result["correct_refusal_rate"], 1/2)
        self.assertEqual(result["correct_refusal_denominator"], 2)

    def test_localization_is_required_for_refusal_credit(self):
        spec = {"seed": 9, "kind": "thermal_nonlinearity"}
        world, problem = self.oracle._world(spec), self.oracle.public_problem(spec)
        answer = self.baseline.infer_imu(problem, None)
        answer.update(abstain=True, diagnosis=spec["kind"], fault_axis=(world["axis"]+1) % 3)
        self.assertEqual(self.oracle._score(world, answer, problem)["combined_score"], 0)
        answer["fault_axis"] = world["axis"]
        self.assertEqual(self.oracle._score(world, answer, problem)["combined_score"], 1)

    def test_input_mutation_does_not_change_budget(self):
        def bad(problem, measure):
            problem["measurement_budget"] = 0
            problem["settings"][0]["temperature_c"] = 999
            answer = self.baseline.infer_imu(problem, measure)
            answer["evidence_ids"] = [measure(0)["query_id"]]
            return answer
        self.assertEqual(self.oracle.evaluate(bad)["valid"], 1)

    def test_metric_key_parity_and_session_reset(self):
        baseline = self.baseline.infer_imu
        class Candidate:
            count = 0
            def reset_session(self):
                self.count += 1
            def __call__(self, problem, measure):
                return baseline(problem, measure)
        candidate = Candidate()
        good = self.oracle.evaluate(candidate)
        bad = self.oracle.evaluate(lambda p, m: {})
        self.assertEqual(candidate.count, len(good["per_instance"]))
        self.assertEqual(set(good), set(bad))
        self.assertEqual(set(good["per_instance"][0]), set(bad["per_instance"][0]))
