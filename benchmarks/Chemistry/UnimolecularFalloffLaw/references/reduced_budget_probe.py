"""Eight-assay ablation of the same complete pressure-curve estimator."""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import least_squares


def _log_rate(log_pressure, parameters):
    log_kinf, log_pr = parameters[:2]
    reduced = log_pr + log_pressure
    result = log_kinf + reduced - np.logaddexp(0.0, reduced)
    if len(parameters) == 3:
        log_fcent = parameters[2]
        width = 0.75 - 1.27 * log_fcent / math.log(10.0)
        result += log_fcent / (1.0 + (reduced / math.log(10.0) / width) ** 2)
    return result


def identify_falloff(problem, measure):
    lo_t, hi_t = problem["temperature_bounds_K"]
    lo_p, hi_p = problem["pressure_bounds_bar"]
    budget = min(8, int(problem["measure_budget_calls"]))
    temperature = min(max(300.0, lo_t), hi_t)
    # Four additional-temperature observations test whether pressure order reverses.
    pressure_count = budget - 4
    if pressure_count < 4:
        return {"abstain": True, "confidence": 0.0}
    pressures = np.geomspace(lo_p, hi_p, pressure_count)
    values = np.array([float(measure(temperature, float(p))) for p in pressures])
    for target in (600.0, 900.0):
        hot = min(max(target, lo_t), hi_t)
        low = float(measure(hot, lo_p))
        high = float(measure(hot, hi_p))
        if high < low - 0.1:
            return {"abstain": True, "confidence": 0.86}
    order = (values[2] - values[0]) / math.log(pressures[2] / pressures[0])
    if values[-1] < values[0] - 0.1 or order < 0.42:
        return {"abstain": True, "confidence": 0.82}

    log_pressure = np.log(pressures)
    initial = [float(values[-1]), float(values[0] - math.log(lo_p) - values[-1])]
    fits = []
    for family in ("lindemann", "troe"):
        starts = [initial] if family == "lindemann" else [
            initial + [math.log(fcent)] for fcent in (0.2, 0.7)
        ]
        lower = [-50.0, -30.0] + ([math.log(0.05)] if family == "troe" else [])
        upper = [50.0, 30.0] + ([0.0] if family == "troe" else [])
        candidates = [least_squares(
            lambda params: _log_rate(log_pressure, params) - values,
            np.clip(start, lower, upper), bounds=(lower, upper),
            ftol=1e-12, xtol=1e-12, gtol=1e-12,
        ) for start in starts]
        result = min(candidates, key=lambda fit: float(np.dot(fit.fun, fit.fun)))
        residual = float(np.dot(result.fun, result.fun))
        # BIC compares the two public model families rather than fixing Fcent a priori.
        criterion = pressure_count * math.log(max(residual / pressure_count, 1e-24))
        criterion += len(result.x) * math.log(pressure_count)
        fits.append((criterion, family, result.x))
    _, family, parameters = min(fits, key=lambda fit: fit[0])
    return {"abstain": False, "family": family,
            "log_k_inf_300K": float(parameters[0]),
            "log_Pr_300K_1bar": float(parameters[1]),
            "Fcent": math.exp(float(parameters[2])) if family == "troe" else 1.0,
            "confidence": 0.72}
