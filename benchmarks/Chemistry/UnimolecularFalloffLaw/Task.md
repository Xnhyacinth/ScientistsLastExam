# UnimolecularFalloffLaw

## The question

A unimolecular (or recombination) rate coefficient depends on both temperature and
pressure. In the Lindemann–Hinshelwood picture it interpolates between a third-body
low-pressure limit and a high-pressure limit. A reduced symmetric Troe *Fcent* law broadens that falloff.
A second, pressure-independent channel, or a rate that **falls** as pressure rises,
is outside this family: refuse.

You have **18** charged `measure(temperature_K, pressure_bar)` assays. They return
`ln k` (1/s) with frozen noise.

## What you implement

```python
def identify_falloff(problem, measure):
    ...
    return {"family": "lindemann"|"troe", "log_k_inf_300K": ...,
            "log_Pr_300K_1bar": ..., "Fcent": ..., "confidence": ...,
            "abstain": False}
```

Lindemann submissions must set `Fcent` to 1. Troe submissions must set `Fcent` in `[0.05, 1)`.

### `problem` keys

| key | meaning |
|---|---|
| `temperature_bounds_K` | inclusive `[300, 1200]` |
| `pressure_bounds_bar` | inclusive `[1e-3, 1e2]` |
| `measure_budget_calls` | 18 |
| `family_names` | `lindemann`, `troe` |
| `rate_law` | the in-family formula |
| `measurement_model` | `measure` returns `ln k` |
| `abstain_when` | second channel, or k falling with P |

The evaluator uses this reduced broadening law, rather than the full Troe 1983 formula:

```text
Pr = k0(T)*[M]/k_inf(T)
n = 0.75 - 1.27*log10(Fcent)
log10(F) = log10(Fcent)/(1 + (log10(max(Pr,1e-12))/n)^2)
k = k_inf(T)*Pr/(1+Pr)*F
```

The full Troe c and d terms are omitted. Fcent is constant in this model.
Negative-pressure-order worlds are synthetic counterexamples, not a claimed elementary law.
Repeated measurements receive distinct deterministic noise draws indexed by call number;
repeats can therefore be averaged within the budget.
Spending past the budget fails the world closed.

## Relation and distinction

- Not `ChemicalKinetics/ReactionMechanismFitting`: that recovers a **network of first-order edges**, not a pressure-dependent elementary law.
- Not `SystemsBiology/EnzymeKineticsLaw`: Michaelis–Menten saturation in a well-mixed enzyme, not gas-phase falloff.
- Not PR #22 `ChronoamperometryLawID`: electrode transients, not Troe/Lindemann.
- Not `Turbulence/WallClosureDiscovery`: a wall mixing-length formula, not chemical kinetics.

## Scoring

Mechanism, false discovery, refusal and coverage are reported separately. Always-abstain
is exactly zero. The held-out split is evaluator-only. `sle.contract_lint` is importable and free to call for shape checks.
The evaluator independently rejects unknown families and non-boolean abstain flags.
