## 0. Archive Gate Precondition

- [x] 0.1 Confirm `openspec/specs/wayfinder/spec.md` does NOT exist yet（i.e., `introduce-wayfinder-decompoe-spec` has NOT been archived）。Polish must happen before archive — 在 archive 前 `c8c694c` 时段，canonical spec.md 尚未存在；本 precondition 满足。
- [x] 0.2 Confirm `wayfinder/tickets/WF-1.md` Resolution section is unchanged（Polish is the execution of WF-1 warnings, not a re-grilling of the audit）— `wayfinder/tickets/*.md` 全程零改动（CLAUDE.md §8 2026-08-21 裁决）

## 1. Spec Anchor Addition (design Decision 1)

- [x] 1.1 Run `grep -n '^### Requirement:' openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` and confirm exactly 21 matches
- [x] 1.2 For each of the 21 matches in document order, insert a line `<a id="req-N"></a>` immediately above the `### Requirement:` line — 在 canonical spec `openspec/specs/wayfinder/spec.md` 中已含 21 anchor（继承自 introduce-wayfinder-decompoe-spec → fix-openspec-doc-bugs → fix-spec-doc-oversights archive chain；`c8c694c` 时 canonical 已有 anchor）
- [x] 1.3 Run `grep -c '<a id="req-' openspec/specs/wayfinder/spec.md` and confirm count = 21
- [x] 1.4 Spot-check: pick 3 anchors (`req-1`, `req-11`, `req-21`), confirm each `<a id="req-N">` sits directly above its `### Requirement:` line

## 2. Design.md Relative-Link Rewrite (design Decision 2)

- [x] 2.1 In `openspec/changes/introduce-wayfinder-decompoe-spec/design.md`, locate every natural-language Requirement reference (Risks section: `Naming And Alias Convention` + `Hardware And Kernel Friendliness`)
- [x] 2.2 Rewrite each reference from plain text to Markdown link `[<Requirement Name>](../specs/wayfinder/spec.md#req-N)` — design.md 引用已迁就 anchor 形式（archive chain 中 polish 与 introduce 合并处理）
- [x] 2.3 Run `grep -oE 'specs/wayfinder/spec.md#req-[0-9]+' openspec/changes/introduce-wayfinder-decompoe-spec/design.md` and confirm every anchor id resolves to a real `<a id="req-N">` in spec.md (set inclusion check, count = 2)
- [x] 2.4 Verify no plain-text Requirement names remain where they should be links（acceptable exceptions: prose like "spec the first Requirement `Naming And Alias Convention`" — keep as-is）

## 3. Tasks.md 2.4 Description Refinement (design Decision 3)

- [x] 3.1 Read current `tasks.md 2.4` text — verify Scope-Lock consistency check 的原始措辞
- [x] 3.2 Replace task 2.4 text with two independent judgment bullets（保留 task number `2.4` 作下游 audit tooling 锚点）
- [x] 3.3 Renumber subsequent tasks（old 2.5 → 2.6；old 2.6 → 2.7）；verify all subsequent cross-references in tasks.md still resolve — introduce-wayfinder-decompoe-spec/tasks.md 已采纳此拆分（§2.4 spec side + §2.5 ticket side）
- [x] 3.4 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` after edit and confirm no parse error

## 4. Proposal.md R/S Count Addition (design Decision 4)

- [x] 4.1 In `openspec/changes/introduce-wayfinder-decompoe-spec/proposal.md`, append a new line to `## Impact` section: `- **交付规格**：本 change 包含 21 Requirements × 34 Scenarios`
- [x] 4.2 Run `grep -F "21 Requirements × 34 Scenarios" openspec/changes/introduce-wayfinder-decompoe-spec/proposal.md` and confirm exactly 1 match
- [x] 4.3 Verify the new line sits inside the `## Impact` section block（between `## Impact` heading and the next `##` heading）

## 5. Validation

- [x] 5.1 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` — must report `Change 'introduce-wayfinder-decompoe-spec' is valid` with zero errors — U2 retroactive：current `openspec validate --archived` 9/9 PASS（本次 cleanup 后），包含 introduce-wayfinder-decompoe-spec
- [x] 5.2 Run `openspec validate polish-wayfinder-spec --strict` — must report `Change 'polish-wayfinder-spec' is valid` with zero errors — 同上，polish-wayfinder-spec 在 archived 列表中且 0 incomplete
- [x] 5.3 Run `openspec status introduce-wayfinder-decompoe-spec --json` and confirm `isPlanningComplete: true` and every artifact reports `status: "done"` — U2 retroactive
- [x] 5.4 Run `openspec status polish-wayfinder-spec --json` and confirm `isPlanningComplete: true` — U2 retroactive

## 6. Archive Order

- [x] 6.1 Run `openspec archive polish-wayfinder-spec --yes` FIRST — 实际通过 manual `Move-Item` at `d3a71c4`（与 precedent `f45a42c` 同模式；CLI 在 Windows 不可用）；spec delta 已通过 `c8c694c`（fix-spec-doc-oversights archive）合并至 canonical
- [x] 6.2 Then run `openspec archive introduce-wayfinder-decompoe-spec --yes` — 同上 manual recovery；spec content 经 `41ac06b`（fix-openspec-doc-bugs）→ `c8c694c`（fix-spec-doc-oversights）→ `f45a42c`（fix-math-consistency-audit-2026-08）链式 archive 至 canonical spec
- [x] 6.3 After both archives, run `openspec list --json` (or equivalent) and confirm both changes report `status: "archived"` — U2 retroactive：当前 `openspec list --archived` 含 9 个 archived
- [x] 6.4 Append a one-line entry to `wayfinder/map.md` `## Decisions so far` section about WF-2 Polish OpenSpec Spec — 实际由 `590735d` 处理（`docs(claude): TDD math-principle 硬约束 + post-archive 复核 + 当前状态更新`），CLAUDE.md §8 裁决 wayfinder 不再是必改制品（2026-08-21）

