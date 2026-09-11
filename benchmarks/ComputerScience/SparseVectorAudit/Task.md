# SparseVectorAudit: does this deployed sparse vector technique keep the privacy it claims?

## 关系与区别 / How this differs from the nearest tasks in this repository

- **`ParticlePhysics/LookElsewhereAnomaly`** is the other task about selection: a local excess
  found by scanning many windows is not a global discovery. Here the scan is yours. You choose
  which pairs of inputs to run and which set of outputs to look at, and the largest ratio among
  everything you looked at is biased upward in the same way. The data are not handed to you. They
  are runs you pay for, and the answer is not a significance but a witness that the oracle scores
  exactly.
- **`Mathematics/HeavyTailEvidence`** and **`ParticlePhysics/DiscrepantMeasurements`** also decide
  what a body of measurements supports. Their claims are about distributions in nature. The claim
  here is a mathematical guarantee made by a piece of software, and it quantifies over every pair
  of neighbouring inputs and every set of outputs. One counterexample refutes it, and no amount
  of sampling proves it.
- **`CausalDiscovery/InterventionalSCM`** and **`Algorithm/GraphFromDistances`** buy queries under
  a budget to recover a structure. Nothing is recovered here. The product is a single inequality
  that fails, or a refusal.

No other task in this repository concerns differential privacy or the audit of an implementation
against its specification.

## The question

A data curator answers a stream of counting queries with the sparse vector technique,
AboveThreshold with a cutoff (Dwork et al. 2009; Lyu, Su and Li 2017), and claims that the
deployed implementation is (epsilon, delta)-differentially private with epsilon 1 and delta
0.001. You are given the specification the curator says was implemented, and you may run the
deployed implementation on query vectors of your choice. Each run costs one unit of a budget of
200000 runs. Either name a violation or say that you found none. A violation is two
neighbouring query vectors and a set of outputs whose probabilities break the claimed
inequality.

## What makes it hard

- **The specification is tight.** Implemented exactly as specified, the mechanism is epsilon-DP.
  It still reaches a loss of 0.90 on some pairs and events, and those events have a mass of one to
  two per cent on one side and under one per cent on the other. Estimated from counts, many pairs and many events show a loss above epsilon
  somewhere by chance. The largest plug-in ratio among everything you tried is a biased estimate,
  and a claim built on it is a false discovery in a world where the claim holds.
- **Delta is part of the claim.** An event whose probability is below delta can have any ratio at
  all and still not break (epsilon, delta). A pure-DP audit that reads an infinite count ratio as
  a violation is wrong whenever the event is that rare.
- **Violations can be small.** Where the deployed implementation does break the claim, the loss
  can sit a quarter of epsilon above it, on an event of well under one per cent on one side.
  Certifying that from counts can cost tens of thousands of runs per side, and those runs come out
  of the same budget as your search for the pair.
- **The deployment is not the specification.** The implementation behind `sample` may differ from
  the specification in ways that are not published. Some of those differences break the claim.
  Others do not, because the outputs they change are rarer than delta. The specification tells you
  what the deployed code should do, and it does not tell you where to look.

Twelve development worlds, each with its own number of queries, cutoff and deployed
implementation. In five the claim holds and in seven it fails. An implementation that differs
from the specification can still satisfy the claim. Nothing in the public problem says which
worlds are which.

## What you implement

```python
def audit(problem, sample):
    ...
    return {"verdict": "violation", "dataset": [...], "neighbour": [...],
            "event": ["FFT", "FFFT"], "confidence": 0.8}
```

### `problem`: every key you are given

