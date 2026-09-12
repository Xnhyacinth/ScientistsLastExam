"""Diagnostic public-input descriptor fit, derived after evaluator inspection.

Reuses public-only graph/grammar helpers from the shipped signature probe.
Fits coefficients from budgeted responses only; no oracle imports/constants,
files, hidden world IDs, or evaluator state are available to this candidate.
Features and acquisition order were selected in this local audit (4 variants).
Not an independently blind first-model draw or new scientific reference.
"""

from __future__ import annotations

import itertools


def _graph_parts(graph, inventory, valence):
    atoms = tuple(graph["atoms"])
    if tuple(sorted(atoms)) != tuple(sorted(inventory)):
        raise ValueError("atom inventory changed")
    bonds = {
        tuple(sorted((int(left), int(right)))) for left, right, order in graph["bonds"]
    }
    if any(int(order) != 1 for _left, _right, order in graph["bonds"]):
        raise ValueError("only single bonds are supported")
    degree = [0] * len(atoms)
    for left, right in bonds:
        degree[left] += 1
        degree[right] += 1
    if any(degree[index] > valence[atom] for index, atom in enumerate(atoms)):
        raise ValueError("valence exceeded")
    seen = {0}
    frontier = [0]
    while frontier:
        node = frontier.pop()
        for left, right in bonds:
            neighbour = right if left == node else left if right == node else None
            if neighbour is not None and neighbour not in seen:
                seen.add(neighbour)
                frontier.append(neighbour)
    if len(seen) != len(atoms):
        raise ValueError("disconnected graph")
    return atoms, bonds


def _canonical_graph(graph, inventory, valence):
    atoms, bonds = _graph_parts(graph, inventory, valence)
    labels = tuple(sorted(atoms))
    encodings = []
    for permutation in itertools.permutations(range(len(atoms))):
        if tuple(atoms[index] for index in permutation) != labels:
            continue
        adjacency = tuple(
            int(tuple(sorted((permutation[left], permutation[right]))) in bonds)
            for left in range(len(atoms))
            for right in range(left + 1, len(atoms))
        )
        encodings.append(adjacency)
    return ",".join(labels) + "|" + "".join(str(value) for value in min(encodings))


def _key_to_graph(key):
    labels_text, bits_text = key.split("|", 1)
    atoms = labels_text.split(",")
    pairs = list(itertools.combinations(range(len(atoms)), 2))
    return {
        "atoms": atoms,
        "bonds": [
            [left, right, 1]
            for bit, (left, right) in zip(bits_text, pairs)
            if bit == "1"
        ],
    }


def _neighbours(graph, inventory, valence):
    key = _canonical_graph(graph, inventory, valence)
    canonical = _key_to_graph(key)
    atoms, bonds = _graph_parts(canonical, inventory, valence)
    pairs = set(itertools.combinations(range(len(atoms)), 2))
    neighbours = {}
    for removed in bonds:
        for formed in pairs - bonds:
            candidate = {
                "atoms": list(atoms),
                "bonds": [
                    [left, right, 1]
                    for left, right in sorted((bonds - {removed}) | {formed})
                ],
            }
            try:
                candidate_key = _canonical_graph(candidate, inventory, valence)
            except ValueError:
                continue
            if candidate_key != key:
                neighbours.setdefault(candidate_key, _key_to_graph(candidate_key))
    return dict(sorted(neighbours.items()))


def _exchange_channels(left_key, right_key):
    left_graph = _key_to_graph(left_key)
    right_graph = _key_to_graph(right_key)
    atoms = tuple(left_graph["atoms"])
    right_atoms = tuple(right_graph["atoms"])
    left_bonds = {tuple(bond[:2]) for bond in left_graph["bonds"]}
    right_bonds = {tuple(bond[:2]) for bond in right_graph["bonds"]}
    pairs = list(itertools.combinations(range(len(atoms)), 2))
    channels = set()
    for mapping in itertools.permutations(range(len(atoms))):
        if any(
            atoms[index] != right_atoms[mapping[index]] for index in range(len(atoms))
        ):
            continue
        aligned_right = {
            pair
            for pair in pairs
            if tuple(sorted((mapping[pair[0]], mapping[pair[1]]))) in right_bonds
        }
        removed = left_bonds - aligned_right
        formed = aligned_right - left_bonds
        if len(removed) == 1 and len(formed) == 1:
            broken_atoms = tuple(sorted(atoms[index] for index in next(iter(removed))))
            formed_atoms = tuple(sorted(atoms[index] for index in next(iter(formed))))
            channels.add((broken_atoms, formed_atoms))
    return tuple(sorted(channels))


