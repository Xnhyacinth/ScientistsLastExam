# MiplibPrimalIncumbent — queens-30

## Source and reference

The original MIPLIB queens-30 MPS has 900 binary variables and 960 constraints.
Official solufile v36 gives `=opt= queens-30 -40`, verified 2026-09-08.
The compressed original and uncompressed hashes are in anchors.json. Only the original
compressed MPS is vendored. No .sol assignment or runtime download is used.

## Baseline

The empty vector is feasible, objective 0, score 0. One queen is feasible and scores
0.006649 on the log-gap scale.

## Shortcut probes and ablation ladder

The old gen-ip002/021/054 suite was measured in a Linux sandbox: SciPy milp with one
thread and 60 seconds per model nearly saturated it. It is withdrawn. The earlier
assertion that seccomp prevented solver reuse was false.

Score is `clip01(log((b-r+1)/(z-r+1))/log(b-r+1))` with `b=0`, `r=-40`. Values below
are recomputed from the same measured objectives; they are not the retired linear `q/40`.

Replacement probe on Python 3.12 / NumPy 1.26.4 / SciPy 1.11.4:

| method | objective | score | scope |
|---|---:|---:|---|
| empty vector | 0 | 0 | exact feasibility check |
| milp, 60 seconds, one thread | -35 | 0.517511 | in process |
| milp, 240 seconds, one thread | -35 | 0.517511 | trusted sle eval + bwrap, 300-second timeout |
| greedy+2-swap candidate, 60 s | -36 | 0.566607 | owner, end-to-end evaluator, valid, violation 0 |
| greedy+2-swap candidate, 240 s | -37 | 0.626695 | owner, end-to-end evaluator, valid, violation 0 |
| greedy+2-swap, stricter script | -38 | 0.704163 | owner, 7.1 s, stricter than evaluator |
| greedy+2-swap, stricter script | -39 | 0.813348 | owner, first hit at 44.3 s |
| local_search_probe.py, 2500 rounds | -38 | 0.704163 | deterministic seed 20260909, sandbox |
| official optimum | -40 | 1 | solufile v36 |

The sandbox milp probe uses CSR constraints, Bounds(lower_bounds,upper_bounds), integrality=1,
and scipy.optimize.milp. It is reproducible from references/milp_probe.py. This is a strong
library baseline, not proof of model hardness or resistance to memorization.

## Construction errors

The old MPS parser silently ignored upper bounds and unsupported sections. The replacement
needs binary upper bounds; they are now read and checked. RANGES, objective offsets and
unsupported bound kinds raise errors, and all columns must be declared integer.

## Robustness

Malformed assignments fail closed. Tests verify one-queen feasibility, binary upper-bound
rejection, file hashes/dimensions, unsupported-section rejection, and the log-gap table
from the measured objectives. No parameter/noise variation or fresh-instance generalization
is claimed for this one fixed public model.

## Model draws

Not run. Lineage and construction status are incomplete_legacy. The milp 0.125 linear-scale
gap was superseded by stronger no-solver local search; it does not establish long-horizon
difficulty. External review pending.

## September 9 no-solver counterexample and admission hold

[Owner measurements](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/31#issuecomment-5594780525)
use greedy insertion plus two-exchange local search. Objectives are unchanged; scores below
are the new log-gap values:

| method | objective | old q/40 | log-gap |
|---|---:|---:|---:|
| greedy+2-swap, 60 s candidate | -36 | 0.900 | 0.566607 |
| greedy+2-swap, 240 s candidate | -37 | 0.925 | 0.626695 |
| same heuristic, stricter script | -38 | 0.950 | 0.704163 |
| same heuristic, first -39 at 44.3 s | -39 | 0.975 | 0.813348 |

These are attributed maintainer probes, not interchangeable timing protocols or model draws.
They supersede the claim that replacing gen-ip with queens-30 removed near-saturation
on the linear scale. The last queen is now the expensive increment (0.187 vs 0.0066 for
the first). The rescale does not add attainable objective levels.

The task remains blocked by limited remaining discrete headroom and pending file-level
data rights.

The self-contained `references/local_search_probe.py` uses only the public CSR matrix,
NumPy, deterministic seed 20260909 and 2500 greedy/two-exchange rounds. Independently run
through `python -m sle eval` with a 180-second timeout, it finds **38 queens**, objective
**-38**, log-gap score **0.704163**, valid with zero constraint violation. This is an
algorithm probe, not a model result or a timing comparison with the maintainer's different
configurations.
