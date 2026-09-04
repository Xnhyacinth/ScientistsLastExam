# RationalDiophantineTuple — construct a larger exact rational tuple

## Scientific background

A rational Diophantine `m`-tuple is a set of distinct, nonzero rational numbers
`{a_1, ..., a_m}` such that `a_i * a_j + 1` is the square of a rational number for
every pair `i < j`. Only off-diagonal products are constrained.

Rational sextuples are known, including infinite families. No rational Diophantine
septuple is currently known. This task asks for the largest exactly verifiable tuple you
can construct. Reproducing a sextuple is useful reconstruction; a verified tuple of size
seven would be a new mathematical result requiring independent expert review.

This package is a graded adaptation of Epoch AI's **FrontierMath: Open Problems** item
"A Rational Diophantine Septuple". It is not a new mathematical problem invented by this
repository. The adaptation adds a legal size-four baseline, an executable public size-six
reference, exact fail-closed resource limits, and immutable-wave provenance. Those additions
make intermediate reconstruction measurable; they do not make a septuple known.

## 关系与区别 / How this differs from nearby repository tasks

- **`Mathematics/CapSetFrontier`** also scores an exact open-record construction, but it has
  several fixed finite-dimensional instances with known lower bounds. This task has one
  cardinality objective and an unresolved existence jump above six.
- **`Mathematics/RamseyLowerBound`** verifies finite graph colourings across several `(s, t)`
  cells. Here the artifact is one set of exact rationals and every pair is checked directly.
- **`Mathematics/Superpermutation`** also permits reconstruction of public records, but its
  coverage condition is finite and improvements shorten a string. Here a score above the
  public reference would resolve an open Diophantine construction problem.
- **`Mathematics/BlackBoxGroupIdentification`** concerns structural discovery under a query
  budget and includes calibrated refusal. This task makes no noisy observations and has no
  refusal axis: a submitted tuple is either exactly feasible or it is not.

No item in the current Frontier-Eng engineering catalogue asks for a rational Diophantine
tuple. The direct external neighbour is the FrontierMath open-problem item named above.

## Your task

Edit **`solution.py`** so it defines:

```python
def construct_tuple() -> list:
    """Return rationals as [[numerator, denominator], ...]."""
```

Each numerator and denominator must be a Python integer; denominators must be nonzero.
The evaluator reduces every fraction canonically before removing duplicates. It then
checks every pair using exact integer arithmetic. Decimal or floating-point values are
not accepted.

## Scoring

Let `m` be the number of distinct reduced rationals in a valid submission. The classical
integer quadruple is the baseline and a published rational sextuple is the executable
reference:

```
score = max(0, (m - 4) / (6 - 4))       # no upper score clamp
```

Thus the baseline scores 0, a valid sextuple scores 1, and any valid tuple larger than
six scores above 1. Invalid output scores 0. The absence of an upper score clamp means a
better verified construction remains visible; it is not a claim that arbitrarily large
rational Diophantine tuples exist.

The fixed wave is nevertheless finite: the 64-entry safety envelope makes its maximum
representable score 30.0. In this repository, `uncapped` means "not clipped at the score-one
reference", not a proof of an infinite mathematical frontier. Only later immutable waves can
extend the benchmark family without rewriting this wave's scores.

## Public reconstruction ladder and shortcut boundary

- the classical integer quadruple `{1, 3, 8, 120}` is valid and scores `0.0`;
- its public Euler extension by `777480/8288641` is a valid quintuple and scores `0.5`;
- Gibbs's published sextuple is the executable reference and scores `1.0`;
- duplicate spellings, permutations and sign-normalized denominator spellings do not increase
  cardinality; invalid pairs score `0.0`.

The quintuple and sextuple are public and may be present in model training data. Reaching `1.0`
can therefore measure retrieval or reconstruction, not new mathematical discovery. No model draw
has yet been run; `flagship`/`T3` is a target review label until frozen HY3 calibration is complete.

## Resource and integrity rules

- Only edit `solution.py`; preserve `construct_tuple()` and the pair-list output format.
- Submit at least 2 distinct reduced rationals and at most 64 rational pairs. Each integer may
  contain at most 1000 decimal digits, and the output may contain at most 16000 integer digits
  in total.
- Entries must be nonzero after reduction. Equivalent spellings such as `[1, 2]` and
  `[2, 4]` count once.
- Standard library only; CPU evaluation.
- Do not read anything under `verification/` or `frontier_eval/`.
