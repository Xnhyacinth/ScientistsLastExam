"""Builder-only full parameter/noise grid; does not modify release worlds on disk.

Uses trusted oracle internals in process. It is neither a candidate nor sandbox
validation, a sealed holdout, external scientific data, or calibration evidence.
Run from this project via uv; --output stores all rows, protocol and source hashes.
"""

import argparse
import hashlib
import importlib.util
import itertools
import json
import pathlib
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[4]
    task = root / "benchmarks/Chemistry/UnimolecularFalloffLaw"

    def load(path, name):
        s = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        return m

    e = load(task / "verification/evaluator.py", "ev")
    r = load(task / "verification/reference_falloff.py", "ref")
    # Complete Cartesian diagnostic, fixed before results; no scoring/noise/window change.
    wall = (0.6, 1.2, 2.4, 4.8, 6.0)
    fc = (0.15, 0.30, 0.45, 0.60, 0.75)
    offsets = (100, 102, 104, 106)
    rows = []
    for split, worlds in [
        ("development", e.DEVELOPMENT_WORLDS),
        ("heldout", e.HELDOUT_WORLDS),
    ]:
        for index, base in enumerate(worlds):
            params = (
                itertools.product(wall, fc if base["kind"] == "troe" else (None,))
                if base["kind"] in e.SUPPORTED
                else ((None, None),)
            )
            for pr, fcent in params:
                for off in offsets:
                    w = dict(base, seed=base["seed"] + off)
                    if pr is not None:
                        w["A0"] = e._a0_for_wall_pr(w["A_inf"], w["E_inf"], w["E0"], pr)
                    if fcent is not None:
                        w["Fcent"] = fcent
                    out = {}
                    for b in (8, 18):
                        e.PUBLIC_PROBLEM["measure_budget_calls"] = b
                        out[str(b)] = e._evaluate_world(
                            r.identify_falloff, w, split, index
                        )
                    rows.append(
                        {
                            "split": split,
                            "index": index,
                            "wall_pr": pr,
                            "fcent": fcent,
                            "offset": off,
                            "results": out,
                        }
                    )
    summary = {}
    for split in ("development", "heldout"):
        rr = [
            x
            for x in rows
            if x["split"] == split and x["results"]["8"]["kind"] in e.SUPPORTED
        ]
        means = {
            str(b): statistics.mean(x["results"][str(b)]["mechanism_score"] for x in rr)
            for b in (8, 18)
        }
        summary[split] = {
            "in_family_worlds": len(rr),
            "mean": means,
            "retention": means["8"] / means["18"],
            "fraction_8_at_least_80pct": sum(
                x["results"]["8"]["mechanism_score"]
                >= 0.8 * x["results"]["18"]["mechanism_score"]
                for x in rr
            )
            / len(rr),
        }
    summary["valid_all"] = all(
        x["results"][str(b)]["valid"] for x in rows for b in (8, 18)
    )
    summary["refusal"] = {
        str(b): statistics.mean(
            x["results"][str(b)]["correct_refusal"]
            for x in rows
            if x["results"][str(b)]["kind"] not in e.SUPPORTED
        )
        for b in (8, 18)
    }
    output = {
        "protocol": {
            "wall_pr": wall,
            "fcent": fc,
            "noise_offsets": offsets,
            "score_scope": "in-family mechanism mean, not release normalized score; procedural diagnostic, not independent physical data",
        },
        "summary": summary,
        "rows": rows,
        "source_hashes": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                task / "verification/evaluator.py",
                task / "verification/reference_falloff.py",
            )
        },
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
