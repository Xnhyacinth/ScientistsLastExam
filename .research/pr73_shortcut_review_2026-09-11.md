# PR73 NeuralReportAttribution 最新 head 固定捷径复测

审查对象：PR73 `c0d1f3e2419c4dc334587dcf1be4b9777bf632be`。
评测器基线：本轮集成 `bfd62be68723fa50e477eaca789a95989ab878ed`。
本文件只描述这一任务；未合并 PR73，未改 task card，未调用模型或重新搜索阈值。

**结论：issue #78 所指的免费噪声键查表前提已在最新源码移除；合法收费代数捷径仍很强，并且最新披露的 grid winner 已独立复现。**
它当前没有达到 reference 或满分。两个代数候选与 reference 在这 20 个冻结 world 上均正确解决所有离散模型/refusal/null 决策，
余下差距主要是连续参数精度。本轮结果不能替代独立模型难度校准或外部神经科学有效性审查。

## 审查范围与身份

- 使用 `sle.spec.load_task_spec` 加载从 PR73 完整归档的 task package，再由当前 `sle.evaluate.evaluate_candidate`
  调用 trusted driver / CandidateProxy / bubblewrap。没有运行作者的 `scripts/audit_neural_report.py`，
  没有在审查 driver 中直接导入 oracle、reference 或 probe 来求分。
- PR73 还新增 `Neuroscience -> Biology` 的 taxonomy 映射；集成基线尚未有这一条。
  审查 driver 在加载 spec 前只在内存添加这条原 PR 映射，runtime 文件保持基线字节不变。
  Task source 的逐文件 SHA-256 来自原 head 归档，并在实测前后核对。
- Linux 独立 checkout：`/home/azureuser/workspace-gzy/zyf/sle-pr73-audit-20260911`。
  Python 3.8.10、NumPy 1.24.4、SciPy 1.10.1；OMP/OpenBLAS/MKL/NumExpr 均固定 1 线程；每次完整评测 timeout 300 秒。
- baseline、reference、默认 algebraic probe、公开 grid winner，各固定重复两次。
  每次都将独立候选源复制到临时 `solution.py`，由沙箱执行；评测器每个 world 重置 candidate session。
  没有扫新 grid，也没有根据本次 development 或 heldout 结果选择参数。
- 公开结果保存聚合科学指标、原始分子/分母和完整结果 hash。
  含逐实例答案的完整 metrics 仅保留在远端 0700 私有目录 `/home/azureuser/workspace-gzy/zyf/sle-pr73-private-20260911`，
  不纳入 Git。完整重复一致性在私有原始 metrics 上比较，不能仅凭四舍五入后的分数断言。

复测驱动、来源 hash 和派生候选：

- `.research/audit_pr73_shortcuts_2026-09-11.py`
- `.research/pr73_task_sources_2026-09-11.json`
- `.research/pr73_shortcut_candidates_2026-09-11/published_grid_winner.py`
- `.research/pr73_shortcut_review_2026-09-11.json`

## 候选输入边界静态审查

所有行号对应上述 PR73 head 的 `benchmarks/Biology/NeuralReportAttribution/`。

- `verification/reference_fit.py:2-3` 只导入 NumPy、SciPy least_squares；`:8-19` 仅使用公开
  `problem` 和计费 `experiment` 的校准/响应。默认 schedule 为每个 report 2 calibration units + 5 response units，
  两个 report 共 14 units。`:23-46` 的模型是 Task.md 公布的四状态传递方程和噪声模型，未读取 world seed、kind、真参数或文件。
- `verification/algebraic_probe.py:6` 只导入 NumPy；`:11-21` 在两个 report 各用 2 calibration units
  和频率索引 0、3 的各一次响应，共 8 units。它去掉公开校准给出的仪器效应，代数求逆得到 A 的估计；
  4×4 维度及指定耦合位置来自公开任务模型。`:34-44` 以固定阈值决定 null/refusal/model 与估计参数。
  无 oracle import、文件访问、动态加载、seed 查表或潜在标签读取。
- 默认 `infer_circuit` 的配置是 `(.25,.3,.15,1,1)`，位置 `verification/algebraic_probe.py:47`。
  公开 grid winner 使用 `(.13,.35,.08,.9,1)`，来自同 head 的 `references/known_best.md` 第 4 节，
  作者披露这些常数由历史 development grid 选出。派生候选仅替换该函数默认元组，不新增运行时信息来源。
  两个候选分别记录 source hash，不能把默认配置的分数冒称公开 grid winner 的复现结果。

## 与 issue #78 的对应关系

