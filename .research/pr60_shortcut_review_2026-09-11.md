# PR60 AquiferPumpingInference 最新 head 固定捷径复测

**结论：当前已披露的 `(2,-3,-4)` 固定策略和 reference 均成功复现，前者仍低于 reference。
这不能证明 issue #78 的更强 0.884294 策略已失效：当前披露没有给出那份完整候选/参数，本次也没有另做 grid 或调参。**

任务 head：`dbc2182268a44b26e383cc950457fd5f7d5aa8d1`。
评测器基线：`68eac7248d30ca9a9f986cdfc4b4c07ee9cddf2e`，其 `sle/` 与本轮先前固定的 `bfd62be` 无差异。
本次只审查 PR60；未合并 PR60，未改 task card，未跑模型或作者的 sweep driver，未推送 GitHub。

## 固定策略与输入边界

下文行号对应当前 PR head 下的 `benchmarks/EarthScience/AquiferPumpingInference/`。

`references/known_best.md:57-63` 明确披露 development-selected 阈值 `(2.0,-3.0,-4.0)`。
因此可复现该策略，无需猜测参数或再搜索。
原 `verification/shortcut_probe.py:11-19` 导入 evaluator 并动态加载 reference；`:87-103` 是 128 点 builder sweep，
**该文件没有被作为候选直接运行**。

本次派生单文件候选采用以下可机械核验的结构：

1. 原 `verification/reference_solver.py` 全部源码作为文件原样前缀。
2. stdlib `SimpleNamespace` 将其中 `_fit`、`_predict`、`_theis` 绑定到 `_REFERENCE`，初始化原 `_FIT_CACHE`。
3. 原 `verification/shortcut_probe.py:23-84` 的 `_candidate` 函数源码原样拼接。
4. 只增加 `_candidate(2.0,-3.0,-4.0)` 与 `infer_aquifer(problem,measure)` 转发入口。

派生候选只导入 math、NumPy、SciPy、types；不含 evaluator、importlib、pathlib、itertools、文件读取或 sweep。
驱动在实测前核验原 helper 前缀、factory 源码和候选 hash，并把三个固定候选的 hash 写入初始计划。
hash 与提取行号均在 `pr60_shortcut_candidates_2026-09-11/source_provenance.json`。

probe 的观察 schedule、sigma、bounds、Q、prediction contexts 和 evidence IDs 均来自公开 problem 或收费 callback。
它只拟合 confined 模型，再按残差统计选择标签；每个 world 的缓存只包含该 world 已付费取得的 drawdown。
评测器按 `verification/evaluator.py:251-260` 在每个 world 重置候选 session。
reference 自身也仅使用公开输入与收费测量，完整四种模型都在 Task.md 公布。

两者均选两个端点 radius、每个 radius 六个 time：12 setup units + 12 measurement units = 24 units。
此捷径减少拟合模型数，**没有节约实验单位**。baseline 为一次观察，按源码费用为 7 units。
这些费用从固定 schedule 与计价合同核对；原 oracle 不导出逐次查询费用，不能声称测到了未返回的 budget trace。

## 沙箱运行与身份

使用当前 `sle.spec.load_task_spec` 和 `sle.evaluate.evaluate_candidate`，经 trusted driver、CandidateProxy、bubblewrap 执行。
从 PR head 归档完整 task package，逐文件 hash 在运行前后均匹配。
PR60 引入的 `Hydrology -> EarthScience` 映射仅在审查 driver 内存添加以加载 spec；没有覆盖 runtime 文件。
尤其没有把 PR 分支中缺少主干 Microbiology 条目的旧 `benchmark_layout.py` 一并复制回来。

- 独立 Linux checkout：`/home/azureuser/workspace-gzy/zyf/sle-pr60-audit-20260911`。
- Python 3.8.10，NumPy 1.24.4，SciPy 1.10.1；OMP/OpenBLAS/MKL/NumExpr 各 1 线程。
- 三个固定候选各重复两次；每次完整评测 timeout 300 秒；未在 development/heldout 上重新选参数。
- 原始 metrics 在私有目录 `/home/azureuser/workspace-gzy/zyf/sle-pr60-private-20260911`（0700）保存。
  该 oracle 只输出聚合指标与计数，不含逐实例答案；Git 中 JSON 因而保留所有原始 metrics。

6 次完整评测均有效，无基础设施失败；每个候选的两次**全部 metrics 完全一致**，不限于显示后的分数。

## 原始数值与三轴分母

每个 split 8 个 world：5 个 supported confined、3 个 unsupported alternative。
下表每格中 `dev / heldout` 保持两者分开。

| 候选 | Development combined | Heldout combined | Mechanism dev / heldout | FDR dev / heldout | 正确拒绝 dev / heldout | Supported coverage dev / heldout |
|---|---:|---:|---|---|---|---|
| baseline | 0.0 | 0.0 | 0/8 / 0/8 | 0/0 / 0/0（按合同定义为0） | 0/3 / 0/3 | 0/5 / 0/5 |
| reference | 0.6220814169260485 | 0.7933520296535728 | 7/8 / 8/8 | 0/7 / 0/8 | 3/3 / 3/3 | 4/5 / 5/5 |
| 披露固定 probe | 0.4818592963355968 | 0.5258162898703973 | 7/8 / 7/8 | 1/8 / 1/8 | 2/3 / 2/3 | 5/5 / 5/5 |

