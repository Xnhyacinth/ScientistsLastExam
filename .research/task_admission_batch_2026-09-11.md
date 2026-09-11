# 2026-09-11 第二批任务准入与修复

本批从 main `3069479717c2d0db0b040babb42390bdcbb60cb1` 出发。#80 的原始 head
`4bb95061846a28a3025f4eb05cdd52210e12b11a` 保留为祖先；其余未通过准入的任务只发布独立修复分支。
合并前仍须完成当前源码的全局冻结证据及 GitHub CI，最终合并记录以集成 PR 为准。
库存为 86 题：42 optimization、44 discovery，5 certified、81 candidate。
新任务的 candidate 准入不是外部认证，也不证明长时反馈收益。

## 本批准入决定

| PR | 固定实测结果与修复 | 决定 |
|---|---|---|
| #80 SparseVectorAudit | 完整 positional reference 0.819398 / 0.729870；7 个固定方法各双跑，18 世界均有效、完整指标确定；每项能力消融降低开发分；151 项 Linux 回归和独立 13-call 贡献门通过；3 个独立有效首提案开发分 0.216592、0.276135、0.265220，均低于完整参考 | 候选准入，完成全局冻结与 CI 后合入；独立隐私领域评审待完成 |
| #72 DarkMatterRecoilAttribution | 补齐参考能力并完成预算、FDR 与隔离验证后，39 项 Linux 回归通过；3 次首提案完整保留：第 0 次 56/56 世界有效且开发 0.585543 高于参考 0.548640；第 1 次仅 49/56 有效、触发预算；第 2 次 0.280270 有效 | D16 失败，保持 open；修复分支 `codex/pr72-admission-fixes` |
| #79 LDMismatchFineMapping | 补齐 masking-aware 标准能力后参考 0.961834 / 0.945518；3 个首提案均 18/18 有效并精确追平参考。另修复 FDR 为 false valid claims / valid claims，旧错误拒答率独立命名；32 项 Linux 回归通过，baseline/reference 各双跑，全部非 FDR 科学字段与历史构造一致 | D16 失败，保持 open；修复分支 `codex/pr79-admission-fixes` |
| #82 CacheReplacementPolicyID | 修复独立世界会话、sticky budget、共享 wrapper 与 claim-denominator FDR；28 项 Linux fixture 回归通过。完整 permutation 参考已提供，但 `expected_score: null`，贡献门明确 incomplete | 完整参考、捷径和首提案标定未完成；修复分支 `codex/pr82-admission-fixes` |
| #47 F6SpinGlassGroundState | 148 项 Linux 回归通过，5 个程序各双跑；参考 0.986111，去 replica exchange 为 0.984568，去 quench 与参考同分 | 捷径分离和有效消融未通过；修复分支 `codex/pr47-admission-fixes` |
| #56 / #57 | Football 的完整参考/首提案证据不足；SortingNetwork 独立构造 0.016667 明显低于查表 0.496667，能力消融未建立 | 保持 open，不以查表成绩证明算法难度 |
| #83 ClockSyncInversion | 修复负物理时延和世界会话；三个冻结计划合计 24 次完整调用，仅 6 次基线有效，18 次运行失败。完整 oracle 测试 900 秒超时且出现失败；新的精确凸包行裁剪仅有 6 项本地轻量回归，尚未完整任务验收 | HOLD；修复分支 `codex/pr83-admission-fixes`，最终 head `e9c4682d8934cc9a5f03cf898e4e60432bf295e6`；失败不能作为低科学分数或难度通过证据 |

三个任务共 9 个预定首提案，全部保留：8 个完整有效、1 个部分无效。
#80 / #72 / #79 的 provider-reported returned-proposal token 分别为 52,280 / 44,696 / 52,200。
这些数不包含不可获得的失败 HTTP 请求用量，价格 unavailable，不能视为零费用。
没有根据 heldout 或失败结果选择候选、重试模型提案、调整阈值或重签旧测量。
#80 的三次首提案用于这次限定的 D16 对照，不是框架注册的正式 model measurement。
全局 maturity 中的 current model measurement 数仍为 0；这次准入不补足多模型、迭代搜索或长时反馈证据。

## 系统修复与证据边界

20 个旧 evaluator 在独立世界入口启动新的候选进程和 tmpfs；同世界的多次 callback、控制器轨迹与远程 callable 状态保留。
修复前 20/20 实际泄漏测试失败，修复后 20/20 通过，另 1 项同世界状态回归通过；共检查 44 个世界边界和 88 次测试 callback。
这组测试验证隔离，不计作科学任务评测。实际修复为 20 个 evaluator 各 3 行，无世界、科学公式或分数更改。

HeatExchanger 和 Truss 的两份既有冻结候选分别在旧 main 与本批源码上双跑，8 次实际 sandbox 评测均有效。
完整指标与逐实例指标在前后四次结果间完全相同，支持这两份固定产物的兼容迁移，不能外推成所有程序等价。
原始产物、旧 metrics、source/runtime/hash 均保留；新兼容记录另存。

