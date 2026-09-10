"""Frozen Glen-flow oracle: recover n, or refuse when the log-log slope is not a named power.

Citations that the oracle actually uses:
Glen (1955) doi:10.1098/rspa.1955.0066; Weertman (1957) doi:10.3189/S0022143000024709;
Paterson and Budd (1982) doi:10.1016/0165-232X(82)90010-6 for the Arrhenius thermal factor;
Goldsby and Kohlstedt (2001) doi:10.1029/2000JB900336 for grain-boundary sliding with n around 1.8.
"""
from __future__ import annotations

import math

import numpy as np

MEASURE_BUDGET = 12
TAU_BOUNDS = (20.0, 200.0)
TEMPERATURE_BOUNDS = (245.0, 265.0)
REFERENCE_TEMPERATURE = 255.0
SUPPORTED = {"glen", "newtonian", "gbs"}
GBS_EXPONENT_BOUNDS = (1.65, 2.05)

PUBLIC_PROBLEM = {
    "stress_bounds_kPa": list(TAU_BOUNDS),
    "temperature_bounds_K": list(TEMPERATURE_BOUNDS),
    "reference_temperature_K": REFERENCE_TEMPERATURE,
    "glen_exponent_bounds": [2.6, 3.6],
    "gbs_exponent_bounds": list(GBS_EXPONENT_BOUNDS),
    "measure_budget_calls": MEASURE_BUDGET,
    "family_names": ["glen", "newtonian", "gbs"],
    "rate_law": (
        "v = A * tau^n * exp(-activation_temperature*(1/T - 1/255)); "
        "Glen n is in [2.6,3.6]; Newtonian n=1; GBS (grain-boundary sliding) n is in [1.65,2.05]; "
        "A and activation_temperature are unknown"
    ),
    "measurement_model": (
        "measure(stress_kPa, temperature_K=255) returns ln speed plus Gaussian noise (sigma=0.03)"
    ),
    "abstain_when": (
        "basal sliding or a stress-dependent exponent curves the log-log slope, "
        "a plug is stress-independent, or n is outside the named families"
    ),
}


def public_problem():
    return dict(PUBLIC_PROBLEM)


def _thermal(spec, temperature):
    activation = float(spec.get("activation_temperature", 0.0))
    return math.exp(-activation * (1.0 / temperature - 1.0 / REFERENCE_TEMPERATURE))


def true_speed(spec, stress, temperature=REFERENCE_TEMPERATURE):
    stress = max(float(stress), 1e-6)
    kind = spec["kind"]
    thermal = _thermal(spec, temperature)
    if kind == "glen":
        return float(spec["A"]) * stress ** float(spec.get("n", 3.0)) * thermal
    if kind == "newtonian":
        return float(spec["A"]) * stress * thermal
    if kind == "gbs":
        return float(spec["A"]) * stress ** float(spec.get("n", 1.8)) * thermal
    if kind == "sliding":
        # Same Arrhenius factor on the Weertman sliding term as on the creep term.
        creep = float(spec["A"]) * stress ** float(spec.get("n", 3.0))
        sliding = float(spec["C"]) * stress
        return (creep + sliding) * thermal
    if kind == "plug":
        return float(spec["C"])
    if kind == "variable_n":
        n0 = float(spec["n0"])
        k = float(spec["k"])
        tau0 = float(spec.get("tau0", math.sqrt(TAU_BOUNDS[0] * TAU_BOUNDS[1])))
        exponent = n0 + k * math.log10(stress / tau0)
        return float(spec["A"]) * stress ** exponent * thermal
    raise ValueError("unknown family")


class _Lab:
    def __init__(self, spec):
        self.spec = spec
        self.used = 0
        self.violated = False

    def measure(self, stress_kPa, temperature_K=REFERENCE_TEMPERATURE):
        stress = float(stress_kPa)
        temperature = float(temperature_K)
        if not math.isfinite(temperature) or not TEMPERATURE_BOUNDS[0] <= temperature <= TEMPERATURE_BOUNDS[1]:
            raise ValueError("assay outside temperature_bounds_K")
        if not math.isfinite(stress):
            raise ValueError("stress must be finite")
        if not (TAU_BOUNDS[0] <= stress <= TAU_BOUNDS[1]):
            raise ValueError("assay outside stress_bounds_kPa")
        if self.used >= MEASURE_BUDGET:
            self.violated = True
            raise RuntimeError("measure budget exhausted")
        self.used += 1
        rng = np.random.default_rng((int(self.spec["seed"]), 19, self.used))
        return float(math.log(max(true_speed(self.spec, stress, temperature), 1e-30)) + 0.03 * rng.normal())


