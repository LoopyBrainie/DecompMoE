# fix-wayfinder-spec-anchor-coverage-l195-l351

## Why

`openspec/specs/wayfinder/spec.md` 当前 33 个 `### Requirement:` 标题但只有 31 个 `<a id="req-N"></a>` anchor — 缺失 2 个 anchor：`No Shared Expert (Pure Geometric Routing)` 在 L195 与 `Prefill And Decode Share The Same Algorithm` 在 L351。两者均违反 `CLAUDE.md` §6 第 8 条 hard constraint "spec anchor 不全：`wayfinder/spec.md` 与 `decompmoe-skeleton/spec.md` 的每个 Requirement MUST 在首行设独立 anchor `<a id="req-N"></a>`，**100% 覆盖**"。

本缺陷由 cycle-N+1 audit-verification loop 经 Python reviewer Agent 在 commit `d71115d` 的全面 review 中识别（review session id `mvs_e69331c3ba70428cb05eb809c5886c03`，2026-09-25 finding `L4-F1`）。它是 pre-existing drift，不是 `d71115d` 引入的 — 历史追溯 `openspec/changes/archive/2026-08-18-introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` L132 当时给 `No Shared Expert` 设了 `<a id="req-10">`（与现行 `req-10 = Territory Seeding` 位置重叠）；后续 spec 演化时把 `No Shared Expert` 推到 L195 但 anchor 没跟随迁出 — 形成当前 gap。

## What changes

- **`openspec/specs/wayfinder/spec.md` L195** — 在 `### Requirement: No Shared Expert (Pure Geometric Routing)` 前一行插入 `<a id="req-21"></a>`。该 anchor 编号选择 (a) 是最小可用整数 slot (req-16 已为本 change 的 L351 占用，req-21/25/27/33 是历史 skipped slots)；(b) 避免 cascade renumbering — 若把 L195 改为 `req-10` 则 req-10 ~ req-36 共 21 个 anchor 须同时 +1 + 全外部 grep 同步更新（per Memory lesson "Multi-surface spec line-number references drift together" 风险高）。
- **`openspec/specs/wayfinder/spec.md` L351** — 在 `### Requirement: Prefill And Decode Share The Same Algorithm` 前一行插入 `<a id="req-16"></a>`。该 anchor 编号是结构性 natural slot（嵌在 req-15 L339 与 req-17 L361 之间，本身就是历史演化留下的空缺），零 cascade 风险。

**NOT changed**:
- 任何 Source 反链 (`wayfinder/tickets/A5-2.md` for L195; `wayfinder/tickets/A7-1.md` for L351) — 已经是有效的 ticket-name 反链，无需改。
- 任何 ticket / map.md / src/ / tests/ 引用 — 经验证所有外部 surface 引用 **by ticket name** (A5-2 / A7-1)，**不** by spec anchor。新 anchor 不会让任何引用变 stale（反而让未来想要 by-anchor 引用的 surface 可以指向 req-21 / req-16）。
- 任何 req-9 / req-10 / req-15 / req-17 的现有 anchor — 不动它们以避免 cascade。
- 任何 req-21 / req-25 / req-27 / req-33 等已 skipped slot 的"自然重启用"逻辑 — 本 change 仅占用 req-21 (L195) 与 req-16 (L351)，其余 skipped slot 保持 skipped (无 ADDED Requirement 申请时不重启用)。

## Impact

- **Affected capability**: `wayfinder` (1 spec file)
- **Blast radius audit (per Fact 4 of pre-investigation)**: 反向 `grep -rn 'req-16\b\|req-21\b' -- src/ wayfinder/tickets/ openspec/specs/ openspec/changes/ tests/` 期望仅命中 (a) `openspec/specs/decompmoe-skeleton/spec.md` 中已使用的 req-16 anchor（peer capability，独立编号空间），(b) `verify_fixes.py` L12/L56 中 track req-21/req-34 的 verification script (审计 utility，不是 spec 引用)。零跨 spec breakage 风险。
- **Lint impact**:
  - `scripts/lint_no_source_field_drift.py` —— Source field 检查，不查 anchor 存在性；本 change 不改任何 Source field → exit=0 保持。
  - `scripts/lint_no_dead_defensive.py` —— defensive code pattern check，与本 change 无关 → exit=0 保持。
  - **`scripts/lint_no_source_field_drift.py` does not currently enforce anchor 100% 覆盖** — `CLAUDE.md` §6 第 8 条 hard rule 仍是手工验证；本 change 是把人工审计结果落地。
- **Test impact**: 0（spec-only edit，199 tests 期望全绿保持）。
- **Commit**: 单 commit on `dev`，不动 `main` / `release`，不 push（per CLAUDE.md §4 + agent memory "offshore-git-workflow"）。

## Out of scope

- `fix-config-docstring-beta-line-drift` (L2-F1 finding: `config.py:50` + `A4-1.md:59` 都引用 `req-7 L122` 但 narrative 实际在 L130) — pre-existing 多 surface spec line drift，独立 follow-up change（per Memory lesson "Multi-surface spec line-number references drift together"）。
- `fix-wayfinder-flops-routing-pytest-coverage` (R-4 finding: `FLOPs_Routing^(l) = 66_048` 未被 pytest 守护) — pre-existing principle-coverage gap，独立 follow-up change。
- 任何 `lint_no_source_field_drift.py` 加 anchor-100% 检查规则的扩展 —— 治理条款级变更，超出本 change scope。
- 历史 archive `openspec/changes/archive/2026-08-18-introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` L132 处旧 `<a id="req-10">` 的清理 —— archive spec.md 是历史 snapshot，**不应**修改（per OpenSpec convention: archive 是 immutable historical record）。