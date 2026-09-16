## Why

`openspec/specs/wayfinder/spec.md` 中的 **Req 17 L311** 与 **Req 19 L356** 在同一份 spec 内对 routing overhead 的子项口径不一致：Req 17 把 extract_C pipeline 算成 `33_040 MACs = 66_080 FLOPs`（含 `+128 MACs` bias add + `+144 MACs` per-head L2-normalize = `+544 FLOPs`），而 Req 19 的 `FLOPs_Routing^(l) = 4·d_c·H_kv·d_k + 2·N_e·d_c = 66_048 FLOPs` 只把 projection + gating similarity 计入、把 bias 与 L2-normalize 完全漏掉。两者在 MVP 配置下净差 **32 FLOPs**（`544 − 512 = 32`），如不解释会让"为什么 Req 17 报 66_080、Req 19 报 66_048"成为悬案。

## What Changes

- 在 `openspec/specs/wayfinder/spec.md` 的 **Req 19**（"Six Baseline Set On 4070 MVP"）中，紧跟 routing overhead 公式与 MVP 数值之后，新增一段 cross-req 备注，明确：
  1. Req 19 的 `FLOPs_Routing` 与 Req 17 L311 的 extract_C pipeline 成本（`66_080 FLOPs`）口径不同——后者把 bias add (`+128 MACs`) 与 per-head L2-normalize (`+144 MACs`) 折算进 projection，后者没有。
  2. 两者口径合并后差 `+32 FLOPs`（= `(128+144)·2 − 2·N_e·d_c = 544 − 512`），方向是 **Req 17 高出 32 FLOPs**——这是因为 Req 17 把"投影 + bias + L2-norm"做单算子合计、Req 19 把"投影 + gating similarity"做单算子合计，且 gating similarity (`2·N_e·d_c = 512`) 比 bias+L2-norm (`544`) 少 32 FLOPs。
  3. **不**改 FLOPs 公式，不改 MVP 数值 `66_048`，不改 active-core denominator。仅作 cross-req 一致性说明。
- 该备注以 `(historical, <origin>; supersedes none)` 风格的归因锚到 `wayfinder/tickets/A8-1.md`（Req 19 的现有 Source），并在文本内 backtick 引一次 `wayfinder/tickets/A7-2.md` 标明对端（Req 17）来源——确保 `lint_no_source_field_drift.py` 的 capability-aware reverse-link 检查通过。

## Capabilities

### New Capabilities
<!-- 无新增 capability；本 change 仅澄清既有 Req 19 文本 -->
无

### Modified Capabilities
- `wayfinder`: Req 19 routing overhead 段新增 cross-req 备注，澄清与 Req 17 extract_C pipeline 之间的 `+32 FLOPs` 净差（不改变公式、不改变数值、不改变 active-core FLOPs parity 核算）。

## Impact

- **Spec 文档**：`openspec/specs/wayfinder/spec.md` 的 Req 19 段（"Six Baseline Set On 4070 MVP"）一处加注。
- **代码**：无影响（这是 spec-level 一致性修缮；不触发 `src/decompmoe/**` 的任何代码改动）。
- **测试**：无影响（不是算式闭式常量改动，不引入新 pytest 条款）。
- **Lint 门**：`scripts/lint_no_source_field_drift.py` 必须 exit=0（保留 Req 19 现有 `**Source:**` 字段的 backtick-wrapped `wayfinder/tickets/A8-1.md` 形式；cross-req 备注中提及 A7-2 时同样 backtick 包裹）。