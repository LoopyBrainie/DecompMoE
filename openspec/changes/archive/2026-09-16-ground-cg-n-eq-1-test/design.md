## Context

当前 `wayfinder` spec 的 Req 20 (CG) 已包含 Scenario "CG zero-gradient invariance"(L434)与 "CG positive homogeneity"(L438),但**缺失 `numel()==1` 边界**场景。Archived delta `2026-09-05-add-cg-n-eq-1-test/specs/wayfinder/spec.md`(2026-09-05 期间)已起草 ADDED Requirement `CG n=1 boundary behavior` + 3 个 Scenario(positive / negative / zero 单元素输入),但 archive 流程未把该 delta 同步到 active spec。后续审计(`/code-review max` LOW 7)再次指出该 delta 仅存活在 archive 目录,`tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` docstring 反链 delta 路径而非 active spec 锚点,违反 CLAUDE.md §2 真相源层级。

**2026-09-16 实际 apply 路径(commit `b8c149c`,作为 `2026-09-16-add-cg-n-eq-1-test` apply 阶段一次性完成):**
- ADDED Requirement `CG n=1 boundary behavior` + 4 个 Scenario(positive / negative / zero 1D + multi-dim `numel()==1`)同步入 active spec
- 新 anchor `<a id="req-34">` 落在 L442(在 "CG positive homogeneity" Scenario L440 与原 `<a id="req-21">` 锚之间)
- Source 字段采用 lint-compliant 格式,primary reverse-link 指向 `wayfinder/tickets/A8-2.md`(per `scripts/lint_no_source_field_drift.py` "first item MUST be per-capability primary ticket lineage")
- `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` 在 L171-211 定义(38 行,5 个 `pytest.approx(abs=1e-12)` 断言),docstring L174 直接写 `Spec anchor: \`openspec/specs/wayfinder/spec.md\` Req 20 (CG) ... + ADDED Requirement "CG n=1 boundary behavior"`(active spec 锚点,非 archive-only delta 路径)
- ground 原 propose 的"surgical edit L179 docstring"工作被 b8c149c 一次性完成,不再需要

本 change 当前定位(post-adjustment):**planning artifacts 与现实对齐的 audit record**。所有 apply 工作已由 `b8c149c` 完成;本 change 的 artifacts 现在反映 b8c149c 后的最终状态(`req-34` anchor / 4 Scenarios / lint-compliant Source / test 函数 L171-211 / 5 个断言 / 188 passed)。

## Goals / Non-Goals

**Goals:**
- 把 ADDED Requirement `CG n=1 boundary behavior`(4 个 Scenario)接入 active `wayfinder` spec,与现有 Req 20 (CG) Scenarios 共存 ✓
- 让 `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` docstring(L174)反链 active spec 锚点 ✓
- 保留 verbatim ADDED Requirement 文案与 `abs=1e-12` 浮点闭式对账容差(`governance/spec.md` req-gov-1 obligation 2:单元素 gradient tensor 无整数闭式对应)✓
- 实际 apply 范围扩展到 multi-dim numel==1(b8c149c 新增第 4 个 Scenario,覆盖 `g.shape ∈ {1, [1,1], [1,1,1]}`),体现 dimension-agnostic L2 norm 性质 ✓

**Non-Goals:**
- 不修改 production code(`metrics.py::CG` 仍为 `torch.linalg.norm(grad)`,abs=1e-12 测试已 PASS) ✓
- 不修改任何 archive 目录物理文件(`2026-09-05-` 与 `2026-09-16-` 两条 add-cg-n-eq-1-test archive,append-only) ✓
- 不收紧 `test_voronoi_residual_below_1e_minus_9` 的 1e-9 witness(spec 强制条款,out-of-scope)
- 不删 `test_sphere.py:127` 行内冗余 `import math`(独立 trivial edit)

## Decisions

### Decision 1: Verbatim carryover of original delta + supersession expand

**Choice**: ADDED Requirement 文案基础 verbatim 自 archived delta (`2026-09-05-add-cg-n-eq-1-test/specs/wayfinder/spec.md`),但 b8c149c apply 时扩展为 4 个 Scenario(新增 multi-dim `numel()==1`)

**Rationale**:
- 原 3 个 Scenario(positive / negative / zero 1D)是 audit review LOW 7 / `/code-review max` LOW 7 认定 spec-correct 的最小子集
- multi-dim numel==1 Scenario 是 b8c149c apply 时的合理扩展:同一 `numel()==1` 边界条件,覆盖 rank ∈ {1, 2, 3},验证 L2 norm dimension-agnostic
- 扩展不偏离已审查的 audit 结论(无任何 spec 数值变更,仍为 `abs(g.item())`,容差仍 `abs=1e-12`)
- 满足 CLAUDE.md §6 第 8 条 "test 必须验证 spec 声称值":每条 spec 数值都有 `pytest.approx(..., abs=1e-12)` 闭式对账

**Alternatives considered**:
- *仅 verbatim 3 个 Scenario*(原 ground propose):拒绝:b8c149c 实际已扩展,planning artifacts 与现实 drift
- *重写文案 + 收紧容差*(如 abs=1e-15):拒绝:偏离已审查的 audit 结论,无证据支持容差变更
- *Verbatim + 4 Scenario supersession expand* ✅ chosen:既保留 audit-correct 基础,又对齐 apply 后的现实

### Decision 2: Active spec 锚点直接写入,无需 surgical edit

**Choice**: `test_cg_n_eq_1_returns_magnitude` docstring 直接写 active spec 锚点(由 b8c149c apply 时一次性完成),不依赖 ground 二次 surgical edit

