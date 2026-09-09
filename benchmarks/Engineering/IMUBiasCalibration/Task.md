# IMUBiasCalibration - design a temperature/pose calibration and attribute its failure

## Scientific setting

A stationary accelerometer has bias, temperature drift, scale error and non-orthogonal sensing
axes. Fitting thermal drift to a poorly chosen set of poses can absorb a different physical
effect. You control a limited calibration campaign, then must either publish a transferable
12-parameter calibration or identify the unsupported fault and its response axis.

The supported model is `a = M @ (g*u) + b + d*(T-T_ref) + noise`. `M` is upper triangular
with positive diagonal: three scale factors and three non-orthogonality coefficients. The
rigid mounting rotation is pre-registered, fixing this coordinate convention. Together with
three bias and three drift components there are twelve free coefficients.

With `x=(T-T_ref)/temperature_scale_c`, each unsupported instrument adds exactly one term:

- `thermal_nonlinearity`: `alpha*x*x` on an unknown response axis;
- `axis_misalignment`: `alpha*x*u[j]` on an unknown response axis `k`, with unknown `j != k`;
  this is temperature-dependent cross-axis response, not the constant non-orthogonality in M;
- `motion_contamination`: `alpha*(3*u[(k+1)%3]**2-1)/2` on response axis `k`, a reduced-order
  orientation-dependent parasitic acceleration that no constant affine calibration can absorb.

The signed fault coefficient has magnitude in `fault_amplitude_range_mps2`. Measurement noise
is independent Gaussian with the supplied per-axis standard deviations. Both signs occur;
faults need not be conspicuous in a single measurement. Uncertainty and available poses do
not announce the fault family. These are synthetic error models, not device specifications.

## Entrypoint and measurement budget

```python
def infer_imu(problem, measure):
    ...
```

No accelerations are supplied for free. Call `measure(setting_id)` to acquire one three-axis
measurement at a listed pose and temperature. Each call costs one unit, including repeats;
repeats have independent, deterministically seeded noise. You have `measurement_budget` units.
An invalid setting or any attempted overrun invalidates the submission even if you catch the
exception. A fresh candidate session is used for every instrument. Do not assume world order.

### Every problem key

| Key | Meaning |
|---|---|
| `schema_version` | 2, the active calibration contract |
| `gravity_mps2` | known gravity magnitude g |
| `reference_temperature_c` | temperature at which bias is defined |
| `temperature_scale_c` | normalization scale used only in the fault equations |
| `measurement_budget` | maximum number of callback calls |
| `measurement_model` | declared supported equation |
| `calibration_convention` | upper-triangular matrix and pre-registered mounting rotation |
| `diagnosis_values` | allowed diagnosis strings |
| `fault_models` | mapping with keys `thermal_nonlinearity`, `axis_misalignment`, `motion_contamination`, containing the equations above |
| `fault_amplitude_range_mps2` | lower and upper bounds on absolute fault coefficient |
| `abstain_when` | supported reason for refusing the affine calibration |
| `parameter_tolerances` | zero-credit error scales: `bias_mps2`, `drift_mps2_per_c`, `matrix_frobenius`, `prediction_mps2` |
| `settings` | available settings, each with `setting_id`, `temperature_c`, unit-vector `orientation`, and three-axis `noise_std_mps2` |
| `prediction_settings` | three transfer queries, each with `temperature_c` and unit-vector `orientation` |

The measurement response contains `setting_id`, `temperature_c`, `orientation`,
`noise_std_mps2`, unique `query_id`, and the three-element measured `accel_mps2`.

### Exact output keys

- `bias_mps2`: three finite numbers;
- `temperature_drift_mps2_per_c`: three finite numbers;
- `calibration_matrix`: finite 3-by-3 upper-triangular matrix with positive diagonal;
- `prediction_accel_mps2`: three finite three-axis predictions, in `prediction_settings` order;
- `diagnosis`: `supported`, `thermal_nonlinearity`, `axis_misalignment`, `motion_contamination`,
  or `undetermined`;
- `fault_axis`: integer 0, 1 or 2 for a fault diagnosis; otherwise `None`;
- `confidence`: finite numeric value in [0,1];
- `abstain`: boolean; true to decline publishing a supported calibration;
- `evidence_ids`: every acquired `query_id` exactly once, and no fabricated IDs. Empty is
  valid only when no measurements were taken.

