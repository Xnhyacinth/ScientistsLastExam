"""Exact oracle for the unregistered MIPLIBPrimalPolicy candidate task.

The two frozen MIPLIB instances use integral coefficients and only integer
variables.  Candidate assignments are therefore checked with integer
arithmetic, which is stricter than the official floating-tolerance checker.
The four shipped anchor solutions were also replayed with the patched official
checker at the frozen 1e-6 linear and 1e-5 integrality tolerances.
"""
from __future__ import annotations

import gzip
import hashlib
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

TASK_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(__file__).resolve().parent / "data"
PRIVATE_DATA_DIR = Path(__file__).resolve().parent / "private_data"

OFFICIAL_LINEAR_TOLERANCE = "1e-6"
OFFICIAL_INTEGRALITY_TOLERANCE = "1e-5"

INSTANCES = (
    {
        "name": "comp12-2idx",
        "mps_sha256": "5c3b597c3d999d4298dfb52fd6589838445752a59590b10c0cc20744453643ce",
        "baseline_sha256": "907c6bec3a9c4562ab78c8a29d58b5557692eac31a277d0a44fdc59ba76af4a9",
        "reference_sha256": "ad5dec0bb00722886c3f89f93e28966140e355003b877eb3abbeb0e265ba09fe",
        "baseline_objective": 391,
        "reference_objective": 277,
        "num_variables": 11863,
        "num_constraints": 16803,
    },
    {
        "name": "scpk4",
        "mps_sha256": "093059e2d4caa1a724dd429342ee301517ac00e4163872e3eb9f310228a7fe9d",
        "baseline_sha256": "2ae902a9345102fc9de070a67190ee83ee3f73d371ad4249666e9b3071ba4594",
        "reference_sha256": "19659d4a50d17838c5968258e657eabf2bb888ed03b0f1f9c9fbd8cef4a00c4e",
        "baseline_objective": 327,
        "reference_objective": 318,
        "num_variables": 100000,
        "num_constraints": 2000,
    },
)
INSTANCE_BY_NAME = {row["name"]: row for row in INSTANCES}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _integer_text(value: str) -> int:
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("MPS number is not decimal") from exc
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError("frozen MPS and solution values must be integral")
    return int(number)


def _pairs(fields: list[str]) -> list[tuple[str, int]]:
    if not fields or len(fields) % 2:
        raise ValueError("MPS row/value fields are malformed")
    return [
        (fields[index], _integer_text(fields[index + 1]))
        for index in range(0, len(fields), 2)
    ]


