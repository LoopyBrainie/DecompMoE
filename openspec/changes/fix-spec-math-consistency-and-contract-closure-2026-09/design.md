## Context

2026-09-08 第二轮 `code-review max` 审计（清单 2 P2）发现 6 处 spec/code 漂移：2 CRITICAL（数学矛盾 + 算法缺失）+ 3 HIGH（契约错位）+ 1 MEDIUM（注释噪）。其中：

- **A-HI-1 / A-HI-2 同源于 design.md D1 决策**——D1 决定"算法常量（β_min / β_max）位于 `decompmoe/beta.py` 模块级，MVPConfig 仅承载几何常量"，而 spec 当前在 L434 要求 `*, cfg` 形参、L22 要求 MVPConfig `β_min/β_max` 字段，与 D1 冲突。代码已按 D1 实现（schedule.py:143-144 注释 + config.py:37-38 注释明文声明 D1 一致性）。这意味着本 change 必须在"动 spec 让它对齐 D1" vs "动代码让 spec 成立"之间二择一。
- **A-CR-1 / A-CR-2 是真矛盾**——CRITICAL 等级，必须 fix，且 fix 方向必须经过独立数值复核（CLAUDE.md §3 "Post-archive 独立复核"强制条款）。
- **A-HI-3 / A-HI-4 / B-ME-1 是契约层**——不涉及数学矛盾或设计哲学冲突，纯 spec/code 对齐。

**D1 决策保留**：本 change 明确维持 `design.md` Decision 1。A-HI-1 / A-HI-2 的修复方向是**修改 spec**（删除冗余 `cfg` / `β_min/β_max` 字段要求），而不是修改代码（避免引入 cfg 形参与 MVPConfig β 字段耦合）。理由：(a) `decompmoe/beta.py` 模块级常量是 `Final[float]`，引入 cfg 会破坏 `Final` 不变量（cfg 默认值变更需传播到 Final 常量）；(b) MVPConfig 加 β 字段会与 `decompmoe/beta.py` 双源真相，违反 spec 单源原则；(c) D1 已有先例——同 change 内的 A-HI-3 也是 spec 加 Scenario 锁契约，而非改代码加守门。

## Goals / Non-Goals

**Goals:**
- 关闭 6 项 review max finding，每项有独立的 spec/code 对账点（CLAUDE.md §6 第 8 条"sentinel closed-form constant must directly verify"原则）
- 维持 design.md D1 决策，不引入 cfg / MVPConfig β 字段
- spec delta 单源真相：A-CR-2 用 `z / max(‖z‖, ε)` 替代 `z / (‖z‖ + ε)`；A-CR-1 用闭式 `c_i − η · ∇_{c_i} L_routing` 对账现有 L153 spec 文字
- 6 项中 5 项走 spec delta + 配套代码修改（A-CR-1 / A-CR-2 / A-HI-3 / A-HI-4 + B-ME-1 注释噪清理）；A-HI-1 / A-HI-2 仅 spec 修订（删除冗余要求）
- tests/ 4 文件新增 5 个 test，**不修改**既有 141 tests（CLAUDE.md §3 surgical 原则）
- 现有 141 tests 全绿 + 5 个新 test 全绿

**Non-Goals:**
- 不动 `decompmoe/beta.py` 模块级常量（`BETA_MIN` / `BETA_MAX` / `MAX_GRAD_PER_C` 等保持 Final 不变）
- 不动 `MVPConfig` 已有字段（`d_model` / `N_e` / `k` / `d_ffn` / `L` / `d_ffn_dense` / `d_c` / `H_kv` / `d_k` / `beta_initial` / `vocab_size` 全部保留；仅 spec L22 的 `β_min / β_max` 字段要求被删除）
- 不动 `CentroidDriver` Phase 0/1/2/3 分支（仅 P4 补 SGD 步）
- 不动 `wayfinder/tickets/` 任何文件（CLAUDE.md §6 第 7 + §8 tickets 已 reference-only）
- 不动 `contracts.py` / `gating.py` / `loss.py` / `experts.py` / `viz.py`
- 不动 `extract_C` 的 Step 1 / Step 3 路径（仅 Step 2 / Step 4 用到的 `spherical_l2_normalize` 公式改）
- 不动 `loss.py` 的 `L_lb` / `L_sep` 闭式（与本次 finding 无关）

