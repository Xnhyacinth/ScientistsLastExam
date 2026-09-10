# MiplibPrimalIncumbent — improve a feasible integer assignment on frozen MIPLIB models

## Scientific setting

MIPLIB 2017 is the standard library of mixed-integer linear programs. A primal heuristic
searches for a better feasible assignment without proving optimality. The official MIPLIB
checker is a primal check: bounds, row activity, integrality, and objective. Duals are not
part of that contract, and this task does not score them.

The frozen model is MIPLIB queens-30: 900 binary variables and 960 constraints.
It maximizes the number of queens on a 30-by-30 board with each queen threatening at
most one other queen, represented as a minimization with negative unit costs.
MIPLIB classifies it as hard; solufile v36 records the proven optimum -40.
The original compressed MPS is hash-bound and parsed locally; there is no runtime download.
The empty assignment is a feasible baseline. This replaces the three gen-ip models that
were nearly saturated by a short SciPy milp call.

This is not permutation flow-shop scheduling. The object is a general integer assignment
on an authentic MIPLIB constraint matrix, not a job permutation and not a makespan.

## Your task

Implement:

```python
def improve_primal(problem):
    """Return one dense integer assignment in frozen MPS column order."""
```

The same function is called once for the frozen instance. `problem` contains:

| key | value |
|---|---|
| `name`, `sense` | instance name and `"minimize"` |
| `n_variables`, `n_constraints` | dimensions |
| `variable_names` | MPS column names in frozen order |
| `objective` | objective coefficients in that order |
| `lower_bounds` | lower bounds, all 0 |
| `upper_bounds` | upper bounds, all 1 |
| `row_senses` | `"L"`, `"G"`, or `"E"` per row |
| `rhs` | right-hand sides |
| `row_ptr`, `column_indices`, `coefficients` | CSR constraint matrix |
| `mps_sha256` | hash of the vendored MPS file |
| `constraint_abs_tol`, `constraint_rel_tol`, `integrality_tol` | MIPLIB checker tolerances |

Return a Python list of exactly `n_variables` integers. Floats, booleans, sparse dicts,
and missing entries are rejected rather than rounded.

## Scoring

For a feasible minimization objective `z`, with weak-feasible baseline `b=0` and frozen
MIPLIB optimum `r=-40`,

```text
clip01( log((b - r + 1) / (z - r + 1)) / log(b - r + 1) )
```

The empty baseline scores zero; a feasible 40-queen assignment scores one. A feasible
assignment with q queens scores `log(41/(41-q))/log(41)`, clipped to [0,1]. Linear
`q/40` is retired: it made the whole 0→0.95 range cheap. The last queens are the
expensive increments. Score-mode remains clipped at the proven optimum; this is not
an uncapped scale. The optimum is sourced from MIPLIB solufile v36; no claim is made
that it is an open record.

## Tools and scope

- NumPy, SciPy, and the standard library are available. SciPy includes HiGHS through scipy.optimize.milp; its use is allowed.
- Networkless, single-process, bounded by the framework timeout.
- Only edit `solution.py`; keep `improve_primal(problem)`.
- Do not read `verification/` or `frontier_eval/`.
- The MPS file under `references/instances/` is the same model as the CSR payload.

## Relation to nearby tasks

- **PermutationFlowShop (open PR #54)** is Engineering × combinatorial too, but the object is a
  job permutation and the check is makespan. This task checks a dense integer assignment
  against an authentic MIPLIB matrix.
- **GraphFromDistances** reconstructs a graph from queries; **ShannonCapacityCertificate**
  verifies information-theoretic constructions. Neither optimizes a dense integer assignment
  against a provided MPS constraint matrix.
- The source and redistribution-status notes are recorded in references/DATA_LICENSE.md.
- Not a Frontier-Eng design task: the object is a general integer assignment on a
  frozen MIPLIB matrix, not a simulator-backed engineering layout.
