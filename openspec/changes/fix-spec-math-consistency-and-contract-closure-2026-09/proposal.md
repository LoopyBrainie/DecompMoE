## Why

2026-09-08 第二轮 post-archive 独立复核（按 CLAUDE.md §3 "Post-archive 独立复核" 强制条款）发现 6 处 spec/code 漂移：

- **2 项 CRITICAL** —— spec 与代码在数学层面互斥或功能缺失。
- **3 项 HIGH** —— spec 与代码在契约层错位（API 签名、模块归属、类型守门），违反 CLAUDE.md §6 第 8 条的"spec 算式必须直接对账生产代码"原则。
- **1 项 MEDIUM** —— 注释噪（5 处 `# noqa: dead-defensive`），不构成功能问题但增加 diff 噪声（CLAUDE.md §3 "Surgical Changes"）。

清单由 `code-review max` 严格事实核查后形成，3 处锚点已修正（原 finding 引用 wayfinder:321 错误，实为 skeleton L307 Requirement "Eight Metrics And Classification"；原 finding 误以为 A-HI-4 锚点在 skeleton，实为 wayfinder L573；A-CR-2 spec 内 L409 提供 `clamp_min(eps) does NOT satisfy this invariant` 的 Phase-4 先例，可作为新公式 `z / max(‖z‖, ε)` 的 spec 内部背书）。

**D1 决策保留**：本 change 维持 `design.md` Decision 1 "算法常量（β_min / β_max）位于 `decompmoe/beta.py` 模块级，MVPConfig 仅承载几何常量"的现有架构。A-HI-1 / A-HI-2 不引入 cfg 形参与 MVPConfig β 字段，而是**修改 spec** 与代码当前架构对齐。这避免了 §6 第 8 条与 design.md 的设计哲学冲突。

## What Changes

### decompmoe-skeleton spec delta（5 项）

1. **A-CR-1** (Phase-4 SGD 补齐) —— 当前 `src/decompmoe/extraction.py:144-154` `CentroidDriver.step` 在 `Phase.PROJECTED_SGD` 分支仅做 L2 收缩，**未实现** spec L153 规定的 `c_i ← (c_i − η · ∇_{c_i} L_routing) / ‖·‖₂` 闭式 SGD 步。spec delta 新增 (a) `step` 签名扩展为 `(centroids, X, mask, *, grad=None, eta=1e-2)`；(b) `Phase-4 SGD-1-step` Scenario 验算 `c_i^(t+1) = (c_i − η·g)/‖·‖`，`pytest.approx(..., abs=1e-7)`；(c) 确认 spec L409 Phase-4 near-zero candidate fallback 已明文要求 `torch.where(use_old, prev, normalize(...))` guard pattern——当前代码 P4 分支已实现 fallback 但 **SGD 步尚未实现**，spec delta 把 L409 的"INVARIANT #4 必须 apply"扩展到完整 P4 路径。
2. **A-CR-2** (球面归一化 ε 矛盾修复) —— spec L96 公式 `z / (‖z‖₂ + ε)` 与 L99 "pow(2).sum(-1) == 1.0 within 1e-5" + L104 "equals z / eps" 数学上互斥：`z = 0` 时输出为 `0` 而非 `z/eps`；`‖z‖₂ = 2.0` 时输出范数为 `2.0 / (2.0 + ε) ≈ 1 − ε/2`，不严格等于 1.0。spec delta 改 L96 公式为 `z / max(‖z‖₂, ε)`（保证 `‖out‖ ∈ [0, 1]` 单调），L99 Scenario 改弱等式 `‖out‖ ∈ [1−2ε, 1]` 当 `‖z‖ ≥ 1−ε`，**删除** L102-104 "Zero-tensor safe: equals z / eps" Scenario。**spec 内部先例**：L409 已明文否定 `centroids / ‖centroids‖.clamp_min(eps)` 在 Phase-4 不满足不变量，与本修订方向一致。
3. **A-HI-1** (D1 保留 → 删 spec cfg 要求) —— spec L434 要求 `beta_effective(gamma, phase, step, *, cfg) -> Tensor`，但 `design.md` D1 决策下 `cfg` 为冗余形参（β_min/β_max 为模块级 `Final[float]`）。代码 `src/decompmoe/schedule.py:129` 三参签名合规（注释 L143-144 显式声明 D1 一致性）。spec delta 删除 `*, cfg` keyword-only 要求，明文承认模块级常量归属——为 D1 决策保留 spec 单源真相。
4. **A-HI-2** (D1 保留 → 删 spec β 字段要求) —— spec L22 要求 MVPConfig 含 `β_min` / `β_max` 字段，但 `src/decompmoe/config.py:41-58` 无此两字段（注释 L37-38 显式声明 "Algorithmic constants live with their usage site"）。spec delta 删除 MVPConfig `β_min == 0.1, β_max == 32` 字段要求，明文承认 `decompmoe/beta.py::BETA_MIN / BETA_MAX` 为唯一权威源。
5. **A-HI-3** (CG 类型守门) —— `src/decompmoe/metrics.py:158-171` `CG(grad)` 仅守门 `grad.numel() == 0`，无 `isinstance(grad, Tensor) and grad.dtype.is_floating_point` 校验。spec L317 + L361-367（Requirement "Eight Metrics And Classification" 内 CG 闭式与 Scenarios）未规定 dtype 守门。spec delta 在 CG Scenarios 之后新增 Scenario `CG(grad) raises TypeError on non-floating-point input`，对账代码即将加的类型守门。

