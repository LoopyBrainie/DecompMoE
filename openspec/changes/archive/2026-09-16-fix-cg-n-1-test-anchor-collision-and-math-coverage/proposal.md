## Why

`/code-review` on `ground-cg-n-eq-1-test` (commit `b8c149c`, 2026-09-16) surfaced two findings that need follow-up:

- **MINOR (Verbatim review finding)**: `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` 5 个 `pytest.approx(abs=1e-12)` 断言只验证 OUTPUT identity（`CG(single_element) == abs(value)`），不验证 L2-norm 推导链；`abs(g.sum())` / `g.abs().max()` 在 numel=1 tensor 上**也**返回 abs(value)，这两类非 L2 norm 实现会绕过测试。spec L445 的 "MUST satisfy the L2-norm identity" 措辞比当前 test 覆盖更严格。
- **MAJOR (Post-review deeper investigation)**: `b8c149c` apply 时给 "CG n=1 boundary behavior" Requirement 添加了 `<a id="req-34">` 锚点，但**这个 anchor 历史上是 "Source Field Format Invariant" Requirement 应有的**（由 `f033d2e` 2026-09-15 同步时**漏掉**，governance spec 与 `tests/test_lint_no_source_field_drift.py` 早已反向引用 `req-34` 期望指向 "governance-origin requirements trigger lint failure" Scenario）。后果：spec 内 `req-34` 现在指向 CG n=1 boundary，与 governance spec 的跨引用断链；Source Field Format Invariant 在 wayfinder/spec.md L676 仍是匿名 Requirement，HTML 中 `<a id="req-34">` 实际被两个不同 Requirement 内容映射（虽然只有 1 个 anchor HTML 元素，但语义上 req-34 应指向 Source Field Format Invariant 的 Scenario "governance-origin requirements trigger lint failure"，不是 CG n=1 boundary）。

## What Changes

- **`<a id="req-34">` 锚点回迁**：从 `openspec/specs/wayfinder/spec.md` L442 (CG n=1 boundary) 移至 L676 (Source Field Format Invariant Requirement 标题前一行)。修复 governance spec L3 + `tests/test_lint_no_source_field_drift.py:3` 的跨引用断链。
- **CG n=1 boundary 重命名**：`<a id="req-34">` 在 L442 改为 `<a id="req-35">`（wayfinder spec 当前最大 anchor 是 req-34，下一个可用 anchor 是 req-35）。无数字跳号，符合 wayfinder spec 整数 anchor 惯例。
- **`tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` 加 L2-norm sanity check**：在 5 个 `pytest.approx(abs=1e-12)` 断言外，验证 `metrics.CG(g) == torch.linalg.norm(g).item()` 在 numel=1 输入上**逐位相等**（L2 norm identity 的形式化对账），把 "L2 norm 是计算路径" 显式钉进测试。当前 test 只验证 value identity（== abs(value)），这个 sanity check 验证 implementation path identity（== L2 norm reduce 路径）。
- **无 active spec requirement body 变更**：CG n=1 boundary Requirement 的 4 个 Scenario、Source 字段、anchor L443-463 内容均不动；Source Field Format Invariant Requirement L676+ 内容、Scenarios、Lint 反规则条款均不动。仅做 anchor relocation + test 加 1 行。
- 无 production code 改动（`src/decompmoe/metrics.py::CG` 已是 `torch.linalg.norm(grad)`，与 spec 一致）。

## Capabilities

### New Capabilities

(无)

### Modified Capabilities

- `wayfinder`: 重命名 anchor `req-34` 的物理绑定位置（CG n=1 boundary → Source Field Format Invariant），新增 anchor `req-35` 给 CG n=1 boundary。**无 Requirement body 改动**，仅 anchor 重新绑定。
- `decompmoe-skeleton`: extend `Scenario: test_cg_n_eq_1_returns_magnitude`（在 `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude`）—— 不影响 spec 文本，只影响 test 代码。等价于 spec Scenario 闭式对账的强化：`CG(g) == torch.linalg.norm(g).item()` 显式钉 L2 norm 作为计算路径。

## Impact

- 受影响文件:
  - `openspec/specs/wayfinder/spec.md`（anchor 移动 + 新增 `req-35`）
  - `tests/test_metrics.py`（新增 L2-norm sanity check 行；不修改任何 `assert` 行为）
  - **无** governance / lint / production code 改动
- 反链：governance spec L3 引用现在正确指向 Source Field Format Invariant "governance-origin requirements trigger lint failure" Scenario；`tests/test_lint_no_source_field_drift.py` 文档字符串现在准确描述 `req-34` 内容。
- 验收基线：
  - `python scripts/lint_no_source_field_drift.py` exit=0（Source 字段格式未变）
  - `python scripts/lint_no_dead_defensive.py` exit=0（无 defensive-code 改动）
  - `uv run pytest tests/test_metrics.py -v` 全过（含 `test_cg_n_eq_1_returns_magnitude` 6 个断言：原 5 个 + 1 个新增 sanity check）
  - `grep "req-34"` 在 `governance/spec.md` + `tests/test_lint_no_source_field_drift.py` + 任何 cross-reference 处仍指向 Source Field Format Invariant（语义上正确）
- 无破坏性变更：纯 anchor renumbering + 1 行 test additive。