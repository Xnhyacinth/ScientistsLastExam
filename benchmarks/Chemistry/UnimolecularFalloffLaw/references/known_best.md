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
