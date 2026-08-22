## Context

`fix-spec-doc-oversights-apply` 是 archived spec-only change `fix-spec-doc-oversights` 的下游 code-level apply change。spec delta（Issues ①②③④⑤⑨）已 merge 到主 spec 与 skeleton spec，但 3 项 code-level hand-off（Issues ⑥⑦⑧）须由本 change 同步实现。

本 design 文档聚焦实现侧的技术决策：如何把 spec 文本的数学约束落到 `src/decompmoe/extraction.py` 与 `tests/test_extraction*.py`，并保证 `pytest.approx` 直接验算 spec 声称的数学不等式（CLAUDE.md §6 硬约束）。

上游 spec contract 已锁定的关键数学不变量（来自 archived skeleton spec "Centroid Four-Phase Lifecycle Driver" + ADDED "Centroid Driver Semantic Invariants"）：
- EMA 输出 `‖c_i‖₂ = 1.0` within `1e-7`
- `n_i = 0 ⇒ m_i ≡ c_i^(t−1)` ⇒ `c_i^(t+1) = c_i^(t)` element-wise within `1e-12`
- near-zero candidate `‖u_i‖₂ < 1e-9 ⇒ c_i^(t+1) = c_i^(t)` element-wise + no NaN
- EMA 系数 Phase 1/2/3 = 0.90 / 0.95 / 0.99

## Goals / Non-Goals

**Goals:**
- 把 3 项 hand-off contract（Issues ⑥⑦⑧）落地到 `extraction.py` 的 `CentroidDriver.step` 方法
- 新增 3 个 invariant test scenarios（`test_empty_cell_preserves_centroid` / `test_spherical_norm_is_strictly_one` / `test_near_zero_candidate_fallback`），与 skeleton spec Scenario L341-351 严格对齐
- 同步更新 `test_phase_090_ema` 等现有 EMA 测试的 expected 值到 `F.normalize` 归一化形式
- 每条 pytest 必须含 `pytest.approx` / `torch.allclose(..., atol=...)` 直接验算 spec 数值（CLAUDE.md §6 硬约束）

**Non-Goals:**
- 不修改 `src/decompmoe/sphere.py`（Voronoi 公式升级属于 `fix-openspec-doc-bugs-apply` SS-7）
- 不修改 `src/decompmoe/loss.py`（L_lb 闭式属于 `fix-openspec-doc-bugs-apply` SS-13）
- 不修改 `src/decompmoe/safeguards.py`、`schedule.py`、`metrics.py`（属于 `fix-openspec-doc-bugs-apply`）
- 不执行训练、不跑 baseline（CLAUDE.md §6）
- 不修改 openspec specs 文件（已 archived 锁定）

## Decisions

### Decision 1 — Issue ⑦ empty-cell 实现选 `torch.where` 而非 `clamp_min`

**Choice**: `n_i = weights.sum(dim=0); weighted = (weights.T @ X); safe_n = n_i.clamp_min(1.0); mean_n = weighted / safe_n.unsqueeze(-1); mean = torch.where(n_i.unsqueeze(-1) > 0, mean_n, centroids)`。

**Rationale**: spec 明确 "no `.clamp_min(ε)` denominator"。`safe_n = n_i.clamp_min(1.0)` 仅用于除法（防止 n_i=0 触发 0/0 NaN 传播到 mean_n），但 `mean` 由 `torch.where` 选择：当 `n_i > 0` 取 `mean_n`，否则取 `centroids`。`centroids` 是上一步的输入，与 fallback invariant 完全一致。

**Alternatives considered**:
- (a) 仅用 `safe_n.clamp_min(1.0)` 除法 + `if n_i == 0: mean = centroids` 分支：分支不易向量化，批处理时效率低
- (b) 完全删除 `clamp_min(1.0)`：当 `n_i = 0` 时 `0/0 = NaN` 传播到下游 `c_i`（违反 invariant 2）
- (c) 用 `index_select` 选择性赋值：复杂度高，无收益

### Decision 2 — Issue ⑥ EMA `F.normalize` 在 `torch.where` 内（near-zero fallback 之前）

**Choice**: `candidate = alpha * centroids + (1.0 - alpha) * mean; norm = candidate.norm(dim=-1, keepdim=True); use_old = (norm < 1e-9); out = torch.where(use_old, centroids, F.normalize(candidate, dim=-1))`。

**Rationale**: 同时实现 Issues ⑥（Spherical Re-Projection）和 Issue ⑧ 派生（near-zero candidate fallback）。
- 当 `‖candidate‖₂ ≥ 1e-9`：正常 `F.normalize(candidate, dim=-1)` ⇒ `‖out‖₂ = 1.0`
- 当 `‖candidate‖₂ < 1e-9`（退化各向同性坍缩）：`out = centroids` ⇒ `‖out‖₂ = 1.0`（保持原 c_i 单位球） + 无 NaN

