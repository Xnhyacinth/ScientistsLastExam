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

## Robustness

Malformed assignments fail closed. Tests verify one-queen feasibility, binary upper-bound
rejection, file hashes/dimensions and unsupported-section rejection. No parameter/noise
variation or fresh-instance generalization is claimed for this one fixed public model.

## Model draws

Not run. Lineage and construction status are incomplete_legacy. The 0.125 gap in the library probe was superseded by stronger no-solver local search
in the September 9 maintainer review; it does not establish long-horizon difficulty. External review pending.


## September 9 no-solver counterexample and admission hold

[Owner measurements](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/31#issuecomment-5594780525)
use greedy insertion plus two-exchange local search: a valid evaluator-tested candidate
finds 36 queens (0.900) in 60 seconds and 37 (0.925) in 240 seconds. A separate script
with stricter feasibility finds 38 (0.950) in 7.1 seconds and 39 (0.975) by 44.3 seconds.
These are attributed maintainer probes, not interchangeable timing protocols or model draws.
They supersede the claim that replacing gen-ip with queens-30 removed near-saturation.

The task remains blocked by limited measured search headroom and pending file-level data
rights. A monotone log-gap rescale would not add attainable objective levels or defeat the
heuristic; this update does not claim it repairs scientific difficulty.


The self-contained `references/local_search_probe.py` uses only the public CSR matrix,
NumPy, deterministic seed 20260909 and 2500 greedy/two-exchange rounds. Independently run
through `python -m sle eval` with a 180-second timeout, it finds **38 queens**, objective
**-38**, score **0.95**, valid with zero constraint violation. This is an algorithm probe,
not a model result or a timing comparison with the maintainer's different configurations.
