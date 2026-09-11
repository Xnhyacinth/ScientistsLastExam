# H tool-interface pilot — 2026-09-11

This is a bounded real-provider integration check, not frozen scientific evidence, a complete task calibration, or the formal J experiment. The two cells below were fixed before either model call. No extra seeds, budgets, resume, or replacement samples were run. Both CLI plans use the `calibration` kind, while their interpretation remains this tool pilot.

## Fixed execution

- Source: `bfd62be68723fa50e477eaca789a95989ab878ed`; the isolated Linux worktree was clean before and after execution.
- Host environment: Python 3.8.10, NumPy 1.24.4, SciPy 1.10.1. No system packages were modified.
- Model: `gpt-5.6-sol`; algorithm `greedy_rewrite`; feedback `selection_blind`; proposal budget `1`; seed `0` for each task.
- Provider output cap: 4,096 tokens; provider timeout and evaluator timeout: 120 seconds.
- `LLMConfig` has no retry setting. The unchanged transport permits up to three attempts per logical model call; this pilot does not establish a one-network-request guarantee.
- Both plans were saved before execution, content-hashed by the campaign tool, and made read-only. Credentials were read from the existing operator config into a private temporary copy (directory mode 0700, file mode 0600). Credential values and endpoint URLs are excluded from this record.

| Task | Plan content SHA-256 |
| --- | --- |
| `Mathematics/CapSet` | `840614474cda4f0b43f68ded4a0c63765b9f266a19944b8c8bcb6caaaeca8598` |
| `DynamicalSystems/ActiveLawDiscovery` | `6a6702faaec87292663021928a5c654e6952147ace0b09617d4e0341a0ec48c2` |

Shared bindings:

- Runtime: `b8cf4421448c2cec02f18d094e37231fb49300fa6bc597d162424bb27620aac6`
- Orchestration: `3275e97f36efb2403b9cc1cdd6187d3f8618cd399d439351a264995203515602`
- Model condition: `9d0313f3542e2c1f350c641116b409f5b0329e080aebaeedc71782776bf9892a`

| Task | Task package SHA-256 | Task contract SHA-256 |
| --- | --- | --- |
| `Mathematics/CapSet` | `ef821c40acf9c85893beae73ba7a37d3ecffaa59725b97ec83f00f83e86c35a4` | `486bbabc823a2659124585b68c0c65a9f3be492583a55dd1bacc50362c7b3ca6` |
| `DynamicalSystems/ActiveLawDiscovery` | `0d870d27c0db1ec5f109c4c76f5ca2e33b3031ec235c5a487a1f79a895999b23` | `54a9dedc4794faf456556c46eae716cf8189a7eb0d6937ec14f5a8ad40814f49` |

## Observed result

| Task | Execute / replay | Proposals valid / accepted | Baseline → incumbent | Input / output tokens | Ledger requests / receipts / attempts |
| --- | --- | --- | --- | --- | --- |
| `Mathematics/CapSet` | complete / complete; both exit 0 | 1 / 1 | 0.000000 → 0.656517 | 956 / 2590 | 2 / 2 / 2 |
| `DynamicalSystems/ActiveLawDiscovery` | complete / complete; both exit 0 | 1 / 1 | 0.000000 → 0.684935 | 1129 / 4008 | 2 / 2 / 2 |

The fixed denominator was 2 cells and all 2 completed. Each run contains exactly two trajectory events: baseline and one proposal. All four event-to-receipt bindings were checked against task/package/runtime, candidate hash, step, and metrics. There were no open evaluation requests, incomplete evaluation attempts, or infrastructure-failure attempts.

Provider-reported totals were **2,085 input + 6,598 output = 8,683 tokens** across two logical calls. No pricing was configured, so dollar cost is unavailable (`null`), not zero.

For each task, `calibrate_task.py --execute --reports ...` and then a separate `--replay --reports ...` generated admission, discovery-triple, and discovery-admission JSON successfully. The real manifests have no top-level proposal budget; `report_cross_model.py` recovered budget 1 from each `summary.json`, retained both runs, and reproduced the same token totals. Only one model was used, so the cross-model report contains no pairwise comparison.

The admission verdict remained `unknown` for both tasks. ActiveLawDiscovery joined its discovery axes through `pooled_runs`; neither run establishes open-loop exhaustion, a paired feedback advantage, seed robustness, shortcut resistance, or difficulty. Campaign reports retain `scientific_admission: not_assessed` and `trusted_evidence: false`. The separate shortcut-probe and formal-experiment admission gates remain required.

## Artifacts and reproduction boundary

The isolated remote source worktree is `/home/azureuser/workspace-gzy/zyf/sle-tool-pilot-20260911`. Plans, run manifests, raw trajectories, evaluation ledgers, command logs, execute/replay reports, and `pilot_summary.public.json` are retained under `/tmp/sle-tool-pilot-20260911/{capset,active_law}` and their parent directory. They are operator artifacts outside the repository; no raw run or credential file is committed here.

Public summary file SHA-256: `f7e2d1d466ee06484eec36d6656730e0514d42cf0b23a3b6830889f8f8e4b3f0`. Its artifact hash map binds each plan file, execute/replay result, manifest, trajectory, and summary. The content hash inside each plan differs intentionally from the hash of its formatted JSON file.

The sequence for each already-existing plan was:

```text
calibrate_task.py --plan <cell>/plan.json --output <cell>/execute.json --execute --reports <cell>/execute_reports
calibrate_task.py --plan <cell>/plan.json --output <cell>/replay.json --replay --reports <cell>/replay_reports
```

The second command reads retained files without another model call. Re-execution or additional sampling would be a new experiment and is outside this pilot.

A durable operator copy is retained at `/home/azureuser/workspace-gzy/zyf/sle-operator-evidence/2026-09-11/tool-pilot`, outside the repository with directory mode 0700. All 66 non-credential files were copied byte-for-byte and checked against the originals; the adjacent `tool-pilot-copy-integrity.json` records their hashes. The `private/` configuration directory was excluded. Original plans, paths and hashes were not rewritten; this copy does not change the experiment's bindings or grant current-runtime compatibility.