## Decisions

### Decision 1: D1 保留 —— A-HI-1 / A-HI-2 通过修改 spec 而非代码修复

**Choice**: A-HI-1 / A-HI-2 的 spec delta 是**删除** spec 中冗余的 `cfg` keyword-only 要求（spec L434）和 MVPConfig `β_min / β_max` 字段要求（spec L22），而不是修改代码加 cfg 形参与 MVPConfig β 字段。

**Rationale**: D1 决策（`design.md` Decision 1, "Algorithmic constants live with their usage site — see design.md D1"）已明确把算法常量集中到使用点（`decompmoe/beta.py`），MVPConfig 仅承载几何常量（model shape）。代码当前实现完全符合 D1：
- `src/decompmoe/schedule.py:129-145` `beta_effective(gamma_p, phase, step)` 三参签名，注释 L143-144 显式声明 "Signature is exactly 3 args: no dead `cfg` param"
- `src/decompmoe/config.py:37-38` MVPConfig docstring 显式声明 "Algorithmic constants (β_min, β_max, α, λ_max, etc.) live with their usage site"
- `src/decompmoe/beta.py:30-31` `BETA_MIN: Final[float] = 0.1; BETA_MAX: Final[float] = 32.0` 为唯一权威源

如果走"修改代码"路径，会引入：(a) `cfg` keyword-only 形参 + `Final[float]` 引用 cfg 的 lazy 解析（破坏 Final 不变量）；(b) MVPConfig 加 β 字段会与 `decompmoe/beta.py` 形成双源真相（哪个是规范源？）；(c) 现有 4 个 caller（tests + schedule.py）需要更新签名。**修改 spec 路径无上述代价**——仅删除冗余文字，明文承认模块级常量为唯一权威源。

**Alternatives considered**:
- (a) 修改代码加 cfg 形参 + MVPConfig β 字段 —— 拒绝：破坏 D1，引入双源真相与 Final 解析复杂度
- (b) 同时修改 spec 与代码（双向对齐）—— 拒绝：scope 膨胀，违反 CLAUDE.md §3 surgical 原则
- (c) 仅删除 spec 文字不改代码（保持现状）—— 选择：spec/code 同时对齐 D1，最小化代码修改

### Decision 2: A-CR-1 修复方向 —— 补闭式 SGD 步而非重写 P4 路径

**Choice**: `CentroidDriver.step` P4 分支从"仅 L2 收缩"扩展为"先 `c_i − η · ∇_{c_i} L_routing`，再 L2 收缩"，保留现有 near-zero fallback 与 re-projection 不变量。

**Rationale**: spec L153 已明文规定 P4 闭式 `c_i ← (c_i − η · ∇_{c_i} L_routing) / ‖·‖₂`，代码当前实现 (extraction.py:144-154) 仅做 `centroids / ‖centroids‖₂`，**未实现 SGD 步**——这是功能缺失而非设计分歧。修复方向严格遵循 spec 闭式，不引入额外自由度（如自定义 SGD 优化器、动量项等）。**签名扩展为 `(centroids, X, mask, *, grad=None, eta=1e-2)`**：
- `grad=None` 时 P4 退化为原 L2 收缩（向后兼容现有 caller）
- `grad` 提供时执行完整 `c_i − η · grad` 后 L2 收缩
- `eta=1e-2` 默认值保守（spec L153 未规定具体值，参考 wayfinder schedule 节奏）

**Alternatives considered**:
- (a) 重写 P4 路径引入 AdamW 风格动量 —— 拒绝：超出 spec 闭式范围，scope 膨胀
- (b) 加新方法 `step_with_grad` 而非扩展现有签名 —— 拒绝：违反 spec L147 `step(centroids, X, mask) -> Tensor` 单一方法契约
- (c) 仅文档化缺失（不改代码）—— 拒绝：review max 标为 CRITICAL，必须 fix 而非 acknowledge

