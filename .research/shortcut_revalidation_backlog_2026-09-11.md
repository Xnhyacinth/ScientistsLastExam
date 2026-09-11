# #78 剩余八项：最新 head 固定捷径复验准备清单

日期：2026-09-11。范围只含 #11/#20/#26/#27/#30/#71/#72/#74。本轮为静态源码、固定参数和提交历史核对；**沙箱评测 0 次、模型调用 0 次、网格搜索 0 次**，未改任务卡或科学准入。

8 个 `origin/pr-*` 均与本轮 `git ls-remote` 返回的远端 PR head 一致。下表的 #78 数字来自[仍为 open 的问题正文](https://github.com/Geniusyingmanji/ScientistsLastExam/issues/78)，属于历史发现，不代表已在本轮最新 head 重测。作者当前文档的数值也仅作为待核验的 provenance。

| PR / task | 固定 head | #78 历史分数 | 本轮准备结论 |
|---|---|---:|---|
| #11 TransitTimingAttribution | `f56031a1363a` | 0.770037 | 相关固定候选可跑；原“四常数”缺失 |
| #20 ActiveFullWaveformInversion | `33b0ab0c6717` | 0.820084 | 独立重建可跑；原始源码缺失、成本高 |
| #26 UnimolecularFalloffLaw | `76876ebff03a` | 0.921819 | 三测量候选可跑；常量 lnPr 版本缺失 |
| #27 LyapunovDecayCertificate | `609b8ae8d5fb` | 0.491533 | 14 点一参原源码/网格缺失 |
| #30 AffineLoopRankingCertificate | `90366563a760` | 1.000000 | 替代 exact LP helper 可移植；155 行版本缺失 |
| #71 AnomalyZoneSpeciesTree | `7623c22be5bf` | 0.858889 | 公开 shape 前提已改变；当前 mean-distance 变体可移植 |
| #72 DarkMatterRecoilAttribution | `8497bd455d30` | 0.657182 | 57.8 策略与已选四分类 probe 可固定派生 |
| #74 FocalMechanismStressInversion | `8193c5aa6abf` | 0.814230 heldout | 对应 .814230 的源码与完整配置齐全 |

建议顺序：**#74 → #72 → #11 → #26 → #71 → #30 → #20 → #27**。先复验源码与固定参数完整的条目；没有原候选的条目保留“related / reconstruction”标签。#27 与 #30 是 optimization，不能强套 discovery 三轴或编造 heldout。

## 加载合同

这些是 head 自带 metadata 的逻辑 ID；不能从物理文件夹反推 ID。若当前 loader 缺映射，在独立审查进程显式适配，保留 provenance，不改任务卡。

| PR | 逻辑 task ID | entrypoint | 物理目录映射 |
|---|---|---|---|
| #11 | `Exoplanets/TransitTimingAttribution` | `attribute_ttv` | `Exoplanets → Physics` |
| #20 | `WavePropagation/ActiveFullWaveformInversion` | `invert_velocity_model` | `WavePropagation → EarthScience` |
| #26 | `ChemicalKinetics/UnimolecularFalloffLaw` | `identify_falloff` | `ChemicalKinetics → Chemistry` |
| #27 | `ControlTheory/LyapunovDecayCertificate` | `build_lyapunov` | `ControlTheory → Engineering` |
| #30 | `ScientificComputing/AffineLoopRankingCertificate` | `build_ranking` | `ScientificComputing → ComputerScience` |
| #71 | `Phylogenomics/AnomalyZoneSpeciesTree` | `infer_species_tree` | `Phylogenomics → Biology` |
| #72 | `ParticlePhysics/DarkMatterRecoilAttribution` | `infer_recoil` | `ParticlePhysics → Physics` |
| #74 | `Geophysics/FocalMechanismStressInversion` | `infer_stress_orientation` | `Geophysics → EarthScience` |

## 统一执行边界

后续执行用当前集成版本的 `evaluate_candidate` / `load_task_spec`，为 task head 与 runtime revision 分别记账；只抽取任务包，不合入 PR 的旧 runtime。独立 Linux worktree、0700 私有指标目录、固定 Python/NumPy/SciPy、OMP/OPENBLAS 单线程。每个基线/参考/固定候选双跑，保存 source bytes/hash、完整未四舍五入指标、指标 hash、paid query 数和失败分类。发现类保留 dev/heldout 三轴、coverage 及各分母；optimization 保留每 instance 证书与目标值。

