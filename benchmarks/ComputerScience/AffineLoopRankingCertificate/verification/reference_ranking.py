"""Discrete lex search: uniform and adjacent pairwise slopes on each nested block.

The search is over public transitions only. A 1-ranking Farkas LP on the whole
system is not used. Pairwise directions can beat the uniform ablation when the
offset is peaked.
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


def _gaussian(matrix, rhs):
    work = [list(row) + [value] for row, value in zip(matrix, rhs)]
    n = len(rhs)
    for k in range(n):
        pivot = next((i for i in range(k, n) if work[i][k]), None)
        if pivot is None:
            return None
        work[k], work[pivot] = work[pivot], work[k]
        scale = work[k][k]
        work[k] = [value / scale for value in work[k]]
        for i in range(n):
            if i != k:
                scale = work[i][k]
                work[i] = [x - scale * y for x, y in zip(work[i], work[k])]
    return [row[-1] for row in work]


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
    # Adjacent 2-support: one pairwise guard.
    if len(support) == 2 and support[1] - support[0] in (1, n - 1) and r[support[0]] == r[support[1]]:
        need = r[support[0]]
        for index, item in enumerate(guards):
            slope = [_frac(entry) for entry in item["g"]]
            ones = [j for j, entry in enumerate(slope) if entry == 1]
            if _frac(item["d"]) == -2 and sorted(ones) == support and all(
                    entry in (0, 1) for entry in slope):
                lambdas[index] = need
                return lambdas
        # wrap-around support {0, n-1} stored unsorted
        want = set(support)
        for index, item in enumerate(guards):
            slope = [_frac(entry) for entry in item["g"]]
            ones = [j for j, entry in enumerate(slope) if entry == 1]
            if _frac(item["d"]) == -2 and set(ones) == want and all(
                    entry in (0, 1) for entry in slope):
                lambdas[index] = need
                return lambdas
        return None
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


def _rotated_lambdas(r, guards):
    n = len(r)
    support = [index for index, item in enumerate(r) if item]
    if not support:
        return _zeros(len(guards))
    rotated = []
    for index, item in enumerate(guards):
        slope = [_frac(entry) for entry in item["g"]]
        if _frac(item["d"]) != -3:
            continue
        if any(slope[j] != 0 and j not in range(support[0], support[-1] + 1)
               for j in range(n)):
            continue
        rotated.append((index, slope))
    width = len(support)
    if len(rotated) != width:
        return None
    offset = support[0]
    matrix = [[rotated[row][1][offset + col] for col in range(width)] for row in range(width)]
    # G^T λ = r, so columns are slopes; rows are coordinates.
    matrix = [[rotated[col][1][offset + row] for col in range(width)] for row in range(width)]
    rhs = [r[offset + row] for row in range(width)]
    local = _gaussian(matrix, rhs)
    if local is None or any(item < 0 for item in local):
        return None
    lambdas = _zeros(len(guards))
    for (index, _), value in zip(rotated, local):
        lambdas[index] = value
    return lambdas


def _multipliers(r, guards):
    pairwise = _pairwise_lambdas(r, guards)
    if pairwise is not None:
        return pairwise
    return _rotated_lambdas(r, guards)


def _honest_delta(ranking, transition):
    a = [[_frac(value) for value in row] for row in transition["A"]]
    b = [_frac(value) for value in transition["b"]]
    guards = transition["guards"]
    n = len(ranking)
    lam = _multipliers(ranking, guards)
    if lam is None:
        return None
    target = [ranking[k] - sum(a[i][k] * ranking[i] for i in range(n)) for k in range(n)]
    if all(item == 0 for item in target):
        mu = _zeros(len(guards))
        delta = -sum(ranking[i] * b[i] for i in range(n))
    else:
        mu = _multipliers(target, guards)
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


def _local_directions(width):
    directions = [[Fraction(1, width)] * width]
    for index in range(width):
        local = _zeros(width)
        local[index] = Fraction(1, 2)
        local[(index + 1) % width] = Fraction(1, 2)
        directions.append(local)
    return directions


def build_ranking(instance):
    depth, width = _levels(instance)
    transitions = instance["transitions"]
    decrease_index = list(range(depth - 1, -1, -1))
    chosen = []
    for level in range(depth):
        active_transition = next(
            t_index for t_index, active in enumerate(decrease_index) if active == level)
        best = None
        for local in _local_directions(width):
            ranking = _block_vector(depth, width, level, local)
            witness = _honest_delta(ranking, transitions[active_transition])
            if witness is None:
                continue
            if best is None or witness["delta"] > best["delta"]:
                best = dict(witness)
                best["r"] = ranking
        if best is None:
            raise ValueError("no feasible ranking on level %d" % level)
        chosen.append(best)
    components = []
    for item in chosen:
        components.append({
            "r": [_ratio(value) for value in item["r"]],
            "s": _ratio(item["s"]),
            "delta": _ratio(item["delta"]),
        })
    nonneg = []
    decrease = []
    for t_index, transition in enumerate(transitions):
        active = decrease_index[t_index]
        lam_row = []
        mu_row = []
        for level in range(depth):
            ranking = chosen[level]["r"]
            if level > active:
                lam_row.append([[0, 1]] * len(transition["guards"]))
                mu_row.append([[0, 1]] * len(transition["guards"]))
                continue
            witness = _honest_delta(ranking, transition)
            if witness is None:
                raise ValueError("prefix certificate failed on transition %d level %d"
                                 % (t_index, level))
            if level == active and witness["delta"] != chosen[level]["delta"]:
                # The active transition is the one the component was chosen on.
                pass
            need = chosen[level]["delta"] if level == active else Fraction(0)
            if level < active and witness["delta"] < 0:
                raise ValueError("prefix increased")
            # Recompute multipliers at the claimed need by reusing honest mu/lam.
            # For prefix, honest_delta used the maximum; Farkas for need=0 is weaker
            # and the same μ still witness a nonnegative decrease.
            lam_row.append([_ratio(value) for value in witness["lam"]])
            mu_row.append([_ratio(value) for value in witness["mu"]])
        nonneg.append(lam_row)
        decrease.append(mu_row)
    return {
        "components": components,
        "decrease_index": decrease_index,
        "nonneg_lambdas": nonneg,
        "decrease_lambdas": decrease,
    }
