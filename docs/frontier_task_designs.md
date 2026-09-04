# Frontier task designs and gated research backlog

## Interpretation of an unbounded task

A frozen wave is always finite. Its release score can be uncapped, but its actual search space,
resource envelope and currently reachable records may still be finite. SLE therefore uses
"unbounded" only for a family whose `lifetime_frontier_credit` can grow when later, independently
reviewed waves add genuinely new scientific cells or improve a verified incumbent. It is not a
promise that any model, theorem class or physical system admits infinitely many improvements.
Every successor wave must also pass a non-overlap, scientific-importance and non-degenerate
difficulty review; adding many easy cells is not frontier progress.

The designs below are deliberately not registered tasks. They have valuable scientific geometry,
but do not yet have all of the toolchain, expert review, independent oracle and evidence-receipt
requirements needed by `CONTRIBUTING.md`.

## FormalResearchProofFrontier

### Scientific unit and non-clone boundary

The unit is closure of an externally sourced, open-at-freeze mathematical statement by a proof
accepted by a frozen proof-assistant kernel. This is not another combinatorial construction task:
the candidate artifact is a proof of a fixed research statement, rather than an object checked by
a bespoke finite predicate. It is also not a natural-language theorem-judging task.

Proposed identity:

```yaml
task_family_id: Mathematics/FormalResearchProofFrontier
```

Each discovery cell must bind a source problem UUID, the formal declaration hash, an
`open_at_freeze` receipt and a pre-freeze expert importance review. A model-proposed conjecture
enters a proposal ledger only. It cannot earn credit until independent reviewers establish its
meaning, novelty and non-triviality and a later immutable wave freezes it; otherwise a system can
mint unlimited credit with easy tautologies.
The proposer and solver provenance must be disjoint. A proposal carries no proof witness, an
external curator publishes and timestamps the freeze before any eligible solver run, and only a
proof first generated after that freeze can earn credit.

### Frozen semantic contract

- Lean version, mathlib commit and container image digest;
- exact challenge declaration, definitions and allowed imports;
- checker source and binary hashes, timeout and memory envelope;
- an axiom allowlist and bans on `sorry`, `sorryAx`, new axioms and native/FFI trust escapes;
- isolated `lake build`, `#print axioms` inspection and a second exported-proof kernel replay.

The candidate may edit proof holes only. Statements, definitions, imports and evaluator files are
read-only. The discovery identity is
`sha256(source_problem_uuid || formal_statement_sha256)`, so different proofs of the same theorem
earn research-closure credit once. A separate optimization cell may reward a smaller permitted
axiom footprint or dependency set, but cannot count the theorem as a second discovery. Optimization
must use a deterministic quantity such as normalized proof-term size, dependency-closure size or a
fixed abstract reduction count; wall-clock and CPU time are not stable scientific measures.

Release reporting keeps verified closures, failed cells, axiom footprint, checking cost,
formalization coverage and expert semantic-review status separate. Kernel acceptance establishes
only that a frozen formal statement has a proof under a frozen trusted base. It does not establish
that the statement faithfully formalizes the source problem, that the proof is conceptually novel
or that the model deserves sole research attribution.

### Admission blockers

- no repository-frozen Lean/mathlib/container stack;
- no dual expert review of source-to-formal-statement semantics;
- no externally auditable open-problem selection and freeze receipt;
- no safe contribution-attribution protocol;
- deep conjectures such as Tate are still tracked as hard and not yet included; their prerequisite
  formal library and statement semantics require an explicit readiness review.

