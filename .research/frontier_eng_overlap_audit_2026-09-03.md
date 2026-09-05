# 与 Frontier-Eng 的任务重合核查(2026-09-03)

起因:TASKS.md 里截至 2026-09-03 的原始 15 道工程优化题被归在名为 `frontier_eng` 的 analogue 下,读起来像是从 Frontier-Eng 搬来的。
本文逐题对照,给出结论并改名。

## 对照来源

- Frontier-Eng 论文(NeurIPS 2026 投稿版,本地 `1024_Frontier_Eng_Benchmarking.pdf`)附录 A 的 47 题目录,
  五类:Computing & quantum(10)、Operations research(9)、Robotics/control/energy(8)、Optics & communication(10)、
  Physical sciences & engineering design(10)。
- 仓库 `github.com/Einsia/Frontier-Engineering` 的 `TASK_DETAILS.md`(95 条,含论文之外的 Optics 16 题、
  SingleCellAnalysis、MolecularMechanics、PowerSystems 等)。

上述 95 条是 2026-09-03 历史核查口径，当时未固定仓库 revision，不能作为移动 `main` 的当前计数。
2026-09-04 增量核查固定到 upstream commit `e3fa29c193356af2ce1ec8b3d23ab1a2e2410071`；该版本
`TASK_DETAILS.md` 有 78 个任务行，展开 EngineeringDesign 的七个子任务后为 84 个具体 ID。

## 结论

**没有一道任务是从 Frontier-Eng 拿来的。** 截至 2026-09-03 的原始 15 道 `engineering_design` 题全部由本仓库在 2026-06-15 至 06-20 之间自行建成
(git 首提交作者 carpedkm),早于 `frontier_eng` 这个标签的出现(2026-09-03,PR #3 的治理提交把它作为 analogue 名引入)。
标签指的是"同一形式"(冻结模拟器下的工程设计、连续奖励、可行性约束),不是出处。

逐题对照(Frontier-Eng 侧列"无"表示两个来源都没有同题):

| 本仓库 | Frontier-Eng 同题? | 同类问题? | 说明 |
|---|---|---|---|
| HeatExchangerDesign | 无 | 无 | |
| TrussWeightMinimization | 无 | **有**:ISCSO2015(45 杆 2D 桁架)、ISCSO2023(284 杆 3D 塔) | 本题产物是跨多结构的尺寸策略,评 sealed topology transfer 与载荷/材料/制造偏移下的稳健性;FE 是单实例 FEM 减重。同类不同题 |
| MOSFETDoping | 无 | 无 | |
| DistillationColumnDesign | 无 | 无 | |
| RANSCalibration | 无 | 无 | |
| NeutronDiffusionCriticality | 无 | 无 | |
| RoomImpulseResponse | 无 | 无 | |
| InvertedPendulumSwingUp | 无 | 无(FE 有四旋翼 PIDTuning,不同系统) | |
| LowThrustTransfer | 无 | 同域不同题:MannedLunarLanding 是 CRTBP 月面着陆载荷最大化 | 本题是 MEE 多圈小推力转移策略 |
| CalorimeterDesign | 无 | 无(FE 的 ParticlePhysics 是 MuonTomography / ProtonTherapyPlanning) | |
| MultilayerThinFilm | 无 | 无 | |
| DiffractionGratingDesign | 无 | **有**:Optics/phase_dammann_uniform_orders(二元相位 Dammann 光栅,-3..+3 级均匀) | 本题是五层介质浮雕 RCWA、+1 级效率、TE/TM、密封的工艺偏移;FE 是 diffractio 标量模型的均匀级配。同类不同题 |
| SparseRecovery | 无 | 无 | |
| ElectrolyteConductivityDesign | 无 | 无(FE 的 EnergyStorage 是电池快充) | |
| AlloyHardnessOptimization | 无 | 无 | |

非工程题里另有一处同域:ForceFieldCalibration(发现类,假设判别 + 拒答)对 FE 仓库的 MolecularMechanics/torsion_profile_fitting(拟合优化),形式不同。

## 2026-09-04 新增任务增量核查

以下风险只指与 Frontier-Eng 的任务重合风险，不替代任务卡对一般先验工作的 `novelty_risk`。

| 本仓库 | Frontier-Eng 同题? | 同类问题? | 说明 |
|---|---|---|---|
| AdaptiveConservativePDEMethod | 无 | 同域不同题:论文附录的 DG Navier--Stokes、DiffSim thermal control；仓库任务以连续或离散工程变量优化物理对象 | **重合风险:低。** 本文任务优化可复用的一维守恒律有限体积离散策略，联合选择 reconstruction、limiter、Riemann solver、SSP time integrator 与局部 shock fallback，并审计精度、稳定性、守恒和 work；它不优化某个固定 PDE 的边界条件、几何或控制量。 |
| OpenVocabularyReactionNetworkDiscovery | 无 | 同域不同题:论文附录的 ReactionOptimisation/snar_multiobjective、mit_case1_mixed、reizman_suzuki_pareto；仓库另有 MolecularMechanics 三题 | **重合风险:低。** Frontier-Eng 的反应题在固定已知反应上优化连续工艺参数或催化剂，以产率、废物或催化周转为目标；MolecularMechanics 做参数覆盖、构象组合或扭转能拟合。本文任务从一个种子和重原子清单开放构造规范物种图及有向基元反应边，主动探测并恢复活化能，同时单列假发现、空网络和模型不足拒答；不暴露候选物种或反应目录。 |
| ProcessMicrostructurePropertyDesign | 无 | 同形式不同问题:仓库新增 AdditiveManufacturing/DiffSimThermalControl；论文附录 47 题无过程-微结构-性质协同设计 | **重合风险:中。** Frontier-Eng 近邻只在固定增材制造 toolpath 上优化激光功率 knots，以热轨迹、固/液相温区、平滑度和能耗组成损失；本文任务提交 4--20 个共混、退火、冷却和拉伸工艺配方，经冻结相场/粗化再均匀化为比模量、阻隔与过程能耗三目标 Pareto 档案，并检查密封材料和过程偏移。二者同为制造过程仿真优化，但物理系统、决策变量、产物和评分对象均不同。 |

## 处置

1. analogue 改名 `frontier_eng` → `engineering_design`,含义不变;README 的形式树写成"与 Frontier-Eng 同形式,任务不重合"。
2. 两道同类不同题(TrussWeightMinimization、DiffractionGratingDesign)保留:它们在 7 任务冻结队列里,改题等于重测全部证据;
   区别已写在本文,后续改卡片时同步进 `novelty_risk`。是否要用别的题替换,由维护者决定。
3. 新题的建题规则进 CONTRIBUTING 检查清单:建题前对照 FE 的两份目录,同一问题类不再立题。
   本轮计划中的新题(隐藏耦合网络重建、强迫信号归因、黑盒群结构辨识)均不在 FE 目录内。
