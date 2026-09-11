## Why

`openspec/specs/wayfinder/spec.md` L678 (req-33 `Test Guard Precision for Closed-Form Numerical Claims`) currently carries a `**Source:**` field whose lineage is `CLAUDE.md` §6 第 8 条 (amended by commits `bec147d` 2026-09-07 + `83a0503` 2026-09-07), NOT any `wayfinder/tickets/*.md` ticket. This is the **single violation** that `scripts/lint_no_source_field_drift.py` (introduced by the archived change `fix-wayfinder-spec-source-field-drift`) reports today — `exit=1, 1 violation on L678`. Per the same change's proposal "Open Follow-ups → `migrate-l678-source`" section, this follow-up is **explicitly required** to close L678 + atomically wire `lint_no_source_field_drift.py` into the archive gate (CLAUDE.md §3 L28). Without this closure, the lint script remains informational-only and the next change that injects an un-ticketed Source line (already happened on 2026-09-11 with `add-should-resurrect-per-step-math-derivation`, intercepted by human review per audit log) continues to bypass automated enforcement.

## What Changes

- **Move req-33 from `wayfinder` to NEW `governance` capability** (option (a) of the 4-option decision matrix in `fix-wayfinder-spec-source-field-drift/proposal.md`): copy the Requirement body + 5 Scenarios + anchor `<a id="req-33">` verbatim from `openspec/specs/wayfinder/spec.md` L662-L704 into a new `openspec/specs/governance/spec.md`. The moved Requirement's `**Source:**` field is rewritten in governance-compliant format (references `CLAUDE.md` §6 第 8 条 + amendment commits + `fix-wayfinder-spec-source-field-drift` design.md Decision 4 + this change's design Decision 1; no `wayfinder/tickets/` reference required because the file lives outside `openspec/specs/wayfinder/`).
- **Remove req-33 from `wayfinder`**: delete the anchor + Requirement header + body + 5 Scenarios from `openspec/specs/wayfinder/spec.md` L662-L704 (req-34 `Source Field Format Invariant` L706-L732 STAYS — it is the rule itself and contains the "governance-origin requirements trigger lint failure" Scenario that mandates this migration).
- **Modify `CLAUDE.md` §3 L28**: replace the `lint_no_source_field_drift.py` informational-only wording with the gate-wired form (consistent with `lint_no_dead_defensive.py` immediately above it on the same line). Both lint scripts run as `/opsx:archive` preconditions.
- **Delete the `KNOWN_OPEN_VIOLATIONS` section** from `scripts/lint_no_source_field_drift.py` docstring (header + 17 lines). After this change's archive, the script's only known violation is closed; the docstring must NOT advertise stale state.
- **Verify `python scripts/lint_no_source_field_drift.py` exits 0** against the post-archive spec tree (post-merge of both `specs/governance/spec.md` and modified `specs/wayfinder/spec.md`). This is the binding acceptance criterion.

No code changes (`src/decompmoe/` untouched). No test changes (`tests/` untouched). Atomicity is mandatory: the 5 changes (move req-33 to governance, update lint script content for per-capability rule, gate wire via CLAUDE.md §3, delete KNOWN_OPEN_VIOLATIONS, verify lint exit=0) MUST ship in a single change per `fix-wayfinder-spec-source-field-drift/proposal.md` "强制同步接线" mandate — splitting creates the same drift pattern the lint gate exists to prevent.

## Capabilities

### New Capabilities

- `governance`: OpenSpec governance specs whose design origin is `CLAUDE.md` amendments (or commits amending `CLAUDE.md`) rather than `wayfinder/tickets/*.md`. This capability exists as a peer of `wayfinder` and `decompmoe-skeleton` because governance-origin Requirements cannot carry a `wayfinder/tickets/` reverse-link in their `**Source:**` field (it would be dishonest attribution per `CLAUDE.md` §6 第 6 条 "不要重写 wayfinder ticket 来调和 spec 与 ticket 不一致"). The `governance` capability's Source convention is described in its first Requirement (this change's archive creates it). Future governance-origin Requirements added in later changes MUST be filed under `governance`, not `wayfinder` or `decompmoe-skeleton` — enforced by the `lint_no_source_field_drift.py` rule "any such requirement whose honest annotation cannot be written ... MUST be migrated to a separate governance capability (e.g. `openspec/specs/governance/spec.md`) before archive" (req-34 last Scenario in `wayfinder/spec.md` L726-732).

### Modified Capabilities

- `wayfinder`: remove `Requirement: Test Guard Precision for Closed-Form Numerical Claims` (req-33) and its 5 Scenarios (currently L662-L704 of `openspec/specs/wayfinder/spec.md`). The remaining 33 Requirements + req-34 (`Source Field Format Invariant for OpenSpec Specs`, L706-L732) are unchanged. The capability's Requirement count drops from 34 to 33 post-archive. No new Source fields added in `wayfinder`; the only Source change is deletion.

## Impact

- **Spec artifacts**:
  - `openspec/specs/governance/spec.md` — NEW file (~45 lines: 1 Requirement + 5 Scenarios + 1 Source field + `<a id="req-gov-1">` anchor); created by archive-merge of `specs/governance/spec.md` in this change.
  - `openspec/specs/wayfinder/spec.md` — ~43 lines deleted (L662-L704 inclusive of blank separator before req-34); requirement count drops 34 → 33.
- **Governance artifacts**:
  - `CLAUDE.md` — §3 L28 wording change (single sentence; the bullet becomes "lint gate 必须 `exit=0` (跑 `python scripts/lint_no_dead_defensive.py` + `python scripts/lint_no_source_field_drift.py`)"; `lint_no_source_field_drift.py` informational-only clause + `migrate-l678-source` follow-up reference deleted).
- **Tooling artifacts**:
  - `scripts/lint_no_source_field_drift.py` — two changes:
    1. **Content (rule itself)**: the current rule requires every `**Source:**` line in `openspec/specs/**/spec.md` to contain the literal `wayfinder/tickets/` substring. This was correct when only `wayfinder` and `decompmoe-skeleton` existed (both use wayfinder-ticket lineage). With the new `governance` capability's CLAUDE.md-amendment lineage, the rule becomes per-capability: `openspec/specs/governance/spec.md` Source lines MUST contain `CLAUDE.md`; all other spec paths MUST retain the `wayfinder/tickets/` requirement. The rule is still content-based (substring search) per the source change's design constraints; the per-capability table is hardcoded in the script (no exemption-table rot, no CLI flag, no env var — same anti-pattern guardrails as the original rule).
    2. **Docstring**: `KNOWN_OPEN_VIOLATIONS` section (~17 lines including header) deleted; the section becomes stale once this change's archive closes the L678 violation.
- **Code layer**: zero changes (no `src/decompmoe/` edits).
- **Test layer**: zero changes (no `tests/` edits).
- **Lint gate behavior**:
  - **Before**: `python scripts/lint_no_source_field_drift.py` → `exit=1, 1 violation on L678` (informational-only per CLAUDE.md §3 L28); `python scripts/lint_no_dead_defensive.py` → gate.
  - **After (post-archive)**: `python scripts/lint_no_source_field_drift.py` → `exit=0, 0 violations` (now gate); `python scripts/lint_no_dead_defensive.py` → gate (unchanged).
- **Archive precondition** (per CLAUDE.md §3 L28 after this change's archive): `/opsx:archive` MUST run both lint scripts with exit=0; previously the second was informational-only.