不要直接运行作者混合 oracle 导入、缓存评分或全网格搜索的 driver。候选必要 helpers 应逐字内联并保存来源 hash；只允许事先已披露的参数。所有 heldout 结果只作诊断，不参与选参。相关配置复验不能代替未找回的原始 #78 候选。

## #11 TransitTimingAttribution

Head：`f56031a1363aaee41e5883617758a7daea9a85d4`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `d4878b4eda61`：连续周期拟合、precision/refusal 门、private noise 与无序不等长 splits；更新 reference 与 probe。其后 evaluator e6152df/02af779/e7a4c1d 是空行/空格整理，无新科学机制。
- `f56031a1363a`：最新 head 仅 README 计数。任务证据说明最后在 1dd91e9 澄清 cached grid 与真实 sandbox replay 的区别。

**候选与参数**

逐字复制 reference_solver.py 后追加 replay_probes.py 的 FIXED_SCHEDULE 字符串；不要运行作者 main。

`{"transits":[13,26,43,59],"relative_rms_max":1.2,"bic_gap_min":3.0,"correlation_max":0.8}`

候选只用 observation、measure 返回与 reference 的公开输入拟合 helpers。

作者文档当前记录（待复验）：`{"development":0.574956,"heldout":0.301806}`。

**缺口与下一步**

- #78 所说“同一算法重调四个常数”的四值/原始候选在本次限定源码检索中未定位；固定 schedule 候选不能冒称那一条 .770037 攻击。
- 基线、reference、固定 schedule 各双跑；若取回四常数原源码再另加双跑。
- 使用当前受信 evaluate_candidate；作者 replay CLI 读取 stdout 全指标的假设不适用于已加入公开过滤的 wrapper。
- 加载逻辑 Exoplanets/TransitTimingAttribution 时核对 Exoplanets→Physics 映射；记录 paid query、两 split 三轴及分母。

**定位**

- [benchmarks/Physics/TransitTimingAttribution/verification/reference_solver.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/f56031a1363aaee41e5883617758a7daea9a85d4/benchmarks/Physics/TransitTimingAttribution/verification/reference_solver.py)；SHA-256 `32fa62da18d59b3de320a8320866917ebe7738bed5db511df2899ad271198e4d`。
- [benchmarks/Physics/TransitTimingAttribution/verification/replay_probes.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/f56031a1363aaee41e5883617758a7daea9a85d4/benchmarks/Physics/TransitTimingAttribution/verification/replay_probes.py)，行 33-48, 55-66；SHA-256 `6975a84a677a5732b3ee00867ed158a4d594398b7bd69c8f1e65cd339caec88b`。
- [benchmarks/Physics/TransitTimingAttribution/verification/calibrate.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/f56031a1363aaee41e5883617758a7daea9a85d4/benchmarks/Physics/TransitTimingAttribution/verification/calibrate.py)；SHA-256 `998da543e9c550478719dbb04d8324db7cff0603cf1412e994154753ab993010`。
- [benchmarks/Physics/TransitTimingAttribution/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/f56031a1363aaee41e5883617758a7daea9a85d4/benchmarks/Physics/TransitTimingAttribution/verification/evaluator.py)；SHA-256 `dc743e33121f02da9feeddbb6398e6e59adead861af680588cf3dc619d5f04a4`。
- [benchmarks/Physics/TransitTimingAttribution/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/f56031a1363aaee41e5883617758a7daea9a85d4/benchmarks/Physics/TransitTimingAttribution/references/known_best.md)；SHA-256 `3565f5d539e902329d10f29b5c1ca25041ad49732a1c5248bed2000e6ead6721`。

## #20 ActiveFullWaveformInversion

Head：`33b0ab0c6717354e2ecb8fc9657b42fa8facd641`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `97261e36c162`：truth 改为独立 random Fourier 场、300 samples、每 split 10 supported+3 controls；旧 Gaussian 结果不再同一分布。
- `50d6dd27f8df`：reference 固定 source 9/15/21，timeout 提至 1200 秒。
- `16faadd3833b`：near-null correction 从 0.001 改为 0.0000001，联合 waveform noise 下确认 null。
- `33b0ab0c6717`：最新 head 仅任务卡/known_best/冻结 replay JSON 等证据说明，无 evaluator/reference 数值代码变化。

**候选与参数**

