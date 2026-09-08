# UnimolecularFalloffLaw — reference results

Builder measurements and separately attributed maintainer probes are recorded below.

## Reproducing

```
python3 frontier_eval/run_eval.py --candidate verification/reference_falloff.py \
    --metrics-out /tmp/metrics.json
```

## Reference - `verification/reference_falloff.py`

Truth-blind: it reads only the public bounds and the budgeted `measure` callback.

| metric | development | held out |
|---|---|---|
| combined / mechanism score (normalized) | **~0.73** | **~0.78** |
| signal recovery rate | ~0.73 | similar |
| false discovery rate | 0.00 | 0.00 |
| correct refusal rate | 1.00 | 1.00 |

It refuses when the low-pressure reaction order is not 1 (second channel) or when k falls as P rises. On in-family worlds it estimates k_inf from the high-P end and Fcent from the mid-falloff point. Publishing a typical Troe Fcent of 0.40 rather than a full master-equation fit is leftover headroom, not an exploit. No frontier draw has been run yet.

## Baseline - `solution.py`

Buys one mid-range assay it treats as pressure-independent Arrhenius. Always publishes Lindemann. Two-channel and negative-order worlds are therefore Lindemann papers.

| metric | value |
|---|---|
| combined score | **0.0000** |
| signal recovery rate | 0.00 |
| false discovery rate | 1.00 |
| correct refusal rate | 0.00 |

## Ablation ladder and shortcut probes

Maintainer measurements in PR #26, 2026-09-08, head 1b5381a: a three-assay
rule (300 K at 100 bar, 1 mbar, 10 mbar) scores 0.565 development / 0.698 heldout,
versus reference 0.731992 / 0.776873. It refuses a falling rate or low-pressure order
below 0.5, otherwise emits Lindemann using the high-pressure rate and low-pressure slope.
This reaches 77% of the reference and limits the current difficulty claim.
We retain the current worlds and weights in this compatibility revision; increasing hardness
requires a separately measured mechanism redesign, not a cosmetic score reduction.

## Construction errors

The initial records omitted shortcut numbers and robustness. Task documentation incorrectly
presented contract_lint as an evaluator call; it is an optional free candidate-side checker.
The public Troe description omitted the symmetric reduced formula and its missing c/d terms; both public interfaces now state the actual oracle formula.

## Robustness and model draws

The held-out numbers above use the fixed evaluator-only split; they are not fresh-seed,
external-data, or model calibration results. No frontier-model draws or long-horizon runs
have been performed. Calibration evidence remains missing and lineage is incomplete_legacy.

Citation metadata checked against Crossref and Wiley on 2026-09-08: DOI
10.1002/bbpc.19830870218 is Gilbert, Luther and Troe, *Theory of Thermal Unimolecular
Reactions in the Fall-off Range. II. Weak Collision Rate Constants* (1983).
DOI 10.1002/bbpc.19830870219 is an unrelated journal notice and has been removed.
The reduced symmetric formula is a benchmark approximation, not the full published law.
