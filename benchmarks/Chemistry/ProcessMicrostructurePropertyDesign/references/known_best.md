# ProcessMicrostructurePropertyDesign — witnesses and limits

## Reproducing

`uv run python -m pytest tests/test_process_microstructure_property_design.py -q`
checks the independent reference, baseline, shortcut families, shifts and runner boundary.
Use `NPY_DISABLE_CPU_FEATURES=AVX512F,AVX512CD,AVX512_SKX,AVX2,FMA3` for the
SIMD-downgraded check. Aggregate nominal/shifted hypervolumes and their normalization
anchors are rounded to 12 decimal places at the same publication boundary. This preserves
exact baseline zero, reference one and equality with the wave's starting incumbent.
It is not a proof that every per-world physical diagnostic is bit-identical across architectures.

## Reference

The independent public-input policy constructs a 1024-point Latin hypercube, ranks points
with its own approximate low-fidelity coefficients, greedily selects a 20-row archive and
performs two coordinate-exchange passes. It does not read the oracle coefficient mapping.
Release scores are clipped; above-reference raw hypervolume remains a separate quantity.

| split | baseline raw | reference raw | baseline shifted | reference shifted |
|---|---:|---:|---:|---:|
| development | 0.036551707421 | 0.055564306822 | 0.032344076195 | 0.049579047191 |
| heldout | 0.039450249715 | 0.061096019789 | 0.035306255126 | 0.055142730186 |

## Baseline

Four shortest, hottest, fastest-cooled, undrawn schedules are legal and score exactly zero.
The public problem contains bounds and units, not the reference recipe or oracle parameters.

## Shortcut and ablation evidence

[Maintainer measurements on 2026-09-09](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/16#issuecomment-5594778785)
use the current approximate reference, before the 12-decimal aggregate publication repair:

| probe | development score |
|---|---:|
| public-only blind three-coordinate 18-point archive | 0.606300 |
| public-only blind two-coordinate 20-point archive | 0.599213 |
| 441-point blend/temperature grid | 0.252806355974678 |
| 343-point blend/time/draw | 0.7038518856341829 |
| 343-point blend/cooling/draw | 0.3038586722374222 |
| 343-point blend/temperature/draw | 0.4597487569332539 |
| 2048-point public pool with reference refinement | 0.9994508031927263 |
| no-draw reference ablation | 0.5338287052189218 |
| shortest-time ablation | 0.7130298217545511 |
| fastest-cooling ablation | 0.782188606082588 |
| one low-temperature ablation | 0.6711731931367305 |

These are attributed algorithm probes, not fresh model calibration. Some grid archive
selection uses evaluator objectives; it is an offline upper-envelope diagnostic, not a
candidate-executable method. Evaluator-aware coordinate exchange reaches raw HV
0.055931851484335146 and is likewise not a blind baseline. Near-one 2048-pool performance
does not establish long-horizon separation or resistance to other low-dimensional searches.

## Superseded construction measurements

The former oracle-aligned reference scored raw 0.05589055199212832 development and
0.06125903702179302 heldout. Its old ladder and unclipped >1 values are superseded by
both the approximate-proxy reference and clipped release contract. They must not be
presented as current headroom measurements. Earlier scalar pool-size and subspace
shortcuts motivated the existing process law; their removal did not certify hardness.

## Robustness and remaining work

Three sealed process/material shifts and heldout worlds are separately reported. Promotion
requires development score >=0.1 and transfer retention; record emission is not ledger
admission. No model calibration, long-horizon evidence, manufacturing validation or
independent real-polymer experiment has been supplied. Lineage remains incomplete_legacy.

## September 12 public-bounds control and transfer ratios

The standalone `references/blind_grid_probe.py` is a new 20-point blend/draw grid using
only public bounds. It is not the unavailable original owner grid, nor an evaluator-aware
archive selector. Linux sandbox score is **0.718235824**, valid=1;
the complete reference remains score one. Older owner controls above remain relevant.

For the reference, raw shifted/nominal hypervolume retention is
**0.892282295 development** and
**0.902558471 heldout**.
These ratios use raw hypervolumes, not separately normalized score-one quantities.
The declared-grid gate is only a reproducible control, not certification against all
known archive searches or a substitute for model calibration.
