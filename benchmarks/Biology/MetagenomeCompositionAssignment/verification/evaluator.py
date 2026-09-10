"""Conditional multinomial mixtures with design-dependent reporting resolution."""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations_with_replacement
import numpy as np

N_TAXA = 14
N_PANELS = 10
N_MARKERS = 6*N_PANELS
READS = 12000
BUDGET = 2
RESOLUTION_THRESHOLD = 9.0
MINIMUM_ABUNDANCE = .08
ABUNDANCE_TOLERANCE = .05
SPECS = tuple((kind, seed) for start in (3100, 7100)
              for kind, seed in zip(["supported"]*6 + ["alias"]*3 + ["out_of_library"]*3,
                                    range(start, start+12)))
DEV = range(12)
HELD = range(12, 24)


def _library(seed):
    rng = np.random.default_rng((seed, 23))
    matrix = rng.uniform(.08, 1, (N_MARKERS, N_TAXA))
    matrix[:, 1] = matrix[:, 0] * np.exp(rng.normal(0, .001, N_MARKERS))
    # Coarse initial markers confound two pairs of strain groups. Other panels
    # distinguish the group before its diagnostic panel resolves strain identity.
    matrix[:6, 4] = matrix[:6, 2]
    matrix[:6, 8] = matrix[:6, 6]
    diagnostics = rng.choice(np.arange(1, N_PANELS), 4, replace=False)
    for first, diagnostic in zip((2, 4, 6, 8), diagnostics):
        matrix[:, first+1] = matrix[:, first]
        indices = np.arange(diagnostic*6, (diagnostic+1)*6)
        original = matrix[indices, first].copy()
        perturbation = rng.normal(0, 1, 6)
        strength = .7
        for _ in range(100):
            altered = original * np.exp(strength*perturbation)
            altered *= original.sum()/altered.sum()
            distance = np.sum((np.sqrt(original/original.sum()) - np.sqrt(altered/altered.sum()))**2)
            if READS*MINIMUM_ABUNDANCE*distance >= 36:
                break
            strength *= 1.4
        else:
            raise RuntimeError("could not construct a separable marker panel")
        # Each pair differs in a distinct diagnostic panel, preserving panel
        # mass and therefore its unmeasured group abundance.
        matrix[indices, first+1] = altered
    matrix /= matrix.sum(axis=0)
    permutation = rng.permutation(N_TAXA)
    return matrix[:, permutation], np.argsort(permutation)


def _truth(kind, seed):
    matrix, inverse = _library(seed)
    rng = np.random.default_rng((seed, 61))
    count = int(rng.integers(3, 5))
    # Two of four query-dependent groups are active, so selecting the relevant
    # diagnostics is necessary and a full-resolution two-call plan exists.
    ids = list(rng.choice([2, 4, 6, 8], 2, replace=False))
    if kind == "alias":
        ids.append(0)
    ids += list(rng.choice([10, 11, 12, 13], count-len(ids), replace=False))
    ids = [i+int(rng.integers(2)) if i < 10 else i for i in ids]
    abundance = .12 + (1-.12*count)*rng.dirichlet(np.full(count, 2.))
    weights = np.zeros(N_TAXA)
    weights[inverse[ids]] = abundance
    probabilities = matrix @ weights
    if kind == "out_of_library":
        base = probabilities.copy()
        basis = np.column_stack((matrix, np.ones(N_MARKERS)))
        direction = rng.normal(0, 1, N_MARKERS)
        direction -= basis @ np.linalg.lstsq(basis, direction, rcond=1e-12)[0]
        direction *= .59 / np.max(np.abs(direction/base))
        for _ in range(100):
            trial = base + direction
            inside = True
            for panel in range(N_PANELS):
                block = matrix[panel*6:(panel+1)*6]
                columns = block/block.sum(axis=0)
                conditional = trial[panel*6:(panel+1)*6]
                conditional = conditional/conditional.sum()
                if np.any(conditional < columns.min(axis=1)) or np.any(conditional > columns.max(axis=1)):
                    inside = False
                    break
            if inside:
                probabilities = trial
                break
            direction *= .9
        else:
            raise RuntimeError("could not construct a shared-marker residual")
    return weights, probabilities


def _marker_order(seed):
    return np.random.default_rng((seed, 953)).permutation(N_MARKERS)


