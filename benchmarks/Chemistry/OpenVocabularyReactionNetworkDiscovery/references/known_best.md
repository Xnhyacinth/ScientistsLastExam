# OpenVocabularyReactionNetworkDiscovery — graph-dependent barriers

## September 12 descriptor-fit counterexample

`references/descriptor_fit_probe.py` is self-contained and uses only public graphs and
paid responses at runtime. Channel-signature indicators, reactant bond-type counts and
degree second moments fit the current barrier sufficiently well to recover both splits.
It was designed after source inspection, with four acquisition-order variants tried;
it is not a clean-room first proposal or model calibration.

Linux sandbox: **combined 1.0, heldout 1.0, FDR 0, valid 1**. Development raw is
**0.9788421717171715**, above reference **0.9316717474829289**. Supported worlds use
24 probes. Run the same `sle eval` command below with `references/descriptor_fit_probe.py`.
The machine-readable shortcut guard now includes this stronger counterexample and fails.

Every legal single-edge deletion/addition preserves cycle count within the connected
component. Cycle terms therefore do not establish additional graph-identification
complexity. Closing the old signature cache was insufficient; scientific admission stays
blocked until a meaningful task redesign and fresh calibration are independently checked.


## Current shortcut probe

`references/signature_probe.py` still caches a paid response by the multiset of
broken/formed bond-type channels. After the barrier was given reactant/product
cycle counts, a degree second moment, and spectator-bond energy, that cache is
no longer an exact table.

Measured on this wave (in-process `evaluate`):

| candidate | combined | development raw | heldout mechanism | mean probes |
|---|---:|---:|---:|---:|
| baseline (one legal false edge) | 0.000000 | — | — | 0 |
| signature_probe.py | 0.880621 | 0.860243 | 1.000000 | 8.166667 |
| independent reference | 1.000000 | 0.931672 | 1.000000 | ≤24 |

The probe remains below the reference on the release score and on development raw.
It does not reach the clipped ceiling.

Reproduce through the actual sandbox:

```
uv run python -m sle eval --task OpenVocabularyReactionNetworkDiscovery --allow-uncertified \
  --candidate benchmarks/Chemistry/OpenVocabularyReactionNetworkDiscovery/references/signature_probe.py --timeout 30
```

## Why the old 13-cell table is closed

Graph energy is still an additive bond-strength sum, so a one-delete/one-add
*energy difference* still cancels to the exchanging pair. The barrier now also
depends on rings and crowding on the rest of each graph and on the spectator
bonds of the reactant. The same broken/formed channel signature is therefore
not a constant barrier (17 of 19 type signatures vary; spread up to ~59 reduced
kJ/mol), and support vs `barrier_limit` can flip with the rest of the graph.

## Reference and baseline

The independent active-frontier reference uses novelty priority, qualitative
bond strength and branching priority. Its development raw score is 0.931672,
normalized to release score 1.0. The shipped legal wrong edge and blanket
refusal both score zero. Release scores are clipped.

## Superseded shortcut evidence

Before the topology term, `signature_probe.py` scored development/heldout 1.0/1.0
with at most 13 probes (mean 8.833333), reproducing the 9 September maintainer
counterexample. A 1024-ordering BFS scan then reached raw 0.946080715974333, and
a novelty-first reference raw was 0.9730176503033645. Those numbers are not
current. Ordering sweeps remain executable but are not a hardness claim.

The first descriptor replay exposed one-ULP variation in mechanism recovery under
parallel executions. The candidate now reports barriers to ten decimal places, within
the unchanged 1e-9 evidence tolerance. Six parallel full sandbox replays then matched
in every metric, with both split scores still one. This changes candidate output
precision only; the oracle, scientific score and evidence predicate were not relaxed.
