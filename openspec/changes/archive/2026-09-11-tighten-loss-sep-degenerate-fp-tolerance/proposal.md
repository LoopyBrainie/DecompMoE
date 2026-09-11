## Why

`tests/test_loss.py::test_lambda_zero_phase_1_2` 在第 132 行用 `assert parts.L_sep.item() == 0.0` 直接断言 `L_sep` 在 phase ∈ {1,2}（`λ=0`）退化边界上为精确零。这违反 `CLAUDE.md` §6 第 8 条（"spec 中每个含具体数值的算式都必须有 `pytest.approx(..., abs=...)` 直接对账"）——`L_sep = λ · L_sep_raw` 的浮点乘法路径不能保证输出位级等于 `0.0`（即便数学上为零），应当用闭式容差 `abs=1e-12` 与同测试文件第 183 行的 `test_sep_formula_orthonormal_degenerate` 对账（后者已用 `pytest.approx(0.0, abs=1e-12)` 处理同样的正交基退化边界）。

本次是承接 `2026-09-06-tighten-test-precision-tolerance` 的后续收紧专项：上轮 audit 已覆盖 `tests/test_config.py` 与 `tests/test_sphere.py` 的精度 gap，本轮仅剩 `tests/test_loss.py` 一处遗漏。

## What Changes

- **`tests/test_loss.py::test_lambda_zero_phase_1_2` 第 132 行**：将 `assert parts.L_sep.item() == 0.0` 改为 `assert parts.L_sep.item() == pytest.approx(0.0, abs=1e-12)`，与第 183 行 `test_sep_formula_orthonormal_degenerate` 的 `L_sep(orthonormal basis) == 0.0` 容差完全对齐。

无 production code 变更；无新测试添加；无 `L_sep` 闭式 **值** 变化（spec 中 `L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` 的 Frobenius 形式不变，仅调整该闭式在退化边界上的测试容差）。

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `decompmoe-skeleton` — **MODIFIED** `Loss Composition With Staged Lambda` Requirement: 仅改写 Scenario `Lambda zero in phases 1 and 2` 的 THEN 子句（line 184-186），从"exactly `0.0`"改为"within `abs=1e-12`"，与同 Requirement 下 Scenario `L_sep closed form`（line 196-198）的 `abs=1e-12` 容差表述对齐。两 Scenario 都覆盖 `L_sep == 0.0` 退化边界，spec 内部从此一致。其它 4 个 Scenario（Alpha pinned / Lambda cosine ramp / Lambda fixed / L_lb gradient flows）和 Requirement 主体不变。

## Impact

- 反链: `CLAUDE.md` §6 第 8 条（closed-form `pytest.approx` 强制）；`tests/test_loss.py::test_sep_formula_orthonormal_degenerate:183`（已建立的 `abs=1e-12` 范式）；`openspec/specs/decompmoe-skeleton/spec.md` L_total Requirement（`L_sep` Frobenius 闭式）。
- 验收基线: `uv run pytest tests/test_loss.py -v` 全过（含 line 132 改为 `approx` 后、`phase ∈ {1,2}` 仍以 `abs=1e-12` 守门）；`uv run pytest tests/ -v` 全套仍过。
- 无破坏性变更: `λ=0` 时 `L_sep` 数学上为零，`abs=1e-12` 与原 `== 0.0` 在浮点零附近等价；不会产生新失败，仅把字面等式断言升级为带容差的闭式守门，与项目既有规则统一。
- 不需要运行训练或 baseline。
- 不引入新依赖，不修改 `src/decompmoe/loss.py`，不修改 `compute_L_sep` / `L_total` 任何实现。
