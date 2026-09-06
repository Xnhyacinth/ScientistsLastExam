"""Reference-free one-coordinate primal descent over the public CSR payload.

This deliberately modest heuristic proves the policy interface is usable. On
the two frozen early incumbents every individually improving bound move is
infeasible, so it returns two valid assignments but scores zero. It is not the
score-one reference and is retained as a measured maturity blocker.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse


def improve_primal(problem):
    values = np.asarray(problem["incumbent"], dtype=np.int64).copy()
    matrix = sparse.csr_matrix(
        (
            problem["coefficients"],
            problem["column_indices"],
            problem["row_ptr"],
        ),
        shape=(problem["num_constraints"], problem["num_variables"]),
        dtype=np.int64,
    )
    columns = matrix.tocsc()
    activity = np.asarray(matrix @ values, dtype=np.int64)
    objective = np.asarray(problem["objective"], dtype=np.int64)
    lower = np.asarray(problem["lower_bounds"], dtype=np.int64)
    upper = np.asarray(problem["upper_bounds"], dtype=np.int64)
    rhs = np.asarray(problem["rhs"], dtype=np.int64)
    senses = np.asarray(problem["row_senses"])

    order = np.argsort(-np.abs(objective), kind="stable")
    for column in order:
        coefficient = int(objective[column])
        if coefficient == 0:
            continue
        target = int(lower[column]) if coefficient > 0 else int(upper[column])
        delta = target - int(values[column])
        if delta == 0:
            continue
        start = int(columns.indptr[column])
        stop = int(columns.indptr[column + 1])
        rows = columns.indices[start:stop]
        trial = activity[rows] + columns.data[start:stop] * delta
        row_senses = senses[rows]
        sides = rhs[rows]
        feasible = np.all(
            ((row_senses != "L") | (trial <= sides))
            & ((row_senses != "G") | (trial >= sides))
            & ((row_senses != "E") | (trial == sides))
        )
        if feasible:
            values[column] = target
            activity[rows] = trial
    return values
