# RationalDiophantineTuple — construct a larger exact rational tuple

## Scientific background

A rational Diophantine `m`-tuple is a set of distinct, nonzero rational numbers
`{a_1, ..., a_m}` such that `a_i * a_j + 1` is the square of a rational number for
every pair `i < j`. Only off-diagonal products are constrained.

Rational sextuples are known, including infinite families. No rational Diophantine
septuple is currently known. This task asks for the largest exactly verifiable tuple you
can construct. Reproducing a sextuple is useful reconstruction; a verified tuple of size
seven would be a new mathematical result requiring independent expert review.

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

## Resource and integrity rules

- Only edit `solution.py`; preserve `construct_tuple()` and the pair-list output format.
- Submit at most 64 rational pairs. Each integer may contain at most 1000 decimal digits,
  and the output may contain at most 16000 integer digits in total.
- Entries must be nonzero after reduction. Equivalent spellings such as `[1, 2]` and
  `[2, 4]` count once.
- Standard library only; CPU evaluation.
- Do not read anything under `verification/` or `frontier_eval/`.
