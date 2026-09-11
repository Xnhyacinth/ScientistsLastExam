"""Construction checks for SparseVectorAudit: Python 3.8 syntax of every module, determinism,
blanket refusal in both forms, the specification's compliance on the library, the
compliant-branch worlds below delta, and every violating world's anchor above epsilon.

    .venv/bin/python .research/sparse_vector_audit/checks.py
"""
import ast
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import anchors as an  # noqa: E402
from run_both import CANDIDATES, ROOT, TASK, ev  # noqa: E402

modules = sorted(TASK.rglob("*.py")) + sorted(Path(__file__).parent.glob("*.py"))
modules.append(ROOT / "tests/test_sparse_vector_audit.py")
for path in modules:
    if path.is_file():
        ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 8))
print("python 3.8 syntax: %d modules parse" % sum(p.is_file() for p in modules))

reference = CANDIDATES["reference"]()
first, second = ev.evaluate(reference), ev.evaluate(reference)
print("determinism:", json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True))
for submission in ({"verdict": "no_violation"}, {"abstain": True}):
    m = ev.evaluate(lambda _p, _s, s=submission: dict(s))
    print("blanket refusal %s: combined %.4f valid %.1f refusal %.2f" % (
        submission, m["combined_score"], m["valid"], m["development_correct_refusal_rate"]))

for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
    mech = ev._Mechanism(spec)
    if spec["kind"] in ("compliant", "compliant_branch"):
        best = max(ev.best_event_loss(mech, a, b)[0] for a, b in an.library(mech.k))
        best = max(best, max(ev.best_event_loss(mech, b, a)[0] for a, b in an.library(mech.k)))
        line = "%-24s library best loss %.4f (epsilon %.1f)" % (spec["name"], best, ev.EPSILON)
        if spec["kind"] == "compliant_branch":
            offset, side, positions = mech.branch
            flip = an.p_correct_flip(mech, offset, side)
            eta = flip if (side == "up" and mech.c == 1) else flip * len(positions)
            w = an.straddle(mech)
            loss, p1, p2 = ev.witness_loss(mech, w["dataset"], w["neighbour"], w["event"])
            line += "  coupling delta %.2e  straddle mass %.2e  straddle loss %s" % (
                eta * (1 + math.exp(ev.EPSILON)), max(p1, p2), loss)
        print(line)
    else:
        a = spec["anchor"]
        loss = ev.witness_loss(mech, a["dataset"], a["neighbour"], a["event"])[0]
        print("%-24s anchor loss %s" % (spec["name"], loss))