def _parse_mps(path: Path) -> dict[str, Any]:
    section = None
    objective_row = None
    row_names: list[str] = []
    row_types: list[str] = []
    row_index: dict[str, int] = {}
    row_entries: list[list[tuple[int, int]]] = []
    rhs: list[int] = []
    column_names: list[str] = []
    column_index: dict[str, int] = {}
    objective: list[int] = []
    lower_bounds: list[int] = []
    upper_bounds: list[int | None] = []
    integer_columns: list[bool] = []
    integer_mode = False
    rhs_name = None
    bounds_name = None
    saw_endata = False

    with gzip.open(path, "rt", encoding="iso-8859-1", newline=None) as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if not line or line.startswith("*"):
                continue
            fields = line.split()
            keyword = fields[0]
            if keyword == "NAME":
                if section is not None:
                    raise ValueError("duplicate or misplaced MPS NAME section")
                section = "NAME"
                continue
            if keyword in {"ROWS", "COLUMNS", "RHS", "BOUNDS"}:
                section = keyword
                continue
            if keyword == "ENDATA":
                saw_endata = True
                break
            if keyword in {"OBJSENSE", "OBJNAME", "RANGES", "SOS"}:
                raise ValueError("unsupported section in frozen MPS: " + keyword)

            if section == "ROWS":
                if len(fields) != 2 or fields[0] not in {"N", "L", "G", "E"}:
                    raise ValueError("malformed MPS row")
                row_type, name = fields
                if row_type == "N":
                    if objective_row is not None:
                        raise ValueError("frozen MPS must have one objective row")
                    objective_row = name
                else:
                    if name in row_index:
                        raise ValueError("duplicate MPS row")
                    row_index[name] = len(row_names)
                    row_names.append(name)
                    row_types.append(row_type)
                    row_entries.append([])
                    rhs.append(0)
                continue

            if section == "COLUMNS":
                if len(fields) == 3 and fields[1].strip("'") == "MARKER":
                    marker = fields[2].strip("'")
                    if marker == "INTORG":
                        if integer_mode:
                            raise ValueError("nested MPS integer marker")
                        integer_mode = True
                    elif marker == "INTEND":
                        if not integer_mode:
                            raise ValueError("unmatched MPS integer marker")
                        integer_mode = False
                    else:
                        raise ValueError("unknown MPS marker")
                    continue
                if objective_row is None:
                    raise ValueError("MPS columns precede objective row")
                name = fields[0]
                if name not in column_index:
                    column_index[name] = len(column_names)
                    column_names.append(name)
                    objective.append(0)
                    lower_bounds.append(0)
                    upper_bounds.append(None)
                    integer_columns.append(integer_mode)
                index = column_index[name]
                if integer_mode:
                    integer_columns[index] = True
                for row_name, coefficient in _pairs(fields[1:]):
                    if row_name == objective_row:
                        objective[index] += coefficient
                    elif row_name in row_index:
                        row_entries[row_index[row_name]].append(
                            (index, coefficient)
                        )
                    else:
                        raise ValueError("MPS column names an unknown row")
                continue

            if section == "RHS":
                name = fields[0]
                if rhs_name is None:
                    rhs_name = name
                elif name != rhs_name:
                    raise ValueError("multiple MPS RHS vectors are unsupported")
                for row_name, value in _pairs(fields[1:]):
                    if row_name == objective_row:
                        if value:
                            raise ValueError("objective offsets are absent by contract")
                    elif row_name in row_index:
                        rhs[row_index[row_name]] = value
                    else:
                        raise ValueError("MPS RHS names an unknown row")
                continue

            if section == "BOUNDS":
                if len(fields) not in {3, 4}:
                    raise ValueError("malformed MPS bound")
                bound_type, name, variable = fields[:3]
                if bounds_name is None:
                    bounds_name = name
                elif name != bounds_name:
                    raise ValueError("multiple MPS bound vectors are unsupported")
                if variable not in column_index:
                    raise ValueError("MPS bound names an unknown column")
                index = column_index[variable]
                value = _integer_text(fields[3]) if len(fields) == 4 else None
                if bound_type == "BV" and value is None:
                    lower_bounds[index], upper_bounds[index] = 0, 1
                    integer_columns[index] = True
                elif bound_type in {"UP", "UI"} and value is not None:
                    upper_bounds[index] = value
                    integer_columns[index] = integer_columns[index] or bound_type == "UI"
                elif bound_type in {"LO", "LI"} and value is not None:
                    lower_bounds[index] = value
                    integer_columns[index] = integer_columns[index] or bound_type == "LI"
                elif bound_type == "FX" and value is not None:
                    lower_bounds[index] = value
                    upper_bounds[index] = value
                else:
                    raise ValueError("unsupported bound type in frozen MPS")
                continue

            raise ValueError("MPS data appeared outside a supported section")

    if not saw_endata or integer_mode or objective_row is None:
        raise ValueError("frozen MPS is incomplete")
    if not column_names or not row_names:
        raise ValueError("frozen MPS has no variables or constraints")
    if not all(integer_columns) or any(bound is None for bound in upper_bounds):
        raise ValueError("frozen MPS must contain bounded integer variables only")

    row_ptr = [0]
    column_indices: list[int] = []
    coefficients: list[int] = []
    for entries in row_entries:
        for column, coefficient in entries:
            column_indices.append(column)
            coefficients.append(coefficient)
        row_ptr.append(len(column_indices))
    suffix = ".mps.gz"
    if not path.name.endswith(suffix):
        raise ValueError("frozen model path lacks the MPS gzip suffix")
    return {
        "name": path.name[:-len(suffix)],
        "sense": "minimize",
        "num_variables": len(column_names),
        "num_constraints": len(row_names),
        "variable_names": tuple(column_names),
        "name_to_column": column_index,
        "objective": np.asarray(objective, dtype=np.int64),
        "lower_bounds": np.asarray(lower_bounds, dtype=np.int64),
        "upper_bounds": np.asarray(upper_bounds, dtype=np.int64),
        "row_senses": tuple(row_types),
        "rhs": np.asarray(rhs, dtype=np.int64),
        "row_ptr": np.asarray(row_ptr, dtype=np.int64),
        "column_indices": np.asarray(column_indices, dtype=np.int64),
        "coefficients": np.asarray(coefficients, dtype=np.int64),
    }


