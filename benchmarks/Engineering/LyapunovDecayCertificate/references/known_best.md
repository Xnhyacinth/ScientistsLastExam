# LyapunovDecayCertificate — scientific admission hold

## Reference

`verification/reference_lyapunov.py` uses only public modes. It searches a finite
catalog of 3-by-3 rational Gram matrices (identity, diagonals, pairwise shears,
two-off-diagonal shears, and a handful of full 5-DOF shears) and, for each Gram
that is a common Lyapunov function at rate 0, maximizes alpha by exact rational
bisection to the public numerator/denominator cap. The trace of each Hurwitz
mode is a public upper bound. The returned rate cannot be increased by 1e-4
while keeping the same Gram feasible.

Current in-process reference score: **0.366560**, all four instances valid.
Proven rates: braid 85424/333333; cycle 107257/333333; twist 55505/333333;
cross 118507/333333. Wall time 1.16 s.

The catalog is a competent Boyd-style witness and is deliberately not a 5-DOF
exhaustive search. That leftover is measured below.

## Baseline

The identity Gram at alpha=1/10000 is legal on every instance and scores exactly zero.

## Ablation ladder

In-process substitutions of the reference catalog / rate search, same evaluator:

| witness | combined |
|---|---|
| identity Gram, exact bisection of alpha | 0.176288 |
| diagonal Grams only, exact bisection | 0.176288 |
| diagonals plus single-plane (pairwise) shears, exact bisection | 0.176288 |
| full catalog, 7-point coarse rate table (no bisection) | 0.283200 |
| full catalog, exact bisection (shipped reference) | **0.366560** |
| same certificates dumped as floats | 0.000000 |
| 5488-point 5-DOF rational scan, den=40 bisection | 0.458200 |

Single-plane shears do not beat identity on this permutation-switched family.
The 3-way catalog terms are worth 0.190 of the reference score; replacing the
coarse rate table with bisection is worth another 0.083. Exact arithmetic is
not cosmetic: the float dump of a valid witness scores zero.

## Shortcut probes

These are maintainer measurements on the real scoring path (in-process
`evaluate`, same oracle as `python -m sle eval`). The 2-parameter family is
`P = [[1, b, 0], [b, d, 0], [0, 0, 1]]`, the 3-by-3 analogue of the (b, d)
grid that beat the previous 2-by-2 reference.

| probe | scale / wall | combined | vs reference |
|---|---|---|---|
| baseline `solution.py` | — | **0.000000** | 0.00× |
| padded September 9 constant `p11=1, p12=-3/5, p22=1, p13=p23=0, p33=1, alpha=59/100` | 0 search | **0.000000** (infeasible on every instance) | 0.00× |
| identity Gram, exact bisection of alpha | 4 bisections | 0.176288 | 0.48× |
| **2-param grid `b,d` step 1/10, 725 Grams, rational bisection** | **725×4, 2.0 s** | **0.206533** | **0.56×** |
| **reference** (112 Grams, public-cap bisection) | **1.16 s** | **0.366560** | 1.00× |
| 5-DOF rational scan, 5488 Grams, den=40 | 15.2 s | 0.458200 | 1.25× |
| spectral mean ceiling if every instance hit `2\|Re λ_max\|` | — | ≈ 0.511 | 1.39× |

The constant certificate that scored 0.786533 on the 2-by-2 family is not a
Lyapunov function here. The 2-parameter grid that scored 0.799867 in 0.1 s
there scores **0.206533 in 2.0 s**, below the reference by 0.160. Checkpoint 12
is a pass: thousands of evaluations in a few seconds do not beat the reference.

`references/constant_probe.py` and `references/grid_probe.py` reproduce the
constant and 2-param rows. `tests/test_lyapunov_decay_certificate.py` pins
that both stay below the reference.

## Frontier draw

None. `calibration_runs` is empty and `long_horizon.status` is `not_tested`.
This is a candidate, not a certified exam item.

## Construction errors

The previous 2-by-2 family had only two free Gram parameters after homogeneity.
A 0.1-second (b, d) grid scored 0.799867 against a coarse-rate reference of
0.749867, and the instance-blind constant above scored 0.786533. Repairing only
the rate table pushed the reference to 0.8496, against a mean ceiling of 0.8499,
which is not leftover scientific headroom. The instances are now four
permutation-switched 3-by-3 plants (braid, cycle, twist, cross). No shared 2-by-2
warehouse matrix is the whole family. No padded old instance or change of basis
is claimed as that redesign.

## Robustness and limits

Floats and malformed certificates fail closed. A 2-by-2 key set without
`p13`/`p23`/`p33` scores zero. Numerically found 3-by-3 matrices converted to
exact rational witnesses are not inherently forbidden; that is the intended
scientific work. The 5-DOF scan at 0.4582 versus the catalog at 0.3666 is the
documented leftover (a larger rational catalog or an SDP-plus-reconstruction).
The PR remains Draft; no model calibration or long-horizon evidence was created.
