"""Baseline reusable primal-improvement policy.

It returns the supplied feasible incumbent unchanged.  The evaluator scores
that policy as zero; edit this function to produce a better exact-integer
assignment from the generic sparse MIP representation.
"""
from __future__ import annotations


def improve_primal(problem):
    """Return one dense assignment in the model's frozen variable order."""
    return problem["incumbent"].copy()