@lru_cache(maxsize=len(INSTANCES))
def _load_model(name: str) -> dict[str, Any]:
    if name not in INSTANCE_BY_NAME:
        raise KeyError("unknown frozen MIPLIB instance")
    frozen = INSTANCE_BY_NAME[name]
    path = DATA_DIR / (name + ".mps.gz")
    if _sha256(path) != frozen["mps_sha256"]:
        raise ValueError("frozen MPS hash differs")
    model = _parse_mps(path)
    if (
        model["name"] != name
        or model["num_variables"] != frozen["num_variables"]
        or model["num_constraints"] != frozen["num_constraints"]
    ):
        raise ValueError("frozen MPS dimensions differ")
    return model


def _solution_values(path: Path, model: dict[str, Any]) -> tuple[np.ndarray, int]:
    assignment = np.zeros(model["num_variables"], dtype=np.int64)
    seen = set()
    claimed_objective = None
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for raw_line in stream:
            fields = raw_line.split()
            if not fields:
                continue
            if len(fields) != 2:
                raise ValueError("frozen SOL line is malformed")
            name, raw_value = fields
            value = _integer_text(raw_value)
            if name == "=obj=":
                if claimed_objective is not None:
                    raise ValueError("frozen SOL repeats its objective")
                claimed_objective = value
                continue
            if name not in model["name_to_column"] or name in seen:
                raise ValueError("frozen SOL has unknown or duplicate variable")
            seen.add(name)
            assignment[model["name_to_column"][name]] = value
    if claimed_objective is None:
        raise ValueError("frozen SOL lacks an objective")
    return assignment, claimed_objective


@lru_cache(maxsize=2 * len(INSTANCES))
def _cached_frozen_assignment(name: str, kind: str) -> tuple[int, ...]:
    if kind not in {"baseline", "reference"}:
        raise ValueError("frozen assignment kind must be baseline or reference")
    frozen = INSTANCE_BY_NAME[name]
    path = PRIVATE_DATA_DIR / (name + "-" + kind + ".sol.gz")
    if _sha256(path) != frozen[kind + "_sha256"]:
        raise ValueError("frozen SOL hash differs")
    assignment, claimed = _solution_values(path, _load_model(name))
    objective = _check_assignment(_load_model(name), assignment)
    if claimed != objective or objective != frozen[kind + "_objective"]:
        raise ValueError("frozen SOL objective differs")
    return tuple(int(value) for value in assignment)


def _load_frozen_assignment(name: str, kind: str) -> np.ndarray:
    return np.asarray(_cached_frozen_assignment(name, kind), dtype=np.int64)


def _strict_assignment(raw: Any, size: int) -> np.ndarray:
    if isinstance(raw, (str, bytes, Mapping)) or not isinstance(
        raw, (Sequence, np.ndarray)
    ):
        raise TypeError("assignment must be a dense integer sequence")
    if isinstance(raw, np.ndarray) and raw.ndim != 1:
        raise ValueError("assignment must be one dimensional")
    if len(raw) != size:
        raise ValueError("assignment length differs from the model")
    values = np.empty(size, dtype=np.int64)
    for index, value in enumerate(raw):
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise TypeError("assignment values must be exact integers")
        try:
            values[index] = int(value)
        except OverflowError as exc:
            raise ValueError("assignment integer exceeds the supported range") from exc
    return values


