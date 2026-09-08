# MiplibPrimalIncumbent — queens-30

## Source and reference

The original MIPLIB queens-30 MPS has 900 binary variables and 960 constraints.
Official solufile v36 gives `=opt= queens-30 -40`, verified 2026-09-08.
The compressed original and uncompressed hashes are in anchors.json. Only the original
compressed MPS is vendored. No .sol assignment or runtime download is used.

## Baseline

The empty vector is feasible, objective 0, score 0. One queen is feasible and scores 0.025.

## Shortcut probes and ablation ladder

The old gen-ip002/021/054 suite was measured in a Linux sandbox: SciPy milp with one
thread and 60 seconds per model scores 0.996066 (per model 0.995833/0.998416/0.993950).
It is withdrawn; the earlier assertion that seccomp prevented solver reuse was false.

Replacement probe on Python 3.12 / NumPy 1.26.4 / SciPy 1.11.4:

| method | objective | score | scope |
|---|---:|---:|---|
| empty vector | 0 | 0 | exact feasibility check |
| milp, 60 seconds, one thread | -35 | 0.875 | in process |
| milp, 240 seconds, one thread | -35 | 0.875 | trusted sle eval + bwrap, 300-second timeout |
| official optimum | -40 | 1 | solufile v36 |

The sandbox probe uses CSR constraints, Bounds(lower_bounds,upper_bounds), integrality=1,
and scipy.optimize.milp. It is reproducible from references/milp_probe.py. This is a strong
library baseline, not proof of model hardness or resistance to memorization.

## Construction errors

The old MPS parser silently ignored upper bounds and unsupported sections. The replacement
needs binary upper bounds; they are now read and checked. RANGES, objective offsets and
unsupported bound kinds raise errors, and all columns must be declared integer.
FrozenKernelProofFrontier is withdrawn from the PR and retained on a separate local branch.

## Robustness

Malformed assignments fail closed. Tests verify one-queen feasibility, binary upper-bound
rejection, file hashes/dimensions and unsupported-section rejection. No parameter/noise
variation or fresh-instance generalization is claimed for this one fixed public model.

## Model draws

Not run. Lineage and construction status are incomplete_legacy. The remaining 0.125 gap in
the measured library probe does not establish long-horizon difficulty. External review pending.
