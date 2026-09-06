"""Published score-one solution replay, not a candidate-equivalent policy."""
from __future__ import annotations

import gzip
from decimal import Decimal
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parent / "private_data"


def improve_primal(problem):
    names = {name: index for index, name in enumerate(problem["variable_names"])}
    values = np.zeros(problem["num_variables"], dtype=np.int64)
    path = DATA_DIR / (problem["name"] + "-reference.sol.gz")
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            fields = line.split()
            if not fields or fields[0] == "=obj=":
                continue
            value = Decimal(fields[1])
            if value != value.to_integral_value():
                raise ValueError("reference assignment is not integral")
            values[names[fields[0]]] = int(value)
    return values
