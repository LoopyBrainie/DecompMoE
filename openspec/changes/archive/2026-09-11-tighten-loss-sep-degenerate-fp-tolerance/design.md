## Context

`tests/test_loss.py::test_lambda_zero_phase_1_2` 第 132 行使用 `assert parts.L_sep.item() == 0.0` 守 `L_sep = λ · L_sep_raw` 在 `λ=0` 退化边界（`phase ∈ {1, 2}`）的零值。同时 `tests/test_loss.py::test_sep_formula_orthonormal_degenerate` 第 183 行使用 `pytest.approx(0.0, abs=1e-12)` 守正交基退化边界 `c = I_d ⇒ L_sep == 0.0`。同文件两条 zero-degenerate 守门精度不一致。

`openspec/specs/decompmoe-skeleton/spec.md` `Loss Composition With Staged Lambda` Requirement 下 Scenario `Lambda zero in phases 1 and 2`（line 184-186）的 THEN 写"exactly `0.0`"，而 Scenario `L_sep closed form`（line 196-198）的 THEN 写"within `abs=1e-12`"——spec 内部已不自洽（同一 `L_sep == 0` 退化语义两处容差不一致），且 line 184-186 的"exactly 0.0"在浮点路径上不可达（违反 CLAUDE.md §6 第 8 条）。本 design 闭环对齐 spec Scenario + test 断言。

## Goals / Non-Goals

**Goals:**
- 把 spec Scenario `Lambda zero in phases 1 and 2` 的 THEN 从"exactly `0.0`"改为"equals `0.0` within `abs=1e-12`"，与 Scenario `L_sep closed form` 容差表述对齐。
- 把对应 test (`tests/test_loss.py:132`) 从 `assert parts.L_sep.item() == 0.0` 改为 `assert parts.L_sep.item() == pytest.approx(0.0, abs=1e-12)`，与同文件 line 183 范式对齐。

**Non-Goals:**
- 不修改 `src/decompmoe/loss.py`（`L_total` / `compute_L_sep` 实现不变；退化边界数学为零，`λ·x = 0` 路径本应严格返回零张量）。
- 不修改 spec 中 `L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` Frobenius 闭式 **值**——仅调整 Scenario 2 的容差表述。
- 不收紧/放宽其它断言的容差（如 `test_load_balance_alpha_fixed` 已用 `pytest.approx(1.0, abs=1e-6)`、`pytest.approx(0.01, abs=1e-8)`，属另一专项）。
- 不引入新依赖，不引入新测试函数，不修改其它模块。

## Decisions

### D1. 容差选择 `abs=1e-12`（而非 `1e-9` / `1e-6` / `==`）

**选择**：`abs=1e-12`。

**理由**：
- `λ=0` 路径下 `L_sep = lam * L_sep_raw`（`src/decompmoe/loss.py:120` 是单点张量乘，**无 reduction**；`mean()` 仅出现在 L_lb 路径 line 114-115）；数学上 `0 · x ≡ 0` 严格，IEEE 754 保证 `0.0 * finite = exact 0`——理论上原 `== 0.0` 已能通过。`abs=1e-12` 容差是 project-level safety margin：与同文件 line 183 正交基退化场景（`abs=1e-12`）对齐；若未来 `loss.py` 在 `lam * L_sep_raw` 路径上意外插入 reduction step（如 broadcast + `mean()`），仍能容忍 ~1e-12 量级实现漂移。这也是 CLAUDE.md §6 第 8 条对 float closed-form 算式的硬约束（"pytest.approx(..., abs=...) 直接对账"）。
- 同文件 line 183 (`test_sep_formula_orthonormal_degenerate`) 已建立 `abs=1e-12` 范式（Scenario `L_sep closed form` 也用此容差）；保持一致可避免"两条 zero-degenerate 守门用两套容差"的内部不一致。
- 比 `abs=1e-9` 严格 3 个数量级（`1e-9` 太松会掩盖真实实现漂移），比 `abs=1e-6` 严格 6 个数量级（`1e-6` 是 `test_load_balance_alpha_fixed` 通用层容差，不适合退化边界专用）。

