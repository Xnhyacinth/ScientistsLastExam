# AffineLoopRankingCertificate — prove a loop ranks, do not just run it

## The question

A rational affine while-loop over real states is published in full: a conjunction of linear
guards `g_i · x + d_i ≥ 0` and an update `x := A x + b`. A linear ranking
function `ρ(x) = r · x + s` with a positive `delta` is a proof that **every**
guard-satisfying state descends by at least `delta`, independently of any
start state you might simulate.

Submit exact rationals. `r` must have 1-norm exactly 1 so that `delta` is
comparable across directions. Floats are rejected, not rounded: a numerical
LP dump is not a certificate. The two implications are proved by Farkas
multipliers, not by sampling states.

## What you implement

```python
def build_ranking(instance):
    ...
    return {"r": [[num, den], ...], "s": [num, den], "delta": [num, den],
            "nonneg_lambdas": [[num, den], ...],
            "decrease_lambdas": [[num, den], ...]}
```

Let `ρ(x) = r·x + s`. The multipliers must witness, in exact `Fraction`
arithmetic:

1. `ρ ≥ 0` on the guard polyhedron: `r = Σ λ_i g_i` and
   `s - Σ λ_i d_i ≥ 0` with `λ ≥ 0`.
2. `ρ(x) - ρ(Ax+b) ≥ delta` on the same polyhedron, with a second multiplier
   vector `μ ≥ 0`.

Four coupled transitions use dimensions 8, 10, 12 and 16. A differs from identity,
so the decrease depends on the state and the second multiplier vector is necessary.
For a valid certificate the score is
`min(max(0,(delta-1/10000)/(optimal_delta-1/10000)),1)`, averaged over the loops.
The uniform ranking at delta=1/10000 is valid and scores exactly zero. `optimal_delta`
is the exactly verified Farkas LP optimum for each instance, not an arbitrary clip unit.
A failed certificate scores zero. Rational transitions are checked over all real states;
no claim is made that the update maps every integer vector to another integer vector.

### `instance` keys

| key | meaning |
|---|---|
| `name` | instance label |
| `dimension` | 8, 10, 12 or 16 |
| `guards` | list of `{g, d}` with `g·x + d ≥ 0`; each entry `[numerator, denominator]` |
| `A` | affine update matrix, same rational encoding |
| `b` | affine update offset |
| `optimal_delta` | exact rational optimum used for score one |
| `max_numerator` | 10**18 |
| `max_denominator` | 10**18 |

### submission keys

| key | meaning |
|---|---|
| `r` | ranking slope, 1-norm exactly 1 |
| `s` | ranking constant |
| `delta` | positive uniform decrease |
| `nonneg_lambdas` | Farkas multipliers for `ρ ≥ 0`, one per guard |
| `decrease_lambdas` | Farkas multipliers for the decrease |

## Relation and distinction

- Not `ControlTheory/LyapunovDecayCertificate`: that is a **continuous**
  quadratic Lyapunov function for a switched ODE. This is a **discrete**
  linear ranking function for an rational affine loop, with a 1-norm
  normalisation that Lyapunov does not need.
- Not `Algorithm/GraphFromDistances`: that recovers a graph from queries.
  This submits a proof of termination, not a graph.
- Not `Algorithm/MatrixMultiplicationRank`: a bilinear decomposition, not a
  ranking function.

Other exact-certificate neighbours are SpherePackingCertificate, BellBoundCertificate and
ShannonCapacityCertificate. They bound geometric, quantum or information-theoretic objects;
this task certifies program descent. These loop optima are known and the score is clipped.

## Scoring

The formula above uses each instance's exact optimum. Malformed submissions, floats,
a ranking with nonunit 1-norm, or false Farkas identities score zero.
`sle.contract_lint` is importable and free to call for shape checks; the evaluator verifies
both Farkas identities independently in exact arithmetic.
