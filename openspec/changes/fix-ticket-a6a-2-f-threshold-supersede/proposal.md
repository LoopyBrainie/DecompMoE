# Proposal

## Why

`wayfinder/tickets/A6a-2.md` L63 currently hardcodes `f_i^avg < 1/128`, an N_e=64 design-era snapshot. `openspec/specs/wayfinder/spec.md` req-13 (Numerical Safeguards, body at L268; `<a id="req-13">` anchor at L264) has long since superseded this to the parameterized form `f_threshold = 1/(2·N_e)`, and its Source field (current L270) carries the explicit `(historical, threshold 1/128)` supersede annotation. The ticket is the **sole remaining stale end** of the spec↔ticket↔src triangle (src/`_dead_expert_threshold(N_e)` and the L29 legacy note are already correct). Appending the matching supersede annotation to ticket L63 closes the historical decision chain on the ticket side, so any future "read-ticket-not-spec" implementation cannot reproduce the stale `1/128` literal — which at MVP N_e=16 would defeat dead-expert resurrection entirely (uniform `f_avg = 0.0625` vs. ticket threshold `0.0078125` = `1/(2·64)` = 0.125 of uniform; would require an 8× drop to ever fire).

## What Changes

- `wayfinder/tickets/A6a-2.md` L63: append a single italic `(historical, ...)` supersede annotation in-line at the **触发** bullet (preserves the trigger description verbatim, mirrors the canonical form in `openspec/specs/wayfinder/spec.md` req-34 Scenario "superseded values use the historical annotation format" L742-746 + Requirement body L723). No other lines.

No other files. No spec Requirements change (`skip_specs: true`). No code change. No tests/CLAUDE.md change.

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 — `skip_specs: true` is set. The change is ticket-only historical-decision-chain annotation; spec req-13 L268 + L270 already reflects the supersede chain correctly.）

## Impact

- **Affected code** (none): 0 files src/ / tests/ / spec/ / CLAUDE.md changed.
- **Affected tickets** (surgical 1 处): `wayfinder/tickets/A6a-2.md` L63 inline italic annotation.
- **Affected APIs / dependencies / systems**: none.
- **Risk**: low (annotation, not code; preserves decision chain; matches req-34 canonical form).

**Source**:

- `openspec/specs/wayfinder/spec.md` req-13 Numerical Safeguards (L264 anchor + L268 body + L270 Source field) — truth source per CLAUDE.md §2.
- `openspec/specs/wayfinder/spec.md` req-34 L723 + L742-746 — canonical `(historical, <原值>; superseded by <change> Decision N)` annotation form.
- `.audit/audit-verification/audit-verification.md` L853 — verify-12 cycle-9 MEDIUM finding #1 axis-γ fix recommendation verbatim.
- `.audit/audit-verification/README.md` §"6-cycle ticket-stale pattern family" — cycle-9 finding 1 sits in the cycle-5/6/7/9/12/13 same-source family.
- `openspec/specs/governance/spec.md` req-gov-2 L51-67 (Documenting-only meta Requirement: ticket `(historical, ...)` supersede annotation pattern as CLAUDE.md §3 source-field rules application) — the only currently-active governance Requirement that documents this pattern. The planned clause-(4)(a) drift-remediation protocol in `.audit/.../09-fix-claude-md-ticket-advisory-boundary/` is **NOT** invoked as authority here; this annotation fits the active req-gov-2 form already.

Co-Authored-By: Claude Code <noreply@anthropic.com>
