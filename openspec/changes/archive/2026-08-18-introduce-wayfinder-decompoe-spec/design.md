## Context

Wayfinder 子系统（`wayfinder/` 目录下 `map.md` + 21 个 ticket）自报 **Map Status: CHART COMPLETE**——全部 20 个 ticket 关闭，决策可编译 spec。但 OpenSpec 尚未成为其真相源：`openspec/specs/` 为空，无主 spec、无 delta、无 archive。本次 change 是 formalize-only：把现有设计资产编译为 OpenSpec capability spec，不引入实现代码、训练执行或论文写作。详见 `proposal.md - Why`。

## Goals / Non-Goals

**Goals:**
- 让 `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md`（archive 后落到 `openspec/specs/wayfinder/spec.md`）成为 DecompMoE 设计的唯一 OpenSpec 真相源
- 通过 `**Source:**` 反链保留 `wayfinder/tickets/*.md` 的决策 trail，让 reviewer 能从 spec 跳回原决策
- 为后续 code-level delta（例如 `add-decompoe-mvp-module`、`add-geometric-router`）提供稳定的 capability 锚点
- 通过 5 个制品（`proposal.md` / `specs/wayfinder/spec.md` / `design.md` / `tasks.md` + archive 后的主 spec）的依赖关系保证规划完整性

**Non-Goals:**
- 不写任何 Python 实现代码
- 不发起训练、不产出 baseline 结果
- 不撰写完整 arxiv 论文（实验 / ablation / 相关工作综述）
- 不删除 `wayfinder/map.md` 与 `wayfinder/tickets/*.md`（保留 trail）
- 不二次决策或重写 ticket 结论（formalize 是翻译/压缩，不是再 grill）

## Decisions

### Decision 1: 单 capability `wayfinder`

把 21 ticket 收拢到一个 capability，目录路径 `specs/wayfinder/`，主 spec 按 A0–A8 章节化展开每个 ticket 决策。

**Why:** Wayfinder 是一个自治子系统（命名、范围、设计资产都自洽）。首次引入 OpenSpec 应遵循 YAGNI，把管理负担与 delta 粒度风险最小化。

**Alternatives considered:**
- 按 A0..A8 拆 8 个 capability —— 细粒度但管理负担最重；命名 / 符号 / 阶段时长等横切项难归属（一个 Requirement 会跨多个 capability）。
- 按主题聚类拆 4–5 个 capability（如 `core-concepts` / `routing` / `expert-architecture` / `training-loop` / `inference-eval`）—— 在扁平与细粒度之间折中，但首次引入仍属过度切分；待出现具体跨主题 delta 时再切。

### Decision 2: Spec 仅承载 ADDED Requirements 与 Source 反链

Delta 文档 `specs/wayfinder/spec.md` 仅包含 `## Purpose` + `## ADDED Requirements` + 每个 Requirement 的 `#### Scenario`（4 个 #），并以 `**Source:**` 引用 ticket id。

**Why:** OpenSpec spec 是 behavior contract，不是实现说明；可测试的最小契约由 Requirement + WHEN/THEN Scenario 提供。`Source:` 反链把 spec 与原 ticket 绑死，避免 formalize 软化原约束（精确数字如 β ∈ [0.1, 32]、FLOPs ≈ 65.5 K/token、W_proj ≈ 64 KB、Phase 时长 1/5/20/30/44% 都直接抄录而非重述）。

**Alternatives considered:**
- 在 spec 内重写 rationale 与 alternatives considered —— 与 design.md 角色重叠，且使 spec 过长，违反 "spec is a behavior contract"。
- 用 Markdown bullet 取代 OpenSpec Requirement 结构 —— 违反 spec-driven 规范，`openspec validate` 会失败。
- 把 phase schedule / hyperparameter set 等放进 design.md 而非 spec.md —— 错；这些是用户可观测的行为约束（每个 step 的 β 演变 / 整个训练的 FLOPs parity），属于 SHALL/MUST。

### Decision 3: design.md 描述"如何 formalize"而非"系统如何实现"

Design 文档聚焦本次 change 自身的结构选择（capability 切分、Source 反链、章节化、跨章节一致性校验任务），不重述 spec 中的 Requirement；不写代码、不写数学。

**Why:** spec-driven schema 中 proposal = why / specs = what / design = how。本次 change 是 formalize，"how" 就是"如何把 wayfinder 的设计资产编译进 OpenSpec"。系统的"如何实现"留给未来 code-level delta 的 design.md。

### Decision 4: tasks.md 不含实现代码任务

Tasks 拆为：编译 spec 章节 → 跨章节一致性校验 → 起草引用矩阵 → 准备 archive 触发条件验证。所有任务都是文档制品。

**Why:** 严格遵守用户在 AskUserQuestion 中选定的 formalize-only 目标；tasks.md 必须与 `proposal.md - What Changes` 对齐（"不写 Python 代码"已显式声明）。

## Risks / Trade-offs

- **[Risk] 措辞漂移**：21 ticket 编译成 spec 时可能引入轻微措辞不一致。**Mitigation:** 每个 Requirement 标注 `**Source:**` 反链 ticket id；`tasks.md` 第一项是"跨章节一致性校验"，强制 review 所有 Requirement 的 Source 反链完整性与数值与原 ticket 一致。
- **[Risk] 命名歧义**：DecompMoE vs GeoMoE alias 可能引发 spec 内部不一致。**Mitigation:** spec 第一个 Requirement [Naming And Alias Convention](../specs/wayfinder/spec.md#req-1) 锁住命名层级；后续所有 Requirement 引用项目时用 DecompMoE。
- **[Risk] capability 切分过粗**：未来若要把 routing / training / eval 拆为独立 capability，需要做 capability split。**Mitigation:** 在 design.md Future Work 中显式记录此 trade-off；当实际出现跨主题 delta 时再触发；archive 不阻塞后续 split。
- **[Risk] archive 触发条件模糊**：本次 change 是"首次引入主 spec"，archive 后会把 `specs/wayfinder/spec.md` 复制到 `openspec/specs/wayfinder/spec.md`，原 deltas 不存在。**Mitigation:** archive 前必须确保 `openspec validate --strict` 通过；`specs/wayfinder/spec.md` 含完整 Purpose 段（≥ 50 字符），无 "TBD Update Purpose after archive" 占位符。
- **[Risk] Source 反链维护成本**：未来 ticket 文件被改写时，反链可能断链。**Mitigation:** 反链引用 ticket 文件路径与 ticket id（如 `wayfinder/tickets/A3-1.md`），不依赖行号；ticket 文件不删除，仅新增 supersede 版本。

## Open Questions

无。所有 material 决策已通过 AskUserQuestion 与 Source 反链闭环；后续若出现 phase schedule 具体数值（如 100 K 还是更长）、baseline 数据集选型等，属于未来 code-level delta 的范畴，留给对应 change 的 spec 增量阶段处理。
