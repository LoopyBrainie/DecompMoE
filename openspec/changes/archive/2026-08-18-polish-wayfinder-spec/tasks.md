## 0. Archive Gate Precondition

- [ ] 0.1 Confirm `openspec/specs/wayfinder/spec.md` does NOT exist yet (i.e., `introduce-wayfinder-decompoe-spec` has NOT been archived). Polish must happen before archive, otherwise the change's own spec.md copy in `openspec/changes/.../specs/wayfinder/spec.md` becomes stale vs the archived canonical.
- [ ] 0.2 Confirm `wayfinder/tickets/WF-1.md` Resolution section is unchanged (Polish is the execution of WF-1 warnings, not a re-grilling of the audit).

## 1. Spec Anchor Addition (design Decision 1)

- [ ] 1.1 Run `grep -n '^### Requirement:' openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` and confirm exactly 21 matches.
- [ ] 1.2 For each of the 21 matches in document order, insert a line `<a id="req-N"></a>` immediately above the `### Requirement:` line, where N starts at 1 and increments by 1 per match. Use the Edit tool per match (or one multi-line replacement) — do NOT renumber existing Requirement titles.
- [ ] 1.3 Run `grep -c '<a id="req-' openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` and confirm count = 21.
- [ ] 1.4 Spot-check: pick 3 anchors (`req-1`, `req-11`, `req-21`), confirm each `<a id="req-N">` sits directly above its `### Requirement:` line in spec.md.

## 2. Design.md Relative-Link Rewrite (design Decision 2)