### wayfinder spec delta（1 项）

6. **A-HI-4** (resurrection 单事件契约闭合) —— `openspec/specs/wayfinder/spec.md:573-583` Requirement "Resurrection Perturbation Per-Expert Contract" 已规定：(i) API 签名 `resurrection_perturb_distribution(target_idx, *, eps_std=0.05)` 保留 `target_idx`（**当前代码 `src/decompmoe/safeguards.py:107` 形参已对齐，不违规**——L123 `del target_idx` 仅丢弃值而非删形参）；(ii) `β_i ← 0.85·β_{j*}` 与 `β_{j*} ← 0.85·β_{j*}` "MUST execute as part of the same resurrection event"。**代码当前实现把 (ii) 拆为 `apply_resurrection_beta_decay` 独立函数**（safeguards.py:139），未保证单事件原子性。spec delta 新增 Scenario `same-event beta decay` 验证 perturb + β 衰减在同一次调用栈中完成；代码侧加 thin wrapper `resurrect_expert(i, j_star, β_per_expert, cfg)` 串起两步，**不删 target_idx**。

### src/ 边界修改（4 文件 surgical Edit）

- `src/decompmoe/extraction.py:96-156` —— `CentroidDriver.step` P4 分支补 SGD 步（保留现有 near-zero fallback 与 re-projection 不变量）
- `src/decompmoe/sphere.py:37-46` —— `spherical_l2_normalize` 公式改 `z / max(‖z‖₂, ε)`
- `src/decompmoe/metrics.py:158-171` —— `CG` 加 `isinstance(grad, Tensor) and grad.dtype.is_floating_point` 守门（不动现有 `numel == 0` 守门）
- `src/decompmoe/metrics.py:110, 148, 152` —— 删 `# noqa: dead-defensive` 注释噪（3 处）
- `src/decompmoe/safeguards.py:105-152` —— 加 `resurrect_expert` wrapper；`target_idx` 形参保留不删
- `src/decompmoe/safeguards.py:160, 171` —— 删 `# noqa: dead-defensive` 注释噪（2 处）

### tests/ 边界修改（4 文件）

