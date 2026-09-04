"""Canonical identifier for exactly reduced rational Diophantine tuples."""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction


def canonical_payload(values):
    reduced = sorted(set(Fraction(value) for value in values))
    payload = [[value.numerator, value.denominator] for value in reduced]
    return json.dumps(payload, separators=(",", ":"))


def canonical_tuple_id(values):
    digest = hashlib.sha256(canonical_payload(values).encode("utf-8")).hexdigest()
    return "sha256:" + digest