#80 首提案原始源为 c02e402。随后只更新 TASK_CARD 和 known_best 的记录，未改变 Task.md、候选可见契约、oracle、参考、世界、预算或分数。
固定计划另将三份原始程序各重评两次，逐键对比原回执；六次结果全部有效且完整指标均与原回执一致；该计划是文档更新后的兼容性检查，模型调用为 0。
公开结果见 `experiments/sparse_vector_first_draw_compatibility_2026-09-11.json`。
完整私有指标和模型响应保存在源树外的 0700 目录；公开证据只含汇总、分母、文件哈希和来源绑定。

审计代码将已移除的 `ast.Str` 检查替换为 `ast.Constant` 字符串检查，保持 Python 3.8 兼容并修复 Python 3.14 审计失败。
新增 docstring 与数字/bytes 常量的区别回归。便携卡片/库存/分类回归 20 passed，另 5 subtests。
CI 固定要求执行 #80 的 18 项检查及旧任务隔离的 20 项检查，缺收集或跳过均不能算通过。

## 合并前全局冻结与验证

新 certification v86 / baseline v70 / maturity v28 已生成：86 道基线各双跑，
86/86 有效且确定，基础设施失败 0；这是基线确定性证据，异常候选调用数为 0，不能冒称异常覆盖。
公共 baseline v70 从保留的私有原件投影，保留评测源 `15fc7050`，另记导出源 `1e290833`；
完整指标、隐藏逐字段差值、原错误消息和原始命令保留在 Git 外部的 0700/0600 文件中。
公共预检只保留允许的指标、汇总判定和哈希；隐藏字段漂移仍参与完整判定，不能因公开过滤变成通过。

wrapper v4 为 86/86，通过的 recovery v10 为 8/8 场景；preflight v3 对 7 道任务各运行 3 次，
得到 70 pass、0 fail、0 missing。spec v14、manifest v11、artifacts v11 保留 7 份候选源码，
仅对有实际兼容报告支撑的 Heat/Truss 变更建立新绑定。
严格冻结库存测试在 `36e6e02c` 上为 15 文件、166 passed、0 failed、0 skipped，不能替代完整 GitHub CI。
详细来源和哈希见 `experiments/global_freeze_validation_2026-09-11_v1.json`。

新私有 raw baseline 和 preflight 的 blob 不在本批分支可达历史中；旧公开 v68 原样保留。
随后修正 rebind 生成器的说明：实际行为变更通过固定产物兼容测量或重新测量迁移时，
不再错误地标成 declarative-only。该修改只改新记录的解释，不改拒绝规则、原有证据或科学测量。
CI 的真实世界依赖已在独立 Linux Python 3.10 环境按 20 个固定版本安装并核对，13 个模块导入及 pip check 通过。

## 保留的队列与后续条件

新的 GitHub 快照记录 34 个 open PR、15 个 draft，原始 head 未按本地修复分支改写。
#74 固定策略分离仍不满足；#73 付费代数策略较强；#60 缺少历史更强策略的精确源码；#30 LP 失败不能被当作数学方案无效。
#17 的运行时修复与 family/lifetime-credit 提案保持独立；本批没有启用其语义。独立修复分支
`codex/pr17-runtime-verifier-fixes` 的最终 head 为 `d97e2a09a7b3460ed52dff05bd2e42b055559cda`。
其中依赖检查改为验证沙箱实际挂载的 distribution metadata，防止宿主的临时 PYTHONPATH 掩盖版本不符；
固定候选的基础 NumPy/SciPy RPC 通过，qutip 配置因真实版本不匹配在启动前拒绝，不能记作 qutip 功能通过。
最终源码 `e2ecdb2fcb4c3dec4ce547a17fb0fd47ea97ae10` 的关键 Linux lane 为 144 passed、0 skipped；
较早的完整组合仍有 3 项环境/profile 失败，未安装缺失依赖，也未宣称完整组合在最终源码全部通过。
保留精确依赖缺口及历史失败，完整 PR 继续 open。
其他未复验投稿保留 `unreviewed` 或既有 blocker，不因旧 CI 绿色而自动合入。


## 原始远端 head 的证据声明快照

逐一读取 34 个 open PR 的精确 head，按相对 main 的变更路径检查任务卡；原始 head 上涉及的任务包均未声明新版可执行 `shortcut_probe` 合同。校验只解析文本/YAML，没有运行投稿代码。部分任务声明历史或可迁移标定，但声明本身不证明当前 source 兼容或首提案低于完整参考；其余仍明确 missing。完整逐项记录见 `pr_declared_evidence_2026-09-11_batch2.json`，其中每张卡有 SHA-256。

这些是远端原始 head 的声明，不能替代本批独立修复与复验后的结果：#80 已补齐合同和有效首提案证据；#72/#79 已补齐部分工程条件但 D16 实测失败；#82 和 #47 分别保留 incomplete 与捷径/消融失败。其他投稿需要继续核验和迁移，不从旧绿色 CI 推断科学准入。
