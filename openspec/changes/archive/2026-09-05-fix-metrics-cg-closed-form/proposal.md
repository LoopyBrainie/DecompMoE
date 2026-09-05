## Why

`src/decompmoe/metrics.py:144-156` 的 `CG` 函数实现为 `mean pairwise |g_i − g_j|`（输入梯度展平后的成对绝对差均值），但 `openspec/specs/wayfinder/spec.md` Req 20 L394 明确规定 `CG = ‖∇_{W^{K, V, b}} L_total‖₂`（L2 范数）。两实现都满足正齐次性 `|CG(2g) − 2·CG(g)| < 1e-6`，因此现有 `test_cg_positive_homogeneity` 无法捕获此 bug——它是测试盲点。闭式验算示例：`g = [3.0, 4.0]` 时，L2 范数 = `5.0`，但当前实现返回 `1.0`（仅 1 对 `|3−4|`）；`g = [1.0, 2.0, 3.0]` 时 L2 = `√14 ≈ 3.742`，但当前实现返回 `4/3 ≈ 1.333`。后果：(a) `CG` 报告值与 spec 闭式不一致，所有依赖 CG 的下游判断（debug stability probe）失真；(b) metric 与 spec 的字面承诺不兑现，违反 CLAUDE.md §6 第 8 条「数值必须 `pytest.approx` 闭式对账」。

## What Changes

- **`src/decompmoe/metrics.py:144-156`** `CG` 函数实现替换为 L2 范数：
  - 旧实现：`mean pairwise |g_i − g_j|` over flattened entries（spec 不符）
  - 新实现：`torch.linalg.norm(grad).item()`（与 spec `CG = ‖∇‖₂` 字面对齐）
  - docstring 同步：从「mean pairwise」改为「L2 norm per spec Req 20」
- **`tests/test_metrics.py::test_cg_l2_norm_closed_form`** 新增闭式对账测试：
  - `CG([3.0, 4.0]) == pytest.approx(5.0, abs=1e-6)`
  - `CG([1.0, 2.0, 3.0]) == pytest.approx(sqrt(14.0), abs=1e-6)`
  - `CG(zeros) == 0.0` 保留（既有 `test_cg_zero_gradient_invariance` 不变）
  - `CG(2g) == 2·CG(g)` 保留（既有 `test_cg_positive_homogeneity` 不变）
- 无 spec 改动（spec Req 20 L394 `CG = ‖∇‖₂` 已正确，问题在 code 实现）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 — 本次为 code-only fix，spec 层无 requirement 变更；`.openspec.yaml` 设 `skip_specs: true`）

## Impact

- 受影响源码：`src/decompmoe/metrics.py:144-156`
- 受影响测试：`tests/test_metrics.py`（新增 `test_cg_l2_norm_closed_form`）
- 反链：审计报告 `.audit/audit-report.md` 中 CRIT-3（已确认）；独立 verifier 用闭式验算 `g=[3,4]→1 vs spec 5`、`g=[1,2,3]→4/3 vs √14`
- 验收基线：`uv run pytest tests/test_metrics.py -v` 全过；新测试 `test_cg_l2_norm_closed_form` 闭式对账通过
- 无破坏性变更（CG 仅 debug 指标，不进入 quality acceptance per spec L394）