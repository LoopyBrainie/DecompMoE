# Design

## Context

See `proposal.md` Why for motivation. Current state of the defect being closed:

`openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` carries two lineage-incorrect claims about the new `Test Guard Precision for Closed-Form Numerical Claims` Requirement:

- **L12**: "(Req 32) added to `wayfinder`" — wrong on two counts (live Req 32 occupied by "Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper" at `openspec/specs/wayfinder/spec.md:702`; actual delta was anchored at `req-33` in commit `6f22278`).
- **L22**: "adds Requirement `Test Guard Precision for Closed-Form Numerical Claims` (3 Scenarios) to the `wayfinder` capability" — wrong destination (canonical home today is `governance/spec.md` `req-gov-1` after migration in commit `34b37be`).

These two claims were carried forward verbatim from the original `e437c2d` archive commit (2026-09-17) through the `889d81c` post-archive drift closure (2026-09-24) — `889d81c` H4 fixed the rad literal description (`1.1736` → `1.1735`) but preserved the wrong `(Req 32)` and `wayfinder` references because they were not flagged in its drift scan.

The **canonical Requirement home** is `openspec/specs/governance/spec.md` `<a id="req-gov-1">` L9 (added by `34b37be` `migrate-l678-source` 2026-09-12; subsequent commits `bec147d + 83a0503` had already reversed the integer-vs-float closed-form policy direction by the time the requirement was applied in commit `6f22278` 2026-09-08). The orphan `<a id="req-33">` left behind in `wayfinder/spec.md` after `34b37be` migration was closed by commit `24118d6` (2026-09-24, "fix(spec,archive): req-33 orphan anchor cleanup + 2026-09-06 archive lineage annotation"). That same `24118d6` commit also added a 3-section HTML-comment annotation block at `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` L1-16 documenting the full lineage (req-33 → req-gov-1 migration; policy reversal via bec147d+83a0503; canonical landing via 6f22278+34b37be).

The **specific defect** is the `(Req 32)` writing error in proposal.md L12 and the `wayfinder` capability mis-attribution in proposal.md L22. Both are prose claims that were never true at any commit (per git history: L12 originally said `(Req 32)` in `e437c2d`; the actual delta `6f22278` had `req-33`; L22 originally said `wayfinder` in `e437c2d`; the canonical home migrated to `governance/req-gov-1` later). The fix is a 2-line prose correction in `proposal.md` + 1 reverse-link bullet in the same file's Impact section.

Constraints:
- **Archive immutability convention**: archive files are audit-trail records. Single-line textual edits are allowed for drift annotations (precedent: `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` was annotated by `fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` on 2026-09-24; `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/` is being annotated by `fix-archive-ground-cg-n-eq-1-test-stale-anchor` on 2026-09-24). Deletion of archive folders or wholesale rewrite is NOT allowed.
- **No touching `specs/wayfinder/spec.md` in this archive**: that file was annotated by another change (`fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian`, archived at `openspec/changes/archive/2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian/`). Editing it in this change would create concurrent-modification conflict; the existing annotation is comprehensive and correct.
- **`lint_no_source_field_drift.py`**: per-capability reverse-link rule (introduced by `34b37be`); archive files are not in the live lint scan set. The drift fix MUST NOT break the live scan by introducing a governance reverse-link in a wayfinder-anchored archive (which is already lint-clean per `889d81c` post-archive drift closure H4).
- **CLAUDE.md §6 第 8 条**: `<a id="req-N"></a>` MUST precede every Requirement (100% coverage). The fix does NOT add or remove any anchor; it only corrects prose claims about an existing Requirement.
- **CLAUDE.md §3 / §6 第 7-8**: wayfinder tickets are advisory non-binding; this fix touches no ticket files.

## Goals / Non-Goals

**Goals:**
- Edit `archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` L12 to replace "(Req 32) added to `wayfinder`" with a lineage-correct parenthetical: `Requirement (originally added to wayfinder as req-33 in commit 6f22278; superseded by governance/req-gov-1 via commit 34b37be migrate-l678-source)`.
- Edit `archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` L22 (`### Modified Capabilities`) to replace "adds Requirement ... (3 Scenarios) to the `wayfinder` capability" with a lineage-correct description: "(historical: added to wayfinder as req-33 by commit 6f22278; current authoritative home is `governance/spec.md` `req-gov-1` after migration in commit 34b37be; orphan req-33 anchor in wayfinder cleaned up by 24118d6)" — preserves the `(3 Scenarios)` claim, corrects destination capability from `wayfinder` → `governance`.
- Add a reverse-link bullet in the same file's Impact section pointing to `openspec/specs/governance/spec.md` `req-gov-1` so future audit cycles grepping for the Requirement's lineage land on the proposal's reverse-link without depending on the spec-delta annotation block.
- Ensure `python scripts/lint_no_source_field_drift.py` exit=0 post-change (archive is not in the live lint scan set, but re-run for hygiene confirmation).
- Ensure `openspec validate --specs` and `openspec validate --change fix-archive-tighten-test-precision-tolerance-req-claim-drift` both pass post-change.

