# Design: fix-wayfinder-spec-anchor-coverage-l195-l351

## Context

Cycle-N+1 audit-verification loop 经 Python reviewer Agent（session id `mvs_e69331c3ba70428cb05eb809c5886c03`，2026-09-25）在 commit `d71115d` 的全面 review 中识别 `L4-F1` finding：wayfinder spec 33 个 Requirements 中 2 个缺 anchor（`No Shared Expert` L195 + `Prefill And Decode` L351）。

Pre-investigation 在本 change 入口已完成：
- **Fact 1** — 两处缺失 anchor 现场核实（`source: spec.md:179 req-9` + `spec.md:205 req-10` 之间的 L195；`spec.md:339 req-15` + `spec.md:361 req-17` 之间的 L351）。
- **Fact 2** — anchor 序列 31 个，缺失 slots 是 `16 / 21 / 25 / 27 / 33`（其中 16/21/25/27/33 在 spec 文件中未出现 `<a id="req-N">`，是历史演化遗留的整数空缺）。
- **Fact 3** — 可用整数 slot 候选（详见 `proposal.md` What changes 段）。
- **Fact 4** — 反向引用 blast radius：所有引用 A5-2 / A7-1 的下游 surface 都用 **ticket name**，不用 anchor；零 anchor-side breakage。
- **Fact 5** — L195 的结构性困境（无自然 slot）：选项 A cascade / B 远端 / C 局部 cascade / D 非整数。
- **Fact 6** — 历史演化提示：`2026-08-18-introduce-wayfinder-decompoe-spec` archive 显示 L195 当时带 `<a id="req-10">`，后续 spec 演化把它推到 L195 但 anchor 没迁出。

User 已批准具体选择：
- **L351 → `<a id="req-16">`**（天然 slot，0 风险）
- **L195 → `<a id="req-21">`**（远端最小可用 slot，0 cascade 风险，符合 CLAUDE.md §3 surgical "Touch only what you must"）

## Decisions

### Decision 1 — Anchor 选择：req-16 for L351, req-21 for L195

**Rationale**: 
- L351 req-16 是结构性 natural slot（嵌在 req-15 ↔ req-17 之间），最小改动原则。
- L195 req-21 是次优解 — 项目约定 integer anchor，但 L195 在 req-9 ↔ req-10 之间无自然 slot；req-21 是最小可用远端 slot。
- 两选项**都是**非 cascade fix，符合 CLAUDE.md §3 surgical + Memory lesson "Multi-surface spec line-number references drift together"。

**Rejected alternatives**:
- **Renumber cascade** (Option A/C): would touch 21 anchors + all downstream grep references. Cascade risk from Memory lesson outweighs structural-order benefit.
- **Non-integer anchor** (Option D req-9a / req-9.5): violates project convention `lint_no_source_field_drift.py` expects `<a id="req-N">` with integer N.

**Trade-off acknowledged**: req-21 L195 引入 **structural-order ↔ anchor-id 失配** (semantic disconnect between position-in-file and integer). Mitigation: each Requirement is independently addressable by title and by anchor; readers navigate by title first, anchor second. The cost is minor.

### Decision 2 — 不修改任何 Source 反链或 ticket 引用

**Rationale**: 验证显示所有引用 A5-2 / A7-1 的 surface 都用 ticket name 而非 spec anchor。新 anchor 仅 enable by-anchor 引用，**不**替换任何 by-ticket 引用。零改动 blast radius。

### Decision 3 — 不触碰任何 req-21/25/27/33 中未使用的 skipped slot 重启用逻辑

**Rationale**: 项目历史形成 req-16/21/25/27/33 skipped slots 列表 — 它们是"未来 ADDED Requirements 申请时按 next-unused 选择"的预留位（per `scripts/merge_spec_deltas.py:9-13` "assigns anchors to ADDED blocks (numbered from the next unused)"）。本 change 仅占用 req-21 (L195) 和 req-16 (L351)；其余 skipped slot 保持 skipped。**风险点**: 未来某 ADDED Requirement 自动选中 req-21 时会撞 L195 → mitigation: `lint_no_source_field_drift.py` 应在 merge 时验证 anchor 唯一性（**注**: 当前 lint 不验证 anchor 唯一性；本 change 不扩展 lint 规则，超 scope）。

### Decision 4 — Edit tool boundary 严格守住保留内容（per Memory lesson "Edit tool `old_string` boundary is greedy"）

**Implementation detail**:
- L195 edit `old_string` 末尾是 `### Requirement: No Shared Expert`（待保留的下一段首行之前是 blank line），`new_string` 把 blank line + anchor + blank line 嵌进去，**不**包含 `### Requirement` 行本身 → 边界安全。
- L351 edit `old_string` 末尾是 `### Requirement: Prefill And Decode Share`，同样不包含后续 body → 边界安全。
- Edit 后立即 grep `### Requirement: No Shared Expert` 与 `### Requirement: Prefill And Decode Share` 双重确认两段 Requirement body 仍存在（保留内容边界未误删）。

### Decision 5 — 单 commit on dev（per CLAUDE.md §4）

**Rationale**: spec-only edit，零行为改动；单 commit + 详尽 commit message 包含双向 reference (per Memory lesson "Validation claim wording 必须 scope-explicit" — claim 必须 scope-bound)。

**NOT in this commit**:
- `dev → main` 或 `dev → release` 合并（per agent memory "offshore-git-workflow" — merge commit 只允许在 main/release 上）
- 任何 `git push`（per plan Step 6 "No git push until user asks"）
- in-flight change `2026-09-23-01-fix-ticket-stale-numerical-4file-batch` 的任何行（L50-54 beta_initial，与本 change 行号不重叠）

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Edit tool 引入 CRLF (Windows + non-ASCII) | per memory lesson | Step "Verify" 中 byte-level 检查 `($_ -eq 13).Count` 必须 0 |
| Edit tool `old_string` 边界误删下一段 body | per memory lesson | `old_string` 末尾严格停在待保留首行之前；Edit 后 grep `### Requirement: No Shared Expert` 与 `### Requirement: Prefill And Decode Share` 验证 |
| Future ADDED Requirement 撞 req-21 | LOW | (a) 本 change 不引入撞号；（b）`merge_spec_deltas.py` 在 merge 阶段若启用 anchor 唯一性检查可拦截 |
| Anchor 100% 覆盖仍依赖人工审计，无 lint gate | LOW (pre-existing) | 本 change 不扩展 lint 规则（超 scope） |
| 现有 backward-compat: 若有外部 surface 已 by-anchor 引用了未来 (req-21) 应是别的 Requirement → 撞号 | 已 grep 验证 0 hits | "req-21" + "req-16" 在 active surfaces 0 hits except decompmoe-skeleton peer (peer 独立 namespace, 无 cross-capability collision) |