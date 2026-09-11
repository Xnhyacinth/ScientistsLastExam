"""1-ranking inverse-column probe on the first transition.

The previous identity-guard simplex closed form. On nested-reset loops a single
linear ranking is incomplete, so this depth-1 attempt must not reach score one.
"""
from fractions import Fraction


def build_ranking(instance):
    n = instance["dimension"]
    first = instance["transitions"][0]
    a = [[Fraction(*value) for value in row] for row in first["A"]]
    b = [Fraction(*value) for value in first["b"]]
    m = [[Fraction(i == j) - a[j][i] for j in range(n)] for i in range(n)]
    inverse = [row[:] + [Fraction(i == j) for j in range(n)] for i, row in enumerate(m)]
    try:
        for k in range(n):
            pivot = next(i for i in range(k, n) if inverse[i][k])
            inverse[k], inverse[pivot] = inverse[pivot], inverse[k]
            scale = inverse[k][k]
            inverse[k] = [value / scale for value in inverse[k]]
            for i in range(n):
                if i != k:
                    scale = inverse[i][k]
                    inverse[i] = [x - scale * y for x, y in zip(inverse[i], inverse[k])]
    except StopIteration:
        return {"components": []}
    rays = [[inverse[i][n + j] for i in range(n)] for j in range(n)]
    directions = []
    for ray in rays:
        total = sum(abs(value) for value in ray)
        if total == 0:
            continue
        directions.append([value / total for value in ray])
    if not directions:
        return {"components": []}
    r = directions[0]
    n_trans = len(instance["transitions"])
    n_guards = [len(t["guards"]) for t in instance["transitions"]]
    def ratio(value):
        return [value.numerator, value.denominator]
    zeros = lambda m: [[0, 1]] * m
    return {
        "components": [{
            "r": list(map(ratio, r)),
            "s": [0, 1],
            "delta": [1, 10000],
        }],
        "decrease_index": [0] * n_trans,
        "nonneg_lambdas": [[zeros(m)] for m in n_guards],
        "decrease_lambdas": [[zeros(m)] for m in n_guards],
    }