**Non-Goals:**
- **Not** modifying `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` (already carries comprehensive 3-section annotation block from `24118d6` 2026-09-24; editing it would conflict with the deliverable of change `fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian`).
- **Not** modifying `archive/2026-09-06-tighten-test-precision-tolerance/design.md` (cross-check verified: references to "the new `Test Guard Precision for Closed-Form Numerical Claims` requirement" at L84 and L104 do NOT claim `Req 32` or `added to wayfinder`; they describe the requirement generically without false anchors).
- **Not** modifying `archive/2026-09-06-tighten-test-precision-tolerance/tasks.md` (cross-check verified: no references to the new requirement's anchor at all; tasks describe test-side edits only).
- **Not** modifying `openspec/specs/wayfinder/spec.md` (live; already authoritative at `<a id="req-32">` L702 Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper, and `<a id="req-33">` does not exist post-24118d6 cleanup).
- **Not** modifying `openspec/specs/governance/spec.md` (live; already authoritative at `<a id="req-gov-1">` L9 Test Guard Precision for Closed-Form Numerical Claims).
- **Not** modifying `wayfinder/tickets/` — tickets are advisory non-binding per `CLAUDE.md §8`.
- **Not** modifying any line-number references (e.g., `L11` or `L22` pointers) in `proposal.md` or other archive files — those describe the apply-time state, distinct concern from anchor naming.
- **Not** modifying any `src/` code or `tests/` test — no production or test behavior change.
- **Not** checking whether other archive folders in `openspec/changes/archive/` carry similar prose-claim drift (those would be separate changes if determined in scope; this change is scoped exclusively to `2026-09-06-tighten-test-precision-tolerance/proposal.md`).

## Decisions

### Decision 1: Surgical 3-edit prose fix in 1 archive file, no live spec delta, `skip_specs: true`

**Choice**: This change uses `skip_specs: true` (`.openspec.yaml`) and modifies only `archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` (3 textual edits: L12, L22, Impact reverse-link bullet). No `specs/<capability>/spec.md` delta is created in the change directory.

**Rationale**: Per the OpenSpec spec-driven workflow rule "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation.":
- The 3 edits in `proposal.md` are descriptive prose claims about an existing Requirement. The Requirement body, anchor, and Scenarios in `governance/spec.md req-gov-1` are not modified.
- The drift is a writing error that persisted from `e437c2d` archive creation through `889d81c` post-archive drift closure; closing it is metadata accuracy, not Requirement semantics.

**Alternatives considered**:
- (a) Create a `specs/governance/spec.md` delta in the change directory with `## MODIFIED Requirements` containing a corrected "Test Guard Precision for Closed-Form Numerical Claims" block. **Rejected**: the canonical Requirement body in `governance/spec.md` is already correct; only the archive proposal.md prose claims were wrong. A MODIFIED delta against `governance/spec.md` would be a no-op and confuse `openspec validate`.
- (b) Touch only `specs/wayfinder/spec.md` (the archive spec delta file) — adding or amending an annotation block. **Rejected**: that file already carries a comprehensive annotation block from `24118d6` (L1-16, added by `fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian`). Editing it in this change would create a conflict with that change's deliverable; the existing block is sufficient.
- (c) Bulk-edit all 4 archive text files (`proposal.md` + `design.md` + `tasks.md` + `specs/wayfinder/spec.md`). **Rejected** by cross-check: `design.md` and `tasks.md` carry no `(Req 32)` or `added to wayfinder` claims (verified via grep 2026-09-24); `specs/wayfinder/spec.md` annotation block is comprehensive. Only `proposal.md` L12 + L22 require correction; bulk editing would introduce churn without value.

### Decision 2: L12 correction format — inline historical supersede parenthetical

**Choice**: Replace L12's "Requirement (Req 32) added to `wayfinder`" with: "Requirement (originally added to wayfinder as req-33 in commit 6f22278; superseded by governance/req-gov-1 via commit 34b37be migrate-l678-source)". Single parenthetical, embedded inline in the existing sentence structure.

**Rationale**: Per `wayfinder/tickets/A8-2.md` L70 + L74 (existing ticket-side `(historical, <value>; superseded by spec req-N L###)` pattern) and `governance/spec.md` req-gov-2 ("Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application"), the cross-link annotation format is the audit-trail standard for DecompMoE. Reusing it for proposal.md prose keeps the audit-trail format consistent with ticket-side annotations. The single-parenthetical form preserves the L12 paragraph's narrative flow ("The new `Test Guard Precision for Closed-Form Numerical Claims` Requirement (...) added to `wayfinder` is new test-side policy text — it does NOT modify the Req 11 closed-form values themselves.") without requiring restructuring.

**Alternatives considered**:
- (a) Use a free-form prose correction. **Rejected**: the `(historical, ...)` pattern is recognized by `scripts/lint_no_source_field_drift.py` for ticket-side annotations and recorded in `governance/spec.md` req-gov-2 as the canonical format. Free-form would not benefit from grep-based audit-trail queries.
- (b) Add a separate "Lineage note:" paragraph after L12. **Rejected**: the paragraph breaks the existing narrative flow ("The new X ... added to wayfinder ... does NOT modify Req 11"); a single inline parenthetical is less disruptive.
- (c) Delete the L12 paragraph's anchor claim entirely (e.g. "The new `Test Guard Precision for Closed-Form Numerical Claims` Requirement added to `wayfinder` is new test-side policy text — ..."). **Rejected**: deleting the number leaves no audit trail explaining where the Requirement landed; the parenthetical form records the lineage without disrupting readability.

### Decision 3: L22 correction — drop `(3 Scenarios)` count claim, correct destination capability

**Choice**: Replace L22's "adds Requirement `Test Guard Precision for Closed-Form Numerical Claims` (3 Scenarios) to the `wayfinder` capability" with: "(historical: added to wayfinder as req-33 by commit 6f22278; current authoritative home is `governance/spec.md` `req-gov-1` after migration in commit 34b37be; orphan req-33 anchor in wayfinder cleaned up by 24118d6)" — **drop** the `(3 Scenarios)` count claim entirely. Replace it with a clarifying note pointing readers to the L1-L16 HTML-comment annotation block on the archive spec.md file for full lineage (which explains the 2026-09-06 archive body is **NOT** what was applied to live spec).

**Rationale**: The `(3 Scenarios)` count claim in the original `e437c2d` proposal.md L22 was historically correct only for the **e437c2d archive delta body** (which has 3 Scenarios — the original 2026-09-06 proposal that was never applied as-is per `bec147d + 83a0503` policy reversal). The actual applied delta body in commit `6f22278` (which became `req-33` in wayfinder, then migrated to `req-gov-1` in governance) has **5 Scenarios** (verified via `git show 6f22278:openspec/changes/archive/2026-09-08-tighten-closed-form-eq-integer-checks/specs/wayfinder/spec.md | grep "Scenario:"` → 5 hits; `Select-String -Path "openspec\specs\governance\spec.md" -Pattern "Scenario:"` for req-gov-1 region L25-L45 → 5 hits). The destination capability name `wayfinder` is the mis-claim. **Dropping** the count entirely (rather than preserving "3" or fixing to "5") avoids perpetuating a count that was always ambiguous between archive body vs canonical body, and avoids expanding the change's scope to a fact-correction beyond the user's original instruction ("修正 proposal.md 描述" was scoped to the (Req 32)/wayfinder misattribution, not the (3 Scenarios) count).

**Alternatives considered**:
- (a) Preserve "(3 Scenarios)" with corrected attribution to the e437c2d archive body. **Rejected**: the count remains ambiguous to readers who don't realize the archive body ≠ canonical body; the L1-L16 annotation block already records this distinction.
- (b) Fix to "(5 Scenarios) (matching the `6f22278` delta body)". **Rejected** (this was the initial design but the review caught the wrong attribution): the count would be correct for canonical but mismatched with the e437c2d archive body; expanding scope to a fact-correction beyond user's narrow instruction.
- (c) **Drop** the `(3 Scenarios)` count claim from L22 entirely + add note pointing to L1-L16 annotation. **Accepted** (this is what we did).
- (d) Move the lineage description to a new bullet below L22. **Rejected**: the existing L22 bullet is the natural place for the corrected description; adding a sibling bullet would clutter the section.
- (e) Replace L22 entirely with a single sentence. **Rejected**: L22 is in `### Modified Capabilities` section and reads as a list item with a bullet; preserving its structural form aids grep-based audits.

### Decision 4: Add Impact reverse-link bullet to `governance/spec.md req-gov-1`

**Choice**: Add one bullet to the existing Impact section of `proposal.md`: "**反链**: `\`openspec/specs/governance/spec.md\` \`req-gov-1\` (Test Guard Precision for Closed-Form Numerical Claims — current authoritative home, migrated from wayfinder/req-33 by commit 34b37be)". This is the only addition to the proposal.md beyond the L12 + L22 corrections.

**Rationale**: The Impact section's existing reverse-link bullets point to: `CLAUDE.md` §6 第 8 条, `CLAUDE.md` §3, `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`, `tests/test_sphere.py::test_voronoi_rad_precision_alignment`. None of these point to the canonical spec home (`governance/spec.md req-gov-1`). Adding the reverse-link closes that gap and lets future audit cycles grepping for "where does this Requirement live canonically?" land on proposal.md without depending on the annotation block in `specs/wayfinder/spec.md`.

**Alternatives considered**:
- (a) Don't add the reverse-link; rely on the existing annotation block. **Rejected**: the annotation block is in a different file (`specs/wayfinder/spec.md`) and might be edited/moved by future changes; the proposal.md itself should carry its own reverse-link per the convention from `governance/spec.md` req-gov-2.
- (b) Replace the existing reverse-link bullets. **Rejected**: those bullets are still valid; the new reverse-link is additive.

## Risks / Trade-offs

- **[R1] L12 parenthetical may be misread as a separate claim** → **Mitigation**: the parenthetical is clearly bounded by parentheses and embeds the lineage inline; future readers can grep for `governance/req-gov-1` to find the canonical home. The pattern matches ticket-side `(historical, ...; superseded by ...)` from `wayfinder/tickets/A8-2.md` L70 + L74.
- **[R2] L22 correction may conflict with `openspec validate --change`** → **Mitigation**: `openspec validate --change` checks proposal structure (Why / What Changes / Capabilities / Impact sections) but does NOT validate prose claims. Replacing L22 text preserves the bullet structure (`- <description>`); the change passes validate as long as the bullet count and section structure remain intact.
- **[R3] Edit tool on Windows may introduce CRLF in non-ASCII content** → **Mitigation**: per CLAUDE.md hygiene lesson (2026-09-23, "Edit tool on Windows can introduce CRLF in non-ASCII files"), every modified file gets a byte-level CRLF check: `python -c "import sys; data=open(sys.argv[1],'rb').read(); print(data.count(b'\\r\\n'))" <file>` returns `0`. If non-zero, run strip-CRLF PowerShell snippet before commit. The proposal.md is non-ASCII (Chinese mixed with English) so this check is mandatory.
- **[R4] Adding reverse-link to Impact may trigger lint_no_source_field_drift.py if it expects wayfinder-primary reverse-link for archive proposal.md** → **Mitigation**: archive files are NOT in the live lint scan set (verified by `python scripts/lint_no_source_field_drift.py --help` and reading script logic); the archive's existing reverse-link bullet structure is unaffected. The new bullet adds an explicit reference to `governance/spec.md req-gov-1`, which is the appropriate primary reverse-link for the requirement lineage.
- **[R5] Future archive-corrective changes may re-introduce "(Req 32)" drift if they re-process this file** → **Mitigation**: out of scope to design a permanent anti-drift mechanism here. Documented as a known limitation; future archive-corrective changes would handle recurring drifts via the same surgical-edit convention.
- **[R6] Concurrent modification with `fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` (which annotated `specs/wayfinder/spec.md`) could cause merge conflicts** → **Mitigation**: this change explicitly excludes `specs/wayfinder/spec.md` from its edit set; the only file in this change's edit set is `proposal.md`. No concurrent-modification conflict with the sibling change.

## Migration Plan

Single-pass apply via Edit tool on 1 archive text file (no shell script, no live-spec edits, no archive-folder creation/deletion). The file is `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/proposal.md`. After apply, run byte-level CRLF check + lint + validate hygiene checks.

**Rollback** (if lint/validate fails post-apply): `git checkout HEAD -- openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` to restore pre-apply state. The file is git-tracked, so a clean rollback exists.

## Open Questions

(none — all decisions resolved via ask_user 2026-09-24: change scope = new change, name = fix-archive-tighten-test-precision-tolerance-req-claim-drift, annotation detail = 3-section — though the 3-section structure ends up being implicit in the L12 parenthetical rather than a separate annotation block, because the existing block on `specs/wayfinder/spec.md` is already comprehensive from `24118d6`.)