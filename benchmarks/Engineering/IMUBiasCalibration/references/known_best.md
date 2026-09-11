# Known best - active IMUBiasCalibration, schema 2

## Reference

The truth-blind witness selects eighteen settings by approximate D-optimal design over the
joint supported/fault regression span. It fits the upper-triangular twelve-parameter model
by known-noise weighted least squares, residualizes each declared one-parameter fault
alternative against that null, and compares the resulting chi-square statistics with
Bonferroni familywise error control at 0.05. It reports the winning fault's response axis,
or the supported calibration and predictions at three transferred poses/temperatures.

Design and regression use only public settings and acquired measurements. No hidden seed,
family or coefficients enter the reference. The Gaussian one-parameter survival probability
is evaluated exactly as erfc(sqrt(statistic/2)), using the standard math library. Remaining
headroom comes from finite information, noisy coefficient recovery and near-threshold model
separation, not an intentionally missing calibration step. It is not a published sensor SoTA.

At executable revision `835db79c9f0709a466ff5f6978bd29f30a81af13`, reference development /
held-out scores are **0.7186990470 / 0.5522152347**. Matrix recovery alone is 0.632562 / 0.658447;
coverage is 12/12 / 11/12, correctly localized refusal is 9/9 / 8/9, and false claims are
0/12 / 1/12. The complete metrics match across two sandbox runs for all fifteen policies.
The external trusted-subprocess wrapper returns the same score; one isolated reference
evaluation took 8.01 seconds on the ali Linux host (Python 3.10.12, NumPy 1.26.4).

## Baseline

The baseline makes a confident supported claim for the factory identity matrix with zero
bias/drift, without measuring. The evaluator normalizes so never-refusing calibration and
all blanket-refusal variants are zero. The anchor is not a tuned reference score.

Supported quality weighs bias 0.25, drift 0.25, matrix 0.30 and transferred prediction 0.20.
Their public tolerances are 0.035 m/s^2, 0.0014 m/s^2/C, 0.006 Frobenius error and
0.07 m/s^2 RMS vector prediction error. These represent calibration-error scales, not
hardware specifications. Correct fault refusal requires both type and response axis.
The headline is clip((sum(quality)-U)/S,0,1)*(correct_refusals/U). Mechanism is separately
matrix recovery quality over all supported worlds; false discovery, refusal and coverage
retain their own counts/denominators. Confidence has no headline weight.

## Ablation ladder

`verification/calibrate.py` tests six and twelve measurements, central temperatures only,
sequential rather than information-designed settings, diagonal-only calibration, and removal
of each fault diagnostic. It also tests fixing every predicted fault axis, blanket refusal
and never-refusing claims. Every selected policy is independently replayed twice through the
Linux trusted driver and bubblewrap; the complete metrics must match.

| Policy | Development | Held-out |
|---|---:|---:|
| Full reference, eighteen measurements | 0.718699 | 0.552215 |
| Six measurements | 0.000000 | 0.004345 |
| Twelve measurements | 0.356836 | 0.254128 |
| Central temperatures only | 0.047489 | 0.169275 |
| Sequential settings | 0.165670 | 0.434979 |
| Diagonal-only calibration | 0.000000 | 0.000000 |
| Without thermal nonlinearity test | 0.312466 | 0.206246 |
| Without thermal cross-axis test | 0.312466 | 0.348838 |
| Without parasitic-acceleration test | 0.312466 | 0.206246 |
| Fixed fault axis | 0.134237 | 0.004212 |
| Baseline / all-abstain / never-refuse | 0.000000 | 0.000000 |

The multiplicity correction remains fixed at twelve in all diagnostic ablations, so removing
a test does not silently loosen the remaining tests' decision threshold.

## Shortcut probes

Two 900-policy grids fit the supported triangular calibration but use only whitened residual
RMS and peak thresholds to label faults and choose the largest-residual response axis. One
uses the reference's public-input design and one takes settings sequentially. Thresholds
and fault labels are selected using development only. Public transcripts of this fixed
trusted probe are cached for grid scoring; the selected policies are independently sandboxed.
The registered grid is not an exhaustive upper bound over all possible algorithms.

Selected information-designed probe: **0.072900 / 0.024859**. Selected sequential probe:
**0.025579 / 0.075309**. Exact parameter grids, selected thresholds and aggregated diagnostics
are in `experiments/imu_bias_calibration_active_review_2026-09-08.json`; the code reproduces
the selection and replay without inspecting held-out data during selection.

## Model calibration

The record `experiments/imu_bias_calibration_deepseek_calibration_2026-09-07.json` is strictly
historical passive-schema evidence. Its Windows in-process values cannot calibrate schema 2.
Intermediate Linux passive-schema revisions are also historical: after fixing metric
accounting and missing held-out motion coverage, Flash's first proposal scored 0.986466 on
development, exceeding the reference's 0.985196; Pro scored 0.973504. An earlier Pro draw
was invalid because its generated abstention path called .tolist() on a Python list.
Those observations triggered the scientific redesign rather than a reference-score adjustment.
Fresh active-schema model results must identify their exact clean source revision and
effective thinking configuration. DeepSeek evidence alone is not independent frontier admission.

Final source `835db79`, seed 29, temperature 0, 16000-token cap, thinking disabled in every
actual chat request, greedy_rewrite with normal feedback and calibration role:

