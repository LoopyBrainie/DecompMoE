## Why

`fix-openspec-doc-bugs` 已 archived（commit `41ac06b`，2026-08-21），spec delta 涵盖 13 项修订（编号 A-1 ~ A-13），分两个 capability：

- 主 spec `wayfinder/spec.md`：8 处 MODIFIED（Req 6/7/11/12/13/14/19/20）+ 4 处 ADDED（Req 22 Empty-Cell Invariant / Req 23 Spherical Re-Projection / Req 24 Beta Parameterization Space vs Operational Domain / Req 25 CentroidDriver Dual-Channel Architecture Contract）
- skeleton spec `decompmoe-skeleton/spec.md`：8 处 MODIFIED + 1 处 ADDED

`fix-openspec-doc-bugs/tasks.md` §6 hand-off 把全部 13 项 code-level 修复（含 `extraction.py` / `loss.py` / `metrics.py` / `safeguards.py` / `schedule.py` / `distance.py` / `gating.py` / `experts.py` 与对应测试）移交给下游 `fix-openspec-doc-bugs-apply`，**该 apply change 至今未创建、未执行**。本 change 严格遵循 CLAUDE.md §3 SDD 流程：每条 spec 修订 = 1 个 RED → GREEN → Refactor 循环，每条 pytest 必须含数学原理约束（CLAUDE.md §6 硬约束）。

本 change 按 plan `ultracode-opsx-apply-reflective-hamster.md` Phase C 的 20 个 sub-spec 拆分执行（SS-1 ~ SS-20），其中 SS-7/SS-13/SS-14/SS-15/SS-16 5 个 sub-spec 涉及 `src/` 代码修改，其余 15 个 sub-spec 复用现有 test 覆盖。

## What Changes

按 plan 的 critical files 表修改 6 个 src 模块（按 sub-spec 映射）：

### SS-7：Voronoi canonical + measurement（skeleton spec Req "Voronoi Self-Consistency Threshold" + wayfinder Req 11）

**修改 `src/decompmoe/sphere.py`**：
- 删除 `voronoi_angle(d_c) = degrees(atan(π/√d_c))`（旧公式，违反 spec）
- 新增 `canonical_voronoi_angle(num_experts, signature_dim) -> float`：解正则化不完全 Beta 函数 `½·I_{sin²θ}((d_c−1)/2, 1/2) = 1/N_e`，MVP `(16, 16)` → 0.9076 rad（52°），`(64, 16)` → 0.4494 rad（25.45°）
- 新增 `voronoi_angle(centroids: Tensor) -> float`：测量层（offline only），从质心张量估计
- 实现依赖：`scipy.special.betainc`（stdlib，无需额外依赖）

**修改 `tests/test_sphere.py`**：
- `test_voronoi_angle_self_consistency` 改测 `canonical_voronoi_angle(16,16) ≈ 0.9076 rad`
- 新增 `test_voronoi_N_e_dependence`：`(64,16)` ≈ 0.4494 rad
- 新增 `test_voronoi_self_consistency_against_1_e_boundary`：`θ_Voronoi(16,16) > θ_{1/e}(β=16) ≈ 20.36°`

### SS-13：L_total + λ(t) + L_lb 双因子（skeleton spec Req "Loss Composition With Staged Lambda" + wayfinder Req 12）

**修改 `src/decompmoe/loss.py`**：
- `L_total` 签名扩展为 `(task_logits, targets, f_per_expert, p_per_expert, c_centroids, phase, step, *, cfg)`（新增 `p_per_expert` 与 `cfg` 关键字参数）
- 重写 `L_lb = N_e · Σ_i f_i.detach() · P_i`，其中 `P_i = (1/T) · Σ_t p_i(C_t)`
- 保留 `compute_L_sep` 的 Frobenius 形式

**修改 `tests/test_loss.py`**：
- 新增 `test_lb_gradient_flows_through_P_i`：验证 `∂L_lb/∂P_i ≠ 0` AND `∂L_lb/∂f_i ≡ 0`（用 `torch.autograd.grad` + `pytest.approx`）
- 现有 `test_lb_uses_detached_fractions`（AST 检查）保留为补充验证

### SS-14：Five Safeguard Helpers（skeleton spec Req "Five Numerical Safeguard Helpers" + wayfinder Req 13）

**修改 `src/decompmoe/safeguards.py`**：
- `DEAD_EXPERT_FRACTION: Final[float] = 1.0 / 128.0` → `1.0 / (2.0 * N_e)` 参数化（默认 N_e 来自 cfg 或 caller）
- `should_resurrect` 签名改为 `(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/(2·N_e), consec=200) -> set[int]`，与 spec 对齐

**修改 `tests/test_safeguards.py`**：
- `test_resurrection_trigger_window`：用 `threshold=1/32`（MVP N_e=16 评估）
- `test_resurrection_N_e_parameterized`：验证 N_e=64 下 threshold 自动变 1/128

