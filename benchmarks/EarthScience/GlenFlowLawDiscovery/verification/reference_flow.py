"""Public-input stress/temperature design and joint log-linear fit.

Labels only Glen and Newtonian windows. A third supported power-law family
(GBS, n around 1.8) falls between those windows and is abstained.
"""
from __future__ import annotations
import math
import numpy as np


def identify_flow_law(problem, measure):
    lo, hi = problem["stress_bounds_kPa"]
    temperatures = problem["temperature_bounds_K"]
    reference_t = problem["reference_temperature_K"]
    stresses = (lo, math.sqrt(lo * hi), hi)
    rows, values, curvatures = [], [], []
    for temperature in temperatures:
        means = []
        for stress in stresses:
            y = sum(float(measure(stress, temperature)) for _ in range(2)) / 2.0
            rows.append([1.0, math.log(stress), -(1.0 / temperature - 1.0 / reference_t)])
            values.append(y)
            means.append(y)
        spacing = math.log(stresses[1] / stresses[0])
        curvatures.append((means[2] - 2.0 * means[1] + means[0]) / spacing)
    log_a, n, activation = np.linalg.lstsq(np.asarray(rows), np.asarray(values), rcond=None)[0]
    if max(abs(x) for x in curvatures) > 0.12 or activation < 0:
        return {"abstain": True, "confidence": 0.05}
    if 2.5 <= n <= 3.7:
        family = "glen"
    elif 0.8 <= n <= 1.2:
        family = "newtonian"
    else:
        return {"abstain": True, "confidence": 0.05}
    return {"abstain": False, "family": family, "n": float(n), "log_A": float(log_a),
            "activation_temperature": float(activation), "confidence": 0.8}
