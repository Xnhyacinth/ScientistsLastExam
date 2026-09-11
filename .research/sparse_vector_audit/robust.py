"""Rerun a candidate with every world's seed shifted, so the draws change and the worlds do not.

    SVA_SHIFTS=1,2,3 .venv/bin/python .research/sparse_vector_audit/robust.py [reference|baseline|headroom|no_confirm]
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_both import CANDIDATES, ev, load  # noqa: E402

CANDIDATES["headroom"] = lambda: load(Path(__file__).parent / "headroom_positional.py", "sva_headroom").audit
CANDIDATES["no_confirm"] = lambda: __import__("ablation").build("library_no_confirm")   # the probe's best

shifts = [int(x) for x in os.environ.get("SVA_SHIFTS", "0,1,2,3,4,5,6,7").split(",")]
name = (sys.argv[1:] or ["reference"])[0]
original = {s["name"]: s["seed"] for s in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS}
dev, held, fd = [], [], 0
for shift in shifts:
    for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
        spec["seed"] = original[spec["name"]] + 7919 * shift
    ev._WORLDS.clear()
    m = ev.evaluate(CANDIDATES[name]())
    fds = [r["split"][0] + str(r["world_index"]) for r in m["per_instance"] if r["false_discovery"]]
    fd += len(fds)
    dev.append(m["development_mechanism_score"]); held.append(m["heldout_mechanism_score"])
    print("shift %d  dev %.4f  held %.4f  false discoveries %s" % (shift, dev[-1], held[-1], fds or "none"))
print("mean dev %.4f (min %.4f max %.4f)  mean held %.4f (min %.4f max %.4f)  false discoveries %d" % (
    sum(dev) / len(dev), min(dev), max(dev), sum(held) / len(held), min(held), max(held), fd))