逐字复制 .research/pr20_fwi_continuous_probe.py，仅覆盖已披露四个模块常量。

`{"LENSES":5,"STOP_NOISE":5,"DEPTH_CAP":0.7,"THRESHOLD":0.22,"source_policy":"linspace endpoints and middle of public source_indices: 3/15/28"}`

standalone 自写波传播器与有限差分拟合，仅公开几何、声源、noise_std 和 acquire；无 oracle/reference imports。

作者文档当前记录（待复验）：`{"development":0.136683,"heldout":0.059821}`。

**缺口与下一步**

- known_best 与 probe 首行明确 original maintainer grid/source 未提供；这只是同族独立重建，不是 .820084 的精确源码。
- 先 baseline/reference/已公开最强 depth 配置双跑；不运行 threshold sweep，不按 heldout 改阈值。
- 单次 timeout 1200 秒；作者报告 reference 约 607–619 秒，合理安排独立 Linux CPU 时间与线程=1。
- 其余三个已选配置可在独立授权/预算下固定复验；开发集选择与当前生成族都属于 builder evidence。
- 引用最新 oracle/hash，禁止以 September 9 JSON 代替本轮最新分布证据。

**定位**

- [benchmarks/EarthScience/ActiveFullWaveformInversion/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/33b0ab0c6717354e2ecb8fc9657b42fa8facd641/benchmarks/EarthScience/ActiveFullWaveformInversion/verification/evaluator.py)；SHA-256 `91afbdfde27d0d3782740045a0d3b24acd8e5025d6cbdbc8e05409001366859b`。
- [benchmarks/EarthScience/ActiveFullWaveformInversion/verification/reference_solver.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/33b0ab0c6717354e2ecb8fc9657b42fa8facd641/benchmarks/EarthScience/ActiveFullWaveformInversion/verification/reference_solver.py)；SHA-256 `c55d3705682275465c4e62a7d5b8c221f6e92b901b18e63aaeb3d63aecb85c8d`。
- [benchmarks/EarthScience/ActiveFullWaveformInversion/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/33b0ab0c6717354e2ecb8fc9657b42fa8facd641/benchmarks/EarthScience/ActiveFullWaveformInversion/references/known_best.md)，行 86-101；SHA-256 `997eb9886873117cf412d4a86469b00280b8516206aeca514662a0aab8bac712`。
- [.research/pr20_fwi_continuous_probe.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/33b0ab0c6717354e2ecb8fc9657b42fa8facd641/.research/pr20_fwi_continuous_probe.py)，行 1-12,37-112；SHA-256 `2face2f15a7925010a2d6f786719f3d719bac569efc40e442e1db17b7730e6d3`。
- [scripts/audit_fwi_thresholds.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/33b0ab0c6717354e2ecb8fc9657b42fa8facd641/scripts/audit_fwi_thresholds.py)，行 35-38；SHA-256 `3d47399c7d4a527b2f9ce838b0e3952dd5818202db04b7df6f42c7ad4bb58bf5`。

## #26 UnimolecularFalloffLaw

Head：`76876ebff03a37ce1ad2fe76cf3d859c29164bc1`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `325a97c69554`：query noise 按 (world,T,P) keyed；100 bar 的 Pr(300K)=2，使最高压非 k_inf 渐近墙；前一 bb6c950 已改 reference 为完整 pressure-curve fit。
- `76876ebff03a`：head 是 main 合并+inventory；与第一父提交的目标 task 目录 diff 为空。无后续独立 task doc-only 提交；科学证据在 325a97c 的混合代码/文档提交。

**候选与参数**

references/three_assay_probe.py 可直接作为单文件 candidate。

`{"measurements":"最低 temperature; high P, low P, min(10*low P, high P)","negative_high_slack":0.1,"pressure_slope_min":0.42,"f_obs_threshold":0.82,"troe_Fcent":0.4,"confidence_abstain":0.82,"confidence_claim":0.72}`

只 import math、读取 public bounds 和 measure；log_Pr 由观测反推，并非固定常数。

作者文档当前记录（待复验）：`{"development":0.198579,"heldout":0.324198}`。

**缺口与下一步**

- #78 的“3 测量 + 常量 lnPr”与此 probe 观测导出的 log_pr 不同；.921819 所用常量、源码未在限定检索定位。
- 现存 2304 网格的旧记录未在 revised oracle 重跑，不能视为上界已修复。
- 只复验 baseline/reference_falloff/现存 three_assay 各双跑，同时保留 exact issue probe 待取回。
- 禁止用当前 .198579/.324198 的不同候选直接关闭 #78。
- 仅范围 UnimolecularFalloffLaw，不扩展同 PR 的 DiblockMorphologyDiscovery。

