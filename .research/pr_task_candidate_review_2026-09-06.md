# PR task candidate review

Snapshot: upstream `69738d7`, inspected 2026-09-06. This is a candidate-selection
record, not a new task registration or a hardness certificate.

## Corrected inventory

The upstream taxonomy contains 75 tasks across seven discipline roots. Counting
distinct `(discipline, analogue-or-kind)` pairs gives 31 occupied cells out of 63,
leaving 32 empty. The earlier 29/34 count is obsolete. Open PR proposals are not
merged inventory and must be reported separately.

Upstream now includes `QuantumFoundations/BellBoundCertificate`,
`DiscreteGeometry/SpherePackingCertificate`, `Exoplanets/TransmissionSpectrumSpecies`
and `Turbulence/WallClosureDiscovery`. The certificate-bound analogue exists.
Methane attribution has research files upstream; it is not a registered task.

The inspected open PRs are [#9](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/9),
[#10](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/10),
[#11](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/11),
[#13](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/13) and
[#15](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/15).
File enumeration must paginate: the first 100 files omit many task packages in
#9 and #13. PR titles alone do not establish current task contents or quality.

The five PRs change 41 Task.md files (21 + 1 + 1 + 10 + 8), representing
40 unique paths and 39 unique additions: MetabolicStrainDesign is duplicated
across two PRs, and KissingNumber is an existing task modification.

## Decisions on the proposed next wave

| Proposal | Current overlap | Decision |
| --- | --- | --- |
| Bell rational certificate | Upstream BellBoundCertificate already verifies exact rational SOS identities with candidate-selected words | Review or extend that family; do not register a parallel Bell task merely for a different inequality |
| MIPLIB primal | #9 has PermutationFlowShop and other engineering optimization, but not the same heterogeneous open-MPS object | Priority for instance qualification; no registered package until instances and checker are frozen |
| Hess network | #9 ThermochemicalCycleAudit directly covers reaction-network closure, edge faults, instrument drift and budgeted resolving assays | Review #9 rather than create another Hess task |
| OpenFWI acquisition | #9 ActiveFullWaveformInversion already proposes active seismic inversion | Compare acquisition and identifiability semantics before any successor |
| Biology combinatorial/design | #9 OrthogonalDNACodewords; #13 DiploidHaplotypeAssembly, PhylogeneticParsimonySearch, FedBatchBioprocessDesign, RobustReserveNetworkDesign; MetabolicStrainDesign appears in both | These are proposed cells, not vacant opportunities; prioritize quality and duplicate resolution |
| Chemistry formula/structure | #9 ChronoamperometryLawID and MassFragmentationTree | No empty-cell argument for another generic formula or graph-recovery task |

The physical roots stay Biology, Chemistry, ComputerScience, EarthScience,
Mathematics, Physics and Engineering. New subfields do not require empty roots.

## MIPLIB primal: concrete admission contract

The [official download page](https://miplib.zib.de/download.html) publishes dated
open-instance lists and warns that classifications change. Freeze the actual
selected instance files and reference solutions; do not treat a historical count
of open instances as a permanent property. The
[MIPLIB paper](https://doi.org/10.1007/s12532-020-00194-3) is the benchmark anchor.

- Select 2–4 instances from distinct applications, with redistributable MPS files,
  finite feasible public baselines and strictly better checked reference solutions.
- Submit a complete named assignment. Recompute integrality, variable bounds,
  constraint feasibility and objective using the official primal checker with
  explicitly fixed tolerances. Never interpret primal acceptance as a dual proof.
- Normalize oriented objective improvement using a positive frozen baseline-to-
  reference gap; reject zero-gap anchors. Better-than-reference solutions can
  exceed one. Report feasibility and raw objective separately.
- Search budgets apply to candidate search; oracle work is solution verification.
  Avoid scoring solver wall time. Bound file size and verification work.
- Include a public-incumbent replay control. An open optimality gap may reflect
  inability to prove optimality, not difficulty improving the primal solution.
- Prefer a reusable search policy evaluated across independently sourced instances.
  Row/column permutation or renaming alone does not remove memorized solutions;
  fresh generated instances change the claim from published-record improvement to
  solver generalization and must be reported as a separate evaluation axis.
- Use one focused qualification run for checker parity and a small baseline ladder.
  A full repository suite is unnecessary before a runnable package exists.

No specific instance is admitted by this note. Instance selection, license review,
reference replay and residual primal headroom remain required.

The focused instance review nominates
[`comp12-2idx`](https://miplib.zib.de/instance_details_comp12-2idx.html)
(timetabling, reported incumbent 277) and
[`scpk4`](https://miplib.zib.de/instance_details_scpk4.html)
(set covering, reported incumbent 318) for qualification. Both have integer
objectives and published improvement histories. The numerics-tagged
`minutedispatchstrategy` is deferred. These values are snapshot references and
still need the actual best-solution files replayed before becoming score anchors.

The [2026 competition checker guidance](https://www.mixedinteger.org/2026/competition/#solution-checker)
is preferable to copying historical tolerance claims: it supplies an objective-offset
fix and specifies linear/integer tolerances of `1e-6`/`1e-5`. The checker source
review found that process success alone does not establish acceptance; the wrapper
must verify the integrality, constraint and objective results. Freeze the patched
source and its actual scaled tolerance semantics. For these integer-objective
instances, require at least one full objective unit of improvement over the anchor.

## Hess: review the existing contribution

PR #9 at `3106a1e672a933439aa5953751ab859d0cbef311` describes seven synthetic
isomers, thirteen determinations and six assay units. A replicate costs one;
an independent cross-check costs three. A pendant duplicate/reverse pair supports
an information-dependent refusal case. This already implements the proposed
edge-fault/Hess shape.

Review priorities are whether overlapping cycles actually localize faults,
whether refusal follows the observed information rather than a world label,
whether cross-checks alter the justified verdict, and whether the reference is
materially better than simple residual ranking. Its claim about the nearby
DiscrepantMeasurements task having no budget is inaccurate: upstream describes
charged split tests. Correct that comparison without removing the network-specific
scientific distinction.

[ATcT](https://atct.anl.gov/) motivates network-based thermochemistry, but its
optimized formation enthalpies are not independent raw measurements. A synthetic
network should remain labelled synthetic; public tables alone do not supply a
redistributable raw edge dataset with full uncertainty covariance.
Count independent cycle constraints from the stoichiometric matrix, rather than
counting duplicate or reverse edges as independent cycles. For any claim of unique
fault localization, check that competing faults do not have identical observable
residual signatures under the available assays.

## Additional directions with a defensible distinction

### Active non-Gaussian noise spectroscopy — strongest discovery follow-up

[Sung et al. (2019)](https://arxiv.org/abs/1903.01043) experimentally reconstruct
higher-order noise spectra using controlled qubit measurements. A candidate task
could select pulse filters under a shot budget, identify noise components and
refuse unresolved Gaussian/non-Gaussian alternatives. This probes an open-system
environment, distinct from fitting a closed-system Hamiltonian.

Freeze a pulse grammar and a small independently checked stochastic-process
oracle. Charge shots, use fresh held-out filters, and report component recovery,
false claims, predictive error and unresolved-case refusal. A same-PSD/different-
higher-order pair should defeat PSD-only policies. Scientific relevance is
supported; executable oracle quality and search difficulty remain unmeasured.

### Certified metabolic intervention discovery — conditional successor

[von Kamp and Klamt (2014)](https://doi.org/10.1371/journal.pcbi.1003378) study
enumeration of minimal intervention sets in genome-scale metabolic models.
The useful distinction from the small exhaustive PR #13 MetabolicStrainDesign is
a stream of certified minimal intervention sets on a fixed reconstruction.

Each claim would carry an exact infeasibility certificate for the undesired flux
region, a viable-growth witness, and witnesses establishing inclusion-minimality.
Deduplicate by model, phenotype and canonical intervention set. This avoids
running a full combinatorial search inside the oracle. Model provenance, rational
certificate size and meaningful intervention novelty must be established first;
renaming the existing knockout optimization is insufficient.

### Stabilizer-code certificates — retain gated

The [public qLDPC challenge](https://github.com/unitaryfoundation/qldpc-challenge)
distinguishes cheap structural checks from exact-distance certification. A logical
operator of weight `w` establishes `distance <= w`; it cannot justify rewarding a
claimed lower bound `distance >= w`. A stronger code-design task needs bounded exact
distance verification or a checked lower-bound proof, with fixed qubit count,
rate/check-weight constraints and equivalence-aware deduplication. Keep this under
Physics and do not register until that proof path is available.

### Golden Gate assembly — empirical-data design candidate

[Pryor et al. (2020)](https://pubmed.ncbi.nlm.nih.gov/32877448/) measure ligation
outcomes and demonstrate data-guided assemblies of up to 35 fragments.
[OMEGA](https://github.com/RomeroLab/omega) is a related implementation source.
The candidate artifact would specify target-sequence breakpoints and overhangs;
the oracle checks exact reconstruction, restriction sites and assembly fidelity
under a frozen measured ligation matrix. This differs from #9 DNA codeword-library
packing only if sequence segmentation and enzyme-dependent crosstalk are central.
Freeze raw data permissions and condition-specific matrices, and compare against
the published design algorithm before claiming difficulty. Predicted fidelity is
a data-replay metric, not a new wet-lab result.

### Receiver-function crustal interpretation — lower priority

The [EarthScope EARS archive](https://data.earthscope.org/app/products/portal/ears/)
provides receiver-function and crustal H–kappa products. A prospective task could
select events and identify a justified crustal model or refuse a single-layer
interpretation when phase multiples and azimuthal behavior do not support it.
Published H–kappa estimates are not ground truth. A parameter-only H/kappa fit
belongs to parameter inversion, not automatically to the vacant structure cell.
Layer or interface discovery would need a separate identifiable forward model;
until then this stays below the active-FWI contribution in priority.

## Local PR scope

The existing three runnable frontier prototypes remain candidate submissions:
AdaptiveConservativePDEMethod, OpenVocabularyReactionNetworkDiscovery and
ProcessMicrostructurePropertyDesign. Reconcile their task-level mechanisms against
upstream and open PRs before refreshing evidence or calibration. Preserve the
independent framework branch. The frozen older task branch is not synchronized
with this upstream snapshot and should not be described as merge-ready.

This review adds no task roots, evaluators, dependencies or model calls. It is a
separate local documentation commit based on current upstream. Next implementation
priority is MIPLIB instance qualification, followed by noise-spectroscopy oracle
design; Bell/Hess/FWI receive overlap-aware review of existing work.
