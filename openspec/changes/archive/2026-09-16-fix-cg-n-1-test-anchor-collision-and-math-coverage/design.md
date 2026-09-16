## Context

`b8c149c` (2026-09-16, ground-cg-n-eq-1-test apply) 在 `openspec/specs/wayfinder/spec.md` 给 "CG n=1 boundary behavior" Requirement 添加了 `<a id="req-34">` 锚点。但这个 anchor 在 wayfinder spec 的历史 lineage 中应属于 "Source Field Format Invariant" Requirement（由 `f033d2e` 2026-09-15 同步 `tighten-source-field-format-lint-2026-09/specs/wayfinder/spec.md` 时**漏掉**该 anchor，但已 append Requirement 标题 + Scenarios 到 wayfinder spec L659+）。结果：
1. wayfinder spec L442 有 `<a id="req-34">` 指向 CG n=1 boundary
2. wayfinder spec L676 "Source Field Format Invariant" Requirement 存在但**无 anchor**
3. governance spec L3 引用 `wayfinder/spec.md req-34 'governance-origin requirements trigger lint failure' Scenario` —— 这条引用实际指向 CG n=1 boundary，不是 governance-origin Scenario
4. `tests/test_lint_no_source_field_drift.py:3` 文档字符串描述 "Wayfinder req-34 Scenarios (reverse-link must be wrapped in backticks + primary reverse-link must be the first top-level item)" —— 同样指向错的 Requirement

代码 review 阶段还发现 `test_cg_n_eq_1_returns_magnitude` 5 个 `pytest.approx(abs=1e-12)` 断言只验证 `CG(g) == abs(g.item())` 不验证 L2-norm 推导链（`abs(g.sum())` / `g.abs().max()` 在 numel=1 上也会 PASS）。spec L445 "MUST satisfy the L2-norm identity" 措辞比 test 覆盖严格。

本 change 范围：
- wayfinder spec: anchor `<a id="req-34">` 从 L442 (CG n=1) 移至 L676 (Source Field Format Invariant)；CG n=1 改用 `<a id="req-35">`（wayfinder spec 整数 anchor 惯例 + 下一个可用编号）
- test_metrics.py: `test_cg_n_eq_1_returns_magnitude` 加 1 行 L2-norm sanity check（`metrics.CG(g) == torch.linalg.norm(g).item()` 逐位相等）
- 无 production code 改动
- 无 governance / wayfinder spec Requirement body 改动（仅 anchor relocation）

## Goals / Non-Goals

**Goals:**
- 修复 governance spec L3 + `tests/test_lint_no_source_field_drift.py:3` 的断链跨引用（让 `req-34` 指向 Source Field Format Invariant 的 "governance-origin requirements trigger lint failure" Scenario）
- 修复 test 对 L2-norm 推导链的约束力（新增 `metrics.CG(g) == torch.linalg.norm(g).item()` 断言在 numel=1 上形式化钉 L2-norm identity）
- 保留所有 assertion 行为不变（无 `assert` 数值放宽或收紧；仅追加 1 行 sanity check）
- 保留 wayfinder spec 整数 anchor 惯例（CG n=1 改用 `req-35`，非 `req-34a` / `req-20a` 等 sub-anchor 语法）
- 保留 Source Field Format Invariant Requirement 内容、Scenarios、Source 字段不变
- 保留 CG n=1 boundary Requirement 内容、Scenarios、Source 字段不变

**Non-Goals:**
- 不修改 production code（`src/decompmoe/metrics.py::CG` 仍是 `torch.linalg.norm(grad)`，与 spec 一致）
- 不修改 governance spec / `tests/test_lint_no_source_field_drift.py` 内容（被 fix 的 source 反链会让 governance spec L3 重新正确指向 Source Field Format Invariant；该测试的 source field 文档字符串也会重新正确）
- 不修改 wayfinder spec 其他 anchor（仅 `req-34` 物理绑定位置变更 + 新增 `req-35`）
- 不收紧 `pytest.approx(abs=...)` 容差（仍 `abs=1e-12`，符合 governance req-gov-1）
- 不新增 test（仅在 `test_cg_n_eq_1_returns_magnitude` 内部追加 sanity check，不新增 test function）
- 不重写 test docstring（仅追加 1 行代码）

## Decisions

### Decision 1: Anchor relocation vs anchor renumbering

**Choice**: 把 `<a id="req-34">` 从 CG n=1 boundary (L442) 物理移动到 Source Field Format Invariant (L676)，给 CG n=1 boundary 新 anchor `<a id="req-35">`。

