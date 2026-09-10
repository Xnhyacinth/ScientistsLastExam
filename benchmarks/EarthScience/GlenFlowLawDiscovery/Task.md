# GlenFlowLawDiscovery

## The question

This reduced creep model is
`v = A * tau^n * exp(-activation_temperature * (1/T - 1/255))`.
Three viscous families are in play:
Glen's exponent varies continuously over [2.6,3.6]; Newtonian creep has n=1;
Goldsby–Kohlstedt-style grain-boundary sliding (GBS) has n in [1.65,2.05].
Amplitude A and activation_temperature (Q/R, in kelvin) are also unknown.
A resolvable basal-sliding mixture, a stress-independent plug, or a stress-dependent
exponent that curves log v versus log tau is outside the family.

You have 12 charged `measure(stress_kPa, temperature_K=255)` assays returning ln v
with Gaussian noise of standard deviation 0.03. The finite noise realization is deterministic;
repeated calls have distinct draws. The thermal factor is a reduced Arrhenius hypothesis,
not a claim of a validated glacier model. The same factor multiplies every viscous term
that depends on stress, including a sliding mixture when that mixture is present.

## What you implement

```python
def identify_flow_law(problem, measure):
    ...
    return {"family": "glen"|"newtonian"|"gbs", "n": ..., "log_A": ...,
            "activation_temperature": ..., "confidence": ...,
            "abstain": False}
```

### `problem` keys

| key | meaning |
|---|---|
| `stress_bounds_kPa` | inclusive `[20, 200]` |
| `temperature_bounds_K` | inclusive `[245,265]` |
| `reference_temperature_K` | 255 |
| `glen_exponent_bounds` | `[2.6,3.6]` |
| `gbs_exponent_bounds` | `[1.65,2.05]` |
| `measure_budget_calls` | 12 |
| `family_names` | `glen`, `newtonian`, `gbs` |
| `rate_law` | the stress/temperature law above |
| `measurement_model` | `measure` returns `ln v` |
| `abstain_when` | sliding or a stress-dependent exponent curves the slope, a plug is stress-independent, or n is outside the named families |

Spending past the budget fails the world closed.

## Relation and distinction

- `Physics/ComplexBoseLaw` also recovers an exponent with family refusal; this task
  jointly identifies creep amplitude, exponent and thermal response across three viscous families.
- `SystemsBiology/EnzymeKineticsLaw` uses budgeted assays of a saturation law; here
  the experimental controls are stress and temperature.
- Not `Oceanography/AMOCTippingRefusal`: that is a fold in a scalar climate
  ODE. This is a rheological exponent in ice.
- Not `Turbulence/WallClosureDiscovery`: a wall mixing-length formula, not Glen
  creep.
- Not PR #20 `IceObservationNetworkDesign`: that **places sensors**. This
  recovers the flow law from budgeted speed-vs-stress assays, or refuses.

## Scoring

Correct-family joint recovery is
`exp(-(abs(n-n_true)/0.1 + abs(log_A-log(A_true))/0.3 + abs(Q_over_R-Q_over_R_true)/1000)/3)`.
Wrong family or refusal on a supported world gives zero; correct refusal on an unsupported
world gives one. The mean is normalized above always-abstain and clipped to [0,1].
Mechanism, false discovery, refusal, coverage and confidence calibration are reported separately,
with supported/unsupported counts. Confidence is the probability that a supported flow family
applies to the world; its calibration target is the world's in-family status. Invalid
submissions receive zero calibration credit. Always-abstain has combined score zero.
Held-out metrics are evaluator-only.
`sle.contract_lint` is importable and free to call for shape checks; the evaluator validates
submissions independently. Non-refusals require finite log_A and nonnegative activation_temperature.

Glen (1955), Weertman (1957), Paterson and Budd (1982), *Flow parameters for ice sheet modeling*,
DOI 10.1016/0165-232X(82)90010-6, and Goldsby and Kohlstedt (2001), *Superplastic deformation of ice*,
DOI 10.1029/2000JB900336, motivate the viscous families and the temperature-dependent creep factor.
These specific parameter ranges and synthetic worlds are benchmark choices, not transcribed experimental data.
