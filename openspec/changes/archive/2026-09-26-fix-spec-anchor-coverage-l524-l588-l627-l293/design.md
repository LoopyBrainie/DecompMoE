# Design: fix-spec-anchor-coverage-l524-l588-l627-l293

## Context

Cycle-N+1 audit-verification loop 2026-09-26 经 L4-F1 finding 二次扫描识别：wayfinder spec 36 个 Requirements 中仍有 3 个缺 anchor，decompmoe-skeleton 23 个 Requirements 中仍有 1 个缺 anchor。in-flight change `2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351`（commit `139e093`）已部分修 L195 + L351 但未覆盖本次 4 个新发现项。

**Pre-investigation**（已完成）：

- **Fact 1** — 4 处缺失 anchor 现场核实（实测当前行号）：
  - wayfinder L530 Six-Module Visualization Toolchain
  - wayfinder L594 CentroidDriver Dual-Channel Architecture Contract
  - wayfinder L633 Phase 2 β Box Equality
  - decompmoe-skeleton L303 Five-Phase Schedule State Machine
- **Fact 2** — anchor 序列实测（grep `<a id="req-[0-9]+"></a>`）：
  - wayfinder 当前 33 个 unique anchor（L824 narrative back-link `req-20` 重复不计），缺 `25/27/33`
  - decompmoe-skeleton 当前 22 个 unique anchor，缺 `13`
- **Fact 3** — A2.1 清单 4 项中 1 项误报（L502 实有 req-35 锚定 @ L506），3 项真实缺失（A2.1 清单声称 L524/L588/L627 三项均实存，但行号随 spec 演化漂移 +6）。
- **Fact 4** — Blast radius 反向 grep：`req-25/27/33/13` 在 `src/ tests/ wayfinder/` 全部 0 hit（除 `tests/test_merge_spec_deltas.py:120` synthetic fixture in master file）。
- **Fact 5** — req-33 历史 lineage：archived change `2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian`（commit `24118d6`，2026-09-24 19:51:44）曾删除孤儿 `req-33` @ 历史 L740，理由是 34b37be 已将 Requirement body 迁至 governance/req-gov-1。本 change 重新启用 req-33 锚定 L633 Phase 2 β Box Equality —— 与历史删除决定表面冲突但语义独立：当前 L633 Phase 2 β Box Equality 是合规 Requirement body（Source = A6b-1 + change fix-math-consistency-audit-2026-08 Decision 3），与原孤儿 req-33 (Test Guard Precision for Closed-Form Numerical Claims，迁至 governance/req-gov-1) 是不同 Requirement。整数 slot 33 因此重新承载一个真实 Requirement。
- **Fact 6** — decompmoe-skeleton req-13 slot 的历史 lineage（archived change `2026-09-15-fix-skeleton-spec-duplicate-and-completeness-2026-09-15` 注解中提到 "req-13 (Centroid Driver Invariant Test Scenarios, L331-347)"）：该历史 req-13 经后续 spec 演化已迁至 L378 重命名为 req-17，整数 slot 13 因此空缺。当前 L303 Five-Phase Schedule State Machine 占用此 slot 是自然填位。**注意**：与 wayfinder `req-13`（Numerical Safeguards @ wayfinder L305）是不同 capability 的独立 anchor namespace，跨 capability 不冲突。

## Decisions

### Decision 1 — Anchor 选择

**Choice** (final state @ HEAD `2d0950b` 2026-09-26 15:13:03):
- L524 Six-Module Visualization Toolchain → `<a id="req-25"></a>` ✅ (committed by `2d0950b`)
- L588 CentroidDriver Dual-Channel Architecture Contract → `<a id="req-27"></a>` ✅ (committed by `2d0950b`)
- L627 Phase 2 β Box Equality → `<a id="req-33"></a>` ✅ (committed by `2d0950b`, resuscitated from `24118d6` orphan slot)
- L293 Five-Phase Schedule State Machine → `<a id="req-13"></a>` ✅ (committed by `de96ba6` parallel session, 2026-09-26 14:58:47; out of this change scope)
- L313 Six Visualization Module Protocol Stubs → `<a id="req-14"></a>` ✅ (already in HEAD, never deleted; pre-existing assumption in original plan was wrong)

**Rationale**:
- 全部为**自然 slot**（嵌在已有 req-N ↔ req-(N+1) 之间），0 cascade 风险。
- 全部为**最小可用整数**选择，符合 project convention（per `scripts/lint_no_source_field_drift.py` 期望 `<a id="req-N">` 整数 N）。
- req-33 复用 archived orphan slot 的论证见 Fact 5。

**Rejected alternatives**:
- **Cascade renumbering**：会触动 21+ anchor 与全部下游 grep 引用。Memory lesson "Multi-surface spec line-number references drift together" 风险高，违背 CLAUDE.md §3 surgical "Touch only what you must"。
- **新建 slot (如 req-37)**：会让 anchor 序列出现新空洞（33 永久跳过），未来 merge_spec_deltas.py 自动 anchor 分配可能持续错位。
- **非整数 anchor (如 req-25a / req-25.5)**：违反 project convention `lint_no_source_field_drift.py` 期望 `<a id="req-N">` 整数 N。

