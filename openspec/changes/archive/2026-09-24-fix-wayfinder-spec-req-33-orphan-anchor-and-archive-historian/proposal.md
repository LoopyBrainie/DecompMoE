# Proposal

## Why

Investigation of commit `e437c2d` (which archived the untracked `2026-09-06-tighten-test-precision-tolerance` directory) surfaced two spec-hygiene defects from the historical `req-33` lifecycle:

1. **Orphan anchor** at `openspec/specs/wayfinder/spec.md` L740 — `<a id="req-33"></a>` was left behind by commit `34b37be` (`migrate-l678-source`) when it moved the "Test Guard Precision for Closed-Form Numerical Claims" Requirement body to `governance/spec.md` as `req-gov-1`. The body was deleted but the anchor was not, producing an orphan anchor that grep-by-title cannot detect but breaks the `<a id="req-N"></a>` ↔ `### Requirement: <title>` invariant.
2. **Archive delta misleading-history** at `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` — this delta represents the **original 2026-09-06 proposal** that proposed `pytest.approx(..., abs=0)` for integer closed-form claims. That proposal was **superseded** by commits `bec147d + 83a0503` (policy reversal to bare `==`) and was **never applied** as a delta to live `wayfinder/spec.md` — the actual final landing of the closed-form-precision policy happened via `tighten-closed-form-eq-integer-checks` (commit `6f22278`) which added req-33 to `wayfinder/spec.md`, then via `migrate-l678-source` (commit `34b37be`) which migrated it to `governance/spec.md` as `req-gov-1`. The archive delta file's lack of `**Source:**` and `(historical, ...; superseded by ...)` annotation makes it easy to mis-read as "what the change actually added to live spec".

This change closes both defects with a surgical 2-edit fix; no Requirement semantics are changed.

## What Changes

- **Delete orphan anchor**: remove `<a id="req-33"></a>` (single line) from `openspec/specs/wayfinder/spec.md` L740. The corresponding Requirement body has lived in `governance/spec.md` as `req-gov-1` since commit `34b37be` (2026-09-12); the anchor is unowned.
- **Annotate archive delta file**: prepend a `(historical, ...; superseded by ...)` annotation block to `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md`, mirroring the existing ticket-side `(historical, ...)` supersede pattern (`wayfinder/tickets/A8-2.md` L70 + L74). The annotation records: (i) this delta was the original 2026-09-06 proposal, (ii) policy was reversed by `bec147d + 83a0503`, (iii) the actual final landing is `governance/req-gov-1` via `migrate-l678-source` (commit `34b37be`).

No source-code changes. No test changes. No ticket changes. No change to live `governance/spec.md` (already authoritative).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — see `skip_specs: true` rationale in `.openspec.yaml`)

### `skip_specs` rationale

This change is **pure spec-hygiene** with **no observable behavior change**:

- The orphan `<a id="req-33"></a>` anchor removal in `wayfinder/spec.md` L740 is **structural** — the anchor has no associated Requirement body since commit `34b37be` (2026-09-12) migrated the body to `governance/spec.md` as `req-gov-1`. Removing it changes no Requirement semantics; it only enforces the `<a id="req-N"></a>` ↔ `### Requirement: <title>` invariant from `CLAUDE.md` §6 第 8 条.
- The archive annotation added to `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` is **historical metadata** on a non-live archive delta. Archive files are immutable audit-trail records; annotating them does not modify any live spec.

Per the OpenSpec spec-driven workflow rule "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation.", this change sets `skip_specs: true`. The `apply` phase directly edits the two text files without producing a `specs/<capability>/spec.md` delta.

## Impact

- **Affected files**:
  - `openspec/specs/wayfinder/spec.md` (1 line deletion at L740)
  - `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` (annotation prepended, ~10-15 lines added)
- **Affected code/APIs/dependencies**: none.
- **Lint**: `python scripts/lint_no_source_field_drift.py` exit=0 (no governance reverse-link violation; the orphan anchor removal is purely structural).
- **OpenSpec validate**: `openspec validate --specs` and `openspec validate --change <name>` both pass.
- **Audit trail**: future cycles can grep `wayfinder/spec.md` for `req-33` and correctly conclude it is absent because it was migrated to `governance/req-gov-1` (rather than wondering if migration was incomplete).