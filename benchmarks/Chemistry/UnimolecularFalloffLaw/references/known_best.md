# UnimolecularFalloffLaw — reference results

Builder measurements after per-world wall Pr. No frontier-model draws or pairing Δ
were taken.

## Reproducing

```
python3 frontier_eval/run_eval.py --candidate verification/reference_falloff.py \
    --metrics-out /tmp/metrics.json
```

In-process `evaluator.evaluate` on the published seeds matches the numbers below.

## Reference - `verification/reference_falloff.py`

Truth-blind: it reads only the public bounds and the budgeted `measure` callback.
It fits the public reduced Lindemann/Troe pressure law jointly for log k_inf, log Pr
and Fcent (14 log-spaced pressures at 300 K and four hotter assays for pressure-order
refusal). BIC compares the two fitted families. Only existing NumPy/SciPy and public
observations are used.

| metric | development | held out |
|---|---|---|
| combined / mechanism score (normalized) | **0.969831** | **0.719345** |
| false discovery rate | 0.00 | 0.00 |
| correct refusal rate | 1.00 | 1.00 |

Those frozen-panel scores are a lucky draw. Across 12 noise panels (world seeds offset
by 0, 2, …, 22; same estimator, only the seed changes) the full 18-assay reference is
development mean **0.7767** (min 0.401, max 0.970) and held-out mean **0.8479**.
The 0.9698 frozen-panel number is the maximum on that 12-panel set, not a typical
value. A previous 0.9613 figure was likewise a maximum across panels.

Held-out Troe on the frozen panel scores 0.468 while held-out Lindemann scores 0.970.
That is underfit of k_inf against Fcent inside the observable window, not leftover
ceiling. It is not evidence that the reference saturates the task.

## Baseline - `solution.py`

Buys one mid-range assay it treats as pressure-independent Arrhenius. Always publishes
Lindemann. Two-channel and negative-order worlds are therefore Lindemann papers.

| metric | value |
|---|---|
| combined score | **0.0000** |
| signal recovery rate | 0.00 |
| false discovery rate | 1.00 |
| correct refusal rate | 0.00 |

## Ablation ladder and shortcut probes

Same reference estimator, only `measure_budget_calls` changed, mean over the same 12
noise panels:

| budget | development mean | held-out mean |
|---|---|---|
| 8 | 0.7080 | 0.6957 |
| 10 | 0.7658 | 0.7479 |
| 12 | 0.7683 | 0.7857 |
| 18 | 0.7767 | 0.8479 |

A 1215-point truth-blind 3-assay grid (high / 10 mbar / 1 mbar; same refusal as
`three_assay_probe.py`; 9 k_inf offsets × 15 log Pr × 9 Fcent) scores
**0.299711 / 0.284082** on the frozen panel, below the full-curve reference.

A 3-assay probe that pins one constant `log_Pr_300K_1bar` for every world and inverts
Fcent from the mid point no longer finds a shared constant. A 13-point 1-D scan on the
frozen panel peaks at ln Pr = −5.00 with **0.152536 / 0.118574**; held-out instead
peaks near −3.50 (0.416). Development and held-out no longer peak at the same ln Pr.

`references/three_assay_probe.py` (the September 9 wall-as-k_inf counterexample) now
scores **0.042868 / 0.396599** against the repaired worlds.

## Construction errors

Earlier packages pinned Pr(300 K, 100 bar) = 2 on every in-family world, so
log Pr(300 K, 1 bar) = ln(0.02) was a shared constant a 1-D scan could hit without
measurements. Wall Pr is now per world in [0.6, 6], still in the falloff
(`k(100 bar)/k_inf` in (0.10, 0.85) on in-family worlds), and the 1-D constant-Pr
probe no longer beats the reference.

A previous note that treated held-out Troe as leftover headroom contradicted
measurement: the reference underfits that world, and a cheap constant-Pr rule used
to outscore it while the constant leaked. That sentence is withdrawn.

The public Troe description states the symmetric reduced formula and its missing
c/d terms. `sle.contract_lint` is an optional free candidate-side checker, not an
evaluator call.

## Robustness and model draws

The held-out numbers above use the fixed evaluator-only split plus the 12 seed-offset
noise panels named in the ablation table. They are not external-data or model
calibration results. No frontier-model draws or long-horizon runs have been
performed. Calibration evidence remains missing and lineage is incomplete_legacy.

