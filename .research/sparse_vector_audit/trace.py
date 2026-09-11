"""Trace the reference's library stage on the noise-scale worlds: screened pairs, plug-in values,
chosen events, and what the exact loss of each chosen event is."""
import importlib.util
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/ComputerScience/SparseVectorAudit"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ev = load(TASK / "verification/evaluator.py", "sva_oracle")
ref = load(TASK / "verification/reference_library_scan.py", "sva_ref")
names = sys.argv[1:]
for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
    if spec["kind"] != "noise_scale" or (names and spec["name"] not in names):
        continue
    world = ev._world(spec)
    mech = world["mechanism"]
    problem = ev._public_problem(world)
    sample = ev._Campaign(world).oracle()
    k, t, delta = mech.k, ev.THRESHOLD, ev.DELTA
    screened, rows = {}, []
    for a, b in ref._library(k, t):
        for q in (a, b):
            if tuple(q) not in screened:
                screened[tuple(q)] = (sample(q, ref.SCREEN_RUNS), ref.SCREEN_RUNS)
        for f, s in ((a, b), (b, a)):
            c1, n1 = screened[tuple(f)]; c2, n2 = screened[tuple(s)]
            v, e = ref._plug_in_event(delta, c1, n1, c2, n2)
            exact, p1, p2 = ev.witness_loss(mech, f, s, e) if e else (-math.inf, 0, 0)
            best_exact, best_e = ev.best_event_loss(mech, f, s)
            rows.append((v, exact, p1, p2, len(e), best_exact, f, s))
    rows.sort(key=lambda r: -r[0])
    print("==", spec["name"], "anchor %.3f" % world["anchor_loss"])
    for v, exact, p1, p2, ne, be, f, s in rows[:6]:
        print("  plug-in %.3f  exact-of-chosen %.3f (p1 %.4f p2 %.4f |S| %d)  pair-best %.3f  %s -> %s" % (
            v, exact, p1, p2, ne, be, [x - t for x in f], [x - t for x in s]))
