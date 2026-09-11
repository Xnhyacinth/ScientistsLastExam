# SparseVectorAudit: known best

## Admission repair status (2026-09-11)

The tables below retain the contributor's historical in-process measurements at PR head `4bb95061846a28a3025f4eb05cdd52210e12b11a`. They are not current Linux sandbox measurements. In particular, the original columns labelled false discovery used false claims / all worlds; that is a world-level fraction, not FDR. The repaired oracle publishes false claims / valid claims with explicit counts; zero claims remain unavailable under the metric contract. This correction does not change the mechanism score, worlds, seeds or anchors.

The previous first-query reference deliberately omitted later positions and is inadequate as an admission reference. `verification/reference_positional.py` now packages the existing positional method with original helper source inlined and no parameter changes. Source hashes and the exact adaptation are recorded in `.research/pr80_source_adaptation_2026-09-11.json`. The original method remains a no-later-position control. Fixed source-matched no-scan, no-library and no-confirmation programs are standalone, and the machine shortcut contract includes the historical strongest no-confirmation alternative as well as the full positional method without confirmation. The fixed pilot below now supplies measured expected scores in a separate card update; no model difficulty pass is implied.

The discrete compliance derivation, branch-coupling delta argument and truncation limits are in `references/compliance_argument.md`. Complete catalog novelty comparison and three genuine first proposals are now recorded below and in .research/pr80_admission_2026-09-11.md. Independent privacy-domain review remains pending.

The following historical narrative is retained for provenance; it does not override this current admission status.

## Independent fixed Linux method measurements (2026-09-11)

| Frozen candidate | Development | Held out | Dev false/claims | Held false/claims |
|---|---:|---:|---:|---:|
| Baseline | 0.000000 | 0.000000 | 12/12 | 6/6 |
| Complete positional reference | 0.819398 | 0.729870 | 0/6 | 0/3 |
| First position only | 0.570283 | 0.479870 | 0/5 | 0/2 |
| No scan | 0.176793 | 0.229870 | 0/2 | 0/1 |
| No library | 0.571429 | 0.500000 | 0/4 | 0/2 |
| Positional, no confirmation | 0.322314 | 0.000000 | 2/7 | 5/6 |
| Historical strongest fixed shortcut | 0.427426 | 0.000000 | 1/6 | 2/4 |

All seven candidates ran twice at clean source `5c5b358cdf47ec3ce1319fc722cc88bd4afcb0f2`.
Every one of the 14 runs was valid in all 12 development and six held-out worlds; each complete
metric pair was identical. Runtime: Linux Python 3.8.10, NumPy 1.24.4, SciPy 1.10.1, numerical
thread counts one, 300-second task timeout. The runtime source hash is
`e29d3b1d7b0e0f9f5b1b09a8c0a45ace098ad8790547d0333c1940e0a421bea9`; the only `sle/*.py`
change from main3069479 is the contributor's DataPrivacy logical-domain mapping. Full metrics
are private; scalar measurements and exact source hashes are in
`.research/pr80_method_qualification_2026-09-11.json`.

The full reference reaches 0.8193980000000003; both declared probes stay below the unchanged
10% margin threshold 0.7374582000000003. Each substantive capability ablation lowers the
score: later-position scanning, scanning as a whole, the library, and confirmation. This is
fixed candidate-method qualification, not a model difficulty or iteration result. The old
318-policy grid is author provenance; only its fixed reported strongest alternative and the
stronger positional no-confirmation alternative were re-evaluated here, without new grid
selection, seed tuning or changed worlds. The independent first-proposal comparison below was run after this fixed method pilot.

## Reference (truth-blind): a first-query dissent scan, a screened library, one confirmed pair

`verification/reference_library_scan.py`. It reads only the public problem and the counts that
`sample` returns, and it audits in three stages.

- **Scan.** For a query g above the threshold, the specification fixes how often the first output
  should still be F, and for a query g below it, how often it should be T. On a grid of four, on
  both sides, the reference runs a vector whose first query sits at that gap and whose other
  queries sit at the bottom of the range. It runs enough copies for the specification to expect
  eight dissents, and skips any grid point that would need more than 6000 runs. A grid point with
  no dissent is a branch that skips the noise. It walks the three values below to pin the offset,
  and confirms the straddling pair with Clopper-Pearson bounds.
