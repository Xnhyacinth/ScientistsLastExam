# Compliance and numerical-oracle audit

The curator's specification matches [Lyu, Su and Li, Algorithm 1 and Theorem 1](https://www.vldb.org/pvldb/vol10/p637-lyu.pdf): threshold noise scale 2/epsilon, query noise scale 4c/epsilon, one threshold draw, and at most c positive outputs. Their paper uses continuous Laplace noise. The integer adaptation below is an additional derivation for this task, not a claim that the paper stated a discrete theorem. [Ding et al.](https://arxiv.org/abs/1805.10277) supports the statistical counterexample-search setting; it does not establish this task's individual compliance labels.

For integer noise with mass proportional to exp(-abs(z)/b), translating by an integer d changes each mass by a factor at most exp(abs(d)/b). Summing this pointwise inequality gives the same bound for tail probabilities. For any neighboring query vectors, shift the threshold-noise summation index by one. The negative-output factors only increase under the corresponding query shift; each positive-output factor costs at most exp(2/b_query). There are at most c such factors, while the threshold mass costs at most exp(1/b_threshold). Thus every output-string probability ratio is bounded by exp(1/(2/epsilon) + 2c/(4c/epsilon)) = exp(epsilon). Summing over any event preserves the inequality. This applies to the unbounded discrete-noise specification with nonmonotone sensitivity-one adjacency.

For a branch deployment M' and the compliant specification M, couple all noise draws. They agree until the first forced comparison would disagree with the compliant comparison. For fixed query vectors, branch eligibility and its first eligible position are deterministic. A union bound over eligible positions gives disagreement probability at most eta. In the special case of an upward branch and cutoff one, only the first eligible position matters: if reached, both output T and halt or they first disagree there. This justifies using one comparison rather than multiplying by the number of branch positions in that special case. Downward branches use the full union bound.

If total variation between M'(q) and M(q) is at most eta uniformly over every q, then for every neighboring q,q' and event S,

```
P[M'(q) in S] <= P[M(q) in S] + eta
               <= exp(epsilon) P[M(q') in S] + eta
               <= exp(epsilon) P[M'(q') in S] + eta*(1+exp(epsilon)).
```

The maximum dissent probability of a forced comparison occurs at the branch boundary. `verification/reference_compliance.py` independently evaluates its infinite-support geometric tails and adds the analytic omitted threshold-noise tail. Tests supply each compliant-branch parameterization to this helper and verify that the resulting delta bound stays below the claimed 0.001. This is a uniform argument over inputs; a sampled search maximum below epsilon alone would not prove compliance. The supplied numerical check also includes an explicit 1e-12 rounding slack; it is not a machine-verified interval proof.

The sampler uses unbounded differences of geometric draws. The oracle's probability enumeration instead normalizes each noise on [-1200,1200]. Consequently “exact” in the original contribution means deterministic model enumeration, not exact real arithmetic. For discrete Laplace scale b, the removed mass is

```
2 * exp(-(K+1)/b) / (1 + exp(-1/b)), K=1200.
```

Conditioning each of the independent noises within that range gives a total-variation discrepancy at most the threshold tail plus k query tails. All current worlds satisfy a bound below 1e-40. This bound excludes floating-point arithmetic error. Regression controls independently compare analytic geometric tails and enumerate the complete output distribution; ordinary floating-point arithmetic is retained. No sampling seed, world, anchor, or normalization is changed by this audit, and it does not claim a formal numerical certificate at a threshold separated only by machine precision.
