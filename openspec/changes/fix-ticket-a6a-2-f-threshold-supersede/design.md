# Design

## Context

See `proposal.md` for motivation. The current state:

- `wayfinder/tickets/A6a-2.md` L63 hardcodes `f_i^avg < 1/128` (an N_e=64 design-era snapshot).
- `openspec/specs/wayfinder/spec.md` req-13 (anchor at L264; body at L268; Source field at L270) has been superseded to `f_threshold = 1/(2·N_e)` and carries the matching `(historical, threshold 1/128)` supersede annotation on its Source field.
- `src/decompmoe/safeguards.py` already implements `_dead_expert_threshold(N_e) = 1.0 / (2.0 * N_e)` (L34-36) with a legacy note "Previously hardcoded to 1/128 (N_e=64 legacy)" at L29.
- Spec ↔ src ↔ tests triangle is locked; **ticket A6a-2 L63 is the lone stale end** per verify-12 (`.audit/audit-verification/audit-verification.md` L820-853, SEVERITY-OK + worst-case mitigated + L853 fix recommendation).

The single design constraint is therefore: surgically append an italic `(historical, ...)` supersede annotation in-line at ticket L63 to mirror the spec's annotation form, preserving the trigger description verbatim.

## Goals / Non-Goals

**Goals:**

