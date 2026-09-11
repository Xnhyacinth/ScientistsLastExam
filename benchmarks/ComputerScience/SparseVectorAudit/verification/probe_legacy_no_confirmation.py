"""Truth-blind reference for SparseVectorAudit.

It audits in three stages and never reads anything but the public problem and the counts that
`sample` returns.

    scan      the specification says how often the first query should dissent from the side of
              the threshold it sits on: a query g above the threshold should still come out F
              with a probability the specification fixes. For g on a grid of four, on both sides,
              it runs enough copies of a vector with that first query and every other query at
              the bottom of the range for the specification to expect eight dissents. A grid
              point with none is a branch that skips the noise; the offset is then pinned by
              walking the three values below it, and the straddling pair is confirmed.
    library   the StatDP-style pairs, every answer one step either side of the threshold, are
              screened with 8000 runs of each vector; for each pair the event is the prefix of
              outputs, sorted by their empirical ratio, that maximises the plug-in loss.
    confirm   the best screened pair is rerun on fresh samples with everything left of the
              budget, and a claim is made only if the Clopper-Pearson bounds at level 0.2,
              split over the two sides, certify a loss above epsilon with delta subtracted.

What it does not do, on purpose: it scans only the first query, so a branch that exists only at
later positions is never reached, and it confirms the event it chose on the screening counts
rather than searching for the event with the best certified bound. Those are the places it
leaves room.
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

    # --- scan the first query for a branch that skips the noise --------------------------------
    def dissent_count(counts, side):
        want = "F" if side == "up" else "T"
        return sum(v for o, v in counts.items() if o[:1] == want)

    def probe(gap, side):
        p = _dissent_probability(problem, gap, side)
        n = math.ceil(SCAN_EXPECTED / max(p, 1e-300))
        if n > SCAN_MAX_RUNS:
            return None
        q = [lo_q] * k
        q[0] = t + gap if side == "up" else t - gap
        counts, used = run(q, n)
        if counts is None:
            return None
        return dissent_count(counts, side)

    for side in ("up", "down"):
        room = (hi_q - t) if side == "up" else (t - lo_q)
        for gap in range(SCAN_STEP, room + 1, SCAN_STEP):
            seen = probe(gap, side)
            if seen is None or seen > 0:
                continue
            offset = gap
            for g in range(gap - SCAN_STEP + 1, gap):
                s = probe(g, side)
                if s == 0:
                    offset = g
                    break
            dataset = [lo_q] * k
            neighbour = [lo_q] * k
            if side == "up":
                dataset[0], neighbour[0] = t + offset, t + offset - 1
                event = [o for o in patterns if o[:1] == "F"]
            else:
                dataset[0], neighbour[0] = t - offset, t - offset + 1
                event = [o for o in patterns if o[:1] == "T"]
            p_next = _dissent_probability(problem, offset - 1, side)
            n_conf = min(20000, max(2000, math.ceil(60.0 / max(p_next, 1e-9))))
            cn, nn = run(neighbour, n_conf)
            cd, nd = run(dataset, n_conf)
            if cn is None or cd is None:
                break
            x1 = sum(cn.get(o, 0) for o in event)
            x2 = sum(cd.get(o, 0) for o in event)
            if _certified(delta, x1, nn, x2, nd, CONFIRM_ALPHA) > eps:
                return {"verdict": "violation", "dataset": neighbour, "neighbour": dataset,
                        "event": event, "confidence": 0.9}
            break

    # --- screen the library -----------------------------------------------------------------------
    screened = {}
    pairs = []
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

    if pairs[0][0] > eps:
        _v, first, second, event = pairs[0]
        return {"verdict": "violation", "dataset": list(first), "neighbour": list(second),
                "event": event, "confidence": 0.8}
    return {"verdict": "no_violation", "confidence": 0.7}
    # --- confirm on fresh samples -------------------------------------------------------------------
    _value, first, second, event = pairs[0]
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
