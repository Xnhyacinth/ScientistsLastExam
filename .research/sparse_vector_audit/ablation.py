"""Ablation ladder: the reference with one stage removed or weakened at a time, plus the
documented headroom.

    SVA_ONLY=no_scan,alpha_005 .venv/bin/python .research/sparse_vector_audit/ablation.py
"""
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_both import ev, load, TASK  # noqa: E402

SRC = (TASK / "verification/reference_library_scan.py").read_text()
CONFIRM_START = "    # --- confirm on fresh samples"
LIBRARY_START = "    # --- screen the library"
FIXED_SCAN = ("        n = math.ceil(SCAN_EXPECTED / max(p, 1e-300))\n        if n > SCAN_MAX_RUNS:\n            return None\n",
              "        n = 2000\n")
SCAN_NO_CONFIRM = ("            p_next = _dissent_probability(problem, offset - 1, side)\n",
                   "            return {\"verdict\": \"violation\", \"dataset\": neighbour, \"neighbour\": dataset,\n"
                   "                    \"event\": event, \"confidence\": 0.9}\n"
                   "            p_next = _dissent_probability(problem, offset - 1, side)\n")
RUNGS = {
    "reference": [],
    "no_scan": [('    for side in ("up", "down"):\n        room', '    for side in ():\n        room')],
    "no_library": [(LIBRARY_START, '    return {"verdict": "no_violation", "confidence": 0.7}\n' + LIBRARY_START)],
    "screen_4000": [("SCREEN_RUNS = 8000", "SCREEN_RUNS = 4000")],
    "alpha_005": [("CONFIRM_ALPHA = 0.2 ", "CONFIRM_ALPHA = 0.05 ")],
    "alpha_050": [("CONFIRM_ALPHA = 0.2 ", "CONFIRM_ALPHA = 0.5 ")],
    "ignore_delta": [("        if _certified(delta, x1, n1, x2, n2, CONFIRM_ALPHA) > eps:",
                      "        if _certified(0.0, x1, n1, x2, n2, CONFIRM_ALPHA) > eps:")],
    "library_no_confirm": [(CONFIRM_START, "    if pairs[0][0] > eps:\n        _v, first, second, event = pairs[0]\n"
                            "        return {\"verdict\": \"violation\", \"dataset\": list(first), \"neighbour\": list(second),\n"
                            "                \"event\": event, \"confidence\": 0.8}\n"
                            "    return {\"verdict\": \"no_violation\", \"confidence\": 0.7}\n" + CONFIRM_START)],
    "scan_no_confirm": [SCAN_NO_CONFIRM],
    "fixed_scan_no_confirm": [FIXED_SCAN, SCAN_NO_CONFIRM],
}


def build(name):
    src = SRC
    for old, new in RUNGS[name]:
        assert src.count(old) == 1, (name, old)
        src = src.replace(old, new)
    mod = types.ModuleType("rung_" + name)
    exec(compile(src, name, "exec"), mod.__dict__)
    return mod.audit


def row(name, audit):
    m = ev.evaluate(audit)
    won = [r["split"][0] + str(r["world_index"]) for r in m["per_instance"] if r["witness_strength"] > 0]
    print("%-22s dev %.4f held %.4f  fdr %.2f/%.2f  coverage %.2f/%.2f  won %s" % (
        name, m["development_mechanism_score"], m["heldout_mechanism_score"],
        m["development_false_discovery_rate"], m["heldout_false_discovery_rate"],
        m["development_discovery_coverage"], m["heldout_discovery_coverage"], " ".join(won)))


def main():
    only = [x for x in os.environ.get("SVA_ONLY", "").split(",") if x]
    for name in RUNGS:
        if not only or name in only:
            row(name, build(name))
    if not only or "headroom_positional" in only:
        row("headroom_positional", load(Path(__file__).parent / "headroom_positional.py", "sva_headroom").audit)


if __name__ == "__main__":
    main()
