"""Fixed public-bounds grid; no surrogate coefficients or objective queries.

This is a new two-coordinate control, not the missing owner's original grid.
"""
import math


def design_process_archive(problem):
    bounds = problem["bounds"]
    base = {name: (low + high) / 2 for name, (low, high) in bounds.items()}
    for name in ("anneal_time", "cooling_rate"):
        low, high = bounds[name]
        base[name] = math.sqrt(low * high)
    processes = []
    for i in range(5):
        for j in range(4):
            row = dict(base)
            for name, fraction in (("blend_fraction_b", i / 4), ("draw_ratio", j / 3)):
                low, high = bounds[name]
                row[name] = low + fraction * (high - low)
            processes.append(row)
    return {"processes": processes}
