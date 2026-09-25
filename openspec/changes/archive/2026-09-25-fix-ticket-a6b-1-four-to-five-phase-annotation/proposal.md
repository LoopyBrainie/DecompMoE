# Proposal

## Why

`wayfinder/tickets/A6b-1.md` L1（标题 `# A6b-1: 四阶段演进逻辑`）和 L14（Question 段 `4 阶段训练 pipeline 的具体排法：`）仍使用 **"四阶段 / 4 阶段"** 措辞，与 spec 真相源 `openspec/specs/wayfinder/spec.md` req-14 "Five-Phase Time-Driven Schedule"（`<a id="req-14">` anchor at L319；Requirement title at L321；body at L323 "The system MUST partition training into **five phases** with the fixed duration ratios `1% / 5% / 20% / 30% / 44%`"）显式冲突。req-14 Source 字段 at L325 显式记录该 5-phase 决议来源：`change \`fix-openspec-doc-bugs\` design.md (Decision 2)`。

ticket 端已在 L101（`N_e = 64 → MVP N_e = 16`）+ L133（`γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` 公式落 spec req-7）建立 supersede annotation 范式，本次新增的"L1 标题 + L14 Question"两处 stale 措辞属同一模式的延续 —— **ticket ↔ spec 决策链记录不完整，audit reader 可能把 ticket 当 spec 真相源读**。`.audit/spec-math-audit/README.md` L223 A2.1 finding 已锁定该 stale（severity LOW，scope: wayfinder/tickets/*.md 修改）。

## What Changes

- `wayfinder/tickets/A6b-1.md` L1：标题追加 italic `(historical, ...)` annotation，**保留**原 `# A6b-1: 四阶段演进逻辑` 字样
- `wayfinder/tickets/A6b-1.md` L14：紧跟 `4 阶段训练 pipeline 的具体排法：` 后追加 italic `(historical, ...)` annotation，**保留**原 `4 阶段` 字样

两处 annotation 文本完全平行，对齐 ticket 已有的 L101 / L133 supersede 范式，遵守 `openspec/specs/governance/spec.md` req-gov-2（governance L51-67）Documenting-only meta Requirement 的 canonical 形式 `<原值 reading>; superseded by spec req-N L### via <change> Decision M` —— 3-反链齐（ticket + spec anchor + change Decision）+ 全 backtick-wrapped。

无其他文件改动。无 spec Requirement / Scenario 变更（`skip_specs: true`，req-14 已是真相源，body / Source 字段已正确）。无 `src/`、`tests/`、`CLAUDE.md`、MVPConfig 改动。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— `skip_specs: true` 已设置。spec req-14 L319/L321/L323 + L325 Source 字段已正确反映 5-phase 决议，本 change 仅 ticket 端历史决策链记录，无 spec-level behavior 改动。）

## Impact

- **Affected code**（无）：0 文件 src/ / tests/ / spec/ / CLAUDE.md 改动。
- **Affected tickets**（surgical 2 处）：`wayfinder/tickets/A6b-1.md` L1（标题）+ L14（Question 段），inline italic annotation 追加。
- **Affected APIs / dependencies / systems**：无。
- **Risk**：low（annotation 仅追加，不改 ticket 既有内容；保留决策链；与 ticket 既有 L101 / L133 范式对齐）。

## Evidence Chain

- `.audit/spec-math-audit/README.md` L223 —— A2.1 finding verbatim `"L17 已加 supersede annotation 但 L91 secondary table 未加"`（原 finding 行号错指，由本 change 修正为 L1 / L14 真正 stale 点；事实修正记录保留在 commit body / tasks.md）。
- `.audit/spec-math-audit/spec-math-audit.md` L592 finding 2 —— "【INFO】五阶段编排 spec ↔ ticket 高度对齐：phase boundaries + ratios + EMA α (0.90/0.95/0.99) + β schedule (1.0/4.0/16.0) + frozen rules + λ(t) schedule + Adam reset + γ' continuity closed-form + limit-continuity 4e-4 residual 全部 bare `==` / verbatim 匹配。**req-14 是"已对齐 req"**" —— 确认 spec req-14 已是真相源，本次 fix 仅 ticket 端 annotation 补全，不改 spec。
- `openspec/specs/wayfinder/spec.md` L319/L321/L323/L325 —— req-14 "Five-Phase Time-Driven Schedule" anchor / title / body / Source 字段，spec 端已正确反映 5-phase。
- `openspec/specs/governance/spec.md` L51-67 —— req-gov-2 canonical ticket `(historical, <原值>; superseded by spec req-N L### via <change> Decision M)` 形式权威。
- `openspec/specs/wayfinder/spec.md` L742-751 —— req-34 Source Field Format Invariant（spec-side 范式，ticket-side annotation 形式以 req-gov-2 为权威，req-34 仅 spec Source 字段约束）。
- `openspec/changes/archive/2026-09-22-fix-ticket-a6a-2-f-threshold-supersede/` —— 同结构 ticket-only 单一 supersede annotation fix 的 archive 先例（`skip_specs: true`，单 ticket L63 inline annotation，proposal/design/tasks 三件套格式可直接镜像）。
- `openspec/changes/archive/2026-09-23-01-fix-ticket-stale-numerical-4file-batch/proposal.md` L34-38 —— ticket 端 supersede annotation 范式（`N_e = 64 → MVP N_e = 16`、`θ_Voronoi ~52° → 67.24°` 等批次）。

Co-Authored-By: Claude Code <noreply@anthropic.com>