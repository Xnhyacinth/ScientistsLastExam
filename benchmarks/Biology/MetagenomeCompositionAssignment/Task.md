# MetagenomeCompositionAssignment — composition under sequencing resolution

Allocate targeted sequencing panels and infer a microbial mixture. Report an
individual taxon only at the resolution of the acquired panels, report unresolved
groups with their total abundance, or refuse composition assignment when the
reference library cannot jointly explain the marker counts.

## Interface

Implement `assign_composition(problem, sequence)`. Calling `sequence(panel_id)`
charges one panel and returns `panel_id`, `read_count`, and `marker_counts`.
Counts follow `marker_ids` order; markers outside that panel have zero counts.
Panel 0 is supplied initially. Two additional panels may be bought, including
repeats of the same panel. An initial panel and each additional panel have 12000
reads. Arguments must be listed integer panel IDs; malformed signatures/types
and over-budget requests permanently invalidate the submission even if caught.
Streams are tied to panel and replicate, so interleaving calls cannot reroll them.
The total candidate wall-clock deadline across all instances is 600 seconds.

| Problem key | Meaning |
| --- | --- |
| `taxon_ids` | Column labels of the reference matrix. |
| `marker_ids` | Row labels and count-vector order. |
| `reference_profiles` | Positive marker-by-taxon probabilities; each column sums to one. |
| `initial_observation` | The already acquired panel-0 observation. |
| `available_panels` | Integer IDs eligible for additional sequencing. |
| `panel_markers` | Mapping from panel ID to its marker labels, including panel 0. |
| `panel_budget` | Maximum additional calls, two. |
| `reads_per_panel` | Number of multinomial reads per observation. |
| `minimum_reported_abundance` | 0.08; reporting cutoff and coefficient in the resolution rule below. |
| `abundance_tolerance` | 0.05 absolute abundance error exhausts abundance-accuracy credit. |
| `resolution_threshold` | 9, for the operational reporting rule below. |
| `observation_model` | `conditional_multinomial`. |

Return exactly these keys, with ordinary Python numbers and Boolean values:

```python
{
    "taxa": [{"taxon": "t4", "abundance": 0.4}],
    "ambiguous_groups": [{"taxa": ["t0", "t1"], "abundance": 0.6}],
    "abstain": False,
}
```

These names are an example, not a supplied alias list. Each group has at least
two unique names. Names must be known, and no name may occur twice or in both a
group and a concrete claim. Abundances must be finite in [0,1]; their total may
not exceed 1 (apart from 1e-6 arithmetic tolerance). A partial assignment may
omit low-confidence components. If `abstain` is true, both claim lists must be
empty. `sle.contract_lint` is available for submission-shape checks.

## Observation model

There are fourteen reference taxa, 60 markers, and ten disjoint panels of six markers.
For a supported mixture with abundance vector `w`, global marker probabilities
are `A @ w`. In panel `P`, reads are multinomial with probabilities
`(A @ w)[P] / sum((A @ w)[P])`. Panel conditioning therefore matters: normalizing
each taxon's panel profile first and then mixing with `w` is generally incorrect.
Abundances here are marker-source mixture proportions, assuming calibrated equal
total marker yield per component; the model does not estimate cell counts or
correct genome sizes and marker copy numbers. Mixtures contain three to four active
taxa with continuous abundances. Every true
component exceeds the reporting cutoff. Marker and taxon labels have no fixed
biological meaning across worlds.

The library contains four pairs that each differ only in a distinct follow-up
panel, one near-alias pair unresolved at the available budget, and four other
taxa. Exactly two of the four query-dependent pairs contribute one active member
each; remaining components are other taxa, including a near-alias member in
alias worlds. Diagnostic changes conserve panel mass. Thus every supported world
has a legal two-call full-resolution design, but choosing panels requires
identifying the active groups from underdetermined initial counts. This is a
synthetic construction prior, not a population model. There is no public alias
table; all groups and diagnostic panels must be inferred from the profiles.
The initial screen has identical conditional profiles for two pairs of these
query-dependent groups. It cannot determine which group in a pair contributes;
follow-up panels also distinguish this community-level ambiguity. Thus selecting
a diagnostic panel requires accounting for uncertainty in the active groups.
In a library-inadequate world, positive shared-marker probabilities deviate jointly
from the reference family. Every noiseless individual panel coordinate is inside
the reference columns' coordinatewise envelope; there is no zero-weight sentinel.
Assess joint compatibility rather than treating a large count alone as a diagnosis.

## Reporting resolution

For reference taxon `i`, let `r[P,i] = A[P,i] / sum(A[P,i])`. Using all acquired
observations, including the initial panel and repeats, define pair separation:

`D(i,j) = minimum_reported_abundance * sum_observations(read_count *
           sum_markers((sqrt(r[P,i]) - sqrt(r[P,j]))**2))`.

Connect two taxa when `D(i,j) < resolution_threshold`; the graph's connected
components are the reporting units. A singleton calls for a concrete taxon;
a larger component calls for one group with its combined abundance. Empty units
should not be reported. This is a conservative operational resolution convention,
not a general theorem about mixture identifiability or a confidence level.