**定位**

- [benchmarks/Chemistry/UnimolecularFalloffLaw/references/three_assay_probe.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/76876ebff03a37ce1ad2fe76cf3d859c29164bc1/benchmarks/Chemistry/UnimolecularFalloffLaw/references/three_assay_probe.py)，行 5-20；SHA-256 `8e227cd906c6d46ce0468300c1a79b6d49bad0b1fc646a1b739297c32be0d610`。
- [benchmarks/Chemistry/UnimolecularFalloffLaw/verification/reference_falloff.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/76876ebff03a37ce1ad2fe76cf3d859c29164bc1/benchmarks/Chemistry/UnimolecularFalloffLaw/verification/reference_falloff.py)；SHA-256 `ae6499a370e4252ac704901ac45c22cdd9a80fc8559a81d4817f5b3024ddcd1e`。
- [benchmarks/Chemistry/UnimolecularFalloffLaw/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/76876ebff03a37ce1ad2fe76cf3d859c29164bc1/benchmarks/Chemistry/UnimolecularFalloffLaw/verification/evaluator.py)；SHA-256 `1352cf77f30039aca56e056d9108af0202cffa6fe809d72101b129f7f99308f5`。
- [benchmarks/Chemistry/UnimolecularFalloffLaw/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/76876ebff03a37ce1ad2fe76cf3d859c29164bc1/benchmarks/Chemistry/UnimolecularFalloffLaw/references/known_best.md)；SHA-256 `db6db38847fbba92a47178f6ba3cde3f0344e9e3ec75c0b3cd753bbbafd801ad`。

## #27 LyapunovDecayCertificate

Head：`609b8ae8d5fb06686e921aa927d376c2b769ff5a`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `f746a03c8666`：2×2 改为四组 permutation-switched 3×3；reference 112 Grams；旧 constant 与两参 block-diagonal probe 改成新输入可执行版本。
- `609b8ae8d5fb`：head main 合并+inventory，目标 task 相对第一父无变化；没有后续 task doc-only 科学修复。

**候选与参数**

grid_probe.py 引入 reference_lyapunov 的 _holds/_matrix/_pack/_trace/_upper；独立 candidate 必须逐字内联这些只消费公开矩阵的 helpers，不能保留 verification 路径 import。

`{"b":"Fraction(k,10), k=-12..12","d":"Fraction(k,10), k=2..30","grams":725,"matrix":"[[1,b,0],[b,d,0],[0,0,1]]"}`

helpers 可静态审查为公开 instance 的精确有理 PSD 检查；原驱动直接导入 reference，不可直接跨隔离边界使用。

作者文档当前记录（待复验）：`{"two_parameter":0.206533,"reference":0.36656,"documented_five_parameter_scan":0.4582}`。

**缺口与下一步**

- #78 的“对称一参数、14 点” .491533 精确 ansatz/网格/alpha 规则未定位。
- known_best 还披露 5488 点五参 .458200，但未在任务目录找到其独立完整 candidate/config；也不能用两参 .206533 当全族上界。
- 优先索取/定位已披露 14-point 源码和精确 Fraction 参数，冻结后双跑；本任务不新建/扫描网格。
- 在其缺失时只能先做 baseline/reference/现存两参候选准备，结论限制为该两参族。
- 此为 optimization：按四个 instance 的 feasible/rate/normalization 验收；发现三轴并不适用，不填伪造 dev/heldout 三轴。

**定位**

