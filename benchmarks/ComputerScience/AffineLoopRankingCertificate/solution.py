"""Token-delta nested ranking: one uniform component per level, proven decrease 1/10000."""
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


def _block_ranking(depth, width, level):
    ranking = _zeros(depth * width)
    for index in range(width):
        ranking[level * width + index] = Fraction(1, width)
    return ranking


def _pairwise_uniform(r, guards):
    n = len(r)
    lambdas = _zeros(len(guards))
    support = [index for index, item in enumerate(r) if item]
    if not support:
        return lambdas
    value = r[support[0]]
    if any(r[index] not in (0, value) for index in range(n)):
        return None
    if any(r[index] != value for index in support):
        return None
    width = len(support)
    if support != list(range(support[0], support[0] + width)):
        return None
    need = value / 2
    for index, item in enumerate(guards):
        slope = [_frac(entry) for entry in item["g"]]
        intercept = _frac(item["d"])
        ones = [j for j, entry in enumerate(slope) if entry == 1]
        zeros = sum(1 for entry in slope if entry == 0)
        if intercept == -2 and len(ones) == 2 and zeros == n - 2 and all(j in support for j in ones):
            lambdas[index] = need
    if all(x == 0 for x in lambdas):
        return None
    return lambdas


def _certificate_component(ranking, transition, delta):
    a = [[_frac(value) for value in row] for row in transition["A"]]
    b = [_frac(value) for value in transition["b"]]
    guards = transition["guards"]
    n = len(ranking)
    lam = _pairwise_uniform(ranking, guards)
    if lam is None:
        raise ValueError("uniform pairwise multipliers failed")
    target = [ranking[k] - sum(a[i][k] * ranking[i] for i in range(n)) for k in range(n)]
    if all(item == 0 for item in target):
        mu = _zeros(len(guards))
    else:
        mu = _pairwise_uniform(target, guards)
        if mu is None:
            raise ValueError("uniform decrease multipliers failed")
    s = sum(_frac(item["d"]) * lam[j] for j, item in enumerate(guards))
    if s < 0:
        s = Fraction(0)
    return lam, mu, s, delta


def build_ranking(instance):
    depth, width = _levels(instance)
    components = []
    for level in range(depth):
        ranking = _block_ranking(depth, width, level)
        # Token decrease; Farkas is checked at this delta, not at the honest maximum.
        components.append({
            "r": [_ratio(value) for value in ranking],
            "s": [0, 1],
            "delta": [1, 10000],
        })
    decrease_index = list(range(depth - 1, -1, -1))
    nonneg = []
    decrease = []
    for t_index, transition in enumerate(instance["transitions"]):
        active = decrease_index[t_index]
        lam_row = []
        mu_row = []
        for level in range(depth):
            ranking = _block_ranking(depth, width, level)
            if level > active:
                lam_row.append([[0, 1]] * len(transition["guards"]))
                mu_row.append([[0, 1]] * len(transition["guards"]))
                continue
            delta = Fraction(1, 10000) if level == active else Fraction(0)
            lam, mu, _, _ = _certificate_component(ranking, transition, delta)
            lam_row.append([_ratio(value) for value in lam])
            mu_row.append([_ratio(value) for value in mu])
        nonneg.append(lam_row)
        decrease.append(mu_row)
    return {
        "components": components,
        "decrease_index": decrease_index,
        "nonneg_lambdas": nonneg,
        "decrease_lambdas": decrease,
    }
