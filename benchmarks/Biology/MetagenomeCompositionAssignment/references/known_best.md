# MetagenomeCompositionAssignment — coarse-screen ambiguity revision

## 1. Scientific endpoints and scope

Fourteen taxa, sixty markers and ten panels; initial panel plus two charged
follow-ups, each with 12000 reads. Four strain pairs have distinct diagnostic
panels; exactly two contribute one member each. Three or four total components
have continuous abundances. Two pairs of these groups share conditional initial
marker profiles, so an initial fit alone cannot resolve community membership.
This is a disclosed synthetic prior. Other panels distinguish the groups as well
as strain identity. The legal full-resolution endpoint remains attainable.
Read depth, count-noise model, seeds, abundance tolerance and scoring were not
changed. All reference
profiles are positive; library generation is category-blind, and inadequate
samples remain inside all marginal envelopes but outside the reference span.
The model estimates source proportions at calibrated equal total marker yield,
not empirical cell abundances or clinical quantities.

## 2. Frontier calibration

Three independent tool-free Codex CLI 0.153.4 first proposals, gpt-5.6-terra,
high reasoning, tested clean frozen source `b75dc6cebae38bc66feb5f5e38fb29268af0dc6f`. Each generation received
only the public task prompt, baseline and search-visible baseline feedback;
no repository, reference, previous candidate or model tools were mounted.
Generation budget 900 seconds, evaluation budget 600 seconds. All submitted code
was evaluated unedited in the Linux candidate sandbox. These are local CLI
checks requested by the contributor, not registered batch_evolve API calibration.
No cross-model ranking is established; calibration_runs remains empty.

A repository-native `batch_evolve.py --run-role calibration` run was then made
after merging upstream main, on clean source
`b35783af7326fb6ed6aa75d93129891f3d30c6b6`. Configuration was one
`greedy_rewrite` proposal, normal feedback, seed 0, gpt-5.6-terra through the
Responses wire, high reasoning, a 16000 output-token cap and a 900-second runner
timeout. The valid proposal scored 0.743401678 versus the zero baseline and
0.827795949 reference, using 2998 input and 9853 output tokens in 274.676 seconds.
The trusted ledger recorded two complete requests and receipts with no
infrastructure failure. Candidate SHA256:
`5d71305d46f3614439751a063badc86338103e548e5978764439c2124885bea4`.
The local report SHA256 is
`d27b4f6c3ab298977acf592565aeba0ee72b9dbd1132999f530f7afb5c87ebde`.
The raw report remains uncommitted under the contributor's audit-file policy,
so the card does not claim a repository-resolvable calibration artifact.

After removing the proposed repository-wide shared wrapper, the same formal
one-proposal protocol was repeated on clean source
`226b26344e1b1497872e87c40cad719a1d4ef38f`. The task-local wrapper was outside
the proposal's mounted agent files; Task.md, the baseline and the evaluator were
unchanged. The valid proposal scored 0.750256148 development and 0.777317035
held-out, below the 0.827795949 reference, with zero false claims and complete
alias recovery and library refusal on both splits. It used 3052 input and 11989
output tokens in 370.335 seconds. The ledger recorded two requests and two
receipts with no incomplete or infrastructure-failure attempts. Candidate
SHA256: `7b7ce2b18d3765c06168a3825f42175c2aa98c2b29f88d786c636622933156ad`.
Local report SHA256:
`bc89792d8ca5bd0191637af9a023e29cac2c7d4c22aec92960aa3f55d86820be`.
That raw report is also intentionally uncommitted.

After PR review reduced implementation-specific reference details in the public
prompt, the same one-proposal protocol ran on clean source
`1b641fa79609376065c85095d28c06e6adf00d31`. The valid proposal scored
0.734877700 development and 0.745303334 held-out, below the reference, with zero
false claims and complete alias recovery, refusal and coverage on both splits.
It used 3072 input and 9175 output tokens; the full run, including baseline and
proposal evaluation, took 323.635 seconds with no infrastructure failures.
Candidate SHA256: `b5f80b9e586aef7a1131171fa557134ab3bb83452ce54bd08b261dbe261bfc4b`.
Local report SHA256:
`541909cbe3ebeaea9c70ac6621b82e3cf5f572569b37250d795eb172c45cac55`.
The raw report remains intentionally uncommitted.