**Rationale**:
- 原 ground propose 的 "把 delta 路径反链改为 active spec 锚点" surgical edit 假设 test 已存在并以 delta 路径反链——但 b8c149c 在 add-cg-n-eq-1-test apply 时**一次性**写好了 test + correct anchor,无需 ground 介入
- 测试断言体(5 个 `pytest.approx(abs=1e-12)`)与 spec 数值严格对应,改动 docstring 锚点字符串不会影响测试行为
- 不存在 "Removed g_pi = math.pi case" rationale 块(ground 原 propose 基于已 rolled-back 的 `commit 5416f93` 时代 test docstring;该 rationale 在 `commit 7929770 @fix(audit)` 时被删除,b8c149c apply 时未恢复)
- 符合 CLAUDE.md §3 Surgical Changes 原则:b8c149c 一次性写对 docstring 比 ground 二次 surgical edit 更省 churn

**Alternatives considered**:
- *Surgical edit on L179*(原 ground propose):已过期——docstring 实际在 L174,且 b8c149c 已写正确锚点
- *Full docstring rewrite*:拒绝:扩大 diff,无必要
- *No-op*(test 已正确) ✅ chosen:b8c149c 已完成

### Decision 3: Keep both add-cg-n-eq-1-test archives physically untouched

**Choice**: 不删除 / 不修改 `openspec/changes/archive/2026-09-05-add-cg-n-eq-1-test/` 与 `openspec/changes/archive/2026-09-16-add-cg-n-eq-1-test/` 任何文件,本 change 在 Source 字段引用 archive 路径

**Rationale**:
- OpenSpec archive 是 append-only 历史日志,删除 archived change 会破坏 audit trail
- 两条 archive 提供完整的演化 lineage:`2026-09-05-`(原 proposal,3 Scenario,无 Source 字段)→ `2026-09-16-`(apply 阶段,b8c149c,4 Scenario,lint-compliant Source)→ `2026-09-XX-ground-cg-n-eq-1-test/`(本 change,post-apply no-op audit record)
- Source 反链保留双 archive 路径,review 时可推断完整 supersession chain

**Alternatives considered**:
- *Delete archived delta*:拒绝:OpenSpec convention 禁止;丢失 audit trail
- *Mark superseded in proposal*:已采纳,在本 proposal "Supersession Note" 段显式声明
- *Keep both archives untouched* ✅ chosen:OpenSpec convention + audit trail

## Risks / Trade-offs

- **[Risk] ADDED Requirement 与 parent Req 20 的层级关系混乱** → **Mitigation**: 新 anchor `<a id="req-34">` 物理上落在 Req 20 cluster (L434-440 Scenarios) 与原 req-21 anchor 之间(L464),渲染时按顺序展示,清晰分组;ADDED Requirement 文本明确"dimension-agnostic ... `g.numel() == 1`",承接 Req 20 的 `CG = ‖∇‖₂` 定义。

- **[Risk] Source 字段格式漂移** → **Mitigation**: 本 change delta(Source field)的 primary reverse-link 为 `wayfinder/tickets/A8-2.md`,对齐 active spec 现存格式与 `scripts/lint_no_source_field_drift.py` "first item MUST be per-capability primary ticket lineage" 要求;`lint_no_source_field_drift.py` exit=0 验证。

- **[Risk] 测试基线 assertion 数与 ground 原 propose 不一致**(3 → 5)→ **Mitigation**: b8c149c 扩展的 2 个断言(2D positive、3D negative)同样是 `pytest.approx(abs=1e-12)` 浮点闭式对账,无容差放宽,行为不变;5 个断言全部 PASS;`uv run pytest tests/` 全套 188 passed 无回归。

- **[Risk] archived delta 物理未动 → 后续 review 可能误判两个 change 的关系** → **Mitigation**: 本 proposal "Supersession Note" 段 + spec delta 的 `**Source:**` 都显式声明 supersession chain(archived delta 路径 + `/code-review max` LOW 7 + `b8c149c` commit ref);review 时 grep "CG n=1" 在 archive/(3 处) 和 spec/(1 处) 都能命中,可推断完整 lineage。

## Migration Plan

1. **Apply 阶段**(已完成,by `commit b8c149c` 2026-09-16):
   - ADDED Requirement `CG n=1 boundary behavior` + 4 Scenarios 同步入 active `openspec/specs/wayfinder/spec.md`(L442-463)
   - 新 anchor `<a id="req-34">` 写入
   - `test_cg_n_eq_1_returns_magnitude` 在 `tests/test_metrics.py` L171-211 定义,docstring L174 写 active spec 锚点
   - 验收基线:`uv run pytest tests/ -v` → 188 passed, 1 warning;两 lint gate exit=0
2. **本 change post-apply no-op**(当前步骤):
   - planning artifacts (proposal.md / design.md / tasks.md / spec delta) 已更新为反映 b8c149c 后状态
   - `openspec validate ground-cg-n-eq-1-test --strict` 通过(delta 与 main spec 一致)
   - `openspec sync-specs ground-cg-n-eq-1-test` 判定 idempotent no-op(无需 main spec 改写)
3. **Archive**: `openspec archive ground-cg-n-eq-1-test --yes` → change 移入 `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/`;两条 add-cg-n-eq-1-test archive (`2026-09-05-` 与 `2026-09-16-`) 物理均未动
4. **Rollback**(若需要):OpenSpec archive 是单向操作,无内置 rollback;手动:
   - `git revert b8c149c`(撤销 add-cg-n-eq-1-test apply)
   - 删除 `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/`(如需重做本 change)

## Open Questions

(无 —— 所有 spec/approach/task breakdown 决策均已落定,b8c149c 已 apply,本 change 为 post-apply audit record)