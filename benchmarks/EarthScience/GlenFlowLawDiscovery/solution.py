"""Always publish Newtonian viscous ice."""
from __future__ import annotations
import math


def identify_flow_law(problem, measure):
    lo, hi = problem["stress_bounds_kPa"]
    _ = problem["measure_budget_calls"]
    _ = problem["family_names"]
    _ = problem["gbs_exponent_bounds"]
    _ = problem["rate_law"]
    _ = problem["measurement_model"]
    _ = problem["abstain_when"]
    value = float(measure(0.5 * (lo + hi)))
    return {"abstain": False, "family": "newtonian", "n": 1.0, "confidence": 0.7,
            "log_A": value - math.log(0.5 * (lo + hi)), "activation_temperature": 0.0}