def _validate(submission):
    if not isinstance(submission, dict):
        raise ValueError("submission must be a mapping")
    abstain = submission.get("abstain", False)
    if not isinstance(abstain, bool):
        raise ValueError("abstain must be a boolean")
    confidence = float(submission.get("confidence", 0.0))
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must lie in [0, 1]")
    if abstain:
        return True, None, None, confidence, None, None
    family = submission.get("family")
    if family not in PUBLIC_PROBLEM["family_names"]:
        raise ValueError("family must be one of family_names")
    exponent = float(submission.get("n"))
    if not math.isfinite(exponent) or exponent <= 0.0:
        raise ValueError("n must be a positive finite number")
    log_a = float(submission.get("log_A"))
    activation = float(submission.get("activation_temperature"))
    if not math.isfinite(log_a) or not math.isfinite(activation) or activation < 0:
        raise ValueError("finite log_A and nonnegative activation_temperature are required")
    return False, family, exponent, confidence, log_a, activation


def _true_n(spec):
    kind = spec["kind"]
    if kind == "newtonian":
        return 1.0
    if kind == "gbs":
        return float(spec.get("n", 1.8))
    return float(spec.get("n", 3.0))


def _mechanism(spec, abstain, family, exponent, log_a, activation):
    if spec["kind"] not in SUPPORTED:
        return (1.0 if abstain else 0.0), bool(abstain), (not abstain)
    if abstain:
        return 0.0, False, False
    if family != spec["kind"]:
        return 0.0, False, False
    error = (abs(exponent - _true_n(spec)) / 0.1
             + abs(log_a - math.log(spec["A"])) / 0.3
             + abs(activation - spec["activation_temperature"]) / 1000.0) / 3.0
    return math.exp(-error), False, False


DEVELOPMENT_WORLDS = (
    {"kind": "glen", "seed": 71001, "A": 2.0e-7, "n": 2.65, "activation_temperature": 4000.0},
    {"kind": "glen", "seed": 71002, "A": 5.5e-7, "n": 3.45, "activation_temperature": 7200.0},
    {"kind": "newtonian", "seed": 71003, "A": 0.012, "activation_temperature": 5400.0},
    {"kind": "sliding", "seed": 72001, "A": 1.0e-5, "C": 0.05, "activation_temperature": 4800.0},
    {"kind": "sliding", "seed": 72002, "A": 3.0e-6, "C": 0.01, "activation_temperature": 7800.0},
    {"kind": "sliding", "seed": 72003, "A": 2.0e-7, "C": 3.6e-5, "activation_temperature": 6500.0},
    {"kind": "plug", "seed": 73001, "C": 0.45},
    {"kind": "plug", "seed": 73002, "C": 1.2},
    {"kind": "gbs", "seed": 74001, "A": 1.0e-5, "n": 1.72, "activation_temperature": 5100.0},
    {"kind": "gbs", "seed": 74002, "A": 4.0e-6, "n": 1.98, "activation_temperature": 8000.0},
    {"kind": "variable_n", "seed": 75001, "A": 1.5e-7, "n0": 3.0, "k": 0.20,
     "tau0": 63.245553203367585, "activation_temperature": 5600.0},
)
HELDOUT_WORLDS = (
    {"kind": "glen", "seed": 81001, "A": 3.4e-7, "n": 3.15, "activation_temperature": 6100.0},
    {"kind": "newtonian", "seed": 81002, "A": 0.008, "activation_temperature": 8600.0},
    {"kind": "sliding", "seed": 82001, "A": 1.0e-5, "C": 0.05, "activation_temperature": 4800.0},
    {"kind": "plug", "seed": 83001, "C": 0.7},
    {"kind": "sliding", "seed": 82002, "A": 3.0e-5, "C": 0.2, "activation_temperature": 5100.0},
    {"kind": "sliding", "seed": 82003, "A": 3.4e-7, "C": 5.1e-5, "activation_temperature": 7500.0},
    {"kind": "gbs", "seed": 84001, "A": 8.0e-6, "n": 1.85, "activation_temperature": 6400.0},
    {"kind": "variable_n", "seed": 85001, "A": 2.8e-7, "n0": 3.25, "k": 0.22,
     "tau0": 63.245553203367585, "activation_temperature": 6900.0},
)


