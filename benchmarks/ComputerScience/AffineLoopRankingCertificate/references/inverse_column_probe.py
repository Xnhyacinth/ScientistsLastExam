"""Exact public-input counterexample for the previous identity-guard simplex family.

This is the 20-line column enumeration of (I-A^T)^{-1}. On the overcomplete
guard family it must not recover score one: multipliers are no longer λ=r
and μ=(I-A^T)r, and the feasible set is not that n-vertex simplex.
"""
from fractions import Fraction


def build_ranking(instance):
    n = instance["dimension"]
    a = [[Fraction(*value) for value in row] for row in instance["A"]]
    b = [Fraction(*value) for value in instance["b"]]
    m = [[Fraction(i == j) - a[j][i] for j in range(n)] for i in range(n)]
    inverse = [row[:] + [Fraction(i == j) for j in range(n)] for i, row in enumerate(m)]
    for k in range(n):
        pivot = next(i for i in range(k, n) if inverse[i][k])
        inverse[k], inverse[pivot] = inverse[pivot], inverse[k]
        scale = inverse[k][k]
        inverse[k] = [value / scale for value in inverse[k]]
        for i in range(n):
            if i != k:
                scale = inverse[i][k]
                inverse[i] = [x - scale * y for x, y in zip(inverse[i], inverse[k])]
    objective = [1 - sum(row) - shift for row, shift in zip(a, b)]
    rays = [[inverse[i][n + j] for i in range(n)] for j in range(n)]
    directions = [[value / sum(ray) for value in ray] for ray in rays]
    r = max(directions, key=lambda ray: sum(x * c for x, c in zip(ray, objective)))
    mu = [sum(m[i][j] * r[j] for j in range(n)) for i in range(n)]
    delta = sum(x * c for x, c in zip(r, objective))
    def ratio(value):
        return [value.numerator, value.denominator]
    return {"r": list(map(ratio, r)), "s": [0, 1], "delta": ratio(delta),
            "nonneg_lambdas": list(map(ratio, r)), "decrease_lambdas": list(map(ratio, mu))}