[Issue #78](https://github.com/Geniusyingmanji/ScientistsLastExam/issues/78) 对 PR73 的原始记录是：
把公开的 `measurement_noise_sd` 当作实例查表键，以零测量取得满分。
最新 `verification/evaluator.py:14` 将该量固定为 0.012；`:63-70` 构造的整个 public problem
只含固定模型设置，不再由 seed/kind/采样真参数决定。因此那个“每个实例有不同免费噪声键”的前提已移除。
这一点由最新源码静态核验；本次没有编造或重新发布历史答案 lookup 表。

这不等于已证明没有捷径。当前仍有合法的收费校准后直接代数恢复路线；
需要用下面的最新实测数值评价其强度。公开 deterministic generator 和付费观测 fingerprint 的污染风险
也不能仅靠移除免费噪声键排除。task card 仍明确缺少独立模型校准、外部神经科学审查与 server-held 新实例。

## 固定沙箱结果

8 次完整评测全部完成，无基础设施失败。每种候选的两次**完整 metrics（含私有 per-instance records）完全相等**。
development 与 heldout 各 10 个 world：6 个 supported、2 个 null、2 个 unsupported。

| 固定候选 | Development mechanism | Heldout mechanism | FDR dev / heldout | 正确拒绝 dev / heldout | Units / world | 两次秒数 |
|---|---:|---:|---|---|---:|---|
| baseline | 0.0000000000 | 0.0000000000 | 7/10 / 7/10 | 0/2 / 0/2 | 1 | 9.661 / 9.863 |
| reference | 0.8593921017 | 0.7432827847 | 0/6 / 0/6 | 2/2 / 2/2 | 14 | 66.347 / 67.308 |
| algebraic 默认 | 0.7449182513 | 0.6079550292 | 0/6 / 0/6 | 2/2 / 2/2 | 8 | 9.691 / 9.969 |
| 公开 grid winner | 0.7540713032 | 0.5456852969 | 0/6 / 0/6 | 2/2 / 2/2 | 8 | 8.943 / 7.578 |

所有候选每个 split 均有效 10/10，supported claim coverage 均为 6/6；
baseline 的 null correctness 为 0/2，其余三个候选均为 2/2。
coverage 仅计 supported world 上是否作正面声称，baseline 的 6/6 并不表示其模型正确，须联读 FDR 与 mechanism。
秒数只是同机并存其他审查任务时观察到的整次耗时，不能直接当作严格隔离的性能基准。

mechanism 的未归一化 utility 分子如下，分母均为 10；最终分数是 `max(0,(sum/10 - 0.2)/0.8)`。
FDR 分子/分母已在上表列出；其余原始分母与重复数值均保存在 JSON。

| 候选 | Development utility sum | Heldout utility sum |
|---|---:|---:|
| baseline | 0.0 | 0.0 |
| reference | 8.875136813722504 | 7.9462622774938705 |
| algebraic 默认 | 7.9593460105542375 | 6.863640233574873 |
| 公开 grid winner | 8.032570425841582 | 6.365482374985724 |

默认代数候选达到本次 reference 的 development **86.68%**、heldout **81.79%**；
公开 grid winner 分别为 **87.74%**、**73.42%**，仅用 8/14 的实验单位。
公开 winner 的 0.7540713032 / 0.5456852969 与 PR 当前文档完全一致到其公布的 10 位小数。
当前 reference 与作者的 Python 3.12/NumPy 1.26.4/SciPy 1.13.1 数值有约 1e-4 的 development 差异，
本次固定 Python 3.8/NumPy 1.24.4/SciPy 1.10.1 结果不应覆写成作者旧数值。
默认候选的 heldout 高于历史 development grid winner，不据此修改参数或替换事先指定的策略。

上述有限探针没有推翻当前披露的有限探针成绩，也没有证明排除了更强捷径；尤其不能单凭与一个参考见证尚有差距就认证为 hard。
本轮不自动改变任务准入或 tier。任务仍需按当前 contribution/shortcut contract 明确记录 pending 的独立校准。

## Candidate 与 runtime SHA-256

| Artifact | SHA-256 |
|---|---|
| baseline | `5658d4c2d1abe731ff48b4e0c90565b8165b183b5206cb51813932ba615a66ef` |
| reference | `86ff59c290764f55bd45f20bf35f961da1076cb998abed041d368dc2d32ac51d` |
| algebraic 默认 | `50d90ca08938563f8d10f65ca0af2bd1f77d032761b2d4c9726d2cabb06646ca` |
| 公开 grid winner 派生源 | `958119238cb505301cc704715ed3cfb34ce7a092df124af56dbaaea15193df4f` |
| evaluator.py | `f0d8614a0d94f7350b721f0f3e2fea1d801cd8a9ab3242b9e58e0a69397d4bc9` |
| integration runtime source | `b8cf4421448c2cec02f18d094e37231fb49300fa6bc597d162424bb27620aac6` |
| task package | `f229133ca911451b7698ae491147d530d27737ef1de511c3c1b283176a3862e3` |

复现须在 `bfd62be` 基线 checkout 上提取 PR73 的完整 task package，并复制本次审查 driver、source hashes 与派生候选。
不要直接运行作者包含 oracle import 的 grid driver；固定实验命令为：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
FRONTIER_SCIENCE_TRUSTED_PYTHON=/usr/bin/python3 \
/usr/bin/python3 .research/audit_pr73_shortcuts_2026-09-11.py \
  --private-root /path/outside/checkout/pr73-private
```

审查分支只提交此文档、聚合 JSON、驱动和源 hash/派生候选，不提交 PR73 task package，
也不修改 root 的 integration/CI/validation worktree 或推送 GitHub。
