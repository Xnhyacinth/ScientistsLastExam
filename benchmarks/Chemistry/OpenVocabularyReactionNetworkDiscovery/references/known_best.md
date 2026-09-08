# Current revision and superseded measurements

The 2026-09-08 revision clips release scores to [0,1]. Earlier uncapped scores below
are historical diagnostics, not current release scores. No model calibration has been run.

# Known witnesses and limits

## Reproducing

Run `python -m unittest tests.test_open_vocabulary_reaction_network_discovery`. The evaluator is
deterministic, CPU-only, and all reference probes are charged through the normal callback.

## Reference

`verification/reference_reaction_network.py` performs novelty-first active-frontier search using
the public problem, charged responses, a qualitative bond-strength rank, and public grammar
branching as an information-gain tie-break. With the 24-query budget it scores `1.0`; development
raw world score is `0.9730176503033645`, mean supported-world recovery is
`0.9595264754550469`, FDR is zero, and mean probe use is 16. Complete oracle recovery scores
`1.0421807272444035`, demonstrating uncapped headroom.

## Baseline

The shipped solution returns one legal but confidently wrong fixed edge and scores `0.0` with FDR
`1.0`. A separate no-probe always-abstaining control is valid and also scores exactly `0.0`.

## Difficulty ladder

The measured ladder is fixed wrong edge = blanket refusal = `0.0`, budgeted active frontier =
`1.0`, and evaluator-only complete recovery = `1.0421807272444035`. No HY3 or external-agent
calibration has been run, so task difficulty remains `uncalibrated_candidate`.

## Shortcut probe

The former 80-query exhaustive scan saturated this four-heavy-atom grammar. At budget 24, a
1024-seed SHA256 neighbour-order BFS sweep reaches raw `0.946080715974333`, or
`0.9578902692868527` after normalization to the current reference. A second executable sweep varies
1024 final tie-break seeds around the reference acquisition rule; public branching priority makes
all draws equal to the reference raw score. Removing novelty priority scores
`0.9645472862744551`, removing the barrier surrogate scores `0.9257058383039174`, and removing the
branching tie-break scores `0.996111761955115`. The cell remains finite and analytically enumerable,
so this is mitigation rather than proof of long-horizon hardness.

## Construction history

Review found five degeneracies: exhaustive-query exhaustion, a blanket-refusal shipped baseline,
atom-map-dependent truth for repeated elements, an ordering-only BFS improvement over the first
24-query anchor, and a final-tie ordering improvement over its replacement. The oracle now takes
the minimum barrier over all valid channels. The independent reference uses novelty-first
acquisition, a qualitative bond-strength prior and public branching information gain; it imports
neither evaluator nor panel.

## Robustness and model draw pending

Null and model-inadequate worlds, held-out selectivity changes, malformed shapes, callback-budget
violations, graph isomorphism, ambiguous atom maps, seeded ordering sweeps and standalone runner
isolation are tested. Chemical realism,
larger-grammar scaling, noisy barriers, long-horizon gain, and HY3 model draws remain pending.

## Historical recipe and measurements removed from the candidate prompt

The independent reference prioritizes unseen product graphs, then uses a fixed qualitative
bond-strength rank as a low-barrier surrogate and public grammar branching as an information-gain
tie-break. It depends only on the public problem, its explicit chemical prior, and at most 24
charged probes. Its development raw score is the normalization anchor at `1.0`; an
always-abstaining policy and the shipped confidently wrong legal edge both score `0.0`. The score
is uncapped, so complete oracle recovery can exceed the budgeted reference rather than being hidden
by clipping.

The executable deterministic ladder is fixed wrong edge = blanket refusal = `0.0`, a 1024-ordering
BFS sweep `0.9578902692868527`, budgeted reference `1.0`, and complete evaluator-only recovery
`1.0421807272444035`. Removing novelty priority, the qualitative barrier surrogate, or public
branching priority gives `0.9645472862744551`, `0.9257058383039174`, and
`0.996111761955115`. These are algorithmic ablations inside a four-heavy-atom synthetic grammar;
they do not certify chemical realism or long-horizon difficulty.

