"""Public-only three-assay counterexample from the September 9 review."""
import math


def identify_falloff(problem, measure):
    lo_p, hi_p = problem["pressure_bounds_bar"]
    temperature = problem["temperature_bounds_K"][0]
    mid_p = min(10 * lo_p, hi_p)
    high = float(measure(temperature, hi_p))
    low = float(measure(temperature, lo_p))
    mid = float(measure(temperature, mid_p))
    if high < low - 0.1 or (mid - low) / math.log(mid_p / lo_p) < 0.42:
        return {"abstain": True, "confidence": 0.82}
    log_pr = low - math.log(lo_p) - high
    pr_mid = math.exp(log_pr) * mid_p
    f_obs = math.exp(mid - high) * (1 + pr_mid) / pr_mid
    family = "troe" if f_obs < 0.82 else "lindemann"
    return {"abstain": False, "family": family, "log_k_inf_300K": high,
            "log_Pr_300K_1bar": log_pr, "Fcent": 0.4 if family == "troe" else 1.0,
            "confidence": 0.72}
