# MIPLIBPrimalPolicy — improve a feasible solution, and prove feasibility exactly

## Status and claim boundary

This is an **unregistered candidate task**. It has two qualified instances and
a runnable evaluator, but it has not received external operations-research
review, model calibration, or long-horizon measurement. Official solution
files are fetched into an ignored local directory rather than redistributed,
because their pages do not state a separate license. Its existence here is
not a claim that the task is hard for a particular model.

## Scientific setting

A primal heuristic for a mixed-integer linear program searches for a good
feasible assignment without needing to prove global optimality. This task
freezes two public MIPLIB 2017 minimization instances whose status was `open`
in `open-v29.test`:

| instance | structure | variables | constraints | early baseline | frozen reference |
|---|---|---:|---:|---:|---:|
| `comp12-2idx` | curriculum timetabling | 11,863 integer | 16,803 | 391 | 277 |
| `scpk4` | set covering | 100,000 integer | 2,000 | 327 | 318 |

The early and reference assignments are literal solutions published by
MIPLIB and fetched from hash-bound official URLs, not numbers copied into the
scorer. The evaluator reparses the frozen
MPS files and recomputes every variable bound, row activity, and objective.
All coefficients, bounds, right-hand sides, and variables in this two-instance
subset are integral, so evaluation uses exact integer arithmetic and no
tolerance.

As an independent qualification, all four assignments also passed the
objective-offset-patched MIPLIB native checker at linear tolerance `1e-6` and
integrality tolerance `1e-5`, with zero maximum violations. The native
checker is not the runtime oracle: it requires GMP development files not
provided by this repository, and its process exit status is zero even for a
failed feasibility check. The replay utility therefore parses all three
printed flags rather than trusting the exit status.

## Your task

Implement:

```python
def improve_primal(problem):
    """Return one dense exact-integer assignment in frozen variable order."""
```

The same function is called once for each instance. `problem` contains:

| key | value |
|---|---|
| `name`, `sense` | instance name and `"minimize"` |
| `num_variables`, `num_constraints` | dimensions |
| `variable_names` | variable names in frozen column order |
| `objective` | integer objective vector |
| `lower_bounds`, `upper_bounds` | finite integer bounds |
| `row_senses` | tuple containing `"L"`, `"G"`, or `"E"` per row |
| `rhs` | integer right-hand sides |
| `row_ptr`, `column_indices`, `coefficients` | CSR constraint matrix |
| `incumbent` | the early feasible baseline assignment |

Numeric arrays are NumPy arrays. Return a one-dimensional list, tuple, or
NumPy array of exactly `num_variables` Python/NumPy integers. Floats,
booleans, missing entries, unknown sparse keys, and out-of-range integers are
rejected rather than rounded.

The current best-known reference objective is public in this document, but
the corresponding assignment is oracle-only and is never included in the
candidate RPC payload. This is an interface separation, not a contamination
claim: the instances and MIPLIB solution files are public and may occur in
training data.

## Scoring

For a feasible minimization objective `z`, with early baseline `b` and frozen
reference `r`, the instance score is

```text
max(0, (b - z) / (b - r)).
```

Returning the supplied incumbent scores zero. Matching the 2026-01-26 frozen
MIPLIB reference scores one. A strictly smaller verified objective scores
above one; the formula is not clipped above the reference.

This is **not a mathematically infinite fixed task**. Each frozen MILP has a
finite feasible objective range, so even an unclipped normalization has a
finite instance maximum. Continuing lifetime credit would have to come from
new immutable waves, not from pretending one finite model has unlimited
improvement.

## Tools and scope

- NumPy, SciPy, and the standard library are already available in the normal
  candidate sandbox. No additional solver dependency is introduced here.
- Candidate execution is networkless, single-process, and bounded by the
  framework timeout. Whether an already-available generic solver makes the
  task easy is a calibration question, not something this prototype assumes
  away.
- A direct sandbox probe found that `scipy.optimize.milp` terminates the
  candidate worker under the framework's no-process seccomp policy even on a
  one-variable problem. This is a runtime observation, not a general defense
  against solver reuse.
- Only edit `solution.py`; preserve `improve_primal(problem)`.
- Do not read `verification/` or `frontier_eval/`.

Sources, hashes, attribution, license caveats, anchor histories, and native
checker qualification are recorded under `references/`. Run
`python references/fetch_solution_assets.py` before offline evaluation.

`references/public_coordinate_descent.py` is a reference-free optimization
heuristic over exactly the candidate payload. It preserves feasibility but
scores zero on both early incumbents because neither admits an individually
improving bound move. The score-one `reference_policy.py` only replays the
official published assignments and is not candidate-equivalent or
truth-blind. No positive reusable-policy on-ramp has yet been demonstrated;
that is a registration blocker, not a result to smooth over.

## Nearest repository comparison

The removed `FlowShopMakespan` task introduced in commit `c9bd045` also asked
for a scheduling policy, but it used generated permutation-flow-shop
matrices, checked only a job permutation, and clipped all performance at the
NEH heuristic. It was later removed during difficulty rebalancing. This
candidate instead exposes one generic sparse-MIP policy across timetabling and
set covering, checks the complete assignment exactly on authentic MIPLIB
models, and preserves verified improvements above a frozen reference. That is
a broader oracle and a real public-data frontier, but it also carries a larger
memorization risk and is not promoted until positive policy and HY3 evidence
exist.
