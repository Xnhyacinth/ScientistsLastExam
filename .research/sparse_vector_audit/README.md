# SparseVectorAudit construction scripts

The scripts that produced every number in `benchmarks/ComputerScience/SparseVectorAudit/Task.md`,
`TASK_CARD.yaml` and `references/known_best.md`. Run them from the repository root with the
project interpreter; they import the task's oracle directly and never touch the sandbox.

| script | what it produces | runtime |
|---|---|---|
| `engine.py` | the exploration engine the worlds were designed on: a standalone exact model of the mechanism, its sampler and the StatDP-style input library | library only |
| `anchors.py` | every world's anchor on the evaluator's exact engine: an exact-objective local search for noise-scale worlds, the straddling witness for branch worlds, the coupling bound for compliant-branch worlds; writes `anchors.json`, which is pasted into the evaluator | about 3 min |
| `worlds.py` | the construction statistics of every graded world: scales, branch offsets and positions, the compliant worlds' search maximum, the coupling bound on delta, each anchor's loss and event mass, and the runs per side a Clopper-Pearson certificate of the anchor needs | about 3 min |
| `tight.py` | the compliant worlds' strongest witnesses with the mass of their events | about 1 min |
| `run_both.py` | reference, baseline and blanket-refusal metrics with one row per world | about 2 s |
| `trace.py` | the reference's library stage on the noise-scale worlds: plug-in value, chosen event and its exact loss for the best screened pairs | about 5 s |
| `feasibility.py` | Clopper-Pearson runs per side needed to certify each noise-scale anchor | about 1 s |
| `budget.py` | where the reference's budget goes per world: scan, screen, confirm | about 1 s |
| `variants.py` | the reference variants compared while choosing its confirmation (one or two pairs, screen size, shrinkage, level) | about 10 s |
| `ablation.py` | the difficulty ladder, one reference choice changed at a time, and the headroom (`SVA_ONLY=<rung,...>` restricts) | about 15 s |
| `headroom_positional.py` | the documented headroom: the reference with the branch scan run at every position | module |
| `scan_cost.py` | what the headroom's positional scan spends per world | about 2 s |
| `robust.py` | a candidate re-run with every world's seed shifted, eight shifts by default (`SVA_SHIFTS`), for `reference`, `baseline`, `headroom` or `no_confirm` | about 10 s |
| `probe.py` | the 318-strategy shortcut probe: blind straddle guesses, screen-and-claim over run counts, libraries, event rules and thresholds, with and without the first-query scan, and screen-then-confirm on the baseline pair | about 4 min |
| `checks.py` | Python 3.8 syntax, determinism, blanket refusal in both forms, the specification's library maximum, the compliant-branch coupling bounds and every anchor's loss | about 20 s |
| `debug_branch_c.py` | the per-call trace that found the headroom scan's early false alarm in dev-branch-c | about 1 s |

`probe.py`, `worlds.py` and the reference trace write their output to stdout; the numbers in the
task documents are copied from those outputs.
