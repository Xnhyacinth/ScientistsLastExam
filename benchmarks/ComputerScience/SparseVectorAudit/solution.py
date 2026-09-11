"""Weak but valid baseline for SparseVectorAudit.

The everyday audit: run the classic "one query above the threshold, every other query below"
pair two thousand times each, take the output whose count ratio is largest, and report it as a
violation. It never declines.

Three things are wrong with it. A ratio of counts is not a ratio of probabilities: the largest of
many noisy ratios is above the truth, so a correct implementation shows a violation somewhere. It
ignores delta, so an output that is rare enough can have any ratio without breaking the claim.
And it only ever tries one pair of inputs, so it finds nothing that pair does not happen to show.
"""
from __future__ import annotations

RUNS = 2000


def audit(problem, sample):
    k, t = int(problem["n_queries"]), int(problem["threshold"])
    dataset = [t + 1] + [t - 1] * (k - 1)
    neighbour = [t] * k
    a = sample(dataset, RUNS)
    b = sample(neighbour, RUNS)
    best, first, second, output = 0.0, dataset, neighbour, None
    for o in set(a) | set(b):
        for x, y, d1, d2 in ((a, b, dataset, neighbour), (b, a, neighbour, dataset)):
            ratio = (x.get(o, 0) + 1.0) / (y.get(o, 0) + 1.0)
            if ratio > best:
                best, first, second, output = ratio, d1, d2, o
    return {"verdict": "violation", "dataset": first, "neighbour": second,
            "event": [output], "confidence": 0.9}
