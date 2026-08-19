## Why

DecompMoE（"decomposed MoE"，项目命名见 `wayfinder/tickets/A0-1.md`）的整套设计当前仅以 `wayfinder/map.md` + `wayfinder/tickets/A*-*.md` 的探索/笔记形式存在。`map.md` 自报 **Map Status: CHART COMPLETE**——全部 20 个 ticket 关闭，决策可由 decisions + ticket body 编译 spec。但 `openspec/specs/` 为空，OpenSpec 尚未成为该子系统的真相源；设计与后续评审 / delta / 实现之间没有正式契约。

本次 formalize 的目标：把 `wayfinder/` 下已完备的设计资产以 OpenSpec 的 capability spec、design、tasks 制品固化下来，让 OpenSpec 接管真相源，并明确**不引入实现代码**——本次 change 是设计资产的迁移/编译，不是落地实现。

## What Changes

- **新增** capability `wayfinder` 的主 spec（`specs/wayfinder/spec.md`），按 A0–A8 八大章节化展开 21 个 ticket 的结论：命名/术语（A0/A1）、拓扑挂载点（A2）、C 提取算子（A3）、距离度量与门控（A4）、专家结构与超参（A5）、损失与数值稳定/调度（A6a/A6b）、推理增量（A7）、baseline 与几何量化指标/可视化（A8）。
- **新增** `design.md`：把决策之间的耦合（A6a↔A6b、C 提取↔门控↔专家、4 阶段时间驱动 + 状态 advisory）、关键数学构造（球面归一、各向同性弦长、`L_sep` 软正交、5 项 safeguard）、物理参数（KV cache 0 增量、Decode 走 SRAM）与框架兼容面，沉淀为一张可被实现者直接读懂的架构图谱。
- **新增** `tasks.md`：把 formalize 拆为可勾选步骤（spec 章节编译、跨章节一致性校验、design 图表与数学主文档起草、与原 tickets 的引用矩阵），全部任务均为文档制品，**不写 Python 代码**。
- **保留** `wayfinder/map.md` 与 `wayfinder/tickets/*.md` 作为 trail；spec 内的每个 Requirement 通过 `**Source**:` 反向引用对应 ticket id，不删除原文件以保留决策上下文。

## Capabilities

### New Capabilities

- `wayfinder`: DecompMoE 的唯一形式化真相源。覆盖命名/术语、Decoder-Only Llama 内的 Post-FFN 几何路由（GeometricRouter → TerritoryHolder）、C 提取算子（per-head 投影 + 球面归一 + cross-head mean）、Top-k 稀疏掩码 + Local Softmax 纯几何凸组合门控、Standard SwiGLU FFN 专家、损失三件套（`L_CE + α·L_lb + λ(t)·L_sep`）与 5 项数值 safeguard、5 阶段时间驱动 + 3 层混合触发器调度、Prefill/Decode 解耦的零 HBM 增量推理、6 类 baseline + 8 项几何量化指标 + 6 模块可视化工具链。Scope Lock：仅 Decoder-Only Llama；显式排除 Linear Attention / SSM / RNN；不包含训练执行与论文写作。

### Modified Capabilities

无（specs/ 首次引入，无既有 capability）。

## Impact

- **新增制品**：
  - `openspec/specs/wayfinder/spec.md`（capability 主 spec）
  - `openspec/changes/introduce-wayfinder-decompoe-spec/{proposal,design,tasks}.md`
- **既有资产**：保留 `wayfinder/map.md` 与 `wayfinder/tickets/A0-1.md … A8-3.md`（21 个 ticket），作为决策 trail。后续对 DecompMoE 的任何 spec-level 变更将通过 OpenSpec 的 delta 形式进入 `specs/wayfinder/`，原 tickets 视为历史快照。
- **代码库**：本次 change 不编辑 `wayfinder/` 之外的任何 Python 代码；formalize-only。
- **依赖/外部系统**：无新增第三方依赖；OpenSpec 仍是单仓本地流程，无 store。
- **风险**：spec 与原 tickets 的微小措辞漂移（formalize 是翻译/压缩过程）；通过在每个 Requirement 标注 `**Source**:` 引用 ticket id 兜底，并通过 tasks.md 中的"跨章节一致性校验"任务强制审阅。
- **交付规格**：本 change 包含 21 Requirements × 34 Scenarios（grep `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` 验证）。