A correctly reported group earns full resolution credit if no pair within it can
cross the separation threshold under any legal two-call plan. Otherwise its
resolution credit is one half: ambiguity caused by skipping an available
informative measurement receives less credit than resolving the component.
Singletons earn full resolution credit. Library inadequacy calls for `abstain`,
not a large ambiguous group.

## Scoring and scope

For a true reporting unit of mass `w`, a correct claim of mass `a` earns
`w * resolution_credit * (0.2 + 0.8 * max(0, 1-abs(a-w)/abundance_tolerance))`.
Missing or incorrectly grouped units earn zero. Sum this over correct units and
multiply by claim precision: correct claims divided by all reported claims.
Thus declaring every possible group or ignoring abundance does not solve the task.
In library-inadequate worlds, only empty-list abstention earns scientific credit;
every composition claim counts as false. Group and concrete claims each count once
in the all-world false-discovery denominator.

There are twelve development and twelve held-out worlds, with three inadequate
libraries in each split. Both splits use `max(0, (mean_scientific-0.25)/0.75)`.
The supplied single-taxon baseline and blanket refusal score zero. Alias-group
recovery and library refusal are reported separately with separate denominators.
Any invalid world zeros both aggregate scores; per-world diagnostics are trusted
reports only. Held-out means excluded from search feedback, not secret data.

## Relationship to other tasks and model sources

This is a reduced marker-mixture model, not an empirical microbiome identification
or clinical claim. Compared with CrowdedSpectrumAssignment and
TransmissionSpectrumSpecies, it uses conditioned count mixtures, charged marker
panels, group abundances and shared-marker library residuals. MetaPhlAn
(doi:10.1038/nmeth.2066) motivates marker-based abundance profiling; StrainEst
(doi:10.1038/s41467-017-02209-5) motivates resolving mixtures of related strains.
GRAMMy (Xia et al. 2011, doi:10.1371/journal.pone.0027992) directly supports
finite read-distribution mixtures and likelihood-based abundance estimation.
Panel conditioning, the query budget and the operational resolution convention
are this task's synthetic extensions; none of these papers validates them.
MethaneSourceAttribution attributes fixed atmospheric source signatures without
charged panel choice or resolution groups. QuinaryConvexHull and
PhaseDiagramDiscovery infer thermodynamic stability or phase structure rather
than conditional count mixtures.


## Reference, ablations and reserved capability

The input-only reference uses sparse conditional-likelihood composition fitting,
adaptive panel selection and a joint library-adequacy check. These are approximate
rather than exact Bayesian inference. Implementation-specific search and numerical
reporting choices are documented in `references/known_best.md`.

| Method | Development | Held-out |
| --- | ---: | ---: |
| Reference | 0.827796 | 0.828552 |
| No adaptive second query | 0.723671 | 0.778845 |
| Model-averaged utility planning | 0.814041 | 0.828552 |
| No adequacy check | 0.494463 | 0.495218 |
| Initial panel only | 0.145944 | 0.340638 |
| Without reporting rounding | 0.827363 | 0.827361 |
| Previous dense-planning method | 0.752475 | 0.761481 |
| Best of 45 fixed plans | 0.687528 | 0.673133 |
| Terra coarse0, independent first proposal | 0.745179 | 0.744529 |
| Terra coarse1, independent first proposal | 0.728136 | 0.744529 |
| Terra coarse2, independent first proposal | 0.747863 | 0.744293 |
| Terra formal `batch_evolve` first proposal | 0.743402 | withheld from search |
| Terra formal task-local-runtime first proposal | 0.750256 | withheld from search |
| Terra final-prompt formal first proposal | 0.734878 | withheld from search |

The earlier expansion without coarse-screen ambiguity was insufficient: one
fresh Terra proposal matched its reference. Those results are retained as
historical evidence. Three first proposals use isolated direct Codex CLI,
gpt-5.6-terra, high reasoning, with the same 600-second evaluation budget.
An additional clean-tree `batch_evolve --run-role calibration` first proposal
used the same model and scored 0.743402; after replacing the proposed shared
wrapper with this task's local wrapper, a clean-tree repeat scored 0.750256.
After PR review reduced implementation-specific reference details in this prompt,
a final clean-tree first proposal scored 0.734878.
Held-out metrics remained outside search feedback. This is not a cross-model
ranking or evidence of long-horizon
resistance. Twenty extra count-noise repeats and all construction comparisons
are recorded in `references/known_best.md`.

Reads, abundance tolerance, score and seeds remain unchanged. A legal two-call
full-credit witness exists; this is an endpoint check, not a measured solver.
Full count-outcome lookahead and calibrated joint uncertainty over supports and
abundances remain proposed capabilities. A simplified optimistic lookahead and
a constrained-prior joint plan were tested and did not improve the reference.
`discovery_coverage` means at least one correct claim in a supported world, not
recovery of every component.
