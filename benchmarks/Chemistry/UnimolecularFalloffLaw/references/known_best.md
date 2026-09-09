# UnimolecularFalloffLaw — complete pressure fit, scientific admission pending

## Reference and reproduction

`verification/reference_falloff.py` fits the public reduced Lindemann/Troe pressure law
jointly for log k_inf, log Pr and Fcent. It uses 14 log-spaced pressure observations at
300 K and four higher-temperature observations for pressure-order refusal, within the
unchanged 18-assay budget. BIC compares the two fitted families; Fcent is not a fixed 0.40.
Only existing NumPy/SciPy and public observations are used.

```
uv run python -m sle eval --task UnimolecularFalloffLaw --allow-uncertified \
  --candidate benchmarks/Chemistry/UnimolecularFalloffLaw/verification/reference_falloff.py --timeout 30
```

The updated reference scores **0.9364326667 development / 0.9535225000 heldout**, valid,
with zero false discovery on both splits. These values were reproduced through the real
sandbox. The former scan scored **0.7319923333 / 0.7768720000**. It spent 12–13 assays
but hardcoded Fcent=.40 and treated the 100-bar measurement as k_inf; its documentation
incorrectly said it estimated Fcent from the middle of the curve.

## Baseline

The one-assay pressure-independent Arrhenius guess always publishes Lindemann. It is valid
and scores zero, including false claims on unsupported channels.

## Shortcut and budget evidence

`references/three_assay_probe.py` independently reconstructs the [September 9 owner counterexample](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/26#issuecomment-5594779434):
using the former reference's own family predicate, it scores **0.746885 / 0.808437**.
The earlier 0.565/0.698 probe always emitted Lindemann and understated this shortcut.
The complete curve fit beats the stronger three-assay rule on both fixed splits.

An in-process diagnostic varied only the noise seeds across 16 deterministic panels
(seed offsets 100000 through 1600000); world parameters and score were unchanged.
Full-minus-three-assay development gaps range **0.071850–0.244938**, mean **0.201187**;
heldout gaps **0.100845–0.189645**, mean **0.146796**. This is evidence for the benefit
of using the full curve in this family, not fresh-parameter or model calibration.
Noiseless tests recover Fcent=.25 and .65 rather than the old fixed guess.

## Corrections to proposed repairs

Current call-index seeds already give independent noise for repeated settings. Seeding solely
by (T,P) would repeat identical noise and prevent averaging, so that suggestion was not adopted.
The release score is normalized above blanket refusal, not divided by reference score:
0.746885 never became 1.0 merely because it exceeded the old reference.

## Remaining scientific hold

A more competent reference now approaches the task ceiling (fresh-noise means about
0.935/0.957). This does not establish hard or long-horizon search. Broader identifiable
parameter/family regimes and matched shortcut/model evidence are still required; the PR
remains Draft without a cosmetic scale change or weakened reference. The heldout split
is evaluator-only; no model runs or frozen calibration records were regenerated.

## Model and provenance scope

The reduced symmetric broadening formula omits the full Troe c/d terms. This is a
benchmark approximation, not the full published law. Original source checks (September 8)
identify DOI 10.1002/bbpc.19830870218 as Gilbert, Luther and Troe, *Theory of Thermal
Unimolecular Reactions in the Fall-off Range. II. Weak Collision Rate Constants* (1983).
Lineage remains incomplete_legacy and independent scientific review is pending.