- [benchmarks/Engineering/LyapunovDecayCertificate/references/grid_probe.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/609b8ae8d5fb06686e921aa927d376c2b769ff5a/benchmarks/Engineering/LyapunovDecayCertificate/references/grid_probe.py)，行 9-36；SHA-256 `5277393de56fd1b6526e9cfd094b289734cd0014e249cec61193c3c5b6aff596`。
- [benchmarks/Engineering/LyapunovDecayCertificate/references/constant_probe.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/609b8ae8d5fb06686e921aa927d376c2b769ff5a/benchmarks/Engineering/LyapunovDecayCertificate/references/constant_probe.py)；SHA-256 `e4dd804cd6d2e3b1d9470525d75fb571afca33f10601aefa4f9a74efa4159968`。
- [benchmarks/Engineering/LyapunovDecayCertificate/verification/reference_lyapunov.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/609b8ae8d5fb06686e921aa927d376c2b769ff5a/benchmarks/Engineering/LyapunovDecayCertificate/verification/reference_lyapunov.py)；SHA-256 `73a0e3e3a41512cf9546519f0343845e0234dfef7278bfda53bca9b4c6dc105d`。
- [benchmarks/Engineering/LyapunovDecayCertificate/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/609b8ae8d5fb06686e921aa927d376c2b769ff5a/benchmarks/Engineering/LyapunovDecayCertificate/verification/evaluator.py)；SHA-256 `318081641d89f35f0508df31bc1ee9c2ffc9077c2f1d4d185010085236b4da58`。
- [benchmarks/Engineering/LyapunovDecayCertificate/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/609b8ae8d5fb06686e921aa927d376c2b769ff5a/benchmarks/Engineering/LyapunovDecayCertificate/references/known_best.md)；SHA-256 `1cfa345dd229c7a04ddc6339d173e38dbb712e231d6e02e64c2fb66f038ec685`。

## #30 AffineLoopRankingCertificate

Head：`90366563a7605e8f6eb6226200b1463615419b4a`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `65c23e5ce2ef`：改为 8/10/12/16 维、2n 个 overcomplete guards、mixed-sign affine loops；消除 inverse-column identity shortcut；完整 exact Farkas LP=1 仍明确披露。
- `90366563a760`：main 合并+inventory；目标 task 相对第一父为空。无独立后续 task doc-only；旧 optimal_delta/known_optima.json 删除保持。

**候选与参数**

tests/affine_ranking_lp.py 的 exact_maximum_delta(guards,A,b) 只读参数，可逐字内联；增加 public-instance Fraction 解析和 JSON rational packing 的 build_ranking adapter。

`{"optimizer":"scipy.optimize.linprog(method=highs), followed by Fraction Gaussian elimination","problem":"由公开 guards/A/b 构建完整 Farkas LP；不读 hidden optimum"}`

helper 不 import evaluator，不含 answer table；使用 NumPy/SciPy，任务 constraints 允许这两库。adapter 应验证 exact equality/caps 与 public signed/overcomplete 格式。

作者文档当前记录（待复验）：`{"full_exact_lp":1.0,"local_reference":0.459105,"inverse_column_probe":0.0}`。

**缺口与下一步**

- #78 155 行纯标准库、1.34 秒实现未定位；当前 scipy + exact reconstruction 是不同实现，不能复用原效率数字或标为原源码。
- 先将 test helper 忠实移植为单文件，不增加 search/随机策略；保存 helpers 原 hash 与 adapter diff。
- baseline/reference_ranking/LP-adapter 双跑，报告每 instance certificate 可行性、delta、score、runtime。
- optimization 没有 discovery 三轴；若 LP 仍到 1，应标候选空间上界问题而不是归咎旧 coordinate-guard 漏洞。

**定位**

- [tests/affine_ranking_lp.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/90366563a7605e8f6eb6226200b1463615419b4a/tests/affine_ranking_lp.py)，行 4-7,25-119；SHA-256 `6d5a9d2b8550cc84f93aae27935ca02abe2d3c8a1d2175fb75f8ccfbfa4f9207`。
- [benchmarks/ComputerScience/AffineLoopRankingCertificate/references/inverse_column_probe.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/90366563a7605e8f6eb6226200b1463615419b4a/benchmarks/ComputerScience/AffineLoopRankingCertificate/references/inverse_column_probe.py)；SHA-256 `448549d3167fd63c93af142b6ed1ae10a493611a9362381b311224f6bb5bec26`。
- [benchmarks/ComputerScience/AffineLoopRankingCertificate/verification/reference_ranking.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/90366563a7605e8f6eb6226200b1463615419b4a/benchmarks/ComputerScience/AffineLoopRankingCertificate/verification/reference_ranking.py)；SHA-256 `6f92e7ce8680baebf063924022b6664094f29c1e9e0fc0506321b6e32c42f01e`。
- [benchmarks/ComputerScience/AffineLoopRankingCertificate/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/90366563a7605e8f6eb6226200b1463615419b4a/benchmarks/ComputerScience/AffineLoopRankingCertificate/verification/evaluator.py)；SHA-256 `3ebca671fd9c769630564f5d6f0a5f1cb2cabc8184abd7f0fa4fa2066f17c4a3`。
- [benchmarks/ComputerScience/AffineLoopRankingCertificate/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/90366563a7605e8f6eb6226200b1463615419b4a/benchmarks/ComputerScience/AffineLoopRankingCertificate/references/known_best.md)；SHA-256 `4054c6d5eed7f7e870fa4a62cf98ca9f9d4f60b08ebe48573e08fd23c44133a7`。