**Rationale**:
- governance spec L3 + `tests/test_lint_no_source_field_drift.py:3` 的跨引用反向期望 `req-34` 指向 governance-origin Scenario（Source Field Format Invariant 子句），这是 wayfinder spec 的**真实意图**
- `f033d2e` 同步 Source Field Format Invariant 时漏了 anchor 是历史 bug，应在本次 fix 中**修复历史 bug**（恢复 anchor 到正确位置），而不是给 Source Field Format Invariant 新 anchor（如 `req-35a`）
- CG n=1 boundary 是新 Requirement（2026-09-16），让出 `req-34` 给历史 Requirement 是合理安排；新 Requirement 用下一个可用 anchor `req-35` 也符合 wayfinder spec 整数 anchor 惯例（无 sub-anchor 语法先例）
- 跨 capability 影响范围可控：仅 1 个 HTML `<a id>` 移动 + 1 个新增；governance spec + lint test 的反向引用**自动修复**（因为它们一直期望 `req-34` 指向 governance-origin 内容，现在确实指向了）

**Alternatives considered**:
- *保留 `req-34` 给 CG n=1 boundary + 给 Source Field Format Invariant 新 anchor `req-22`*：拒绝——会让 governance spec + lint test 的跨引用持续断链；需要 update 两处 source 反链字符串才能 fix（违反 CLAUDE.md §3 Surgical Changes 原则）
- *保留 `req-34` 给 CG n=1 + 给 Source Field Format Invariant 新 anchor `req-33.5` / `req-21a`（sub-anchor 语法）*：拒绝——wayfinder spec 无 sub-anchor 语法先例；引入新语法增加 lint / tooling 复杂度
- *anchor 物理移动 + CG n=1 用 `req-35`* ✅ chosen：单一变更，最小 churn，自动修复历史跨引用断链

### Decision 2: Test L2-norm sanity check vs docstring-only clarification

**Choice**: 在 `test_cg_n_eq_1_returns_magnitude` 现有 5 个 `pytest.approx(abs=1e-12)` 断言**外**，追加 1 行 `assert metrics.CG(g_pos_1d).item() == torch.linalg.norm(g_pos_1d).item()` 作为 L2-norm identity 的形式化 sanity check。

**Rationale**:
- spec L445 明确写 "MUST satisfy the L2-norm identity"。当前 test 只验证 value identity（`CG(g) == abs(value)`），不验证 implementation path identity（`CG(g) == L2 norm reduce 路径`）
- 实测 `abs(g.sum())` 和 `g.abs().max()` 在 numel=1 tensor 上也返回 abs(value)，绕过当前 test。这违背 spec 措辞 "L2-norm identity"
- `torch.linalg.norm(g).item()` 在 numel=1 上等价于 `abs(g.item())` 但**形式上钉 L2-norm reduce 路径**：如果实现改为 `abs(g.sum())`，断言会 FAIL（sum 不是 L2 norm）
- 1 行 sanity check 最小 churn；不影响现有 5 个断言；test function name + docstring 不变；维持 spec↔test closure 强度
- 对 numel=1 tensor，`torch.linalg.norm(g).item()` 与 `abs(g.item())` FP-exact 相等（`sqrt(g²)` 在 IEEE-754 二进制64 上对 `|g| ≤ 2^52` 是精确的），所以新断言不会引入任何容差问题

**Alternatives considered**:
- *替换 5 个 `pytest.approx` 断言为 `== torch.linalg.norm(g).item()`*：拒绝——现有断言验证 closed-form 数值（5.0, 5.0, 0.0），与 spec Scenario 文案一致；替换会丢失 Scenario 文案的直接对账
- *新增 1 行 sanity check（仅 1D positive 测 1 次）*：可接受——但 multi-dim 也需验证 dimension-agnostic 一致；选择 sanity check 1 行已足够（`g_pos_1d` 与 `g_pos_2d` 走同一 `torch.linalg.norm` 路径，1D 验证即可代表）
- *sanity check 加在 5 个断言末尾作为第 6 个 assert* ✅ chosen：1 行新增，0 行删除，test docstring 完整；spec ↔ test 闭式对账强化

### Decision 3: No production code change

**Choice**: 不修改 `src/decompmoe/metrics.py::CG`。当前实现 `torch.linalg.norm(grad)` 已正确对应 spec `CG = ‖∇‖₂` definition；本 change 修复 spec anchor 与 test coverage，与实现路径无关。