### Decision 2 — 不修改任何 Source 反链或 ticket 引用

**Rationale**: 实测所有引用 A5-2 / A6b-1 / A8-3 等的 surface 都用 **ticket name**，不用 spec anchor。新 anchor 仅 enable by-anchor 引用，**不**替换任何 by-ticket 引用。零改动 blast radius。

### Decision 3 — 不触碰任何 req-21/25/27/33 中未使用的 skipped slot 重启用逻辑（除 req-33 本 change 主动复用）

**Rationale**: project 历史形成 skipped slot 列表 —— 它们是"未来 ADDED Requirements 申请时按 next-unused 选择"的预留位（per `scripts/merge_spec_deltas.py` "assigns anchors to ADDED blocks (numbered from the next unused)"）。本 change 仅占用 `req-25` / `req-27` / `req-33` / `req-13` 四个 slot（其中 req-33 是主动复用 archived orphan slot）；其余 skipped slot 保持 skipped。

**风险点**: 未来某 ADDED Requirement 自动选中 req-25/27/33/13 时会撞本 change 锚定的 Requirement → mitigation: `lint_no_source_field_drift.py` 应在 merge 时验证 anchor 唯一性（**注**: 当前 lint 不验证 anchor 唯一性；本 change 不扩展 lint 规则，超 scope）。

### Decision 4 — Edit tool 边界严格守住保留内容（per Memory lesson "Edit tool `old_string` boundary is greedy"）

**Implementation detail**:
- 每个 edit 的 `old_string` 末尾停在待保留首行**之前**的 blank line，**不得**包含 `### Requirement:` 行本身。
- `new_string` 把 anchor 行 + 空行嵌进去，**保留**原 blank line + `### Requirement:` 行不变。
- Edit 后**立即 grep** 该 Requirement 标题验证 body 未被吞掉（4 处 edit 各做一次）。

### Decision 5 — Skip-specs 适用

**Choice**: `skip_specs: true`（纯结构性 anchor 增补，无 Requirement body 变化）。

**Rationale**: Per OpenSpec spec-driven workflow 规则 "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation."。

**Precedent**: archived change `2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` Decision 1 同款论证。

### Decision 6 — 单 commit on dev（per CLAUDE.md §4）

**Rationale**: spec-only edit，零行为改动；单 commit + 详尽 commit message 包含双向 reference + lineage + audit fact-check（per Memory lesson "Validation claim wording 必须 scope-explicit"）。

**NOT in this commit**:
- `dev → main` 或 `dev → release` 合并（per agent memory "offshore-git-workflow" — merge commit 只允许在 main/release 上）。
- 任何 `git push`（per plan Step 6）。
- in-flight change `2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351` 的归档（L195/L351 已 apply，但 archive 流程不在本 change scope）。
- in-flight change `2026-09-23-01-fix-ticket-stale-numerical-4file-batch` 的任何行。

## Risks / Trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| Edit tool 引入 CRLF（Windows + non-ASCII：中文 / 数学符号 / β / γ） | per memory lesson | tasks.md Step "Post-edit verify" 中 byte-level 检查 `($_ -eq 13).Count` 必须 0 |
| Edit tool `old_string` 边界误删下一段 Requirement body | per memory lesson | `old_string` 末尾严格停在待保留首行之前；Edit 后 grep 4 个标题分别验证 |
| req-33 复用与 commit `24118d6` 删除决定产生解释负担 | LOW | commit message + tasks.md + (可选) commit message body 中明示 lineage |
| 未来 ADDED Requirement 撞 req-25/27/13 | LOW | (a) 本 change 不引入撞号；(b) merge_spec_deltas.py 在 merge 时若启用 anchor 唯一性检查可拦截 |
| Anchor 100% 覆盖仍依赖人工审计，无 lint gate | LOW (pre-existing) | 本 change 不扩展 lint 规则（超 scope）；audit cycle 已能持续识别此类 gap |
| 现有 backward-compat: 是否有外部 surface 已 by-anchor 引用未来 (req-25/27/33/13) 应是别的 Requirement | 已 grep 验证 0 hits | "req-25/27/33/13" 在 active surfaces 0 hits（除 `tests/test_merge_spec_deltas.py:120` synthetic fixture in master file） |
| Plan 行号 L524/L588/L627/L293 与实测当前 L530/L594/L633/L303 漂移 | LOW | plan Step 2 已说明"实测当前行号而非 plan 行号作为 anchor"；commit message 引用实测行号 |

## Migration Plan

无部署 / 回滚担忧：
- change 是 4 处单行 anchor 增补（每处 1 行 `<a id="req-N"></a>` + 1 行 blank）+ 1 个 OpenSpec change 目录新建。
- 零生产代码触动。
- 零 test 文件触动。
- 零 spec behavior 改动。
- Rollback 是反向操作：`git revert <commit>` 删除 4 行 anchor + 新建目录；`rm -rf openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/`。

## Open Questions

None. Scope bounded by 4-edit 结构性 fix；无 spec behavior 改动；无延期决策。