### SS-15：Five-Phase Schedule（skeleton spec Req "Five-Phase Schedule State Machine" + wayfinder Req 14）

**修改 `src/decompmoe/schedule.py`**：
- `phase_step_frozen_names(2)`：从 `{W_g, W_u, W_d}` 改为 `{c_i, beta_i}`（gradient channel frozen；W_K/W_V/b 在 phase 2 解冻）
- 新增 `phase_step_frozen_names(3)`：返回 `{c_i}`（gradient channel frozen；beta_i 在 phase 3 解冻）

**修改 `tests/test_schedule.py`**：
- `test_phase2_freeze_experts`：期望 `{c_i, beta_i}`（非旧 `{W_g, W_u, W_d}`）
- 新增 `test_phase3_freeze`：期望 `{c_i}`

### SS-16：Eight Metrics + classification（含 OFFLINE 实现）（skeleton spec Req "Eight Metrics And Classification" + wayfinder Req 20）

**修改 `src/decompmoe/metrics.py`**：
- `S_load(f_per_expert) = N_e · max_i f_i`（替换 `‖f − 1/N‖₂` 旧公式）
- `UR` 改为带 100-step sliding buffer（新增 `metrics.URBuffer` 类或函数）；闭式 `(1/N_e) · Σ_i I[f_i > 0]`
- 实现 OFFLINE tier 闭式：
  - `SP_i(c_centroids, assignments, expert_idx)`：若 `‖T_i‖₁ = 0` 返回 `NaN`（死专家 undefined）
  - `D_chord(c_centroids)`：`(2/(N_e(N_e-1))) · Σ_{i<j} √(2(1 − c_iᵀ c_j))`
  - `MCI(c_centroids, assignments)`：`(1/d_c) · Σ_j 1/λ̃_j²`，`λ̃_j = λ_j/Σ_r λ_r`
  - `CG(c_centroids, params)`：stub 返回 `‖∇_{W^{K,V,b}} L_total‖₂`（debug only）

**修改 `tests/test_metrics.py`**：
- `test_S_load_closed_form`：`f = [0.5, 0.5]` → `S_load = 16·0.5 = 8.0`
- 新增 `test_SP_dead_expert_undefined`：构造空 expert，断言 `SP = NaN`（spec 要求死专家 undefined）
- 新增 `test_D_chord_closed_form`：3 个 unit 矢量的 chord length 闭式
- 新增 `test_UR_100_step_window`（如实现为 sliding buffer）

### SS-9 协调：CentroidDriver invariants（与 fix-spec-doc-oversights-apply 共享）

CentroidDriver step 改写已在 `fix-spec-doc-oversights-apply` 完成（Issues ⑥⑦⑧）。本 change 仅引用其产物，不重复实现。

## Capabilities

### New Capabilities

无（code-only change，不引入新 spec 边界；spec contract 由 archived `fix-openspec-doc-bugs` 锁定）。

### Modified Capabilities

无（本 change 不修改任何 Requirement；spec 一致性由 archived change 维护）。

## Impact

- **Spec 层**：本 change **不动** `openspec/specs/wayfinder/spec.md` 或 `openspec/specs/decompmoe-skeleton/spec.md`。spec contract 由 archived `fix-openspec-doc-bugs` 锁定（commit `41ac06b`）。
- **代码层**（5 个 src 模块）：
  - `src/decompmoe/sphere.py`（SS-7 Voronoi canonical + measurement）
  - `src/decompmoe/loss.py`（SS-13 L_total 签名 + L_lb 双因子）
  - `src/decompmoe/safeguards.py`（SS-14 DEAD_EXPERT_FRACTION 参数化 + should_resurrect 签名）
  - `src/decompmoe/schedule.py`（SS-15 phase_step_frozen_names(2/3)）
  - `src/decompmoe/metrics.py`（SS-16 S_load/UR 闭式 + OFFLINE metrics）
- **测试层**（4 个 test 文件）：test_sphere.py / test_loss.py / test_safeguards.py / test_schedule.py / test_metrics.py 各自更新
- **Ticket 层**：CLAUDE.md §8 2026-08-21 裁决 wayfinder 不再是必改制品
- **依赖 change**：`openspec/changes/fix-spec-doc-oversights-apply/`（处理 Issues ⑥⑦⑧）

## Out of Scope（明确不动）

- 不执行训练、不跑 baseline、不读实验数据（CLAUDE.md §6）
- 不修改 `src/decompmoe/extraction.py` 的 `CentroidDriver.step`（属于 `fix-spec-doc-oversights-apply` Issues ⑥⑦⑧ 范围）
- 不修改 `src/decompmoe/contracts.py` / `__init__.py` / `experts.py` / `distance.py` / `gating.py` / `beta.py` / `config.py` / `viz.py`（已与 archived spec 对齐）
- 不重写 wayfinder ticket（CLAUDE.md §8 2026-08-21 裁决）
- 不引入 scipy 等新依赖——`scipy.special.betainc` 已在 stdlib 内（无需 pyproject.toml 改动）