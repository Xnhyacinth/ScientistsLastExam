"""Deterministic finite-volume oracle for frozen scalar conservation-law panels."""
from __future__ import annotations

import importlib.util
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np


TASK_DIR = Path(__file__).resolve().parent.parent
CONTRACT_DIR = TASK_DIR / "frontier_eval" / "contracts"


def _load_contract(name, filename):
    spec = importlib.util.spec_from_file_location(name, CONTRACT_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load frozen semantic contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_CANONICALIZER = _load_contract(
    "adaptive_conservative_pde_method_canonicalizer",
    "method_canonicalizer_v1.py",
)
_EVIDENCE = _load_contract(
    "adaptive_conservative_pde_evidence_predicate",
    "evidence_predicate_v1.py",
)


class WorkBudgetExceeded(ValueError):
    pass


def _load_panel():
    path = CONTRACT_DIR / "evaluation_panel_v1.json"
    panel = json.loads(path.read_text(encoding="utf-8"))
    if panel.get("schema_version") != 1 or not isinstance(panel.get("worlds"), list):
        raise RuntimeError("invalid frozen evaluation panel")
    return panel


def _public_problem():
    return {
        "method_fields": list(_CANONICALIZER.METHOD_FIELDS),
        "discrete_choices": {
            "reconstruction": list(_CANONICALIZER.RECONSTRUCTIONS),
            "limiter": list(_CANONICALIZER.LIMITERS),
            "riemann_solver": list(_CANONICALIZER.RIEMANN_SOLVERS),
            "time_integrator": list(_CANONICALIZER.TIME_INTEGRATORS),
            "cells": list(_CANONICALIZER.CELL_COUNTS),
        },
        "continuous_bounds": {
            key: list(value) for key, value in _CANONICALIZER.BOUNDS.items()
        },
        "equations": ["constant-coefficient advection", "inviscid Burgers"],
        "boundary_conditions": ["periodic", "fixed far-field states"],
        "adaptivity": (
            "MUSCL slopes are locally reduced when a normalized curvature sensor exceeds "
            "sensor_threshold; shock_blend controls the reduction strength"
        ),
        "objectives": [
            "cell-average L1 accuracy",
            "discrete flux-balance conservation",
            "maximum-principle and total-variation stability",
            "cell-stage work",
        ],
        "work_unit_definition": "one finite-volume cell update in one Runge--Kutta stage",
        "max_work_units_per_case": 120000,
        "scope_warning": (
            "repository-visible frozen scalar-law benchmark; not evidence that a method "
            "generalizes to multidimensional or real application PDEs"
        ),
    }


def _normalize_method(value, _problem=None):
    return _CANONICALIZER.normalize_method(value)


def _canonical_method_id(method):
    return _CANONICALIZER.canonical_method_id(method)


def _canonical_payload(method):
    return _CANONICALIZER.canonical_payload(method)


def _weak_method():
    return {
        "reconstruction": "constant",
        "limiter": "minmod",
        "riemann_solver": "rusanov",
        "time_integrator": "euler",
        "cells": 32,
        "cfl": 0.45,
        "sensor_threshold": 0.5,
        "shock_blend": 1.0,
        "flux_dissipation": 1.15,
    }


def _reference_method():
    return {
        "reconstruction": "muscl",
        "limiter": "mc",
        "riemann_solver": "godunov",
        "time_integrator": "ssprk2",
        "cells": 96,
        "cfl": 0.72,
        "sensor_threshold": 0.28,
        "shock_blend": 0.82,
        "flux_dissipation": 1.0,
    }


def _initial_value(x, initial):
    kind = initial["kind"]
    if kind == "sine":
        angle = 2.0 * np.pi * initial["frequency"] * (x - initial["phase"])
        return initial["offset"] + initial["amplitude"] * np.sin(angle)
    if kind == "multisine":
        angle = 2.0 * np.pi * (x - initial["phase"])
        shape = 0.65 * np.sin(angle) + 0.25 * np.sin(3.0 * angle)
        shape += 0.10 * np.cos(5.0 * angle)
        return initial["offset"] + initial["amplitude"] * shape
    if kind == "gaussian":
        distance = np.minimum(
            np.abs(x - initial["center"]), 1.0 - np.abs(x - initial["center"])
        )
        pulse = np.exp(-0.5 * (distance / initial["width"]) ** 2)
        return initial["low"] + (initial["high"] - initial["low"]) * pulse
    if kind == "top_hat":
        inside = (x >= initial["left"]) & (x < initial["right"])
        return np.where(inside, initial["high"], initial["low"])
    if kind == "riemann":
        return np.where(x < initial["location"], initial["left"], initial["right"])
    raise RuntimeError("unknown frozen initial condition")


def _exact_value(x, world, time):
    initial = world["initial"]
    if world["equation"] == "advection":
        foot = np.mod(x - world["speed"] * time, 1.0)
        return _initial_value(foot, initial)
    left = float(initial["left"])
    right = float(initial["right"])
    location = float(initial["location"])
    if time == 0.0:
        return _initial_value(x, initial)
    if left > right:
        shock = location + 0.5 * (left + right) * time
        return np.where(x < shock, left, right)
    similarity = (x - location) / time
    return np.where(similarity <= left, left, np.where(similarity >= right, right, similarity))


def _cell_averages(world, cells, time):
    quadrature_points = 96
    offsets = (np.arange(quadrature_points, dtype=float) + 0.5) / quadrature_points
    points = (np.arange(cells, dtype=float)[:, None] + offsets[None, :]) / cells
    return np.mean(_exact_value(points, world, time), axis=1)


def _boundary_values(world):
    initial = world["initial"]
    return float(initial["left"]), float(initial["right"])


def _minmod(*values):
    arrays = [np.asarray(value, dtype=float) for value in values]
    positive = np.logical_and.reduce([value > 0.0 for value in arrays])
    negative = np.logical_and.reduce([value < 0.0 for value in arrays])
    magnitude = np.minimum.reduce([np.abs(value) for value in arrays])
    return np.where(positive, magnitude, np.where(negative, -magnitude, 0.0))


def _limited_slope(state, method, world):
    if method["reconstruction"] == "constant":
        return np.zeros_like(state)
    if world["boundary"] == "periodic":
        backward = state - np.roll(state, 1)
        forward = np.roll(state, -1) - state
    else:
        left, right = _boundary_values(world)
        extended = np.concatenate(([left], state, [right]))
        backward = state - extended[:-2]
        forward = extended[2:] - state

    limiter = method["limiter"]
    if limiter == "minmod":
        slope = _minmod(backward, forward)
    elif limiter == "mc":
        slope = _minmod(0.5 * (backward + forward), 2.0 * backward, 2.0 * forward)
    elif limiter == "van_leer":
        denominator = backward + forward
        same_sign = backward * forward > 0.0
        slope = np.where(
            same_sign,
            2.0 * backward * forward / np.where(np.abs(denominator) > 1.0e-15, denominator, 1.0),
            0.0,
        )
    else:
        first = _minmod(2.0 * backward, forward)
        second = _minmod(backward, 2.0 * forward)
        slope = np.where(np.abs(first) >= np.abs(second), first, second)

    sensor = np.abs(forward - backward) / (
        np.abs(forward) + np.abs(backward) + 1.0e-14
    )
    threshold = method["sensor_threshold"]
    activation = np.maximum(sensor - threshold, 0.0) / (1.0 - threshold)
    activation = np.minimum(activation, 1.0)
    return slope * (1.0 - method["shock_blend"] * activation)


def _physical_flux(value, world):
    if world["equation"] == "advection":
        return world["speed"] * value
    return 0.5 * value * value


def _numerical_flux(left, right, method, world):
    if method["riemann_solver"] == "rusanov":
        if world["equation"] == "advection":
            speed = abs(float(world["speed"]))
        else:
            speed = np.maximum(np.abs(left), np.abs(right))
        speed = method["flux_dissipation"] * speed
        return 0.5 * (_physical_flux(left, world) + _physical_flux(right, world)) - (
            0.5 * speed * (right - left)
        )
    if world["equation"] == "advection":
        return world["speed"] * (left if world["speed"] >= 0.0 else right)

    rarefaction = left <= right
    rare_flux = np.where(
        left >= 0.0,
        0.5 * left * left,
        np.where(right <= 0.0, 0.5 * right * right, 0.0),
    )
    shock_speed = 0.5 * (left + right)
    shock_flux = np.where(shock_speed >= 0.0, 0.5 * left * left, 0.5 * right * right)
    return np.where(rarefaction, rare_flux, shock_flux)


def _residual(state, method, world):
    cells = len(state)
    dx = 1.0 / cells
    slope = _limited_slope(state, method, world)
    if world["boundary"] == "periodic":
        left = state + 0.5 * slope
        right = np.roll(state, -1) - 0.5 * np.roll(slope, -1)
        face_flux = _numerical_flux(left, right, method, world)
        residual = -(face_flux - np.roll(face_flux, 1)) / dx
        return residual, 0.0

    boundary_left, boundary_right = _boundary_values(world)
    face_left = np.empty(cells + 1, dtype=float)
    face_right = np.empty(cells + 1, dtype=float)
    face_left[0] = boundary_left
    face_right[0] = state[0] - 0.5 * slope[0]
    face_left[1:cells] = state[:-1] + 0.5 * slope[:-1]
    face_right[1:cells] = state[1:] - 0.5 * slope[1:]
    face_left[cells] = state[-1] + 0.5 * slope[-1]
    face_right[cells] = boundary_right
    face_flux = _numerical_flux(face_left, face_right, method, world)
    residual = -(face_flux[1:] - face_flux[:-1]) / dx
    return residual, float(face_flux[-1] - face_flux[0])


def _stage_count(method):
    return {"euler": 1, "ssprk2": 2, "ssprk3": 3}[method["time_integrator"]]


def _speed_bound(world):
    if world["equation"] == "advection":
        return abs(float(world["speed"]))
    initial = world["initial"]
    return max(abs(float(initial["left"])), abs(float(initial["right"])), 1.0e-12)


def _estimated_work(method, world):
    steps = math.ceil(
        world["final_time"] * _speed_bound(world) * method["cells"] / method["cfl"]
    ) + 2
    return steps * method["cells"] * _stage_count(method)


def _advance(state, dt, method, world):
    integrator = method["time_integrator"]
    first, flux_first = _residual(state, method, world)
    if integrator == "euler":
        return state + dt * first, dt * flux_first, 1
    stage_one = state + dt * first
    second, flux_second = _residual(stage_one, method, world)
    if integrator == "ssprk2":
        updated = 0.5 * state + 0.5 * (stage_one + dt * second)
        return updated, 0.5 * dt * (flux_first + flux_second), 2
    stage_two = 0.75 * state + 0.25 * (stage_one + dt * second)
    third, flux_third = _residual(stage_two, method, world)
    updated = (state / 3.0) + (2.0 / 3.0) * (stage_two + dt * third)
    flux_integral = dt * (flux_first / 6.0 + flux_second / 6.0 + 2.0 * flux_third / 3.0)
    return updated, flux_integral, 3


def _total_variation(state, world):
    if world["boundary"] == "periodic":
        return float(np.sum(np.abs(np.roll(state, -1) - state)))
    left, right = _boundary_values(world)
    return float(np.sum(np.abs(np.diff(np.concatenate(([left], state, [right]))))))


def _physical_bounds(world):
    initial = world["initial"]
    if initial["kind"] == "sine":
        return initial["offset"] - initial["amplitude"], initial["offset"] + initial["amplitude"]
    if initial["kind"] in {"gaussian", "top_hat"}:
        return float(initial["low"]), float(initial["high"])
    if initial["kind"] == "riemann":
        return min(initial["left"], initial["right"]), max(initial["left"], initial["right"])
    dense = np.arange(16384, dtype=float) / 16384.0
    values = _initial_value(dense, initial)
    return float(np.min(values)), float(np.max(values))


def _run_world(method, world):
    predicted_work = _estimated_work(method, world)
    if predicted_work > int(world["max_work_units"]):
        raise WorkBudgetExceeded("declared method exceeds the frozen per-case work budget")
    cells = method["cells"]
    state = _cell_averages(world, cells, 0.0)
    initial_state = state.copy()
    mass_initial = float(np.mean(state))
    initial_tv = _total_variation(state, world)
    elapsed = 0.0
    boundary_flux_integral = 0.0
    work_units = 0
    while elapsed < world["final_time"] - 1.0e-15:
        max_speed = _speed_bound(world)
        if world["equation"] == "burgers":
            max_speed = max(max_speed, float(np.max(np.abs(state))))
        dt = method["cfl"] / (cells * max(max_speed, 1.0e-12))
        dt = min(dt, world["final_time"] - elapsed)
        state, flux_integral, stages = _advance(state, dt, method, world)
        if not np.all(np.isfinite(state)):
            raise ValueError("nonfinite finite-volume state")
        elapsed += dt
        boundary_flux_integral += flux_integral
        work_units += stages * cells
        if work_units > int(world["max_work_units"]):
            raise WorkBudgetExceeded("realized method work exceeds the frozen per-case budget")

    exact = _cell_averages(world, cells, world["final_time"])
    l1_error = float(np.mean(np.abs(state - exact)))
    lower, upper = _physical_bounds(world)
    scale = max(upper - lower, 1.0e-12)
    overshoot = max(float(np.max(state)) - upper, lower - float(np.min(state)), 0.0)
    final_tv = _total_variation(state, world)
    tv_growth = max(final_tv - initial_tv, 0.0) / max(initial_tv, 1.0e-12)
    if world["boundary"] == "periodic":
        conservation_error = abs(float(np.mean(state)) - mass_initial)
    else:
        conservation_error = abs(
            float(np.mean(state)) - mass_initial + boundary_flux_integral
        )
    accuracy = math.exp(-l1_error / float(world["accuracy_scale"]))
    stability = math.exp(-18.0 * overshoot / scale - 4.0 * tv_growth)
    conservation = math.exp(-conservation_error / 1.0e-11)
    cost = 1.0 / (1.0 + work_units / float(world["max_work_units"]))
    utility = 0.72 * accuracy + 0.14 * stability + 0.10 * conservation + 0.04 * cost
    initial_kind = world["initial"]["kind"]
    regime = "smooth" if initial_kind in {"sine", "multisine", "gaussian"} else "shock"
    return {
        "id": world["id"],
        "split": world["split"],
        "regime": regime,
        "l1_error": l1_error,
        "accuracy_score": accuracy,
        "stability_score": stability,
        "conservation_score": conservation,
        "conservation_error": conservation_error,
        "overshoot": overshoot,
        "tv_growth": tv_growth,
        "work_units": work_units,
        "cost_score": cost,
        "raw_utility": utility,
    }


def _mean(rows, key):
    if not rows:
        return 0.0
    return float(sum(float(row[key]) for row in rows) / len(rows))


def _aggregate(rows):
    smooth = [row for row in rows if row["regime"] == "smooth"]
    shock = [row for row in rows if row["regime"] == "shock"]
    return {
        "raw_utility": _mean(rows, "raw_utility"),
        "accuracy_score": _mean(rows, "accuracy_score"),
        "smooth_accuracy_score": _mean(smooth, "accuracy_score"),
        "shock_accuracy_score": _mean(shock, "accuracy_score"),
        "stability_score": _mean(rows, "stability_score"),
        "conservation_score": _mean(rows, "conservation_score"),
        "max_conservation_error": max(
            (float(row["conservation_error"]) for row in rows), default=math.inf
        ),
        "mean_work_units": _mean(rows, "work_units"),
        "cost_score": _mean(rows, "cost_score"),
    }


def _evaluate_fixed(method):
    normalized = _normalize_method(method)
    rows = [_run_world(normalized, world) for world in _load_panel()["worlds"]]
    development = [row for row in rows if row["split"] == "development"]
    heldout = [row for row in rows if row["split"] == "heldout"]
    return _aggregate(development), _aggregate(heldout)


@lru_cache(maxsize=1)
def _anchors():
    weak, _ = _evaluate_fixed(_weak_method())
    reference, _ = _evaluate_fixed(_reference_method())
    if reference["raw_utility"] <= weak["raw_utility"]:
        raise RuntimeError("invalid task anchors: reference must improve the weak method")
    return weak["raw_utility"], reference["raw_utility"]


def _normalized(value, weak, reference):
    if reference <= weak:
        raise ValueError("reference anchor must exceed weak anchor")
    return max((float(value) - float(weak)) / (float(reference) - float(weak)), 0.0)


def _invalid_metrics(errors, call_count):
    weak, reference = _anchors()
    return {
        "combined_score": 0.0,
        "valid": 0.0,
        "development_raw_utility": 0.0,
        "heldout_raw_utility": 0.0,
        "baseline_utility": weak,
        "reference_utility": reference,
        "candidate_world_call_count": call_count,
        "evaluation_error_count": len(errors),
        "evaluation_errors": errors,
        "frontier_records": [],
    }


def evaluate(candidate):
    panel = _load_panel()
    expected_payload = None
    method = None
    rows = []
    errors = []
    call_count = 0
    for index, world in enumerate(panel["worlds"]):
        try:
            if index and hasattr(candidate, "reset_session"):
                candidate.reset_session()
            call_count += 1
            proposal = candidate(_public_problem())
            normalized = _normalize_method(proposal)
            payload = _canonical_payload(normalized)
            if expected_payload is None:
                expected_payload = payload
                method = normalized
            elif payload != expected_payload:
                raise ValueError("candidate must return one deterministic method for every world")
            rows.append(_run_world(normalized, world))
        except Exception as exc:  # noqa: BLE001 - candidate and method failures fail closed
            errors.append({"world_id": world["id"], "error": type(exc).__name__})

    if errors or method is None or len(rows) != len(panel["worlds"]):
        return _invalid_metrics(errors, call_count)

    development_rows = [row for row in rows if row["split"] == "development"]
    heldout_rows = [row for row in rows if row["split"] == "heldout"]
    development = _aggregate(development_rows)
    heldout = _aggregate(heldout_rows)
    weak, reference = _anchors()
    score = _normalized(development["raw_utility"], weak, reference)
    canonical_id = _canonical_method_id(method)
    record = _EVIDENCE.make_frontier_record(
        canonical_id,
        development["raw_utility"],
        development["max_conservation_error"],
        True,
    )
    frontier_records = [] if record is None else [record]
    valid = 1.0 if record is not None else 0.0
    return {
        "combined_score": score if valid else 0.0,
        "valid": valid,
        "development_raw_utility": development["raw_utility"],
        "development_accuracy_score": development["accuracy_score"],
        "development_smooth_accuracy_score": development["smooth_accuracy_score"],
        "development_shock_accuracy_score": development["shock_accuracy_score"],
        "development_stability_score": development["stability_score"],
        "development_conservation_score": development["conservation_score"],
        "development_max_conservation_error": development["max_conservation_error"],
        "development_mean_work_units": development["mean_work_units"],
        "development_cost_score": development["cost_score"],
        "heldout_raw_utility": heldout["raw_utility"],
        "heldout_accuracy_score": heldout["accuracy_score"],
        "heldout_smooth_accuracy_score": heldout["smooth_accuracy_score"],
        "heldout_shock_accuracy_score": heldout["shock_accuracy_score"],
        "heldout_stability_score": heldout["stability_score"],
        "heldout_conservation_score": heldout["conservation_score"],
        "heldout_max_conservation_error": heldout["max_conservation_error"],
        "heldout_mean_work_units": heldout["mean_work_units"],
        "heldout_cost_score": heldout["cost_score"],
        "baseline_utility": weak,
        "reference_utility": reference,
        "candidate_world_call_count": call_count,
        "evaluation_error_count": 0,
        "method_canonical_id": canonical_id,
        "per_world": rows,
        "frontier_records": frontier_records,
    }