- Mirror the spec L270 Source-field annotation form onto ticket L63 (ticket ↔ spec supersede chain symmetry).
- Preserve ticket L63 trigger description verbatim (`**触发**：\`f_i^avg < 1/128\` 持续 200 steps`); append, never replace.
- Annotation form aligns with `openspec/specs/wayfinder/spec.md` req-34 L723 (Requirement body canonical form) + L742-746 (Scenario "superseded values use the historical annotation format").
- Annotation evidence chain cites `audit-verification.md` L853 verbatim text (cycle-9 MEDIUM finding #1 fix recommendation).

**Non-Goals:**

- Do not modify `openspec/specs/{wayfinder,decompmoe-skeleton,governance}/spec.md` — `skip_specs: true`.
- Do not modify `src/decompmoe/safeguards.py` — already parameterized.
- Do not modify `tests/` — no test LOCKS stale `1/128` (per verify-12 worst-case claim).
- Do not modify `CLAUDE.md` or `MVPConfig`.
- Do not introduce a new test (governance req-gov-2 clause-(4) future test anchor — out of scope for this change).
- Do not touch the other 5 entries in the 6-cycle ticket-stale pattern family (cycle-5/6/7 → change 01; cycle-12 → change 03; cycle-13 → change 04).
- Do not invoke `.audit/.../09-fix-claude-md-ticket-advisory-boundary/` clause-(4)(a) drift-remediation protocol — that requirement is currently a planning draft, NOT yet proposed/applied/archived (per `openspec/specs/governance/spec.md` L57 explicit statement). This annotation stands on its own under the **already-active** req-gov-2 (Documenting-only meta Requirement, governance L51-67) + req-34 canonical form.

## Decisions

### Decision 1: ticket-only annotation, no spec / src / tests edits

**Choice**: Append one italic `(historical, ...)` annotation in-line at ticket A6a-2 L63; no other file changes.

**Rationale**: verify-12 three-axis evidence (`.audit/.../audit-verification.md` L820-853) confirms the spec ↔ src triangle is locked, with ticket A6a-2 L63 as the **only stale end**. Editing the spec or src is unnecessary and would violate CLAUDE.md §3 surgical. Editing tests would invent a guardian for an annotation (not executable code).

**Alternatives considered**:

- (a) Edit spec req-13 — rejected: already correct (L268 body + L270 Source).
- (b) Edit src/`safeguards.py` — rejected: already parameterized + L29 legacy note correct.
- (c) Delete ticket L63 trigger description — rejected: violates governance req-gov-2 (current L51-67) "annotation preserving the decision chain" semantics; deletion destroys decision history.
- (d) Append annotation in-line only — chosen.

### Decision 2: annotation form verbatim from audit-verification L853 + req-34 L723 canonical form

**Choice**: Annotation text:

```
*(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L268 `f_threshold = 1/(2·N_e)` via `fix-openspec-doc-bugs` design.md Decision 7)*
```

**Rationale**: The annotation is assembled from three independently-cited fragments:

1. `audit-verification.md` L853 (verify-12 cycle-9 axis-γ follow-up): literal `(historical, threshold 1/128 at N_e=64; superseded by spec req-13 L245 via fix-openspec-doc-bugs Decision 7)` — but with **spec line number updated from stale L245 to current L268** (line drift +23 from subsequent spec edits captured in commits adf41ef / 229016f / d239f57 / f077be8 / 784d011 / f6475ad).
2. `openspec/specs/wayfinder/spec.md` req-34 L723 (Requirement body canonical form): `<original-value>; superseded by <change> Decision N`.
3. `openspec/specs/wayfinder/spec.md` req-13 L268 verbatim phrase: `f_threshold = 1/(2·N_e)` (the superseding formula, backtick-wrapped).

The `<原值>` slot is `threshold 1/128 at N_e=64` (verbatim from audit-verification L853 recommendation), the `<superseding formula>` slot is `f_threshold = 1/(2·N_e)` (verbatim from spec L268), the `<spec req>` slot is `req-13 L268` (matches req-34 canonical first-line primary anchor + current line), the `<change>` slot is `fix-openspec-doc-bugs`, the `<decision>` slot is `Decision 7`.

**Alternatives considered**:

- (a) Bare `(historical, 1/128)` only — rejected: incomplete supersede chain; req-gov-2 (current L51-67) Scenario L62-67 requires 3-反链齐 (ticket + spec anchor + change Decision).
- (b) Markdown link reference — rejected: ticket markdown doesn't support cross-file links; req-34 + req-gov-2 use paren annotation form by convention.
- (c) Block quote `> Superseded by ...` — rejected: spec convention (req-34 Scenarios) is italic inline annotation.
- (d) Verbatim拼接 from three canonical sources — chosen.

### Decision 3: italic `*...*` wrapping vs bold / plain / code

**Choice**: Italic `*...*` outer wrap, with two inner backtick-wrapped code spans (`` `f_threshold = 1/(2·N_e)` `` and `` `fix-openspec-doc-bugs` ``).

**Rationale**: Ticket A6a-2 L63 is a bullet whose label is bold `**触发**`. The annotation is a trailing inline note; markdown convention distinguishes:

- bold `**...**` — bullet label / structural marker;
- italic `*...*` — inline annotation / supplementary note;
- code `` `...` `` — formula / identifier.

Italic is visually distinct from the bold `**触发**` label, and is the conventional form used by req-34 Scenario "superseded values use the historical annotation format" L742-746 (which itself cites the in-spec live example as paren annotation, not bold or code-block).

**Alternatives considered**:

- (a) Plain text — rejected: no visual distinction from the bold label, would render as if it were bullet-label continuation.
- (b) Bold `**...**` — rejected: same weight as the bold label, ambiguity risk.
- (c) Code fence — rejected: code fence is for code blocks; this is an inline note.
- (d) Italic `*...*` — chosen.

### Decision 4: skip_specs: true; no spec Requirement / Scenario added

**Choice**: `skip_specs: true` in `.openspec.yaml`. No `specs/<capability>/spec.md` delta files created.

**Rationale**:

- Spec req-13 (Numerical Safeguards, L268 + L270 Source) already reflects the supersede chain — req-13 L268 body says `f_threshold = 1/(2·N_e) parameterized by N_e, not a hardcoded 1/128 from a prior N_e = 64 design`; L270 Source already carries the `(historical, threshold 1/128), change fix-openspec-doc-bugs design.md (Decision 7 — threshold superseded by 1/(2·N_e))` annotation.
- src/decompmoe/safeguards.py L34-36 + L29 are already correct.
- No new Requirement introduces or removes behavior; this change is documentation-only (annotation on a ticket). `openspec validate` accepts `skip_specs: true` for pure documentation / tooling / refactor changes; this fits.

**Alternatives considered**:

- (a) Add Scenario "supersede annotation mirrored on ticket side" to wayfinder spec — rejected: would expand scope; the spec is already correct, what changes is the ticket side.
- (b) Add Requirement in governance spec to formalize drift-remediation obligation — rejected: this is precisely what change 09 (`09-fix-claude-md-ticket-advisory-boundary/`) is a planning draft for; duplicating now would scope-creep into a separate change.
- (c) `skip_specs: true` — chosen.

### Decision 5: no new test

**Choice**: No new test added in this change.

**Rationale**:

- The ticket annotation is not executable code; it cannot be unit-tested for the same reason a docstring cannot.
- The mathematical claim `1/(2·N_e)` is already formally tested via `src/decompmoe/safeguards.py::_dead_expert_threshold(N_e)` and any test that materializes the function with `N_e=16, N_e=64` (these tests are not added here but exist in the broader test suite per the project conventions).
- Annotation-format adherence (req-gov-2 active scenario L62-67) is verifiable via `grep` checks enumerated in `tasks.md`.

**Alternatives considered**:

- (a) Add `test_a6a2_supersede_annotation_50digit` — rejected: ticket is non-executable, no test can directly probe an annotation.
- (b) Add `test_dead_expert_threshold_spec_canonical_form` — rejected: out of scope; this change is ticket-only.
- (c) No new test — chosen; cross-validation lives in `tasks.md` §C + `audit-verification.md` verify-10 / 11 / 12.

## Risks / Trade-offs

- **[Risk 1]** annotation text drifts from spec L270 Source field. **Mitigation**: both texts use identical `(historical, ...; superseded by ... Decision ...)` template from req-34 L723 + L742-746; `tasks.md` §C grep-verifies spec L270 ↔ ticket L63 annotation form identical except for italic wrap and inline location.
- **[Risk 2]** annotation mislabels ticket as "stale" instead of "historical". **Mitigation**: req-34 L723 + governance req-gov-2 (current L51-67) require the canonical form `<原值> ... ; superseded by ...` which preserves the original value verbatim; "stale" reads as a delete, "historical" reads as a record; the form's wording enforces the latter.
- **[Risk 3]** markdown italic / backtick / full-width character nesting renders ambiguously. **Mitigation**: outer `*...*` italic, inner `` `...` `` code spans; the two wrap levels are independent in markdown's parse model (italic is an inline element, code span is an inline element, and the latter takes precedence inside the former without ambiguity). `tasks.md` §A.3 includes a manual markdown-render check.
- **[Risk 4]** future audit-verification cycle cross-checks annotation text. **Mitigation**: annotation text contains the verbatim audit-verification L853 evidence IDs (and the now-current spec line L268) so future cycles can `grep -n` for cross-validation; the verbatim spec L268 phrase `f_threshold = 1/(2·N_e)` is grep-stable.
- **[Risk 5]** Windows Edit tool CRLF contamination of the ticket file (per historical CRLF pitfalls in `.audit/.../opsx-changes` round-1 lessons). **Mitigation**: `tasks.md` §A.4 LF validation via `git diff --stat wayfinder/tickets/A6a-2.md` + `file wayfinder/tickets/A6a-2.md` showing `ASCII text`; `sed -i 's/\r$//' wayfinder/tickets/A6a-2.md` as fall-back (project uses CRLF per `.gitattributes` for *.md, so the file's final state should remain CRLF if that's the project convention — see `git show HEAD:wayfinder/tickets/A6a-2.md | file -` to confirm before applying).
- **[Risk 6]** other 6-cycle ticket-stale family findings (cycle-5/6/7/12/13) get conflated into this change. **Mitigation**: `proposal.md` §Impact + `tasks.md` §B specify this change touches **only** ticket A6a-2 L63; `tasks.md` §D.2 enumerates the other 5 family entries and their respective OpenSpec changes as the appropriate scope.

## Migration Plan

N/A — no deployment, no rollback, no migration. Surgical single-line annotation:

1. Edit `wayfinder/tickets/A6a-2.md` L63: append italic annotation at line end.
2. `git diff --stat` on the ticket file: should be +1 line / -0 lines (inline appendix).
3. LF / CRLF validation per `tasks.md` §A.4.
4. `grep` cross-validation per `tasks.md` §C.
5. `python scripts/lint_no_dead_defensive.py` exit 0 (no src edits).
6. `python scripts/lint_no_source_field_drift.py` exit 0 (no spec edits).
7. `uv run pytest tests/ -v` all green (no test edits).
8. Single `fix(ticket): A6a-2 L63 supersede annotation per cycle-9 audit-verification (1/128 → 1/(2·N_e))` commit on `dev`, with Co-Authored-By trailer.

## Open Questions

- **Future test addition** — governance req-gov-2 (active L51-67) Scenario L61-67 + req-gov-2's "future test anchor" implicitly references `tests/test_audit_verification_loop.py`. Should a follow-up change add `test_a6a2_supersede_annotation_50digit` to cover ticket-side annotation adherence? Open: separate change scope; this change does not cover.
- **6-cycle batch fix** — `audit-verification/README.md` L74-79 documents that cycle-5/6/7 (change 01), cycle-12 (change 03), cycle-13 (change 04) need their own ticket-side supersede annotations. Could they be batched into a single 5-file change? Open: needs user decision on batching strategy; this change does not cover.
- **LOOPS.md dormant-bug clause** — audit-verification verify-18 / meta-08 suggest LOOPS.md add a proactive dormant-bug-upgrade clause. Open: out of scope for this change.

Co-Authored-By: Claude Code <noreply@anthropic.com>
