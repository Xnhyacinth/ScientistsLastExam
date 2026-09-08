"""Feasible pair-coordinate ascent using only the public affine transition.

This local rational heuristic can stall where a coupled direction is needed. It neither
reads the exact optimum nor solves the full Farkas LP.
"""
from fractions import Fraction


def build_ranking(instance):
    n = instance["dimension"]
    a = [[Fraction(*value) for value in row] for row in instance["A"]]
    b = [Fraction(*value) for value in instance["b"]]
    m = [[Fraction(i == j) - a[j][i] for j in range(n)] for i in range(n)]
    objective = [1 - sum(row) - shift for row, shift in zip(a, b)]
    r = [Fraction(1, n)] * n
    for _ in range(20):
        changed = False
        for donor in range(n):
            for receiver in range(n):
                if objective[receiver] <= objective[donor]:
                    continue
                mu = [sum(m[k][j] * r[j] for j in range(n)) for k in range(n)]
                direction = [m[k][receiver] - m[k][donor] for k in range(n)]
                step = min([r[donor]] + [mu[k] / -direction[k] for k in range(n) if direction[k] < 0])
                if step > 0:
                    r[donor] -= step
                    r[receiver] += step
                    changed = True
        if not changed:
            break
    mu = [sum(m[k][j] * r[j] for j in range(n)) for k in range(n)]
    delta = sum(x * c for x, c in zip(r, objective))
    ratio = lambda x: [x.numerator, x.denominator]
    return {"r": [ratio(x) for x in r], "s": [0, 1], "delta": ratio(delta),
            "nonneg_lambdas": [ratio(x) for x in r], "decrease_lambdas": [ratio(x) for x in mu]}
