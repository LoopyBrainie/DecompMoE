## Context

See `proposal.md` (## Why) for motivation: `openspec/specs/wayfinder/spec.md` L678 (req-33) carries a `**Source:**` line that fails `scripts/lint_no_source_field_drift.py` (currently informational-only per CLAUDE.md §3 L28, will become gate post-this-change). The change closes the only known violation AND atomically wires the lint script into the `/opsx:archive` gate per the `fix-wayfinder-spec-source-field-drift/proposal.md` "Open Follow-ups → migrate-l678-source" section's "强制决策要求" + "强制同步接线" mandates. Brief restatement of constraints that shape the design:

- Per `fix-wayfinder-spec-source-field-drift/proposal.md` "强制决策要求", this change's `proposal.md` MUST contain an explicit 2.7 Decision Record selecting ONE of 4 options (a/b/c/d). Option (a) "split capability migration" is the recommended default per the same source. Options (c) "create new ticket" is forbidden by CLAUDE.md §6 第 6 条 ("不要重写 wayfinder ticket 来调和 spec 与 ticket 不一致"). Option (d) "permanent informational-only" defeats the lint gate. Option (b) "weak ticket annotation" requires picking a weak A* ticket with WEAK annotation — accepted by the source change but not recommended.
- Per the same source's "强制同步接线" mandate, the 5 actions (move req-33 to governance, update lint script content for per-capability rule, modify CLAUDE.md §3, delete KNOWN_OPEN_VIOLATIONS, verify lint exit=0) MUST ship in a single change. Splitting creates the same drift pattern the gate exists to prevent.
- The `wayfinder/spec.md` req-34 last Scenario ("governance-origin requirements trigger lint failure", L726-732) explicitly mandates migration to `openspec/specs/governance/spec.md` for any governance-origin Requirement — this change satisfies that mandate for req-33 and establishes the precedent for future governance-origin additions.
- Lint script `scripts/lint_no_source_field_drift.py` is content-based (substring `wayfinder/tickets/`) per its design; moving the Requirement out of `openspec/specs/wayfinder/` removes the violation regardless of how the moved Requirement's new Source field is written.

## Goals / Non-Goals

**Goals:**
- Move `openspec/specs/wayfinder/spec.md` L662-L704 (req-33 + 5 Scenarios + `<a id="req-33">` anchor) verbatim into a NEW capability `openspec/specs/governance/spec.md`; rewrite the moved Requirement's `**Source:**` field in governance-compliant form (CLAUDE.md lineage, no `wayfinder/tickets/` reference).
- **Modify `scripts/lint_no_source_field_drift.py` content (rule becomes per-capability)**: the current rule requires `wayfinder/tickets/` substring in every `**Source:**` line of every `openspec/specs/**/spec.md`. With `governance` capability introducing CLAUDE.md-amendment lineage, this becomes a per-capability rule: `openspec/specs/governance/spec.md` Source lines MUST contain `CLAUDE.md`; all other spec paths (`wayfinder/`, `decompmoe-skeleton/`) MUST retain the `wayfinder/tickets/` requirement. The rule stays content-based (substring search) per the source change's design constraints; the per-capability mapping is hardcoded in the script (no exemption-table rot, no CLI flag, no env var — same anti-pattern guardrails as the original rule).
- Wire `python scripts/lint_no_source_field_drift.py` into `/opsx:archive` precondition by modifying CLAUDE.md §3 L28 to drop the `informational-only` clause and replace the `migrate-l678-source` follow-up reference with both lint scripts running at gate.
- Delete the `KNOWN_OPEN_VIOLATIONS` section (header + 17 lines) from `scripts/lint_no_source_field_drift.py` docstring; the section becomes stale once the migration archives.
- Verify `python scripts/lint_no_source_field_drift.py` exits 0 against the post-archive spec tree (binding acceptance criterion per the "强制同步接线" mandate).
- All 5 actions in the same single change (no splitting); the change's `/opsx:archive` either succeeds with all 5 in place or fails with the lint gate revealing the missing piece.

**Non-Goals:**
- No code changes to `src/decompmoe/` (the L678 Requirement governs test-assertion-form, not production code; the test files in `tests/` are unchanged at the implementation level — only the spec-side citation moves from wayfinder to governance).
- No edits to `openspec/specs/wayfinder/spec.md` req-34 `Source Field Format Invariant for OpenSpec Specs` (L706-L732) — req-34 STAYS in wayfinder because (a) it carries no `**Source:**` line (it's a rule definition, not a content requirement; the lint rule only flags existing Source lines), (b) its "governance-origin requirements trigger lint failure" Scenario IS the rule that mandates this migration, (c) moving req-34 would create a circular dependency (req-34 mandates governance migration; governance migration depends on req-34 staying in wayfinder to define the rule).
- No edits to `openspec/specs/decompmoe-skeleton/spec.md` — the decompmoe-skeleton capability has 2 Source fields (L208, L359) both with `wayfinder/tickets/A6a-2.md` references; both pass lint; no migration needed.
- No edits to `openspec/specs/governance/spec.md` Source-field convention — the convention is described in the moved Requirement's rewritten Source line + the new capability's `## Purpose` section. Future governance additions follow the same pattern (CLAUDE.md lineage + amendment commits + change Decision 反链).
- No retroactive fix of the 2026-09-11 `add-should-resurrect-per-step-math-derivation` change's review-time Source injection (that change applied Option 1 "delete Source from delta" — the spec body is now clean, no further action needed).
- No deprecation of the `Open follow-up` clause in any other change's design.md (out of scope; the follow-up gate wiring is what this change accomplishes).

## Decisions

### Decision 1: Adopt option (a) — split capability migration to `openspec/specs/governance/spec.md`

**Chosen**: Move req-33 (Test Guard Precision for Closed-Form Numerical Claims) verbatim from `openspec/specs/wayfinder/spec.md` L662-L704 to a new `openspec/specs/governance/spec.md` file. The new capability's `## Purpose` section (per OpenSpec spec-driven schema's "New capabilities only: start the delta spec with a `## Purpose` section" rule) declares the capability's scope: governance-origin specs whose design lineage is `CLAUDE.md` amendments. The moved Requirement's new `**Source:**` field rewrites the lineage from `wayfinder/tickets/` to `CLAUDE.md` §6 第 8 条 + amendment commits + change Decision 反链.

**Rationale**:
- The 4-option decision matrix in `fix-wayfinder-spec-source-field-drift/proposal.md` "Open Follow-ups → migrate-l678-source" section identifies (a) as the recommended option: "字面承认 governance lineage 是一等公民". This aligns with req-34's "governance-origin requirements trigger lint failure" Scenario which explicitly names `openspec/specs/governance/spec.md` as the migration target.
- Options (c) and (d) are forbidden: (c) "create new ticket" violates CLAUDE.md §6 第 6 条 ("不要重写 wayfinder ticket 来调和 spec 与 ticket 不一致"); (d) "permanent informational-only" defeats the lint gate (退化为"装了锁不上门").
- Option (b) "weak ticket annotation" was accepted by the source change as a WEAK-annotation option but requires fabricating a weak A* ticket reference. The fact that a WEAK reference is necessary is itself diagnostic of misplaced lineage — moving to governance capability is the honest fix per `fix-wayfinder-spec-source-field-drift/proposal.md` Decision 4 rationale: "Patching it with a `(historical, ...)` annotation would be dishonest; the design intent of this change is that the lint rule **fail** on L678, signalling that it must migrate to a `governance` capability in a separate change."
- The 2026-09-11 audit incident (an unrelated change `add-should-resurrect-per-step-math-derivation` attempted a Scenario-level Source injection; intercepted by human review) further validates the need: the lint gate is the only sustainable enforcement mechanism, and option (a) is the only path to making it pass cleanly without re-fabricating ticket lineage.

**Alternatives considered**:
- *B (rejected)*: Weak ticket annotation in wayfinder spec — accepts WEAK `(historical, ...)` annotation pointing at e.g. `wayfinder/tickets/A8-3.md` or `WF-1.md` with connection rationale. Same exemption-by-stealth problem the lint rule was written to prevent; the `fix-wayfinder-spec-source-field-drift/proposal.md` Decision 4 already rejected this for L678 specifically ("Patching L678 with `wayfinder/tickets/A4-1.md` and a long annotation — rejected (false attribution; A4-1 is about β parameterization, not test precision)").
- *C (rejected)*: Create new wayfinder ticket for L678 — CLAUDE.md §6 第 6 条 "不要重写 wayfinder ticket 来调和 spec 与 ticket 不一致"; new ticket is creation not rewrite but spirit of the rule (no ticket fabrication to mask governance lineage) applies.
- *D (rejected)*: Accept permanent informational-only — defeats lint gate; "装了锁不上门" regression of the source change's intent.

### Decision 2: governance capability structure — single Requirement initially, anchor scheme `req-gov-N`

**Chosen**: The new `openspec/specs/governance/spec.md` carries:
- `## Purpose` section per OpenSpec spec-driven schema's "New capabilities only" rule (one or two sentences declaring scope).
- One Requirement initially: the moved `Requirement: Test Guard Precision for Closed-Form Numerical Claims` with anchor `<a id="req-gov-1"></a>` (new naming scheme `req-gov-N` to distinguish governance requirements from `wayfinder`'s `req-N` scheme).
- The 5 Scenarios moved verbatim (no wording changes; only the file location changes).
- Rewritten `**Source:**` field per Decision 3.

The `## Purpose` section declares the capability's scope so future governance-origin additions can file under `governance` (per the migration rule in `wayfinder/spec.md` req-34).

**Rationale**:
- The `req-gov-N` anchor scheme is parallel to but distinct from wayfinder's `req-N` scheme to avoid any cross-capability anchor collision (e.g., wayfinder `req-33` currently exists; future governance `req-gov-33` would not collide). The `<a id="...">` HTML anchors are file-scoped in practice (a reader navigating via `req-N` in wayfinder vs `req-gov-N` in governance sees the right file), but the prefix also serves as a human-readable disambiguator.
- Single-Requirement initial state matches the source state (req-33 was the only governance-origin Requirement); future additions would follow the same pattern.
- The `## Purpose` section is mandatory for new capabilities per OpenSpec spec-driven schema; without it archive fails with `TBD ... Update Purpose after archive` placeholder (per `openspec instructions specs` instruction text).

**Alternatives considered**:
- *A (rejected)*: Reuse wayfinder's `req-33` anchor in the new file (`<a id="req-33">`). Rejected because anchors are conventionally file-scoped; using the same anchor in two files risks cross-reference confusion if a future document links to `req-33` ambiguously.
- *B (rejected)*: Use no anchor on the moved Requirement. Rejected because the current wayfinder spec uses anchors per Requirement (33 anchors for 34 Requirements — req-34 is unanchored, an inconsistency); the moved Requirement should follow the anchored pattern to keep cross-spec references stable.

### Decision 3: governance Source field format — CLAUDE.md lineage + amendment commits + change Decision 反链

**Chosen**: The moved Requirement's rewritten `**Source:**` field follows this template:

```
**Source:** `CLAUDE.md` §6 第 8 条 (amended by <commit-sha> YYYY-MM-DD HH:MM:SS),
`CLAUDE.md` §3 (sync-amended by <commit-sha> YYYY-MM-DD HH:MM:SS);
change `<source-change-name>` design.md (Decision <N> — <one-line summary>);
change `migrate-l678-source` design.md (Decision 1 — option (a) governance-capability migration
per `<source-change-name>/proposal.md` "Open Follow-ups → migrate-l678-source" section).
```

**AND** the lint script `scripts/lint_no_source_field_drift.py` is updated to enforce a per-capability Source rule: `openspec/specs/governance/spec.md` Source lines MUST contain `CLAUDE.md` substring (rather than `wayfinder/tickets/`); all other `openspec/specs/**/spec.md` Source lines retain the existing `wayfinder/tickets/` requirement. The per-capability mapping is hardcoded as a small table in the script (no exemption registry, no CLI flag, no env var — same anti-pattern guardrails as the original rule).

For the moved req-33, the actual values are:
- `CLAUDE.md` §6 第 8 条 amended by `bec147d` 2026-09-07 21:21:31
- `CLAUDE.md` §3 sync-amended by `83a0503` 2026-09-07 22:02:52
- change `fix-wayfinder-spec-source-field-drift` design.md Decision 4 (L678 intentional debt + governance-migration signal)
- change `migrate-l678-source` design.md Decision 1 (option (a) governance-capability migration)
- Test anchors unchanged from pre-migration form (5 test files, ~10 test function names)
- Archive reference: `archive/2026-09-06-tighten-test-precision-tolerance/design.md` Decision 4 (the original carve-out being closed — now superseded by `bec147d` + `83a0503` policy reversal)

**Rationale**:
- The Source field is the spec's audit-trail field; for governance-origin Requirements, the audit trail points at governance artifacts (`CLAUDE.md` + commits + governance-mandated changes), NOT at `wayfinder/tickets/`.
- The `fix-wayfinder-spec-source-field-drift/proposal.md` Decision 4 verbatim wording is preserved where applicable ("now superseded by `bec147d` + `83a0503` policy reversal") so future readers can reconstruct the design history without leaving the spec.
- The template's "test anchors" + "archive reference" sections preserve the test-anchor audit trail (5 test files, ~10 test function names) intact — only the citation location moves (wayfinder req-33 → governance req-gov-1).
- The format aligns with the existing wayfinder Source convention (backtick-quoted file paths, comma-separated clauses, optional `(historical, ...)` annotation when superseding prior values).

**Alternatives considered**:
- *A (rejected)*: Omit the change Decision 反链 and rely solely on CLAUDE.md lineage. Rejected because the audit trail then loses the intermediate "why we knew this was governance-origin" decision (`fix-wayfinder-spec-source-field-drift` Decision 4) and the migration authorization (`fix-wayfinder-spec-source-field-drift/proposal.md` "Open Follow-ups → migrate-l678-source"). Future readers would not know why this Requirement was moved out of wayfinder.
- *B (rejected)*: Use `(historical, ...)` annotation format to record the pre-migration `**Source:**` content. Rejected because `(historical, ...)` is reserved for `wayfinder/tickets/` value-vs-spec-value divergence (per `wayfinder/spec.md` req-34 "superseded values use the historical annotation format" Scenario); the pre-migration Source line was governance-origin, not wayfinder-ticketed, so the annotation format does not apply.
- *C (rejected)*: Keep the lint script's rule uniform (every Source line in `openspec/specs/**/spec.md` MUST contain `wayfinder/tickets/`), and document the governance spec's CLAUDE.md-lineage Source as an expected-info exception. Rejected because the source change's design constraint explicitly forbids exemption-table-style exceptions ("NO exemption table (not `JUSTIFIED_EXEMPTIONS`, not per-line `# noqa`, not env var, not CLI flag)"). The per-capability rule replaces a uniform rule with a hardcoded 2-row table (still content-based, still no rot-prone exemption registry).

### Decision 4: Atomicity — all 5 actions in single change, lint exit=0 binding

**Chosen**: This change ships all 5 actions in one commit/merge:
1. `specs/governance/spec.md` (NEW capability) added
2. `specs/wayfinder/spec.md` req-33 removed (REMOVED Requirement)
3. `scripts/lint_no_source_field_drift.py` content updated (per-capability Source rule)
4. `CLAUDE.md` §3 L28 modified (lint script wired into gate)
5. `scripts/lint_no_source_field_drift.py` docstring `KNOWN_OPEN_VIOLATIONS` section deleted

The binding acceptance criterion is `python scripts/lint_no_source_field_drift.py` → exit=0 against the post-archive spec tree. If at any pre-archive step the lint already exits 0 (e.g., the spec delta + per-capability rule together remove the violation before the CLAUDE.md change), the archive still requires the CLAUDE.md + script changes to ship atomically (the lint script must be wired into the gate at the same time as the violation is closed, per `fix-wayfinder-spec-source-field-drift/proposal.md` "强制同步接线" mandate).

**Rationale**:
- The source change explicitly mandates atomicity ("不允许把'L678 解决'和'gate 接线'拆成两个独立 change——中间态(脚本存在但 gate 未接)会重蹈本 change 闭环前的覆辙,CLAUDE.md §3 bullet 与脚本行为的对应关系会再次漂移").
- The archive precondition `lint_no_source_field_drift.py` → exit=0 becomes enforceable in this change's archive step (via CLAUDE.md §3 modification); any future change that re-introduces a violation will be rejected at archive time.
- The `KNOWN_OPEN_VIOLATIONS` deletion is mandatory because the docstring currently advertises "exit code 1, exactly 1 violation on L678" as expected behavior; post-archive the script exits 0, contradicting the docstring. Leaving the docstring as-is would create a fresh drift between the script's runtime behavior and its docstring claim.
- The lint script's per-capability rule (Decision 3 alignment, Action 3 above) MUST ship in the same commit as the governance capability creation. Without it, the governance spec's CLAUDE.md-lineage Source line would fail the lint gate at archive time, blocking this change's archive — defeating the change's purpose. The per-capability rule preserves the source change's design constraints (content-based substring search, no exemption table, no CLI flag, no env var) by hardcoding the per-capability mapping in the script (still no rot-prone exemption table).

**Alternatives considered**:
- *A (rejected)*: Split into two changes (one for spec migration, one for lint gate wiring). Rejected per the source change's atomicity mandate; the intermediate state ("script exists but gate not wired") recreates the drift pattern that motivated the source change.
- *B (rejected)*: Keep `KNOWN_OPEN_VIOLATIONS` section as historical record with an "as of YYYY-MM-DD" timestamp. Rejected because the section's wording ("Expected behavior: exit code 1, exactly 1 violation on L678") becomes false post-archive; a stale "historical" section would be the same drift pattern the lint script was written to prevent.

## Risks / Trade-offs

- [R1: The moved Requirement's `## Purpose` of the new `governance` capability may be too narrow to admit future governance-origin additions cleanly] → Mitigation: the `## Purpose` section is written to admit any governance-origin Requirement (CLAUDE.md amendment lineage, not wayfinder-tickets), not just the moved req-33. If a future addition requires broader scope (e.g., commit-amended spec lines that aren't CLAUDE.md-amended), the `## Purpose` can be amended in that future change without requiring this change to be re-opened.
- [R2: The `req-gov-N` anchor scheme diverges from wayfinder's `req-N` scheme; future cross-capability references (e.g., wayfinder spec citing governance capability) may use the wrong anchor] → Mitigation: the `req-gov-N` prefix is explicitly designed to be self-identifying; future cross-capability references use the full anchor string. The lint script does not parse anchors, so anchor scheme divergence has no script-side impact.
- [R3: Lint script regression — if a future change re-introduces an un-ticketed Source line in `openspec/specs/wayfinder/spec.md`, the script will fail at archive time (now gated); the archive will be rejected, surfacing the regression] → Mitigation: this is the intended behavior per `fix-wayfinder-spec-source-field-drift` change. The script's docstring (post-`KNOWN_OPEN_VIOLATIONS` deletion) will document exit=0 as the expected state; any exit=1 archive rejection will be a regression signal, not a normal state.
- [R4: The `CLAUDE.md` §3 L28 wording change may be misread as a relaxation of the archive gate (if a reviewer assumes `lint_no_source_field_drift.py` is optional)] → Mitigation: the new wording is explicit ("both lint scripts run as `/opsx:archive` preconditions") with parallel structure to the existing `lint_no_dead_defensive.py` mention immediately above on the same bullet. A reviewer skimming CLAUDE.md §3 will see the pattern.
- [R5: Atomicity breakage — if a developer applies this change in two commits (one for spec move + lint content, one for gate wire), the intermediate commit will leave the lint script failing exit=1 while not yet wired into the gate; this is functionally equivalent to today's pre-change state, but creates a `git log` archaeology question for future audits] → Mitigation: `tasks.md` §2 (the single tooling task group) is structured so all 5 actions are checked off in the same session; no intermediate commit should be created between them. If an intermediate commit is unavoidable (e.g., git plumbing issue), the post-archive independent verification §5.2 explicitly verifies the merge commit on `dev` contains all 5 changes atomically.
- [R6: The 2026-09-11 `add-should-resurrect-per-step-math-derivation` change's Option 1 fix (delete Scenario-level Source) means no `decompmoe-skeleton` Source changes are needed in this change; if a reviewer assumes this change should also retrofit that change's spec, scope creep] → Mitigation: `proposal.md` Impact explicitly states "No retroactive fix of the 2026-09-11 `add-should-resurrect-per-step-math-derivation` change's review-time Source injection"; scope is L678 + governance capability + gate wiring only.

## Migration Plan

1. `/opsx:propose` complete (current state): `proposal.md` (option (a) Decision Record) + `specs/governance/spec.md` (NEW capability) + `specs/wayfinder/spec.md` (REMOVED Requirement) + `design.md` (4 Decisions) + `tasks.md` all written; all 4 artifacts marked `done` by `openspec status`.
2. **User review**: read `proposal.md` for the option (a) Decision Record, `specs/governance/spec.md` for the moved Requirement's rewritten Source field (verify CLAUDE.md lineage + amendment commits + change Decision 反链 format), `specs/wayfinder/spec.md` for the REMOVED Requirement's Reason + Migration text. Confirm the `req-gov-1` anchor scheme + `## Purpose` text are sufficient for future governance additions.
3. **Pre-archive lint gate** (per CLAUDE.md §3 archive precondition — UNCHANGED in this change; the change itself ENABLES the gate wiring for FUTURE changes): `python scripts/lint_no_dead_defensive.py` must exit 0. `python scripts/lint_no_source_field_drift.py` exit code is informational at this point (the script's gate wiring is in this change's commit, but the spec delta alone — moving req-33 to governance — already closes the violation; pre-archive lint should exit=0 against the spec delta state).
4. **Apply atomicity check**: verify all 5 actions are present in `openspec/changes/migrate-l678-source/` artifacts before `/opsx:archive` (governance spec file exists, wayfinder REMOVED block present in delta spec, lint script content implements per-capability rule, CLAUDE.md change in scope, lint script docstring change in scope). If any one is missing, abort archive and re-run the missing artifact's `openspec instructions` to regenerate it.
5. **`/opsx:archive`**: archive merges `specs/governance/spec.md` → `openspec/specs/governance/spec.md` (new file created) + `specs/wayfinder/spec.md` → main `openspec/specs/wayfinder/spec.md` (req-33 removed; requirement count drops 34 → 33). The change directory moves to `openspec/changes/archive/2026-09-XX-migrate-l678-source/`. The archive step itself runs both lint scripts as precondition (CLAUDE.md §3 gate); both must exit=0.
6. **Post-archive independent verification** (per CLAUDE.md §3 "Post-archive 独立复核" 强制项): verify (a) `openspec/specs/governance/spec.md` exists and carries the moved Requirement verbatim with rewritten Source field, (b) `openspec/specs/wayfinder/spec.md` has req-33 deleted and req-34 intact, (c) `python scripts/lint_no_source_field_drift.py` exits 0 against the merged spec tree, (d) `scripts/lint_no_source_field_drift.py` docstring `KNOWN_OPEN_VIOLATIONS` section deleted, (e) `CLAUDE.md` §3 L28 wording reflects both lint scripts as gate preconditions.
7. **Rollback strategy**: `git revert` the archive merge commit. Because the change is spec + tooling + governance artifact only (no production code, no test code), rollback is low-risk. The lint script's gate wiring would revert to informational-only; the spec delta (governance capability added, req-33 removed) would also revert; the system returns to the pre-change state. The `fix-wayfinder-spec-source-field-drift/proposal.md` "Open Follow-ups → migrate-l678-source" follow-up marker would need to be re-opened.

## Open Questions

(none) — all decisions resolved; option (a) is the recommended path per the source change's Decision Record, and the 4 alternative options (b/c/d) are explicitly rejected in the same source.
