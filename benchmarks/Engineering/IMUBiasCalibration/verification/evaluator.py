"""Trusted active accelerometer-calibration laboratory, schema 2."""
from __future__ import annotations

import copy
import math

import numpy as np

GRAVITY = 9.80665
T_REF = 25.0
BUDGET = 18
FAULTS = ("thermal_nonlinearity", "axis_misalignment", "motion_contamination")
VALID_DIAGNOSES = {"supported", "undetermined", *FAULTS}
PUBLIC_PROBLEM = {
    "schema_version": 2,
    "gravity_mps2": GRAVITY,
    "reference_temperature_c": T_REF,
    "temperature_scale_c": 25.0,
    "measurement_budget": BUDGET,
    "measurement_model": "a = calibration_matrix @ (g*u) + bias + drift*(T-T_ref) + noise",
    "calibration_convention": "upper triangular, positive diagonal; rigid mounting rotation is pre-registered",
    "diagnosis_values": sorted(VALID_DIAGNOSES),
    "fault_models": {
        "thermal_nonlinearity": "one response axis adds alpha*x*x",
        "axis_misalignment": "one response axis adds alpha*x*u[j], with j unequal to the response axis",
        "motion_contamination": "one response axis k adds alpha*(3*u[(k+1)%3]**2-1)/2",
    },
    "fault_amplitude_range_mps2": [0.035, 0.065],
    "abstain_when": "one of the three declared non-affine fault terms is supported; identify its response axis",
    "parameter_tolerances": {"bias_mps2": 0.035, "drift_mps2_per_c": 0.0014,
                             "matrix_frobenius": 0.006, "prediction_mps2": 0.07},
}

# All families share the same public design/noise distribution. Split and family
# never enter the public schema, candidate IDs, or measurement uncertainty.
DEVELOPMENT_WORLDS = tuple({"seed": 34001 + i, "kind": kind} for i, kind in enumerate(
    ["supported"] * 12 + [kind for kind in FAULTS for _ in range(3)]))
HELDOUT_WORLDS = tuple({"seed": 57001 + i, "kind": kind} for i, kind in enumerate(
    ["supported"] * 12 + [kind for kind in FAULTS for _ in range(3)]))


def _world(spec):
    rng = np.random.default_rng(spec["seed"])
    matrix = np.eye(3)
    matrix[np.diag_indices(3)] += rng.uniform(-.025, .025, 3)
    matrix[np.triu_indices(3, 1)] = rng.uniform(-.018, .018, 3)
    return {**spec, "matrix": matrix, "bias": rng.uniform(-.20, .20, 3),
            "drift": rng.uniform(-.003, .003, 3), "axis": int(rng.integers(3)),
            "driver": int(rng.integers(2)),
            "amplitude": float(rng.uniform(.035, .065) * rng.choice([-1, 1]))}