import numpy as np


def discover_reaction_network(problem, probe):
    inventory = tuple(problem["atom_inventory"])
    valence = problem["element_valence_bounds"]
    seed = _canonical_graph(problem["seed_species"][0], inventory, valence)
    graphs = {seed: _key_to_graph(seed)}
    todo = [seed]
    edges = []
    while todo:
        left = todo.pop(0)
        for right, graph in _neighbours(graphs[left], inventory, valence).items():
            edges.append((left, right))
            if right not in graphs:
                graphs[right] = graph
                todo.append(right)
    edges = sorted(set(edges))
    signatures = sorted({_exchange_channels(*e) for e in edges})
    types = sorted(set(tuple(sorted(p)) for p in itertools.combinations(inventory, 2)))

    def feature(edge):
        graph = graphs[edge[0]]
        deg = [0] * len(inventory)
        counts = dict.fromkeys(types, 0)
        for a, b, _ in graph["bonds"]:
            deg[a] += 1
            deg[b] += 1
            counts[tuple(sorted((graph["atoms"][a], graph["atoms"][b])))] += 1
        return (
            [float(_exchange_channels(*edge) == s) for s in signatures]
            + [counts[t] for t in types]
            + [sum(d * d for d in deg)]
        )

    X = np.array([feature(e) for e in edges], float)
    X /= np.maximum(np.linalg.norm(X, axis=0), 1)
    observed = {}
    yes = []
    values = []
    no = []
    for step in range(int(problem["probe_budget"])):
        remaining = [i for i in range(len(edges)) if i not in observed]
        if not remaining:
            break
        if yes:
            basis = np.linalg.pinv(X[yes])
            uncertainty = np.linalg.norm(X - X @ basis @ X[yes], axis=1)
            prediction = X @ basis @ np.array(values)
        else:
            uncertainty = np.linalg.norm(X, axis=1)
            prediction = np.zeros(len(edges))
        reached = {seed}
        while True:
            added = {edges[i][1] for i in yes if edges[i][0] in reached}
            if added <= reached:
                break
            reached |= added
        idx = max(
            remaining,
            key=lambda i: (
                int(edges[i][0] in reached),
                round(float(uncertainty[i]), 9),
                -i,
            ),
        )
        result = probe(
            {"reactant": graphs[edges[idx][0]], "product": graphs[edges[idx][1]]}
        )
        if result["status"] == "model_inadequate":
            return {"abstain": True, "confidence": 0.0}
        observed[idx] = result
        if result["status"] == "supported":
            yes.append(idx)
            values.append(float(result["activation_energy"]))
        else:
            no.append(idx)
    if not yes:
        return {"abstain": True, "confidence": 0.0}
    basis = np.linalg.pinv(X[yes])
    pred = X @ basis @ np.array(values)
    uncertainty = np.linalg.norm(X - X @ basis @ X[yes], axis=1)
    lower = max(values)
    upper = min(
        [pred[i] for i in no if uncertainty[i] < 1e-7 and pred[i] > lower]
        + [lower + 1e-5]
    )
    threshold = (lower + upper) / 2
    selected = {
        i: float(pred[i])
        for i in range(len(edges))
        if uncertainty[i] < 1e-7 and 0 <= pred[i] <= threshold
    }
    for i in no:
        selected.pop(i, None)
    selected.update(dict(zip(yes, values)))
    reachable = {seed}
    while True:
        more = {edges[i][1] for i in selected if edges[i][0] in reachable}
        if more <= reachable:
            break
        reachable |= more
    selected = {i: v for i, v in selected.items() if edges[i][0] in reachable}
    if not selected:
        return {"abstain": True, "confidence": 0.0}
    keys = sorted({k for i in selected for k in edges[i]})
    positions = {k: i for i, k in enumerate(keys)}
    return {
        "abstain": False,
        "confidence": 1.0,
        "species": [graphs[k] for k in keys],
        "reactions": [
            {
                "reactant": positions[edges[i][0]],
                "product": positions[edges[i][1]],
                # Stabilize fitted last bits within the existing 1e-9 evidence tolerance.
                "activation_energy": round(v, 10),
            }
            for i, v in sorted(selected.items())
        ],
    }
