# OpenVocabularyReactionNetworkDiscovery — scientific admission blocked

## Current counterexample

`references/signature_probe.py` is a self-contained, public-input candidate. It constructs
legal graph neighbors, caches a paid response by the multiset of broken/formed bond-type
channels, and explores reachable edges using that cache. It imports only itertools and
contains no evaluator constants or private-panel reads.

On the current four-heavy-atom oracle it scores development/heldout 1.0/1.0, development
raw recovery 1.0, with 8.833333 mean development probes and at most 13 per world. This
independently reproduces the [September 9 maintainer counterexample](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/16#issuecomment-5594778785).

Reproduce through the actual sandbox:

```
uv run python -m sle eval --task OpenVocabularyReactionNetworkDiscovery --allow-uncertified \
  --candidate benchmarks/Chemistry/OpenVocabularyReactionNetworkDiscovery/references/signature_probe.py --timeout 30
```

## Why the shortcut works

Graph energy is an additive bond-strength sum. A one-delete/one-add channel changes energy
only through the two exchanged bond types, so the uphill term contains no additional graph
information. All 72 legal directed edges collapse to 13 channel signatures. The 24-query
budget is therefore not constraining. The old claim that complete recovery was
"evaluator-only" is false; reducing the budget from 80 to 24 did not repair the degeneracy.

## Reference and baseline

The independent active-frontier reference uses novelty priority, qualitative bond strength
and branching priority. Its development raw score is 0.9730176503033645, normalized to
release score 1.0; the new counterexample exceeds its raw recovery. The shipped legal wrong
edge and blanket refusal both score zero. Release scores are clipped; the historical
unclipped complete-recovery value 1.0421807272444035 is not current release headroom.

## Superseded shortcut evidence

The 1024-ordering BFS scan reaches raw 0.946080715974333. Ordering and ablation checks
remain executable, but cannot establish mitigation after the stronger signature-cache
counterexample. No frontier-model or long-horizon calibration has been run.

## Required redesign

A new mechanism must break channel-only equivalence through scientifically interpretable
graph-dependent energetics and be tested against descriptor-fit as well as signature-cache
policies. Merely adding per-edge random noise or enlarging the grammar while retaining the
same 13-parameter oracle is insufficient. That redesign is not claimed by this update;
the PR remains scientifically blocked. Graph canonicalization, malformed artifacts,
refusal, charged budgets and sandbox isolation continue to be tested independently.
