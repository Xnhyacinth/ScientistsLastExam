"""Primal-only oracle for the frozen MIPLIB 2017 queens-30 binary program.

The official MIPLIB checker is a primal feasibility and objective check. Duals are not
part of the contract. This evaluator reparses the vendored MPS files and checks a dense
integer assignment with the published MIPLIB linear and integrality tolerances. It does
not fetch anything, does not read `.sol` files, and does not call a MIP solver.
"""
from __future__ import annotations

import hashlib
import gzip
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]
INSTANCE_DIR = TASK_DIR / "references" / "instances"

CONSTRAINT_ABS_TOL = 1e-6
CONSTRAINT_REL_TOL = 1e-5
INTEGRALITY_TOL = 1e-5

# Official proven optimum; source and both archive/content hashes are in anchors.json.
INSTANCES = ({
    "name": "queens-30",
    "mps_filename": "queens-30.mps.gz",
    "mps_sha256": "2f9f48263d7d7770bfdd391c7c47491ac70aa8ff575558063ad510b539680323",
    "n_variables": 900, "n_constraints": 960,
    "baseline_objective": 0.0, "reference_objective": -40.0,
},)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_mps(path: Path) -> dict[str, Any]:
    sense: dict[str, str] = {}
    objective: dict[str, float] = {}
    matrix: dict[str, dict[str, float]] = defaultdict(dict)
    rhs: dict[str, float] = {}
    lower: dict[str, float] = {}
    upper: dict[str, float] = {}
    integer_columns: set[str] = set()
    integer_section = False
    section = None
    objrow = None
    columns: list[str] = []
    seen: set[str] = set()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="iso-8859-1") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("*"):
                continue
            if line in {"RANGES", "OBJSENSE", "OBJNAME", "SOS", "QMATRIX", "QSECTION"}:
                raise ValueError("unsupported MPS section: " + line)
            if line == "ROWS":
                section = "ROWS"
                continue
            if line == "COLUMNS":
                section = "COLUMNS"
                continue
            if line == "RHS":
                section = "RHS"
                continue
            if line == "BOUNDS":
                section = "BOUNDS"
                continue
            if line == "ENDATA":
                break
            if line.startswith("NAME "):
                continue
            fields = line.split()
            if section == "ROWS":
                row_sense, name = fields[0], fields[1]
                if row_sense not in {"N", "L", "G", "E"}:
                    raise ValueError("unsupported row sense: " + row_sense)
                sense[name] = row_sense
                if row_sense == "N" and objrow is None:
                    objrow = name
                continue
            if section == "COLUMNS":
                if "MARKER" in line:
                    if "INTORG" in line:
                        integer_section = True
                    elif "INTEND" in line:
                        integer_section = False
                    else:
                        raise ValueError("unsupported integer marker")
                    continue
                column = fields[0]
                if integer_section:
                    integer_columns.add(column)
                if column not in seen:
                    seen.add(column)
                    columns.append(column)
                rest = fields[1:]
                for index in range(0, len(rest), 2):
                    row, value = rest[index], float(rest[index + 1])
                    if row == objrow:
                        objective[column] = objective.get(column, 0.0) + value
                    else:
                        matrix[row][column] = matrix[row].get(column, 0.0) + value
                continue
            if section == "RHS":
                rest = fields[1:]
                for index in range(0, len(rest), 2):
                    if rest[index] == objrow:
                        raise ValueError("objective RHS offsets are unsupported")
                    rhs[rest[index]] = float(rest[index + 1])
                continue
            if section == "BOUNDS":
                kind = fields[0]
                if kind in {"LO", "LI"}:
                    lower[fields[2]] = float(fields[3])
                elif kind in {"UP", "UI"}:
                    upper[fields[2]] = float(fields[3])
                elif kind == "BV":
                    lower[fields[2]], upper[fields[2]] = 0.0, 1.0
                    integer_columns.add(fields[2])
                elif kind == "FX":
                    lower[fields[2]] = upper[fields[2]] = float(fields[3])
                else:
                    raise ValueError("unsupported MPS bound: " + kind)
                if kind in {"LI", "UI"}:
                    integer_columns.add(fields[2])
    if not columns or set(columns) != integer_columns:
        raise ValueError("this task requires every MPS column to be integer")
    if any(not math.isfinite(value) for mapping in (objective, rhs, lower, upper) for value in mapping.values()):
        raise ValueError("nonfinite MPS value")
    constraint_names = [name for name, row_sense in sense.items() if row_sense != "N"]
    return {
        "columns": columns,
        "objective": [float(objective.get(column, 0.0)) for column in columns],
        "lower_bounds": [float(lower.get(column, 0.0)) for column in columns],
        "upper_bounds": [float(upper.get(column, float("inf"))) for column in columns],
        "row_senses": [sense[name] for name in constraint_names],
        "rhs": [float(rhs.get(name, 0.0)) for name in constraint_names],
        "matrix": [
            {column: coeff for column, coeff in matrix[name].items()}
            for name in constraint_names
        ],
    }


def _load_model(row: dict[str, Any]) -> dict[str, Any]:
    path = INSTANCE_DIR / row["mps_filename"]
    digest = _sha256(path)
    if digest != row["mps_sha256"]:
        raise RuntimeError("vendored MPS hash mismatch for %s" % row["name"])
    model = _parse_mps(path)
    if len(model["columns"]) != row["n_variables"]:
        raise RuntimeError("variable count mismatch for %s" % row["name"])
    if len(model["rhs"]) != row["n_constraints"]:
        raise RuntimeError("constraint count mismatch for %s" % row["name"])
    return model


