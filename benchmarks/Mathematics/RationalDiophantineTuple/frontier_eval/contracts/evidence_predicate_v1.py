"""Evidence gate for an exactly verified rational Diophantine tuple."""
from __future__ import annotations


CELL_ID = "exact-rational-diophantine-tuple"


def make_frontier_record(canonical_id, tuple_size, valid):
    if not valid:
        return None
    if not isinstance(canonical_id, str) or not canonical_id.startswith("sha256:"):
        return None
    if isinstance(tuple_size, bool) or not isinstance(tuple_size, int) or tuple_size < 2:
        return None
    return {
        "cell_id": CELL_ID,
        "canonical_id": canonical_id,
        "value": float(tuple_size),
    }
