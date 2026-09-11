"""The documented headroom: the reference with the branch scan run at every position.

The down side tests every position with one vector (all answers at t - gap, dissents counted per
position); the up side needs one vector per position because an output T halts at cutoff one.
Position 0 keeps the reference's schedule; later positions use a coarser grid of eight and six
expected dissents, so the scan leaves room for the library.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

TASK = Path(__file__).resolve().parents[2] / "benchmarks/ComputerScience/SparseVectorAudit"
_spec = importlib.util.spec_from_file_location("sva_ref_for_headroom", TASK / "verification/reference_library_scan.py")
ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref)

LATER_STEP = 8
LATER_EXPECTED = 6.0


def audit(problem, sample):
    k, t = int(problem["n_queries"]), int(problem["threshold"])
    lo_q, hi_q = int(problem["query_min"]), int(problem["query_max"])
    eps, delta = float(problem["epsilon"]), float(problem["delta"])
    budget = int(problem["sample_budget"])
    patterns = list(problem["output_patterns"])
    spent = [0]

    def run(q, n):
        n = int(min(n, budget - spent[0]))
        if n <= 0:
            return None, 0
        spent[0] += n
        return sample(list(q), n), n

    def dissents(counts, side, pos):
        want = "F" if side == "up" else "T"
        return sum(v for o, v in counts.items() if o[pos:pos + 1] == want)

    def probe(gap, side, positions, expected):
        """Zero-dissent positions among `positions` at this gap, or None when unaffordable."""
        p = ref._dissent_probability(problem, gap, side)
        if side == "down" and len(positions) > 1:
            p = p * (1.0 - p) ** (len(positions) - 1)   # the last position is reached only past every earlier one
        n = math.ceil(expected / max(p, 1e-300))
        if n > ref.SCAN_MAX_RUNS:
            return None
        if side == "down":
            q = [lo_q] * k
            for j in positions:
                q[j] = t - gap
        else:
            (j,) = positions
            q = [lo_q] * k
            q[j] = t + gap
        counts, _ = run(q, n)
        if counts is None:
            return None
        return [j for j in positions if dissents(counts, side, j) == 0]

    def confirm(side, pos, offset):
        dataset, neighbour = [lo_q] * k, [lo_q] * k
        want = "F" if side == "up" else "T"
        if side == "up":
            dataset[pos], neighbour[pos] = t + offset, t + offset - 1
        else:
            dataset[pos], neighbour[pos] = t - offset, t - offset + 1
        event = [o for o in patterns if o[pos:pos + 1] == want]
        p_next = ref._dissent_probability(problem, offset - 1, side)
        n_conf = min(20000, max(2000, math.ceil(60.0 / max(p_next, 1e-9))))
        cn, nn = run(neighbour, n_conf)
        cd, nd = run(dataset, n_conf)
        if cn is None or cd is None:
            return None
        x1 = sum(cn.get(o, 0) for o in event)
        x2 = sum(cd.get(o, 0) for o in event)
        if ref._certified(delta, x1, nn, x2, nd, ref.CONFIRM_ALPHA) > eps:
            return {"verdict": "violation", "dataset": neighbour, "neighbour": dataset,
                    "event": event, "confidence": 0.9}
        return None

    def scan(side, positions, step, expected):
        room = (hi_q - t) if side == "up" else (t - lo_q)
        for gap in range(step, room + 1, step):
            hit = probe(gap, side, positions, expected)
            if not hit:
                continue
            pos = hit[0]
            offset = gap
            for g in range(gap - step + 1, gap):
                s = probe(g, side, [pos], expected)
                if s:
                    offset = g
                    break
            return confirm(side, pos, offset) or "stop"
        return None

    plan = [("up", [0], ref.SCAN_STEP, ref.SCAN_EXPECTED), ("down", [0], ref.SCAN_STEP, ref.SCAN_EXPECTED),
            ("down", list(range(1, k)), ref.SCAN_STEP, LATER_EXPECTED)]
    plan += [("up", [j], LATER_STEP, LATER_EXPECTED) for j in range(1, k)]
    for side, positions, step, expected in plan:
        found = scan(side, positions, step, expected)
        if isinstance(found, dict):
            return found

    screened, pairs = {}, []
    for a, b in ref._library(k, t):
        for q in (a, b):
            if tuple(q) not in screened:
                counts, used = run(q, ref.SCREEN_RUNS)
                if counts is None:
                    break
                screened[tuple(q)] = (counts, used)
        if tuple(a) not in screened or tuple(b) not in screened:
            break
        for first, second in ((a, b), (b, a)):
            c1, n1 = screened[tuple(first)]
            c2, n2 = screened[tuple(second)]
            value, event = ref._plug_in_event(delta, c1, n1, c2, n2)
            if event:
                pairs.append((value, first, second, event))
    pairs.sort(key=lambda r: -r[0])
    if not pairs:
        return {"verdict": "no_violation", "confidence": 0.7}
    _value, first, second, event = pairs[0]
    per_side = (budget - spent[0]) // 2
    c1, n1 = run(first, per_side)
    c2, n2 = run(second, per_side)
    if c1 is not None and c2 is not None:
        x1 = sum(c1.get(o, 0) for o in event)
        x2 = sum(c2.get(o, 0) for o in event)
        if ref._certified(delta, x1, n1, x2, n2, ref.CONFIRM_ALPHA) > eps:
            return {"verdict": "violation", "dataset": list(first), "neighbour": list(second),
                    "event": event, "confidence": 0.8}
    return {"verdict": "no_violation", "confidence": 0.7}