def _observation(kind, seed, panel, replicate):
    _, probabilities = _truth(kind, seed)
    indices = np.arange(panel*6, (panel+1)*6)
    conditional = probabilities[indices]/probabilities[indices].sum()
    rng = np.random.default_rng((seed, panel, replicate, 41))
    counts = np.zeros(N_MARKERS, dtype=int)
    counts[indices] = rng.multinomial(READS, conditional)
    return dict(panel_id=panel, read_count=READS,
                marker_counts=counts[_marker_order(seed)].tolist())


def _problem(kind, seed):
    matrix, _ = _library(seed)
    order = _marker_order(seed)
    inverse = np.argsort(order)
    markers = [f"m{i}" for i in range(N_MARKERS)]
    return dict(taxon_ids=[f"t{i}" for i in range(N_TAXA)], marker_ids=markers,
                reference_profiles=matrix[order].tolist(),
                initial_observation=_observation(kind, seed, 0, 0),
                available_panels=list(range(1, N_PANELS)),
                panel_markers={p: [markers[inverse[i]] for i in range(p*6, (p+1)*6)] for p in range(N_PANELS)},
                panel_budget=BUDGET, reads_per_panel=READS,
                minimum_reported_abundance=MINIMUM_ABUNDANCE,
                abundance_tolerance=ABUNDANCE_TOLERANCE,
                resolution_threshold=RESOLUTION_THRESHOLD,
                observation_model="conditional_multinomial")


class _Sequencer:
    def __init__(self, kind, seed, noise_repeat=0):
        self.kind, self.seed = kind, seed
        self.calls, self.violated = 0, False
        self.panel_calls = {}
        self.noise_repeat = noise_repeat

    def __call__(self, *args, **kwargs):
        try:
            return self._request(*args, **kwargs)
        except (TypeError, ValueError, RuntimeError):
            self.violated = True
            raise

    def _request(self, panel_id):
        if self.violated:
            raise RuntimeError("sequencing contract previously violated")
        if type(panel_id) is not int or panel_id not in range(1, N_PANELS):
            raise ValueError("panel_id must be a listed integer")
        if self.calls >= BUDGET:
            raise RuntimeError("read budget exhausted")
        replicate = self.panel_calls.get(panel_id, 0)
        self.panel_calls[panel_id] = replicate+1
        self.calls += 1
        return _observation(self.kind, self.seed, panel_id, replicate+10*self.noise_repeat)


def _separation(problem, panel_counts):
    matrix = np.asarray(problem["reference_profiles"])
    marker_index = {name: i for i, name in enumerate(problem["marker_ids"])}
    n = len(problem["taxon_ids"])
    result = np.zeros((n, n))
    for panel, repeats in sorted(panel_counts.items()):
        indices = [marker_index[name] for name in problem["panel_markers"][panel]]
        block = matrix[indices]
        roots = np.sqrt(block/block.sum(axis=0))
        for i in range(n):
            for j in range(i):
                value = repeats*problem["reads_per_panel"]*problem["minimum_reported_abundance"]*np.sum((roots[:, i]-roots[:, j])**2)
                result[i, j] += value
                result[j, i] += value
    return result


def _components(problem, separation):
    # Independent union/find implementation; the reference uses graph traversal.
    n = len(problem["taxon_ids"])
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i):
            if separation[i, j] < problem["resolution_threshold"]:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), set()).add(i)
    return list(groups.values())


def _best_separation(problem):
    best = np.zeros((len(problem["taxon_ids"]),)*2)
    for plan in combinations_with_replacement(problem["available_panels"], BUDGET):
        counts = {0: 1}
        for panel in plan:
            counts[panel] = counts.get(panel, 0)+1
        best = np.maximum(best, _separation(problem, counts))
    return best


def _parse(output, problem):
    if not isinstance(output, dict) or set(output) != {"taxa", "ambiguous_groups", "abstain"}:
        return None
    if type(output["abstain"]) is not bool or not isinstance(output["taxa"], list) or not isinstance(output["ambiguous_groups"], list):
        return None
    names = set(problem["taxon_ids"])
    claims, used = {}, set()
    for field in ("taxa", "ambiguous_groups"):
        for row in output[field]:
            key = "taxon" if field == "taxa" else "taxa"
            if not isinstance(row, dict) or set(row) != {key, "abundance"}:
                return None
            members = [row[key]] if field == "taxa" else row[key]
            if not isinstance(members, list) or (field == "ambiguous_groups" and len(members) < 2):
                return None
            if any(not isinstance(name, str) or name not in names for name in members) or len(set(members)) != len(members):
                return None
            group = frozenset(members)
            value = row["abundance"]
            if group & used or type(value) not in (int, float) or not np.isfinite(value) or not 0 <= value <= 1:
                return None
            used |= group
            claims[group] = float(value)
    if sum(claims.values()) > 1+1e-6 or (output["abstain"] and claims):
        return None
    return claims, output["abstain"]


