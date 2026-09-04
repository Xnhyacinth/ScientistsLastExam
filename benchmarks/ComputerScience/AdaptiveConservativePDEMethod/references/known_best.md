# Reference method and evidence boundary

`verification/reference_method.py` returns the executable witness used as the exact score-one
anchor: 96 cells, MUSCL reconstruction, MC limiting, the scalar Godunov flux, SSPRK2 time
integration, CFL 0.72, sensor threshold 0.28 and shock blend 0.82.

This witness is intentionally not called a best-known numerical method. A legal 192-cell
MUSCL/van-Leer/Godunov/SSPRK3 configuration already exceeds it inside the frozen work envelope.
That replay proves local scoring headroom only. It is not HY3 difficulty evidence, a convergence
study, or an external numerical-analysis review.

The cell follows the conservative finite-volume and piecewise-linear reconstruction lineage of
van Leer, *Journal of Computational Physics* 32, 101--136 (1979), DOI
`10.1016/0021-9991(79)90145-1`, and the strong-stability-preserving Runge--Kutta construction of
Shu and Osher, *Journal of Computational Physics* 77, 439--471 (1988), DOI
`10.1016/0021-9991(88)90177-5`.
