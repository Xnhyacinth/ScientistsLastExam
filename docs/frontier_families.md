# Frozen frontier families

## Why this is separate from a release score

A fixed benchmark release must be reproducible and comparable. A scientific frontier must also
be able to accept later problems, regimes, constructions, or discoveries without rewriting the
evidence produced by an earlier release. SLE therefore keeps two quantities separate:

- `combined_score` belongs to one frozen task package and is used for model comparison;
- `lifetime_frontier_credit` belongs to a stable task family and is an append-only record of
  independently verified frontier gains.

An `uncapped` release score may exceed its score-one reference. It does not by itself prove that
the task will remain scientifically productive forever. Lifetime credit can grow across waves,
but must never be used to compare models that were evaluated on different frozen manifests.

## Opt-in metadata

Legacy tasks need no migration. A family-aware package declares both fields in
`frontier_eval/metadata.yaml`:

```yaml
task_family_id: ScientificComputing/AdaptiveConservativePDEMethod
wave_id: wave-1
```

and ships `frontier_eval/wave.yaml`:

```yaml
schema_version: 1
task_family_id: ScientificComputing/AdaptiveConservativePDEMethod
wave_id: wave-1
predecessor_wave_sha256: null
cells:
  - id: smooth-advection-1d
    kind: optimization
    weight: 1.0
    objective: maximize
    reference_value: 0.0
    credit_scale: 1.0
    minimum_delta: 0.01
    semantic_contract:
      canonicalizer_id: conservative-scheme-v1
      canonicalizer_path: frontier_eval/contracts/conservative_scheme_v1.py
      canonicalizer_sha256: <sha256-of-versioned-canonicalizer-artifact>
      evidence_predicate_id: frozen-pde-panel-v1
      evidence_predicate_path: frontier_eval/contracts/pde_predicate_v1.py
      evidence_predicate_sha256: <sha256-of-versioned-verification-artifact>
      evaluation_panel_path: frontier_eval/contracts/pde_panel_v1.json
      evaluation_panel_sha256: <sha256-of-frozen-cell-panel>
```

For a discovery cell use `kind: discovery`, replace the objective fields with a positive
`credit_per_claim`, and add a stable `novelty_namespace`. The semantic contract binds the
versioned canonicalizer, confirmation predicate, and frozen evaluation panel; paths must stay in
the task package and their bytes must match the declared hashes. The loader derives
`definition_sha256` from the
normalized cell semantics.
Authors may include that hash explicitly; a mismatch is rejected. A cell ID cannot later be
reused with different semantics.

The first wave has a null predecessor. A later wave names the semantic manifest SHA-256 of the
previous wave. Every historical wave must remain repository-visible: the repository audit rejects
missing predecessors, multiple genesis waves, forks, repeated wave IDs, and changed cell
definitions. Run manifests and evaluation requests also bind the current family ID, wave ID, wave
manifest hash, task package hash, and runtime source hash.

## Trusted record contract

`FrontierLedger.record()` accepts an `EvaluationLedger` and committed request ID, never raw records
or caller-supplied hashes. It verifies `valid == 1`, extracts `frontier_records` from the durable
receipt, and binds the request, metrics, candidate, package, runtime, and wave hashes into the
event. A candidate program must never choose its own canonical ID, scientific cell, weight,
reference, or minimum delta.

Model runs only produce receipts. A trusted operator promotes a receipt into one explicitly chosen,
cross-run canonical evidence root with `python -m sle frontier-promote --task ... --run-workdir ...
--ledger-root ... --request-id ...`. The command rechecks the current task/runtime hashes and the
run manifest before writing. Passing an individual model run directory as `--ledger-root` would
create an isolated ledger and is not a valid campaign-wide lifetime total.

`python -m sle verify-run --workdir ...` checks internal content consistency under the budget
declared by that run. Release/cohort evidence must additionally pass `--expected-budget N`; the
cohort runner supplies this external campaign contract automatically.

An optimization record contains:

```json
{"cell_id": "smooth-advection-1d", "canonical_id": "sha256-or-canonical-method-id", "value": 1.25}
```

It earns credit only when it improves the recorded incumbent by at least `minimum_delta`:

```text
credit = weight * scientific_improvement / credit_scale
```

A discovery record contains a frozen cell ID and evaluator-derived canonical claim ID. Deduplication
uses `task_family_id + novelty_namespace + canonical_id`, not the cell ID, so overlapping cells
cannot count the same scientific claim twice. The first verified occurrence earns
`weight * credit_per_claim`; repetitions earn zero. Discovery
mechanism recovery, false-discovery rate, calibrated refusal, and attempted-discovery coverage
remain separate release metrics. Lifetime credit must not average or hide any of those axes.

## Integrity properties

The local ledger stores each event as a separately fsynced, atomically published JSON document
under a POSIX advisory lock. Every event binds the previous event hash and is deterministically
replayed before another event is appended. Replay recomputes all deduplication and credit
decisions rather than trusting stored totals; a crash cannot leave a half-written committed event.

The hash chain is tamper-evident, not an external signature. Confirmatory use must publish or
otherwise independently anchor the ledger head hash. A local operator able to rewrite the whole
repository and every external receipt is outside this module's trust boundary.

The following never earns credit:

- an invalid or unverified evaluator result;
- a repeated canonical artifact or discovery;
- an optimization smaller than the frozen minimum scientific delta;
- a candidate-created cell or weight;
- a changed cell definition under an existing cell ID;
- a wave that does not extend the recorded predecessor chain;
- a surrogate-only claim lacking the task's required high-fidelity or fresh confirmation.

The same evaluation request is idempotent. A repeated request returns its original decision; a
different metrics receipt for that request is rejected. Within one wave, the same candidate artifact
must always map to the same canonical record set.

Synthetic deterministic worlds can establish benchmark-frontier credit. They must not be
reported as real-world scientific discovery without the task card's independent confirmation.
