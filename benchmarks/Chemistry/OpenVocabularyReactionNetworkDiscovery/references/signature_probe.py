"""Public-only counterexample: cache each bond-type channel signature once.

This independently reconstructs the maintainer's reported shortcut. It reads only
problem fields and paid probe responses, with no evaluator constants or imports.
It documents a scientific admission failure, not an admissible reference.
"""
from __future__ import annotations

import itertools

def _graph_parts(graph, inventory, valence):
    atoms = tuple(graph["atoms"])
    if tuple(sorted(atoms)) != tuple(sorted(inventory)):
        raise ValueError("atom inventory changed")
    bonds = {tuple(sorted((int(left), int(right)))) for left, right, order in graph["bonds"]}
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
        if any(atoms[index] != right_atoms[mapping[index]] for index in range(len(atoms))):
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


def discover_reaction_network(problem, probe):
    inventory = tuple(problem["atom_inventory"])
    valence = dict(problem["element_valence_bounds"])
    seed = _canonical_graph(problem["seed_species"][0], inventory, valence)
    graphs = {seed: _key_to_graph(seed)}
    attempted, cache, supported = set(), {}, {}
    while True:
        frontier = [(left, right, graph) for left in sorted(graphs)
                    for right, graph in _neighbours(graphs[left], inventory, valence).items()
                    if (left, right) not in attempted]
        if not frontier:
            break
        left, right, graph = min(frontier, key=lambda edge: (edge[0], edge[1]))
        attempted.add((left, right))
        signature = _exchange_channels(left, right)
        if signature not in cache:
            if len(cache) >= int(problem["probe_budget"]):
                continue
            cache[signature] = probe({"reactant": graphs[left], "product": graph})
        response = cache[signature]
        if response["status"] == "model_inadequate":
            return {"abstain": True, "confidence": 0.0}
        if response["status"] == "supported":
            graphs.setdefault(right, graph)
            supported[left, right] = float(response["activation_energy"])
    if not supported:
        return {"abstain": True, "confidence": 0.0}
    keys = sorted({key for edge in supported for key in edge})
    positions = {key: index for index, key in enumerate(keys)}
    return {"species": [graphs[key] for key in keys], "reactions": [
        {"reactant": positions[left], "product": positions[right], "activation_energy": barrier}
        for (left, right), barrier in sorted(supported.items())],
        "abstain": False, "confidence": 1.0}
