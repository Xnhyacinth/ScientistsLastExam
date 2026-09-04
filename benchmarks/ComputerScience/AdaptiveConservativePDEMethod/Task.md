# AdaptiveConservativePDEMethod

## Scientific question

Can one deterministic finite-volume method balance accuracy, nonlinear stability, exact discrete
conservation and cell-stage cost across a frozen panel of smooth and discontinuous scalar
conservation laws?

This task asks for a numerical method, not the solution of one supplied PDE instance. The same
method is replayed on seven repository-visible worlds spanning positive and negative linear
advection, smooth and discontinuous profiles, and Burgers shocks and rarefactions. It is distinct
from parameter fitting or PDE-constrained physical design: the artifact is the discretization
itself.

The oracle is a deterministic one-dimensional benchmark. Success here does not establish order of
convergence, entropy stability for a broader equation class, multidimensional performance, or
fitness for a real simulation code.

## What to implement

```python
def design_finite_volume_method(problem):
    ...
    return {
        "reconstruction": "muscl",
        "limiter": "mc",
        "riemann_solver": "godunov",
        "time_integrator": "ssprk2",
        "cells": 96,
        "cfl": 0.72,
        "sensor_threshold": 0.28,
        "shock_blend": 0.82,
        "flux_dissipation": 1.0,
    }
```

Return a mapping with exactly these nine fields. The five discrete choices are:

| field | choices |
|---|---|
| `reconstruction` | `constant`, `muscl` |
| `limiter` | `minmod`, `mc`, `van_leer`, `superbee` |
| `riemann_solver` | `rusanov`, `godunov` |
| `time_integrator` | `euler`, `ssprk2`, `ssprk3` |
| `cells` | `32`, `48`, `64`, `96`, `128`, `192` |

The four continuous coordinates have public closed bounds:

| field | bounds | role |
|---|---:|---|
| `cfl` | `[0.08, 0.95]` | requested Courant factor |
| `sensor_threshold` | `[0.02, 0.95]` | curvature-sensor onset |
| `shock_blend` | `[0.0, 1.0]` | fraction of slope suppressed at a detected shock |
| `flux_dissipation` | `[1.0, 1.5]` | Rusanov wave-speed multiplier |

For a constant reconstruction the limiter and sensor coordinates are canonically inactive. For a
Godunov flux, `flux_dissipation` is canonically inactive. The evaluator collapses these inactive
coordinates before assigning an artifact identity, so changing unused values cannot create a new
method.

## Public problem mapping

Every key supplied to `design_finite_volume_method` is listed here:

| key | meaning |
|---|---|
| `method_fields` | ordered list of the nine exact output fields |
| `discrete_choices` | legal reconstruction, limiter, flux, integrator and grid choices |
| `continuous_bounds` | legal bounds for all four continuous coordinates |
| `equations` | disclosed scalar equation classes |
| `boundary_conditions` | disclosed periodic and fixed far-field boundary classes |
| `adaptivity` | definition of the local curvature-triggered slope reduction |
| `objectives` | accuracy, conservation, stability and work axes |
| `work_unit_definition` | one cell update in one Runge--Kutta stage |
| `max_work_units_per_case` | deterministic per-world resource envelope |
| `scope_warning` | scientific interpretation boundary |

The same mapping is supplied at every world boundary and the candidate must return the same
canonical method. Sandboxed candidate state is reset between worlds. No world ID, split label,
initial condition, final time or result is passed to the method designer.

## Frozen numerical oracle

Cell averages are evolved by a flux-difference finite-volume update. `constant` selects a
piecewise-constant reconstruction; `muscl` selects a limited piecewise-linear reconstruction.
The normalized curvature sensor continuously reduces a MUSCL slope above
`sensor_threshold`, controlled by `shock_blend`. The chosen Rusanov or exact scalar Godunov flux
is integrated by Euler, SSPRK2 or SSPRK3 stages.

Periodic cases measure mass drift. Fixed-boundary Burgers cases integrate the numerical boundary
flux with the same Runge--Kutta weights and measure the complete discrete balance residual. Smooth
and discontinuous exact solutions are cell-averaged with a frozen deterministic quadrature.

Before simulation, a conservative stage-count bound rejects configurations above the public
`max_work_units_per_case`; realized work is checked again. Thus extremely small CFL factors at a
large grid cannot purchase accuracy outside the common envelope.

## Scoring and continuing improvement

Each world reports four separate axes:

1. cell-average L1 accuracy against the frozen exact solution;
2. discrete conservation residual;
3. maximum-principle overshoot and total-variation growth;
4. realized cell-stage work.

A frozen weighted utility combines those axes on four development worlds. `combined_score`
affinely normalizes that utility so the shipped first-order 32-cell Rusanov/Euler method is exactly
`0.0`, while the executable 96-cell MUSCL/MC/Godunov/SSPRK2 witness is exactly `1.0`. The reference
is not asserted to be optimal and the nonnegative score has no upper cap. Three held-out worlds
repeat all four axes but never enter `combined_score`.

The evaluator also emits one canonical optimization record tied to the frozen method
canonicalizer, evidence predicate and seven-world panel. Later immutable waves can add equation
classes, meshes or fidelity without rewriting credit earned under this wave.

## Rules

- Edit only `solution.py`; keep `design_finite_volume_method(problem)`.
- Return one deterministic exact-field method mapping; booleans, nonfinite values, extra fields,
  unknown choices and out-of-envelope methods fail closed.
- Standard-library code is sufficient. Do not use the network, create processes, or read
  `verification/` or `frontier_eval/`.
- Do not infer a hidden split or specialize by call order; candidate sessions are reset at each
  scientific world boundary.

References: van Leer, *Journal of Computational Physics* 32, 101--136 (1979), DOI
`10.1016/0021-9991(79)90145-1`; Shu and Osher, *Journal of Computational Physics* 77, 439--471
(1988), DOI `10.1016/0021-9991(88)90177-5`.
