"""1-ranking Farkas LP over a whole nested transition system.

Used only by tests. Feasibility here is the Colón–Sipma / Podelski–Rybalchenko
lattice this task leaves: a single linear ranking on every transition at once.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np
from scipy.optimize import linprog


def _gaussian(matrix, rhs):
    work = [list(row) + [value] for row, value in zip(matrix, rhs)]
    n = len(rhs)
    for k in range(n):
        pivot = next((i for i in range(k, n) if work[i][k]), None)
        if pivot is None:
            raise RuntimeError("singular exact recovery")
        work[k], work[pivot] = work[pivot], work[k]
        scale = work[k][k]
        work[k] = [value / scale for value in work[k]]
        for i in range(n):
            if i != k:
                scale = work[i][k]
                work[i] = [x - scale * y for x, y in zip(work[i], work[k])]
    return [row[-1] for row in work]


def exact_maximum_delta(transitions):
    """Maximum delta of a single (r,s) that ranks every transition, or None."""
    n = len(transitions[0][2])
    m_list = [len(guards) for guards, _, _ in ((t[1], t[2], t[3]) for t in transitions)]
    # transitions: (name, guards, A, b)
    n_rp, n_rn = 0, n
    n_sp, n_sn = 2 * n, 2 * n + 1
    n_delta = 2 * n + 2
    cursor = 2 * n + 3
    lam_off = []
    mu_off = []
    slack_nn = []
    slack_dec = []
    for m in m_list:
        lam_off.append(cursor)
        cursor += m
        mu_off.append(cursor)
        cursor += m
        slack_nn.append(cursor)
        cursor += 1
        slack_dec.append(cursor)
        cursor += 1
    nvars = cursor

    def zeros():
        return [Fraction(0)] * nvars

    eqs = []
    row = zeros()
    for i in range(n):
        row[n_rp + i] = Fraction(1)
        row[n_rn + i] = Fraction(1)
    eqs.append((row, Fraction(1)))
    for t_index, (_, guards, update_a, update_b) in enumerate(transitions):
        m = len(guards)
        g_rows = [slope for slope, _ in guards]
        d_vec = [intercept for _, intercept in guards]
        i_minus_at = [[Fraction(i == j) - update_a[j][i] for j in range(n)] for i in range(n)]
        for k in range(n):
            row = zeros()
            for j in range(m):
                row[lam_off[t_index] + j] = g_rows[j][k]
            row[n_rp + k] = Fraction(-1)
            row[n_rn + k] = Fraction(1)
            eqs.append((row, Fraction(0)))
        for k in range(n):
            row = zeros()
            for j in range(m):
                row[mu_off[t_index] + j] = g_rows[j][k]
            for i in range(n):
                row[n_rp + i] -= i_minus_at[k][i]
                row[n_rn + i] += i_minus_at[k][i]
            eqs.append((row, Fraction(0)))
        row = zeros()
        row[n_sp] = Fraction(1)
        row[n_sn] = Fraction(-1)
        for j in range(m):
            row[lam_off[t_index] + j] = -d_vec[j]
        row[slack_nn[t_index]] = Fraction(-1)
        eqs.append((row, Fraction(0)))
        row = zeros()
        for i in range(n):
            row[n_rp + i] = -update_b[i]
            row[n_rn + i] = update_b[i]
        row[n_delta] = Fraction(-1)
        for j in range(m):
            row[mu_off[t_index] + j] = -d_vec[j]
        row[slack_dec[t_index]] = Fraction(-1)
        eqs.append((row, Fraction(0)))

    A = [eq[0] for eq in eqs]
    rhs = [eq[1] for eq in eqs]
    c = [0.0] * nvars
    c[n_delta] = 1.0
    af = np.array([[float(x) for x in row] for row in A], dtype=float)
    bf = np.array([float(x) for x in rhs], dtype=float)
    result = linprog(-np.array(c), A_eq=af, b_eq=bf, bounds=[(0, None)] * nvars,
                     method="highs")
    if not result.success:
        return None
    basic = []
    for idx in np.argsort(-np.abs(result.x)):
        trial = basic + [int(idx)]
        mat = np.array([[float(A[i][j]) for j in trial] for i in range(len(A))], dtype=float)
        if np.linalg.matrix_rank(mat, tol=1e-8) == len(trial):
            basic.append(int(idx))
            if len(basic) == len(A):
                break
    if len(basic) != len(A):
        return {
            "r": [Fraction(0)] * n,
            "s": Fraction(0),
            "delta": Fraction(0),
            "feasible": False,
            "float_delta": float(result.x[n_delta]),
        }
    try:
        x_basic = _gaussian([[A[i][j] for j in basic] for i in range(len(A))], rhs)
    except RuntimeError:
        return None
    x = [Fraction(0)] * nvars
    for idx, value in zip(basic, x_basic):
        if value < 0:
            if value > Fraction(-1, 10 ** 9):
                value = Fraction(0)
            else:
                return None
        x[idx] = value
    r = [x[n_rp + i] - x[n_rn + i] for i in range(n)]
    return {
        "r": r,
        "s": x[n_sp] - x[n_sn],
        "delta": x[n_delta],
        "feasible": x[n_delta] > 0,
        "nonneg_lambdas": [x[lam_off[t]:lam_off[t] + m_list[t]] for t in range(len(transitions))],
        "decrease_lambdas": [x[mu_off[t]:mu_off[t] + m_list[t]] for t in range(len(transitions))],
    }


def _frac(value):
    return Fraction(*value) if isinstance(value, (list, tuple)) else Fraction(value)


def _ratio(value):
    return [int(value.numerator), int(value.denominator)]


def _zeros(n):
    return [Fraction(0)] * n


def _levels(instance):
    depth = len(instance["transitions"])
    width = instance["dimension"] // depth
    return depth, width


def _block_loop(transition, level, width):
    off = level * width
    n = len(transition["b"])
    guards = []
    indices = []
    for index, item in enumerate(transition["guards"]):
        slope = [_frac(x) for x in item["g"]]
        if any(slope[j] != 0 and not (off <= j < off + width) for j in range(n)):
            continue
        if all(x == 0 for x in slope[off:off + width]):
            continue
        guards.append((slope[off:off + width], _frac(item["d"])))
        indices.append(index)
    a = [[_frac(transition["A"][off + i][off + j]) for j in range(width)] for i in range(width)]
    b = [_frac(transition["b"][off + i]) for i in range(width)]
    return guards, indices, a, b, off


def _match_guard(full_guards, block_slope, intercept, off, width, n):
    for index, item in enumerate(full_guards):
        slope = [_frac(x) for x in item["g"]]
        if _frac(item["d"]) != intercept:
            continue
        if slope[off:off + width] != list(block_slope):
            continue
        if any(slope[j] != 0 and not (off <= j < off + width) for j in range(n)):
            continue
        return index
    raise RuntimeError("block guard missing from transition")


def _embed(block_lambdas, block_guards, full_guards, off, width, n):
    out = _zeros(len(full_guards))
    for lam, (slope, intercept) in zip(block_lambdas, block_guards):
        out[_match_guard(full_guards, slope, intercept, off, width, n)] = lam
    return out


def phase_lex_ranking(instance):
    """Verified nested lex tuple: independent exact phase rankings, not a 1-ranking."""
    depth, width = _levels(instance)
    n = instance["dimension"]
    decrease_index = list(range(depth - 1, -1, -1))
    phases = []
    for level in range(depth):
        t_index = next(i for i, active in enumerate(decrease_index) if active == level)
        trans = instance["transitions"][t_index]
        guards, _, a, b, off = _block_loop(trans, level, width)
        witness = exact_maximum_delta([("block", guards, a, b)])
        if witness is None or not witness.get("feasible"):
            raise RuntimeError("phase LP infeasible at level %d" % level)
        local = witness["r"]
        nrm = sum(abs(x) for x in local)
        if nrm == 0:
            raise RuntimeError("zero phase ranking")
        scale = 1 / nrm
        local = [x * scale for x in local]
        ranking = _zeros(n)
        for i, value in enumerate(local):
            ranking[off + i] = value
        phases.append({
            "r": ranking,
            "s": witness["s"] * scale,
            "delta": witness["delta"] * scale,
            "block_guards": guards,
            "lam": [x * scale for x in witness["nonneg_lambdas"][0]],
            "mu": [x * scale for x in witness["decrease_lambdas"][0]],
            "off": off,
        })
    components = [{
        "r": [_ratio(x) for x in item["r"]],
        "s": _ratio(item["s"] if item["s"] >= 0 else Fraction(0)),
        "delta": _ratio(item["delta"]),
    } for item in phases]
    nonneg = []
    decrease = []
    for t_index, trans in enumerate(instance["transitions"]):
        active = decrease_index[t_index]
        lam_row = []
        mu_row = []
        for level in range(depth):
            n_guards = len(trans["guards"])
            if level > active:
                lam_row.append([[0, 1]] * n_guards)
                mu_row.append([[0, 1]] * n_guards)
                continue
            phase = phases[level]
            lam = _embed(phase["lam"], phase["block_guards"], trans["guards"],
                         phase["off"], width, n)
            if level == active:
                mu = _embed(phase["mu"], phase["block_guards"], trans["guards"],
                            phase["off"], width, n)
            else:
                mu = _zeros(n_guards)
            lam_row.append([_ratio(x) for x in lam])
            mu_row.append([_ratio(x) for x in mu])
        nonneg.append(lam_row)
        decrease.append(mu_row)
    return {
        "components": components,
        "decrease_index": decrease_index,
        "nonneg_lambdas": nonneg,
        "decrease_lambdas": decrease,
    }


def one_ranking_as_lex(instance, evaluator):
    """Wrap the whole-system 1-ranking LP as a depth-1 lex tuple, or fail closed."""
    dimension = int(instance["dimension"])
    transitions = evaluator._parse_transitions(instance["transitions"], dimension)
    witness = exact_maximum_delta(transitions)
    if witness is None or not witness.get("feasible") or witness["delta"] <= 0:
        return {"components": []}
    n_trans = len(instance["transitions"])
    return {
        "components": [{
            "r": [_ratio(x) for x in witness["r"]],
            "s": _ratio(witness["s"]),
            "delta": _ratio(witness["delta"]),
        }],
        "decrease_index": [0] * n_trans,
        "nonneg_lambdas": [
            [[_ratio(x) for x in witness["nonneg_lambdas"][t]]]
            for t in range(n_trans)
        ],
        "decrease_lambdas": [
            [[_ratio(x) for x in witness["decrease_lambdas"][t]]]
            for t in range(n_trans)
        ],
    }