coarse0: valid=1.0; 0.745179412/0.744529192; wall 221.384s; SHA256 `9bbac7448354329b33f8f24c07b25f65b31e01749dfb042d57cd8b1a2edc3177`.

coarse1: valid=1.0; 0.728135743/0.744529192; wall 292.779s; SHA256 `05ec9101d1938067a6f7c27f777a6036da63125102af567d2146fca051231a9d`.

coarse2: valid=1.0; 0.747862698/0.744292723; wall 113.438s; SHA256 `9c103846171f77ab3dd782cf9ab9ac163ec0c5853e74b9020aac3f48ed97d75b`.

## 3. Reference and independent checks

The input-only reference uses sparse reporting-unit supports, conditional
multinomial likelihood and the lowest-BIC support for two-call utility design.
BIC model weights order the first query by predictive model discrimination;
then the utility plan is updated after that observation. Final inference uses
a joint full-library
deviance check and a sparse fit. Development-selected 500-bin rounding is a
numerical reporting choice, not biological precision. Neither averaged unresolved
profiles, BIC weighting nor local normal utility is exact posterior inference.
Reference 0.827795949/0.828551628.
Exactly three of the twelve development worlds are inadequate-library worlds,
and the reference correctly refuses all three. Subtracting the 0.25 floor therefore
makes `combined_score` equal `development_mechanism_score`. Claim precision,
alias recovery, refusal and discovery coverage are all 1 (false-discovery rate
is 0), so the remaining normalized development headroom, 0.172204051, comes only
from abundance error and half-credit avoidable unresolved groups.
The actual Python 3.10/SciPy 1.10.1 sandbox reproduces both aggregate scores from
Python 3.11/SciPy 1.11.4. Independent conditional-odds, graph resolution, legal
full-credit, initial-profile ambiguity, panel conservation, category-blindness,
label permutation, permanent budget invalidation and malformed output tests are
included. All 81 task/card/maturity/entrypoint tests pass under Python 3.10;
the Linux contribution gate also passes.

## 4. Capability ablations and planning comparisons

| Method | Development | Held-out |
| --- | ---: | ---: |
| Reference | 0.827796 | 0.828552 |
| No adaptive second query | 0.723671 | 0.778845 |
| Model-averaged utility planning | 0.814041 | 0.828552 |
| No adequacy check | 0.494463 | 0.495218 |
| Initial panel only | 0.145944 | 0.340638 |
| Without reporting rounding | 0.827363 | 0.827361 |
| Previous dense-planning method | 0.752475 | 0.761481 |
| Best of 45 fixed plans | 0.687528 | 0.673133 |
| Terra coarse0, independent first proposal | 0.745179 | 0.744529 |
| Terra coarse1, independent first proposal | 0.728136 | 0.744529 |
| Terra coarse2, independent first proposal | 0.747863 | 0.744293 |
| Terra formal `batch_evolve` first proposal | 0.743402 | not search-visible |
| Terra formal task-local-runtime first proposal | 0.750256 | not search-visible |
| Terra final-prompt formal first proposal | 0.734878 | not search-visible |

The evaluator, baseline and scientific-contract section of Task.md are byte-for-byte
unchanged from the frozen calibration source.

All controls use the same reporting precision except the explicitly unrounded
and historical dense-method rows. All 45 fixed query multisets use the same
sparse estimator; the development-selected plan is [7, 8]. Held-out scores
are validation, not a selection criterion. The reference leaves calibrated joint
support/abundance uncertainty and full count-outcome lookahead unimplemented.
No measured two-hour-search headroom is claimed.

## 5. Shortcut and reporting-precision probes

Final review found that selected-support utility improved the base development
score over model-average utility. The nine-grid scan (bins 5,10,20,40,50,100,200,
500,1000) was repeated on unrounded selected-support outputs; bins500 was best
on development, 0.827795949/0.828551628. This strengthened the reference only;
the task, baseline, evaluator, seeds and scoring were unchanged after the fresh
model draws. Scores remain attributed to their actual frozen source b75dc6c,
whose hidden reference used averaged utility and bins1000. The original averaged
reference scored 0.814843649/0.826067580. No scientific difficulty gain is credited
to these small numerical reporting choices.
Further grids on the final output give best 0.827795949/0.828551628
(bins 500). All 156 scalar refusal thresholds based on maximum
frequency, entropy and coordinate-envelope violation give development-best
0.716684838/0.495218294. Blanket refusal and the supplied single-taxon
baseline both score zero. No alias list, zero sentinel or fixed abundance values
are exposed.

