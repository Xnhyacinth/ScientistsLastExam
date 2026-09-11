"""The compliant worlds' strongest witnesses: loss and the mass of the event on each side."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import anchors as an  # noqa: E402

ev = an.ev
rng = np.random.default_rng(20260911)
for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
    if spec["kind"] not in ("compliant", "compliant_branch"):
        continue
    mech = ev._Mechanism(spec)
    loss, w = an.local_search(mech, rng, 24, 200)
    l2, p1, p2 = ev.witness_loss(mech, w["dataset"], w["neighbour"], w["event"])
    print("%-24s loss %.4f  event of %d outputs, mass %.4f vs %.4f" % (
        spec["name"], l2, len(w["event"]), max(p1, p2), min(p1, p2)))