Citation metadata checked against Crossref and Wiley on 2026-09-08: DOI
10.1002/bbpc.19830870218 is Gilbert, Luther and Troe, *Theory of Thermal
Unimolecular Reactions in the Fall-off Range. II. Weak Collision Rate Constants*
(1983). DOI 10.1002/bbpc.19830870219 is an unrelated journal notice and has been
removed. The reduced symmetric formula is a benchmark approximation, not the full
published law.

## September 12 executable constant-Pr control

`references/constant_pr_probe.py` supplies a complete related reconstruction: three
pressure assays and a two-parameter fit with one shared log-Pr value. It is **not** the
missing original C9 implementation. Its 17-point grid is -6 through -2 in increments
of 0.25; development alone selects -4.0. Full Linux sandbox at that fixed setting gives
**0.387565 development / 0.096163 heldout**, against reference **0.969831 / 0.719345**.
The module's main command prints every grid row and its development-selected winner:
`uv run python benchmarks/Chemistry/UnimolecularFalloffLaw/references/constant_pr_probe.py`.

This supports the limited statement that this explicit constant-Pr control no longer
beats the current reference. It does not certify the unavailable C9 source, independent
parameter-world generalization, model difficulty or the small development budget effect.
The existing 12-panel same-estimator test remains unchanged and passes. Its offsets and
all earlier stronger strategies retain their original evidence scope.

The self-contained `references/reduced_budget_probe.py` uses the same estimator with
only eight assays. On the current frozen panel, the complete sandbox result is
**0.932777666667 / 0.7035045** (valid=1), close to full-budget **0.969831 / 0.719345**.
This stronger control is also declared and fails the 20% shortcut margin. The multi-panel
mean effect reported above remains a different estimand and does not erase this result.
The task is still blocked on meaningful budget dependence and independent calibration.

## September 12 disposition: withdraw this task version

Reproduce all rows and source hashes with:

```bash
uv run python benchmarks/Chemistry/UnimolecularFalloffLaw/references/budget_parameter_diagnostic.py --output /tmp/falloff-budget-grid.json
```

A bounded follow-up checked whether broader parameters within the existing reduced
law rescue the budget argument. Before evaluating, the diagnostic enumerated the
full Cartesian grid: wall Pr = 0.6, 1.2, 2.4, 4.8, 6.0; Troe Fcent = 0.15,
0.30, 0.45, 0.60, 0.75; and noise-seed offsets = 100, 102, 104, 106. Each
published in-family base world retained its other parameters; A0 was recomputed
with `_a0_for_wall_pr`. Lindemann has no Fcent axis. Unsupported worlds retained
all parameters and used the same four offsets. No panel was selected afterwards.
Noise amplitude, observation window, score, estimator, and 8/18 assay budgets
were unchanged. This is an in-process builder diagnostic, not sandbox release
validation, external physical data, or model calibration.

| split / family | parameter-noise worlds | 8-assay mechanism mean | 18-assay mechanism mean | retained fraction |
|---|---:|---:|---:|---:|
| development / Lindemann | 20 | 0.844196 | 0.937266 | 0.900700 |
| development / Troe | 200 | 0.622413 | 0.742850 | 0.837871 |
| heldout-base / Lindemann | 20 | 0.887105 | 0.923288 | 0.960810 |
| heldout-base / Troe | 100 | 0.514402 | 0.766974 | 0.670691 |

All evaluations were valid; both budgets correctly refused all 28 unsupported
worlds. These are in-family mechanism means with the displayed denominators,
not the release's normalized combined scores. The expanded grids are builder
inspection data; their use of heldout base parameters does not create a new sealed
holdout or authorize replacing the frozen release worlds.

Extra measurements help the heldout-base Troe fits substantially. Thus the evidence
is **not** that this domain has no measurement-budget effect. However, both
expanded development families still retain more than 80% with eight assays, while
the existing frozen-panel shortcut guard also fails. Merely expanding this
procedural parameter grid does not establish the desired difficulty or supply
independent scientific validation. The disposition is to **withdraw the current
UnimolecularFalloffLaw submission**, retaining its audit history, rather than tune
noise, normalization, margins, or select a favorable panel. A future proposal needs
independently justified kinetics/observation conditions and matched-budget evidence
before a new task version is submitted. This withdrawal does not apply to Diblock.
