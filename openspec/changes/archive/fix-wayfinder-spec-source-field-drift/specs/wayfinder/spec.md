## ADDED Requirements

### Requirement: Source Field Format Invariant for OpenSpec Specs

Every `**Source:**` field in `openspec/specs/**/spec.md` MUST contain at least one literal `wayfinder/tickets/<ID>.md` reference as the **primary reverse-link**. A `change <name> design.md (Decision N)` reference MAY appear additionally as a **secondary** link, but its presence does NOT substitute for the primary ticket reference.

When the ticket's value at the time of writing differs from the current spec value (e.g. a threshold changed by a later change), the primary ticket reference MUST use the `(historical, <original-value>; superseded by <change> Decision N)` annotation format — preserving the ticket's original value, marking it as historical, and naming the superseding change explicitly. Naked ticket references that omit the annotation but imply current-value parity with the spec are NOT permitted for tickets whose recorded value has been superseded.

This invariant MUST be enforced at archive time by `scripts/lint_no_source_field_drift.py`, which greps `openspec/specs/**/spec.md` for `**Source:**` lines and rejects any line missing the `wayfinder/tickets/` substring. The rule is content-based (not line-number based) so it survives spec edits without producing chronic exemption-table rot. The rule is zero-exemption: NO lines are permitted to bypass it, including governance-level requirements whose design origin is a `CLAUDE.md` amendment rather than a ticket.

#### Scenario: every Source field contains a wayfinder ticket reference

- **WHEN** `scripts/lint_no_source_field_drift.py` is run against `openspec/specs/**/spec.md`
- **THEN** the script enumerates every line beginning with `**Source:**` and verifies the line contains the substring `wayfinder/tickets/`
- **AND** the script exits with code `0` if and only if every such line satisfies the substring check
- **AND** the script outputs a per-line violation report (file path, line number, the violating line content) when any violation exists, with no aggregate-only summary that hides which line failed

#### Scenario: superseded values use the historical annotation format

- **WHEN** a spec Requirement's value differs from the corresponding `wayfinder/tickets/<ID>.md` original value
- **THEN** the Source field MUST be written as `**Source:** \`wayfinder/tickets/<ID>.md\` (historical, <original-value>; superseded by <change-name> Decision <N>), change \`<change-name>\` design.md (Decision <N>)`
- **AND** the `(historical, ...)` annotation MUST include the original value (e.g. a threshold, a constant, a formula term) so a reader can reconstruct the design history without leaving the spec

#### Scenario: governance-origin requirements trigger lint failure

- **WHEN** a spec Requirement's design origin is a `CLAUDE.md` amendment (or a commit amending `CLAUDE.md`) rather than any `wayfinder/tickets/*.md` ticket
- **THEN** the Source field is **required** to still contain a `wayfinder/tickets/<ID>.md` reference with an honest `(historical, ...)` annotation; the lint rule does NOT recognize a "governance-origin" carve-out
- **AND** any such requirement whose honest annotation cannot be written (because no A* ticket is its legitimate design predecessor) MUST be migrated to a separate governance capability (e.g. `openspec/specs/governance/spec.md`) before archive, so the wayfinder main spec never carries Source fields the lint rule cannot validate
- **AND** until such migration occurs, the lint failure on that specific line is the **intended design signal** that the change owning that line is incomplete — it MUST NOT be silently suppressed by an exemption table