- **Library.** It screens nine StatDP-style pairs (Ding et al. 2018), eight distinct vectors with
  every answer one step either side of the threshold, at 8000 runs a vector. For each pair and
  order the event is the prefix of outputs, sorted by empirical ratio, that maximises the plug-in
  loss with delta subtracted.
- **Confirm.** The best screened pair is rerun on fresh samples with everything left of the
  budget, 56000 to 65000 runs a side. A violation is claimed only if Clopper-Pearson bounds at
  level 0.2, split over the two sides, certify a loss above epsilon with delta subtracted.

| split | score | witness strength | false discovery | refusal | coverage | runs per world |
|---|---|---|---|---|---|---|
| development | 0.570 | 0.570 | 0.00 | 1.00 | 0.71 | 167493 |
| held out | 0.480 | 0.480 | 0.00 | 1.00 | 0.50 | 169123 |

World by world on the development split: the three noise-scale worlds are named at losses of
1.434, 1.180 and 1.066 against anchors of 1.443, 1.238 and 1.258, which score 0.981, 0.754 and
0.256. The two branch worlds whose branch covers the first query are named by the scan with an
infinite loss in 4950 and 4965 runs. The two whose branch starts at a later position are declined.
Held out, one noise-scale world is named at 1.244 against 1.266, scoring 0.919. The other is
declined, because its best screened pair has an exact loss of -0.46 behind a plug-in value of
2.77: the chosen event is barely above delta on one side.
One branch world is named by the scan in 14738 runs, and the branch world at positions 4 and 5 is
declined. Every world where the claim holds is declined.

What it leaves on the table, by design:

- **It scans the first query only.** A branch that begins at a later position is never reached,
  which costs three worlds, dev-branch-c, dev-branch-d and held-branch-a.
- **It confirms the event it chose on the screening counts.** It does not search for the pair and
  event with the best certifiable bound. The winner's curse on the screening counts picks events
  whose exact loss is below the anchor.

The recoverable headroom is the positional scan, `.research/sparse_vector_audit/headroom_positional.py`.
It is the same audit, with the down side tested at every position through one vector and the up
side through one vector per position on a grid of eight. It scores 0.819 on the development split
and 0.730 held out with no false discovery. It names both later-position development branches and
the held-out one, and gives back dev-noise-c, because the scan leaves less budget for the
confirmation.

## Model draws

Three predeclared, independent `gpt-5.6-sol` first proposals used `greedy_rewrite`, selection-blind feedback, one proposal per seed label, reasoning high and a 16384-token output cap. The model-condition hash is `967fb197a1603c8c9bd881997ba02cfde1336f0cbb2e1c3a369c3cec24d50d07`; immutable plan hash `8bc89f14b2ffd251113cc619f26cc5d05d785b6e74125c787122999f9894928d`. All cells are retained; there was no adaptive candidate retry or selection.

| Seed label | Development | Held out | Valid worlds | Reaches reference |
|---|---:|---:|---:|---|
| 0 | 0.21659171428571433 | 0.22160099999999994 | 18/18 | No |
| 1 | 0.2761347142857143 | 0.24126249999999996 | 18/18 | No |
| 2 | 0.2652197142857144 | 0.12217275000000004 | 18/18 | No |

The complete measured reference is 0.8193980000000003 development / 0.729870 held out. Each proposal has zero false claims, correct refusal 1.0 in both splits and genuine discovery coverage 2/7 development and 1/4 held out. The first-proposal criterion passes this comparison only; no iterative result or general model-hardness claim follows. Provider-reported returned-proposal usage is 52280 tokens (12441 input, 39839 output); price and possible failed HTTP-attempt usage are unavailable.

The original clean source is `c02e402f7ee709521c5843f6abd3256b6e57f872`, package `fc763f6e070e96cc5356234b3b3e1101ffb867bf6ba5bf4013a2b5ef4f02e94b`, contract `47ded87d94cbdb164dde218aed3f2922281a45ae11b98f42500d1d94e885fdd6`, runtime `e29d3b1d7b0e0f9f5b1b09a8c0a45ace098ad8790547d0333c1940e0a421bea9`. `experiments/sparse_vector_first_draw_review_2026-09-11.json` independently verifies six original evaluation receipts, the retained program bytes and all 42 private artifact hashes. Subsequent card/known-best updates do not change the agent-visible Task.md or scientific implementation. A separate six-evaluation retained-candidate replay establishes compatibility after those documentation edits; it adds no model samples and leaves original evidence immutable. External domain review and fresh server-held confirmation remain pending.

