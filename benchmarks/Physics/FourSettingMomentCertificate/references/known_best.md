# FourSettingMomentCertificate — current witnesses

## Reproducing

Run the task's reference through sle eval. Tests expand both references/level_one_certificate.json
and references/full_pool_certificate.json using exact Fraction arithmetic; no SDP runs in the oracle.

## Reference and anchors

The public-input reference adapts BellBoundCertificate's numerical Gram search, exact rational
identity repair, diagonal PSD repair and LDL squares. All supplied coefficients are checked exactly.
The zero anchor is the exact level-one optimum 5/8: a matching PSD unit-diagonal
moment matrix in level_one_moment_matrix.json attains the same value. Tests verify both sides. The score-one anchor is the included
24-word-pool certificate 0.45533067671165467, a computed witness, not a published optimum.
The pool is 16 mixed A_i B_j words and eight explicitly listed same-party words.
The mixed terms cover all setting pairs; the same-party terms keep both orders of the
disjoint pairs (0,1) and (2,3) on each party. This is a builder-chosen truncation, not an
optimal or exhaustive hierarchy. Omitted pairs are not claimed scientifically irrelevant;
alternative pools need independent comparison before a difficulty claim.

## Ablation ladder and shortcut probes

A Python 3.12 / NumPy 1.26.4 / SciPy 1.14.1 builder probe gave:

| basis | bound | score |
|---|---:|---:|
| baseline triangle SOS | 4 | 0 |
| old pairing shortcut, no nonzero extras | 3.5 | 0 |
| level one, no extras | 0.625 exactly | 0 |
| k=8 reference | 0.5714453258 | 0.255848 |
| k=12 reference | 0.5255800974 | 0.511449 |
| k=16 reference | 0.4588295476 | 0.971947 |
| full k=24 pool witness | 0.4553306767 | 1 |

Reference mean: 0.579748. The numerical solver may vary across SciPy versions;
the exact checker and the two stored anchors do not. The k=16 result is near the full-pool
witness, so this is not a claim of uniform remaining headroom across budgets.

## Construction errors

The old reference contained zero coefficients on every extra moment; its entire pairing ladder
was level one and the same-party-only pool failed to improve the free 5/8 bound in our probe.
Changing only the score from affine to logarithmic did not repair that defect. This revision
changes the pool and reference method, and removes the misleading published_target_bound key.
The solver/algebra lineage is explicitly BellBoundCertificate. The old shortcut is retained
as references/pairing_shortcut.py for regression, with unused padding removed during the test.

## Robustness

Malformed weights, floats, unreduced words, out-of-pool words and incorrect identities fail closed.
Anchor certificates are expanded exactly. No measurement of model robustness is claimed.

## Model draws

Not run. Lineage and construction status are incomplete_legacy. External quantum-information
review and difficulty calibration remain pending; no frozen run evidence is added.
