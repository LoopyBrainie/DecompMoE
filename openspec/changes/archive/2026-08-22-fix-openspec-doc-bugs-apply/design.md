## Context

`fix-openspec-doc-bugs-apply` 是 archived spec-only change `fix-openspec-doc-bugs`（commit `41ac06b`）的下游 code-level apply change。spec delta 已 merge 到主 spec（8 处 MODIFIED + 4 处 ADDED Requirement）与 skeleton spec（8 处 MODIFIED + 1 处 ADDED Requirement），共 13 项 A-1 ~ A-13 修订。本 design 文档聚焦实现侧的技术决策：如何把 spec 文本的数学闭式（Voronoi Beta 反演 / L_lb 双因子 / 死专家阈值参数化 / 双通道冻结集 / 8 指标闭式）落到 5 个 `src/decompmoe/*.py` 模块与对应 tests，并保证 `pytest.approx` 直接验算 spec 声称数值（CLAUDE.md §6 硬约束）。

上游 spec contract 已锁定的关键数学不变量：
- Voronoi：`canonical_voronoi_angle(16,16) ≈ 0.9076 rad`（52°），`(64,16) ≈ 0.4494 rad`（25.45°），`> θ_{1/e}(β=16) ≈ 20.36°`
- L_lb：`L_lb = N_e · Σ_i f_i.detach() · P_i`，梯度流 `∂L_lb/∂P_i ≠ 0` AND `∂L_lb/∂f_i ≡ 0`
- 死专家阈值：`threshold = 1/(2·N_e)`，MVP N_e=16 → 1/32
- Schedule Phase 2 freeze：`{c_i, beta_i}`（gradient channel frozen，W_K/W_V/b 解冻）；Phase 3：`{c_i}`
- 8 metrics 闭式：Realtime 4 + Offline 4（含死专家 `SP_i ≡ undefined`）

## Goals / Non-Goals

**Goals:**
- 把 13 项 archived spec delta 落地到 5 个 src 模块 + 5 个 test 文件
- 每条 pytest 含 `pytest.approx` / `torch.allclose(..., atol=...)` 直接验算 spec 数值（CLAUDE.md §6 硬约束）
- 5 个 SS 子项（SS-7/13/14/15/16）每个跑完整 RED → GREEN → Refactor 循环，写 `.claude/tdd/fix-openspec-doc-bugs-apply.tdd.md` evidence
- checkpoint commit 全部在 `dev` 线性提交（CLAUDE.md §4）

**Non-Goals:**
- 不执行训练、不跑 baseline（CLAUDE.md §6）
- 不修改 `src/decompmoe/extraction.py`（属于 `fix-spec-doc-oversights-apply` Issues ⑥⑦⑧）
- 不修改 `src/decompmoe/contracts.py` / `__init__.py` / `experts.py` / `distance.py` / `gating.py` / `beta.py` / `config.py` / `viz.py`（已与 archived spec 对齐）
- 不修改 openspec specs 文件（已 archived 锁定）
- 不重写 wayfinder ticket（CLAUDE.md §8 2026-08-21 裁决）

## Decisions

### Decision 1 — SS-7 Voronoi 实现用 `scipy.special.betainc` + bisection（不引入新依赖）

**Choice**: `canonical_voronoi_angle(N_e, d_c)` 通过解方程 `0.5 · I_{sin²θ}((d_c-1)/2, 1/2) = 1/N_e` 求 θ，使用 `scipy.special.betainc` 计算正则化不完全 Beta 函数 + 二分搜索（精度 1e-6 rad）。

**Rationale**: scipy 是 stdlib 依赖（`from scipy.special import betainc`），无需修改 `pyproject.toml`。二分搜索保证收敛性，避免调用 `optimize.brentq` 等开销更大的 solver。MVP `(16,16)` 在 ~30 次二分迭代内收敛到 1e-6 rad。

