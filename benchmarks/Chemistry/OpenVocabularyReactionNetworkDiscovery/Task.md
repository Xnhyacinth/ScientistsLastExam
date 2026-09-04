# OpenVocabularyReactionNetworkDiscovery

## Scientific question

Starting from a small heavy-atom inventory and one seed molecule, can an active policy construct
previously unlisted molecular graphs and directed elementary-reaction edges, recover the supported
network and its activation energies, and decline when the public mechanism class has no supported
edge or is inadequate?

This is not `ReactionMechanismFitting` with a longer reaction list. There is no candidate species
table and no candidate edge table. The submitted program must create the vertices and edges it
wants to probe. The current cell uses a small graph grammar so that its oracle is exact and fast;
future waves can enlarge the atom inventory and reaction grammar without changing the artifact.

The oracle is a deterministic analytic graph-reaction benchmark. Its energies are not quantum
chemistry, its atoms omit hydrogens and charge, and a high score is not evidence for a real
reaction mechanism.

## What to implement

```python
def discover_reaction_network(problem, probe):
    ...
```

Return either a network:

```python
{
    "species": [
        {"atoms": ["C", "C", "N", "O"], "bonds": [[0, 1, 1], ...]},
        ...,
    ],
    "reactions": [
        {"reactant": 0, "product": 1, "activation_energy": 54.2},
        ...,
    ],
    "abstain": False,
    "confidence": 0.8,
}
```

or `{"abstain": True, "confidence": 0.0}`.

`confidence` is confidence that the submitted network is supported. It must be a finite number in
`[0, 1]`; `abstain` must be a Boolean. `sle.contract_lint` is available as a free shape checker
and consumes no probe budget.

### Species and canonical identity

Each species has exactly two fields:

- `atoms`: two to six heavy-atom symbols. In this frozen cell every species must have exactly the
  multiset in `atom_inventory`.
- `bonds`: undirected `[left_atom_index, right_atom_index, order]` triples. Only order 1 is allowed.
  The graph must be connected, have no duplicate bond, and obey `element_valence_bounds`.

Atom indices are not chemical identities. The evaluator canonicalizes a coloured graph over all
element-preserving atom permutations. Two isomorphic graphs are one species, and submitting both
fails closed rather than earning duplicate credit. Directed edges are canonicalized by their
canonical reactant and product graphs; duplicate edges also fail closed.

Every claimed reaction indexes two different submitted species. It must obey the public
`elementary_edge_rule`: delete one single heavy-atom bond and form one different single bond while
preserving connectedness. `activation_energy` must be finite and in `[0, 250]` reduced kJ/mol.

## Active probe

One charged query has this form:

```python
probe({"reactant": species_graph, "product": species_graph})
```

The proposed graphs need not have appeared before. A valid response contains:

- `status`: `supported`, `unsupported`, or `model_inadequate`;
- `activation_energy`: the exact value for a supported edge, otherwise `None`;
- `budget_cost`: 1;
- `remaining_budget`: calls left.

Malformed graphs, non-elementary edges, caught callback violations, and calls after `probe_budget`
invalidate that world. Repeating an edge costs another call.

## Every public `problem` key

| key | meaning |
|---|---|
| `atom_inventory` | conserved heavy-atom multiset; currently `C, C, N, O` |
| `seed_species` | one valid starting graph, not a list of all possible species |
| `probe_budget` | maximum charged calls, currently 80 |
| `max_claimed_species` | maximum number of submitted canonical species |
| `max_claimed_reactions` | maximum number of submitted directed edges |
| `allowed_bond_orders` | bond orders supported by this cell, currently `[1]` |
| `element_valence_bounds` | graph-validity degree bounds by element |
| `elementary_edge_rule` | the allowed one-bond-exchange grammar |
| `probe_response` | meanings of the three response statuses |
| `abstain_when` | the two scientifically correct refusal cases |

There are deliberately no `candidate_species` or `candidate_reactions` keys.

## Evaluation

Supported worlds score a mechanism recovery value made from canonical reaction F1 (65%), species
F1 (20%), and activation-energy accuracy on correctly recovered edges (15%). Null and
model-inadequate worlds score one only for refusal. The public `combined_score` averages those
world outcomes and subtracts the credit earned by declining every world. Consequently an
always-abstaining policy is valid and scores exactly `0.0`; an exhaustive charged-probe witness
scores `1.0`.

The evaluator reports the four discovery axes separately:

- `development_mechanism_recovery` and `heldout_mechanism_recovery`;
- `development_false_discovery_rate` and `heldout_false_discovery_rate`;
- `development_calibrated_refusal_score` and `heldout_calibrated_refusal_score`, which require
  both a correct refusal and low confidence in a supported network; raw
  `development_correct_refusal_rate` and `heldout_correct_refusal_rate` remain visible;
- `development_attempted_discovery_rate` and `heldout_attempted_discovery_rate` (also exposed as
  `development_discovery_coverage` and `heldout_discovery_coverage`).

It also reports general confidence calibration, mean charged probes, `development_mechanism_score`,
`heldout_mechanism_score`, feasibility, and evaluator-only per-instance rows. A high recovery
score cannot erase false edges, blanket refusal, or failure to attempt discovery.

## Rules

- Edit only `solution.py`; keep `discover_reaction_network(problem, probe)`.
- Use at most `probe_budget` calls and submit no more than the public size bounds.
- Deterministic CPU code only; standard library/NumPy/SciPy, no network or process creation.
- Do not read `verification/` or `frontier_eval/`.
- Treat this cell as a synthetic algorithmic test. Real-mechanism claims require electronic
  structure, kinetic validation, experimental products, uncertainty analysis and independent
  confirmation outside this benchmark.

References: Unsleber and Reiher, *J. Chem. Theory Comput.* (2022), SCINE Chemoton 2.0,
DOI `10.1021/acs.jctc.2c00193`; Martínez-Núñez et al., *J. Comput. Chem.* (2021), AutoMeKin2021,
DOI `10.1002/jcc.26734`.