def public_problem(spec):
    rng = np.random.default_rng([spec["seed"], 123])
    directions = rng.normal(size=(8, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    directions = np.concatenate([directions, -directions])
    catalog = []
    for direction in directions:
        for temperature in (0.0, 12.5, 25.0, 37.5, 50.0):
            catalog.append({"temperature_c": temperature, "orientation": direction.tolist(),
                            "noise_std_mps2": rng.uniform(.014, .028, 3).tolist()})
    rng.shuffle(catalog)
    for index, setting in enumerate(catalog):
        setting["setting_id"] = index
    predictions = []
    for temperature in (-5.0, 55.0, 40.0):
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        predictions.append({"temperature_c": temperature, "orientation": direction.tolist()})
    return {**copy.deepcopy(PUBLIC_PROBLEM), "settings": catalog, "prediction_settings": predictions}


def _clean(world, setting):
    u = np.asarray(setting["orientation"])
    dt = setting["temperature_c"] - T_REF
    x = dt / PUBLIC_PROBLEM["temperature_scale_c"]
    value = world["matrix"] @ (GRAVITY * u) + world["bias"] + world["drift"] * dt
    axis = world["axis"]
    if world["kind"] == "thermal_nonlinearity":
        value[axis] += world["amplitude"] * x*x
    elif world["kind"] == "axis_misalignment":
        driver = [j for j in range(3) if j != axis][world["driver"]]
        value[axis] += world["amplitude"] * x * u[driver]
    elif world["kind"] == "motion_contamination":
        value[axis] += world["amplitude"] * (3*u[(axis+1) % 3]**2 - 1)/2
    return value


class _Campaign:
    def __init__(self, world, problem):
        self.world, self.problem = world, problem
        self.calls, self.violated = 0, False
        self.ids = []

    def __call__(self, setting_id):
        if self.calls >= self.problem["measurement_budget"]:
            self.violated = True
            raise RuntimeError("measurement budget exhausted")
        if type(setting_id) is not int or not 0 <= setting_id < len(self.problem["settings"]):
            self.violated = True
            raise ValueError("setting_id must be an integer in the supplied catalog")
        self.calls += 1
        setting = self.problem["settings"][setting_id]
        rng = np.random.default_rng([self.world["seed"], 991, setting_id, self.calls])
        measured = _clean(self.world, setting) + rng.normal(size=3) * setting["noise_std_mps2"]
        query_id = f"q{self.calls:03d}"
        self.ids.append(query_id)
        return {**copy.deepcopy(setting), "query_id": query_id, "accel_mps2": measured.tolist()}


def _array(value, shape, name):
    arr = np.asarray(value)
    if arr.shape != shape or arr.dtype.kind not in "iuf" or not np.all(np.isfinite(arr)):
        raise ValueError(name + " must be a finite numeric array of shape " + str(shape))
    return arr.astype(float)


def _validate(submission, campaign):
    keys = {"bias_mps2", "temperature_drift_mps2_per_c", "calibration_matrix",
            "prediction_accel_mps2", "diagnosis", "fault_axis", "confidence", "abstain", "evidence_ids"}
    if not isinstance(submission, dict) or set(submission) != keys:
        raise ValueError("submission keys must match the public contract exactly")
    if type(submission["abstain"]) is not bool:
        raise ValueError("abstain must be boolean")
    if not isinstance(submission["diagnosis"], str) or submission["diagnosis"] not in VALID_DIAGNOSES:
        raise ValueError("unknown diagnosis")
    confidence = submission["confidence"]
    if type(confidence) not in (float, int) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be numeric in [0,1]")
    axis = submission["fault_axis"]
    if axis is not None and (type(axis) is not int or axis not in (0, 1, 2)):
        raise ValueError("fault_axis must be null or 0,1,2")
    if (submission["diagnosis"] in FAULTS) != (axis is not None):
        raise ValueError("fault diagnoses require a response axis; supported/undetermined require null")
    ids = submission["evidence_ids"]
    if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids) or len(set(ids)) != len(ids) or set(ids) != set(campaign.ids):
        raise ValueError("evidence_ids must contain all and only acquired query IDs once")
    result = dict(submission)
    for key, shape in (("bias_mps2", (3,)), ("temperature_drift_mps2_per_c", (3,)),
                       ("calibration_matrix", (3, 3)), ("prediction_accel_mps2", (3, 3))):
        result[key] = _array(submission[key], shape, key)
    matrix = result["calibration_matrix"]
    if np.max(np.abs(np.tril(matrix, -1))) > 1e-10 or np.any(np.diag(matrix) <= 0):
        raise ValueError("calibration_matrix must be upper triangular with positive diagonal")
    if campaign.violated:
        raise ValueError("measurement protocol violated even if the exception was caught")
    return result


def _score(world, answer, problem):
    supported = world["kind"] == "supported"
    claimed = not answer["abstain"]
    correct_model = supported and claimed and answer["diagnosis"] == "supported"
    correct_axis = not supported and answer["abstain"] and answer["fault_axis"] == world["axis"]
    refusal = correct_axis and answer["diagnosis"] == world["kind"]
    quality = {"bias_score": 0.0, "drift_score": 0.0, "matrix_score": 0.0, "prediction_score": 0.0}
    if correct_model:
        tolerances = problem["parameter_tolerances"]
        target = np.asarray([_clean(world, setting) for setting in problem["prediction_settings"]])
        errors = (("bias_score", np.linalg.norm(answer["bias_mps2"]-world["bias"]), tolerances["bias_mps2"]),
                  ("drift_score", np.linalg.norm(answer["temperature_drift_mps2_per_c"]-world["drift"]), tolerances["drift_mps2_per_c"]),
                  ("matrix_score", np.linalg.norm(answer["calibration_matrix"]-world["matrix"]), tolerances["matrix_frobenius"]),
                  ("prediction_score", np.sqrt(np.mean(np.sum((answer["prediction_accel_mps2"]-target)**2, axis=1))), tolerances["prediction_mps2"]))
        quality.update({key: float(np.clip(1-error/tolerance, 0, 1)) for key, error, tolerance in errors})
    science = .25*quality["bias_score"] + .25*quality["drift_score"] + .30*quality["matrix_score"] + .20*quality["prediction_score"]
    return {**quality, "science_score": science, "combined_score": science if supported else float(refusal),
            "mechanism_correct": bool(correct_model), "correct_refusal": bool(refusal),
            "fault_axis_correct": bool(correct_axis), "false_discovery": bool(claimed and not correct_model),
            "confidence_calibration_score": 1-(answer["confidence"]-float(correct_model or refusal))**2}


def _evaluate_world(spec, split, index, candidate):
    world, problem = _world(spec), public_problem(spec)
    campaign = _Campaign(world, problem)
    row = {"split": split, "world_index": index, "kind": world["kind"], "valid": False,
           "abstained": True, "reason": "", "measurements_used": 0,
           **{key: 0.0 for key in ("bias_score", "drift_score", "matrix_score", "prediction_score",
                                  "science_score", "combined_score", "confidence_calibration_score")},
           **{key: False for key in ("mechanism_correct", "correct_refusal", "fault_axis_correct", "false_discovery")}}
    try:
        if hasattr(candidate, "reset_session"):
            candidate.reset_session()
        answer = _validate(candidate(copy.deepcopy(problem), campaign), campaign)
        row.update(_score(world, answer, problem))
        row.update(valid=True, abstained=answer["abstain"])
    except Exception as exc:  # noqa: BLE001 - every malformed or over-budget candidate fails closed
        row["reason"] = f"{type(exc).__name__}: {exc}"
    row["measurements_used"] = campaign.calls
    return row


def _summary(rows):
    supported = [r for r in rows if r["kind"] == "supported"]
    ns, nu = len(supported), len(rows)-len(supported)
    claims = sum(r["valid"] and not r["abstained"] for r in rows)
    coverage = sum(r["valid"] and not r["abstained"] for r in supported)
    refusals = sum(r["correct_refusal"] for r in rows)
    false = sum(r["false_discovery"] for r in rows)
    mechanism = sum(r["matrix_score"] for r in supported)
    normalized = float(np.clip((sum(r["combined_score"] for r in rows)-nu)/max(1, ns), 0, 1)) * (refusals/nu if nu else 1)
    valid = float(all(r["valid"] for r in rows))
    result = {"combined_score": normalized if valid else 0.0, "valid": valid,
              "mechanism_score": mechanism/max(1, ns), "mechanism_quality_sum": mechanism, "mechanism_denominator": ns,
              "supported_correct_model_rate": sum(r["mechanism_correct"] for r in supported)/max(1, ns),
              "supported_correct_model_count": sum(r["mechanism_correct"] for r in supported),
              "false_discovery_rate": false/max(1, claims), "false_discovery_count": false, "false_discovery_denominator": claims,
              "correct_refusal_rate": refusals/max(1, nu), "correct_refusal_count": refusals, "correct_refusal_denominator": nu,
              "discovery_coverage": coverage/max(1, ns), "discovery_count": coverage, "discovery_denominator": ns,
              "fault_axis_accuracy": sum(r["fault_axis_correct"] for r in rows)/max(1, nu),
              "fault_axis_correct_count": sum(r["fault_axis_correct"] for r in rows), "fault_axis_denominator": nu,
              "attempted_discovery": float(claims > 0), "claim_count": claims, "world_count": len(rows),
              "mean_measurements_used": float(np.mean([r["measurements_used"] for r in rows])),
              "confidence_calibration_score": float(np.mean([r["confidence_calibration_score"] for r in rows]))}
    for key in ("science_score", "bias_score", "drift_score", "prediction_score"):
        result[key] = sum(r[key] for r in supported)/max(1, ns)
    return result


def evaluate(candidate):
    development = [_evaluate_world(s, "development", i, candidate) for i, s in enumerate(DEVELOPMENT_WORLDS)]
    heldout = [_evaluate_world(s, "heldout", i, candidate) for i, s in enumerate(HELDOUT_WORLDS)]
    dev, held = _summary(development), _summary(heldout)
    valid = min(dev["valid"], held["valid"])
    metrics = {"combined_score": dev["combined_score"] if valid else 0.0, "raw_score": dev["combined_score"] if valid else 0.0,
               "valid": valid, "robustness_score": held["combined_score"], "attempted_discovery": dev["attempted_discovery"],
               "per_instance": development+heldout}
    for split, summary in (("development", dev), ("heldout", held)):
        metrics.update({f"{split}_{key}": value for key, value in summary.items()})
    return metrics