这里的 FDR 分母是所有 `diagnosis != undetermined` 的 named diagnoses，包括 named refusals，
不是仅对 confined 正面声称计数；见 `verification/evaluator.py:175-179`、`:218-239`。
baseline 的零 FDR 只是没有作出诊断，不能解读为科学识别成功。
headline 是 supported quality 均值乘以正确 named-refusal rate，不能把它与 mechanism accuracy 混为一轴。

| 候选 | Parameter recovery dev / heldout（各以5个supported world求均值） | Prediction dev / heldout（同分母） | 两次整次秒数 |
|---|---|---|---|
| baseline | 0 / 0 | 0 / 0 | 6.483 / 6.415 |
| reference | 0.6749840040711405 / 0.8190082736799278 | 0.45560500063661047 / 0.6710588791941635 | 9.080 / 9.256 |
| 披露固定 probe | 0.7992694660684407 / 0.8190082736799278 | 0.4760934016885999 / 0.6710588791941635 | 8.332 / 8.263 |

固定 probe 为本次 reference 的 development **77.46%**、heldout **66.28%**。
两者及 baseline 均与当前 known_best 披露值匹配到其六位小数。
当前 probe 的 supported coverage 高于 development reference，但每个 split 漏掉一个准确 named refusal，
因此 headline 被 2/3 的 refusal 因子压低；不能只展示较高的 parameter recovery 而遗漏这一轴。
墙钟时间是在同机并存其他审查任务时测得，不能作为严格隔离的性能比较。

## 与 issue #78 的比较及剩余缺口

[Issue #78](https://github.com/Geniusyingmanji/ScientistsLastExam/issues/78) 记载另一份“confined 拟合加残差阈值”候选
development 得 0.884294，占当时 reference 的 142.2%。该记录不等同于当前作者 `_candidate(2,-3,-4)`。
当前 head 的 known_best 仍仅披露 0.481859 的这一组参数，没有足以逐字节重建 issue 候选的源码和阈值。

本次可以确认：**作者当前声明的固定 probe 成绩可重现**。
本次不能确认：issue 中的强候选在当前 head 上是否降分、仍超 reference，或换了一份实现。
evaluator 与 shortcut_probe 的最后任务代码修改仍为 `2293a80`（2026-09-09）；
当前 head 的文档/校准提交不能自动视为对 issue #78 的修复证据。
在取得该历史强候选的精确源码/参数并于当前沙箱固定复验前，PR60 的“便宜候选超 reference”问题应保留为**尚未解决的复验缺口**，
不应因为当前较弱固定 probe 的比例低于某个 margin 就关闭它。

另有一项当前静态文档错误：`known_best.md:39-41` 把 reference 描述为 unweighted least squares，
并将 noise-aware weighting 列为未做能力；但 `verification/reference_solver.py:51-52` 已将拟合残差除以 sigma。
因此不能把“补上噪声加权”当作当前尚未实现的难度/改进空间依据。该文档本轮未修改。

## 复现文件与 SHA-256

| Artifact | SHA-256 |
|---|---|
| baseline | `2d244a11042356185603160c55532db42ffe3e6983df46ee88696d5824793e37` |
| reference 原源 / 派生文件 helper 前缀 | `ab2734e7b8048cd03ab6a431b58f8a0872f996cc13f8ed61fe5c1a1b71e77df6` |
| 作者原 shortcut driver | `3a99b21ea5bce2b23f62d652c5de90a3fbd7242a04bec275f72263f5cf86c40f` |
| 原样 factory 源码段 | `29e9b82a93c7889721fea0451022f901f80abe56d9c7b065b09d21d6d8dadd0c` |
| 派生单文件固定 probe | `429cbb85cc16eb05747415c6cb589de8377b5a8a23597ebef8bb2f101c4a5f95` |
| integration runtime source | `b8cf4421448c2cec02f18d094e37231fb49300fa6bc597d162424bb27620aac6` |
| task package | `deb550bf027f1f9635508c5d3e805026ffda766b595360b5e11614fc22cec4ed` |

完整固定计划、逐次 metrics 与 hash 在 `.research/pr60_shortcut_review_2026-09-11.json`；
驱动为 `.research/audit_pr60_shortcuts_2026-09-11.py`，原 task source 清单为 `.research/pr60_task_sources_2026-09-11.json`；
派生 candidate 与保真 provenance 在 `.research/pr60_shortcut_candidates_2026-09-11/`。

复现时在上述 integration 基线 checkout 中提取 PR60 的完整 task package，复制这些审查文件后执行：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
FRONTIER_SCIENCE_TRUSTED_PYTHON=/usr/bin/python3 \
/usr/bin/python3 .research/audit_pr60_shortcuts_2026-09-11.py \
  --private-root /path/outside/checkout/pr60-private
```

审查 commit 只包含报告、aggregate JSON、固定候选、provenance 与 driver，不包含 PR60 task package。