## 6. Failed constructions and alternative methods

The first fourteen-taxon expansion, without initial-group ambiguity, still let
one independent Terra proposal match the reference: 0.847393579/0.838314196
versus 0.847383756/0.838250912. This counterexample prompted the coarse-screen
change. The other fresh proposals were 0.810118320/0.806087800 and
0.612433230/0.743193646; all were valid, not timeout failures.
Those three unedited programs transferred to the coarse-screen prototype at
0.769065596/0.751967043, 0.577508165/0.638600304 and
0.727101381/0.745303248. These are transfer probes, not fresh calibration.

An intermediate .9 interpolation toward equal initial profiles gave an unrounded
reference of 0.771580015/0.814451513. Exact shared profiles, selected as the
simpler construction and better development result, gave 0.814297774/0.827361227.
A public-prior-constrained latent-support method with optimistic first-query
support revelation gave 0.792109887/0.823903771; its joint-plan variant gave
0.795167594/0.819453468. Both failed to improve development and were rejected.
These are approximate alternatives, not complete Bayesian lookahead tests.

## 7. Noise robustness, reproduction and remaining evidence

Twenty additional count-noise repeats retain libraries and compositions:

- combined_score: mean 0.822652632, range 0.787819150–0.868717785.
- heldout_scientific_score: mean 0.834210895, range 0.794667350–0.874879925.

Both splits have zero false claims and correct library refusal throughout the
twenty repeats. Raw logs remain ignored locally.
`verification/analysis.py --noise-repeats 20`
reproduces the current ablations, fixed plans, reporting/scalar scans and repeats.
The observed method/candidate gaps do not prove ranking across different models
or resistance to longer optimization. External domain review, a
repository-resolvable calibration artifact and maintainer protocol acceptance
remain outstanding.

## Historical expansion evidence (not current calibration)



### 1. Scientific endpoints and scope

The current construction has fourteen taxa, sixty markers, ten panels and
four competing query-dependent pairs. Exactly two pairs contribute one member
each in every world; three or four total components have continuous abundance.
This public synthetic prior preserves a legal full-resolution two-call design.
Reads (12000 per observation), tolerance (.05), all 24 seeds and scoring are
unchanged from the ten-taxon reconstruction. Equal calibrated total marker yield
is assumed; these are source proportions, not empirical cell abundances.
Libraries remain category-blind and strictly positive. Inadequate mixtures remain
outside the reference span but inside every panel's coordinatewise envelope.

### 2. Frontier calibration

Three independent tool-free Codex CLI 0.153.4 first proposals used gpt-5.6-terra,
high reasoning, frozen clean source `5d91fef427cefaa5b2e7826a9e2fc9bfd07624e4`. Only the public task prompt,
zero-score baseline and filtered baseline feedback were mounted. No repository,
reference solution, prior candidates or model tools were available. Generator
budget 900 seconds; candidate budget 600 seconds. This is contributor-requested
local CLI testing, not registered batch_evolve API calibration; calibration_runs
remains empty. No cross-model ranking or long-horizon resistance is established.

hard0: valid=1.0, development 0.810118320, held-out 0.806087800, wall 182.473s, SHA256 `4cb46574a7a221820b3d9095e8977cf83dd6c3e180a61b7683e506d0349b958b`.

hard1: valid=1.0, development 0.612433230, held-out 0.743193646, wall 103.016s, SHA256 `e52777c291f0f2dd9d4d2a79698e0ad089171e2ec5a70ee0fbc484427fa618c7`.

hard2: valid=1.0, development 0.847393579, held-out 0.838314196, wall 52.575s, SHA256 `3f1ff77e5191c23ff1b9d779bf56847dd7c8e7696b33593d454cb612686a7603`.

### 3. Reference and independent checks

The reference fits all one-to-four-unit supports with conditional multinomial
likelihood, retains up to 24 supports within 16 BIC points, and uses approximate
BIC weights for planning. It plans two calls by local abundance/resolution utility,
orders them using predictive model discrimination, and replans after the first
observation. A conservative full-library deviance test rejects inadequate worlds.
Final selected-support abundances are unrounded. Averaging unresolved profiles,
BIC weights and normal-utility estimates are approximations; the method is not
exact posterior inference. The public two-active-pair prior is not enforced in
its support enumeration. The old dense method remains available as `infer`.

