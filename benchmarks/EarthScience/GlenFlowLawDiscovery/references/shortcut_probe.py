"""Reproduce the scalar-threshold shortcut and fresh-noise separation audit."""
from __future__ import annotations
import math

THRESHOLD = 0.03


def identify_flow_law(problem, measure):
    stresses = [20.0, 63.0, 200.0]
    values = [sum(measure(x) for _ in range(4)) / 4 for x in stresses]
    slopes = [(values[i+1]-values[i]) / math.log(stresses[i+1]/stresses[i]) for i in range(2)]
    n = (values[-1]-values[0]) / math.log(10)
    if abs(slopes[1]-slopes[0]) > THRESHOLD or n < 0.6:
        return {"abstain": True, "confidence": 0.0}
    return {"abstain": False, "family": "newtonian" if n < 1.4 else "glen", "n": n,
            "log_A": sum(y-n*math.log(x) for x,y in zip(stresses,values))/3,
            "activation_temperature": 6000.0, "confidence": 0.8}


if __name__ == "__main__":
    import importlib.util
    import json
    from pathlib import Path
    import numpy as np
    path = Path(__file__).resolve().parents[1] / "verification/evaluator.py"
    spec = importlib.util.spec_from_file_location("glen_probe_oracle", path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    best = None
    for step in range(1,61):
        THRESHOLD = step / 100
        result = oracle.evaluate(identify_flow_law)
        row = {"threshold": THRESHOLD, "score": result["combined_score"],
               "heldout": result["heldout_mechanism_score"]}
        if best is None or row["score"] > best["score"]:
            best = row
    print(json.dumps({"threshold_sweep": best}))
    noise = np.random.default_rng(20260908).normal(0,0.03,size=(4000,3,4)).mean(axis=2)
    spacing = math.log(math.sqrt(10))
    for world in [oracle.DEVELOPMENT_WORLDS[0], oracle.DEVELOPMENT_WORLDS[5], oracle.HELDOUT_WORLDS[5]]:
        y = [math.log(oracle.true_speed(world,x)) for x in [20,math.sqrt(4000),200]]
        curvature = (y[2]-2*y[1]+y[0]) / spacing
        observed = curvature + (noise[:,2]-2*noise[:,1]+noise[:,0]) / spacing
        print(json.dumps({"seed":world["seed"], "true_curvature":curvature,
                          "p_gt_012":float(np.mean(observed > 0.12))}))

    # The same complete estimator with one ability removed at a time.
    from functools import partial
    ref_path = path.with_name("reference_flow.py")
    ref_spec = importlib.util.spec_from_file_location("glen_complete_reference", ref_path)
    reference = importlib.util.module_from_spec(ref_spec)
    ref_spec.loader.exec_module(reference)
    for name, candidate in (
        ("complete_reference", reference.identify_flow_law),
        ("no_repeat", partial(reference.identify_flow_law, repeats=1)),
        ("no_temperature_same_budget", partial(reference.identify_flow_law,
                                               repeats=4, temperature_arm=False)),
    ):
        result = oracle.evaluate(candidate)
        print(json.dumps({"candidate": name, "development": result["combined_score"],
                          "heldout": result["heldout_mechanism_score"],
                          "valid": result["valid"],
                          "calls": [r["measure_calls"] for r in result["per_instance"]]}))
