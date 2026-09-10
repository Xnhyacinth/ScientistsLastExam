# UnimolecularFalloffLaw — 100 bar is still falloff, scientific admission pending

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

The reference scores **0.9613366667 development / 0.7277200000 heldout**, valid, with zero
false discovery on both splits. The Arrhenius baseline is valid and scores zero.

## Why the three-assay shortcut existed

In-family worlds previously placed Pr(300 K, 100 bar) in the thousands, so a single in-budget
high-P reading was already k_inf. `references/three_assay_probe.py` reconstructs the
[September 9 owner counterexample](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/26#issuecomment-5594779434)
with that reference's own family predicate (`f_obs < 0.82`, Fcent=0.40). Against the old
12–13 assay scan it scored **0.746885 / 0.808437** versus **0.731992 / 0.776872**. Fitting the
full pressure curve (commit `bb6c950`) raised the reference to **0.936433 / 0.953523**, but
left the 100 bar wall at k_inf and seeded noise by call index.

## Scientific repairs

Noise is now a hash of `(world seed, T, P)`. Repeating the same assay returns the same draw;
extra budget buys new conditions. In-family (and two-channel) A0 is set so
Pr(300 K, 100 bar) = 2: Lindemann k(100 bar)/k_inf = 2/3, and Troe is lower. `log_k_inf` is
an extrapolation from the falloff, not a wall reading.

After those changes the same three-assay probe scores **0.198579 / 0.324198**, below the
repaired reference on both splits. A 2304-point grid that treated 100 bar as k_inf is not
re-run: the wall is no longer k_inf, so that search is not a witness here. No model draws
or pairing Δ were taken.

Held-out Troe still trades k_inf against Fcent inside the observable window; that is leftover
headroom, not a claim that the reference saturates the task.

## Remaining scientific hold

The package remains a candidate. Broader identifiable regimes, server-held worlds, and
independent review are still required. The held-out split is evaluator-only.

## Model and provenance scope

The reduced symmetric broadening formula omits the full Troe c/d terms. This is a
benchmark approximation, not the full published law. Original source checks (September 8)
identify DOI 10.1002/bbpc.19830870218 as Gilbert, Luther and Troe, *Theory of Thermal
Unimolecular Reactions in the Fall-off Range. II. Weak Collision Rate Constants* (1983).
Lineage remains incomplete_legacy and independent scientific review is pending.
