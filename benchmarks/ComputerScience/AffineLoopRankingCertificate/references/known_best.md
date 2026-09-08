# AffineLoopRankingCertificate — coupled transitions

## Construction and exact optima

These are procedural rational affine transitions over real states, not transcribed SV-COMP
integer programs. For dimension n=8,10,12,16, A has diagonal 1/2, next cyclic entry 1/4
and next-two entry 1/8. Guards are x_i>=1. All row/column sums are 7/8.
Both Farkas vectors matter; no coordinate-axis ranking is feasible.

Let M=I-A^T and B=M^-1. Since A is nonnegative and contractive, B is nonnegative.
Writing r=B*mu, mu>=0, sum(r)=1 expresses every feasible ranking as a convex combination
of normalized columns of B. Therefore the maximum decrease is the largest value of
c^T B[:,j]/sum(B[:,j]), where c_i=1-sum(A[i,:])-b_i. Tests recompute these ratios in
exact Fraction arithmetic and verify matching certificates in known_optima.json.
This establishes the score-one LP optimum, not merely a numerical lower witness.

| dimension | optimal delta | local reference delta | reference score |
|---|---:|---:|---:|
| 8 | 145031/28536 | 1689/400 | 0.830807 |
| 10 | 661183/134200 | 3496673/900000 | 0.788571 |
| 12 | 599934529/123666440 | 32869/9000 | 0.752816 |
| 16 | 1280622923/269940120 | 1888523477/576000000 | 0.691102 |

## Baseline and reference

The uniform ranking claims delta=1/10000 and scores exactly zero. The public-input reference
uses feasible pair-coordinate ascent with exact rational steps, scoring 0.765824 mean.
It can stall at a face where improving requires a coupled direction. It does not read optima.

## Shortcut probes and ablations

Axis enumeration: no valid certificates, score 0. Local pair-coordinate ascent: 0.765824.
Full exact cone-ray solution: 1.0. Dropping the second multiplier vector invalidates every
positive normalized ranking because M is invertible. General LP solvers remain applicable;
no frontier-model hardness claim follows from defeating the old coordinate-axis shortcut.

## Construction errors

The previous four A=I instances reduced to coordinate maximization and reference already
attained their global optimum. They were replaced, not rescaled. Task.md and the Chinese
inventory now state the correct baseline subtraction. The new rational coefficients do
not preserve arbitrary integer states; the contract explicitly covers real states.

## Robustness and model draws

Fractions are checked exactly, including both Farkas identities and unit 1-norm. Magnitude
caps are 10^18 to admit these higher-dimensional exact witnesses. Malformed/float certificates
fail closed. No model draws, fresh program corpus or long-horizon calibration has been run.
Lineage is incomplete_legacy and the task remains a candidate.