### Decision 3: A-CR-2 修复方向 —— `z / max(‖z‖, ε)` 替代 `z / (‖z‖ + ε)`

**Choice**: spec L96 公式从 `z / (‖z‖₂ + ε)` 改 `z / max(‖z‖₂, ε)`；L99 Scenario 改弱等式 `‖out‖ ∈ [1−2ε, 1]` 当 `‖z‖ ≥ 1−ε`；删除 L102-104 "Zero-tensor safe: equals z / eps" Scenario。

**Rationale**: 三个 Scenarios（L98 / L102-104 / L106 Idempotence）在 `+ ε` 形式下数学不可调和：
- L98: `z = 0` 时输出 = `0 / (0 + ε) = 0`，但 spec 隐含期望 `z / eps`（L102-104）
- L99: `‖z‖₂ = 2.0` 时 `‖out‖₂ = 2.0 / (2.0 + ε) ≈ 1 − ε/2`，不严格 `== 1.0 within 1e-5`
- L104: `z = 0` 时 `z / eps = 0`，但 L102-104 期望"finite 且 equals z / eps"——后者要求输出非零，矛盾

`z / max(‖z‖₂, ε)` 形式下：
- `z = 0` → `0 / max(0, ε) = 0 / ε = 0`（finite ✓）
- `‖z‖₂ = 2.0` → `2.0 / max(2.0, ε) = 2.0 / 2.0 = 1.0` ✓
- `‖z‖₂ ≥ 1−ε` → `‖out‖₂ ∈ [1−2ε, 1]`（弱等式）
- `‖z‖₂ < ε` → `‖out‖₂ < 1`，但单调递增至 1

**spec 内部先例**：skeleton L409 已明文 "the same `torch.where(use_old, prev, normalize(...))` guard pattern used in EMA must apply to Phase 4 — `centroids / ‖centroids‖.clamp_min(eps)` does NOT satisfy this invariant"——`clamp_min(eps)` 与 `max(‖z‖, ε)` 在数学上同构（clamp 转为 max 形式），spec 已在 Phase-4 场景下否定 `clamp_min(eps)` 模式并要求 `torch.where` 守卫。这给 `z / max(‖z‖, ε)` 方向提供了 spec 内部背书。

**Alternatives considered**:
- (a) 改 `z / max(‖z‖₂, ε)` 但保留 L102-104 "Zero-tensor safe" Scenario —— 拒绝：新公式下 `z = 0` 时输出 = 0（finite ✓），但 spec 期望 `z / eps ≠ 0`，数学上仍不可调和
- (b) 引入 ε-相对形式 `z / max(‖z‖₂, ε · ‖z‖₂)` —— 拒绝：scope 膨胀，且 `ε · ‖z‖₂` 在 `‖z‖₂ → 0` 时退化
- (c) 接受现有 spec 数学矛盾不动 —— 拒绝：review max 标为 CRITICAL，必须 fix

### Decision 4: A-HI-3 修复方向 —— `isinstance + dtype.is_floating_point` 守门

**Choice**: `CG(grad)` 函数入口加 `if not (isinstance(grad, Tensor) and grad.dtype.is_floating_point): raise TypeError(...)` 守门，spec delta 新增 Scenario `CG(grad) raises TypeError on non-floating-point input`。

**Rationale**: spec L317 已声明 `CG = ‖∇_{W^{K, V, b}} L_total‖₂`——`∇_{...}` 必然是 floating-point Tensor。但代码 `metrics.py:158-171` 仅守门 `grad.numel() == 0`，dtype 校验缺失。现有 caller 全部传 Tensor（`safeguards.l2_norm` L54 + `clip_global_grad_norm_`），无回归风险；新增守门是 spec delta 强化的契约。

