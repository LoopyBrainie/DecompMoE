# Design

## Context

See `proposal.md` Why for motivation. Current state of the two defects being closed:

1. **Orphan anchor at `openspec/specs/wayfinder/spec.md` L740**: the line `<a id="req-33"></a>` exists but no `### Requirement:` title follows (the next title is `req-34` Source Field Format Invariant at L744). The `<a id="req-N"></a>` ↔ `### Requirement: <title>` invariant from `CLAUDE.md` §6 第 8 条 is broken at this single anchor.

2. **Archive delta at `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md`**: 28 lines added by commit `e437c2d` (2026-09-17) representing the **original 2026-09-06 proposal** to add req-33 to `wayfinder/spec.md`. The proposal's policy (`pytest.approx(..., abs=0)` for integer closed-form) was reversed by `bec147d + 83a0503` (2026-09-07) before any apply. The archive delta was never applied as a delta to live `wayfinder/spec.md`. The actual final landing of the closed-form-precision policy happened via `tighten-closed-form-eq-integer-checks` (commit `6f22278`) which added req-33 to live `wayfinder/spec.md`, then via `migrate-l678-source` (commit `34b37be`) which migrated it to live `governance/spec.md` as `req-gov-1`. The archive delta file currently has no `(historical, ...)` supersede annotation, making it easy to mis-read as "what was added to live wayfinder/spec.md".

Constraints:
- `CLAUDE.md` §6 第 8 条: `<a id="req-N"></a>` MUST precede every Requirement, 100% coverage. (No requirement says it MUST NOT precede orphan anchors, but the spirit of the invariant is one-anchor-per-Requirement.)
- `scripts/lint_no_source_field_drift.py` per-capability reverse-link rule (introduced by commit `34b37be`): governance/ spec → MUST contain `CLAUDE.md` back-link; wayfinder/ spec → MUST contain `wayfinder/tickets/` back-link. Closing this change MUST NOT break this rule.
- OpenSpec archive convention: archive files are immutable audit-trail records. Annotation blocks added to archive files are metadata, not part of any live spec.

## Goals / Non-Goals

**Goals:**
- Delete the single orphan anchor line at `openspec/specs/wayfinder/spec.md` L740 (1-line edit).
- Prepend a `(historical, ...; superseded by ...)` annotation block to `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` recording: (i) original proposal date 2026-09-06, (ii) policy reversal by `bec147d + 83a0503`, (iii) final landing as `governance/req-gov-1` via `migrate-l678-source` (commit `34b37be`).
- Ensure `python scripts/lint_no_source_field_drift.py` exit=0 post-change.
- Ensure `openspec validate --specs` and `openspec validate --change <name>` both pass post-change.

**Non-Goals:**
- Not adding the `Test Guard Precision for Closed-Form Numerical Claims` Requirement body to `wayfinder/spec.md` — it lives at `governance/spec.md` req-gov-1 (authoritative since 2026-09-12), and re-adding it to wayfinder/spec.md would violate `scripts/lint_no_source_field_drift.py` per-capability reverse-link rule (governance-origin Requirements MUST live in governance/).
- Not changing `governance/spec.md` req-gov-1 content — already authoritative and unchanged by this change.
- Not changing `e437c2d` commit message or history — the commit's body accurately states "current authoritative home is governance/req-gov-1"; the misleading delta is the archive file itself, not the commit message.
- Not touching any `wayfinder/tickets/*.md` file — tickets are reference-only per `CLAUDE.md` §6 第 7 + §8.
- Not touching `src/` code or `tests/` — no production or test behavior change.

## Decisions

### Decision 1: Surgical 2-edit change, no live spec delta file

**Choice**: This change uses `skip_specs: true` and modifies the two text files directly in the apply phase. No `specs/<capability>/spec.md` delta is created in the change directory.

**Rationale**: Per the OpenSpec spec-driven workflow rule "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation.":
- The orphan anchor removal does not change any Requirement semantics — it only enforces structural consistency of the `<a id="req-N"></a>` ↔ `### Requirement: <title>` invariant from `CLAUDE.md` §6 第 8 条.
- The archive annotation does not modify any live spec — archive files are immutable audit-trail records; the annotation is historical metadata.

**Alternatives considered**:
- (a) Create a `specs/wayfinder/spec.md` delta in the change directory with `## REMOVED Requirements` containing an empty `### Requirement: <req-33>` placeholder. Rejected: an empty Requirement is structurally invalid (no WHEN/THEN clause); REMOVED format requires a `Reason` + `Migration` describing an actual Requirement being removed, not an anchor.
- (b) Create a `specs/wayfinder/spec.md` delta with a custom annotation section. Rejected: spec-driven schema enforces ADDED/MODIFIED/REMOVED/RENAMED headers; custom headers are not part of the schema.

### Decision 2: Annotation block format mirrors ticket supersede pattern

