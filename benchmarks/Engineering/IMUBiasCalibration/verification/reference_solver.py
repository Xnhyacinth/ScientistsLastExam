"""Truth-blind approximate D-optimal design and weighted nested-model tests."""
from __future__ import annotations

import numpy as np
from math import erfc, sqrt


def _features(problem, settings):
    u = np.asarray([s["orientation"] for s in settings])
    x = np.asarray([(s["temperature_c"]-problem["reference_temperature_c"])
                    / problem["temperature_scale_c"] for s in settings])
    return np.column_stack([np.ones(len(x)), x, u, x*x, x[:, None]*u,
                            u[:, 0]**2-u[:, 2]**2, u[:, 1]**2-u[:, 2]**2])


def _design(problem, budget, central_only=False, sequential=False):
    settings = problem["settings"]
    F = _features(problem, settings)
    sigma = np.asarray([s["noise_std_mps2"] for s in settings])
    F /= np.sqrt(np.mean(sigma*sigma, axis=1))[:, None]
    F /= np.maximum(np.sqrt(np.mean(F*F, axis=0)), 1e-8)
    inverse = np.eye(F.shape[1])*1e6
    selected = []
    allowed = np.ones(len(settings), dtype=bool)
    if central_only:
        allowed = np.asarray([abs(s["temperature_c"]-problem["reference_temperature_c"]) <= 12.5 for s in settings])
    for index in range(budget):
        leverage = np.einsum("ij,jk,ik->i", F, inverse, F)
        leverage[~allowed] = -1
        chosen = index % len(settings) if sequential else int(np.argmax(leverage))
        selected.append(settings[chosen]["setting_id"])
        direction = inverse @ F[chosen]
        inverse -= np.outer(direction, direction)/(1 + F[chosen] @ direction)
        inverse = (inverse+inverse.T)/2
    return selected


def _infer_imu(problem, measure, *, measurement_limit=None, central_only=False,
               sequential=False, disabled_faults=(), diagonal_only=False):
    count = problem["measurement_budget"] if measurement_limit is None else min(measurement_limit, problem["measurement_budget"])
    rows = [measure(i) for i in _design(problem, count, central_only, sequential)]
    g, scale = problem["gravity_mps2"], problem["temperature_scale_c"]
    u = np.asarray([r["orientation"] for r in rows])
    x = np.asarray([(r["temperature_c"]-problem["reference_temperature_c"])/scale for r in rows])
    y = np.asarray([r["accel_mps2"] for r in rows])-g*u
    sigma = np.asarray([r["noise_std_mps2"] for r in rows])
    matrix, bias, drift = np.eye(3), np.zeros(3), np.zeros(3)
    hypotheses = []
    for axis in range(3):
        components = [axis] if diagonal_only else list(range(axis, 3))
        X = np.column_stack([np.ones(len(rows)), x, u[:, components]])/sigma[:, axis, None]
        Y = y[:, axis]/sigma[:, axis]
        coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
        bias[axis], drift[axis] = coef[0], coef[1]/scale
        matrix[axis, components] += coef[2:]/g
        residual = Y-X@coef
        alternatives = [("thermal_nonlinearity", x*x),
                        ("motion_contamination", (3*u[:, (axis+1) % 3]**2-1)/2)]
        alternatives += [("axis_misalignment", x*u[:, j]) for j in range(3) if j != axis]
        for label, feature in alternatives:
            if label in disabled_faults:
                continue
            v = feature/sigma[:, axis]
            projected = v-X@np.linalg.lstsq(X, v, rcond=None)[0]
            information = float(projected@projected)
            statistic = float(projected@residual)**2/information if information > 1e-10 else 0.0
            hypotheses.append((statistic, label, axis))
    statistic, label, axis = max(hypotheses, default=(0, "undetermined", None))
    # Known-noise nested Gaussian models add one parameter. Bonferroni controls
    # the familywise false-refusal rate without fitting thresholds to worlds.
    # Keep the full twelve-test correction when a diagnostic is ablated too.
    pvalue = min(1.0, 12*erfc(sqrt(statistic/2)))
    abstain = pvalue < .05
    prediction = [matrix @ (g*np.asarray(s["orientation"])) + bias
                  + drift*(s["temperature_c"]-problem["reference_temperature_c"])
                  for s in problem["prediction_settings"]]
    return {"bias_mps2": bias.tolist(), "temperature_drift_mps2_per_c": drift.tolist(),
            "calibration_matrix": matrix.tolist(), "prediction_accel_mps2": np.asarray(prediction).tolist(),
            "diagnosis": label if abstain else "supported", "fault_axis": axis if abstain else None,
            "confidence": 1-pvalue if abstain else .95, "abstain": bool(abstain),
            "evidence_ids": [r["query_id"] for r in rows]}


def infer_imu(problem, measure):
    return _infer_imu(problem, measure)