**Alternatives considered**:
- (a) 自实现完全 Beta 函数反演（不用 scipy）：MVP 尺度无收益，代码量增加
- (b) 用 `mpmath` 高精度库：MVP 无需 1e-15 精度，且引入新依赖
- (c) 查表（precompute 几个常用 (N_e, d_c) 组合）：spec 要求函数依赖两个参数（不只是 d_c），表覆盖不全

### Decision 2 — SS-13 L_lb 实现 `N_e · (f.detach() * P).sum()` 向量化

**Choice**: `L_lb = N_e * (f_per_expert.detach() * p_per_expert).sum(dim=-1).mean()`。

**Rationale**: spec 公式 `L_lb = N_e · Σ_i f_i.detach() · P_i` 是 per-token 标量（`f` 与 `P` 都是 `[B, N, N_e]` 形状张量）。`sum(dim=-1)` 把 N_e 轴求和（每个 token 1 个标量），`.mean()` 对 batch 求平均得到 L_lb 总标量。`f.detach()` 阻断梯度，`p_per_expert` 保持 `requires_grad=True`，满足 `∂L_lb/∂P_i ≠ 0` AND `∂L_lb/∂f_i ≡ 0`。

**Alternatives considered**:
- (a) 显式 for-loop over N_e：spec 公式虽是求和符号，但 N_e=16 规模下向量化更高效；spec 仅要求闭式正确，不要求代码字面循环
- (b) `(f.detach() * P).sum() / N_e`（除以 N_e 而非乘）：spec 明写 `N_e · Σ`，反向

### Decision 3 — SS-14 `should_resurrect` 加 `N_e: int` 必填参数（而非 cfg 对象）

**Choice**: `def should_resurrect(f_per_expert, window_size, last_resurrection_step, current_step, *, N_e: int, consec=200) -> set[int]`（threshold 由 N_e 推导 = `1/(2*N_e)`）。

**Rationale**: spec 明确 `threshold = 1/(2·N_e)`，threshold 由 N_e 单参数唯一确定，无需传入 cfg 对象（保持函数签名简洁）。N_e 是 int，threshold 自动 = `1/(2*16) = 1/32` (MVP) 或 `1/(2*64) = 1/128` (其他配置)。

**Alternatives considered**:
- (a) `cfg: MVPConfig`：耦合 cfg，破坏函数纯净性（应可独立测试）
- (b) 模块全局 `_current_N_e`：副作用式共享状态，难测试

### Decision 4 — SS-15 `phase_step_frozen_names(3)` 返回 `{c_i}`（beta_i 在 phase 3 解冻）

**Choice**: `phase_step_frozen_names(3) = {"c_i"}`（spec 明确：Phase 3 router 训练 via driver-channel EMA，β_i 可调；c_i 仍 gradient channel frozen）。

**Rationale**: skeleton spec L133 "Phase 3 MUST continue router training via driver-channel Masked Spherical EMA at α = 0.99, with operational β ramping 4.0 → 16.0" 暗示 β_i 是可调参数（路由训练的一部分）。Phase 4 时 `c_i` 才完全解冻（gradient channel Active）。

**Alternatives considered**:
- (a) Phase 3 freeze = `{c_i, beta_i}`（同 Phase 2）：spec 明确 β_i 在 Phase 3 解冻；保留会违反 spec
- (b) Phase 3 freeze = empty：Phase 3 仍有 driver-channel 单独 update 行为，c_i gradient channel 仍 frozen

### Decision 5 — SS-16 `UR` 实现用 100-step sliding buffer

**Choice**: 新增 `URBuffer(window_size: int = 100)` 类，内部 `deque[Tensor]` 存储最近 100 步的 `f_per_expert`；`UR(buffer) = (1/N_e) · Σ_i I[any_of_100_f_i[i] > 0]`。

**Rationale**: spec L283 "UR over the most recent W = 100 steps" 明确要求 sliding window。buffer 类封装状态管理，避免 metrics 模块变成全局可变状态。MVP 100 步 / 16 expert = 1600 标量，内存开销可忽略。