**Choice**: Use the `(historical, <原值 reading>; superseded by spec req-N L### via <change> Decision M)` pattern from `wayfinder/tickets/A8-2.md` L70 + L74, adapted for an archive delta file context: `(historical, original proposal superseded; req-33 finally landed as governance/req-gov-1 via migrate-l678-source commit 34b37be)`.

**Rationale**: Per `CLAUDE.md` §3 Source 反链规则 + `governance/spec.md` req-gov-2 "Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application" (recorded 2026-09-22), the `(historical, ...)` pattern is the canonical cross-link annotation for DecompMoE. Reusing it for the archive delta keeps the audit trail format consistent with ticket-side annotations and matches the spec lint format.

**Alternatives considered**:
- (a) Use a free-form prose annotation. Rejected: the `(historical, ...)` pattern is enforced by `scripts/lint_no_source_field_drift.py` for ticket-side annotations and recognized by `governance/spec.md` req-gov-2 as the canonical format. Free-form would not benefit from grep-based audit-trail queries.
- (b) Delete the archive delta file entirely. Rejected: archive files are immutable audit-trail records per OpenSpec convention; deleting would lose the historical record of the original 2026-09-06 proposal. The annotation is the correct way to mark historical context.

### Decision 3: Anchor cleanup uses single-line deletion, not substitution

**Choice**: Delete the single line `<a id="req-33"></a>` at `openspec/specs/wayfinder/spec.md` L740. Do NOT substitute with any other content (e.g., a comment, a stub Requirement, or a redirect).

**Rationale**: A comment or stub Requirement would re-introduce anchor-content mismatch. A redirect (e.g., `<!-- migrated to governance/req-gov-1 -->`) would add lint noise and is not part of OpenSpec spec syntax.

**Alternatives considered**:
- (a) Replace with `<a id="req-33"></a> <!-- migrated to governance/req-gov-1 -->`. Rejected: introduces an HTML comment in a Markdown file (lint-cleanliness concern); comment-only anchors still get flagged by anchor-content lint if any such lint exists in the future.
- (b) Replace with `<!-- req-33 migrated to governance/req-gov-1 -->`. Rejected: removes the anchor entirely; the comment is descriptive prose, not an anchor target.

### Decision 4: Annotation is added at TOP of archive delta file, not bottom

**Choice**: Prepend the `(historical, ...)` annotation block at the top of `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md`, before the existing `## ADDED Requirements` header.

**Rationale**: Top-of-file annotation is read first on encountering the file; bottom-of-file annotation requires scrolling past content. Mirrors ticket-side `(historical, ...)` pattern where supersede annotations are placed near the affected line, not at the end of the file.

**Alternatives considered**:
- (a) Bottom-of-file annotation. Rejected: harder to discover; less aligned with ticket pattern.
- (b) Inline annotation next to the original `### Requirement: Test Guard Precision for Closed-Form Numerical Claims` line. Rejected: clutters the original delta content; top-of-file is more discoverable.

## Risks / Trade-offs

- **[Risk]** Removing the anchor might break external references that pointed at `wayfinder/spec.md#req-33`. → Mitigation: grep for `req-33` in the live `wayfinder/spec.md` returned 0 non-self references (the only matches were the anchor itself at L740 and an unrelated reference at L823 inside req-36 text which references req-20 not req-33 — verified via `grep -nE 'req-33' openspec/specs/wayfinder/spec.md`). The anchor has no live inbound references to break. The `openspec/specs/wayfinder/spec.md` L823 grep match references `req-20` (Eight Geometric Quantification Metrics), not `req-33` — unrelated to this anchor.

- **[Risk]** Annotation block added to archive delta might be misread as part of the original delta content. → Mitigation: the annotation block uses explicit `(historical, ...)` pattern with a clear "this is metadata, not part of the original delta content" framing. Future readers grepping `(historical` will find the annotation; those grepping the original delta body will find it as before.

- **[Risk]** `python scripts/lint_no_source_field_drift.py` might flag the change as adding a Source-field reverse-link violation. → Mitigation: the orphan anchor removal is purely structural (no Source field affected); the archive annotation does not add any new `**Source:**` field to any live spec (only to an archive delta file which the lint script does not scan). Lint pass verified by inspection.

- **[Risk]** Future OpenSpec version might re-emit req-33 anchor in `wayfinder/spec.md` if archived changes are re-applied. → Mitigation: low risk — the archive change was never applied as a delta to live spec, so there is no re-apply scenario. The 2026-09-08 change (`6f22278`) was the actual change that added req-33 to live wayfinder/spec.md, and it has been migrated away.

## Migration Plan

No deployment or rollback concerns:
- The change is 2 single-file edits (1 deletion, 1 annotation prepend).
- No production code touched.
- No test files touched.
- No spec behavior changed.
- Rollback is the inverse: re-add the anchor line (1-line insert), remove the annotation block (1-block delete).

## Open Questions

None. The scope is bounded by the 2-edit fix; no spec behavior change; no decisions to defer.