# 2026-09-26-followup-spec-wording-bugs-after-precision-disclosure

## Why

Cycle-N+1 audit-verification loop 的 anchor coverage audit (A2.1 + A2.2) 列出 5 个候选 anchor gap，但所有 5 项在当前 HEAD (`042cacd`) 实际已 closure（4 项真实 gap 已由独立归档 change `2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293` 在 commit `ef45765` archive 中 fix，1 项 A2.1 L502 是误报）。

原 audit 清单基于 pre-fix 行号 snapshot（L502/L524/L588/L627/L293），与当前 spec 实际 Requirement 头位置 drift `+4 / +6 / +6 / +6 / +10`，并非 spec 缺陷，而是 plan 创建时序与 spec 演化的 race。

**本 change 不修改任何 spec body**，仅作为 audit fact-check 留痕的载体，让 future cycles 能 grep `closes A2.1 / A2.2` 立即定位 closure 证据。

## Scope

**In scope**：
- 创建本 change 的 `proposal.md` + `tasks.md`（声明 audit-closure scope）
- 不修改任何 spec body、src/、tests/、ticket/、map.md、lint script
- 单 commit on dev（per CLAUDE.md §4）

**Out of scope**：
- 任何 anchor 补全（HEAD 已是 100% coverage）
- 任何 lint 规则扩展（治理条款级变更）
- 任何 in-flight change 的 apply / archive 推进
- 重写 archive/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/ 任何文件（已 archive，不重写）

## Affected files

| 文件 | 操作 | 理由 |
|---|---|---|
| `openspec/changes/2026-09-26-followup-spec-wording-bugs-after-precision-disclosure/proposal.md` | create | 本文件 — 声明 scope |
| `openspec/changes/2026-09-26-followup-spec-wording-bugs-after-precision-disclosure/tasks.md` | create | 任务清单 + audit-closure 判定表 |
| 其余 0 文件 | — | — |

## Audit fact-check（与 A2.1 / A2.2 清单对照）

| 清单条目 | 清单 line ref | 当前 Requirement 头位置 + anchor | 判定 | 引用 |
|---|---|---|---|---|
| A2.1.1 | L502 CG n=1 boundary behavior | L506 `<a id="req-35"></a>` | ❌ **误报**（清单点错行；L502 是 Scenario 体） | `archive/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/proposal.md` L57 |
| A2.1.2 | L524 Six-Module Visualization Toolchain | L530 `<a id="req-25"></a>` | ✅ 已修 | commit `2d0950b` (2026-09-26 15:13:03) |
| A2.1.3 | L588 CentroidDriver Dual-Channel Architecture Contract | L596 `<a id="req-27"></a>` | ✅ 已修 | commit `2d0950b` |
| A2.1.4 | L627 Phase 2 β Box Equality | L637 `<a id="req-33"></a>` | ✅ 已修 | commit `2d0950b`（req-33 slot 由 archived `24118d6` orphan 复用，lineage 见 archive change design.md Fact 5） |
| A2.2.1 | L293 Five-Phase Schedule State Machine | L303 `<a id="req-13"></a>` | ✅ 已修 | commit `de96ba6` (2026-09-26 14:58:47, parallel Python reviewer session `mvs_c1970089aa9341cda22ce41910b792a1`) |

**当前 HEAD (`042cacd`) anchor 覆盖率实测**：
- `openspec/specs/wayfinder/spec.md`: 36 anchors / 36 Requirements = **100%**
- `openspec/specs/decompmoe-skeleton/spec.md`: 23 anchors / 23 Requirements = **100%**

## Capabilities

### Modified Capabilities
(none — 纯 audit-closure documentation，无 spec 行为变化)

### `skip_specs` rationale

本 change **零 spec body 改动**，仅 documentation。Per OpenSpec spec-driven workflow 规则 "Use `skip_specs: true` only when no spec-level behavior changes"：
- 不修改任何 `### Requirement:` body
- 不修改任何 `**Source:**` 反链
- 不修改任何 `#### Scenario:`
- 不产出 `specs/<capability>/spec.md` delta

## Source back-link（per governance/req-gov-1 §3 lint rule）

本 Requirement (`req-N` for this closure note) 若在未来被打 anchor，本 change proposal 自带 `**Source:**` 反链：

- **`CLAUDE.md`** — governance 起源（CLAUDE.md §3 §6 第 8 条 hard rule 与 §4 git workflow）
- **`openspec/changes/archive/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/proposal.md`** L53-61 audit fact-check 表（独立得出与本 plan 一致的判定）
- **`change 2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293` design.md Decision 1** — 4 个 anchor 选择 rationale

## Risks / Trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| 用户可能预期"实际补 anchor"动作 | Low | Plan 已基于 `git show HEAD:` 实测证伪；本 change 已 ExitPlanMode approved |
| 重复 future cycle 报同一 finding | Low | 本 proposal + tasks.md 是 future cycle 可 grep 的 canonical closure note |
| `.audit/audit-verification.md` 不在 git 跟踪 | Low | 所有 closure 留痕写在 tracked 的 `openspec/changes/.../tasks.md`，不依赖 `.audit/` |