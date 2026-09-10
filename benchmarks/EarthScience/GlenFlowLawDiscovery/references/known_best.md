# GlenFlowLawDiscovery — family enlarged; admission band now reachable

## Current status

The two-window log-linear reference scores 0.576653 development / 0.620010 heldout.
That drop is from adding a supported GBS family the reference does not label, not from
weakening the fit, deleting the temperature arm, or adding noise. Glen and Newtonian
worlds still recover at the previous residuals (development 0.937233 / 0.990751 / 0.955280).
This PR remains draft until the maintainer re-checks the admission band.

## Mechanism repair

Three viscous families are supported: Glen n in [2.6,3.6], Newtonian n=1, and
Goldsby–Kohlstedt-style grain-boundary sliding with n in [1.65,2.05]. A and thermal
activation Q/R remain jointly unknown. Unsupported worlds are Weertman sliding mixtures,
stress-independent plugs, and a stress-dependent exponent n = n0 + k log10(τ/τ0) that
curves log-log for a different physical reason than sliding. The same Arrhenius factor
multiplies the sliding term C*τ as the creep term; a temperature-independent C would have
been a free discriminator and is not used.

The shipped reference is unchanged: six public stress-temperature points, repeated assays,
joint log-linear fit, curvature refusal, and two n-windows (Glen, Newtonian). GBS n around
1.8 falls between those windows, so the reference abstains on every GBS world.

The prior two weak sliding worlds had true curvatures 0.007/0.006 under a noise floor about
0.03 and should not have been treated as cleanly separable. They now have true curvatures
0.2501707249 / 0.2159040914, both inside the requested 0.1-0.3 intermediate region.
Development n(τ) curvature is 0.20 (k=0.20 on a geometric stress grid).

Reproduce the shortcut sweep and fresh-noise audit with
`uv run python benchmarks/EarthScience/GlenFlowLawDiscovery/references/shortcut_probe.py`.

## Shortcut probes and ablations

An adapted 20/63/200 stress scan, four repeats each at 255 K, guesses Q/R=6000 and sweeps
threshold t=0.01..0.60. Best development score is 0.395379 at t=0.03; heldout is 0.
That is below the two-window reference (0.576653 / 0.620010). Empty refusal baseline and
the shipped Newtonian guess score zero. A candidate that added a third n-window for GBS
could outscore this reference; that is the intended headroom.

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
and EnzymeKineticsLaw. Confidence uses the world's in-family status as its Brier target,
independent of the decision to abstain; invalid submissions receive zero calibration credit.
Blanket refusal scores 6/11 / 5/8 on calibration, not a perfect 1. The axes
include their supported/unsupported denominators. Lineage remains incomplete_legacy.

## Robustness and model draws

Functional tests check continuous exponents, GBS as a third supported power law, n(τ)
curvature, sliding Arrhenius on C, budget/shape handling, separable intermediate sliding
and baseline zero. No LLM calibration or long-horizon evidence exists. The new contract
invalidates prior candidate scores; it does not repair old runs.

## September 9 maintainer audit and the family enlargement that followed

[Owner review](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/29#issuecomment-5594780263)
asked to enlarge the mechanism space rather than sabotage the reference. The previous
two-family reference scored 0.961088 / 0.930015 with saturated refusal. After adding GBS
and n(τ), and giving sliding the same Arrhenius factor as creep, the same two-window
algorithm scores 0.576653 / 0.620010, with FDR 0 and correct refusal 1 on every
unsupported world, and with coverage 0.6 because it abstains on GBS. Maintainer ablations
of the old two-family reference (no refusal 0/0; no temperature arm 0.658965/0.649475;
six unreplicated assays 0.880940/0.467374) remain historical measurements of that
algorithm; they are not the current score.
