## Why

上游 spec-level change `fix-math-consistency-audit-2026-08` 已 archive（commit `f45a42c`），修正后的闭式常量与不变量已落入 master specs（wayfinder + decompmoe-skeleton）。但代码层与测试层尚未对齐：存在 8 处代码 stub / 常量错误、8 处恒真断言（95/95 绿但未验证原理），需按 `apply-checklist.md` 的 17 项 spec-anchored 任务落地，使实现严格服从已 archive 的 spec。

## What Changes

- **代码改动（8 项）**：
  - `sphere.py`：删除 `_VORONOI_MVP_TABLE` 硬编码表，全部输入走 bisection
  - `config.py`：FFN FLOPs 系数 `2*2 → 3*2`（SwiGLU 3 矩阵）
  - `schedule.py`：新增 `gamma_reset_for_phase4` / `phase_beta_max` / `beta_effective`；修复 `phase_beta_box(2)` 落空到 `(1.0, 32.0)` 的 bug
  - `metrics.py`：替换 SP / D_chord（原 D_c）/ MCI / CG 四个 stub 为 spec 闭式实现
  - `experts.py`：`ExpertPool` 改为 `nn.Module` + `nn.ModuleList`
  - `extraction.py`：Phase 4 分支补充近零 candidate fallback（`torch.where(‖c‖ < 1e-9, prev_c, normalize(c))`）
  - `safeguards.py`：resurrection perturb 输出改为单专家形状 `(d_c,)` 或 `(d_model·d_ffn,)`，并加 β 衰减突变
  - `beta.py`：新增 `phase4_inverse_temperature` 与 Phase 4 梯度上界常量
- **测试重写（5 项）**：`test_loss.py` / `test_beta.py` / `test_extraction.py` / `test_gating.py` / `test_config.py` 中 8 处恒真断言替换为 spec 闭式常量的数值对账
- **新测试文件/用例（4 组）**：约 15 个新的 closed-form / residual / continuity 测试
- 无 spec-level 行为变更：所有行为条款已在 master specs 中定义，本次仅为代码/测试对齐。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 — 本次为 code-only change，spec 层无 requirement 变更。`.openspec.yaml` 已设 `skip_specs: true`。）

## Impact

- **Source**: 反链 `fix-math-consistency-audit-2026-08`（archived）及其 apply 入口 `apply-checklist.md`
- 受影响源码：`src/decompmoe/{sphere,config,schedule,metrics,experts,extraction,safeguards,beta}.py`
- 受影响测试：`tests/test_{loss,beta,extraction,gating,config,sphere,schedule,metrics,experts,safeguards}.py`
- 验收基线：现有 95 passed 全保留（重写不增计数），新增 ~15 tests → 目标 ≥ 110 passed, 0 failed
- 不涉及训练执行、baseline、推理引擎实现（Out of Scope 维持 CLAUDE.md §7）