Reference 0.847383756/0.838250912, valid=1,
zero false claims, alias recovery and refusal both one. Python 3.10/SciPy 1.10.1
in the actual Linux candidate sandbox reproduces both aggregate scores exactly
from Python 3.11/SciPy 1.11.4. Independent conditional-odds, graph-resolution,
full-credit endpoint, four-panel mass conservation, label permutation and strict
contract tests are included. Forty task tests pass under Python 3.11; eighty task/card/maturity/entrypoint
tests pass under Python 3.10. Contribution gate passes.

### 4. Capability ablations and planning comparisons

| Method | Development | Held-out |
| --- | ---: | ---: |
| Sparse-support reference | 0.847384 | 0.838251 |
| No adaptive second query | 0.823067 | 0.838251 |
| Use selected model instead of model-average utility | 0.847384 | 0.838251 |
| No adequacy check | 0.514050 | 0.504918 |
| Initial panel only | 0.209373 | 0.570131 |
| Previous dense-planning reference | 0.764570 | 0.785895 |
| Best of 45 fixed query plans | 0.696572 | 0.754095 |
| Terra hard0, fresh first proposal | 0.810118 | 0.806088 |
| Terra hard1, fresh first proposal | 0.612433 | 0.743194 |
| Terra hard2, fresh first proposal | 0.847394 | 0.838314 |

The model-average utility ablation ties the reference on both splits; no distinct
benefit is claimed for this component. Adaptation helps development only in the
base panel. Fixed-plan selection uses development only; all 45 multisets were
tested with the same sparse estimator. The winning fixed plan is [6, 8].
A prototype scan blending resolution-only and precision-aware utility at weights
0, .25, .5 and 1 produced the same aggregate scores; the original precision-aware
method was retained. There was no held-out-driven selection.

### 5. Shortcut and quantization probes

Nine rounding grids (bins 5,10,20,40,50,100,200,500,1000), applied to the same
legally acquired reference outputs, did not beat the unrounded reference.
Best development grid: 1000 bins, 0.846872116/0.838153125.
All 156 scalar refusal thresholds were evaluated on legally acquired observations
using max frequency, entropy and envelope violation. Development-selected best:
0.736272645/0.616028690, below the reference. Blanket refusal and the
supplied nearest-single-taxon baseline both score zero. Historical candidate
transfer results are separate from fresh proposal calibration.
Transferred draw0: valid=1.0, 0.714560342/0.739153521.
transfer results are separate from fresh proposal calibration.
Transferred final2: valid=1.0, 0.724918797/0.746378108.

### 6. Construction errors and repairs

The ten-taxon version offered only one query-dependent pair, so generic dense
planning was too competitive. Four diagnostic pairs and only two active pairs
now make sample-specific measurement choice material. Diagnostic panels conserve
mass and are distinct; exactly two active pairs preserve attainability instead
of imposing an artificial ceiling. Construction priors are disclosed. Malformed
panel checks were updated for the expanded menu. Candidate budget was increased
from 120 to 600 seconds to allow enumeration; timeout is not scientific evidence.
No scoring tolerances, noise or held-out seeds were tuned to suppress models.
The original ten-taxon evidence is retained below as historical evidence only.

### 7. Robustness, reproduction and remaining evidence

Twenty additional paired count-noise repeats, keeping each world's library and
composition unchanged:

sparse: development mean 0.865229106, range 0.821868925–0.900235279; held-out mean 0.863405727, range 0.823508532–0.899023809.

dense: development mean 0.787045311, range 0.741615433–0.826318511; held-out mean 0.798219759, range 0.765776379–0.822464996.

The sparse reference beats the dense control in all twenty paired repeats in
both splits; both methods have zero false claims throughout. This establishes
a method gradient under count noise, not separation among different models.
Raw experiment records remain ignored locally. Run verification/analysis.py for
ablations, fixed plans, rounding and scalar probes; add --noise-repeats 20 for
noise checks. Compare `assign_composition` and `infer` for paired method repeats.
Input-only exact constrained support inference and full sequential lookahead
remain proposed capabilities; no two-hour search headroom is claimed. External
domain review, registered calibration and maintainer protocol acceptance remain
outstanding.

### Historical ten-taxon reconstruction (not current calibration)

### 1. Scientific endpoints and scope

