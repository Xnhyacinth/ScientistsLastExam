# AffineLoopRankingCertificate — nested-reset lexicographic ranking

## Construction and exact qualities

These are procedural nested-reset rational affine transition systems over real states,
not transcribed SV-COMP integer programs. Each instance is a Bradley–Manna–Sipma
nested loop: one inner progress step per level, then a reset that copies the progressing
block onto the next inner block while that inner block is in an exit polyhedron `v_i ≤ 1`.
A single linear ranking cannot serve both an inner decrease (needs a positive inner slope)
and a reset (that slope increases). The Colón–Sipma / Podelski–Rybalchenko 1-ranking Farkas
LP is infeasible on every instance.

Progressing blocks use the mixed-sign circulant update with first row
`(1/2, 1/8, -1/4, 1/16, 0, …)` and overcomplete guards `x_i + x_{i+1} ≥ 2` together with
rotated half-spaces. They are not `n` independent coordinate inequalities.

Score one is the measured quality `Q*` of a verified nested lex ranking whose components
are independent exact phase rankings. That is **not** a 1-ranking Farkas LP optimum of the
whole system. Tests reconstruct `Q*` from `tests/affine_ranking_lp.py:phase_lex_ranking`
and check a matching certificate; no complete instance-answer table is shipped. Public
instances do not disclose `score_one_quality`.

| instance | levels | Q* | uniform honest Q | reference Q | reference score |
|---|---:|---:|---:|---:|---:|
| reset_6 | 2 | 1037/84 | 115/12 | 43/4 | 0.870779 |
| reset_8 | 2 | 3991/248 | 85/8 | 105/8 | 0.815583 |
| nested_9 | 3 | 985/56 | 111/8 | 123/8 | 0.874110 |
| nested_12 | 3 | 10821/496 | 239/16 | 283/16 | 0.810736 |

## Baseline and reference

The uniform nested ranking claims delta=1/10000 on each level and scores exactly zero.
The public-input reference searches uniform and adjacent pairwise slopes on each block
with constructive Farkas multipliers, scoring 0.842802 mean. Pairwise directions beat
uniform on every level because the offset is peaked. Coupled phase rankings beyond those
local moves remain possible. The reference does not read `Q*`.

## Ablation ladder

Measured against the frozen `Q*` (clip01 of summed component deltas). All rows except the
1-ranking LP are valid on every instance.

| candidate | what it searches | combined | valid | wall |
|---|---|---:|---:|---|
| `solution.py` | uniform nested ranking, token δ=1/10000 | 0.000000 | 1 | <0.1s |
| uniform nested ranking, honest δ, no direction search | same r, honest Farkas decrease | 0.727504 | 1 | <0.1s |
| `reference_ranking.py` | uniform + adjacent pairwise per block | 0.842802 | 1 | <0.2s |
| 3-support / skip-2 catalog on top of pairwise | extra discrete directions | 0.842802 on width-4, higher on width-3 | 1 | <0.2s |
| inverse-column enum of one transition (`references/inverse_column_probe.py`) | depth-1 closed form | 0.000000 | 0 | <0.1s |
| whole-system 1-ranking Farkas LP (`one_ranking_as_lex`) | Colón–Sipma lattice | 0.000000 | 0 | <1s |
| independent exact phase rankings (`phase_lex_ranking`) | lex-phase method | 1.000000 | 1 | <1s |

The reference's search half is the adjacent pairwise directions. Removing them drops the
score from 0.842802 to 0.727504. That gap is the search contribution; the previous
overcomplete single-path family was flat because uniform already matched pairwise.

## Shortcut probes

Axis-style depth-1 rankings cannot cover the reset. Inverse-column enum of `(I-A^T)^{-1}`
on the first transition is a 1-ranking attempt and scores 0. The textbook exact Farkas LP
on the whole transition system is infeasible (measured delta 0 on all four instances) and
scores 0. Independent per-phase Farkas LPs reconstruct `Q*` and are disclosed as a residual
lex method, not as the blocked 1-ranking shortcut.

## Construction errors

Single-path overcomplete loops still had a complete 1-ranking LP, and score one was that
LP's optimum. Nested resets leave that lattice: the same LP now scores 0. Public `Q*` and
full optimal certificates are not published. The rational coefficients do not preserve
arbitrary integer states; the contract covers real states.

## Robustness and model draws

Fractions are checked exactly, including lex Farkas identities, unit 1-norm, and "every
component is used". Magnitude caps are 10^18. Malformed/float certificates fail closed.
`valid` is 1.0 iff every instance is valid. No model draws, fresh program corpus or
long-horizon calibration has been run. Lineage is incomplete_legacy and the task remains
a candidate.

## September 11 lex redesign

Owner review (checkpoint 12): a textbook exact Farkas LP on real states plus a single
linear ranking scored 1.0; disclosure cannot replace redesign. Option 2
(lexicographic / multiphase ranking tuples). Instances are nested-reset loops that are
not 1-ranking complete. The certificate is a lex tuple. The old 1-ranking Farkas LP
scores 0.0. Score one is a verified nested lex ranking, not that LP.
