# GlenFlowLawDiscovery — corrected but not admitted

## Current status

**Difficulty NO-GO.** The reference still scores 0.961088 development / 0.930015 heldout.
This PR remains draft. The original reference<0.8 admission test remains failing and
is not bypassed by the functional checks. These are algorithm probes, not model calibration.

## Mechanism repair

Glen n now varies across worlds (2.65,3.45; heldout 3.15); A and thermal activation Q/R
are jointly unknown and scored. The candidate can select stress and temperature with the
same 12-call budget and unchanged log-noise sigma=0.03. Sliding worlds have overlapping
thermal responses, so temperature alone does not reveal the supported/unsupported label.
The reference fits the joint model from public inputs and charged assays.

The prior two weak sliding worlds had true curvatures 0.007/0.006 under a noise floor about
0.03 and should not have been treated as cleanly separable. They now have true curvatures
0.2501707249 / 0.2159040914, both inside the requested 0.1-0.3 intermediate region.

Reproduce the shortcut sweep and fresh-noise audit with
`uv run python benchmarks/EarthScience/GlenFlowLawDiscovery/references/shortcut_probe.py`.

## Shortcut probes and ablations

An adapted 20/63/200 stress scan, four repeats each at 255 K, guesses Q/R=6000 and sweeps
threshold t=0.01..0.60. Best development score is 0.658965667 at t=0.03; heldout is 0.
The original 0.995439 / 0.000 result belongs to the retired scalar-exponent contract.
Joint stress-temperature reference: 0.961088 / 0.930015, with correct refusals on all
current unsupported worlds. Empty refusal baseline and the shipped Newtonian guess score zero.
This exposes the remaining strength of a generic joint regression; it does not establish hardness.

## Fresh-noise identifiability check

4000 fresh Gaussian panels, seed 20260908, sigma=0.03, four repeats at each of
20/sqrt(4000)/200 kPa. For a positive curvature threshold 0.12:

| world | true curvature | P(detect) |
|---|---:|---:|
| pure Glen 71001 | 0 | 0.000 |
| sliding 72003 | 0.250171 | 1.000 |
| sliding 82003 | 0.215904 | 0.999 |

This checks observable separation only; it is not independent scientific validation.

## Construction errors and lineage

The old score reduction depended on noise-indistinguishable worlds. It is retired, not
renamed or used as supporting evidence. The evaluator structure is adapted from
EarthScience/AMOCTippingRefusal; the nearest research-task neighbours are ComplexBoseLaw
and EnzymeKineticsLaw. Confidence now has an explicit calibration metric and the axes
include their supported/unsupported denominators. Lineage remains incomplete_legacy.

## Robustness and model draws

Functional tests check continuous exponents, temperature response, budget/shape handling,
separable intermediate sliding and baseline zero. No LLM calibration or long-horizon evidence
exists. The new contract invalidates prior candidate scores; it does not repair old runs.
