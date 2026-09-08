# GlenFlowLawDiscovery

## The question

This reduced creep model is
`v = A * tau^n * exp(-activation_temperature * (1/T - 1/255))`.
Glen's exponent varies continuously over [2.6,3.6]; Newtonian creep has n=1.
Amplitude A and activation_temperature (Q/R, in kelvin) are also unknown.
A resolvable basal-sliding mixture or stress-independent plug is outside the family.

You have 12 charged `measure(stress_kPa, temperature_K=255)` assays returning ln v
with Gaussian noise of standard deviation 0.03. The finite noise realization is deterministic;
repeated calls have distinct draws. The thermal factor is a reduced Arrhenius hypothesis,
not a claim of a validated glacier model.

## What you implement

```python
def identify_flow_law(problem, measure):
    ...
    return {"family": "glen"|"newtonian", "n": ..., "log_A": ...,
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
| `measure_budget_calls` | 12 |
| `family_names` | `glen`, `newtonian` |
| `rate_law` | the stress/temperature law above |
| `measurement_model` | `measure` returns `ln v` |
| `abstain_when` | sliding mixes the slope, or n is outside the family |

Spending past the budget fails the world closed.

## Relation and distinction

- `Physics/ComplexBoseLaw` also recovers an exponent with family refusal; this task
  jointly identifies creep amplitude, exponent and thermal response.
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
with supported/unsupported counts. Always-abstain is exactly zero. Held-out metrics are evaluator-only.
`sle.contract_lint` is importable and free to call for shape checks; the evaluator validates
submissions independently. Non-refusals require finite log_A and nonnegative activation_temperature.

Paterson and Budd (1982), *Flow parameters for ice sheet modeling*,
DOI 10.1016/0165-232X(82)90010-6, motivates temperature-dependent creep. These specific
parameter ranges and synthetic worlds are benchmark choices, not transcribed experimental data.