def _check_assignment(model: dict[str, Any], raw: Any) -> int:
    values = _strict_assignment(raw, model["num_variables"])
    if np.any(values < model["lower_bounds"]) or np.any(
        values > model["upper_bounds"]
    ):
        raise ValueError("assignment violates a variable bound")

    row_ptr = model["row_ptr"]
    columns = model["column_indices"]
    coefficients = model["coefficients"]
    for row, sense in enumerate(model["row_senses"]):
        activity = 0
        for position in range(int(row_ptr[row]), int(row_ptr[row + 1])):
            activity += int(coefficients[position]) * int(
                values[int(columns[position])]
            )
        side = int(model["rhs"][row])
        if (
            (sense == "L" and activity > side)
            or (sense == "G" and activity < side)
            or (sense == "E" and activity != side)
        ):
            raise ValueError("assignment violates a linear constraint")

    objective = 0
    for coefficient, value in zip(model["objective"], values):
        objective += int(coefficient) * int(value)
    return objective


def _problem_payload(model: dict[str, Any], incumbent: np.ndarray) -> dict[str, Any]:
    return {
        "name": model["name"],
        "sense": model["sense"],
        "num_variables": model["num_variables"],
        "num_constraints": model["num_constraints"],
        "variable_names": model["variable_names"],
        "objective": model["objective"],
        "lower_bounds": model["lower_bounds"],
        "upper_bounds": model["upper_bounds"],
        "row_senses": model["row_senses"],
        "rhs": model["rhs"],
        "row_ptr": model["row_ptr"],
        "column_indices": model["column_indices"],
        "coefficients": model["coefficients"],
        "incumbent": incumbent,
    }


def _normalized(objective: int, baseline: int, reference: int) -> float:
    denominator = baseline - reference
    if denominator <= 0:
        raise ValueError("minimization anchors are not ordered")
    return float(max(0.0, (baseline - objective) / denominator))


def _score_instance(frozen: dict[str, Any], improve_primal) -> dict[str, Any]:
    name = frozen["name"]
    model = _load_model(name)
    incumbent = _load_frozen_assignment(name, "baseline")
    published = {
        "name": name,
        "baseline_objective": frozen["baseline_objective"],
        "frozen_reference_objective": frozen["reference_objective"],
    }
    try:
        proposed = improve_primal(_problem_payload(model, incumbent.copy()))
        objective = _check_assignment(model, proposed)
        score = _normalized(
            objective,
            frozen["baseline_objective"],
            frozen["reference_objective"],
        )
        published.update({
            "valid": True,
            "objective": objective,
            "instance_score": score,
            "beats_frozen_reference": objective < frozen["reference_objective"],
        })
    except Exception as exc:  # noqa: BLE001 - one bad instance scores zero
        published.update({
            "valid": False,
            "reason": f"{type(exc).__name__}: {exc}",
            "objective": None,
            "instance_score": 0.0,
            "beats_frozen_reference": False,
        })
    return published


def evaluate(improve_primal) -> dict[str, Any]:
    rows = []
    for index, frozen in enumerate(INSTANCES):
        if index and hasattr(improve_primal, "reset_session"):
            improve_primal.reset_session()
        rows.append(_score_instance(frozen, improve_primal))
    valid_count = sum(row["valid"] for row in rows)
    combined = sum(row["instance_score"] for row in rows) / len(rows)
    return {
        "combined_score": float(combined),
        "valid": 1.0 if valid_count == len(rows) else 0.0,
        "feasibility_rate": valid_count / len(rows),
        "raw_score": float(combined),
        "instances_beating_frozen_reference": sum(
            row["beats_frozen_reference"] for row in rows
        ),
        "per_instance": rows,
    }
