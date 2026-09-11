"""Try reference variants built by source substitution; print per-world outcomes on the
noise-scale worlds plus the split scores.

    .venv/bin/python .research/sparse_vector_audit/variants.py NAME...
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/ComputerScience/SparseVectorAudit"
sys.path.insert(0, str(Path(__file__).parent))
from run_both import ev  # noqa: E402

SRC = (TASK / "verification/reference_library_scan.py").read_text()

ONE_PAIR = [("CONFIRM_PAIRS = 2", "CONFIRM_PAIRS = 1"),
            ("CONFIRM_MAX_RUNS = 40000", "CONFIRM_MAX_RUNS = 10**9")]
MASS_FLOOR = [("        if A[j] > delta:\n", "        if A[j] > delta and A[j] * n1 >= MIN_HITS:\n"),
              ("SUPPORT = 1500\n", "SUPPORT = 1500\nMIN_HITS = 40\n")]
SCREEN8 = [("SCREEN_RUNS = 4000", "SCREEN_RUNS = 8000")]
SHRINK = [("    p1 = np.array([c1.get(o, 0) / n1 for o in outputs])\n",
           "    p1 = np.array([c1.get(o, 0) / n1 for o in outputs])\n    raw1 = np.array([c1.get(o, 0) for o in outputs])\n"),
          ("            v = math.log((A[j] - delta) / B[j])\n",
           "            hits = np.cumsum(raw1[order])[j]\n"
           "            lo = max(A[j] - 1.645 * math.sqrt(A[j] / n1), 0.0)\n"
           "            hi = B[j] + 1.645 * math.sqrt(B[j] / n2)\n"
           "            if lo <= delta:\n                continue\n"
           "            v = math.log((lo - delta) / hi)\n")]
VARIANTS = {
    "current": [],
    "one_pair": ONE_PAIR,
    "one_pair_floor": ONE_PAIR + MASS_FLOOR,
    "one_pair_screen8": ONE_PAIR + SCREEN8,
    "one_pair_shrink": ONE_PAIR + SHRINK,
    "one_pair_screen8_shrink": ONE_PAIR + SCREEN8 + SHRINK,
    "one_pair_screen6_shrink": ONE_PAIR + [("SCREEN_RUNS = 4000", "SCREEN_RUNS = 6000")] + SHRINK,
    "one_pair_screen8_a20": ONE_PAIR + SCREEN8 + [("CONFIRM_ALPHA = 0.05", "CONFIRM_ALPHA = 0.2")],
    "one_pair_screen8_shrink_a20": ONE_PAIR + SCREEN8 + SHRINK + [("CONFIRM_ALPHA = 0.05", "CONFIRM_ALPHA = 0.2")],
    "two_pair_shrink": [("CONFIRM_MAX_RUNS = 40000", "CONFIRM_MAX_RUNS = 10**9")] + SHRINK,
}


def build(name):
    src = SRC
    for old, new in VARIANTS[name]:
        assert src.count(old) == 1, (name, old)
        src = src.replace(old, new)
    mod = types.ModuleType("variant_" + name)
    exec(compile(src, name, "exec"), mod.__dict__)
    return mod.audit


for name in sys.argv[1:] or VARIANTS:
    m = ev.evaluate(build(name))
    rows = " ".join("%s:%s" % (r["kind"][:2] + str(r["world_index"]), "%.2f" % r["witness_strength"] if not r["abstained"] else ("ok" if r["kind"].startswith("compliant") else "--"))
                    for r in m["per_instance"] if r["kind"] in ("noise_scale", "branch"))
    print("%-18s dev %.4f held %.4f fdr %.2f/%.2f samples %.0f | %s" % (
        name, m["combined_score"] if "combined_score" in m else m["development_mechanism_score"],
        m["heldout_mechanism_score"], m["development_false_discovery_rate"], m["heldout_false_discovery_rate"],
        m["development_mean_samples_used"], rows))