**Alternatives considered**:
- (a) 仅 `F.normalize(candidate)`，对 `‖candidate‖ < 1e-9` 会产生 0/0 = NaN 传播
- (b) 用 `candidate / norm.clamp_min(1e-12)`：spec 明确禁止 `.clamp_min(ε)` 用作分母（即便此处非 empty-cell）

### Decision 3 — Issue ⑧ 三个 invariant test scenarios 直接对齐 spec Scenario L341-351

**Choice**: 测试名严格匹配 spec：`test_empty_cell_preserves_centroid` / `test_spherical_norm_is_strictly_one` / `test_near_zero_candidate_fallback`（skeleton spec "Centroid Driver Invariant Test Scenarios" Requirement L337-351）。

**Rationale**: spec 文本显式列出这 3 个测试名作为 invariant verification contract。test 命名必须字面对齐以便后续 `grep test_empty_cell_preserves_centroid openspec/specs/decompmoe-skeleton/spec.md` 验证 spec ↔ test 一一对应。

**Alternatives considered**:
- (a) 改名（如 `test_empty_cell_fallback`）：破坏 spec 合同锚点
- (b) 合并到 1 个 test：spec 是 3 个独立 Scenario，独立 test 更清晰

### Decision 4 — `test_phase_090_ema` 等 EMA expected 值同步到归一化形式

**Choice**: `expected = F.normalize(0.9 * centroids + 0.1 * mean, dim=-1)`（替换当前 `0.9 * centroids + 0.1 * mean`）。

**Rationale**: 当前测试固化了「EMA 输出未归一化」的违规行为。修 Issue ⑥ 时必须同步，否则测试与实现都违反 spec 但仍互绿（spec drift 的隐蔽形态）。

**Alternatives considered**:
- (a) 删 `test_phase_090_ema`：失去 EMA 公式验证，违反 SS-9 的核心数学约束
- (b) 仅改实现不改测试：测试继续失败（绿测无法达成）

### Decision 5 — checkpoint commit 落在 `dev`，遵循 CLAUDE.md §4 线性提交

**Choice**: 13 个 checkpoint commit 全部在 `dev` 上 fast-forward 线性提交，**禁止** merge commit 或 feature branch。

**Rationale**: CLAUDE.md §4 硬约束——`dev` 永远线性，绝对无 merge commit。archive 后由用户决定是否 `dev → main`（关键存档点）+ `dev → release`（必带 tag）。

## Risks / Trade-offs

**[Risk 1] `test_extraction_phase.py` 中 `test_phase_4_projected_sgd` 可能因 Decision 2 的 EMA 改动而 fail**：当前实现对 Phase 4 直接 `centroids / norm.clamp_min(eps)`，与 Decision 2 无关但需要重新审视。**Mitigation**: Phase 4 不在 Issue ⑥ 范围；如 fail 则单独修复并在 SS-9 范围内处理。

**[Risk 2] `test_phase_transition_swaps_rule` 检查 EMA 输出与 `0.90/0.99` 系数差异**：Decision 4 同步 expected 后仍需保留 `α != β` 的差异验证。**Mitigation**: 该测试只断言 `0.90*c + 0.10·mean` vs `0.99*c + 0.01·mean` 的差异，差异在归一化前后都存在；归一化只改变幅度不改变方向。

**[Risk 3] `F.normalize` 在 `dim=-1` 对 `dim=0` 单向量（如 `(d_c,)`）也能工作**：候选实现必须确保 `centroids` 是 2D `(... × d_c)`。**Mitigation**: spec 明确 `centroids ∈ R^{N_e × d_c}`，调用方保证 2D；test 同样构造 2D 张量。

**[Risk 4] 现有 `test_phase_seeding_no_grad` 检查 `out.requires_grad == False`**：Decision 2 的 `F.normalize(candidate)` 不引入 `requires_grad`，但 `torch.where` 在 autograd 下可能引入隐式 branch。**Mitigation**: `F.normalize` 链式可微，`torch.where` 选择分支但仍可微；如 SEEDING fail，需在 mask=None 路径加 `return centroids.detach()` 不变。

## Migration Plan

本 change 是 code-only，无运行时迁移：

1. **apply 阶段（spec archive 后）**：`openspec instructions apply --change fix-spec-doc-oversights-apply --json` 拿到 task list
2. **代码实现**：按 tasks.md §1-3 的 13 个 checkbox 顺序执行 RED → GREEN → Refactor 循环
3. **archive**：`openspec archive fix-spec-doc-oversights-apply` 把 delta 合并到主 spec（如有，本 change 无 spec delta，仅归档 change 目录）
4. **rollback**：git revert 本 change 的 commit chain

## Open Questions

无。3 项 Issue hand-off 决策已落地到 spec 文本（archived `fix-spec-doc-oversights/proposal.md` Downstream Hand-off 段）与本 design.md Decisions。