## #71 AnomalyZoneSpeciesTree

Head：`7623c22be5bf464099bc18d81df1534fcf0feb68`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `7f45aa22dd38`：隐藏并跨 worlds 分散 gamma shape；reference 从60 loci估计 shape；改 oracle/reference/probe/ablation。旧公开 shape 前提已改变，不能直接把 .858889 带到此 head。
- `7623c22be5bf`：最新 head 仅 README inventory；任务最近更新仍 7f45aa2 的代码/文档混合提交。

**候选与参数**

使用当前 reference + ablation.py MEAN_PATCH 和 _mean_index；将 _MEAN_D 与参考 helpers 内联，删除 evaluator/msc/world tracking 和任何 _CURRENT shape 注入。

`{"CHOSEN_CLASS":"slow","CHOSEN_SITES":800,"SHAPE_LOCI":60,"REFUSAL_STATISTIC":260.0,"topology":"one neighbour joining on mean gamma-corrected distances","shape":"estimated from public bought sequences, not world truth"}`

MEAN_PATCH 本身可完全由已付费 alignment 与 standalone reference helpers 实现；作者完整 ablation.py 混合 oracle-shape 变体并 monkey-patch ev._world，禁止直接当候选或科学复验 driver。

作者文档当前记录（待复验）：`{"development":0.8,"heldout":0.664,"reference_development":0.912,"reference_heldout":0.903}`。

**缺口与下一步**

- .858889 原始候选没有独立单文件；旧 published-shape 攻击在新 API 上不能静默改用真实 shape。
- known_best 的 .780 guessed-shape 两-cell winner 披露 shape=.5、topology slow300/500 loci、refusal slow800/250 loci，但具体 refusal threshold 未完整列出；不能从全网格重选补足。
- 优先固定 current mean-distance ablation 与 baseline/reference 双跑，标作 related current candidate，不能称旧源码精确复验。
- 不执行102060策略 probe.py；若复验 .780 winner，先找回已保存 winner 的完整 config。
- 逻辑 Phylogenomics/AnomalyZoneSpeciesTree，核对 Phylogenomics→Biology 映射；检查 source 中 reference 辅助函数为公开数学/树处理，不向 candidate 挂载 verification/msc。

**定位**

- [benchmarks/Biology/AnomalyZoneSpeciesTree/verification/reference_quartet_consensus.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/7623c22be5bf464099bc18d81df1534fcf0feb68/benchmarks/Biology/AnomalyZoneSpeciesTree/verification/reference_quartet_consensus.py)；SHA-256 `b95ea8b852d9c6305398c31f01a740e5c34a546b33a89d4a85354eabe107f0cc`。
- [benchmarks/Biology/AnomalyZoneSpeciesTree/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/7623c22be5bf464099bc18d81df1534fcf0feb68/benchmarks/Biology/AnomalyZoneSpeciesTree/verification/evaluator.py)；SHA-256 `32c68e6bdbb99e40af077a309298f3e9dfb756daef004c225b40f13407c45599`。
- [benchmarks/Biology/AnomalyZoneSpeciesTree/verification/msc.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/7623c22be5bf464099bc18d81df1534fcf0feb68/benchmarks/Biology/AnomalyZoneSpeciesTree/verification/msc.py)；SHA-256 `2121fd013e2a2eb513f0dedcddd1d278b437283d04133026e38a64a7ad5c7fd5`。
- [benchmarks/Biology/AnomalyZoneSpeciesTree/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/7623c22be5bf464099bc18d81df1534fcf0feb68/benchmarks/Biology/AnomalyZoneSpeciesTree/references/known_best.md)；SHA-256 `4b4eb0684c97c7a1fc59f21ce5e4264dbebffa73070675c747376573dec70ee3`。
- [.research/anomaly_zone_species_tree/ablation.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/7623c22be5bf464099bc18d81df1534fcf0feb68/.research/anomaly_zone_species_tree/ablation.py)，行 75-93；SHA-256 `e345b098ef69cfdd25d4d56e56b6f895ae562b93c348fea7157f50fcd4a2626b`。
- [.research/anomaly_zone_species_tree/probe.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/7623c22be5bf464099bc18d81df1534fcf0feb68/.research/anomaly_zone_species_tree/probe.py)；SHA-256 `edd5602ab455d69a38b1ebed6f659e42f89a9e24d7f0bb6f5561c04302c05c2c`。

