"""Candidate-equivalent public-problem-only process-archive witness.

The witness generates a deterministic Latin-hypercube pool, evaluates a
builder-chosen approximate mixture/crystallization surrogate,
greedily adds the process with the largest proxy hypervolume increment, and
performs deterministic coordinate exchange on the selected archive.  It never
imports or calls the scored phase-field oracle.
"""
from __future__ import annotations

import math
from heapq import heappop, heappush

# Search settings and approximate surrogate belong to the policy, not the public problem.
SEARCH = {
    "pool_size": 1024,
    "archive_size": 20,
    "coordinate_refinement_passes": 2,
    "coordinate_refinement_points_per_axis": 11,
    "latin_hypercube_multipliers": [
        1,
        73,
        127,
        181,
        239
    ],
    "latin_hypercube_offsets": [
        0,
        19,
        43,
        71,
        101
    ]
}
PROXY = {
    "crystallinity_equilibrium_temperature_coefficient": 4.0,
    "crystallinity_equilibrium_temperature_reference": 0.75,
    "crystallinity_equilibrium_cooling_coefficient": 0.25,
    "crystallization_rate_constant": 500.0,
    "crystallization_activation_energy": 6.0,
    "crystallization_temperature_offset": 0.2,
    "modulus_voigt_base": 0.5,
    "modulus_orientation_weight": 0.3,
    "modulus_reuss_base": 0.5,
    "crystallinity_base": 0.75,
    "crystallinity_gain": 0.3,
    "draw_modulus_gain": 0.4,
    "density_base": 1.0,
    "density_blend_coefficient": 0.2,
    "permeability_parallel_base": 0.3,
    "permeability_orientation_weight": 0.5,
    "permeability_series_base": 0.7,
    "draw_permeability_penalty": 0.25,
    "energy_time_base": 0.1,
    "energy_temperature_coefficient": 0.8,
    "energy_temperature_reference": 0.4,
    "energy_draw_coefficient": 0.3,
    "energy_draw_exponent": 1.5,
    "energy_cooling_coefficient": 0.2
}


def _quantize(problem, process):
    row = {}
    for field in problem["process_fields"]:
        low, high = problem["bounds"][field]
        resolution = problem["manufacturing_resolutions"][field]
        bin_index = round((process[field] - low) / resolution)
        row[field] = min(max(low + bin_index * resolution, low), high)
    return row


def _candidate_pool(problem, pool_size=None):
    search = dict(SEARCH)
    if pool_size is not None:
        search["pool_size"] = pool_size
    size = search["pool_size"]
    rows = []
    for index in range(size):
        row = {}
        for field, multiplier, offset in zip(
            problem["process_fields"],
            search["latin_hypercube_multipliers"],
            search["latin_hypercube_offsets"],
        ):
            low, high = problem["bounds"][field]
            unit = ((multiplier * index + offset) % size + 0.5) / size
            row[field] = low + unit * (high - low)
        rows.append(_quantize(problem, row))
    return rows


def _proxy_objectives(problem, process):
    parameters = PROXY
    normalization = problem["objective_normalization"]
    blend = process["blend_fraction_b"]
    temperature = process["anneal_temperature"]
    duration = process["anneal_time"]
    cooling_rate = process["cooling_rate"]
    draw_ratio = process["draw_ratio"]
    draw_low, draw_high = problem["bounds"]["draw_ratio"]
    orientation = (draw_ratio - draw_low) / (draw_high - draw_low)

    equilibrium_crystallinity = 1.0 / (
        1.0
        + math.exp(
            parameters["crystallinity_equilibrium_temperature_coefficient"]
            * (
                temperature
                - parameters["crystallinity_equilibrium_temperature_reference"]
            )
            + parameters["crystallinity_equilibrium_cooling_coefficient"]
            * cooling_rate
        )
    )
    crystallization_rate = parameters["crystallization_rate_constant"] * math.exp(
        -parameters["crystallization_activation_energy"]
        / (temperature + parameters["crystallization_temperature_offset"])
    )
    crystallinity = equilibrium_crystallinity * (
        1.0 - math.exp(-crystallization_rate * duration)
    )

    modulus_a, modulus_b = problem["constituent_properties"]["reduced_modulus"]
    voigt = modulus_a * (1.0 - blend) + modulus_b * blend
    reuss = 1.0 / ((1.0 - blend) / modulus_a + blend / modulus_b)
    modulus = (
        (
            parameters["modulus_voigt_base"]
            + parameters["modulus_orientation_weight"] * orientation
        )
        * voigt
        + (
            parameters["modulus_reuss_base"]
            - parameters["modulus_orientation_weight"] * orientation
        )
        * reuss
    )
    modulus *= (
        parameters["crystallinity_base"]
        + parameters["crystallinity_gain"] * crystallinity
    )
    modulus *= 1.0 + parameters["draw_modulus_gain"] * orientation
    density = parameters["density_base"] + parameters[
        "density_blend_coefficient"
    ] * blend
    specific_modulus = modulus / density

    permeability_a, permeability_b = problem["constituent_properties"][
        "reduced_permeability"
    ]
    parallel = permeability_a * (1.0 - blend) + permeability_b * blend
    series = 1.0 / ((1.0 - blend) / permeability_a + blend / permeability_b)
    permeability = (
        (
            parameters["permeability_parallel_base"]
            + parameters["permeability_orientation_weight"] * orientation
        )
        * parallel
        + (
            parameters["permeability_series_base"]
            - parameters["permeability_orientation_weight"] * orientation
        )
        * series
    )
    permeability *= 1.0 + parameters["draw_permeability_penalty"] * orientation
    barrier_index = 1.0 / permeability

    energy = (
        duration
        * (
            parameters["energy_time_base"]
            + parameters["energy_temperature_coefficient"]
            * (temperature - parameters["energy_temperature_reference"]) ** 2
        )
        + parameters["energy_draw_coefficient"]
        * (draw_ratio - draw_low) ** parameters["energy_draw_exponent"]
        + parameters["energy_cooling_coefficient"] / cooling_rate
    )

    def normalized(value, specification):
        return min(max(value, specification["minimum"]), specification["maximum"])

    return (
        normalized(
            (specific_modulus - normalization["specific_modulus"]["offset"])
            / normalization["specific_modulus"]["scale"],
            {"minimum": 0.0, "maximum": 1.0},
        ),
        normalized(
            (barrier_index - normalization["barrier_index"]["offset"])
            / normalization["barrier_index"]["scale"],
            {"minimum": 0.0, "maximum": 1.0},
        ),
        normalized(
            1.0 - energy / normalization["process_energy"]["maximum"],
            {"minimum": 0.0, "maximum": 1.0},
        ),
    )


