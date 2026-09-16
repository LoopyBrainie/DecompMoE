## Why

`/code-review max` 对 `2026-09-05-fix-metrics-cg-closed-form`（CRIT-3 修复）的 post-archive review 发现 **LOW 7**：CG 函数行为在 `n==1` 输入情况下发生了**未文档化**的 silent change：

- **OLD** `CG` (`mean pairwise |g_i − g_j|`)：`CG([5.0])` 返回 `0.0`（pairwise diff 需要 `n≥2`，函数体早 return `_ZERO`）
- **NEW** `CG` (`torch.linalg.norm(grad)`)：`CG([5.0])` 返回 `5.0`（L2 范数 = single element 绝对值）

新实现 per spec L394 `CG = ‖∇‖₂` 是数学正确的（spec 没说 n==1 边界），但 silent change 违反 CLAUDE.md §3「Surgical Changes」原则（行为变化未文档化），且 `/code-review max` 进一步指出原提案以 `skip_specs: true` 跳过 spec 是反 CLAUDE.md §2「先改 spec 后改 code/test」。

## What Changes (actual diff only)

- **`openspec/specs/wayfinder/spec.md`**（在 archive 时合并）**ADDED Requirement `CG n=1 boundary behavior`** + 3 个 Scenario（positive / negative / zero 单元素输入的 `CG(g) == abs(g.item())` 闭式对账）+ **`**Source:**` 字段**（治理 req-33 + `scripts/lint_no_source_field_drift.py` 硬约束）。Anchor: Req 20 (CG) 表 **L390** `CG = ‖∇_{W^{K, V, b}} L_total‖₂`（2026-09-15 后 spec 因 FLOPs consistency 调整行号漂移，L394 → L390；原 change 锚点需随之刷新）
- **`tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude`** 新增：3 个闭式对账（`CG([5.0]) == 5.0`、`CG([-5.0]) == 5.0`、`CG([0.0]) == 0.0`），docstring 反链 `wayfinder Req 20 (CG) L390 + ADDED "CG n=1 boundary behavior"` 作为 spec anchor
- 无 code 改动（`metrics.py::CG` 实现 `torch.linalg.norm(grad)` 已正确，仅补 spec anchor + test 守护）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `wayfinder` — ADDED Requirement `CG n=1 boundary behavior`（3 个 Scenario 守护 `n=1` 输入的 L2 范数行为）

## Impact

- 受影响文件：`tests/test_metrics.py`（新增 `test_cg_n_eq_1_returns_magnitude`）
- 反链：code-review agent（`a22626aefc6a5eea3`）LOW 7；上游 change `2026-09-05-fix-metrics-cg-closed-form`；CLAUDE.md §2「先改 OpenSpec spec」
- 验收基线：`uv run pytest tests/test_metrics.py -v` 全过（含新测试）；`uv run pytest tests/ -v` 当前 baseline **187 passed**（`uv run pytest tests/ --collect-only -q` 输出 187 tests / 4.03s @ 2026-09-16），apply 后 +1 → **188 passed**；`openspec validate --strict add-cg-n-eq-1-test` 通过；`python scripts/lint_no_source_field_drift.py` exit=0（验证 Source 字段结构合规）
- 无破坏性变更（pure spec + test addition）