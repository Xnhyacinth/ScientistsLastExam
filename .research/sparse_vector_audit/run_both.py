"""Score the reference, the baseline and blanket refusal on both splits.

    .venv/bin/python .research/sparse_vector_audit/run_both.py [reference|baseline|abstain]
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "benchmarks/ComputerScience/SparseVectorAudit"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ev = load(TASK / "verification/evaluator.py", "sva_oracle")
CANDIDATES = {
    "reference": lambda: load(TASK / "verification/reference_library_scan.py", "sva_ref").audit,
    "baseline": lambda: load(TASK / "solution.py", "sva_base").audit,
    "abstain": lambda: (lambda p, s: {"verdict": "no_violation"}),
}


def main():
    which = sys.argv[1:] or list(CANDIDATES)
    for name in which:
        t0 = time.time()
        m = ev.evaluate(CANDIDATES[name]())
        keys = [k for k in m if k != "per_instance"]
        print("==", name, "%.1fs" % (time.time() - t0))
        print(json.dumps({k: (round(m[k], 4) if isinstance(m[k], float) else m[k]) for k in keys}))
        for r in m["per_instance"]:
            print("  %-11s %2d %-17s abst=%-5s loss=%-9s strength=%.3f fd=%-5s samples=%d %s" % (
                r["split"], r["world_index"], r["kind"], r["abstained"], r["witness_loss"],
                r["witness_strength"], r["false_discovery"], r["samples_used"], r.get("reason", "")))


if __name__ == "__main__":
    main()