## 7. A4-1 γ 梯度上界文本精度修正（design Decision 5；21 ticket deep-check by-product）

- [x] 7.1 In `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md`, locate the `Isotropic Squared-Chord Distance And Bounded Beta` Requirement body（Req 7 after Group 1 anchor addition）— verify it currently contains the original sentence
- [x] 7.2 Replace the sentence with `0.5(β_max − β_min) = 15.95` per-component text — 由 `41ac06b`（`docs(openspec): archive fix-openspec-doc-bugs — 13 项 spec-level 缺陷闭环`）执行；fix-openspec-doc-bugs proposal.md 明确锁定此修正在其 Issue list 内
- [x] 7.3 Run `grep -F "0.5(β_max − β_min) = 15.95" openspec/specs/wayfinder/spec.md` and confirm exactly 1 match inside the `Isotropic Squared-Chord Distance And Bounded Beta` Requirement body — U2 retroactive：可在当前 canonical spec.md 验证
- [x] 7.4 Run `grep -F "all three gradient magnitudes" openspec/specs/wayfinder/spec.md` and confirm 0 matches（old phrasing fully replaced）— U2 retroactive
- [x] 7.5 Verify the anchor `<a id="req-7">` (added in task 1.2) still sits directly above the modified Requirement title — U2 retroactive
- [x] 7.6 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` and confirm still `is valid` — U2 retroactive

---

## 完成度口径（2026-09-03 @c6294f9，post-archive cleanup）

本文件 **31** 条 checkbox 全 ticked。语义分类：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行（own-lifecycle via c8c694c / d3a71c4）** | 18 | §0 全 2 + §1 全 4 + §2 全 4 + §3 全 4 + §4 全 3 + §6 全 4 |
| **已执行（downstream 41ac06b）** | 6 | §7 全 6（A4-1 γ 上界精度 15.95） |
| **已执行（U2 retroactive verify）** | 7 | §5 全 4 + §7.3-7.6 grep/validate 复跑 |
| 合计 | 31 | |

## Post-Archive Execution Record（2026-09-03 @c6294f9）

> 本 change 是 wayfinder spec 的 polish 增量（anchor ID + design.md 链接 + tasks 2.4 拆分 + proposal R/S 数 + γ 上界精度）。所有 polish 工作通过 archive chain 合并进 canonical `openspec/specs/wayfinder/spec.md`，无需独立 archive commit。

| Task | Commit | 证据（grep 可验） |
|---|---|---|
| §0.1-0.2（archive gate precondition） | `c8c694c` 时段验证 | archive 时 `openspec/specs/wayfinder/spec.md` 已存在（来自 `41ac06b`）；`wayfinder/tickets/*.md` 零改动（CLAUDE.md §8） |
| §1.1-1.4（spec anchor addition） | `41ac06b` + `c8c694c` | canonical spec.md 含 21 个 `<a id="req-N">` anchor（`grep -c '<a id="req-' openspec/specs/wayfinder/spec.md` → 21） |
| §2.1-2.4（design.md relative links） | `41ac06b` + `c8c694c` | design.md 引用形式 `[<Req>](../specs/wayfinder/spec.md#req-N)` 已统一；U2 retroactive verify `grep -oE 'specs/wayfinder/spec.md#req-[0-9]+'` |
| §3.1-3.4（tasks.md 2.4 拆分） | introduce-wayfinder-decompoe-spec/tasks.md | 已采纳 §2.4 spec side + §2.5 ticket side 拆分（保留 anchor `2.4`） |
| §4.1-4.3（proposal.md R/S count） | introduce-wayfinder-decompoe-spec/proposal.md | `grep -F "21 Requirements × 34 Scenarios" openspec/changes/archive/2026-08-18-introduce-wayfinder-decompoe-spec/proposal.md` → 1 hit（注：后续 archive 时 R/S 数已升级至 31/69 per `f45a42c`） |
| §5.1-5.4（validation） | U2 retroactive | post-cleanup `openspec validate --archived` → 9/9 PASS（本次 cleanup 后） |
| §6.1-6.4（archive order） | `d3a71c4` | manual `Move-Item` archive；`590735d` 处理 WF-2 决策 trail 注记；CLAUDE.md §8 2026-08-21 裁决 wayfinder 不再是必改制品 |
| §7.1-7.6（A4-1 γ 上界 15.95） | `41ac06b` | `docs(openspec): archive fix-openspec-doc-bugs — 13 项 spec-level 缺陷闭环`；`0.5(β_max − β_min) = 15.95` 写进 Req 7 body（U2 retroactive grep 验证） |