**Alternatives considered**:
- (a) 函数签名加 `f_history: list[Tensor]`：caller 负责 buffer 管理，metrics 模块保持纯净；但破坏 spec "UR metric" 的开箱即用性
- (b) 全局 `metrics._ur_buffer`：副作用式，难测试

### Decision 6 — SS-16 `D_chord` 用双重 for-loop（不是矩阵化）

**Choice**: `D_chord(c) = (2 / (N_e*(N_e-1))) * sum_{i<j} sqrt(2 * (1 - c[i] @ c[j]))`，显式双层 for-loop over `(i, j)` pairs。

**Rationale**: N_e=16 时只有 120 对，循环开销可忽略；可读性远高于矩阵化 `triu_indices` + `einsum`。spec 要求闭式而非性能。

**Alternatives considered**:
- (a) 矩阵化 `c @ c.T` + `triu_indices` + `sqrt`：性能更优，但牺牲可读性
- (b) `torch.cdist` with p=2：返回欧氏距离（不是 chord），与 spec 不符

### Decision 7 — checkpoint commit 落在 `dev`，遵循 CLAUDE.md §4 线性提交

**Choice**: 21 个 checkpoint commit 全部在 `dev` 上 fast-forward 线性提交。

**Rationale**: CLAUDE.md §4 硬约束——`dev` 永远线性。archive 后由用户决定 `dev → main`（关键存档点）+ `dev → release`（必带 tag）。

## Risks / Trade-offs

**[Risk 1] `scipy.special.betainc` 在 Windows + Python 3.13 + torch==2.12.1 环境下可能 wheel 缺失**：`uv sync` 会自动拉 `torch==2.12.1` 与 `scipy`（如 pyproject.toml 中已声明）；若 scipy 未声明，bisection 实现需重写。**Mitigation**: 验证 `pyproject.toml` 含 `scipy`；若缺则改为自实现完全 Beta 函数 `B(sin²θ)` 用 gamma 函数字面求和（15 项 series）。

**[Risk 2] `L_total` 签名变更破坏现有 7 个 test 调用**：2.2 已规划同步更新。**Mitigation**: tests/task.md §2.2 列出所有需更新的 test 名称。

**[Risk 3] `should_resurrect` 签名变更破坏 `tests/test_safeguards.py::test_resurrection_trigger_window`**：当前传 `threshold=1/256 < 1/128`，修后传 `threshold=1/32`（MVP 默认）。**Mitigation**: tests/task.md §3.1 列出。

**[Risk 4] `phase_step_frozen_names(2)` 返回集合变更影响 Phase 2 训练循环**：spec 与 code 一错，archive 后实现修，测试 §4.1 同步。**Mitigation**: tasks.md §4.1。

**[Risk 5] `S_load = N_e · max` 对极端分布（如 one-hot）爆炸**：`S_load = 16·1 = 16`（理论上限），无 NaN 风险。**Mitigation**: 无需特殊处理。

**[Risk 6] `MCI` 实现用 `torch.linalg.eigvalsh` 需要 symmetric matrix**：构造 `Cov(C) = (C - mean)ᵀ (C - mean)` 自动 symmetric。**Mitigation**: 测试已验证 `eigvalsh` 在 symmetric 输入上收敛。

## Migration Plan

本 change 是 code-only，无运行时迁移：

1. **apply 阶段（spec archive 后）**：`openspec instructions apply --change fix-openspec-doc-bugs-apply --json` 拿 task list
2. **代码实现**：按 tasks.md §1-5 的 21 个 checkpoint 顺序执行 RED → GREEN → Refactor
3. **archive**：`openspec archive fix-openspec-doc-bugs-apply`
4. **rollback**：git revert 本 change 的 commit chain

## Open Questions

无。13 项 archived spec delta 决策已落地到 spec 文本（archived `fix-openspec-doc-bugs/proposal.md` A-1 ~ A-13 段）与本 design.md Decisions 1-7。