## Why

2026-09-19 对 `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/` 跑事实验证（30 个 verify cycle + 9 个 meta-发现的 audit-verification loop 收尾审计），发现 4 处 scope fidelity 问题（F1-F4），均属**规划制品层面的 fidelity 缺陷**（不涉及 spec/代码行为变化）：

| ID | 问题 | 证据 |
|---|---|---|
| F1 | proposal.md `What Changes` §B 与 Impact §Affected code 完全未提 `wayfinder/tickets/A1-1.md` L97，但 tasks.md B1.2 + design.md L19 + audit-verification.md L132 都明确把 A1-1 L97 列为 cycle-5 finding 源头之一 | `.audit/audit-verification/audit-verification.md` L132 字面 `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°`；本 change 上一轮事实验证脚本 17/17 文本核对 T3 ✓ |
| F2 | change 名 `4-file batch` 与 proposal.md L33/L46-47 + design.md L33/L119 的"4-file 边界修改"声明错位；含 A1-1 后实为 5-file | tasks.md B1.2 显式列举 A1-1 L97 修改 |
| F3 | proposal.md L7 table `15.24° (29% relative)` 的"29%"惯例与 `.audit/spec-math-audit/spec-math-audit.md` L134 的 `15.24° 偏离（相对偏离 22.7%）` 跨文档不一致；29% 用 ticket stale (52°) 作 base、22.7% 用 spec truth (67.24°) 作 base | 两个 base 都在项目 audit trail 出现，但 change 01 未声明 base convention |
| F4 | A1-1 L97 的 supersede annotation 操作在 tasks.md B1.2 直接列出（"Done in propose phase"），但**未走 design.md Decision 流程**（D1 Choice 只列 A5-3 + A4-1，不含 A1-1） | design.md D1 Choice 字面无 A1-1 |

本 change 是 **process-style 修复**：仅编辑 change 01 的**规划制品**（proposal.md / design.md / tasks.md），不修改任何 spec / 代码 / 测试——因为 F1-F4 都是"planning artifacts 的 fidelity 缺陷"，而非"行为定义/实现"的缺陷。

## What Changes

**目标文件**（4 个，均在 `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/`，不进 git 追踪 per audit README L5）：

1. **`.audit/.../01-fix-ticket-stale-numerical-4file-batch/proposal.md`** —— 4 处 surgical Edit：
   - (F1) §Why table cycle-5 #1 行加 `| A1-1 L97 | 同上 | θ_Voronoi≈52° | 67.24° | 15.24° |` 子行
   - (F1) §What Changes §B 加新行 `#3.5 ticket A1-1 L97（cycle-5 #1 同源）` —— 完整 supersede annotation 文本（与 §B #3 平行）
   - (F2) §Why 表头 `形成同源 "ticket 端 stale 数值源头" pattern，4-file batch` 改 `5-file batch`
   - (F2) §What Changes 末尾 "不动 wayfinder tickets 其他文件" 改 "仅 A5-3 + A4-1 + A1-1 三处加 supersede annotation"（明确 5-file 而非 4-file）
   - (F3) §Why table cycle-5 #1 行加 base 声明：`15.24° absolute (29% relative-to-ticket-base / 22.7% relative-to-truth-base)`，并在表头注脚明示 base convention
   - (F4) §Impact `Affected code` 列表加 `wayfinder/tickets/A1-1.md:97`

2. **`.audit/.../01-fix-ticket-stale-numerical-4file-batch/design.md`** —— 2 处 surgical Edit：
   - (F4) §Decision 1 Choice 改 `ticket A5-3.md L62 ...；ticket A1-1.md L97 ...；ticket A4-1.md L58 ...`（A1-1 顺序在 A5-3 之后、A4-1 之前，因属 cycle-5 同源 finding）
   - (F4) §Decision 1 Rationale 末段加 `A1-1 L97 包含在 scope 内是 cycle-5 finding 的源头完整性要求（audit-verification.md L132 字面锁定），属 ticket → spec 闭式 supersede annotation 路径；决策路径与 A5-3 完全平行`
   - (F2) §Goals `4-file 边界修改` 改 `5-file 边界修改`
   - (F2) §Migration Plan step 2 加 `wayfinder/tickets/A1-1.md` L97

