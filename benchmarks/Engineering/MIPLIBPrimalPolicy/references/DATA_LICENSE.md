# Data licensing and attribution

The two MPS instances are redistributed unchanged from MIPLIB 2017. The
upstream submission metadata records `license: cc-license`; the MIPLIB 2017
paper identifies that submission-form choice as Creative Commons
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

- `comp12-2idx`: submitted by Matias Sørensen; creators Gerald Lach and
  Marco E. Lübbecke; owner recorded as “Free for all usages”.
- `scpk4`: submitted and created by Shunji Umetani; owner Osaka University.

Canonical license: https://creativecommons.org/licenses/by-sa/4.0/

The compressed MPS files have not been modified. MIPLIB publishes four
solution artifacts from its instance pages, with the solution submitters and
dates recorded there, but those pages do not state a separate per-solution
license. The solution bytes are therefore **not redistributed by this
branch**. `fetch_solution_assets.py` downloads them directly from the official
URLs into an ignored local directory and verifies their frozen hashes. A
clean checkout without those local assets fails evaluation as a missing
trusted dependency; it does not substitute or synthesize a solution.

MIPLIB citation: A. Gleixner et al., “MIPLIB 2017: Data-Driven Compilation of
the 6th Mixed-Integer Programming Library”, Mathematical Programming
Computation 13 (2021), https://doi.org/10.1007/s12532-020-00194-3.