def _hypervolume_2d(points):
    xs = sorted({0.0, *(point[0] for point in points)})
    area = 0.0
    for left, right in zip(xs, xs[1:]):
        active = [point[1] for point in points if point[0] >= right]
        if active:
            area += (right - left) * max(active)
    return area


def _hypervolume_3d(points):
    xs = sorted({0.0, *(point[0] for point in points)})
    volume = 0.0
    for left, right in zip(xs, xs[1:]):
        active = [(point[1], point[2]) for point in points if point[0] >= right]
        if active:
            volume += (right - left) * _hypervolume_2d(active)
    return volume


def _refine_archive(problem, rows):
    fields = problem["process_fields"]
    search = SEARCH
    objectives = [_proxy_objectives(problem, row) for row in rows]
    for _ in range(search["coordinate_refinement_passes"]):
        for row_index in range(len(rows)):
            for field in fields:
                low, high = problem["bounds"][field]
                best_row = rows[row_index]
                best_objective = objectives[row_index]
                best_hypervolume = _hypervolume_3d(objectives)
                for point_index in range(
                    search["coordinate_refinement_points_per_axis"]
                ):
                    denominator = (
                        search["coordinate_refinement_points_per_axis"] - 1
                    )
                    value = low + point_index / denominator * (high - low)
                    trial = _quantize(
                        problem, {**rows[row_index], field: value}
                    )
                    trial_key = tuple(trial[name] for name in fields)
                    if any(
                        index != row_index
                        and tuple(row[name] for name in fields) == trial_key
                        for index, row in enumerate(rows)
                    ):
                        continue
                    trial_objective = _proxy_objectives(problem, trial)
                    trial_objectives = list(objectives)
                    trial_objectives[row_index] = trial_objective
                    hypervolume = _hypervolume_3d(trial_objectives)
                    if hypervolume > best_hypervolume:
                        best_row = trial
                        best_objective = trial_objective
                        best_hypervolume = hypervolume
                rows[row_index] = best_row
                objectives[row_index] = best_objective
    return rows


def _select_archive_indices(objectives, archive_size):
    """Return the exact greedy sequence using lazy submodular marginal gains."""
    heap = []
    for index, objective in enumerate(objectives):
        heappush(heap, (-_hypervolume_3d([objective]), index, 0))
    selected = []
    base_hypervolume = 0.0
    for round_index in range(archive_size):
        while True:
            _negative_gain, candidate, updated_round = heappop(heap)
            if updated_round == round_index:
                selected.append(candidate)
                base_hypervolume = _hypervolume_3d(
                    [objectives[index] for index in selected]
                )
                break
            candidate_hypervolume = _hypervolume_3d(
                [objectives[index] for index in selected + [candidate]]
            )
            gain = candidate_hypervolume - base_hypervolume
            heappush(heap, (-gain, candidate, round_index))
    return selected


def design_process_archive(problem, pool_size=None):
    """Search and coordinate-refine the declared public proxy Pareto witness."""
    pool = _candidate_pool(problem, pool_size)
    objectives = [_proxy_objectives(problem, process) for process in pool]
    archive_size = min(SEARCH["archive_size"], problem["archive_size_bounds"][1])
    selected = _select_archive_indices(objectives, archive_size)
    rows = [pool[index] for index in selected]
    return {"processes": _refine_archive(problem, rows)}
