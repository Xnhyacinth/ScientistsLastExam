# FourSettingMomentCertificate — exact SOS on I_4422^{13} with a frozen moment pool

## Scientific setting

Alice and Bob each have four binary measurements. Brunner and Gisin (arXiv:0711.3362)
list 26 tight Bell inequalities for that scenario. This task uses **`I_{4422}^{13}`**,
printed in full in that paper's Appendix A, not `I3322` and not a free word-budget SOS
on the sibling `BellBoundCertificate` task.

The Collins–Gisin table is

```
         |  -2  -1  -1   0
    ---------------------
     -2  |   0   1   1   1
     -1  |   1  -2   1   1
     -1  |   1   1  -1   1
      0  |   1   1   1  -1     ≤ 0
```

Converted to ±1 correlators by `P(A)=(1+a)/2` and `P(AB)=(1+a+b+ab)/4`, then multiplied
by 4 to clear denominators. Exhaustive enumeration of the 256 deterministic strategies
gives classical maximum **0**. The affine form `1 + I_CG` is quoted in arXiv:1811.11820
as `L=1`, `Q=1.25`, so the two-qubit quantum value of `I_CG` is **0.25**. A certificate
proving a bound below 0.25 is reported, not scored.

The open part is **which extra NPA-2 moments to spend a Hamming-weight budget on**.
The frozen 24-word pool contains all 16 mixed-party words A_i B_j, plus the
same-party pairs A0A1, A1A0, A2A3, A3A2 and B0B1, B1B0, B2B3, B3B2.
Each instance allows 8, 12 or 16 extras on top of nine NPA-1 words. Words outside
this declared pool are rejected. Mixed-party words supply constraints unavailable to the
former same-party-only pool.

The evaluator never solves an SDP. Floats are rejected.

## Your task

Implement:

```python
def build_certificate(instance):
    """Return {"basis": [...], "squares": [{"weight": ..., "vector": ...}, ...]}."""
```

`instance` contains:

| key | value |
|---|---|
| `name`, `settings` | instance id and `(4, 4)` |
| `functional` | correlator coefficients of the ×4 stored form |
| `scale`, `offset` | reported bound is `(beta + offset) / scale` |
| `extra_budget` | Hamming weight `k` of extra moments |
| `moment_pool` | the frozen list of allowed extra words `[[A-letters, B-letters], ...]` |
| `max_basis` | `9 + extra_budget` |
| `max_squares`, `max_word_letters` | caps |
| `max_numerator`, `max_denominator` | rational magnitude caps |
| `free_bound` | exact level-one certificate bound 5/8, the zero of the scale |
| `catalog_sos_bound` | same 5/8 free certificate bound |
| `score_one_bound` | included full-pool rational certificate bound, approximately 0.4553306767 |
| `full_pool_certificate_bound` | same as `score_one_bound` |
| `best_known_quantum_value` | 0.25 |

`basis` words are `[A-letters, B-letters]` with setting indices in `{0,1,2,3}`, already
reduced (`A_i A_i` is illegal). Extra words must occur in `moment_pool`. Weights and
vector entries are integers or `[numerator, denominator]` pairs.

## Scoring

Mean over budgets k=8,12,16 of logarithmic progress in the gap to 0.25:

```text
max(0, log((0.625 - 0.25)/(bound - 0.25))
       / log((0.625 - 0.25)/(score_one_bound - 0.25)))
```

Score one is supported by an exact rational certificate over the entire pool. It is a
builder-computed witness, not a published optimum and not a guarantee that each smaller
budget can reach it. The free certificate and full-pool certificate are re-expanded by tests.
Scores above one mean a stronger exact bound than that witness. Below 0.25 is reported
and scores zero. Numerical optimization is permitted for proposal construction, but the
submitted operator identity must hold exactly.

## Tools and scope

- NumPy/SciPy only. No CVXPY, no MOSEK, no network.
- Only edit `solution.py`; keep `build_certificate(instance)`.
- Do not read `verification/` or `frontier_eval/`.

## Relation to nearby tasks

- **BellBoundCertificate** is I3322 plus CHSH, with a free word budget. This functional
  is `I_4422^{13}` and the extras are a Hamming subset of a frozen pool.
- Sphere packing certificates are Cohn–Elkies functions, not Bell SOS.