- Pro: one fresh valid proposal, development 0 / held-out 0.016946. It uses all eighteen
  observations; supported science quality is 0.455583 / 0.454794, but correctly localized
  refusals are 0/9 / 4/9 and drift recovery is zero.
- Flash: initial proposal invalid because a three-axis weight matrix was passed to a per-axis
  fit. A separately logged one-proposal retry is valid at 0/0, uses all eighteen observations,
  and has development supported science quality 0.673478 but no correctly attributed refusals.
  The invalid draw is not scientific difficulty evidence; zero does not mean no useful recovery.
- Earlier active source `3f34617`: a separate three-step Flash search progressed from zero to
  0.001036; the third proposal was invalid. Pro's three-step search remained at zero. These are
  historical runs, not final-oracle values. The unchanged development-selected Flash program
  was migrated to final source and scores **0.020591 / 0.056366**. This is a replay, not a new draw.

All eleven review-era runs and their fifteen proposals, including the failures, are compactly
recorded in `experiments/imu_bias_calibration_active_deepseek_2026-09-08.json`. No failed
draws were silently excluded. Scientific code was frozen before the final draws; the measured ladder is recorded
here, not in Task.md, without changing candidate input data,
scoring or search-visible keys. These small-sample checks do not replace independent review.

## Construction errors

1. The original passive laboratory made all data free and faults conspicuous. An early Flash
   draw exceeded the first reference; changing a few thresholds did not remove on-ramp difficulty.
2. Maintainer review found absent top-level discovery axes, missing denominators, recovery credit
   on supported abstentions, free prediction credit on wrong refusals, and two invalid citations.
3. Fixing those defects exposed missing held-out motion coverage; adding that family corrected
   the split but did not solve simplicity. A fresh first proposal still reached the reference.
4. The active redesign removes the free table, expands six coefficients to twelve, moves faults
   toward single-measurement noise, and requires axis localization. Budget enforcement is sticky:
   catching the callback's exception cannot restore validity. Query evidence cannot be fabricated.
5. The first active ablation showed no development benefit from the motion diagnostic. Its
   centered-square basis had maximum 2/3 and smaller RMS than the other fault bases. Using the
   standard second Legendre polynomial P2(u)=(3*u^2-1)/2 defines alpha as its aligned-pose
   amplitude and gives a comparable directional RMS, without altering the public amplitude
   range, measurement noise, seeds, calibration coefficients or reference decision threshold.

No model program, provider configuration, prompt, key or raw request is committed. Historical
failures are retained; they are not evidence for the current score or reference difficulty.

## Robustness and limitations

Both development and held-out splits contain twelve supported worlds and nine faults, three
per named family, with independent seeds, settings, noise and coefficients. Public settings
and uncertainties have identical distributions across families. Noise on repeated requests
is deterministic by world, setting and call number but independent across repeats. Every
world starts a new candidate session. This remains a finite, public procedural family, not
real-device replication; unknown mounting rotation, hysteresis, mixed faults and full
six-degree-of-freedom motion are outside scope. A server-held family and external domain
review are still required for certification. No full-repository test suite or maintainer-owned
global evidence refresh is run for this contribution.

Final executable validation: full task gate 15/15; related pytest 74 passed plus 18 subtests;
nineteen malformed-output variants and sticky invalid-setting/over-budget tests; CLI
raises/empty/wrong_type all scored invalid with zero evaluator crashes. Mechanism and
held-out diagnostics remain outside the closed SEARCH_VISIBLE_KEYS allowlist. Baseline,
reference, ablation and probe determinism compare complete metrics, not only the headline.

Reproduce from a clean Linux checkout:

```bash
python -m sle eval --allow-uncertified --task Sensors/IMUBiasCalibration
python benchmarks/Engineering/IMUBiasCalibration/verification/calibrate.py --output /tmp/imu-review.json
python scripts/check_task_contribution.py --task Sensors/IMUBiasCalibration
python scripts/check_evaluator_survives_bad_candidates.py --task Sensors/IMUBiasCalibration
python -m pytest tests/test_imu_bias_calibration.py tests/test_task_cards.py tests/test_discovery_contract_lint_is_documented.py tests/test_benchmark_layout.py tests/test_measurement_health_preflight.py tests/test_scientific_materiality.py tests/test_batch_runner.py -q
```

## Verified sources

- Woodman (2007), *An introduction to inertial navigation*, UCAM-CL-TR-696,
  DOI 10.48456/tr-696. Publisher record: https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-696.html.
  This supports sensor bias, scale and alignment-error modeling; the exact fault polynomials,
  triangular coordinate convention and temperature coefficients here are synthetic assumptions.
- Kiefer and Wolfowitz (1960), *The Equivalence of Two Extremum Problems*,
  DOI 10.4153/CJM-1960-030-4. Foundation for information-based experimental design;
  the greedy finite-catalog implementation is an approximation, not globally optimal design.
- Wilks (1938), *The Large-Sample Distribution of the Likelihood Ratio for Testing Composite
  Hypotheses*, DOI 10.1214/aoms/1177732360. General model-comparison background; with the
  known Gaussian noise and one linear added coefficient here the null chi-square law is exact.

Titles/identifiers verified against publisher/Crossref records on 2026-09-08. The removed
10.1109/5.554205 is Hall and Llinas's unrelated multisensor-fusion introduction; the removed
10.1109/TIM.2014.2325662 did not resolve. Neither is retained as supporting evidence.
