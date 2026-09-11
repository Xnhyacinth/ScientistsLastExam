# Independent world session isolation repair — 2026-09-11

Twenty existing task evaluators reused the candidate process across independent scientific worlds. A real Linux CandidateProxy regression reproduced all twenty leaks before the repair, then passed all twenty tests after it. This repairs process isolation; it does not requalify difficulty, certify tasks, or establish compatibility of historical scientific scores.

## Source and minimal repair

- Main baseline: `3069479717c2d0db0b040babb42390bdcbb60cb1`.
- Test-only reproduction: `554d5004891fd7252a643841d88a8835ee0beea4`.
- Fixed task source: `06246029139b44c8fca10478e07957953ef6e027`.
- Runtime source SHA-256 remains `8159a99d54894dd304e3ac48956cd05d4389f12a041f5d5d86a2c079641c2c86`.
- Regression: [`tests/test_world_session_isolation.py`](../tests/test_world_session_isolation.py).
- Per-task source/package hashes and exact test identities: [`world_session_isolation_2026-09-11.json`](world_session_isolation_2026-09-11.json).

The task patch is exactly three inserted lines in each of twenty evaluator files: obtain the candidate's `reset_session` method and call it when callable, immediately before that world's top-level candidate invocation. Plain function candidates remain supported. Reset errors remain within the existing candidate error handling. Runtime implementation, sandbox restrictions, instance generation, world seeds, scoring mathematics, normalizers, and candidate programs are unchanged.

The reset is inside the shared world/instance helper or inside the per-world loop. It therefore applies before the first world and at the development-to-held-out boundary. It is never inserted inside a laboratory callback or between reanalyses of an already submitted design under shifted physical conditions.

| Boundary inspected and repaired | Task packages |
| --- | --- |
| `_evaluate_world` | EnzymeKineticsLaw; OccupancyDetectionDesign; PhaseDiagramDiscovery; ReactionMechanismFitting; ForcedSignalAttribution; GravityInversion; UPbConcordiaInference; ModalDamageAttribution; BlackBoxGroupIdentification; DiscrepantMeasurements; HiddenCouplingNetwork |
| `_score_instance` | NMRSpectrumFitting; HeatExchangerDesign; TrussWeightMinimization |
| Each world in `_score_split` | SpinSystemInference; GraphFromDistances; SequenceLawRecovery; HamiltonianLearning; RadialVelocityPlanets |
| Each of six worlds in `evaluate` | InterventionalSCM |

## Actual Linux evidence

Tests ran in the independent `sle-world-isolation-20260911` worktree on g450 using `/usr/bin/python3` 3.8.10, NumPy 1.24.4, SciPy 1.10.1, the temporary pytest installation `/tmp/sle-pytest38-20260911`, and one thread for OpenBLAS/OMP/MKL/NumExpr. Original scientific checkouts, runs, dependencies, and frozen records were not modified.

| Fixed test plan | Before source | Fixed source |
| --- | --- | --- |
| Twenty real CandidateProxy boundary tests | 20 failed, 0 errors, 0 skipped; 13.85 s | 20 passed, 0 errors, 0 skipped; 34.24 s |
| Existing runtime regression for repeated calls, returned controller callbacks, and explicit reset | Not required for the reproduction | 1 passed, 0 errors, 0 skipped |

The twenty task tests exercise 44 world boundaries: one actual development world and one actual held-out world for each of nineteen split tasks, and all six InterventionalSCM worlds. A trusted adapter invokes a fixed, test-owned state probe in a real sandbox and then returns a constant refusal to the original world scorer. Scientific world data are not sent to this probe. No task score is asserted or published, and there are zero scientific `evaluate_candidate` calls and zero model draws in this repair plan.

Each test warms the worker before the first world, then checks that the next world starts with fresh candidate globals, imported-module attributes, and tmpfs. Each world also makes two test-owned RPC callbacks while checking that its own state persists. Before the repair, all twenty tests fail specifically because the prior state survives. After the repair, each world sees fresh state, exactly one reset, and both callbacks complete. The separate existing runtime test also confirms that two top-level calls without a reset and returned-controller calls retain the same session, and an explicit reset creates fresh process/tmpfs state.

The after-run coverage report requires the twenty test identities from the fixed case list; no absent or skipped case can satisfy it. JUnit files and their digests are recorded in the JSON. The public artifact contains source hashes, aggregate counts, test identities, and limitations, without per-world scientific outputs or credentials.

## Historical evidence remains a separate obligation

Changing the evaluator changes all twenty task package hashes. The JSON records both the main-baseline and fixed hashes, computed from the Git source tree and checked against the framework's current package hashing function. The unchanged runtime hash does **not** make historical task records current-equivalent.

No old raw record, expected source hash, migration declaration, frozen-cohort preflight binding, certification status, or global evidence report was changed. In particular, HeatExchangerDesign and TrussWeightMinimization participate in the existing frozen-preflight cohort. Their frozen candidate artifacts must be re-evaluated in the sandbox under the integrated source and their compatibility evidence reviewed before any new binding is recorded. That follow-up is outside this engineering test result.

The focused regressions exercise the common world boundaries, not every scientific world or each task's full reference solution. Changes in scientific outcomes for stateful candidates are possible and are the reason old evidence cannot simply be relabeled. No scientific score equivalence or current admission result is claimed here.
