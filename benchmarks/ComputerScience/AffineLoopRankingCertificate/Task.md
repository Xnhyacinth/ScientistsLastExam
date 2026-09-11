# AffineLoopRankingCertificate — prove a nested loop ranks, do not just run it

## The question

A nested-reset rational affine transition system over real states is published in full.
Each transition has linear guards `g_i · x + d_i ≥ 0` and an update `x := A x + b`.
These loops are the Bradley–Manna–Sipma nested-reset family: an inner progress step
together with a reset that copies a large outer block onto the inner block. A **single**
linear ranking function is incomplete on this family (the Colón–Sipma / Podelski–Rybalchenko
1-ranking Farkas LP is infeasible). Submit a **lexicographic tuple** of linear ranking
functions that proves every transition descends in the lexicographic order.

Submit exact rationals. Each component's slope `r` must have 1-norm exactly 1 so that
component decreases are comparable. Floats are rejected, not rounded. The implications
are proved by Farkas multipliers, not by sampling states.

## What you implement

```python
def build_ranking(instance):
    ...
    return {
        "components": [{"r": [[num, den], ...], "s": [num, den], "delta": [num, den]}, ...],
        "decrease_index": [int, ...],  # one index per transition
        "nonneg_lambdas": [  # [transition][component][guard]
            [[[num, den], ...], ...],
            ...
        ],
        "decrease_lambdas": [
            [[[num, den], ...], ...],
            ...
        ],
    }
```

Let `ρ_j(x) = r_j · x + s_j`. For transition `t` with active index `i = decrease_index[t]`:

1. For every `j ≤ i`, `ρ_j ≥ 0` on the guard polyhedron of `t` (Farkas with `nonneg_lambdas[t][j]`).
2. For every `j < i`, `ρ_j(x) - ρ_j(A_t x + b_t) ≥ 0` on that polyhedron (weak prefix).
3. `ρ_i(x) - ρ_i(A_t x + b_t) ≥ delta_i > 0` on that polyhedron.

Every component must be the active decrease of at least one transition. At most
`max_components` components. Four nested-reset systems use dimensions 6, 8, 9 and 12
(two 2-level loops and two 3-level loops). Progressing blocks use overcomplete mixed-sign
guards, not `n` coordinate inequalities, so Farkas multipliers are search variables.

The score of a valid certificate is
`min(max(0, (Q - Q0) / (Q* - Q0)), 1)`, averaged over the systems, where `Q` is the sum
of the proven component deltas, `Q0` is `n_levels / 10000`, and `Q*` is an evaluator-only
verified nested lex ranking (independent exact phase rankings). `Q*` is **not** a
1-ranking Farkas LP optimum: that LP is infeasible on every instance. A failed certificate
scores zero. Rational transitions are checked over all real states.

### `instance` keys

| key | meaning |
|---|---|
| `name` | instance label |
| `dimension` | 6, 8, 9 or 12 |
| `transitions` | list of `{name, guards, A, b}`; `guards` are `{g, d}` with `g·x + d ≥ 0` |
| `max_numerator` | 10**18 |
| `max_denominator` | 10**18 |
| `max_components` | 3 |

### submission keys

| key | meaning |
|---|---|
| `components` | lex tuple; each entry has slope `r` (1-norm 1), constant `s`, positive `delta` |
| `decrease_index` | which component strictly decreases on each transition |
| `nonneg_lambdas` | Farkas multipliers for `ρ_j ≥ 0`, indexed `[transition][component][guard]` |
| `decrease_lambdas` | Farkas multipliers for prefix non-increase and the active decrease |

## Relation and distinction

- Not `DiscreteGeometry/SpherePackingCertificate`: that certifies a Cohn–Elkies packing
  bound. This certifies lexicographic descent of an affine program.
- Not `QuantumFoundations/BellBoundCertificate`: that is an exact SOS bound on a Bell
  functional. This is a discrete ranking tuple for a loop.
- Not `InformationTheory/ShannonCapacityCertificate`: that certifies an interval for an
  odd-cycle capacity. This certifies program termination ranking.
- Not `Algorithm/GraphFromDistances`: that recovers a graph from queries. This submits a
  proof of ranking, not a graph.

`ControlTheory/LyapunovDecayCertificate` is not in this inventory. Other exact-certificate
neighbours on main are SpherePackingCertificate, BellBoundCertificate and
ShannonCapacityCertificate. They bound geometric, quantum or information-theoretic objects;
this task certifies nested affine-program descent.

## Scoring

The formula above uses each instance's hidden verified lex quality `Q*`. Malformed
submissions, floats, a ranking with nonunit 1-norm, a 1-ranking that does not cover every
reset, or false Farkas identities score zero.
`sle.contract_lint` is importable and free to call for shape checks; the evaluator verifies
the lex Farkas identities independently in exact arithmetic.
`valid` is 1.0 only when every instance has a valid certificate, otherwise 0.0.
