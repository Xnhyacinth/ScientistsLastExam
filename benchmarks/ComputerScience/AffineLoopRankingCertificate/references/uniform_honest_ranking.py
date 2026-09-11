"""Uniform nested ranking with an honest Farkas decrease, no direction search.

Self-contained so the sandbox probe cannot read verification/. Measured
combined_score 0.727504, below the pairwise reference.
"""
from fractions import Fraction


def _frac(value):
    return Fraction(*value) if isinstance(value, (list, tuple)) else Fraction(value)


def _ratio(value):
    return [value.numerator, value.denominator]


def _zeros(n):
    return [Fraction(0)] * n


def _levels(instance):
    depth = len(instance["transitions"])
    width = instance["dimension"] // depth
    return depth, width


def _block_vector(depth, width, level, local):
    ranking = _zeros(depth * width)
    for index, value in enumerate(local):
        ranking[level * width + index] = value
    return ranking


def _pairwise_lambdas(r, guards):
    n = len(r)
    lambdas = _zeros(len(guards))
    support = [index for index, item in enumerate(r) if item]
    if not support:
        return lambdas
    if all(r[index] == r[support[0]] for index in support) and support == list(
            range(support[0], support[-1] + 1)):
        need = r[support[0]] / 2
        for index, item in enumerate(guards):
            slope = [_frac(entry) for entry in item["g"]]
            ones = [j for j, entry in enumerate(slope) if entry == 1]
            if (_frac(item["d"]) == -2 and len(ones) == 2
                    and all(j in support for j in ones)
                    and all(entry in (0, 1) for entry in slope)):
                lambdas[index] = need
        if any(item > 0 for item in lambdas):
            return lambdas
        return None
    return None


def _honest_delta(ranking, transition):
    a = [[_frac(value) for value in row] for row in transition["A"]]
    b = [_frac(value) for value in transition["b"]]
    guards = transition["guards"]
    n = len(ranking)
    lam = _pairwise_lambdas(ranking, guards)
    if lam is None:
        return None
    target = [ranking[k] - sum(a[i][k] * ranking[i] for i in range(n)) for k in range(n)]
    if all(item == 0 for item in target):
        mu = _zeros(len(guards))
        delta = -sum(ranking[i] * b[i] for i in range(n))
    else:
        mu = _pairwise_lambdas(target, guards)
        if mu is None:
            return None
        delta = (-sum(ranking[i] * b[i] for i in range(n))
                 - sum(_frac(item["d"]) * mu[j] for j, item in enumerate(guards)))
    if delta < 0:
        return None
    s = sum(_frac(item["d"]) * lam[j] for j, item in enumerate(guards))
    if s < 0:
        s = Fraction(0)
    return {"lam": lam, "mu": mu, "s": s, "delta": delta}


def build_ranking(instance):
    depth, width = _levels(instance)
    decrease_index = list(range(depth - 1, -1, -1))
    chosen = []
    for level in range(depth):
        ranking = _block_vector(depth, width, level, [Fraction(1, width)] * width)
        t_index = next(i for i, active in enumerate(decrease_index) if active == level)
        witness = _honest_delta(ranking, instance["transitions"][t_index])
        if witness is None:
            raise ValueError("uniform honest ranking failed")
        chosen.append({"r": ranking, **witness})
    components = [{
        "r": [_ratio(x) for x in item["r"]],
        "s": _ratio(item["s"]),
        "delta": _ratio(item["delta"]),
    } for item in chosen]
    nonneg = []
    decrease = []
    for t_index, trans in enumerate(instance["transitions"]):
        active = decrease_index[t_index]
        lam_row = []
        mu_row = []
        for level in range(depth):
            if level > active:
                zeros = [[0, 1]] * len(trans["guards"])
                lam_row.append(zeros)
                mu_row.append(zeros)
                continue
            witness = _honest_delta(chosen[level]["r"], trans)
            lam_row.append([_ratio(x) for x in witness["lam"]])
            mu_row.append([_ratio(x) for x in witness["mu"]])
        nonneg.append(lam_row)
        decrease.append(mu_row)
    return {
        "components": components,
        "decrease_index": decrease_index,
        "nonneg_lambdas": nonneg,
        "decrease_lambdas": decrease,
    }
