"""Related constant-Pr red-team strategy, not the missing original C9 source.

Three public pressure assays; fit log k_inf and Fcent with log Pr held fixed.
Running this file as an audit scans a declared grid using development only.
"""
import math

import numpy as np
from scipy.optimize import least_squares

LOG_PR = -4.0


def identify_falloff(problem, measure):
    low, high = problem["pressure_bounds_bar"]
    pressures = np.array([low, min(10 * low, high), high])
    values = np.array([measure(problem["temperature_bounds_K"][0], float(p))
                       for p in pressures])
    order = (values[1] - values[0]) / math.log(pressures[1] / pressures[0])
    if values[-1] < values[0] - 0.1 or order < 0.42:
        return {"abstain": True, "confidence": 0.82}
    reduced = LOG_PR + np.log(pressures)
    base = reduced - np.logaddexp(0, reduced)
    fits = []
    for family in ("lindemann", "troe"):
        def residual(parameters):
            predicted = parameters[0] + base
            if family == "troe":
                width = 0.75 - 1.27 * parameters[1] / math.log(10)
                predicted = predicted + parameters[1] / (1 + (reduced / math.log(10) / width) ** 2)
            return predicted - values
        start = [float(values[-1])] + ([math.log(0.4)] if family == "troe" else [])
        fit = least_squares(residual, start,
                            bounds=([-50] + ([math.log(0.05)] if family == "troe" else []),
                                    [50] + ([-1e-10] if family == "troe" else [])))
        rss = float(fit.fun @ fit.fun)
        bic = 3 * math.log(max(rss / 3, 1e-24)) + len(start) * math.log(3)
        fits.append((bic, family, fit.x))
    _, family, params = min(fits, key=lambda row: row[0])
    return {"abstain": False, "family": family, "log_k_inf_300K": float(params[0]),
            "log_Pr_300K_1bar": LOG_PR,
            "Fcent": math.exp(float(params[1])) if family == "troe" else 1.0,
            "confidence": 0.72}


if __name__ == "__main__":
    import importlib.util
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "verification/evaluator.py"
    spec = importlib.util.spec_from_file_location("audit_oracle", path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    rows = []
    for step in range(-24, -7):
        LOG_PR = step / 4
        result = oracle.evaluate(identify_falloff)
        rows.append({"log_pr": LOG_PR, "development": result["combined_score"],
                     "heldout": result["heldout_mechanism_score"], "valid": result["valid"]})
    print(json.dumps({"selection": "development only; heldout is diagnostic",
                      "scope": "related reconstruction, not original owner C9",
                      "grid": rows, "best": max(rows, key=lambda row: row["development"])}, indent=2))