The withdrawn family had nine worlds, a public alias list, a zero-weight sentinel,
and originally four constant abundance values. Continuous abundances repaired
rounding leakage but not the two lookup decisions. Historical reference values
0.694504, 0.723821 and 0.643541 belong to successive withdrawn revisions, not to
this reconstruction. The original constant-rounding probe reached 0.942 / 1.

The new panel has 24 worlds, ten taxa, 36 positive marker profiles and a budget of
two follow-up panels of 12000 reads after an initial panel of the same depth.
True mixtures have two to four active taxa and continuous abundances. Near aliases
are determined by matrix geometry and acquired panels, not a supplied name list.
Group claims include total abundance. A precise operational Hellinger-based
reporting convention replaces an undefined claim of universal identifiability.
It is not asserted to be a confidence theorem for arbitrary mixtures.

Outside-library probabilities have a component orthogonal to the reference span
but stay within every panel's coordinatewise template envelope. The distinguishing
signal is a joint shared-marker residual. No marker has zero reference probability.
The legal single-taxon baseline and blanket refusal score zero. Full credit has
a legal acquisition/reporting witness using perfect composition knowledge; that
is an endpoint sanity check, not an input-only algorithm or noise-free evidence.

### 2. Frontier calibration

One isolated, tool-free Codex CLI 0.153.4 first proposal using `gpt-5.6-terra`
(high reasoning) ran against clean frozen revision `a862e09d62361c2103a192c1d5c46c70e3c13b6c`.
It scored valid=1, 0.878964592 / 0.808010267 with zero false claims in 22.773 seconds.
Candidate SHA256: `d22a2069c97dcceac00c4e798509f5aef9fe8cde025e202636635a970e6d2f4a`.
The generator received only the public task prompt and baseline; no repository,
reference, previous candidates or model tools were accessible. It implemented
sparse-support likelihood/BIC inference and acquired two panels. This is a local
CLI check authorized by the contributor, not a registered `batch_evolve.py` API
calibration. The stronger reference and Task.md ablation disclosures below were
added afterward; the independent draws on the revised contract are recorded below.
The task remains a candidate, with no scientific admission, external review or
measured long-horizon headroom claimed.

Two further independent CLI first proposals ran on clean `47898d87fc265781859203cb85a0b18229f54c7d`,
with the stronger reference and public ablation disclosures:

| Draw | Valid | Development | Held-out | Runtime |
| --- | ---: | ---: | ---: | ---: |
| final0 | 1 | 0.818622329 | 0.646583921 | 19.863 s |
| final1 | 1 | 0.890706517 | 0.793915053 | 93.761 s |

Both used the same isolated CLI condition and made zero false claims. The first
missed supported/alias worlds through conservative support/adequacy decisions;
the second enumerated sparse supports. These are functioning scientific proposals,
not syntax failures counted as difficulty. SHA256 respectively:
`5638f43dcae0154ca0151ee65a2c371de3a31844f87c50e2c7c0a6770650cdfc` and
`5529a1ce4855d53fd1eb240cfafe3b11201f733e31451b11d1a5ae441668ea0f`.
A final source freeze follows the latest-main integration and model-source
clarifications. The merged-tree contribution gate, certification audit and 91
targeted tests (plus 13 subtests) pass. A new isolated first proposal on clean
`471e87b` scored valid=1, **0.904085928 / 0.830015655**, with zero false claims,
complete alias recovery and library refusal, in 90.807 seconds. Candidate SHA256:
`7f0c04ae8275706eeaa300d3afcff2bb7e743933a5f627f9f5e8e456c67c155e`.
The complete metrics dictionary is identical under secure Python 3.10/NumPy
1.24.4/SciPy 1.10.1 and Python 3.11/NumPy 1.26.4/SciPy 1.11.4. It uses legal
information-based acquisition and conditional mixture fitting. All three revised
first proposals are below the reference; neither this comparison nor the earlier
pilot is represented as a registered API run. The contributor requested direct
Codex CLI testing; acceptance of this protocol is still a maintainer decision.

One additional post-hoc refinement on clean `38794da` started from the
highest-development first proposal and received only project-allowlisted feedback.
It scored valid=1, **0.780695738 / 0.838331429**, with zero false claims, in
92.173 seconds; it did not improve the development incumbent. Candidate SHA256:
`c52966ef835184d5280c513326465daa908f447ccf7f0c79ee81098716c5998b`.
The CLI reported a WebSocket-to-HTTPS timeout fallback before completing its turn;
manual review confirmed no model tool calls and the unedited reply was evaluated.
This single unsuccessful refinement neither counts as an independent first draw
nor establishes long-horizon headroom or resistance to all future optimization.