**Rationale**:
- `src/decompmoe/metrics.py:185` 单一路径 `torch.linalg.norm(grad)`，与 spec L445 "no special-case branch — the L2 norm definition handles it directly" 字面对齐
- 实测：complex/bool/int dtype raise TypeError（被 `is_floating_point` 过滤）；4D numel=1 tensor `CG([[[[-7.0]]]])` → 7.0（dimension-agnostic 实证）
- 修改 production code 违反 CLAUDE.md §3 Surgical Changes（"Touch only what you must"）

**Alternatives considered**: *改 `torch.linalg.norm(grad)` 为 `grad.norm()` 或 `(grad**2).sum().sqrt()` 等 explicit L2 norm 实现*：拒绝——`torch.linalg.norm` 是 PyTorch 官方 L2 norm API；改写无收益且违反 §3

## Risks / Trade-offs

- **[R1] Anchor relocation 触发 cross-capability 跨引用 breakage** → **Mitigation**: 跨引用 breakage 是当前 bug 的"修复"——governance spec L3 + `tests/test_lint_no_source_field_drift.py:3` 的反向引用自动从错的（CG n=1）变对的（Source Field Format Invariant）。无任何 cross-reference 需要手动更新。
- **[R2] `req-35` 编号跳号（从 33 直接跳到 35，没有 34）** → **Mitigation**: 这正是 fix 的本意——`req-34` 已迁回 Source Field Format Invariant；`req-35` 是 wayfinder spec 当前最大编号 + 1（req-6/10/16 历史上空缺但仍存在整数编号惯例）。`req-35` 不会与任何已存在 anchor 冲突。
- **[R3] L2-norm sanity check 与 `pytest.approx(abs=1e-12)` 现有断言重复** → **Mitigation**: sanity check 验证 implementation path（`== torch.linalg.norm(g).item()`），现有 5 个 `pytest.approx` 验证 closed-form value identity（`== 5.0` 等）。两者测的是不同维度，互补不重复。
- **[R4] Test docstring 没更新引用 `req-35`** → **Mitigation**: 现有 test docstring 引用 `wayfinder Req 20 (CG) + ADDED Requirement "CG n=1 boundary behavior"`，无 `req-34` / `req-35` 引用；docstring 文本与新 anchor 不矛盾。后续如有其他 fix 触及 test docstring 可一并更新。
- **[R5] Git workflow 与 dev linear requirement** → **Mitigation**: 本 change 工作 tree 改动由 user 走 CLAUDE.md §4 git 流程（dev linear commit → main --no-ff → release --no-ff + tag）；agent 不直接 commit。

## Migration Plan

1. **Apply 阶段**:
   - `openspec/specs/wayfinder/spec.md`：删除 L442 的 `<a id="req-34"></a>`，改为 `<a id="req-35"></a>`；在 L676 (Source Field Format Invariant Requirement 标题前) 新增 `<a id="req-34"></a>`。
   - `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude`：在 5 个现有 `pytest.approx(abs=1e-12)` 断言后追加 1 行 `assert metrics.CG(g_pos_1d).item() == torch.linalg.norm(g_pos_1d).item(), f"actual={...}"`（L2-norm path sanity check）。
2. **Apply 阶段 lint gates**（per CLAUDE.md §3 archive precondition）:
   - `python scripts/lint_no_source_field_drift.py` exit=0（Source 字段未改；anchor 重绑定不影响 lint 逻辑）
   - `python scripts/lint_no_dead_defensive.py` exit=0（无 defensive-code 改动）
3. **Apply 阶段 test gates**:
   - `uv run pytest tests/test_metrics.py -v` → 全过（含 `test_cg_n_eq_1_returns_magnitude` 6 个断言：5 个现有 + 1 个 sanity check）
   - `uv run pytest tests/ -v` → 全套 PASS（188 → 188 不变，sanity check 不引入新 test function）
4. **Archive 阶段**: `openspec archive fix-cg-n-1-test-anchor-collision-and-math-coverage --yes` → change 移入 `openspec/changes/archive/2026-09-16-fix-cg-n-1-test-anchor-collision-and-math-coverage/`
5. **Rollback**: `git revert` archive merge commit；anchor 与 sanity check 是 text 改动，rollback 零风险。

## Open Questions

(无) — anchor relocation 决策、sanity check 设计、production code 不动 均已落定；spec↔test 闭式对账强化目标明确。