## Baseline: the classic pair, a count ratio, never declining

`solution.py`. It runs the vector with the first query one above the threshold and every other
query one below, and the vector with every query at the threshold, 2000 times each. It claims the
single output with the largest add-one-smoothed count ratio, in either order, at confidence 0.9.

| split | score | raw | false discovery | refusal | coverage |
|---|---|---|---|---|---|
| development | 0.000 | -0.583 | 1.00 | 0.00 | 1.00 |
| held out | 0.000 | — | 1.00 | 0.00 | 1.00 |

Every one of its witnesses has an exact loss of 0.83 or less. It is wrong in every world where
the claim holds, which the specification's compliance guarantees. It is also wrong in every world where the
claim fails, because its one pair never reaches a branch and its single-output event is not where
the noise-scale violations are. The normalisation takes it to zero.

## Difficulty ladder

`.research/sparse_vector_audit/ablation.py`, one reference choice changed at a time, graded seeds.

| strategy | development | held out | false discovery (dev / held) | coverage (dev / held) |
|---|---|---|---|---|
| reference | **0.570** | 0.480 | 0.00 / 0.00 | 0.71 / 0.50 |
| without the scan | 0.177 | 0.230 | 0.00 / 0.00 | 0.29 / 0.25 |
| without the library | 0.286 | 0.250 | 0.00 / 0.00 | 0.29 / 0.25 |
| screening at 4000 runs a vector | 0.400 | 0.250 | 0.00 / 0.00 | 0.43 / 0.25 |
| confirmation at level 0.05 | 0.426 | 0.480 | 0.00 / 0.00 | 0.43 / 0.50 |
| confirmation at level 0.5 | 0.570 | 0.480 | 0.00 / 0.00 | 0.71 / 0.50 |
| delta ignored in the library confirmation | 0.570 | 0.480 | 0.00 / 0.00 | 0.71 / 0.50 |
| the best screened pair claimed without confirmation | 0.427 | 0.000 | 0.08 / 0.33 | 0.86 / 0.75 |
| the scan's first zero claimed without confirmation | 0.037 | 0.000 | 0.17 / 0.33 | 0.71 / 0.75 |
| the scan at a fixed 2000 runs a point, no confirmation | 0.000 | 0.000 | 0.75 / 1.00 | 1.00 / 1.00 |
| the first design: two pairs, Bonferroni at 0.05, 4000 runs a vector, 40000 a side | 0.400 | 0.250 | 0.00 / 0.00 | 0.43 / 0.25 |
| **headroom**: the scan at every position | 0.819 | 0.730 | 0.00 / 0.00 | 0.86 / 0.75 |

Without the scan the branch worlds are gone. Without the library the noise-scale worlds are gone.
The confirmation is what makes the claims safe. Claiming the best screened pair without it
matches the reference's hits and adds a false discovery on the development split and two held out.
Claiming the scan's first zero without it names worlds where the claim holds. A scan at a fixed
run count finds zero dissents wherever the specification itself expects fewer than one, and
claims a violation there, including in the compliant-branch worlds, whose deviation is rarer than
delta. Screening at 4000 runs a vector picks worse events and loses two noise-scale worlds. A
level of 0.05 loses two. A level of 0.5 and ignoring delta in the library confirmation change
nothing on the graded seeds, because the library's events all have masses far above delta. Delta
matters in the scan, where the compliant-branch events live.

## Shortcut probe

`.research/sparse_vector_audit/probe.py`, 318 strategies in four families:

| family | strategies | best development | held out | best strategy |
|---|---|---|---|---|
| blind straddle guesses at every offset, either side, no runs | 100 | 0.000 | 0.000 | any |
| screen fixed pairs (the baseline pair or the library) at 1000 to 24000 runs a vector, claim the single output or the ratio prefix above a threshold of 1 to 4 | 176 | 0.248 | 0.008 | library at 16000 runs, single output, threshold 1.25 |
| the reference's first-query scan, then screen-and-claim | 24 | **0.427** | 0.000 | 8000 runs, threshold 1 |
| screen the baseline pair, confirm with Clopper-Pearson at 0.05, 0.2 or 0.5 | 18 | 0.000 | 0.000 | any |

