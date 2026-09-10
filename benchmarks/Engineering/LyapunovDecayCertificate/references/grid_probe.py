"""Two-parameter block-diagonal Gram scan used as a checkpoint-12 probe.

P = [[1, b, 0], [b, d, 0], [0, 0, 1]] with exact rational bisection of alpha.
This is the 3-by-3 analogue of the 2-by-2 (b, d) grid that beat the previous
reference. It reads public modes only.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verification"))
from reference_lyapunov import _holds, _matrix, _pack, _trace, _upper  # noqa: E402

B_VALS = tuple(Fraction(k, 10) for k in range(-12, 13))
D_VALS = tuple(Fraction(k, 10) for k in range(2, 31))


def build_lyapunov(instance):
    modes = [_matrix(mode) for mode in instance["mode_matrices"]]
    upper = min(-_trace(mode) for mode in modes)
    denominator = min(50, int(instance.get("max_denominator", 50)))
    best = None
    for b in B_VALS:
        for d in D_VALS:
            gram = _upper(b, 0, d, 0, 1)
            if not _holds(modes, gram, Fraction(0)):
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
        gram = _upper(0, 0, 1, 0, 1)
        alpha = Fraction(1, 10000)
    else:
        gram, alpha = best
    return _pack(gram, alpha)
