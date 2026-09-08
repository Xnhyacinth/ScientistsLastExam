"""Invariants for QuantumFoundations/FourSettingMomentCertificate."""
from __future__ import annotations

import importlib.util
import itertools
import json
from fractions import Fraction
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks" / "Physics" / "FourSettingMomentCertificate"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR = _load("i4422_evaluator", TASK / "verification" / "evaluator.py")
ALGEBRA = _load("i4422_algebra", TASK / "verification" / "algebra.py")
REFERENCE = _load("i4422_reference", TASK / "verification" / "reference_certificate.py")
BASELINE = _load("i4422_baseline", TASK / "solution.py")


def _words(settings):
    return ([[[], []]]
            + [[[x], []] for x in range(settings[0])]
            + [[[], [y]] for y in range(settings[1])])


class TranscriptionTests(unittest.TestCase):
    def test_classical_bound_is_zero(self):
        best = -1e9
        for a in itertools.product((-1, 1), repeat=4):
            for b in itertools.product((-1, 1), repeat=4):
                total = -8
                for (left, right), coefficient in EVALUATOR.I4422_TIMES_FOUR.items():
                    value = 1
                    for x in left:
                        value *= a[x]
                    for y in right:
                        value *= b[y]
                    total += coefficient * value
                best = max(best, total / 4)
        self.assertEqual(best, 0.0)

    def test_the_two_copies_of_the_algebra_agree(self):
        for letters in itertools.product(range(4), repeat=3):
            self.assertEqual(EVALUATOR.reduce_side(letters), ALGEBRA.reduce_side(letters))
        for u in (((0,), ()), ((), (1,)), ((0, 1), ()), ((), ())):
            for v in (((2,), ()), ((), (3,)), ((), ()), ((1,), (0,))):
                self.assertEqual(EVALUATOR.multiply(u, v), ALGEBRA.multiply(u, v))
                self.assertEqual(REFERENCE.multiply(u, v), ALGEBRA.multiply(u, v))


