# fix-spec-anchor-coverage-l524-l588-l627-l293

## Why

`openspec/specs/wayfinder/spec.md` 与 `openspec/specs/decompmoe-skeleton/spec.md` 仍有未补 anchor 的 Requirement body,违反 `CLAUDE.md` §6 第 8 条 "spec anchor 不全：每个 Requirement MUST 在首行设独立 anchor `<a id="req-N"></a>`，**100% 覆盖**" hard rule.

具体缺失位置（实测 grep 确认）：

| spec 文件 | Requirement heading | 当前行号 | 缺 anchor |
|---|---|---|---|
| wayfinder/spec.md | Six-Module Visualization Toolchain | L530 | req-25 |
| wayfinder/spec.md | CentroidDriver Dual-Channel Architecture Contract | L594 | req-27 |
| wayfinder/spec.md | Phase 2 β Box Equality | L633 | req-33 |
| decompmoe-skeleton/spec.md | Five-Phase Schedule State Machine | L303 | req-13 |

行号相对 plan snapshot (`L524/L588/L627/L293`) 漂移了 `+6/+6/+6/+10` —— 这反映 plan 创建后 spec 继续被其它 in-flight change 微调；本 change 用**实测当前行号**而非 plan 行号作为 anchor。

## What changes

- **`openspec/specs/wayfinder/spec.md`** — 在 L530 `### Requirement: Six-Module Visualization Toolchain` 前一行插入 `<a id="req-25"></a>`。该 slot 是历史 cascade-free 方案中预留的 skipped integer slot（req-24 L572 ↔ req-26 L620 之间），嵌位自然、零 cascade 风险。
- **`openspec/specs/wayfinder/spec.md`** — 在 L594 `### Requirement: CentroidDriver Dual-Channel Architecture Contract` 前一行插入 `<a id="req-27"></a>`。自然 slot（嵌 req-26 L620 ↔ req-28 L651 之间）。
- **`openspec/specs/wayfinder/spec.md`** — 在 L633 `### Requirement: Phase 2 β Box Equality` 前一行插入 `<a id="req-33"></a>`。**复用 archived change `2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian`（commit `24118d6`）曾主动删除的孤儿 slot @ 历史 L740**。该 orphan slot 自删除后未被任何 spec 元素占用，而 L633 Phase 2 β Box Equality 是合规 Requirement body（Source = `wayfinder/tickets/A6b-1.md` + change `fix-math-consistency-audit-2026-08` Decision 3），值得占用此整数 slot。Lineage 记录在 commit message + tasks.md 中。
- **`openspec/specs/decompmoe-skeleton/spec.md`** — 在 L303 `### Requirement: Five-Phase Schedule State Machine` 前一行插入 `<a id="req-13"></a>`。自然 slot（嵌 req-12 L236 ↔ req-14 L323 之间）。**注意**：与 wayfinder `req-13`（Numerical Safeguards @ wayfinder L305）是不同 capability 的独立 anchor namespace，跨 capability 不冲突（per `scripts/lint_no_source_field_drift.py` 的 per-capability reverse-link rule 同款论证）。

**NOT changed**：
- 任何 Source 反链（`wayfinder/tickets/A8-3.md` for L530；A6b-1 for L633；CentroidDriver Source = req-9 + req-23 同款；Five-Phase Source = wayfinder Req 14 + decompmoe-skeleton peer requirement 集合）— 全部保持原状。
- 任何 ticket / map.md / src/ / tests/ 引用。
- 任何 req-1..24/26/28/29/30/31/32/34/35/36 (wayfinder) 或 req-1..12/14..23 (decompmoe-skeleton) 的现有 anchor。
- 任何 `req-21/25/27/33` 中已 skipped slot 的"自然重启用"逻辑自动决策 —— 本 change 是手工选定，非 `merge_spec_deltas.py` 自动行为。

## Audit fact-check（与 A2.1/A2.2 清单对照）

