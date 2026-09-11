"""Standalone positional audit from the contributor's already fixed headroom method.

Only packaging is changed: public-input helpers are inlined from reference_library_scan.py;
no oracle, filesystem access, hidden world, importlib or sibling import is present.
Parameters and decisions are unchanged from PR80 4bb95061846a28a3025f4eb05cdd52210e12b11a.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import beta

SCREEN_RUNS = 8000
SCAN_STEP = 4
SCAN_EXPECTED = 8.0      # runs per scan point: enough for the specification to expect this many dissents
SCAN_MAX_RUNS = 6000     # a scan point that would need more is skipped
CONFIRM_ALPHA = 0.2       # a false claim and a missed one each cost one world
SUPPORT = 1500


def _dlap(b):
    x = np.arange(-SUPPORT, SUPPORT + 1)
    w = np.exp(-np.abs(x) / b)
    return x, w / w.sum()


def _dissent_probability(problem, gap, side):
    """Under the specification, P(first output F | first query gap above the threshold) for side
    up, P(first output T | first query gap below) for side down."""
    x, p_rho = _dlap(problem["threshold_noise_scale"])
    _, p_nu = _dlap(problem["query_noise_scale"])
    ge = np.concatenate([np.cumsum(p_nu[::-1])[::-1], [0.0]])      # P(nu >= x[j])

    def tail(t):
        return np.where(t < -SUPPORT, 1.0, ge[np.clip(t + SUPPORT, 0, 2 * SUPPORT + 1)])

    if side == "up":     # F when nu < rho - gap
        return float(np.sum(p_rho * (1.0 - tail(x - gap))))
    return float(np.sum(p_rho * tail(x + gap)))                    # T when nu >= rho + gap


def _library(k, t):
    A, B, h = t + 1, t - 1, k // 2
    return [
        ([A] + [B] * (k - 1), [A - 1] + [B + 1] * (k - 1)),
        ([B] + [A] * (k - 1), [B + 1] + [A - 1] * (k - 1)),
        ([A] * h + [B] * (k - h), [A - 1] * h + [B + 1] * (k - h)),
        ([B] * h + [A] * (k - h), [B + 1] * h + [A - 1] * (k - h)),
        ([A] * k, [A - 1] * k), ([B] * k, [B + 1] * k),
        ([t] * k, [t + 1] * k), ([t] * k, [t - 1] * k),
        ([t] * k, [t + 1 if i % 2 else t - 1 for i in range(k)]),
    ]


def _lower(x, n, alpha):
    return 0.0 if x <= 0 else float(beta.ppf(alpha, x, n - x + 1))


def _upper(x, n, alpha):
    return 1.0 if x >= n else float(beta.ppf(1.0 - alpha, x + 1, n - x))


def _certified(delta, x1, n1, x2, n2, alpha):
    lo, hi = _lower(x1, n1, alpha / 2.0), _upper(x2, n2, alpha / 2.0)
    if lo <= delta:
        return -math.inf
    return math.log((lo - delta) / hi)


def _plug_in_event(delta, c1, n1, c2, n2):
    """The ratio-sorted prefix of outputs that maximises the plug-in loss."""
    outputs = sorted(set(c1) | set(c2))
    p1 = np.array([c1.get(o, 0) / n1 for o in outputs])
    p2 = np.array([(c2.get(o, 0) + 0.5) / (n2 + 1.0) for o in outputs])
    order = np.argsort(-(p1 / p2), kind="stable")
    A, B = np.cumsum(p1[order]), np.cumsum(p2[order])
    best, event = -math.inf, []
    for j in range(len(order)):
        if A[j] > delta:
            v = math.log((A[j] - delta) / B[j])
            if v > best:
                best, event = v, [outputs[o] for o in order[: j + 1]]
    return best, event


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
        p = _dissent_probability(problem, gap, side)
        if side == "down" and len(positions) > 1:
            p = p * (1.0 - p) ** (len(positions) - 1)   # the last position is reached only past every earlier one
        n = math.ceil(expected / max(p, 1e-300))
        if n > SCAN_MAX_RUNS:
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
        return {"verdict": "violation", "dataset": neighbour, "neighbour": dataset,
                "event": event, "confidence": 0.9}
        p_next = _dissent_probability(problem, offset - 1, side)
        n_conf = min(20000, max(2000, math.ceil(60.0 / max(p_next, 1e-9))))
        cn, nn = run(neighbour, n_conf)
        cd, nd = run(dataset, n_conf)
        if cn is None or cd is None:
            return None
        x1 = sum(cn.get(o, 0) for o in event)
        x2 = sum(cd.get(o, 0) for o in event)
        if _certified(delta, x1, nn, x2, nd, CONFIRM_ALPHA) > eps:
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

    plan = [("up", [0], SCAN_STEP, SCAN_EXPECTED), ("down", [0], SCAN_STEP, SCAN_EXPECTED),
            ("down", list(range(1, k)), SCAN_STEP, LATER_EXPECTED)]
    plan += [("up", [j], LATER_STEP, LATER_EXPECTED) for j in range(1, k)]
    for side, positions, step, expected in plan:
        found = scan(side, positions, step, expected)
        if isinstance(found, dict):
            return found

    screened, pairs = {}, []
    for a, b in _library(k, t):
        for q in (a, b):
            if tuple(q) not in screened:
                counts, used = run(q, SCREEN_RUNS)
                if counts is None:
                    break
                screened[tuple(q)] = (counts, used)
        if tuple(a) not in screened or tuple(b) not in screened:
            break
        for first, second in ((a, b), (b, a)):
            c1, n1 = screened[tuple(first)]
            c2, n2 = screened[tuple(second)]
            value, event = _plug_in_event(delta, c1, n1, c2, n2)
            if event:
                pairs.append((value, first, second, event))
    pairs.sort(key=lambda r: -r[0])
    if not pairs:
        return {"verdict": "no_violation", "confidence": 0.7}
    _value, first, second, event = pairs[0]
    if _value > eps:
        return {"verdict": "violation", "dataset": list(first), "neighbour": list(second),
                "event": event, "confidence": 0.8}
    return {"verdict": "no_violation", "confidence": 0.7}
    per_side = (budget - spent[0]) // 2
    c1, n1 = run(first, per_side)
    c2, n2 = run(second, per_side)
    if c1 is not None and c2 is not None:
        x1 = sum(c1.get(o, 0) for o in event)
        x2 = sum(c2.get(o, 0) for o in event)
        if _certified(delta, x1, n1, x2, n2, CONFIRM_ALPHA) > eps:
            return {"verdict": "violation", "dataset": list(first), "neighbour": list(second),
                    "event": event, "confidence": 0.8}
    return {"verdict": "no_violation", "confidence": 0.7}
