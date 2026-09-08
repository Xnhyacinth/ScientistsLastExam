# LyapunovDecayCertificate — reference results

Every number here is produced by running code in this directory. Nothing is copied from a table.

## Reproducing

```
python3 frontier_eval/run_eval.py --candidate verification/reference_lyapunov.py \
    --metrics-out /tmp/metrics.json
```

## Reference - `verification/reference_lyapunov.py`

Truth-blind: it reads only the published modes and searches a catalog of rational Gram matrices, keeping the largest exact-feasible rate.

| metric | value |
|---|---|
| combined score | **0.749867** |
| instances with a valid certificate | 4 / 4 |
| shear / pair / three proven alpha | 1/2 |
| mid proven alpha | 3/4 |

A larger rational catalog, or a better-conditioned Gram than the eight catalog entries, is leftover headroom, not an exploit. No frontier draw has been run yet.

## Baseline - `solution.py`

The identity Gram at `alpha = 1/10000`, which is a valid common Lyapunov function because every published mode has a negative numerical abscissa.

| metric | value |
|---|---|
| combined score | **0.000000** |
| instances with a valid certificate | 4 / 4 |

## Ablation ladder and shortcut probes

Maintainer PR #27, 2026-09-08, f2f1dcc: identity baseline 0.000000, reference
0.749867. On shear, P=[[1,-21/37],[-21/37,442/1369]] proves alpha=3/5 exactly,
for instance score 0.799867 versus reference alpha=1/2 and score 0.666533.
Increasing alpha by 1e-6 fails the exact inequality. This is an algorithmic witness,
not a frontier-model draw.

## Construction errors

Task.md and the Chinese inventory had retained the old alpha/(3/4) formula and
near-zero claim. Both now state the baseline subtraction and exact zero.
GridTopologyRecovery and UltrasonicDefectSpecies are removed from this PR pending redesign;
their original source is retained on review/grid-ultrasonic-redesign-20260908.

## Robustness and limits

These are four fixed rational instances, not a distributional robustness result. The 3/4
unit is an engineering clip, not a theorem or published record; the slow eigenvalue limits
shear/pair/three to about 0.8 on this scale. No perfect-score attainability is claimed.
No model draws or long-horizon calibration have been performed. Lineage is incomplete_legacy.