- [ ] 2.1 In `openspec/changes/introduce-wayfinder-decompoe-spec/design.md`, locate every natural-language Requirement reference. Expected references in Risks section: `Naming And Alias Convention` (Decision 2 / Risks / naming ambiguity Mitigation) and `Hardware And Kernel Friendliness` (Risks / archive trigger ambiguity Mitigation).
- [ ] 2.2 Rewrite each reference from plain text to Markdown link `[<Requirement Name>](../specs/wayfinder/spec.md#req-N)` where N is the anchor index from task 1.2. Use exact anchor index, not fuzzy name match.
- [ ] 2.3 Run `grep -oE 'specs/wayfinder/spec.md#req-[0-9]+' openspec/changes/introduce-wayfinder-decompoe-spec/design.md` and confirm every anchor id resolves to a real `<a id="req-N">` in spec.md (set inclusion check, count = 2).
- [ ] 2.4 Verify no plain-text Requirement names remain where they should be links (acceptable exceptions: prose like "spec the first Requirement `Naming And Alias Convention`" — keep as-is if it's general prose, not a cross-reference).

## 3. Tasks.md 2.4 Description Refinement (design Decision 3)

- [ ] 3.1 Read current `tasks.md 2.4` text — verify it currently reads: "Scope-Lock consistency check — confirm spec body contains no requirement for Linear Attention / SSM / RNN / Pre-Attention Dynamic Bias / dense-or-other-MoE checkpoint conversion; these appear only in the `## Purpose` exclusion list or in `Source:` references to "Future Work" sections inside tickets".
- [ ] 3.2 Replace task 2.4 text with two independent judgment bullets. The replacement MUST keep task number `2.4` (anchor for downstream audit tooling) and SHOULD follow the form:
  - `- [ ] 2.4 Scope-Lock consistency check, spec side — grep `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` for `Linear Attention` / `SSM` / `RNN` / `Pre-Attention Dynamic Bias` / `checkpoint conversion`; each MUST appear only inside `## Purpose`'s exclusion clause, not inside any `### Requirement:` body or `#### Scenario:` body.`
  - `- [ ] 2.5 Scope-Lock consistency check, ticket side — for each of the five terms, run `grep -nE 'Future Work' wayfinder/tickets/*.md` and confirm any ticket mentions appear only inside the ticket's `## Future Work` section, not inside the ticket's Resolution body.`
- [ ] 3.3 Renumber subsequent tasks (old 2.5 Naming consistency check → 2.6; old 2.6 Hardware-compatibility matrix check → 2.7). Verify all subsequent cross-references in tasks.md still resolve.
- [ ] 3.4 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` after edit and confirm no parse error.

## 4. Proposal.md R/S Count Addition (design Decision 4)

- [ ] 4.1 In `openspec/changes/introduce-wayfinder-decompoe-spec/proposal.md`, append a new line to the end of the `## Impact` section (before any subsequent `##` heading): `- **交付规格**：本 change 包含 21 Requirements × 34 Scenarios（grep `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` 验证）。`
- [ ] 4.2 Run `grep -F "21 Requirements × 34 Scenarios" openspec/changes/introduce-wayfinder-decompoe-spec/proposal.md` and confirm exactly 1 match.
- [ ] 4.3 Verify the new line sits inside the `## Impact` section block (between `## Impact` heading and the next `##` heading). Use a heading grep boundary check.

## 5. Validation

- [ ] 5.1 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` from `D:\myProject\DecompMoE` — must report `Change 'introduce-wayfinder-decompoe-spec' is valid` with zero errors.
- [ ] 5.2 Run `openspec validate polish-wayfinder-spec --strict` from `D:\myProject\DecompMoE` — must report `Change 'polish-wayfinder-spec' is valid` with zero errors.
- [ ] 5.3 Run `openspec status introduce-wayfinder-decompoe-spec --json` and confirm `isPlanningComplete: true` and every artifact reports `status: "done"`.
- [ ] 5.4 Run `openspec status polish-wayfinder-spec --json` and confirm `isPlanningComplete: true` (proposal done, specs skipped, design done, tasks done).

## 6. Archive Order

- [ ] 6.1 Run `openspec archive polish-wayfinder-spec --yes` FIRST. This logs the polish into change history before the prior change is archived.
- [ ] 6.2 Then run `openspec archive introduce-wayfinder-decompoe-spec --yes`. The archived canonical at `openspec/specs/wayfinder/spec.md` MUST contain the polished anchor IDs, the polished `Source:` lines, AND the polished A4-1 γ 梯度上界 per-component text.
- [ ] 6.3 After both archives, run `openspec list --json` (or equivalent) and confirm both changes report `status: "archived"`.
- [ ] 6.4 Append a one-line entry to `wayfinder/map.md` `## Decisions so far` section: `- [WF-2 Polish OpenSpec Spec](tickets/WF-2.md) — PASS：3 项 WF-1 warning 全部收敛（proposal R/S 数 / spec 锚点 + design 相对链接 / tasks 2.4 判定路径拆分）+ 21 ticket deep-check 发现的 A4-1 γ 梯度上界精度修正（15.95 ⊂ 32 子集，行为契约未扩张），`openspec validate --strict` 双 change 通过；archive 顺序 polish → introduce 已执行`——create `wayfinder/tickets/WF-2.md` with the same status / type / arena as WF-1 before appending the map entry.

## 7. A4-1 γ 梯度上界文本精度修正（design Decision 5；21 ticket deep-check by-product）

- [ ] 7.1 In `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md`, locate the `Isotropic Squared-Chord Distance And Bounded Beta` Requirement body (anchor `# `req-7` after Group 1 anchor addition; body content lines ~82–93). Verify it currently contains the sentence: `The system MUST bound all three gradient magnitudes (with respect to `C`, `c_i`, and `γ`) by ` ≤ β_max = 32` as a hard numerical-stability guarantee.`
- [ ] 7.2 Replace the sentence with: `The system MUST bound `‖∂logit/∂C‖₂` and `‖∂logit/∂c_i‖₂` by ` ≤ β_max = 32`, and `|∂logit/∂γ_i|` by ` ≤ 0.5(β_max − β_min) = 15.95`, as hard numerical-stability guarantees derived from ticket A4-1.`
- [ ] 7.3 Run `grep -F "0.5(β_max − β_min) = 15.95" openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` and confirm exactly 1 match inside the `Isotropic Squared-Chord Distance And Bounded Beta` Requirement body.
- [ ] 7.4 Run `grep -F "all three gradient magnitudes" openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md` and confirm 0 matches (old phrasing fully replaced).
- [ ] 7.5 Verify the anchor `<a id="req-7">` (added in task 1.2) still sits directly above the modified Requirement title; the body edit MUST NOT shift the heading line.
- [ ] 7.6 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` and confirm still `is valid` (the change is text-precision only, not a Requirement addition, so spec-driven schema tolerates it under `skip_specs: true` in this change).