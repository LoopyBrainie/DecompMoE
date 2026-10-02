# Proposal

## Why

A-3 桶在 change `2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix`
的 task 3.1–3.5 完成逐条重判后，有 4 条落在 `decompmoe-skeleton` spec 侧。其中
3 条是 **spec 自身的契约缺口**（改代码会把未定义的契约固化），1 条是 spec 侧记录
（代码才是偏离方）：

1. **req-18 的 Phase 0 义务只是描述性文字，不是 MUST**（AC-35 / AC-14）。原文写
   「the `‖c_i‖₂ ≡ 1.0` invariant for Phase 0 is the caller's responsibility, not the
   driver's」——一句括号内的说明。它与 `wayfinder` req-23 原先的「any Phase（含 0）」
   构成两份 peer spec 对同一 MUST 的互斥约束。`wayfinder` 侧已由配对 change 收窄为
   **Phase 1–4**；若 skeleton 侧不把该义务升格为显式 MUST，Phase 0 的范数就会
   **两边都不管**——从「互斥」变成「真空」，比原状更糟。

2. **req-1 的「every public symbol」没有去重规则**（AC-78）。审计实测该数量为
   「76 个」，而重判复算发现：**13 个子模块 `__all__` 逐个求和 = 76，去重并集 =
   75**，唯一冲突是 `flops_per_token` 同时声明在 `config` 与 `metrics`（后者是转发
   wrapper）。**「76」是求和未去重的产物**。spec 正文未钉任何数字，所以这不是 spec
   写错，而是不钉规则就会让每个下游都重新踩同一个坑。

3. **req-7 的 `‖C_t‖₂ = 1` 是无条件断言，与本 spec 自己的 req-19 矛盾**
   （`X-main38`，Stage 0 由盲区层新纳入）。req-7 L149 写「`‖C_t‖₂ = 1` for every
   token (within 1e-5)」，而 req-19 L471-472 明文规定退化区 `0 < ‖z‖₂ < ε` 首次
   作用产生 `‖out‖₂ = ‖z‖₂/ε < 1`（次单位范数）。管线的球面投影步除以
   `max(‖·‖₂, ε)`，故该矛盾是**可达**的，不是纸面之争。

4. **req-18 的 `mask` 已是必填位置参数，偏离方是代码**（AC-17）。spec 侧无需改动，
   本 change 只把它写成显式 MUST 并说明**为什么不允许给默认值**；代码侧的修复在
   配套 change 中进行。

## What Changes

- **req-18 签名处**：把 `mask` 提升为显式的 REQUIRED 位置参数条款，写明缺少
  `mask` 时 MUST 拒绝而非替代——默认 `mask=None` 会诱使实现用全批均值替代
  per-expert masked mean `m_i`，从而把同一个均值广播给所有质心并使所有 territory
  坍缩到一点。
- **req-18 Phase 0 条目**：把「调用方责任」从括号内说明升格为**规范性 MUST**，
  声明 driver MUST NOT 归一化/投影/修复 Phase 0 输入，并交叉引用已收窄的
  `wayfinder` req-23（Phase 1–4），说明两侧 MUST 由此不再冲突。
- **req-1**：增补**去重规则**（规范性）：「every public symbol」= 13 个子模块
  `__all__` 的**去重并集** = **75** 个名称；加 3 个 dunder 后包级 `__all__` 共
  **78** 项；唯一跨模块冲突 `flops_per_token` MUST 绑定到 `config` 定义，
  `metrics` 版须保持 `decompmoe.metrics.flops_per_token` 可达；并显式声明
  **求和得 76 不是期望总数**。
- **req-7 输出一致性 Scenario**：把无条件范数断言加上前置条件（每个 per-head 投影
  `‖z^{l,h}‖₂ ≥ ε = 1e-6`），并说明退化区会产出次单位范数，与 req-19 使用**同一**
  阈值。

**不改动**：`wayfinder` spec、`src/**`、`tests/**`、`.audit/**`。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `decompmoe-skeleton` — req-1 增补去重规则；req-7 输出一致性断言加前置条件；
  req-18 增补 `mask` 必填 MUST 与 Phase 0 规范性义务。Requirement 数不变（23）。

## Impact

- **受影响 capability**：`decompmoe-skeleton`。
- **不改动代码**：本 change 是纯 spec 契约收口。req-1 的 75/78 计数与 `mask` 必填
  的代码侧落地分别在后续配套 change 中完成，并各自带数值/签名测试。
- **与 `wayfinder` 配对**：本 change 是
  `2026-10-02-a3-wayfinder-phase0-territory-and-wb` 的对应半边。两侧只改一条都会
  留下不一致——这正是 AC-35 的成因。
- **与重判台账的对应**：`AC-35`（skeleton 侧）、`AC-14`（测试覆盖落点）、
  `AC-17`（spec 侧记录）、`AC-75`（req-7 签名为准，代码对齐）、`AC-78`
  （去重规则）、`X-main38`（req-7 vs req-19）。