**实现要点**：
- `isinstance(grad, Tensor)` 排除 list / np.ndarray / None
- `grad.dtype.is_floating_point` 排除 int / bool / complex（即使 complex Tensor 也不在该 contract 内）
- TypeError message 引用 spec L317 闭式作为契约来源

**Alternatives considered**:
- (a) 用 `torch.is_tensor(grad) and grad.is_floating_point()` —— 等价实现；选择 `isinstance + is_floating_point` 是更显式的 API 风格（PEP 484 typing）
- (b) 仅 `is_tensor` 不校验 dtype —— 拒绝：dtype 错误会得到无意义的 norm（`int_tensor.norm()` 返回 float，但语义错误）
- (c) 把 dtype 校验放 caller 侧 —— 拒绝：违反 defencive programming 原则；spec 强制 contract 在 CG 函数入口

### Decision 5: A-HI-4 修复方向 —— 加 thin wrapper 而非合并现有函数

**Choice**: 加 thin wrapper `resurrect_expert(i, j_star, β_per_expert, cfg) -> (c_perturbed, β_per_expert_new)`，内部串起 `resurrection_perturb_distribution` + `apply_resurrection_beta_decay`。**不删** `resurrection_perturb_distribution` 与 `apply_resurrection_beta_decay` 两个现有函数（保持向后兼容）。**不删** `target_idx` 形参（spec L577 已规定 `resurrection_perturb_distribution(target_idx, *, eps_std=0.05)` 保留 target_idx）。

**Rationale**: spec L573-583 Requirement "Resurrection Perturbation Per-Expert Contract" 已规定 (i) API 签名保留 `target_idx` 与 (ii) β 衰减 MUST execute as part of the same resurrection event。当前代码：
- `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim=None)` —— 保留 target_idx ✓
- `apply_resurrection_beta_decay(β_per_expert, j_star, i)` —— 独立函数 ✗（违反单事件要求）

修复方向是**加 wrapper 串起两步**，保证 perturb + β 衰减在同一次调用栈完成。spec delta 仅新增 Scenario `same-event beta decay` 验证 wrapper；不修改 spec L577 API 签名（target_idx 保留不删）。

**实现要点**：
- wrapper 签名 `resurrect_expert(i, j_star, β_per_expert, cfg) -> tuple[Tensor, Tensor]` 返回 `(c_perturbed, β_per_expert_new)`
- 内部先调 `resurrection_perturb_distribution(f, j_star, eps_std=0.05, dim=cfg.d_c)` 得 `c_perturbed`
- 再调 `apply_resurrection_beta_decay(β_per_expert, j_star, i)` 得 `β_per_expert_new`
- 两者**严格在同一调用栈**（无 yield / await / spawn）
- wrapper 加 `__all__` 导出，但不删现有两个函数

**Alternatives considered**:
- (a) 合并 `resurrection_perturb_distribution` 与 `apply_resurrection_beta_decay` 为单一函数 —— 拒绝：破坏向后兼容（4 个 caller），scope 膨胀
- (b) 删 `target_idx` 形参 —— 拒绝：spec L577 明确要求保留
- (c) 加 callback 让 caller 自己串 —— 拒绝：spec 强制"same event"语义，caller 不应负责

### Decision 6: B-ME-1 注释噪清理 —— 5 处 `# noqa: dead-defensive` 全删

**Choice**: 删除 `src/decompmoe/schedule.py:160, 171` 与 `src/decompmoe/metrics.py:110, 148, 152` 共 5 处 `# noqa: dead-defensive` 注释。

**Rationale**:
- `schedule.py:160, 171`: 注释 `# noqa: dead-defensive — float(gamma_p) on None/'abc' raises real TypeError/ValueError` 与 except 子句并置，self-evident；except 行为不变
- `metrics.py:110, 148, 152`: `0-d tensor .item() never raises` / `int → float never raises` / `0-d .item() never raises; check is the real guard` —— 都是关于"该转换不会失败"的 self-evident 注释，与 except/if 行为不变

删除后保留 except / if 子句与相应 docstring；删除的只是冗余注释，不动任何 catch 行为。`grep -r "# noqa: dead-defensive" src/` 应返回 0 命中。

