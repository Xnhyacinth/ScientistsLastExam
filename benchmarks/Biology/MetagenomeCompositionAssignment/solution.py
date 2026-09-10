"""Legal one-panel, one-taxon baseline; no mixture or adequacy inference."""
import numpy as np


def assign_composition(problem, sequence):
    matrix = np.asarray(problem["reference_profiles"], dtype=float)
    observation = problem["initial_observation"]
    index = {name: i for i, name in enumerate(problem["marker_ids"])}
    selected = [index[name] for name in problem["panel_markers"][observation["panel_id"]]]
    columns = matrix[selected]
    columns = columns/columns.sum(axis=0)
    counts = np.asarray(observation["marker_counts"])[selected]
    frequencies = counts/counts.sum()
    best = int(np.argmin(np.sum((columns-frequencies[:, None])**2, axis=0)))
    return dict(taxa=[dict(taxon=problem["taxon_ids"][best], abundance=1.)],
                ambiguous_groups=[], abstain=False)