### 3. Reference and independent checks

`verification/reference_assignment.py` is a self-contained input-only solver.
It fits the correctly conditioned multinomial likelihood and compares all fifteen
legal two-call multisets using Fisher-information volume. It buys the first
panel of the selected plan, updates the mixture estimate, then selects the second
panel by approximate expected abundance/resolution credit. It checks joint
deviance and refits the detected sparse support. Final complete compositions are
rounded and renormalized with development-selected 1% precision. The deviance
threshold conservatively retains all multinomial degrees of freedom; it does not
miscount boundary mixture coefficients as ordinary free parameters. It uses no
world IDs, hidden weights, private group names or outside-library labels.

An analytic two-taxon conditional-odds solution independently checks the likelihood
fit. Union/find in the oracle and graph traversal in the reference independently
check resolution groups. Tests verify positive profiles, outside-span deviations,
coordinatewise envelope inclusion, group-mass conservation, charged streams,
immutable scoring inputs, strict output mass and malformed-request rejection.
Marker row permutations and arbitrary taxon renaming preserve the results.

### 4. Capability ablations and planning comparisons

All evaluations obey the two-call budget. The original joint-plan reference on
`a862e09` scored 0.893727002 / 0.844498769. Its 1% rounding probe exceeded it on
development (0.904085928 / 0.836304253), requiring a stronger reference.
The oracle, seeds, score endpoints and baseline have not changed in response.

| Method | Development | Held-out |
| --- | ---: | ---: |
| Current sequential reference | 0.919921457 | 0.853898566 |
| No adaptive second query | 0.904085928 | 0.836304253 |
| No sparse-support refit | 0.883929735 | 0.815565031 |
| No library-adequacy check | 0.586588124 | 0.520565232 |
| Initial observation only | 0.296225827 | 0.536589245 |
| Best development-selected fixed plan among 15 | 0.887688379 | 0.796299309 |
| No rounding | 0.913678965 | 0.855579522 |
| Blanket refusal | 0 | 0 |

The reference has zero false claims, complete intrinsic-alias recovery and all six
library refusals. World-level coverage is one; this means at least one correct
claim per supported world, not a separate guarantee of complete unit recall.
Rounding improves development but slightly worsens held-out, and is not itself a
scientific capability. Posterior sparse-support uncertainty and full sequential
experimental design remain unimplemented; actual headroom has not been measured.

Eight earlier joint-design variants ranged from 0.847511 to 0.893727 development.
A single-step greedy first query followed by adaptive selection reached
0.926996945 / 0.826175748 after largest-remainder precision tuning. It was rejected
as the reference because 20 noise repeats produced development false-discovery
rates up to 0.068966 and scores down to 0.775280. This higher development score
is retained as a counterexample to any assertion that the selected reference is
optimal. The joint-plan-first adaptive strategy has zero false claims in the same
20 repeats. No scientific difficulty claim rests on the rejected strategy's
errors or on reporting quantization.

### 5. Shortcut and quantization probes

All 156 distinct scalar threshold/direction refusal rules on six count summaries
were evaluated against otherwise full, legally acquired composition fits.
Features are maximum marker fractions, entropy and coordinatewise envelope excess,
initially and across acquired panels. The best development-selected rule scores
0.701166 / 0.520565. The sweep exhausts distinct classifications on development;
it is construction evidence, not independent model calibration.

Reporting grids 1/50, 1/100, 1/200, 1/500 and 1/1000, rounded then renormalized,
score 0.892268, 0.919921, 0.904880, 0.911969 and 0.914189 development.
Held-out scores are 0.830564, 0.853899, 0.858658, 0.856908 and 0.854199.
The 1/100 choice was selected on development; held-out did not select it.
Applying further grids 0.01, 0.025, 0.05, 0.1 and 0.2 to the final reference gives
at most 0.915398 development. Old-constant rounding scores 0.481519 / 0.367562.
These comparisons do not show saturation or claim that every possible shrinkage
or rounding rule must be inferior. The old fixed-value task and its 0.942 / 1
shortcut remain withdrawn.

### 6. Construction errors and repairs

An exploratory query-dependent pair changed its total marker yield when its
unmeasured panel changed. That made group total abundance itself ambiguous.
The final generator conserves the changed panel's mass, leaving unmeasured
columns identical rather than proportional. Near-intrinsic aliases are below the
public resolution threshold at every permitted design.

