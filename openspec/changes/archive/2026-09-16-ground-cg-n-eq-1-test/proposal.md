## Why

`/code-review max` 对 `ground-cg-n-eq-1-test` change 自身的 spec-grounding audit 发现 **LOW 7**:`tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` docstring 反链 `openspec/changes/add-cg-n-eq-1-test/specs/wayfinder/spec.md`(archived delta),但该 delta 的 ADDED Requirement 从未 promote 进 active spec——`grep` `openspec/specs/wayfinder/spec.md` 全文 **零匹配** "CG n=1" / "boundary behavior"。后果:测试断言行为在 active spec 无 grounding,违反 CLAUDE.md §2 真相源层级("想修改 DecompMoE 行为,先改 OpenSpec spec")+ `/code-review max` LOW 7 原审查对 archived delta 的反 CLAUDE.md §2 警告。本 change 把 archived delta 的 ADDED Requirement verbatim 接入 active `wayfinder` spec,docstring 反链从 delta 路径改为 active spec 锚点——**零行为变更**(测试已 PASS),pure spec-grounding 修复。

## What Changes

- **`openspec/changes/ground-cg-n-eq-1-test/specs/wayfinder/spec.md`**(本 change 的 delta,apply 时同步入 active spec)**ADDED Requirement `CG n=1 boundary behavior`** + 4 个 Scenario(positive / negative / zero 1D 单元素 + multi-dim `numel()==1` 单元素,`CG(g) == abs(g.item())` 闭式对账,`abs=1e-12`)。Anchor: `req-34`(active `wayfinder` spec L442);parent requirement 为 `wayfinder` Req 20 (CG) `CG = ‖∇‖₂`(anchor `<a id="req-20">` at active spec L370)。Source: archived delta `openspec/changes/archive/2026-09-05-add-cg-n-eq-1-test/` + `wayfinder/tickets/A8-2.md`(Eight Metrics 设计 lineage,lint gate "first item MUST be per-capability primary ticket lineage")+ `tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude` + `/code-review max` LOW 7(audit trigger)。ADDED Requirement 文案、Scenario 标题、闭式数值自 archived delta 起逐步演化(原 delta 仅 3 个 1D Scenario;实际 apply 通过 `commit b8c149c` 扩展至 4 个 Scenario,新增 `multi-dim numel==1` 覆盖 `g.shape ∈ {1, [1,1], [1,1,1]}`)。
- **`tests/test_metrics.py`**(test 函数定义于 L171,docstring 锚点字符串于 L174):docstring 直接写 `Spec anchor: \`openspec/specs/wayfinder/spec.md\` Req 20 (CG) ... + ADDED Requirement "CG n=1 boundary behavior"`,从一开始就指向 active spec 而非 archive-only delta(apply 时不需要 ground 的二次 surgical edit,因为 `b8c149c` 一次性写好了正确反链)。test 含 5 个 `pytest.approx(..., abs=1e-12)` 断言:1D positive / 1D negative / 1D zero / 2D positive / 3D negative,每个断言失败消息嵌入 `f"actual={...}"`(`governance/spec.md` req-gov-1 obligation 4)。
- 无 code 改动(CG 实现 `torch.linalg.norm(grad)` 已正确;abs=1e-12 测试已 PASS)。

## Capabilities

### New Capabilities

(无)

### Modified Capabilities

- `wayfinder` — ADDED Requirement `CG n=1 boundary behavior`(4 个 Scenario 守护 `numel()==1` 输入的 L2 范数行为,dimension-agnostic)。逻辑上属于 active `wayfinder` Req 20 (CG) 的子需求;不破坏现有 Req 结构(原 Req 20 已有 Scenario "CG zero-gradient invariance" L434 / "CG positive homogeneity" L438,本 ADDED Requirement 填补 `numel()==1` 边界场景,新 anchor `req-34` 落在 L438 与 req-21 之间)。

## Impact

- 受影响文件(apply 已由 `commit b8c149c` 在 2026-09-16 一次性完成):
  - `openspec/specs/wayfinder/spec.md`(+23 行:ADDED Requirement `req-34` + 4 个 Scenario + lint-compliant Source)
  - `tests/test_metrics.py`(+38 行:`test_cg_n_eq_1_returns_magnitude` 5 个 `pytest.approx(abs=1e-12)` 断言 + docstring 锚点字符串)
- 不动:`openspec/changes/archive/2026-09-05-add-cg-n-eq-1-test/` 与 `openspec/changes/archive/2026-09-16-add-cg-n-eq-1-test/` 物理文件(OpenSpec archive append-only 历史日志)
- 反链:`/code-review max` LOW 7 审查结论;archived delta `2026-09-05-add-cg-n-eq-1-test/proposal.md`;archived delta `2026-09-16-add-cg-n-eq-1-test/`(本次 supersession);`CLAUDE.md §2` 真相源层级;active spec `wayfinder` Req 20 (CG) `req-20` L370 `CG = ‖∇‖₂`;`tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude`(L171-211)
- 验收基线(2026-09-16 commit `b8c149c` post-commit baseline):
  - `openspec validate ground-cg-n-eq-1-test --strict` 通过(本 change delta 与 active spec 一致,no drift)
  - `grep -A2 "CG n=1 boundary" openspec/specs/wayfinder/spec.md` 命中 ADDED Requirement 标题 + 4 个 Scenario 标题
  - `uv run pytest tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude -v` 5 个断言(1D pos/1D neg/1D zero/2D pos/3D neg)abs=1e-12 全部 PASS
  - `uv run pytest tests/ -v` 全套 188 passed,1 warning(`pytest-asyncio` 无关警告,与本 change 无关)
- 无破坏性变更:pure spec grounding + 1 个新增 test,行为不变。
- Scope 排除:
  - ❌ 不修改 production code(`metrics.py::CG` 实现不变)
  - ❌ 不动任何 archive 目录(append-only)
  - ❌ 不收紧 `test_voronoi_residual_below_1e_minus_9` 的 1e-9 witness(独立 finding,out-of-scope)
- 不引入新依赖。

## Supersession Note (2026-09-16)

本 change (`ground-cg-n-eq-1-test`) 的原 apply scope 已在 `2026-09-16-add-cg-n-eq-1-test` apply 时由 `commit b8c149c` 一次性完成,且实际 apply 范围**超出** ground 原 proposal(从 3 个 Scenario 扩展到 4 个,新增 multi-dim numel==1 Scenario;从 3 个 test assertion 扩展到 5 个,新增 2D positive 与 3D negative 闭式对账)。本 change 现调整为 **post-apply no-op**:仅做规划 artifacts 与现实对齐(proposal.md / design.md / tasks.md / spec delta 更新为反映 b8c149c 后状态的最终形态),无进一步 apply 工作。Archive 时 `openspec sync-specs` 会判定 delta 与 main spec 一致(idempotent no-op),无需重写 active spec。