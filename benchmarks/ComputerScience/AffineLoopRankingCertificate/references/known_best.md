# AffineLoopRankingCertificate — overcomplete mixed-sign loops

## Construction and exact optima

These are procedural rational affine transitions over real states, not transcribed SV-COMP
integer programs. For dimension n=8,10,12,16 the update is circulant with first row
`(1/2, 1/8, -1/4, 1/16, 0, …)`. The negative skip term makes `(I-A^T)^{-1}` mixed-sign,
so the old identity-guard simplex of nonnegative inverse columns is gone. Guards are 2n
half-spaces: `x_i + x_{i+1} ≥ 2` and `2 x_i + x_{i+3} ≥ 3`. They are not n independent
coordinate inequalities, so `λ=r` and `μ=(I-A^T)r` are not Farkas solutions. The fibre
`G^T λ = r` is positive-dimensional.

Coordinate-axis rankings lie outside the guard cone. Tests recompute each hidden
`optimal_delta` with an independent exact Farkas LP in `tests/affine_ranking_lp.py` and
check a matching certificate; no complete instance-answer table is shipped. Commit
`f7586e6` removed public `optimal_delta` and `references/known_optima.json`; those
disclosures stay gone.

| dimension | optimal delta | local reference delta | reference score |
|---|---:|---:|---:|
| 8 | 43769/5136 | 73/16 | 0.535373 |
| 10 | 292551/27376 | 81/16 | 0.473728 |
| 12 | 1160739799/121772784 | 211/48 | 0.461160 |
| 16 | 102537959/8118000 | 37/8 | 0.366159 |

## Baseline and reference

The uniform ranking claims delta=1/10000 and scores exactly zero. The public-input reference
searches uniform and pairwise slopes with constructive Farkas multipliers, scoring 0.459105
mean. It can stall where improving requires a coupled direction. It does not read optima.

## Shortcut probes and ablations

Axis enumeration: no valid certificates, score 0. Inverse-column enum of `(I-A^T)^{-1}`
(`references/inverse_column_probe.py`, the previous 20-line closed form): feasibility 0,
combined 0.0 on all four instances (mixed-sign columns fail the unit 1-norm; n multipliers
for 2n guards). Local uniform-plus-pairwise reference: 0.459105. Full exact Farkas LP:
1.0. General LP solvers remain applicable; no frontier-model hardness claim follows from
defeating the identity-guard column enum.

## Construction errors

The A=I translations reduced to coordinate maximization. Replacing A only, while keeping
`x_i ≥ 1`, left a simplex on the columns of `(I-A^T)^{-1}`. Those instances were replaced,
not rescaled. Public `optimal_delta` and full optimal certificates were removed in `f7586e6`
and are not restored. The rational coefficients do not preserve arbitrary integer states; the
contract explicitly covers real states.

## Robustness and model draws

Fractions are checked exactly, including both Farkas identities and unit 1-norm. Magnitude
caps are 10^18 to admit these higher-dimensional exact witnesses. Malformed/float certificates
fail closed. No model draws, fresh program corpus or long-horizon calibration has been run.
Lineage is incomplete_legacy and the task remains a candidate.

## September 10 instance repair

Owner review: changing A≠I only changed the basis while n coordinate guards uniquely determined
`λ=r` and `μ=(I-A^T)r`. The new overcomplete mixed-sign family makes those identities false.
The same inverse-column probe now scores 0.0, not 1.0. A general exact LP still reaches the
hidden scalar optimum and is disclosed as a residual shortcut, not as admission evidence.