A first shared-marker residual could still exceed an individual template envelope.
The final mismatch is explicitly inside all envelopes while outside the full
reference span. An initially weaker residual had inadequate power on one world;
its amplitude was increased before calibration, retaining all seeds and checking
all noise repeats. Earlier 6000-read prototypes and their scores remain local;
the final 12000-read model supplies the declared abundance accuracy. These are
construction decisions, not blind measurements or changes made after model draws.

The original callback also accepted malformed numeric types and allowed query
interleaving to change the sampled stream. The repaired contract permanently
rejects invalid requests and binds draws to panel/replicate. Public input mutation
cannot change scoring tolerances, names or resolution thresholds. Invalidity in
any single world zeros both aggregate scores.

### 7. Robustness, reproduction and remaining evidence

The prior frozen reconstruction passed the full CI-core environment suite:
1123 passed, 50 skipped and 452 subtests (Python 3.10, NumPy 1.24.4,
SciPy 1.10.1). Its secure reference score matched Python 3.11 exactly.
The final reference revision adds 16 malformed-output aggregate-zero cases and a
repeat/budget check: all 39 task tests and 21 card/maturity tests pass in the CI-core
environment. The contribution gate passes; secure Python 3.10 and Python 3.11
reference scores match exactly at 0.919921457 / 0.853898566. The final model check
and its cross-version equality are recorded in Section 2. The actual external
wrapper also reproduces the reference and keeps held-out metrics out of the public
file. It deliberately does not put a full-report sidecar beside search-visible
output; full diagnostics remain available through a separate trusted `sle eval`.

Twenty noise repeats of the selected sequential reference give mean development /
held-out 0.890011 / 0.875063, with ranges 0.858851–0.927694 and
0.836352–0.913021. All repeats have zero false claims, complete alias recovery
and library refusal. Fixed-seed evaluation is deterministic; these repeats measure
sensitivity to independent count noise and do not guarantee performance on new
ecological libraries. The original joint-plan reference's repeat means were
0.891099 / 0.872862. Thus the adaptive method's fixed-panel gain is not claimed as
a uniform improvement across sampling noise.

```sh
python -m pytest -q tests/test_metagenome_composition.py
python benchmarks/Biology/MetagenomeCompositionAssignment/verification/analysis.py --noise-repeats 20
python scripts/check_task_contribution.py --task Microbiology/MetagenomeCompositionAssignment --timeout 120
```

All data and code are original. MetaPhlAn (10.1038/nmeth.2066) and StrainEst
(10.1038/s41467-017-02209-5) motivate marker/strain abundance inference; they do
not validate this reduced synthetic model. No papers, external source code or
datasets are redistributed. Raw local experiments and global audit snapshots
are not included in the task contribution.


The model citation GRAMMy (Xia et al. 2011,
[doi:10.1371/journal.pone.0027992](https://doi.org/10.1371/journal.pone.0027992))
supports read-distribution mixtures and likelihood abundance estimation. Our
conditional marker counts are a reduced extension, with calibrated equal total
marker yield; cell abundance, genome size and marker copy-number inference are
outside scope. The public resolution rule is not attributed to that paper.

Novelty was also compared with all 47 tasks in Frontier-Eng
[Appendix A, v1](https://arxiv.org/html/2604.12290v1) and the current full
[TASK_DETAILS](https://github.com/Einsia/Frontier-Engineering/blob/main/TASK_DETAILS.md).
The retrieved inventory has 78 table rows (84 names after expanding EngDesign),
not the historical 95 named in CONTRIBUTING; SHA256
`11be782992273d8131b077c6d7f30e78c0389e8db1d2af6494388621b043bbf5`.
The single-cell denoising, perturbation prediction and modality prediction entries
produce expression predictions, not budgeted microbial mixture assignments with
abundance-bearing resolution groups and joint library refusal. No identical
problem class was identified in this internal comparison; external novelty
review remains pending. Neither external catalog nor local audit snapshots are
included in this contribution.

The current Frontier-Eng repository tree was additionally checked for unlisted
Task.md files. `SingleCellAnalysis/denoising_ttt` is expression-matrix imputation;
`ProteinDesign/FixedBackboneDesign` optimizes amino-acid identities on a fixed
backbone. Neither is the same microbial mixture-assignment problem.
