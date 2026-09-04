# RationalDiophantineTuple — candidate-wave evidence

All scores below are recomputed by the package's exact oracle. They are benchmark evidence,
not a claim that this repository discovered any of the published tuples.

## 1. Reference method and complete configuration

`verification/reference_tuple.py` is an independently runnable, truth-blind candidate. It returns
the first published positive rational Diophantine sextuple reported by Phil Gibbs:

```
{11/192, 35/192, 155/27, 512/27, 1235/48, 180873/16}
```

Reproduce it through the same isolated protocol used for submissions:

```
python -m sle eval --allow-uncertified --task Mathematics/RationalDiophantineTuple \
  --candidate benchmarks/Mathematics/RationalDiophantineTuple/verification/reference_tuple.py
```

The hash-bound candidate panel requires at least 2 distinct reduced rationals and accepts at most 64 submitted
pairs, with at most 1000 decimal digits per integer and 16000 integer digits in total. Fractions
are reduced, denominator signs normalized and equivalent entries de-duplicated before exact pair
checking.

## 2. Baseline and development scores

There is one exact construction objective rather than a sampled development set. The shipped
baseline is the classical integer quadruple `{1, 3, 8, 120}`.

| candidate | exact size | valid | combined score |
|---|---:|---:|---:|
| shipped quadruple | 4 | 1 | 0.0 |
| quadruple plus Euler's `777480/8288641` extension | 5 | 1 | 0.5 |
| independently runnable Gibbs sextuple | 6 | 1 | 1.0 |

The score is `max(0, (m - 4) / 2)` and is not clipped at one. The panel's 64-entry resource
envelope does impose a representable maximum of 30.0 in this wave.

## 3. Held-out score and generalization boundary

Held-out scoring is not applicable. Feasibility is the universal exact predicate over every pair
in the submitted finite set, so there is no stochastic world sample or hidden split to generalize
across. The evaluator reports the complete result for the submitted artifact. Independent
mathematical and provenance review is still required before treating a size-seven result as a
research discovery.

## 4. Ablation ladder and shortcut probe

This reference is a public construction, not a multi-stage numerical algorithm. Its meaningful
ablation ladder removes one published element at a time:

| ablation or shortcut | size | score | interpretation |
|---|---:|---:|---|
| Gibbs sextuple | 6 | 1.0 | public reference reconstruction |
| remove one element | 5 | 0.5 | exact valid quintuple |
| remove two elements | 4 | 0.0 | weak legal four-element subset; same score as the shipped baseline |
| append a duplicate or equivalent fraction spelling | 6 | 1.0 | canonical de-duplication blocks padding |
| permute all entries | 6 | 1.0 | ordering is not credited |
| change one numerator by one | 6 | 0.0 | exact pair predicate rejects the artifact |

The dominant shortcut is retrieval: published sextuples and parametric sextuple families may be
present in training data. It can reach the reference score of 1.0 but cannot by itself earn the
1.5 associated with a verified septuple. This task therefore must not use reference reconstruction
as evidence of new reasoning or discovery.

## 5. Frontier draw and construction history

No model or API has been run on this package. The first draw remains preregistered for HY3 normal
versus selection-blind calibration after the candidate wave is committed and frozen. Builder
review made the panel the source of score/resource anchors, hash-bound the complete evaluator in
the candidate wave, added an isolated reference candidate and expanded malformed-output coverage.
Consequently there are no model-triggered task edits to report yet. Any later edit after the first
draw must create a new wave or invalidate and rerun the affected calibration.

## 6. Robustness and computational cost

The dedicated suite exercises fourteen malformed return shapes through the Linux candidate
sandbox: null, scalar string, mapping, empty sequence, one- and three-field entries, float, boolean
and string numerators, zero denominator, zero entry, a nonsquare pair, too many entries and an
overlong integer. Each produces `valid = 0` and `combined_score = 0` without an infrastructure
failure. Separate tests pin exact arithmetic, canonical de-duplication, permutation invariance,
determinism, frontier-record identity, panel hashes and reference isolation.

Verification requires `O(m^2)` exact rational multiplications and integer-square checks for
`m <= 64`, with bounded integer and aggregate decimal digits. It uses the Python standard library
only and requires no network, GPU or stochastic seed.

## 7. Limitations and claim boundary

- Gibbs, *Some Rational Diophantine Sextuples*, arXiv:math/9902081, reports positive sextuples:
  https://arxiv.org/abs/math/9902081
- Dujella, Kazalicki, Mikić and Szikszai, *There are infinitely many rational Diophantine
  sextuples*, arXiv:1507.00569: https://arxiv.org/abs/1507.00569
- Epoch AI's FrontierMath open-problem page states the septuple problem and is the direct source
  adapted here: https://epoch.ai/frontiermath/open-problems/diophantine-septuple

Matching size six is public-answer reconstruction. A size-seven submission scores 1.5, but no such
tuple is currently known and any candidate requires independent number-theory and provenance
review. It is not known that size seven exists; there is no theorem guaranteeing arbitrarily large
tuples or indefinitely increasing fixed-wave scores. The 64-entry limit is a safety envelope, not
a mathematical upper-bound claim. The repository currently has no top-level license file, so
redistribution terms for the package must be resolved at repository level before a public release.