## #72 DarkMatterRecoilAttribution

Head：`8497bd455d3090087e6a15e99fb85f5fae75e5cd`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `fcddf93266c6`：20 signal+4 null+4 outside per split，mass 按两 law 配对log strata；unsupported 每target与支持族 exact twin而联合mass不一致；改归一化。reference 数值算法不变。
- `8497bd455d30`：最新 head 仅 Linux suite logs/JSON/README；f7785a6 的 evaluator diff 也仅修正 docstring。不能把测试记录称新的科学修复。

**候选与参数**

A:复制 reference_profile.py，只把最终正信号返回的 mass_gev 从 best[2] 改 57.8，保持 none/abstain/law 决策。B:逐字提取 audit_dark_matter_recoil.py peak_features+probe_answer，添加固定 config 的候选 entrypoint；不运行 driver 搜索。

`{"A_fixed_mass_gev":57.8,"B_config":[1,1,60,2,95.83680934806682,1,0.5],"B_order":["target","units","excess_threshold","hardness_ratio","mass_gev","peak_kind","peak_threshold"]}`

A 保留 public campaign reference；B 只用 one Ge target paid counts/background。constant_mass_bound uses truth，是 author oracle-assisted bound，绝不当合法 candidate。

作者文档当前记录（待复验）：`{"reference_development":0.548485,"reference_heldout":0.499983,"selected_four_way_development":0.24953505103907683,"selected_four_way_heldout":0.13067021899641232}`。

**缺口与下一步**

- 原始 reviewer 单文件未附；57.8 精确常数与“reference 决策”语义已完整披露，可以构造明确标注的忠实派生源码，不宣称 bit-for-bit original。
- baseline/reference/A57.8/Bselected 各双跑，总8；固定任何常数之前冻结源码/hash，不运行233280 grid。
- 新 mass distribution 与 outside controls 已变，当前 score 应独立测量；不凭历史 .657182 直接判 head 失败。
- 锁 Python/NumPy/SciPy。作者记录 NumPy1.24.4/SciPy1.10.1 reference约 .548432/.499973，与1.26/1.13略有差异；只要求同环境重复一致。

**定位**

- [benchmarks/Physics/DarkMatterRecoilAttribution/verification/reference_profile.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8497bd455d3090087e6a15e99fb85f5fae75e5cd/benchmarks/Physics/DarkMatterRecoilAttribution/verification/reference_profile.py)，行 55-73；SHA-256 `78da166c44b216e3f69a492ba1a4aa605af0cc21d3223f2168196a9d68325d2c`。
- [benchmarks/Physics/DarkMatterRecoilAttribution/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8497bd455d3090087e6a15e99fb85f5fae75e5cd/benchmarks/Physics/DarkMatterRecoilAttribution/verification/evaluator.py)；SHA-256 `8c255e27b25f458f7964ac689eea9140a85d003790149072c02d394438ded72a`。
- [benchmarks/Physics/DarkMatterRecoilAttribution/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8497bd455d3090087e6a15e99fb85f5fae75e5cd/benchmarks/Physics/DarkMatterRecoilAttribution/references/known_best.md)；SHA-256 `05e5f7b3c07c621e1fd1dc3bf52a4f5364513a836a9b2e1caf994c446d1ed8ca`。
- [scripts/audit_dark_matter_recoil.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8497bd455d3090087e6a15e99fb85f5fae75e5cd/scripts/audit_dark_matter_recoil.py)，行 34-57；SHA-256 `3cef9a3aad3327181e49ed9df96b1e36b828033b4f7cb2053f82b520a4cb4993`。
- [experiments/dark_matter_recoil_revision_2026-09-10.json](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8497bd455d3090087e6a15e99fb85f5fae75e5cd/experiments/dark_matter_recoil_revision_2026-09-10.json)，行 3864-3876；SHA-256 `2a983d49362b95917ad56c570a6792407eadd7533a25ef3952b67c9c45dbcb59`。

