## Why

`openspec/specs/decompmoe-skeleton/spec.md` 包含两处需要修复：

1. **结构违规**（孤儿 Scenario 副本）：L349-360 是三个 `#### Scenario:` 块（"Parameterization endpoints" / "gamma reset for phase 4 boundary continuity" / "beta_effective is continuous at Phase 3 → 4 boundary"），**与 L427-440 逐字相同**，但 L349-360 没有 `### Requirement:` 父标题——它们夹在前一个 Requirement "Centroid Driver Invariant Test Scenarios"（L331-347）与下一个 Requirement "Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension"（L365-396）之间，是孤儿。这是 OpenSpec 格式违规：每个 `#### Scenario:` 必须有 `### Requirement:` 父级，且重复 Scenario 与"单一权威"原则相违。历史来源：上一个 change `2026-09-10-fix-wayfinder-and-skeleton-spec-duplicate-requirements` 显式决定保留这些 orphan Scenarios（其 `tasks.md` L7 + L13："保留 L436 / L440 / L444 orphan Scenarios"），但实际未补足其在 L349-360 处的结构对齐；本次 change 关闭该遗留漏洞。
2. **完整性缺口**（SP 下界缺闭式见证）：现有 spec 在 req-20（"Eight Metrics And Classification — CG Type Guard"，L471）下给了 3 个 SP 闭式场景——`SP = 1`（orthonormal-aligned inputs，L504-507）、`SP = 0.5`（60° offset，L509-512）、泛 range bound `−1 − 1e-6 ≤ SP ≤ 1 + 1e-6`（L514-517）。上界与中点都有具体闭式见证，但**下界 −1 仅靠泛断言**，没有"什么输入产生 `SP = −1`"的闭式场景——这与上/中点的覆盖不对齐，对应 `tests/test_metrics.py` 也缺 `test_sp_antipodal_aligned_inputs`（现有 `test_sp_*` 仅 4 个：orthonormal / 60° / skip-empty / range-containment）。`SP ∈ [−1, 1]` 的下界紧性可由 `c_iᵀ C_t ∈ [−1, 1]` + `C_t = −c_{a(t)}` 反极点对齐构造证实（`SP_i = c_iᵀ(−c_i) = −1`）。

## What Changes

- **REMOVE** `openspec/specs/decompmoe-skeleton/spec.md` L347-360（`---` 分隔符 + 三个孤儿 `#### Scenario:` 块）。三个 Scenario 的内容已**逐字**保留在 L427-440（req-3 "Beta Parameterization Operational Domain — D1 Module-Level Constants" 下），删除后无内容丢失。
- **ADD** `openspec/specs/decompmoe-skeleton/spec.md` 一个新 Scenario，紧接 L512 之后（"SP closed-form on 60° offset" 后、`SP range bound` 前）：
  ```
  #### Scenario: SP closed-form on antipodal-aligned inputs
  - **WHEN** `SP(centroids, assignments, signatures)` is called with every
 assigned token's signature equal to the antipode of its assigned centroid
     (`C_t = −c_{a(t)}` for all `t ∈ T_i`)
  - **THEN** the aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` equals `−1.0`
     within `abs=1e-6` (each `SP_i = c_iᵀ (−c_i) = −1`)
  ```
- **ADD** `tests/test_metrics.py::test_sp_antipodal_aligned_inputs`，使用 `pytest.approx(−1.0, abs=1e-6)` 对账闭式常量；对称于已有的 `test_sp_orthonormal_aligned_inputs`（L171，上界 = 1.0）和 `test_sp_60_degree_offset`（L183，中点 = 0.5）。

无代码（`src/decompmoe/`）改动——`SP` 实现已经在 `metrics.py:92-97` 按定义计算 `SP_i = mean(c_iᵀ C_t)`，新场景仅是被现有实现满足、但此前未在 spec 中显式声明的闭式覆盖。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `decompmoe-skeleton`:
  - **REMOVE** 三个孤儿 Scenario（"Parameterization endpoints" / "gamma reset for phase 4 boundary continuity" / "beta_effective is continuous at Phase 3 → 4 boundary"）—— 它们在 spec 主文件中已**逐字**保留于 req-3（L427-440），删除不损失任何 spec 覆盖。这是结构清理，不修改任何 Requirement 的 body，也不删除任何 active requirement。
  - **ADD** 一个新 Scenario `SP closed-form on antipodal-aligned inputs` 于 req-20（"Eight Metrics And Classification — CG Type Guard"）下，与既有 `SP closed-form on orthonormal-aligned inputs`（L504-507，上界 = 1.0）和 `SP closed-form on 60° offset`（L509-512，中点 = 0.5）形成对称闭式覆盖（上 / 中 / 下 三点紧点均闭式可见）。

## Impact

- **代码层**：`src/decompmoe/metrics.py` 零改动。`SP` 实现（`metrics.py:92-97`）已按 `SP_i = mean_{t: a(t)=i} c_iᵀ C_t` 计算，新 Scenario 是现有实现的闭式覆盖点，不需要任何代码变更。
- **测试层**：`tests/test_metrics.py` 新增 1 个测试 `test_sp_antipodal_aligned_inputs`（与 `test_sp_orthonormal_aligned_inputs` / `test_sp_60_degree_offset` 风格对称）。无现有测试被修改或删除。
- **CI / lint**：
  - `python scripts/lint_no_dead_defensive.py` 必须 exit=0（archive 前置条件）
  - `python scripts/lint_no_source_field_drift.py` 必须 exit=0（archive 前置条件）—— 本次不引入任何新 `**Source:**` 行，新 Scenario 直接挂接 req-20 不带 source 字段，与既有 L504-512 两个 SP 闭式 Scenario 一致
  - `openspec validate` 必须 pass
- **历史追溯**：被删孤儿 Scenario 的内容在 req-3 (L427-440) 已**逐字**存在，可通过本 change 的 git diff 反向找回任何被移除的文本（diff 显示 14 行删除：3 行 `---` + 11 行 Scenario 行）。来源 ticket：`wayfinder/tickets/A3-2.md`（Masked Spherical EMA 推导 — `parameterization endpoints` 与 `gamma_reset_for_phase4` 决策的原始 ticket）。
- **Spec 主文件**：净改动 `decompmoe-skeleton/spec.md` 14 行删除（L347-360）+ 8 行新增（一个新 Scenario）。req-20 net 增加 1 个 Scenario，总 Scenario 数 `76 → 77`（参见 `openspec/specs/decompmoe-skeleton/spec.md` 当前 76 个 Scenario）。