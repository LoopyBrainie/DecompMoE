## Why

`openspec/specs/decompmoe-skeleton/spec.md` 在 `should_resurrect semantic interpretation (per-step vs avg-window)` 场景的"Mathematical equivalence disambiguation"段落中写反了数学命题方向，并把"per-step ⊊ avg-window"这条**正确**的严格包含关系错误地断言为"they are not nested by inclusion"。同一段内同时出现"flag_step ⟹ flag_avg is not universally true"和"any history flagged by per-step is also flagged by avg-window only when…"两条互相否定的命题，导致该段自相矛盾，初等代数可直接证伪前者。该 spec 又把这条数学错误传染给了两个外部制品——(a) `Beta Parameterization Operational Domain` 需求里把 `MAX_GRAD_PER_GAMMA_PHASE4` 的引用行号记成陈旧的 `:46`（实际公开常量在 `src/decompmoe/beta.py:50`，L46 是 INTERNAL 中间常量），(b) `tests/test_safeguards.py` 守护测试的函数名 `test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history` 写成"superset"方向，与 docstring 三处的 `per-step ⊊ avg-window` 完全相反。这次修复同时校正 spec 命题方向、spec 行号、test 函数名，使 spec ↔ code ↔ test 在 `per-step ⊊ avg-window` 这一数学事实上三方自洽。

## What Changes

- **`openspec/specs/decompmoe-skeleton/spec.md` L244-256（"Five Numerical safeguards helpers" Scenario `should_resurrect semantic interpretation` 内的 "Mathematical equivalence disambiguation" 块）**：重写 L248 的命题方向，把"`flag_step ⟹ flag_avg` is **not** universally true (counterexample below)"改为"`flag_step ⟹ flag_avg` IS universally true (by elementary algebra: ∀j: H[j][i] < T ⇒ Σ H[j][i] < consec·T ⇒ mean < T); the non-universal direction is `flag_avg ⟹ flag_step`, demonstrated by the counterexample below"；把"they are not nested by inclusion"改为"`per-step` is strictly tighter than `avg-window` (per-step ⊊ avg-window): per-step triggers only on histories that also trigger avg-window, but not conversely"；清掉后段"only when the avg-window condition holds on the same history"的矛盾修饰。
- **`openspec/specs/decompmoe-skeleton/spec.md` L423（"Beta Parameterization Operational Domain" 需求正文）**：把 `src/decompmoe/beta.py:46` 改为 `src/decompmoe/beta.py:50`（指向真正承载 `MAX_GRAD_PER_GAMMA_PHASE4` 的公开导出常量行；L46 是 `_MAX_GRAD_BETA_PHASE4_INTERNAL`，下划线前缀、不在 `__all__`）。
- **`tests/test_safeguards.py` L677（`test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history`）**：把函数名中的 `strict_superset` 改为 `strict_subset`（与 docstring L678/L703/L745 的 `per-step ⊊ avg-window` 一致，与修复后的 spec 数学事实一致）。**NOT BREAKING**（无外部调用方；纯测试函数名改名，运行行为不变）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `decompmoe-skeleton`：
  - Requirement "Five Numerical Safeguard Helpers" 的 Scenario `should_resurrect semantic interpretation (per-step vs avg-window)` 内"Mathematical equivalence disambiguation"段：修正 `flag_step ⟹ flag_avg` 命题方向与嵌套关系表述。
  - Requirement "Beta Parameterization Operational Domain — D1 Module-Level Constants" 内对 `MAX_GRAD_PER_GAMMA_PHASE4` 的行号引用：从 `:46` 更新为 `:50`。

## Impact

- **Spec 影响**：`openspec/specs/decompmoe-skeleton/spec.md` 内两处需求/场景文本。无结构性变更（无新增/删除 Requirement，无 Scenario 数量变化），属于**纯文本校正**。
- **Code 影响**：`src/decompmoe/` 下**无任何代码改动**（数学命题在 spec 文本层修正，不引入行为变更）。`src/decompmoe/beta.py` 行号变动属于"reference to existing artifact"，常量位置不动。
- **Test 影响**：`tests/test_safeguards.py` L677 函数名改名（`strict_superset` → `strict_subset`），运行行为与闭式断言不变；其它测试（`test_should_resurrect_current_per_step_semantic_pinned` L634 等）不受波及。
- **CI 影响**：`/opsx:archive` 前置条件（`lint_no_dead_defensive.py`、`lint_no_source_field_drift.py`）须 `exit=0`；本次修正不涉及 `Source:` 反链字段的破坏（spec 已正确指 `wayfinder/tickets/A6a-2.md` + `change fix-openspec-doc-bugs design.md (Decision 7)`），lint 期望通过。
- **跨 spec 影响**：`openspec/specs/wayfinder/spec.md` L249 的 `f_i^avg < 1/(2·N_e)` 文字与本次修正**完全自洽**（per-step 解读与 wayfinder L249 的"200 consecutive steps"措辞契合），无需修改。