**Alternatives considered**:
- (a) 保留注释但删除 `# noqa: dead-defensive` 字样 —— 拒绝：用户清单标注"清理注释噪"，保留"# noqa"前缀与删除整条注释无本质区别
- (b) 改为 docstring 整合到函数 docstring —— 超出 scope（CLAUDE.md §3 surgical 原则）
- (c) 不清理 —— 拒绝：MEDIUM 等级 finding + 用户明确要求

## Risks / Trade-offs

- **[Risk]** A-CR-1 P4 SGD 步引入会改变训练动力学。Mitigation：默认 `eta=1e-2` 保守值；保留 near-zero fallback 不变量；测试用闭式 `pytest.approx(..., abs=1e-7)` 对账保证数值正确
- **[Risk]** A-CR-2 sphere 公式改动 `+ ε` → `max(‖z‖, ε)` 影响 `extract_C` Step 2 / Step 4 梯度流。Mitigation：现有 `test_full_differentiability`（test_extraction.py:142）守护梯度路径；新增 `test_sphere_norm_monotone_in_z_norm` 守护单调性；spec L409 Phase-4 先例已为 `max` 形式背书
- **[Risk]** A-HI-1 / A-HI-2 spec 修订会让现有 spec 文字不再描述代码。Mitigation：D1 是 design-level 决策，本 change 把 spec 单源真相对齐到 design.md 而非代码；code 不动
- **[Risk]** A-HI-3 CG dtype 守门会让未来非 Tensor caller 抛 TypeError 而非静默归零。Mitigation：现有 4 个 caller 全部传 Tensor（grep verify）；spec Scenario 锁契约
- **[Risk]** A-HI-4 wrapper 函数新增 API surface。Mitigation：纯新增；不删现有函数；target_idx 保留不删；4 个现有 caller 仍走单函数路径
- **[Risk]** Windows Edit tool CRLF contamination。Mitigation：每个 src/ Edit 后跑 `git diff --stat` 验证 LF 保留；必要时 `sed -i 's/\r$//'`
- **[Risk]** 测试覆盖不全（A-CR-2 改公式后需重写 2 个既有 test + 加 1 个新 test）。Mitigation：5 个新 test + 2 个重写 test 全部由 spec Scenario 驱动（CLAUDE.md §3 数学约束协议）

## Migration Plan

N/A — no deployment, no rollback, no migration. 本 change 是 surgical test + spec delta + 4 文件 src/ 修改。实施步骤：
1. spec delta 落地：`specs/decompmoe-skeleton/spec.md` 5 处 MODIFIED + `specs/wayfinder/spec.md` 1 处 MODIFIED
2. src/ surgical edit（4 文件 / 6 处修改，per Decision 1-6）
3. tests/ 5 个新 test + 2 个重写 test
4. `uv run pytest tests/ -v` 全绿
5. `git diff --stat` 验证 LF 保留（无 CRLF contamination）
6. 单 commit on `dev`：`fix(spec,code): close 6 review-max findings (P2 audit 2026-09-08)`

## Open Questions

- **Future audit**: 既有 141 tests 中可能有其他 spec/code 漂移未被清单 2 P2 审计枚举。Open Question：是否开 follow-up change 枚举所有 review max CRITICAL/HIGH 级 finding？本 change 明确只覆盖 6 项；不预先承诺 follow-up 范围
- **A-CR-2 公式选择空间**: spec 作者若希望保留 `+ ε` 形式但承认弱等式（不删除 L102-104），需要回滚本 change 的 L102-104 删除决议。Mitigation：本 change 的 design.md Decision 3 已论证 `+ ε` 形式数学不可调和；review max 等级 CRITICAL 必须 fix
- **A-HI-3 caller 守门升级**: 当前 CG dtype 守门只挡非浮点 Tensor；未来若 caller 传稀疏 Tensor（`torch.sparse_coo_tensor`），norm 计算可能慢。Open Question：是否要加 `grad.is_sparse` 守门？本 change 不覆盖