All keys are required even when declining. A numerical placeholder is allowed when abstaining;
it must still satisfy shape and finiteness. Faults require both the correct diagnosis and axis.

## Scoring

On a supported instrument, an abstention or non-supported diagnosis scores zero. Otherwise
bias, drift and matrix qualities are `clip(1-error/tolerance,0,1)`, using Euclidean vector errors
and Frobenius matrix error. Prediction error is the RMS Euclidean error over the three transfer
queries. Supported quality q weighs bias 0.25, drift 0.25, matrix 0.30 and prediction 0.20.
Confidence is a separate squared-error calibration diagnostic, not free headline credit.
An unsupported instrument contributes one only for correctly labelled and localized refusal.

For S supported and U unsupported instruments, with R correct fault refusals, the split score
is `clip((sum(q)-U)/S,0,1) * R/U`. Both splits contain each family. This removes all reward
available from blanket abstention; the refusal multiplier also makes never-refusing fits zero.
Any invalid submission makes that split invalid with score zero, and an invalid split
on either side sets the reported headline to zero as well.

Separate development/held-out axes include:

- `mechanism_score`: matrix recovery quality summed over all supported instruments / S,
  including zero for missed or invalid claims; this is not the joint score;
- `false_discovery_rate`: wrong model-family claims / actual non-abstained claims, zero if none;
- `correct_refusal_rate`: correctly labelled and localized fault refusals / U;
- `discovery_coverage`: supported-world claims, including wrong diagnoses / S.

Their numerators and denominators, supported model accuracy, fault-axis accuracy, bias/drift/
prediction qualities and `attempted_discovery` are reported independently. Held-out and
mechanism diagnostics are not search-visible. The headline value is the development
score, but a valid submission is required on both splits.

## Relations and differences

- `StructuralEngineering/ModalDamageAttribution` localizes stiffness loss using modal ratios;
  here the design must separate tensor calibration, thermal drift and non-affine sensor error.
- `HeatTransfer/ConvectionDiffusionOpt` couples PDE identification to heater design; here the
  artifact is an inertial calibration matrix and a sensor-fault attribution, not a thermal field.
- `Sensors/QuartzCrystalMicrobalanceLab` infers resonance admittance and deposition from sweeps,
  rather than vector sensor calibration from temperature/pose interventions.

## Measured competence ladder

Linux sandbox calibration; development / held-out normalized scores:

| Policy | Development | Held-out |
|---|---:|---:|
| Information-designed, full calibration and fault tests | 0.718699 | 0.552215 |
| Six measurements | 0.000000 | 0.004345 |
| Twelve measurements | 0.356836 | 0.254128 |
| Central temperatures only | 0.047489 | 0.169275 |
| Sequential settings | 0.165670 | 0.434979 |
| Diagonal-only calibration | 0.000000 | 0.000000 |
| Without thermal fault test | 0.312466 | 0.206246 |
| Without temperature-dependent cross-axis test | 0.312466 | 0.348838 |
| Without parasitic-acceleration test | 0.312466 | 0.206246 |
| Fixed fault axis | 0.134237 | 0.004212 |
| Best designed-measurement residual-threshold grid | 0.072900 | 0.024859 |
| Best sequential-measurement residual-threshold grid | 0.025579 | 0.075309 |
| Factory baseline / blanket refusal / never refusing | 0.000000 | 0.000000 |

Each grid contains 900 policies selected on development only. These are registered probe
maxima, not bounds on all algorithms. Finite-budget calibration error and fault discrimination
leave room for improvement.

## Rules and sources

Only edit `solution.py`. Deterministic CPU Python, NumPy and SciPy are available.
`sle.contract_lint` provides free shape checks. No network, subprocesses, oracle inspection,
hidden-world assumptions or access to `verification/` are allowed.

Woodman, *An introduction to inertial navigation*, UCAM-CL-TR-696 (2007),
DOI `10.48456/tr-696`, motivates the sensor-error setting. Kiefer and Wolfowitz,
*The Equivalence of Two Extremum Problems* (1960), DOI `10.4153/CJM-1960-030-4`,
provides an experimental-design foundation. Exact fault polynomials are synthetic approximations.
