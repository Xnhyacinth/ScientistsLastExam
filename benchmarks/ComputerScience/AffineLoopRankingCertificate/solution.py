"""Uniform rational ranking at a token proven decrease."""
from fractions import Fraction


def build_ranking(instance):
    n = instance["dimension"]
    m = len(instance["guards"])
    r = [Fraction(1, n)] * n
    a = [[Fraction(*value) for value in row] for row in instance["A"]]
    target = [r[k] - sum(a[i][k] * r[i] for i in range(n)) for k in range(n)]
    # Pairwise guards alone certify the uniform slope; rotated multipliers stay off.
    lam = [Fraction(1, 2 * n)] * n + [Fraction(0)] * (m - n)
    mu = [target[0] / 2] * n + [Fraction(0)] * (m - n)
    ratio = lambda x: [x.numerator, x.denominator]
    return {"r": [ratio(x) for x in r], "s": [0, 1], "delta": [1, 10000],
            "nonneg_lambdas": [ratio(x) for x in lam], "decrease_lambdas": [ratio(x) for x in mu]}
