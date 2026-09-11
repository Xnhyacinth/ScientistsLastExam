"""How many runs per side does a Clopper-Pearson certificate of the anchor witness need?"""
import importlib.util
import math
from pathlib import Path

from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/ComputerScience/SparseVectorAudit"
spec_ = importlib.util.spec_from_file_location("sva_oracle", TASK / "verification/evaluator.py")
ev = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(ev)


def certified(p1, p2, n, alpha=0.05):
    x1, x2 = p1 * n, p2 * n
    lo = beta.ppf(alpha / 2, x1, n - x1 + 1); hi = beta.ppf(1 - alpha / 2, x2 + 1, n - x2)
    return math.log((lo - ev.DELTA) / hi) if lo > ev.DELTA else -math.inf


for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
    if spec["kind"] != "noise_scale":
        continue
    w = ev._world(spec); m = w["mechanism"]; a = spec["anchor"]
    loss, p1, p2 = ev.witness_loss(m, a["dataset"], a["neighbour"], a["event"])
    if p2 > p1:
        p1, p2 = p2, p1
    need = next((n for n in (2000, 5000, 10000, 20000, 40000, 60000, 80000, 100000) if certified(p1, p2, n) > ev.EPSILON), None)
    # the best event for the anchor pair traded for mass: sweep prefixes
    print("%-16s anchor %.3f p1 %.4f p2 %.4f  runs/side for CP>eps: %s  cert@40k %.3f @80k %.3f" % (
        spec["name"], loss, p1, p2, need, certified(p1, p2, 40000), certified(p1, p2, 80000)))
