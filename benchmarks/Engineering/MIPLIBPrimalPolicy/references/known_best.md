# Frozen MIPLIB primal anchors

Snapshot date: 2026-09-06. Status membership is frozen to MIPLIB
`open-v29.test` (2026-01-26), and objectives to `miplib2017-v36.solu`
(2026-01-26). The open list is retained; the solufile URL and hash are
recorded without redistributing its bytes in `source_manifest.json`.

| instance | early feasible baseline | frozen best-known reference | status |
|---|---:|---:|---|
| comp12-2idx | 391 (solution 1) | 277 (solution 5) | open |
| scpk4 | 327 (solution 1) | 318 (solution 7) | open |

After running `python references/fetch_solution_assets.py`, every value above
is recomputed from the corresponding literal assignment by the exact task
oracle. The solution files remain ignored local prerequisites rather than
redistributed repository files. Independently, all four assignments passed the patched
MIPLIB native checker with linear tolerance `1e-6`, integrality tolerance
`1e-5`, and zero reported maximum violations. The patched source and its
objective-offset fix are identified in `source_manifest.json`.

“Open” is MIPLIB's current status label, meaning no solve has been reported;
it is not a proof that a specific model or time budget cannot match the frozen
incumbent. The instances and historical solutions are public. Replaying or
memorizing solution 5/7 can reach score one, so score one is an on-ramp rather
than evidence of new optimization research. A strictly feasible assignment
below 277 or 318 would beat this frozen snapshot, but must be freshness-checked
against MIPLIB before any public record claim.