Relevant prior work: [Formal Conjectures](https://arxiv.org/abs/2605.13171), the
[Lean proof-validation guidance](https://lean-lang.org/doc/reference/latest/ValidatingProofs/),
[FrontierMath Open Problems](https://epoch.ai/frontiermath/open-problems/about/faq), and the
[Rethlas repository](https://github.com/frenzymath/Rethlas) and
[technical report](https://arxiv.org/abs/2604.03789). Formal Conjectures tracks the difficulty of
formalizing the [Tate conjecture](https://github.com/google-deepmind/formal-conjectures/issues/644)
and the algebraic K-theory prerequisites for
[Birch--Tate](https://github.com/google-deepmind/formal-conjectures/issues/1764).

## PolyesterCircularityCoDesign

### Scientific unit and non-clone boundary

This family is valuable only if it spans molecular identity, polymerization, processing,
microstructure, application properties, depolymerization and life-cycle consequences. A task that
changes only coefficients in a reduced phase-field model is a clone of
`ProcessMicrostructurePropertyDesign`, not a circular-polymer flagship.

Proposed identity:

```yaml
task_family_id: PolymerScience/PolyesterCircularityCoDesign
```

The artifact must include a canonical stochastic polymer representation, repeat-unit and
stereochemical information, copolymer composition, executable monomer-synthesis and
polymerization templates, catalyst and process conditions, target molecular-weight distribution,
processing/morphology plan, application functional unit, depolymerization route, recovered
monomer identity/purity/yield, repolymerization plan and every LCI/TEA input, source, version and
uncertainty required by the wave's frozen system boundary.

### Evidence ladder and namespaces

1. `in_silico_screening` freezes the virtual-synthesis grammar, surrogate versions and their
   applicability domains. It can earn benchmark credit only.
2. `independent_computational_confirmation` freezes DFT/MD/process/LCA protocols and uncertainty
   thresholds. It remains computational evidence, not experimental confirmation.
3. `external_lab_confirmation` follows a wave-specific preregistered power or precision target,
   independent-batch and blinding rules, laboratory-independence requirement and acceptance
   thresholds. It includes structure confirmation, performance, monomer recovery and at least one
   repolymerization cycle. A signed receipt establishes provenance, not experimental adequacy.
4. Application waves for packaging, fibres or elastomers each freeze their own functional unit,
   service constraints and system boundary.

Canonical de-duplication uses separate namespaces:

- chemistry discovery: canonical stochastic-polymer identity;
- process optimization: chemistry identity plus quantized morphology/process recipe and
  application cell;
- recycling confirmation has an explicit claim type. A recyclability claim identifies a polymer
  and normalized recovered-monomer set once across all routes. A genuinely new-route claim also
  binds the canonical reaction, catalyst and process identity.

Repeated assays strengthen evidence but do not create another discovery. Deterministic evaluators
parse frozen, signed experimental receipts and apply preregistered uncertainty rules; they do not
pretend that physical measurements themselves are deterministic.

Synthesis validity, property feasibility, monomer recovery and purity, cycle-to-cycle property
retention, energy/GWP/water/toxicity, uncertainty and refusal remain separate metrics. Pareto
hypervolume is permitted only inside one frozen application cell. Surrogate predictions cannot be
promoted to real-material discovery.

### Admission blockers

- stochastic-polymer canonical identity and manufacturing resolution are not frozen;
- polymer chemistry, process engineering and LCA reviews are missing;
- no independent high-fidelity or experimental receipt workflow exists;
- functional units, inventory data and life-cycle system boundaries are not fixed;
- the current reduced process prototype admits simple corner policies and is not a substitute for
  this multiscale task.

The scientific trade-offs are supported by closed-loop chemical recycling
([Science, DOI 10.1126/science.aar5498](https://doi.org/10.1126/science.aar5498)), recyclable
high-performance polyesters
([Nature Chemistry, DOI 10.1038/s41557-022-01077-x](https://doi.org/10.1038/s41557-022-01077-x)),
virtual forward synthesis and experimental down-selection
([npj Computational Materials, DOI 10.1038/s41524-025-01683-6](https://doi.org/10.1038/s41524-025-01683-6)),
[BigSMILES](https://doi.org/10.1021/acscentsci.9b00476) and its
[canonicalization work](https://doi.org/10.1021/acspolymersau.2c00009). The
[NIST polymer LCA programme](https://www.nist.gov/el/applied-economics-office/lca-polymers-plastics-improve-circularity)
and [ISO 14040](https://www.iso.org/standard/37456.html) are governance references. A wave binds
specific inventory dataset versions and hashes, allocation rules, characterization factors and
the explicit system boundary instead of treating a programme page or standard as data.

## Additional discovery candidates

These remain design backlog and do not change the task inventory.

### 1. ActiveNoiseSpectroscopy

This physics task would actively choose dynamical-decoupling filter functions to discover an
environmental noise spectrum and non-Gaussian polyspectral components. It is not
`HamiltonianLearning`, which recovers a closed-system Hamiltonian. A deterministic prototype must
freeze the pulse grammar and identifiability class and bind counter-based randomness to world,
canonical schedule, global query ordinal and absolute shot index. The evaluator merges nearby
reported components under frozen frequency-resolution, peak-width and cumulant-order rules;
canonical claim IDs bind world lineage to evaluator-owned latent component IDs. It reports
component recall, total false components divided by total
claims, held-out pulse predictive likelihood, attempted-discovery coverage and budget separately.
Useful foundations are [PRL 107, 230501](https://doi.org/10.1103/PhysRevLett.107.230501),
[PRL 116, 150503](https://doi.org/10.1103/PhysRevLett.116.150503) and
[Bayesian QNS](https://doi.org/10.1088/1367-2630/aaf207). Synthetic injected-component recovery is
benchmark evidence, not discovery of a real device environment. Admit only after a
quantum-metrology and identifiability audit.

### 2. AdaptiveTreatmentEffectDiscovery

This biostatistics task would discover heterogeneous subgroups and dynamic treatment regimes under
multiplicity, safety and sequential allocation. It is distinct from graph recovery and evidence
synthesis only if subgroup selection and fresh-cohort confirmation are central. Canonical subgroup
identity binds trial/world lineage, treatment contrast or regimen, stage, endpoint and a membership
bitset hash on a frozen reference population; a tree string alone is insufficient. The fresh
confirmation cohort is evaluator-only and cannot feed selection. Global FDR,
interval coverage, fresh-cohort policy regret, null refusal, sample budget and toxicity budget stay
separate. Prior work includes [causal forests](https://doi.org/10.1080/01621459.2017.1319839),
[SMART designs](https://doi.org/10.1177/1740774514536795), and FDA guidance on
[enrichment](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/enrichment-strategies-clinical-trials-support-approval-human-drugs-biological-products)
and [multiple endpoints](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials).
Any first implementation is synthetic benchmark evidence only, never a clinical efficacy claim.

### 3. StrongLensSubstructureDiscovery

This astronomy task would jointly infer a two-dimensional lens, source, PSF and zero or more dark
substructures with multi-band systematic refusal. Without that joint inverse problem it is too
close to `GravityInversion`. The renderer and `lenstronomy` version must be frozen; catalogues use
permutation-invariant matching, and only evaluator-matched stable projected-perturber IDs enter
discovery records. Do not reward an unidentifiable host-subhalo versus line-of-sight-halo origin
label. Condition recall on a pre-frozen, independently audited injection-recovery sensitivity
region and publish FDR, position/mass error,
calibration and held-out-band prediction. Foundations include
[direct substructure detection](https://doi.org/10.1038/nature10669) and
[lenstronomy](https://doi.org/10.1016/j.dark.2018.11.002). Lens angular complexity
([arXiv:2310.10714](https://arxiv.org/abs/2310.10714)) and source modelling
([arXiv:2502.18571](https://arxiv.org/abs/2502.18571)) can create false positives. Success on a
synthetic renderer means recovery of an injected projected perturber, not discovery of real dark
matter substructure, so this remains a T3 design candidate pending dual-oracle and astrophysics
review.
