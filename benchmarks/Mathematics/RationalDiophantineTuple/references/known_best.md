# RationalDiophantineTuple — executable reference frontier

The scoring reference is the first positive rational Diophantine sextuple reported by
Phil Gibbs:

```
{11/192, 35/192, 155/27, 512/27, 1235/48, 180873/16}
```

`verification/evaluator.py:_reference_size` sends this witness through the same exact
oracle used for submissions; `tests/test_rational_diophantine_tuple.py` independently
pins its validity, cardinality, and score. The anchor is therefore recomputable rather
than an unchecked size literal.

Known status:

- Gibbs, *Some Rational Diophantine Sextuples*, arXiv:math/9902081, gives positive
  sextuples: https://arxiv.org/abs/math/9902081
- Dujella, Kazalicki, Mikić, and Szikszai, *There are infinitely many rational
  Diophantine sextuples*, arXiv:1507.00569, proves infinitely many sextuples:
  https://arxiv.org/abs/1507.00569
- Epoch AI's FrontierMath open-problem page states that no rational Diophantine septuple
  is known: https://epoch.ai/frontiermath/open-problems/diophantine-septuple

Matching size six is reconstruction and scores 1.0. A verified size-seven submission
scores 1.5, but it would need independent expert and provenance review before any claim
of discovery. It is not known that size seven exists, and there is no theorem guaranteeing
arbitrarily large tuples or indefinitely increasing scores. The 64-entry output bound is
a benchmark resource envelope, not a mathematical upper-bound claim.