def evaluate(assign_composition, noise_repeat=0):
    rows = []
    for kind, seed in SPECS:
        problem = _problem(kind, seed)
        if noise_repeat:
            problem["initial_observation"] = _observation(kind, seed, 0, 10*noise_repeat)
        sequencer = _Sequencer(kind, seed, noise_repeat)
        try:
            parsed = _parse(assign_composition(deepcopy(problem), sequencer), problem)
        except Exception:
            parsed = None
        valid = parsed is not None and not sequencer.violated
        claims, abstain = parsed if valid else ({}, False)
        separation = _separation(problem, {0: 1, **sequencer.panel_calls})
        best = _best_separation(problem)
        weights, _ = _truth(kind, seed)
        targets = {}
        intrinsic = {
            frozenset(problem["taxon_ids"][i] for i in component)
            for component in _components(problem, best)
            if len(component) > 1 and sum(weights[i] for i in component) > 0
        }
        for component in _components(problem, separation):
            mass = float(sum(weights[i] for i in sorted(component)))
            if mass == 0:
                continue
            group = frozenset(problem["taxon_ids"][i] for i in component)
            irreducible = all(best[i, j] < RESOLUTION_THRESHOLD for i in component for j in component)
            reward = 1. if len(component) == 1 or irreducible else .5
            targets[group] = mass, reward
        correct = set(claims) & set(targets)
        false = len(set(claims)-set(targets))
        mechanism = sum(targets[group][0]*targets[group][1] *
                        (.2+.8*max(0., 1-abs(claims[group]-targets[group][0])/ABUNDANCE_TOLERANCE))
                        for group in sorted(correct, key=lambda g: tuple(sorted(g))))
        mechanism *= len(correct)/max(1, len(claims))
        if not valid or abstain:
            mechanism = 0.
        if kind == "out_of_library":
            scientific = float(valid and abstain)
            false = len(claims)
            mechanism = 0.
        else:
            scientific = mechanism
        rows.append(dict(kind=kind, seed=seed, valid=valid, scientific=scientific,
                         mechanism=mechanism, false=false, claimed=len(claims),
                         refusal=float(valid and abstain and kind == "out_of_library"),
                         coverage=float(bool(correct) and kind != "out_of_library"),
                         intrinsic_group_count=len(intrinsic) if kind != "out_of_library" else 0,
                         intrinsic_group_correct=len(intrinsic & correct) if kind != "out_of_library" else 0,
                         calls=sequencer.calls, panel_counts=dict(sequencer.panel_calls)))
    metrics = dict(valid=float(all(row["valid"] for row in rows)),
                   feasibility_rate=float(np.mean([row["valid"] for row in rows])), per_world=rows)
    for prefix, indices in (("development", DEV), ("heldout", HELD)):
        panel = [rows[i] for i in indices]
        library = [row for row in panel if row["kind"] == "out_of_library"]
        compositions = [row for row in panel if row["kind"] != "out_of_library"]
        false, claims = sum(row["false"] for row in panel), sum(row["claimed"] for row in panel)
        groups = sum(row["intrinsic_group_count"] for row in panel)
        floor = len(library)/len(panel)
        score = max(0., (np.mean([row["scientific"] for row in panel])-floor)/(1-floor))
        metrics.update({
            f"{prefix}_mechanism_score": float(np.mean([row["mechanism"] for row in compositions])),
            f"{prefix}_false_discovery_rate": false/max(1, claims),
            f"{prefix}_false_discovery_count": false,
            f"{prefix}_claim_count": claims,
            f"{prefix}_alias_resolution_rate": sum(row["intrinsic_group_correct"] for row in panel)/max(1, groups),
            f"{prefix}_alias_group_count": groups,
            f"{prefix}_correct_refusal_rate": sum(row["refusal"] for row in library)/len(library),
            f"{prefix}_refusal_world_count": len(library),
            f"{prefix}_discovery_coverage": float(np.mean([row["coverage"] for row in compositions])),
        })
        metrics["combined_score" if prefix == "development" else "heldout_scientific_score"] = float(score) if metrics["valid"] else 0.
    return metrics
