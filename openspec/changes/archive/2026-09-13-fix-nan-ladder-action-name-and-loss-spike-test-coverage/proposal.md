# Proposal: 2026-09-13-fix-nan-ladder-action-name-and-loss-spike-test-coverage

## Why

Comprehensive review of archived change `2026-09-12-replace-literal-wayfinder-l249-with-anchor-ref` (anchored at wayfinder Req 13 + skeleton spec `Five Numerical Safeguard Helpers`) revealed 3 actionable findings, ordered by severity:

**🔴 Finding 1 (HIGH) — `halve_lr` action name is misleading**. `nan_ladder(3)` returns `("halve_lr", 0.1, False)`. The action name `halve_lr` semantically means "LR ÷ 2", but `lr_scale = 0.1` mathematically means "LR ÷ 10" (per wayfinder L249: "3 consecutive NaN trigger **LR ÷ 10**"). The repo has TWO uses of "halve" naming with DIFFERENT semantics:
- `nan_ladder(c).action == "halve_lr"` → lr_scale = 0.1 (= LR ÷ 10) — **misnamed**
- `beta_saturation_global_halve()` → triggers LR × 0.5 (= LR ÷ 2) — **correctly named**

This is an API trap: callers pattern-matching on `action == "halve_lr"` would correctly apply `lr_scale = 0.1`, but the action name suggests LR × 0.5 — confusing for future readers and source of potential silent bugs. The spec/code/test are internally consistent on the misnomer (all three agree `action = "halve_lr"` + `lr_scale = 0.1`), but the action name is wrong relative to wayfinder L249 init decision. The rename to `div_lr_10` aligns action name with actual math.

**🟡 Finding 2 (MEDIUM) — `loss_spike_defense` TDD closure gap**. `test_loss_spike_defense_phase3plus` uses literal `5.0 > 2.5` without explicit `pytest.approx(2.5, abs=1e-12)` to spec closed-form `LOSS_SPIKE_RATIO = 2.5`. If `LOSS_SPIKE_RATIO` is retuned to `3.0`, the test still passes (`5.0 > 3.0` ⇒ True), silently dropping the spec contract. Per CLAUDE.md §6 last bullet, every spec closed-form numeric MUST have a `pytest.approx` direct guard.

**🟡 Finding 3 (MEDIUM) — `loss_spike_defense` strict-greater-than boundary unguarded**. Spec L208 item (5) defines `L_task > ratio · L_task_ema` with STRICT greater-than (per `>` not `≥`). No test pins the boundary case `L_task == ratio · L_task_ema` → returns False. A regression weakening `>` to `>=` would silently change behavior at the equality boundary.

## What Changes

- **`openspec/specs/decompmoe-skeleton/spec.md` L208** (Requirement body, `nan_ladder` signature): rename Literal type member `halve_lr` → `div_lr_10`. The full text becomes `nan_ladder(consecutive_nan) -> tuple[str, float, bool] returning (action, lr_scale, halt) where action ∈ {"skip", "div_lr_10", "halt"} for counts (1, 3, 10) respectively`.
- **`openspec/specs/decompmoe-skeleton/spec.md` L218-219** (Scenario `NaN ladder default at consecutive_nan=0`, the c ∈ [3, 9] tier entry): rename `("halve_lr", 0.1, False)` → `("div_lr_10", 0.1, False)`.
- **`src/decompmoe/safeguards.py` L8** (module docstring, "3 → halve_lr"): rename to `3 → div_lr_10`.
- **`src/decompmoe/safeguards.py` L53** (NaNAction Literal type): rename `"halve_lr"` → `"div_lr_10"`.
- **`src/decompmoe/safeguards.py` L62** (nan_ladder return for c ∈ [3, 9]): rename action `"halve_lr"` → `"div_lr_10"`.
- **`tests/test_safeguards.py`**:
  - `test_nan_ladder` (3 exact-tuple assertions): update `"halve_lr"` → `"div_lr_10"` in c=3 expected tuple.
  - `test_nan_ladder_lr_scale_equivalence_to_lr_div_10` (action assertion): update `action == "halve_lr"` → `action == "div_lr_10"`.
  - `test_loss_spike_defense_phase3plus`: add explicit `safeguards.LOSS_SPIKE_RATIO == pytest.approx(2.5, abs=1e-12)` closure-form guard so test input `2.5` is anchored to spec, not magic number.
  - **NEW** `test_loss_spike_defense_at_ratio_boundary_returns_false`: assert `loss_spike_defense(L_task=2.5, L_task_ema=1.0, phase=3) is False` to pin strict `>` boundary equality rejection.
- **NOT BREAKING at call site**: a regression search shows the literal `"halve_lr"` string is used ONLY inside `safeguards.py` (definition) + `tests/test_safeguards.py` (test assertions). No external call site pattern-matches on this action. The `lr_scale` value (0.1) is unchanged, so callers using the lr_scale numerical value continue to work without changes.

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `decompmoe-skeleton`：Requirement `Five Numerical Safeguard Helpers` 下 Scenario `NaN ladder default at consecutive_nan=0` body 中的 Literal type member name (`halve_lr` → `div_lr_10`)。同步修改 `src/decompmoe/safeguards.py` 的 `NaNAction` Literal type 与 `nan_ladder` 返回值；同步修改 `tests/test_safeguards.py` 的两个测试断言。无 Scenario 数量变化，无 Requirement 数量变化，**但** NaNAction type 是 public API（被 `__all__` 导出），属于 spec-level 行为变更。

## Impact

- **Spec 影响**：`openspec/specs/decompmoe-skeleton/spec.md` 内 1 个 Requirement 下 1 个 Scenario body 文字 + 1 处 Requirement body 的 Literal type 成员名。无结构性变更。
- **Code 影响**：`src/decompmoe/safeguards.py` 内 4 处同步：module docstring L8、`NaNAction` Literal type L53、`nan_ladder` 返回 tuple L62。**返回值数值不变**（仍 `0.1`），仅字符串 action 名变更。
- **Test 影响**：`tests/test_safeguards.py` 内 2 个 test 字符串更新 + 1 个 test 加 1 行 closure-form guard + 1 个新 test（边界守护）。运行行为闭式断言不变。
- **CI 影响**：`/opsx:archive` 前置条件 `scripts/lint_no_source_field_drift.py` 和 `scripts/lint_no_dead_defensive.py` 须 `exit=0`。Source 字段未动（L206/L251 已含 `wayfinder/tickets/A6a-2.md`），lint 期望通过。
- **跨 spec 影响**：`openspec/specs/wayfinder/spec.md` L249 写 "LR ÷ 10"——已经准确，本次 change 与 wayfinder init decision 字面对齐。
- **回滚友好**：纯字面 rename，回滚 = 反向 rename。
- **API break scope**：`NaNAction` Literal type 在 `__all__` 导出（`from decompmoe.safeguards import NaNAction`）；module docstring + return type annotation 都暴露 `"halve_lr"` 字面。仓库内 grep 显示仓库内无第三方调用方 pattern-match `"halve_lr"`，仅 tests + safeguards.py 自己用——本次 archive 后 grep 应返回 0 匹配（确认 rename 完整）。
