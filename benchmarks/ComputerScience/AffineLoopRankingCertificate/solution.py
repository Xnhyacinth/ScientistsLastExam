"""Uniform rational ranking at a token proven decrease."""
from fractions import Fraction


def build_ranking(instance):
    n = instance["dimension"]
    r = [Fraction(1, n)] * n
    a = [[Fraction(*value) for value in row] for row in instance["A"]]
    mu = [r[j] - sum(a[i][j] * r[i] for i in range(n)) for j in range(n)]
    ratio = lambda x: [x.numerator, x.denominator]
    return {"r": [ratio(x) for x in r], "s": [0, 1], "delta": [1, 10000],
            "nonneg_lambdas": [ratio(x) for x in r], "decrease_lambdas": [ratio(x) for x in mu]}