class ContractTests(unittest.TestCase):
    def test_reference_uses_nonzero_extra_moments(self):
        instance = EVALUATOR.INSTANCES[0]
        basis, weights, vectors = EVALUATOR._read_certificate(
            REFERENCE.build_certificate(EVALUATOR._public_instance(instance)), instance)
        self.assertTrue(any(weight > 0 and vector[i] != 0
                            for weight, vector in zip(weights, vectors)
                            for i, word in enumerate(basis) if word not in instance["npa1"]))

    def test_baseline_is_valid_and_scores_exactly_zero(self):
        result = EVALUATOR.evaluate(BASELINE.build_certificate)
        self.assertEqual(result["valid"], 1.0)
        self.assertEqual(result["combined_score"], 0.0)
        for row in result["per_instance"]:
            self.assertEqual(row["certified_bound"], 4.0)

    def test_reference_improves_with_nonzero_mixed_moments(self):
        result = EVALUATOR.evaluate(REFERENCE.build_certificate)
        self.assertEqual(result["feasibility_rate"], 1.0)
        self.assertGreater(result["combined_score"], 0.3)
        self.assertLess(result["combined_score"], 0.8)
        bounds = [row["certified_bound"] for row in result["per_instance"]]
        self.assertTrue(all(0.25 < bound < 0.625 for bound in bounds))
        self.assertGreater(bounds[0], bounds[1])
        self.assertGreater(bounds[1], bounds[2])

    def test_both_score_anchors_have_exact_rational_witnesses(self):
        for budget, filename, expected in [
            (0, "level_one_certificate.json", 0.625),
            (24, "full_pool_certificate.json", EVALUATOR.I4422_SCORE_ONE),
        ]:
            instance = EVALUATOR._i4422("anchor", budget)
            certificate = json.loads((TASK / "references" / filename).read_text())
            basis, weights, vectors = EVALUATOR._read_certificate(certificate, instance)
            bound = EVALUATOR.certified_bound(basis, weights, vectors, instance)
            self.assertEqual(float(bound), expected)
            if budget == 0:
                self.assertEqual(bound, Fraction(5, 8))
            self.assertAlmostEqual(EVALUATOR._instance_score(instance, bound)[0], float(budget > 0))

    def test_level_one_bound_has_a_matching_feasible_moment_matrix(self):
        raw = json.loads((TASK / "references/level_one_moment_matrix.json").read_text())
        matrix = [[Fraction(*x) for x in row] for row in raw]
        self.assertTrue(ALGEBRA.is_positive_semidefinite(matrix, 9))
        self.assertTrue(all(matrix[i][i] == 1 for i in range(9)))
        self.assertTrue(all(matrix[i][j] == matrix[j][i] for i in range(9) for j in range(9)))
        value = Fraction(-8)
        for (a, b), coefficient in EVALUATOR.I4422_TIMES_FOUR.items():
            i = a[0] + 1 if a else 0
            j = b[0] + 5 if b else 0
            value += coefficient * matrix[i][j]
        self.assertEqual(value / 4, Fraction(5, 8))

    def test_old_pairing_shortcut_scores_zero_even_without_padding(self):
        shortcut = _load("pairing_shortcut", TASK / "references" / "pairing_shortcut.py")
        def candidate(instance):
            certificate = shortcut.build_certificate(instance)
            certificate["basis"] = certificate["basis"][:9]
            for square in certificate["squares"]:
                square["vector"] = square["vector"][:9]
            return certificate
        result = EVALUATOR.evaluate(candidate)
        self.assertEqual(result["feasibility_rate"], 1.0)
        self.assertEqual(result["combined_score"], 0.0)
        self.assertTrue(all(row["certified_bound"] == 3.5 for row in result["per_instance"]))

    def test_a_word_outside_the_frozen_pool_is_rejected(self):
        def candidate(instance):
            cert = BASELINE.build_certificate(instance)
            cert["basis"].append([[0, 2], []])
            cert["squares"][0]["vector"].append([0, 1])
            return cert

        result = EVALUATOR.evaluate(candidate)
        self.assertEqual(result["combined_score"], 0.0)

    def test_floats_are_rejected(self):
        for value in (0.5, [0.5, 1], float("nan")):
            with self.assertRaises(ValueError):
                EVALUATOR._fraction(value)

    def test_malformed_submissions_score_zero_without_raising(self):
        def sized(instance, **payload):
            return payload

        cases = {
            "empty": lambda i: {},
            "none": lambda i: None,
            "no_basis": lambda i: {"basis": [], "squares": [{"weight": [1, 1], "vector": []}]},
            "no_squares": lambda i: {"basis": _words(i["settings"]), "squares": []},
            "negative_weight": lambda i: {
                "basis": _words(i["settings"]),
                "squares": [{"weight": [-1, 1], "vector": [[1, 1]] * 9}]},
            "unreduced_word": lambda i: {
                "basis": [[[0, 0], []]], "squares": [{"weight": [1, 1], "vector": [[1, 1]]}]},
            "duplicate_words": lambda i: {
                "basis": [[[], []], [[], []]],
                "squares": [{"weight": [1, 1], "vector": [[1, 1], [1, 1]]}]},
            "over_budget_extras": lambda i: {
                "basis": _words(i["settings"]) + [[[0, 1], []], [[1, 0], []], [[2, 3], []],
                                                  [[3, 2], []], [[0, 2], []]],
                "squares": [{"weight": [1, 1], "vector": [[1, 1]] * 14}]},
            "zero_denominator": lambda i: {
                "basis": _words(i["settings"]),
                "squares": [{"weight": [1, 0], "vector": [[1, 1]] * 9}]},
            "boolean": lambda i: {
                "basis": _words(i["settings"]),
                "squares": [{"weight": True, "vector": [[1, 1]] * 9}]},
            "mismatched_vector": lambda i: {
                "basis": _words(i["settings"]),
                "squares": [{"weight": [1, 1], "vector": [[1, 1]]}]},
            "raises": lambda i: (_ for _ in ()).throw(RuntimeError("boom")),
        }
        self.assertGreaterEqual(len(cases), 10)
        for name, candidate in cases.items():
            with self.subTest(candidate=name):
                result = EVALUATOR.evaluate(candidate)
                self.assertEqual(result["combined_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