**替代**：
- `==`（原状）：违反 CLAUDE.md §6 第 8 条，且无法容忍 FP 噪声下的 1e-17 偏差。
- `abs=1e-9`：过松，掩盖未来可能的实现漂移（如同 requirement 收紧时本应失败但被噪声吞掉）。
- `abs=1e-15`：过严，可能在某些 GPU 后端（如 TF32、bfloat16）误杀合理路径。本项目用 float32，无此风险，但仍按 line 183 范式统一。

### D2. 走 `MODIFIED Requirements` 而非 `ADDED Requirements`

**选择**：MODIFIED `Loss Composition With Staged Lambda` Requirement，仅改 Scenario `Lambda zero in phases 1 and 2` 的 THEN 子句。

**理由**：
- 现有 Scenario 2 (`Lambda zero in phases 1 and 2`, line 184-186) 已覆盖"phase ∈ {1, 2} ⇒ L_sep contribution is 0"的语义，只是 THEN 容差表述与 line 196-198 不一致——这是**修正**而非**新增**。
- ADDED 会产生两条 Scenario 都守"phase ∈ {1,2} ⇒ L_sep==0"，语义重复且 spec 内部矛盾仍然存在（"exactly 0.0"vs"abs=1e-12"）。
- MODIFIED 的 archive 语义是把整个 L_total Requirement block（含全部 6 个 Scenario）并入主 spec 后，line 184-186 的 THEN 子句自动替换；其它 5 个 Scenario 与 Requirement 主体保持原样。
- MODIFIED 也符合 archive precedent `2026-09-06-tighten-test-precision-tolerance` 的处理模式（修改 wayfinder 的某 Requirement 的某个 Scenario 表述）。

**替代**：
- ADDED Requirement（如"L_sep Degenerate Boundary Numerical Tolerance"）：引入语义重复，且与 line 196-198 Scenario 重叠。
- skip_specs：CLI validate 不通过（spec 内部不自洽本身算 spec-level issue；fix 测试精度但不修 spec 会让 spec 文本继续误指"exactly 0.0"）。

### D3. 不修改 `src/decompmoe/loss.py`

**选择**：保持 `src/decompmoe/loss.py` 不变。

**理由**：
- `λ=0` 路径下 `L_sep = λ · L_sep_raw`，FP 数学上为严格零；测试改为 `pytest.approx(0.0, abs=1e-12)` 是守门端容差变化，不影响实现端应返回值。
- 若未来 `L_total` 实现路径引入新加和步骤导致 `L_sep` 在 `λ=0` 边界从 ~0 漂移到 ~1e-10，`abs=1e-12` 守门将捕获此漂移——这正是收紧测试的意义（CLAUDE.md §6 第 8 条 + §3 TDD 原则）。
- 实现端改动属于 `loss.py` 重构范畴，超出本次"测试精度收紧"边界；如未来发现 `λ=0` 路径真有非零输出，应开新 change 处理（不应借精度收紧夹带实现修复）。

**替代**：
- 同时改 `loss.py`（如显式 `if λ == 0: return torch.zeros_like(...)`）：超出提案范围，且让 `abs=1e-12` 守门永远不报警（失去 test guard 价值）。

## Risks / Trade-offs

- **R1: `abs=1e-12` 过严误杀** → Mitigation: 复用 line 183 已建立的 `abs=1e-12` 范式作为先验；同文件、同 requirement、同一 `L_sep==0` 退化语义。
- **R2: spec archive 后 line 184-186 文本漂移** → Mitigation: MODIFIED block 内的 Scenario 2 THEN 文本与主 spec line 184-186 完全对齐（仅替换 "exactly `0.0`" → "equals `0.0` within `abs=1e-12`"），archive 时按 OpenSpec delta 合并语义替换，不会漂移。
- **R3: 测试漏掉其它 zero-degenerate case** → Mitigation: 后续 audit 轮次专门扫描（本次仅针对 line 132 一处遗漏，承接 archive `2026-09-06-tighten-test-precision-tolerance`）。

## Migration Plan

无迁移需求：
- 无 production code 变更
- 无 API 变更
- 无配置变更
- 测试容差收紧是**严格化**而非**放宽**，不可能引入回归失败
- 无需 rollback 预案

## Open Questions

(none)
