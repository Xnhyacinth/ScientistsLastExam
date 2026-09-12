# DiblockMorphologyDiscovery — reference results

Builder measurements and separately attributed maintainer probes are recorded below.

## Reproducing

```
python3 frontier_eval/run_eval.py --candidate verification/reference_morphology.py \
    --metrics-out /tmp/metrics.json
```

## Reference - `verification/reference_morphology.py`

Truth-blind: it reads only the public q bounds and the budgeted `measure` callback.

| metric | development | held out |
|---|---|---|
| combined / mechanism score (normalized) | **1.00** | **1.00** |
| signal recovery rate | 1.00 | 1.00 |
| false discovery rate | 0.00 | 0.00 |
| correct refusal rate | 1.00 | 1.00 |

It locates the first Bragg peak, probes the distinctive harmonics of lamella / hex / bcc / gyroid, and refuses when a second q* is incommensurate with those ratios. Disorder is the single bright RPA peak. No frontier draw has been run yet.

## Baseline - `solution.py`

Buys one mid-q assay it ignores. Always publishes lamellae. Mixture and ABC traces are therefore lamellar papers.

| metric | value |
|---|---|
| combined score | **0.0000** |
| signal recovery rate | 0.20 |
| false discovery rate | 1.00 |
| correct refusal rate | 0.00 |

## Ablation ladder and shortcut probes

Maintainer measurements in PR #26, 2026-09-08, head 1b5381a: replacing reference
refusals with lamella gives 0.600 development / 0.333 heldout. A 16-point grid and
secondary-peak-ratio nearest neighbour gives 0.400 development. Reference is 1.000 / 1.000.
Peak height distinguishes several generator classes; this is a known shortcut. No unmeasured
headroom or frontier-model hardness is claimed from the reference ceiling.

## Construction errors

The initial records omitted shortcut numbers and robustness. Task documentation incorrectly
presented contract_lint as an evaluator call; it is an optional free candidate-side checker.
The amplitude cue in the synthetic traces remains a known limitation pending redesigned and remeasured instances.

## Robustness and model draws

The held-out numbers above use the fixed evaluator-only split; they are not fresh-seed,
external-data, or model calibration results. No frontier-model draws or long-horizon runs
have been performed. Calibration evidence remains missing and lineage is incomplete_legacy.

## September 12 executable refusal ablation

`references/no_refusal_probe.py` is a self-contained copy of the complete public-input
matcher with only its two refusal exits changed to publish lamella. Full Linux sandbox
scores **0.600000 development / 0.333333 heldout**, versus the full reference **1.0 / 1.0**.
The shortcut declaration records this actual ablation, not a duplicate baseline.
No scientific model or score was changed. Current model calibration and independent
scientific admission are still missing; functional/declared-probe passes do not supply them.
