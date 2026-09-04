"""Exact oracle for rational Diophantine tuples.

Every submitted rational is represented by a JSON-safe ``[numerator, denominator]``
pair.  Verification uses only Python integers and ``fractions.Fraction``; no
floating-point approximation enters the feasibility decision.
"""
from __future__ import annotations

import importlib.util
from collections.abc import Mapping
from fractions import Fraction
from math import isqrt
from pathlib import Path


MAX_ENTRIES = 64
MAX_INTEGER_DIGITS = 1000
MAX_TOTAL_DIGITS = 16_000
_MAX_INTEGER_BITS = 3322
TASK_DIR = Path(__file__).resolve().parent.parent
CONTRACT_DIR = TASK_DIR / "frontier_eval" / "contracts"


def _load_contract(name, filename):
    spec = importlib.util.spec_from_file_location(name, CONTRACT_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load frozen semantic contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_CANONICALIZER = _load_contract(
    "rational_diophantine_tuple_canonicalizer",
    "tuple_canonicalizer_v1.py",
)
_EVIDENCE = _load_contract(
    "rational_diophantine_tuple_evidence_predicate",
    "evidence_predicate_v1.py",
)


def _digit_count(value: int) -> int | None:
    magnitude = abs(value)
    if magnitude.bit_length() > _MAX_INTEGER_BITS:
        return None
    return len(str(magnitude))


def _canonical_tuple(raw) -> tuple[tuple[Fraction, ...] | None, str]:
    if raw is None or isinstance(raw, (str, bytes, Mapping)):
        return None, "expected a sequence of numerator-denominator pairs"
    try:
        iterator = iter(raw)
    except Exception as exc:  # noqa: BLE001 - untrusted candidate boundary
        return None, "not an iterable: %s" % exc

    values: set[Fraction] = set()
    total_digits = 0
    try:
        for index in range(MAX_ENTRIES + 1):
            try:
                item = next(iterator)
            except StopIteration:
                break
            if index == MAX_ENTRIES:
                return None, "more than %d entries" % MAX_ENTRIES
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                return None, "each rational must be [numerator, denominator]"
            numerator, denominator = item
            if type(numerator) is not int or type(denominator) is not int:
                return None, "numerator and denominator must be exact integers"
            numerator_digits = _digit_count(numerator)
            denominator_digits = _digit_count(denominator)
            if numerator_digits is None or denominator_digits is None:
                return None, "integer exceeds %d decimal digits" % MAX_INTEGER_DIGITS
            if (numerator_digits > MAX_INTEGER_DIGITS
                    or denominator_digits > MAX_INTEGER_DIGITS):
                return None, "integer exceeds %d decimal digits" % MAX_INTEGER_DIGITS
            total_digits += numerator_digits + denominator_digits
            if total_digits > MAX_TOTAL_DIGITS:
                return None, "output exceeds %d total integer digits" % MAX_TOTAL_DIGITS
            if denominator == 0:
                return None, "zero denominator"
            value = Fraction(numerator, denominator)
            if value == 0:
                return None, "tuple entries must be nonzero"
            values.add(value)
        else:  # pragma: no cover - the explicit index check returns first
            return None, "too many entries"
    except Exception as exc:  # noqa: BLE001 - untrusted candidate boundary
        return None, "malformed output: %s" % exc

    if len(values) < 2:
        return None, "need at least two distinct rationals"
    return tuple(sorted(values)), "ok"


def _is_rational_square(value: Fraction) -> bool:
    if value < 0:
        return False
    return (
        isqrt(value.numerator) ** 2 == value.numerator
        and isqrt(value.denominator) ** 2 == value.denominator
    )


def verify_tuple(raw) -> tuple[bool, int, str]:
    values, reason = _canonical_tuple(raw)
    if values is None:
        return False, 0, reason
    for left_index, left in enumerate(values):
        for right in values[left_index + 1:]:
            if not _is_rational_square(left * right + 1):
                return False, len(values), "a pair product plus one is not a rational square"
    return True, len(values), "ok"


def _reference_witness():
    """A published rational sextuple, retained so the score anchor is executable."""
    return [
        [11, 192], [35, 192], [155, 27], [512, 27],
        [1235, 48], [180873, 16],
    ]


def _reference_size() -> int:
    valid, size, reason = verify_tuple(_reference_witness())
    if not valid:
        raise RuntimeError("bundled reference witness failed verification: %s" % reason)
    return size


def _baseline_size() -> int:
    return len({Fraction(1), Fraction(3), Fraction(8), Fraction(120)})


def _normalized(value: float, baseline: float, sota: float) -> float:
    """Return 0 at baseline, 1 at the reference, and >1 beyond it."""
    denominator = sota - baseline
    if denominator <= 0:
        return 0.0
    return float(max(0.0, (value - baseline) / denominator))


def evaluate(construct_tuple) -> dict:
    try:
        raw = construct_tuple()
    except Exception as exc:  # noqa: BLE001 - untrusted candidate boundary
        return {
            "combined_score": 0.0,
            "valid": 0.0,
            "tuple_size": 0,
            "reason": "candidate raised: %s" % exc,
            "beat_sota": False,
            "frontier_records": [],
        }

    valid, size, reason = verify_tuple(raw)
    if not valid:
        return {
            "combined_score": 0.0,
            "valid": 0.0,
            "tuple_size": size,
            "reason": reason,
            "beat_sota": False,
            "frontier_records": [],
        }

    values, _ = _canonical_tuple(raw)
    assert values is not None
    canonical_id = _CANONICALIZER.canonical_tuple_id(values)
    record = _EVIDENCE.make_frontier_record(canonical_id, size, True)
    reference_size = _reference_size()
    score = _normalized(float(size), float(_baseline_size()), float(reference_size))
    return {
        "combined_score": score,
        "valid": 1.0,
        "feasibility_rate": 1.0,
        "tuple_size": size,
        "reference_size": reference_size,
        "beat_sota": bool(score > 1.0),
        "tuple_canonical_id": canonical_id,
        "frontier_records": [] if record is None else [record],
    }
