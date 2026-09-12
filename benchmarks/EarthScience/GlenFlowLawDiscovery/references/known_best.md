# GlenFlowLawDiscovery — complete reference and admission hold

## Reference

The public-input reference uses both temperature endpoints, three stress values and
repeated assays, jointly fits log A, n and Q/R, and labels all three public supported
families: Glen, Newtonian and GBS. It refuses resolved curvature and negative activation.

The September 12 Linux sandbox replay scores **0.930806 development / 0.944128 heldout**,
with valid=1, FDR=0, correct refusal=1 and coverage=1. This fails the unchanged
`reference < 0.8` admission test. The task remains Draft and scientifically blocked.

## Baseline

The shipped one-assay Newtonian guess is valid and scores zero. Blanket refusal is also
valid and scores zero. Confidence calibration is separate from the discovery decision:
blanket refusal has calibration 6/11 development and 5/8 heldout, not a perfect one.

## Same-estimator ablations

Run from the repository root:

```sh
uv run python benchmarks/EarthScience/GlenFlowLawDiscovery/references/shortcut_probe.py
uv run python -m sle eval --task Glaciology/GlenFlowLawDiscovery --allow-uncertified \
  --candidate benchmarks/EarthScience/GlenFlowLawDiscovery/verification/reference_flow.py --timeout 60
```

The first command reports in-process ablations, the scalar-threshold sweep and the
fresh-noise curvature diagnostic. The second performs the full reference sandbox replay.

| estimator | calls per world | development | heldout |
|---|---:|---:|---:|
| complete reference | 12 | 0.930806 | 0.944128 |
| no repeated assays | 6 | 0.889844 | 0.630187 |
| no temperature arm, Q/R fixed at 6000 | 12 | 0.632150 | 0.714893 |

These are frozen-panel algorithm measurements, not fresh-noise mean effects or model draws.
Removing repeats has only a 0.040962 development effect; it does not establish a strong
budget requirement. Refusal is saturated on the full reference.

## Shortcut probes

The historical scalar-threshold scan uses three stresses, four repeats each at 255 K,
a fixed Q/R of 6000 and two family windows. Its 60-point development-selected sweep
scores 0.395379 / 0 at threshold 0.03, also confirmed in the sandbox. It is weaker than
the complete three-family ablations above; passing that declared probe does not close
the difficulty gate or establish resistance to better strategies.
The self-contained `references/no_repeat_probe.py` also participates in the declared
guard: 0.889844 exceeds the 20%-margin threshold 0.7446448, so this stronger guard fails.

## Construction errors

The previous 0.576653 / 0.620010 result came from omitting GBS from the reference, despite
GBS being a public supported family. Calling this intended headroom was incorrect.
The reference now covers GBS, and tests require recovery instead of locking in abstention.
Neither the oracle, its noise, normalization nor the admission threshold was weakened.

Earlier noise-indistinguishable sliding worlds were replaced by resolvable curvature
0.2501707249 / 0.2159040914. The same Arrhenius factor now multiplies sliding and creep;
a temperature-independent sliding term would be a synthetic free discriminator.
GBS and stress-dependent n are reduced benchmark models, not experimental ice datasets.

## Robustness

The script's 4000-panel curvature experiment (seed 20260908, sigma 0.03) detects the
intermediate sliding worlds with probabilities 1.000 / 0.999 at threshold 0.12, while
pure Glen gives 0.000. This checks that particular observation design only.
Malformed submissions fail closed, discovery denominators are published, and the wrapper
uses the shared search-visible evaluator entrypoint. Full metrics remain trusted diagnostics.

## Model draws and remaining evidence

No frontier-model calibration, fresh-parameter confirmation, long-horizon evidence or
external scientific validation exists. Lineage remains incomplete_legacy. Fixing reference
completeness exposes the unresolved task-design problem; it does not qualify this task for
high-quality benchmark data admission. Historical scores do not rebind to this package.
