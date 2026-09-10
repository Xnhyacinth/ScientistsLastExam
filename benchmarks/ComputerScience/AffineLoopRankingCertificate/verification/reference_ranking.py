"""Feasible discrete search over uniform and pairwise ranking slopes.

Uses only the public guards and affine update. It never solves the full Farkas LP
over mixed-support rankings, so coupled directions beyond these local moves remain.
"""
from fractions import Fraction


def _gaussian(matrix, rhs):
    work = [list(row) + [value] for row, value in zip(matrix, rhs)]
    n = len(rhs)
    for k in range(n):
        pivot = next(i for i in range(k, n) if work[i][k])
        work[k], work[pivot] = work[pivot], work[k]
        scale = work[k][k]
        work[k] = [value / scale for value in work[k]]
        for i in range(n):
            if i != k:
                scale = work[i][k]
                work[i] = [x - scale * y for x, y in zip(work[i], work[k])]
    return [row[-1] for row in work]


def _rotated_multipliers(target):
    n = len(target)
    matrix = [[Fraction(0)] * n for _ in range(n)]
    for k in range(n):
        matrix[k][k] = Fraction(2)
        matrix[k][(k - 3) % n] = Fraction(1)
    return _gaussian(matrix, target)


def _parse(instance):
    n = instance["dimension"]
    a = [[Fraction(*value) for value in row] for row in instance["A"]]
    b = [Fraction(*value) for value in instance["b"]]
    intercepts = []
    for item in instance["guards"]:
        intercept = item["d"]
        intercepts.append(Fraction(*intercept) if isinstance(intercept, (list, tuple))
                          else Fraction(intercept))
    return n, len(instance["guards"]), a, b, intercepts


def _certificate(r, a, b, n, m, intercepts):
    target = [r[k] - sum(a[i][k] * r[i] for i in range(n)) for k in range(n)]
    lam = [Fraction(0)] * m
    mu = [Fraction(0)] * m
    if all(x == r[0] for x in r) and r[0] > 0:
        lam = [r[0] / 2] * n + [Fraction(0)] * (m - n)
        if all(x == target[0] for x in target):
            mu = [target[0] / 2] * n + [Fraction(0)] * (m - n)
        else:
            rotated = _rotated_multipliers(target)
            if any(x < 0 for x in rotated):
                return None
            mu = [Fraction(0)] * n + rotated
    else:
        pair = next((i for i in range(n)
                     if r[i] > 0 and r[(i + 1) % n] == r[i]
                     and all(r[j] == 0 for j in range(n) if j not in (i, (i + 1) % n))), None)
        if pair is None:
            return None
        lam[pair] = r[pair]
        rotated = _rotated_multipliers(target)
        if any(x < 0 for x in rotated):
            return None
        mu = [Fraction(0)] * n + rotated
    if any(x < 0 for x in lam + mu):
        return None
    delta = -sum(r[i] * b[i] for i in range(n)) - sum(intercepts[j] * mu[j] for j in range(m))
    if delta <= 0:
        return None
    s = sum(intercepts[j] * lam[j] for j in range(m))
    if s < 0:
        s = Fraction(0)
    ratio = lambda x: [x.numerator, x.denominator]
    return {"r": [ratio(x) for x in r], "s": ratio(s), "delta": ratio(delta),
            "nonneg_lambdas": [ratio(x) for x in lam],
            "decrease_lambdas": [ratio(x) for x in mu],
            "_delta": delta}


def build_ranking(instance):
    n, m, a, b, intercepts = _parse(instance)
    directions = [[Fraction(1, n)] * n]
    for index in range(n):
        ranking = [Fraction(0)] * n
        ranking[index] = Fraction(1, 2)
        ranking[(index + 1) % n] = Fraction(1, 2)
        directions.append(ranking)
    best = None
    for ranking in directions:
        witness = _certificate(ranking, a, b, n, m, intercepts)
        if witness is None:
            continue
        if best is None or witness["_delta"] > best["_delta"]:
            best = witness
    if best is None:
        raise ValueError("no feasible pairwise ranking")
    best.pop("_delta")
    return best
