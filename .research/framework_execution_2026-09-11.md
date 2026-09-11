# SLE 框架执行记录 — 2026-09-11

本轮从 main `f9c05b65b100e0b7d6acabbf16e64602fb73eea9` 出发，在独立集成分支实施。
项目的目标是用可执行的科学任务，测量智能体利用实验反馈持续改进的能力：
optimization 关注有效目标改进；discovery 还需要分别检查机制、错误发现与拒答。
任务能运行、模型有一次高分、反馈产生可靠收益，是需要不同证据支持的结论。

当前库存 **85 道：42 optimization、43 discovery**；认证状态为 **5 certified、80 candidate**。
新的认证、可信基线和成熟度审计均覆盖 85 道，补齐旧版 82 道库存的缺口。
成熟度审计中 `internal_science_admission=85` 是该审计的内部工程/证据门，不能理解为难度已成立；
`open_release_ready`、`externally_validated`、`long_horizon_ready` 仍全部为 0。

## 实施结果

| 工作包 | 已完成 | 尚需完成的验收或后续 |
|---|---|---|
| A 候选隔离 | CriticalPhenomena 迁入真实候选沙箱；增加宿主环境、oracle 文件、宿主写入的实际隔离回归 | 随集成 PR 完成最终 CI |
| B 失败协议 | 可信评测坏 JSON、外层超时、进程/sidecar 失败按基础设施故障处理；外部后端持久化故障标记并中止报告发布；修复 OpenEvolve 缺 sidecar 时重标基线 | greedy 已覆盖 pending/receipt 恢复；外部引擎故障后要求新运行目录，尚不承诺原 pending 的精确续跑 |
| C 报告 | 集成 #66；基线参与 incumbent、明确旧 acceptance、保持任务/模型/算法/反馈/seed/预算身份、同 run/split 三轴、计划分母、真实 manifest 的预算与 token 读取 | 新科学结论需新的完整实验矩阵 |
| D 全局证据 | 在 Linux 固定科学依赖下刷新 85 题认证、基线、成熟度和恢复审计，保留所有旧版本 | 最终全量 CI 与发布状态见本次 PR |
| E 公开入口 | 集成 #37/#69 并补修；85 个 wrapper 复用共享入口、公开指标 allowlist、固定错误类别、私有目录/路径检查 | 全库存回放结果见下方验证记录 |
| F 测试覆盖 | 公开 CI 保存 JUnit 并区分执行、失败、跳过；仓库内集成 PR 与 main 同样强制冻结库存；增加便携篡改/缺失/漂移样例；历史原件单独审计，修复 Photovoltaic 无效 git pathspec | 私有历史通道需保留原始 runs，公开 CI 缺少这些数据时仍明确报告跳过 |
| G 贡献门 | 可执行 shortcut 合同、重复评测与声明核对；结构/运行/捷径/难度分列；跳过或缺声明返回 incomplete | 85 个旧任务逐项迁移，不能由迁移清单自动豁免；现有探针覆盖不等于难度证明 |
| H 标定工具 | 新增 `calibrate_task.py` / `run_delta_ladder.py`；固定哈希计划、执行/恢复/回放、完整分母、分离报告；两格真实模型 pilot 完成 | 正式多 seed、多模型和反馈配对实验 |
| I PR 整理 | 35 个未合 PR 的固定 head 队列；#60/#73 固定探针复验；其余 8 项源码/参数准备清单；#17 三项工程修复的独立分支 | 其余优先投稿复验、#17 格式/profile/family 分批验收；未直接合入任务投稿 |
| J 正式实验 | 保留任务、模型、预算和反馈配对所需工具；明确实验前置条件 | 难度证据与任务准入未齐，尚未启动正式多模型/长时测量 |

框架集成保留 #37、#66、#69 的提交祖先；没有整包合入 #17。
所有新证据按实际来源提交记录，未替换旧分析文件、旧 request/receipt 或旧 run 的 hash。

## 验证记录

- 最终运行时源指纹：`8159a99d54894dd304e3ac48956cd05d4389f12a041f5d5d86a2c079641c2c86`。
- 基准环境：Linux，`/usr/bin/python3` 3.8.10，NumPy 1.24.4、SciPy 1.10.1；数值线程固定为 1。
  pytest 8.3.5 安装到隔离临时目录，未更改科学依赖。