| 清单项 | 判定 |
|---|---|
| A2.1 声称 L502 CG n=1 boundary behavior 缺 anchor | ❌ **误报剔除**。实测 req-35 @ L506 已锚定 L508 Requirement heading。审计员混淆了相邻行位置。 |
| A2.1 缺 L524 Six-Module Visualization Toolchain | ✅ 当前实际行号 L530（spec 演化 +6 行 drift）。本 change 修。 |
| A2.1 缺 L588 CentroidDriver Dual-Channel Architecture Contract | ✅ 当前实际行号 L594（+6 行 drift）。本 change 修。 |
| A2.1 缺 L627 Phase 2 β Box Equality | ✅ 当前实际行号 L633（+6 行 drift）。本 change 修。 |
| A2.2 缺 L293 Five-Phase Schedule State Machine | ✅ 当前实际行号 L303（+10 行 drift）。本 change 修。 |

## Impact

- **Affected files**: 
  - `openspec/specs/wayfinder/spec.md`（+3 行 anchor，3 处插入，每处格式 `<a id="req-N"></a>` + 1 blank line）
  - `openspec/specs/decompmoe-skeleton/spec.md`（+1 行 anchor）
  - `openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/` 新建（OpenSpec 标准 3 件套 + `.openspec.yaml`）
- **Affected code/APIs/dependencies**: none。
- **Lint**:
  - `python scripts/lint_no_source_field_drift.py` —— Source field 反链 rule 不变 → exit=0 保持（本 change 不改任何 Source field）。
  - `python scripts/lint_no_dead_defensive.py` —— defensive code pattern rule 与本 change 无关 → exit=0 保持。
- **Test**: 0（spec-only edit，199 tests 期望全绿保持）。
- **Blast radius**（per plan Step "Blast radius 反向 grep" 实测）:
  - `src/`: 0 hit for `req-25/27/33/13`
  - `tests/`: 1 hit (`tests/test_merge_spec_deltas.py:120` synthetic fixture in master file，独立临时 fixture，无 active 引用)
  - `wayfinder/`: 0 hit
- **Audit trail**: future cycles 可 grep `req-25/27/33` 与 `decompmoe-skeleton/req-13` 验证完整覆盖，零遗漏。

## Out of scope

- `openspec/changes/2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351/` 的归档（`/opsx:archive`）—— 由用户后续触发；该 change 已部分 apply（commit `139e093`），命名同族但行号不重叠。
- `openspec/changes/2026-09-23-01-fix-ticket-stale-numerical-4file-batch/` —— 独立 in-flight change，行号不重叠。
- 任何 `scripts/lint_no_source_field_drift.py` 加 anchor-100% 检查规则扩展 —— 治理条款级变更，超 scope。
- 历史 `req-33` orphan 删除决定（commit `24118d6`）的归档注解更新 —— commit message + tasks.md 已记录 lineage，可选 archive annotation 不在 scope。
- `fix-config-docstring-beta-line-drift`（L2-F1：src/config.py:50 + A4-1.md:59 引用 `req-7 L122` 但 narrative 在 L130）—— pre-existing 多 surface drift，独立 follow-up。
- `fix-wayfinder-flops-routing-pytest-coverage`（R-4：FLOPs_Routing^(l) = 66_048 未被 pytest 守护）—— pre-existing principle-coverage gap，独立 follow-up。

## Capabilities

### Modified Capabilities
(none — see `skip_specs: true` rationale below)

### `skip_specs` rationale

本 change **纯结构性**（anchor 标签增补），无任何 Requirement body 变化，无 Source 反链变化，无 spec 行为变化：

- anchor 插入是结构性的 —— 它仅启用 by-anchor 引用，不替换任何 by-ticket 引用；零 spec 语义变化；仅强制 CLAUDE.md §6 第 8 条 `<a id="req-N"></a>` ↔ `### Requirement: <title>` invariant。
- 零 `**Source:**` 字段增删；零 Requirement body 修改；零 Scenarios 修改；零 `#### Scenario:` 块增删。

Per OpenSpec spec-driven workflow 规则 "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation."，本 change 设 `skip_specs: true`。`apply` 阶段直接编辑两个 spec 文件，不产出 `specs/<capability>/spec.md` delta。

Precedent: archived change `2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` Decision 1 同款论证。