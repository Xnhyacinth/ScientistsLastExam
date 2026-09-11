"""Group-average then 1-D cyclic line: the checkpoint-12 symmetry probe.

C3 averaging sends any 3-by-3 Gram to aI + b(J - I). After homogeneity that is
the one-parameter family P = I + c(J - I), i.e. p11=p22=p33=1 and
p12=p13=p23=c. Fourteen rational values of c with exact bisection of alpha.
Reads public modes only.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verification"))
from reference_lyapunov import _holds, _matrix, _pack, _spd, _trace, _upper  # noqa: E402

# Owner's 14-point cyclic scan: c = k/10 for k = -4, ..., 9.
C_VALS = tuple(Fraction(k, 10) for k in range(-4, 10))
CYCLE = ((0, 1, 2), (1, 2, 0), (2, 0, 1))


def _c3_average(gram):
    acc = [[Fraction(0), Fraction(0), Fraction(0)] for _ in range(3)]
    for perm in CYCLE:
        for i in range(3):
            for j in range(3):
                acc[i][j] += gram[perm[i]][perm[j]]
    return [[value / 3 for value in row] for row in acc]


def _cyclic_line(coupling):
    return _upper(coupling, coupling, 1, coupling, 1)


def build_lyapunov(instance):
    modes = [_matrix(mode) for mode in instance["mode_matrices"]]
    upper = min(-_trace(mode) for mode in modes)
    denominator = min(1000, int(instance.get("max_denominator", 1000)))
    # Group-average the identity (already cyclic) and a plane shear, then search
    # the remaining scalar. Both averages lie on P = I + c(J - I).
    seeds = (
        _upper(0, 0, 1, 0, 1),
        _upper(Fraction(1, 3), 0, 1, 0, 1),
    )
    averaged = [_c3_average(seed) for seed in seeds]
    best = None
    for coupling in C_VALS:
        gram = _cyclic_line(coupling)
        if not _spd(gram) or not _holds(modes, gram, Fraction(0)):
            continue
        low, high = 0, int(upper * denominator) + 1
        while high - low > 1:
            middle = (low + high) // 2
            if _holds(modes, gram, Fraction(middle, denominator)):
                low = middle
            else:
                high = middle
        alpha = Fraction(low, denominator)
        if alpha > 0 and (best is None or alpha > best[1]):
            best = (gram, alpha)
    if best is None:
        gram = averaged[0]
        alpha = Fraction(1, 10000)
    else:
        gram, alpha = best
    return _pack(gram, alpha)