def _evaluate_world(identify, spec, split, index):
    lab = _Lab(spec)
    base = {"split": split, "world_index": int(index), "kind": spec["kind"], "measure_calls": 0}
    try:
        submission = identify(public_problem(), lab.measure)
        abstain, family, exponent, confidence, log_a, activation = _validate(submission)
        if lab.violated:
            raise RuntimeError("measure budget exceeded")
        mech, refused, false = _mechanism(spec, abstain, family, exponent, log_a, activation)
        return {
            **base,
            "mechanism_score": round(float(mech), 6),
            "correct_refusal": refused,
            "false_discovery": false,
            "valid": True,
            "abstained": bool(abstain),
            "confidence": round(confidence, 6),
            "measure_calls": lab.used,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            **base,
            "mechanism_score": 0.0,
            "correct_refusal": False,
            "false_discovery": False,
            "valid": False,
            "reason": "%s: %s" % (type(exc).__name__, exc),
            "abstained": True,
            "confidence": 0.0,
            "measure_calls": lab.used,
        }


def _split_summary(records):
    supported = [row for row in records if row["kind"] in SUPPORTED]
    unsupported = [row for row in records if row["kind"] not in SUPPORTED]
    raw = float(np.mean([row["mechanism_score"] for row in records]))
    always_abstain = len(unsupported) / len(records)
    normalized = float(np.clip((raw - always_abstain) / (1.0 - always_abstain), 0.0, 1.0))
    return {
        "normalized_mechanism": round(normalized, 6),
        "signal_recovery_rate": float(np.mean([row["mechanism_score"] for row in supported])),
        "false_discovery_rate": float(np.mean([row["false_discovery"] for row in unsupported])),
        "correct_refusal_rate": float(np.mean([row["correct_refusal"] for row in unsupported])),
        "discovery_coverage": float(np.mean([not row["abstained"] for row in supported])),
        "valid_count": sum(bool(row["valid"]) for row in records),
        "world_count": len(records),
        "supported_count": len(supported),
        "unsupported_count": len(unsupported),
        "confidence_calibration": float(np.mean([
            (1.0 - (row["confidence"] - float(row["kind"] in SUPPORTED)) ** 2)
            if row["valid"] else 0.0
            for row in records
        ])),
    }


def _run(identify, worlds, split, reset_before_first=False):
    rows = []
    for index, spec in enumerate(worlds):
        if (index or reset_before_first) and hasattr(identify, "reset_session"):
            identify.reset_session()
        rows.append(_evaluate_world(identify, spec, split, index))
    return rows


def evaluate(identify_flow_law):
    development = _run(identify_flow_law, DEVELOPMENT_WORLDS, "development")
    heldout = _run(identify_flow_law, HELDOUT_WORLDS, "heldout", reset_before_first=True)
    dev = _split_summary(development)
    held = _split_summary(heldout)
    complete = dev["valid_count"] == dev["world_count"]
    return {
        "combined_score": dev["normalized_mechanism"] if complete else 0.0,
        "valid": float(complete),
        "feasibility_rate": dev["valid_count"] / dev["world_count"],
        "raw_score": dev["normalized_mechanism"],
        "development_mechanism_score": dev["normalized_mechanism"],
        "development_signal_recovery_rate": dev["signal_recovery_rate"],
        "development_false_discovery_rate": dev["false_discovery_rate"],
        "development_correct_refusal_rate": dev["correct_refusal_rate"],
        "development_discovery_coverage": dev["discovery_coverage"],
        "heldout_mechanism_score": held["normalized_mechanism"],
        "heldout_signal_recovery_rate": held["signal_recovery_rate"],
        "heldout_false_discovery_rate": held["false_discovery_rate"],
        "heldout_correct_refusal_rate": held["correct_refusal_rate"],
        "heldout_discovery_coverage": held["discovery_coverage"],
        "development_supported_count": dev["supported_count"],
        "development_unsupported_count": dev["unsupported_count"],
        "heldout_supported_count": held["supported_count"],
        "heldout_unsupported_count": held["unsupported_count"],
        "development_confidence_calibration": dev["confidence_calibration"],
        "heldout_confidence_calibration": held["confidence_calibration"],
        "per_instance": development + heldout,
    }