## #74 FocalMechanismStressInversion

Head：`8193c5aa6abff91ff8cbbce9f617518ff3bb9b61`。本轮状态：**未运行独立沙箱复验**。

**科学变更与后续文档**

- `6d3605559b4c`：修负-z/SDR clipping 几何；强化双平面 moment/projection/refinement reference；level3 96 events、coarse/fine noise 10/3、shear floor .04。
- `8193c5aa6abf`：最新 head 为 docs/diagnostics/source-freeze evidence，明确 paired dense grid 仍接近/超过 reference、准入未解决；无新 oracle/reference/probe 数值修改。

**候选与参数**

逐字复制 .research/pr74_grid_probe.py，模块常量覆盖为已披露 paired62208_refined 配置；保持其默认25°拒绝门，不照 diagnostic driver 临时改成 infinity。

`{"GRID_SHAPE":[24,12,24,9],"PAIRED":true,"QUERY_POLICY":"ambiguous","SIGNED":true,"LOCAL_ROUNDS":3,"THRESHOLD_DEG":25.0}`

只有 itertools/NumPy；candidate使用公开problem、两个nodal planes及paid reanalyze；无 evaluator/reference imports。

作者文档当前记录（待复验）：`{"development":0.775136,"heldout":0.81423,"confirmation":0.758167,"reference_development":0.783503,"reference_heldout":0.796709}`。

**缺口与下一步**

- 更早 maintainer 原始四参源码仍不可得；但 issue78 的 .814230 与当前已披露 paired62208_refined 行完全对应，可复验该已保存实现，明确其是作者独立同族probe。
- baseline/reference/paired62208_refined 各双跑，总6，当前 trusted harness 私有记录全部metrics；固定源/hash和25° gate，不跑threshold sweep。
- 逻辑 Geophysics→EarthScience 映射只在 loader适配；300秒 timeout、NumPy/SciPy固定。
- 不要把旧 geometry 修复当 shortcut gap 修复；文档已经明确 unresolved，本轮仍需 current integrated runtime 独立重复验证。

**定位**

- [.research/pr74_grid_probe.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8193c5aa6abff91ff8cbbce9f617518ff3bb9b61/.research/pr74_grid_probe.py)，行 11-16,80-158；SHA-256 `44d5e5395802141d762c8150e26b5e0a5ea6159f8f794807a03d652305621ddc`。
- [.research/pr74_diagnostics.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8193c5aa6abff91ff8cbbce9f617518ff3bb9b61/.research/pr74_diagnostics.py)，行 91-104；SHA-256 `d1ad09e6b71723849caac00051aa0a3d57c64f16c760e6ababc7a912a84b3ba6`。
- [benchmarks/EarthScience/FocalMechanismStressInversion/verification/reference_solver.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8193c5aa6abff91ff8cbbce9f617518ff3bb9b61/benchmarks/EarthScience/FocalMechanismStressInversion/verification/reference_solver.py)；SHA-256 `3d2f071b414fe5a8e41e11d3140d10f72a76d9456236c2e2742934732b7f80e5`。
- [benchmarks/EarthScience/FocalMechanismStressInversion/verification/evaluator.py](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8193c5aa6abff91ff8cbbce9f617518ff3bb9b61/benchmarks/EarthScience/FocalMechanismStressInversion/verification/evaluator.py)；SHA-256 `91e21fa11db09b7203fc4a6753a920570612564fc5b3eed76d5359fb72640404`。
- [benchmarks/EarthScience/FocalMechanismStressInversion/references/known_best.md](https://github.com/Geniusyingmanji/ScientistsLastExam/blob/8193c5aa6abff91ff8cbbce9f617518ff3bb9b61/benchmarks/EarthScience/FocalMechanismStressInversion/references/known_best.md)，行 57-101；SHA-256 `8512eaabc70fc79152cc50846b656227a3bff400b8c2529b2840ce294feaeff1`。

## 验收限制

此清单只表明当前可定位到什么、忠实复验还需要什么，不证明任何任务已经被修复或仍失败。对 #74 已披露的 unresolved gap、#30 已披露的 LP ceiling 如实保留；对已修改 oracle 或 API 的 #11/#20/#26/#27/#71/#72，不从旧分数外推当前失败。原始候选不可得时，先补来源或明确只做同族固定候选复验。完整来源哈希、逐条配置与公共执行合同见同名 JSON。
