## Why

`fix-spec-doc-oversights` 已 archived（spec delta 合并到主 spec 与 skeleton spec）。其 proposal.md "Downstream Hand-off" 段明确锁定 3 项 code-level 修复（Issues ⑥⑦⑧）不在 spec-only change 范围内执行，必须由 archive 后用户显式触发的下游 code-level change `fix-spec-doc-oversights-apply` 同步实现：

- **Issue ⑥**：`src/decompmoe/extraction.py:126` 当前 `return alpha * centroids + (1.0 - alpha) * mean` 缺 `F.normalize(..., dim=-1)`，违反 skeleton spec L129-131 要求的 `Normalize(α·c_i + (1−α)·m_i) / ‖·‖₂`。
- **Issue ⑦**：`src/decompmoe/extraction.py:124-125` 当前 `denom = weights.sum(dim=0).clamp_min(1e-9); mean = (weights.T @ X) / denom.unsqueeze(-1)` 在 `n_i = 0` 时 `denom = 1e-9` 而非回退到 `c_i`，违反 spec 明确 "Empty-Cell Invariant" 与 "no `clamp_min(ε)` denominator"。
- **Issue ⑧**：skeleton spec L337-351 列出的 3 个 invariant test scenarios (`test_empty_cell_preserves_centroid` / `test_spherical_norm_is_strictly_one` / `test_near_zero_candidate_fallback`) 在 `tests/` 完全不存在（grep 0 命中），由 archived spec 的 ADDED Requirement "Centroid Driver Semantic Invariants" 显式要求。

本 change 严格遵循 CLAUDE.md §3 SDD 流程：每条 Issue = 1 个 RED → GREEN → Refactor 循环，每条 pytest 必须含数学原理约束（CLAUDE.md §6 硬约束）。

## What Changes

修改 `src/decompmoe/extraction.py` 的 `CentroidDriver.step` 方法实现以满足 Issues ⑥⑦：
1. 删除 `.clamp_min(1e-9)` 作为 empty-cell 分母，改用 `torch.where(n_i > 0, mean_n, centroids)` 显式回退（Issue ⑦）
2. EMA 三相位（Phase 1/2/3）输出改为 `F.normalize(alpha * centroids + (1.0 - alpha) * mean, dim=-1)`（Issue ⑥）
3. 新增 near-zero candidate fallback：当 `‖u_i‖₂ < 1e-9` 时回退到 `centroids`（invariant 2 派生）

修改 `tests/test_extraction_phase.py` 的 EMA expected 值（同步到归一化形式）。

修改 `tests/test_extraction.py` 新增 3 个 invariant test scenarios（Issue ⑧），断言与 skeleton spec Scenario 严格对齐：
- `test_empty_cell_preserves_centroid`: `‖c_i^(t+1) − c_i^(t)‖₂ < 1e-12`
- `test_spherical_norm_is_strictly_one`: `max_i |‖c_i‖₂ − 1.0| < 1e-7` after Phase 1-4
- `test_near_zero_candidate_fallback`: `c_i^(t+1) == c_i^(t)` element-wise + no NaN

## Capabilities

### New Capabilities

无（code-only change，不引入新 spec 边界；spec contract 由 archived `fix-spec-doc-oversights` 锁定）。

### Modified Capabilities

无（本 change 不修改任何 Requirement；spec 一致性由 archived change 维护）。

## Impact

- **Spec 层**：本 change **不动** `openspec/specs/wayfinder/spec.md` 或 `openspec/specs/decompmoe-skeleton/spec.md`。spec contract 由 archived `fix-spec-doc-oversights` 锁定（已 merge 到主 spec 与 skeleton spec）。
- **代码层**：`src/decompmoe/extraction.py`（`CentroidDriver.step` 改写）；`tests/test_extraction.py`（新增 3 个 invariant test）；`tests/test_extraction_phase.py`（EMA expected 值同步到归一化形式）。
- **Ticket 层**：CLAUDE.md §8 2026-08-21 裁决 wayfinder 不再是必改制品。
- **下游 change**：`openspec/changes/fix-openspec-doc-bugs-apply/`（同步）会处理 wayfinder Req 6/7/11/12/13/14/19/20 + 4 个 ADDED Requirement 的 code-level 修复。

## Out of Scope（明确不动）

- 不执行训练、不跑 baseline、不读实验数据（CLAUDE.md §6）
- 不修改 `src/decompmoe/sphere.py` 的 Voronoi 公式（属于 `fix-openspec-doc-bugs-apply` 范围 SS-7）
- 不修改 `src/decompmoe/loss.py` 的 `L_lb` 闭式（属于 `fix-openspec-doc-bugs-apply` 范围 SS-13）
- 不修改 `src/decompmoe/safeguards.py` 的 `DEAD_EXPERT_FRACTION`（属于 `fix-openspec-doc-bugs-apply` 范围 SS-14）
- 不修改 `src/decompmoe/schedule.py` 的 `phase_step_frozen_names(2)`（属于 `fix-openspec-doc-bugs-apply` 范围 SS-15）
- 不修改 `src/decompmoe/metrics.py` 的 S_load/UR/OFFLINE 闭式（属于 `fix-openspec-doc-bugs-apply` 范围 SS-16）
- 不重写 wayfinder ticket（CLAUDE.md §8 2026-08-21 裁决）