The best strategy reaches 0.427 on the development split, 75 per cent of the reference, and 0.000
held out. It is the ladder's rung that claims the best screened pair without confirmation. On
the graded development seeds it happens to make only one false discovery, in a world where the
claim fails. Re-drawn with eight other seeds for the runs, it averages 0.063 on the development
split, from 0.000 to 0.427, and 0.029 held out, with fifty false discoveries in 144 world-runs.
The reference re-drawn the same way makes none. 289 of the 318 strategies score zero on the
development split. Every blind guess scores zero: one offset hits at most one world and is a
false discovery in the other eleven. So does every confirmed audit of the baseline pair.

## Construction errors caught on the way

- A compliant world whose implementation skipped the threshold noise redraw was cut. Its pure-DP
  loss was only 0.974, too close to epsilon to count as a trap for anyone and too far below it to
  count as a violation.
- A halved threshold noise with a cutoff above one has no compliance proof and a loss that is not
  monotone in the cutoff, so it is used only as a violating world, with a cutoff of one.
- The first reference confirmed the two best screened pairs, Bonferroni-split at 0.05, after
  screening at 4000 runs a vector, with at most 40000 runs a side. It scored 0.400 and 0.250. The
  winner's curse on 4000 runs chose events whose exact loss was far below their plug-in value.
  Held out, one noise-scale world's best screened pair had a plug-in value of 2.53 and an exact
  loss of 0.755. And 40000 runs a side cannot certify an anchor of 1.24 at 0.05, which needs
  65000 to 75000. The reference now screens at 8000 and confirms one pair with everything left,
  at level 0.2, since a missed claim and a false one each cost one world.
- With a false witness scoring zero in a world where the claim fails, the reference without its
  confirmation tied the reference at 0.570 on the development split. Its one false discovery fell
  in a violating world, where it cost nothing. A false witness now scores minus one there, so it
  costs one world wherever it is made. The rung falls to 0.427 and 0.000 held out.
- The headroom's first positional scan stepped the later positions' down side by eight and missed
  an offset of nine. It then sized the all-positions down vector for the first position alone. At
  small gaps the early positions halt most runs, so the last positions saw almost none, and a
  false alarm at gap four stopped the down scan. The vector is now sized by the last position's
  reach probability.
- The baseline's docstring, which the candidate reads, named the family of noise-skipping
  branches. It now says only that one pair finds what that pair happens to show. Task.md names no
  deviation family, offset or position.

## Robustness

`.research/sparse_vector_audit/robust.py` re-runs a candidate with every world's seed shifted, so
the runs change and the worlds do not. Over eight shifts the reference averages 0.446 on the
development split, from 0.395 to 0.570, and 0.440 held out, from 0.372 to 0.480, with no false
discovery in 144 world-runs. The graded seed is its best draw on the development split. The
headroom averages 0.659 (0.530 to 0.819) and 0.588 (0.500 to 0.730), with one false discovery in
144, in dev-compliant-branch-b on one shift. The no-confirmation rung averages 0.063 and 0.029
with fifty.

`.research/sparse_vector_audit/checks.py`: every module parses as Python 3.8, two evaluations of
the reference agree key for key, and declining everything scores 0.000 in both forms. In the
compliant worlds the library's best exact loss stays below epsilon. The compliant-branch worlds
have coupling bounds on delta of 2.7e-4 to 4.4e-4, and straddle masses of 2.6e-5 to 1.5e-4. Every
violating world's anchor is above epsilon. An exact-objective local search, 24 random starts and
the library with 200 steps each, finds at most 0.904 in the compliant worlds (0.633 at cutoff
two). The strongest events have a mass of 0.9 to 2.0 per cent on one side and 0.4 to 0.8 on the
other. Certifying the noise-scale anchors themselves at the reference's level takes 4000 to 34000
runs a side, and at 0.05 it takes 8000 to 75000. The test file checks 27 malformed candidate
shapes, including overspending, a patched budget and float, boolean, zero and oversized run
counts. All of them score valid 0, combined 0 and feasibility 0 without raising. The same vector
run twice gives fresh runs, and the counts do not depend on the order of calls. A reference
evaluation takes about one second in process.

At original author construction, not yet done: the sandbox half of `scripts/check_task_contribution.py` (no Bubblewrap on the build
machine), a frontier-model draw, the global evidence refresh.