3. **`.audit/.../01-fix-ticket-stale-numerical-4file-batch/tasks.md`** —— 0 处 Edit（tasks.md B1.2 已是完整 scope —— 仅作为 ground truth 用于 proposal/design 的逆向对齐）

4. **`.audit/.../01-fix-ticket-stale-numerical-4file-batch/specs/wayfinder/spec.md`** —— 0 处 Edit（spec delta 不变：本 change 是 process-only，不引入新 spec 行为）

**Nothing else**：
- 不动 `.audit/audit-verification/audit-verification.md`（meta 元审计已 closed-loop，事实层是 ground truth）
- 不动 `wayfinder/tickets/A1-1.md`（tickets 实际修改由 change 01 自身的 apply 阶段负责；本 change 只修 change 01 的规划制品对 A1-1 的覆盖声明）
- 不动 `openspec/specs/**` —— skip_specs: true 已声明
- 不动 src/ / tests/
- 不动 git 分支（`.audit/` 内容不进 git 追踪）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无。本 change 是纯 process/scope-correction，spec 行为定义未变化。`skip_specs: true` 已在本 change `.openspec.yaml` 标注，对应 openspec-propose skill 模板 `pure refactor, tooling, docs` 类目）

### Added / Modified Requirements to Existing Capabilities

（无）

## Impact

- **Affected code**（surgical edits per CLAUDE.md §3）：
  - `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/proposal.md` —— 5 处 Edit（F1+F2+F3+F4 联合覆盖）
  - `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/design.md` —— 4 处 Edit（F2+F4）

- **Affected tests**：无（tasks.md B1.2-B1.3 已是 ground truth，不需变更）

- **Affected APIs / dependencies**：无

- **Affected systems**：无（仍是 formalize-only destination per CLAUDE.md §7）

- **Risk**：
  - **(F1/F2/F4)** surgical Edit 改 proposal/design 的 planning 文本 —— 受 CLAUDE.md §3 surgical 原则保护；每个 Edit 后跑 `git diff --stat`（虽然 `.audit/` 不进 git，但用 `diff` 验证 LF 保留即可）。**风险 LOW**。
  - **(F3)** base convention 文档化不引入新事实，只声明哪个 base 已被 audit trail 采用 —— 不影响 50-digit mpmath 数值闭式（该数 15.24° / 29% / 22.7% 都通过事实验证脚本 15/15 PASS）。**风险 LOW**。
  - **跨 audit 文档惯例漂移**：F3 是 doc-level 跨文件不一致（spec-math-audit 用 22.7%、audit-verification 用 29%），本 change 只在 change 01 内部声明 base convention，不回改 `.audit/spec-math-audit/spec-math-audit.md`（避免越权修改历史 audit 报告）。**风险 LOW**；进一步统一 base convention 是 follow-up 待用户决策。
  - **governance compliance**：本 change 不修改 `governance/spec.md` 或 `wayfinder/spec.md`；spec req-34 主反链首位 + backtick-wrapped + paren-depth-aware atomic split 三项结构性检查不受影响。**Mitigation 已规划**（apply 前跑 `python scripts/lint_no_source_field_drift.py` exit=0 复测）。

- **Source**：
  - CLAUDE.md §3 (surgical changes 原则)
  - CLAUDE.md §2 (truth-source hierarchy: spec > audit-evidence > 其他)
  - 本 change 的发现来源：上一轮我对 `.audit/.../01-fix-ticket-stale-numerical-4file-batch/` 的事实验证（脚本 `verify_numerical_claims.py` 15/15 PASS + 17/17 文本 PASS + 4 处 scope fidelity findings F1-F4）
  - cycle-5 finding 源头：`.audit/audit-verification/audit-verification.md` L132 `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°`