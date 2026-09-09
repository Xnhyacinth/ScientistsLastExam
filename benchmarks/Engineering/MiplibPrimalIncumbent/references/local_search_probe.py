"""Deterministic no-solver packing heuristic; uses only the public CSR matrix."""
import numpy as np

ROUNDS = 2500


def improve_primal(problem):
    n, m = problem["n_variables"], problem["n_constraints"]
    rows = [[] for _ in range(n)]
    values = [[] for _ in range(n)]
    for row in range(m):
        for index in range(problem["row_ptr"][row], problem["row_ptr"][row + 1]):
            column = problem["column_indices"][index]
            rows[column].append(row)
            values[column].append(problem["coefficients"][index])
    rows = [np.asarray(row, dtype=int) for row in rows]
    values = [np.asarray(value, dtype=float) for value in values]
    rhs = np.asarray(problem["rhs"], dtype=float)
    rng = np.random.default_rng(20260909)
    selected = np.zeros(n, dtype=bool)
    activity = np.zeros(m)
    best = selected.copy()
    best_count = 0
    for iteration in range(ROUNDS):
        if iteration % 250 == 0:
            selected[:] = False
            activity[:] = 0
        else:
            occupied = np.flatnonzero(selected)
            for column in rng.choice(occupied, size=min(2, len(occupied)), replace=False):
                selected[column] = False
                activity[rows[column]] -= values[column]
        for column in rng.permutation(n):
            if selected[column]:
                continue
            if np.all(activity[rows[column]] + values[column] <= rhs[rows[column]]):
                selected[column] = True
                activity[rows[column]] += values[column]
        count = int(np.count_nonzero(selected))
        if count > best_count:
            best, best_count = selected.copy(), count
    return best.astype(int).tolist()