- `tests/test_extraction.py` —— 新增 `test_phase_4_sgd_1_step_closed_form`（闭式 `c_i^(t+1) = (c_i − η·g)/‖·‖`，`pytest.approx(..., abs=1e-7)`）
- `tests/test_sphere.py` —— 既有 `test_unit_sphere_invar` / `test_near_zero_numerically_safe` 边界用例重写为新公式下的 `max(‖z‖, ε)` 形态；新增 `test_sphere_norm_monotone_in_z_norm`（`‖z‖₂ → ‖out‖₂` 单调性守门）
- `tests/test_metrics.py` —— 新增 `test_cg_raises_type_error_on_int_tensor` + `test_cg_raises_type_error_on_bool_tensor`
- `tests/test_safeguards.py` —— 新增 `test_resurrect_expert_single_event_contract`（验算 perturb + β 同事件；target_idx 形参保留）
- **不修改**：既有 141 tests 全部保持现状；新测试仅针对新增/修订的 spec Scenarios

### nothing else

不动 wayfinder tickets（CLAUDE.md §6 第 7 条 + §8 tickets 已 reference-only）；不动 MVPConfig 已有的 `beta_initial` 字段（D1 保留意味着 β_min/β_max 不进 MVPConfig，但 β_initial 这个具体值字段保留）；不动 contracts.py；不动 gating / loss / experts / viz 模块。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无。Spec delta 经 §7 修正后转为 MODIFIED Requirements —— 见 `specs/decompmoe-skeleton/spec.md` 与 `specs/wayfinder/spec.md`，append 至既有 capability。）

### Added / Modified Requirements to Existing Capabilities

- `decompmoe-skeleton` (5 处 spec delta)：
  - **MODIFIED** Requirement "Centroid Four-Phase Lifecycle Driver"（skeleton L145-155）—— P4 步公式细化为 `c_i^(t+1) = (c_i − η · ∇_{c_i} L_routing) / ‖·‖₂`；新增 `step(centroids, X, mask, *, grad=None, eta=1e-2)` 签名；新增 Scenario `Phase-4 SGD-1-step closed form` 验算闭式常量
  - **MODIFIED** Requirement "Spherical L2 Normalization"（skeleton L94-104）—— L96 公式改 `z / max(‖z‖₂, ε)`；L99 Scenario 改弱等式 `‖out‖ ∈ [1−2ε, 1]`；删除 L102-104 "Zero-tensor safe" Scenario
  - **MODIFIED** Requirement "Beta Parameterization Operational Domain"（skeleton L432-446）—— 删除 `*, cfg` keyword-only 要求；保留模块级常量归属说明
  - **MODIFIED** Requirement "Frozen MVP Hyperparameter Set"（skeleton L20-26）—— 删除 MVPConfig `β_min == 0.1, β_max == 32` 字段要求；明文承认 `decompmoe/beta.py` 为唯一权威源
  - **MODIFIED** Requirement "Eight Metrics And Classification"（skeleton L307-367）—— 在 CG Scenarios（L361-367）后新增 Scenario `CG(grad) raises TypeError on non-floating-point input`
- `wayfinder` (1 处 spec delta)：
  - **MODIFIED** Requirement "Resurrection Perturbation Per-Expert Contract"（wayfinder L573-583）—— 在现有 Scenario `perturbation output shape matches a single expert slot`（L581-583）后新增 Scenario `same-event beta decay` 验证 perturb + β 同事件原子性

## Impact

- **Affected code**（surgical edits per CLAUDE.md §3）：
  - `src/decompmoe/extraction.py:96-156` —— `CentroidDriver.step` P4 分支补 SGD 步
  - `src/decompmoe/sphere.py:37-46` —— `spherical_l2_normalize` 公式改 `z / max(‖z‖₂, ε)`
  - `src/decompmoe/metrics.py:158-171` —— `CG` 加 dtype 守门
  - `src/decompmoe/metrics.py:110, 148, 152` —— 删 `# noqa: dead-defensive` 注释噪（3 处）
  - `src/decompmoe/safeguards.py:105-152` —— 加 `resurrect_expert` wrapper；`target_idx` 形参保留不删
  - `src/decompmoe/safeguards.py:160, 171` —— 删 `# noqa: dead-defensive` 注释噪（2 处）