def _csr(model: dict[str, Any]) -> tuple[list[int], list[int], list[float]]:
    row_ptr = [0]
    column_indices: list[int] = []
    coefficients: list[float] = []
    index = {name: position for position, name in enumerate(model["columns"])}
    for entries in model["matrix"]:
        for name in sorted(entries, key=lambda item: index[item]):
            column_indices.append(index[name])
            coefficients.append(float(entries[name]))
        row_ptr.append(len(column_indices))
    return row_ptr, column_indices, coefficients


def _public_instance(row: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    row_ptr, column_indices, coefficients = _csr(model)
    return {
        "name": row["name"],
        "sense": "minimize",
        "n_variables": row["n_variables"],
        "n_constraints": row["n_constraints"],
        "variable_names": list(model["columns"]),
        "objective": list(model["objective"]),
        "lower_bounds": list(model["lower_bounds"]),
        "upper_bounds": list(model["upper_bounds"]),
        "row_senses": list(model["row_senses"]),
        "rhs": list(model["rhs"]),
        "row_ptr": row_ptr,
        "column_indices": column_indices,
        "coefficients": coefficients,
        "mps_sha256": row["mps_sha256"],
        "constraint_abs_tol": CONSTRAINT_ABS_TOL,
        "constraint_rel_tol": CONSTRAINT_REL_TOL,
        "integrality_tol": INTEGRALITY_TOL,
    }


def _read_assignment(value: Any, n_variables: int) -> list[int]:
    if not isinstance(value, (list, tuple)) or len(value) != n_variables:
        raise ValueError("assignment must be a dense list of n_variables integers")
    assignment: list[int] = []
    for entry in value:
        if isinstance(entry, bool) or not isinstance(entry, int):
            raise ValueError("assignment entries must be integers; floats are rejected")
        assignment.append(int(entry))
    return assignment


def _max_violation(assignment: list[int], model: dict[str, Any]) -> float:
    index = {name: position for position, name in enumerate(model["columns"])}
    worst = 0.0
    for sense, rhs, entries in zip(model["row_senses"], model["rhs"], model["matrix"]):
        activity = 0.0
        for name, coeff in entries.items():
            activity += coeff * assignment[index[name]]
        if sense == "L":
            slack = activity - rhs
        elif sense == "G":
            slack = rhs - activity
        else:
            slack = abs(activity - rhs)
        scale = max(1.0, abs(rhs), abs(activity))
        allowed = max(CONSTRAINT_ABS_TOL, CONSTRAINT_REL_TOL * scale)
        worst = max(worst, slack - allowed)
    return worst


def _objective(assignment: list[int], model: dict[str, Any]) -> float:
    return sum(coeff * value for coeff, value in zip(model["objective"], assignment))


def _instance_score(row: dict[str, Any], objective: float) -> float:
    """Log-gap progress from the empty assignment to the proven MIPLIB optimum.

    ``clip01(log((b-r+1)/(z-r+1)) / log(b-r+1))`` with baseline ``b=0`` and
    reference ``r=-40``. Linear ``q/40`` made the first 36 queens almost free; the
    last queen is the expensive increment. The proven optimum still clips at one.
    """
    baseline = row["baseline_objective"]
    reference = row["reference_objective"]
    easy = baseline - reference + 1.0
    current = objective - reference + 1.0
    if easy <= 1.0:
        return 0.0
    if current <= 0.0:
        return 1.0
    progress = math.log(easy / current) / math.log(easy)
    return max(0.0, min(1.0, progress))


def evaluate(improve_primal):
    rows = []
    for index, row in enumerate(INSTANCES):
        model = _load_model(row)
        published = {
            "instance_index": index,
            "name": row["name"],
            "n_variables": row["n_variables"],
            "n_constraints": row["n_constraints"],
        }
        try:
            assignment = _read_assignment(
                improve_primal(_public_instance(row, model)), row["n_variables"])
            for value, lower, upper in zip(assignment, model["lower_bounds"], model["upper_bounds"]):
                if value < lower - INTEGRALITY_TOL:
                    raise ValueError("variable below its lower bound")
                if value > upper + INTEGRALITY_TOL:
                    raise ValueError("variable above its upper bound")
            violation = _max_violation(assignment, model)
            if violation > 0:
                raise ValueError("infeasible assignment; residual %s" % violation)
            objective = _objective(assignment, model)
            score = _instance_score(row, objective)
            published.update({
                "valid": True,
                "objective": float(objective),
                "instance_score": round(score, 6),
                "constraint_violation": 0.0,
            })
        except Exception as exc:  # noqa: BLE001
            published.update({
                "valid": False,
                "reason": "%s: %s" % (type(exc).__name__, exc),
                "objective": None,
                "instance_score": 0.0,
                "constraint_violation": None,
            })
        rows.append(published)

    valid = [row for row in rows if row["valid"]]
    combined = sum(row["instance_score"] for row in rows) / len(rows)
    return {
        "combined_score": float(combined),
        "valid": 1.0 if valid else 0.0,
        "feasibility_rate": len(valid) / len(rows),
        "raw_score": float(combined),
        "instances_with_a_feasible_assignment": len(valid),
        "per_instance": rows,
    }
