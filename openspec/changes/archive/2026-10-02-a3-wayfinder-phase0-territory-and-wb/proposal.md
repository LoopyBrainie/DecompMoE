# Proposal

## Why

A-3 桶（spec ↔ src 语义偏离）在 change
`2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix` 的 task 3.1–3.5
完成后得到逐条重判。其中 3 条落在 `wayfinder` spec 侧，且**都不是代码 bug，而是
spec 自身的契约缺口**——直接改代码会把未定义的契约固化：

1. **Phase 0 范数不变量在两份 peer spec 间互斥（AC-35 / AC-14）**。Req 23 的
   Scenario 写「any Phase（0 K-Means, 1–3 EMA, 4 Projected SGD）」满足
   `max_i |‖c_i‖₂ − 1.0| < 1e-7`，而 `decompmoe-skeleton` req-18 声明 Phase 0 的
   driver 是 no-op、归一化是**调用方**责任。两者对同一 MUST 给出互斥约束，且
   现有测试无一断言 Phase 0 的范数（`tests/test_extraction_phase.py:25` 跑了
   Phase 0，但只断言 `requires_grad`/`grad_fn`）。这是一颗只在 Phase 0 被真正
   调用时才会引爆的雷。

2. **`territory_collapse` 是 MUST 级悬空标识符（AC-32 / AC-45）**。req-2 的 7 项
   MUST 标识符映射表里，`territory_collapse` 在 `src/` 与 `tests/` 中均零命中
   （两种检索式交叉确认，并以 `territory_seeding` 的 4 处 src 命中作阳性对照
   证明计数器有效），且不像同列表的 `territory_seeding` 那样有 deferred
   Requirement 承接。**spec-only 悬空**：缺口存在于唯一声明它的地方，而那里
   无法执行。

3. **req-15 Layer 2 的两个具体阈值无任何落地或标注（AC-56）**。`WB = 0.0476` 与
   `> 2.0` 严重聚类阈值在 `src/decompmoe/` 中零命中；`advisory_signals()` 是纯
   透传（L194-199 原样返回四个 kwargs）。重判同时更正 audit 的两处错误：归属是
   **req-15 而非 req-15/16**（req-16 从不提及 WB），且「src 与 tests 双零」字面
   为假（`tests/test_schedule.py:135` 有 1 处散文命中，虽在 docstring 内）。

## What Changes

- **req-23 收窄为 Phase 1–4**：Scenario 的 WHEN 由「any Phase（0 K-Means …）」
  改为「Phase 1–4」，并在正文加 Phase scope 注记说明 Phase 0 被排除的理由
  （no-op driver 不产生 driver-channel update；Phase 0 的范数前置条件是调用方
  义务，见 skeleton req-18）。Scenario 标题同步改为
  `Spherical norm is strictly one in Phase 1-4`，避免标题继续暗示一个不存在的
  Phase 0 测试。
- **req-2 增补 `territory_collapse` 的 deferral 注记**，与既有的
  `territory_seeding` 注记同构。
- **新增 `req-38` Territory Collapse Deferred Contract**：把该标识符从
  MUST 级降为 MVP 期 spec-only 的 deferred 契约，并显式记录**为何不设占位函数**
  ——MVP 没有该统计量的闭式，占位函数会断言一个未推导的签名。
- **req-15 增补 Layer 2 deferral note**，写明 `advisory_signals()` 是纯透传、
  两个阈值在 src/tests 中无**可执行**命中，并指向已存在的移交记录
  （`tests/test_schedule.py::test_advisory_signals_read_only` 与引入 Layer 2 的
  change proposal）。

**不改动**：`src/**`、`tests/**`、`decompmoe-skeleton` spec、`.audit/**`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder` — req-2 增补 deferral 注记；req-15 增补 Layer 2 deferral note；
  req-23 收窄 Phase scope；新增 req-38。

## Impact

- **受影响 capability**：`wayfinder`（Requirement 数 36 → 37）。
- **不改动代码**：本 change 是纯 spec 契约收口。AC-14 的测试覆盖缺口与 AC-35 的
  req-18 侧 MUST 升格分别由后续 change 承接（后者在
  `decompmoe-skeleton` 侧，与本 change 配对）。
- **反链有据**：`territory_collapse` 在 `wayfinder/tickets/A1-1.md:112` 的符号
  命名映射表中有真实血缘，而 A1-1 正是 req-2 自身的 Source 反链票。故 req-38 的
  反链写 `` `wayfinder/tickets/A1-1.md` ``——有据，非杜撰。
- **与重判台账的对应**：`AC-35`（wayfinder 侧）、`AC-32`、`AC-45`（同一实体，
  按台账 104 分母保留两个 id 但只做一次修复）、`AC-56`、`AC-14`（wayfinder 侧）。