- [认证 v85](../experiments/task_certification_audit_2026-09-11_v85.json)：85/85。
- [可信基线 v68](../experiments/secure_baseline_determinism_2026-09-11_v68.json)：85/85 有效且双跑一致，85/85 fail-closed，0 基础设施故障。
- [成熟度 v26](../experiments/task_maturity_audit_2026-09-11_v26.json)：85 题全覆盖；当前或可迁移的模型测量为 0，历史测量未自动升级。
- [恢复审计 v8](../experiments/evaluation_recovery_fault_audit_2026-09-11_v8.json)：8 个场景均通过；这是逻辑请求/receipt 恢复证据，不是所有物理执行仅发生一次的证明。
- [公开 wrapper 回放 v2](../experiments/public_wrapper_baseline_replay_2026-09-11_v2.json)：85/85 实际沙箱回放通过，公开 JSON 与可信基线的公开字段一致。
- [冻结预检 v2](../experiments/measurement_health_preflight_2026-09-11_v2.json)：70 pass、0 fail、0 missing；7 道冻结任务仅获探索性运行许可，未获得正式长时准入。
- `a286124bf7daa77ee0de932b9698286ccde558df` 上核心 Linux 回归 **178 passed**。
- 同一源码历史通道 **67/67 必需测试执行并通过，0 skipped**；原件审计覆盖 **10 任务、30/30 runs**，测试前后字节摘要不变。
  内容完整性本身不证明当前运行时兼容；相关迁移拒绝仍被测试保留。

旧集成点 `c29f7076` 的全量测试与当前源码的追加验证分别记录，不把旧提交的全量结果标成最终 HEAD 的全量结果。
旧集成点全量为 1,349 passed、15 failed、48 skipped（41 分 55 秒）；15 项失败位于冻结 manifest、measurement-health/preflight 和 maturity。
最终追加验证与公开 CI 状态以[集成 PR #81](https://github.com/Geniusyingmanji/ScientistsLastExam/pull/81) 的验证记录为准。
JUnit、必要测试清单、历史原件审计与摘要保存在私有持久目录
`/home/azureuser/workspace-gzy/zyf/sle-operator-evidence/2026-09-11/validation`；复制前后文件摘要核对一致。

## Pilot 与投稿审查的边界

[真实工具 pilot](tool_pilot_2026-09-11.md) 使用 `gpt-5.6-sol`，
CapSet 与 ActiveLawDiscovery 各一个 `selection_blind`、budget=1、seed=0 单元。
2/2 执行和独立回放完成，共 8,683 个 provider-reported tokens；未配置价格，费用是 unavailable，不是 0。
两项 admission 均为 unknown。它绑定 `bfd62be` 的原运行时，后续 OpenEvolve 修复没有给旧 pilot 重新签名。

[PR #73](pr73_shortcut_review_2026-09-11.md) 的 8 次固定沙箱评测复现了公开值；旧免费噪声 key 的前提已不存在。
付费代数策略仍较强，尚不能据此给任务难度准入。
[PR #60](pr60_shortcut_review_2026-09-11.md) 的 6 次固定评测复现了当前披露的 `(2,-3,-4)` 探针；
issue #78 的 0.884294 策略缺少精确源码/阈值，未被本轮证伪或判定已修复。

[PR 队列](pr_intake_queue_2026-09-11.md) 保留各 head 和下一动作。
[剩余 8 项复验清单](shortcut_revalidation_backlog_2026-09-11.md) 核对全部远端 head 和 40 份源码摘要，建议从 #74、#72 开始；本轮清单不包含新评测。
[PR #17 审查](pr17_review_2026-09-11.md) 单列预算恢复、timeout、时钟验证与旧 run 格式的兼容问题；
family/lifetime credit 尚无真实 wave 任务证据，不用于本轮科学结论。
三个工程修复保存在[独立修复分支](https://github.com/Geniusyingmanji/ScientistsLastExam/compare/5bf41028801cb02800ffdcc8f2102c10b8b371d3...codex/pr17-runtime-verifier-fixes)，
129 项 mock/synthetic 回归通过、7 项已有 macOS sandbox 检查跳过；Linux runtime profile 仍需验收。该分支未合入本轮主框架。

下一批按顺序补齐剩余优先投稿的可执行探针、reference 能力与合同声明，完成独立首提案标定后，
才将选定的 optimization/discovery 任务放进冻结的多 seed、normal/selection_blind 预算矩阵。