- **Affected tests**（4 文件 expected）：
  - `tests/test_extraction.py` —— 新增 1 个 test（Phase-4 SGD 1-step 闭式）
  - `tests/test_sphere.py` —— 边界用例重写 + 新增 1 个 test
  - `tests/test_metrics.py` —— 新增 2 个 test（CG TypeError）
  - `tests/test_safeguards.py` —— 新增 1 个 test（resurrect single-event）

- **Affected APIs / dependencies**：
  - `CentroidDriver.step` 签名扩为 `(centroids, X, mask, *, grad=None, eta=1e-2)` —— 新增 2 个 keyword-only 形参，向后兼容（默认 `grad=None` 走原 P4 收缩分支）
  - `CG(grad)` 在非 Tensor 输入或非浮点 dtype 下抛 `TypeError` —— 这是 spec delta 强化的契约，不是新行为
  - 新增 `resurrect_expert(i, j_star, β_per_expert, cfg)` wrapper；不删除现有 `resurrection_perturb_distribution` / `apply_resurrection_beta_decay`
  - 无新依赖

- **Affected systems**：无（推理引擎实现代码已 out-of-scope per CLAUDE.md §7）

- **Risk**：
  - **A-CR-1 P4 SGD 步引入**：当前 P4 仅做 L2 收缩，新加 SGD 步会改变 P4 阶段训练动力学。Mitigation：默认 `eta=1e-2` 是保守值；保留现有 near-zero fallback 不变量；测试用闭式常量对账（`pytest.approx(..., abs=1e-7)`）保证数值正确
  - **A-CR-2 sphere 公式改动**：`+ eps` 改 `max(‖z‖, ε)` 影响 `extract_C` Step 2 + Step 4 的梯度流。Mitigation：现有 `test_full_differentiability`（test_extraction.py:142）守护梯度路径；新增 `test_sphere_norm_monotone_in_z_norm` 守护单调性
  - **A-HI-3 CG dtype 守门**：现有 caller 全部传 Tensor（`safeguards.l2_norm` L54 + `clip_global_grad_norm_`），无回归风险
  - **A-HI-4 wrapper 函数**：纯新增，无回归风险；target_idx 形参保留以满足 spec L577 API 签名
  - **D1 保留决策**：spec 修订而非代码修订，与既有 design.md D1 一致；不引入 cfg / β 字段耦合
  - **B-ME-1 注释噪清理**：纯注释删除，不动 catch 行为；现有 141 tests 全绿即证明无回归

- **Source**：清单 2 P2 审计（2026-09-08 第二轮 review max），每项独立证据链：
  - A-CR-1: `src/decompmoe/extraction.py:144-154`（无 SGD 步），spec L153（要求 `c_i − η·∇`）；双向对照
  - A-CR-2: spec L96 / L99 / L102-104 数学矛盾；`src/decompmoe/sphere.py:37-46` 闭式 `+ eps`；spec L409 先例
  - A-HI-1: spec L434 `*, cfg` 要求；`src/decompmoe/schedule.py:129` 三参签名；`config.py:37-38` D1 注释
  - A-HI-2: spec L22 β_min/β_max 字段要求；`config.py:41-58` 字段集合无 β_min/β_max；`beta.py:30-31` 模块级权威源
  - A-HI-3: `src/decompmoe/metrics.py:158-171` 无 dtype 守门；spec L317 + L361-367 CG Scenarios 集合
  - A-HI-4: spec L573-583（含 API 签名 + 单事件要求）；`safeguards.py:105-152` 两函数拆分；wayfinder `design.md Decision 4`
  - B-ME-1: `grep -r "# noqa: dead-defensive" src/` 5 处命中（schedule.py:160,171；metrics.py:110,148,152）