| key | meaning |
|---|---|
| `n_queries` | the number of queries in a vector, 8 to 12 |
| `cutoff` | the number of outputs T after which the mechanism halts, 1 to 3 |
| `threshold` | 50, the public threshold |
| `query_min` | 0, the smallest allowed query answer |
| `query_max` | 100, the largest allowed query answer |
| `epsilon` | 1.0, the claimed epsilon |
| `delta` | 0.001, the claimed delta |
| `threshold_noise_scale` | the specified scale b of the threshold noise, 2/epsilon |
| `query_noise_scale` | the specified scale b of each query's noise, 4 * cutoff / epsilon |
| `sample_budget` | 200000, the runs you may spend in this world |
| `output_patterns` | every possible output string, in a fixed order |
| `algorithm` | prose: the specification, AboveThreshold with a cutoff; the threshold noise is drawn once and is not redrawn after an output T |
| `noise_model` | prose: DLap(b) is the discrete Laplace distribution with probability proportional to exp(-\|x\| / b) |
| `adjacency` | prose: two query vectors are neighbours when they differ and every answer differs by at most one, in either direction, independently per query |
| `claim` | prose: P[M(q) in S] <= exp(epsilon) * P[M(q') in S] + delta for every neighbouring pair and every set S |
| `implementation_model` | prose: `sample` runs the implementation actually deployed, which may or may not be the specification |
| `sample_model` | prose: what `sample` returns and costs |
| `answer_format` | prose: what a violation must contain |

An output is a string of T and F, one letter per query answered before the mechanism halted. It
ends at the cutoff-th T or after the last query.

### `sample(queries, n)`

Runs the deployed implementation `n` times on `queries`, a list of `n_queries` integers in
`query_min`..`query_max`, and returns a dict from output string to count. `n` must be an integer
from 1 to 200000, and each call is charged `n` runs. Runs are independent. Calling the same vector
again gives fresh runs, and the counts do not depend on the order in which you run different
vectors. Spending past `sample_budget` raises and the world scores zero, so count your runs.

### What you return

| key | meaning |
|---|---|
| `verdict` | `"violation"` or `"no_violation"` |
| `dataset` | required for a violation: a query vector, `n_queries` integers in `query_min`..`query_max` |
| `neighbour` | required for a violation: a query vector that differs from `dataset` and is within one of it at every position |
| `event` | required for a violation: a non-empty list of distinct strings from `output_patterns` |
| `confidence` | in `[0, 1]`; clipped |
| `abstain` | `True` is accepted as a synonym for the no_violation verdict |

The inequality is checked in both orders, so it does not matter which vector you call which.
Anything malformed scores that world zero. It is never an infrastructure failure.
`sle.contract_lint` is importable and free to call for shape checks. It costs no run.

## How you are scored

The oracle knows the deployed implementation and computes the two probabilities of your event
exactly. The privacy loss of the witness is the larger over the two orders of
ln((P[M(D) in S] - delta) / P[M(D') in S]). It is minus infinity when P[M(D) in S] is at most
delta, and infinity when P[M(D') in S] is zero while P[M(D) in S] exceeds delta. Nothing in the
score is a statistical estimate.

- **A world where the claim fails.** A witness whose loss L exceeds epsilon scores
  `(min(L, 2 epsilon) - epsilon) / (min(A, 2 epsilon) - epsilon)`, clipped to [0, 1]. Here A is
  the loss of the strongest witness the builder found for that implementation, so a witness at A
  or at twice epsilon scores 1. Declining scores 0. A witness whose loss is at most epsilon is a
  false discovery and scores -1.
- **A world where the claim holds.** Declining scores 1 and is a correct refusal. Every witness
  is a false discovery and scores 0.

A false witness therefore costs one world wherever it is made. `combined_score` is the mean over
the development worlds, renormalised so that **declining every world scores exactly 0.0**. Negative
values clip to 0, so claiming a violation in every world also scores 0.0. `confidence` feeds only
the calibration axis. It cannot turn a false discovery into anything else.

Reported separately, never averaged into one number:

FDR is false valid violation claims divided by all valid violation claims, with explicit count
and denominator metrics. With zero claims the stored numeric placeholder is 0 and the
denominator is 0; reports must mark FDR unavailable. `all_world_false_claim_fraction` preserves
the distinct fraction of worlds receiving a false claim. Mechanism strength and refusal also
have explicit denominators. Every world in both splits must execute validly for task-level
`valid=1`; a partial candidate failure makes the combined score zero.


`development_witness_strength` · `development_false_discovery_rate` ·
`development_correct_refusal_rate` · `development_discovery_coverage` ·
`development_confidence_calibration` · `development_mean_samples_used` ·
`development_raw_mechanism`

A sealed held-out set of six further worlds, two where the claim holds and four where it fails,
is scored too, under the same keys with the `heldout_` prefix, and is not visible to a searcher.
`per_instance` carries one row per world.

## Independent fixed Linux method measurements (2026-09-11)

| Frozen candidate | Development | Held out | Dev false/claims | Held false/claims |
|---|---:|---:|---:|---:|
| Baseline | 0.000000 | 0.000000 | 12/12 | 6/6 |
| Complete positional reference | 0.819398 | 0.729870 | 0/6 | 0/3 |
| First position only | 0.570283 | 0.479870 | 0/5 | 0/2 |
| No scan | 0.176793 | 0.229870 | 0/2 | 0/1 |
| No library | 0.571429 | 0.500000 | 0/4 | 0/2 |
| Positional, no confirmation | 0.322314 | 0.000000 | 2/7 | 5/6 |
| Historical strongest fixed shortcut | 0.427426 | 0.000000 | 1/6 | 2/4 |

All seven candidates ran twice at clean source `5c5b358cdf47ec3ce1319fc722cc88bd4afcb0f2`.
Every one of the 14 runs was valid in all 12 development and six held-out worlds; each complete
metric pair was identical. Runtime: Linux Python 3.8.10, NumPy 1.24.4, SciPy 1.10.1, numerical
thread counts one, 300-second task timeout. The runtime source hash is
`e29d3b1d7b0e0f9f5b1b09a8c0a45ace098ad8790547d0333c1940e0a421bea9`; the only `sle/*.py`
change from main3069479 is the contributor's DataPrivacy logical-domain mapping. Full metrics
are private; scalar measurements and exact source hashes are in
`.research/pr80_method_qualification_2026-09-11.json`.

The full reference reaches 0.8193980000000003; both declared probes stay below the unchanged
10% margin threshold 0.7374582000000003. Each substantive capability ablation lowers the
score: later-position scanning, scanning as a whole, the library, and confirmation. This is
fixed candidate-method qualification, not a model difficulty or iteration result. The old
318-policy grid is author provenance; only its fixed reported strongest alternative and the
stronger positional no-confirmation alternative were re-evaluated here, without new grid
selection, seed tuning or changed worlds. True frontier first-proposal evidence is still missing.

## Historical construction measurements

The following numbers are the contributor's in-process measurements at PR head
`4bb95061846a28a3025f4eb05cdd52210e12b11a`, not independent Linux qualification. The old
first-query-only method is retained as an ablation. The current method candidate is
`verification/reference_positional.py`, a standalone packaging of the existing all-position
method (historical 0.819 development / 0.730 held out); it leaves finite sampling and event
selection headroom, without intentionally excluding query positions. Current fixed sandbox measurements are recorded below; actual frontier first proposals remain pending.

## Where the original first-query scale sat

The original first-query audit scores 0.570 on the development split and 0.480 held out. It makes no false
discovery and declines every world where the claim holds. It names a violation in five of the
seven development worlds where the claim fails and in two of the four held out. Re-drawn with
eight other seeds for the runs, it averages 0.446 and 0.440 and never makes a false discovery.
It is not the ceiling, and a better audit of the same budget exists.

The baseline in `solution.py` scores 0.000. It claims a violation in every world and is wrong in
every one. Declining everything scores 0.000.

A sweep of 318 low-effort strategies was scored on the same worlds. They guess witnesses without
running anything, or screen fixed input pairs at up to 24000 runs a vector and claim the largest
plug-in loss above a threshold, with or without a confirmation. The best of them reaches 0.427 on
the development split, 75 per cent of the reference, and 0.000 held out. It claims the largest
plug-in loss on its screening counts without confirming it. Re-drawn with the same eight other
seeds, it averages 0.063 and makes fifty false discoveries.

## Rules

- Only edit `solution.py`; keep `audit(problem, sample)`.
- `sle.contract_lint` is importable and free to call for shape checks. It costs no run.
- Do not read `verification/` or `frontier_eval/`.
