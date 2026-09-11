"""Construction statistics of every graded world, on the evaluator's exact engine.

For each world: its kind, size and noise scales; for compliant worlds the best loss an exact
local search finds (a sanity bound under the compliance proof); for compliant-branch worlds the
coupling bound on delta and the mass of the straddling event; for noise-scale worlds the anchor's
loss, the mass of its event on each side, and how many runs per side a Clopper-Pearson
certificate of the anchor itself would need at the reference's level; for branch worlds the
offset, side, positions and the straddling event's mass.

    .venv/bin/python .research/sparse_vector_audit/worlds.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta

sys.path.insert(0, str(Path(__file__).parent))
import anchors as an  # noqa: E402

ev = an.ev


def certified(p1, p2, n, alpha):
    x1, x2 = p1 * n, p2 * n
    lo = beta.ppf(alpha / 2, x1, n - x1 + 1)
    hi = beta.ppf(1 - alpha / 2, x2 + 1, n - x2)
    return math.log((lo - ev.DELTA) / hi) if lo > ev.DELTA else -math.inf


def runs_needed(p1, p2, alpha):
    for n in [1000 * i for i in range(1, 401)]:
        if certified(p1, p2, n, alpha) > ev.EPSILON:
            return n
    return None


rng = np.random.default_rng(20260911)
for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
    mech = ev._Mechanism(spec)
    row = {"name": spec["name"], "kind": spec["kind"], "k": mech.k, "c": mech.c,
           "b_rho": round(mech.b_rho, 3), "b_nu": round(mech.b_nu, 3)}
    if mech.branch is not None:
        offset, side, positions = mech.branch
        row.update({"offset": offset, "side": side, "positions": positions})
    if spec["kind"] in ("compliant", "compliant_branch"):
        loss, _w = an.local_search(mech, rng, 24, 200)
        row["search_max_loss"] = round(loss, 4)
    if spec["kind"] == "compliant_branch":
        offset, side, positions = mech.branch
        flip = an.p_correct_flip(mech, offset, side)
        eta = flip if (side == "up" and mech.c == 1) else flip * len(positions)
        w = an.straddle(mech)
        _l, p1, p2 = ev.witness_loss(mech, w["dataset"], w["neighbour"], w["event"])
        row.update({"delta_bound": float("%.3g" % (eta * (1 + math.exp(ev.EPSILON)))),
                    "straddle_mass": float("%.3g" % max(p1, p2))})
    if spec["kind"] == "noise_scale":
        a = spec["anchor"]
        loss, p1, p2 = ev.witness_loss(mech, a["dataset"], a["neighbour"], a["event"])
        hi, lo = max(p1, p2), min(p1, p2)
        row.update({"anchor_loss": round(loss, 4), "anchor_mass": [round(hi, 4), round(lo, 4)],
                    "runs_per_side_at_0.2": runs_needed(hi, lo, 0.2),
                    "runs_per_side_at_0.05": runs_needed(hi, lo, 0.05)})
    if spec["kind"] == "branch":
        a = spec["anchor"]
        loss, p1, p2 = ev.witness_loss(mech, a["dataset"], a["neighbour"], a["event"])
        row.update({"straddle_loss": "inf" if math.isinf(loss) else loss, "straddle_mass": round(max(p1, p2), 4)})
    print(json.dumps(row), flush=True)
