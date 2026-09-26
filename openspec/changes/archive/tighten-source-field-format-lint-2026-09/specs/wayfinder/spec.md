## MODIFIED Requirements

### Requirement: Source Field Format Invariant for OpenSpec Specs

Every `**Source:**` field in `openspec/specs/**/spec.md` MUST carry a **primary reverse-link** to its design lineage as the **first top-level item** of the field, with each reverse-link token **wrapped in backticks** (inline code span). The required primary reverse-link is per-capability:

- `openspec/specs/governance/spec.md` — primary reverse-link MUST be a backtick-wrapped `CLAUDE.md` reference (governance-origin lineage).
- All other `openspec/specs/**/spec.md` (wayfinder-ticketed, decompmoe-skeleton, future peers that cite wayfinder tickets) — primary reverse-link MUST be a backtick-wrapped `wayfinder/tickets/<ID>.md` reference.

A `change <name> design.md (Decision N)` reference MAY appear additionally as a **secondary** link after the primary reverse-link, but its presence does NOT substitute for the primary ticket / governance reverse-link. The primary reverse-link MUST NOT be preceded by any `change \`foo\` design.md (Decision N)` clause or other secondary reference.

When the ticket's value at the time of writing differs from the current spec value (e.g. a threshold changed by a later change), the primary ticket reference MUST use the `(historical, <original-value>; superseded by <change> Decision N)` annotation format — preserving the ticket's original value, marking it as historical, and naming the superseding change explicitly. Naked ticket references that omit the annotation but imply current-value parity with the spec are NOT permitted for tickets whose recorded value has been superseded.

This invariant MUST be enforced at archive time by `scripts/lint_no_source_field_drift.py`. The lint script performs three structural checks on every `**Source:**` line:

1. **Capability-aware substring presence** — the line MUST contain the per-capability required primary reverse-link substring (`CLAUDE.md` for governance, `wayfinder/tickets/` for all others).
2. **Backtick wrapping** — every occurrence of the per-capability required primary reverse-link substring MUST appear inside a backtick-delimited code span; a reverse-link that appears outside a code span is a violation regardless of substring presence.
3. **Primary-first ordering** — the first top-level item (the substring from the `**Source:**` marker up to the first `,` or `;` at paren-depth 0, with code-span atomicity so a delimiter inside a backtick pair does NOT split) MUST be a backtick-wrapped code span whose contents include the per-capability required primary reverse-link substring.

The three checks are independent — a line may fail ① while passing ②③ (substring present, backticked, first item is the backticked primary), or fail ②③ while passing ① (substring present in plain text), or fail all three. The lint script reports each violation with a distinct reason code so a developer can fix the right thing.

The rules are content-based (not line-number based) so they survive spec edits without producing chronic exemption-table rot. The rules are zero-exemption: NO lines are permitted to bypass them, including governance-level requirements whose design origin is a `CLAUDE.md` amendment rather than a ticket (governance is honored by the per-capability substring dispatch, NOT by a carve-out).

#### Scenario: every Source field contains a wayfinder ticket reference

- **WHEN** `scripts/lint_no_source_field_drift.py` is run against `openspec/specs/**/spec.md`
- **THEN** the script enumerates every line beginning with `**Source:**` and verifies the line contains the substring `wayfinder/tickets/` (or `CLAUDE.md` for the governance capability)
- **AND** the script exits with code `0` if and only if every such line satisfies the substring check
- **AND** the script outputs a per-line violation report (file path, line number, the violating line content) when any violation exists, with no aggregate-only summary that hides which line failed

#### Scenario: superseded values use the historical annotation format

- **WHEN** a spec Requirement's value differs from the corresponding `wayfinder/tickets/<ID>.md` original value
- **THEN** the Source field MUST be written as `**Source:** \`wayfinder/tickets/<ID>.md\` (historical, <original-value>; superseded by <change-name> Decision <N>), change \`<change-name>\` design.md (Decision <N>)`
- **AND** the `(historical, ...)` annotation MUST include the original value (e.g. a threshold, a constant, a formula term) so a reader can reconstruct the design history without leaving the spec

#### Scenario: governance-origin requirements trigger lint failure

- **WHEN** a spec Requirement's design origin is a `CLAUDE.md` amendment (or a commit amending `CLAUDE.md`) rather than any `wayfinder/tickets/*.md` ticket
- **THEN** the Source field is **required** to still contain a per-capability required reverse-link (`CLAUDE.md` for the governance capability; for wayfinder-ticketed capabilities, a `wayfinder/tickets/<ID>.md` reference with an honest `(historical, ...)` annotation)
- **AND** any such requirement whose honest annotation cannot be written (because no A* ticket is its legitimate design predecessor) MUST be migrated to a separate governance capability (e.g. `openspec/specs/governance/spec.md`) before archive, so the wayfinder main spec never carries Source fields the lint rule cannot validate
- **AND** until such migration occurs, the lint failure on that specific line is the **intended design signal** that the change owning that line is incomplete — it MUST NOT be silently suppressed by an exemption table

#### Scenario: reverse-link must be wrapped in backticks

- **WHEN** a `**Source:**` line in `openspec/specs/**/spec.md` contains the per-capability required primary reverse-link substring (`wayfinder/tickets/` for wayfinder-ticketed / decompmoe-skeleton specs, `CLAUDE.md` for governance specs) OUTSIDE a backtick-delimited code span
- **THEN** `scripts/lint_no_source_field_drift.py` MUST report a violation with reason `"unbackticked reverse-link: <substring>"` for that line
- **AND** the lint script's check is structural: it MUST strip code spans from the line body and verify that the remaining (unbackticked) text does NOT contain the required substring
- **AND** a backtick-wrapped reverse-link on the same line that satisfies ① still passes (multiple backticked reverse-links on a single line are permitted, e.g. `**Source:** \`wayfinder/tickets/A2-1.md\`, \`wayfinder/tickets/A2-2.md\``)
- **AND** the scenario is verified by `tests/test_lint_no_source_field_drift.py::test_unbackticked_refs_flags_bare_substring` and `::test_unbackticked_refs_ignores_backticked_substring`

#### Scenario: primary reverse-link must be the first top-level item

- **WHEN** a `**Source:**` line in `openspec/specs/**/spec.md` is split by `,` or `;` at paren-depth 0 (with code-span atomicity: a backtick toggles an atomic flag so a delimiter inside a code span does NOT split)
- **THEN** the first top-level item MUST be a backtick-wrapped code span whose contents include the per-capability required primary reverse-link substring
- **AND** `scripts/lint_no_source_field_drift.py` MUST report a violation with reason `"first item is not the primary reverse-link (first code span = <...>, required substring = <required>)"` for any line whose first top-level item is not the primary reverse-link
- **AND** the lint script's split is paren-depth aware: a comma inside `(...)` does NOT split (e.g. `**Source:** \`wayfinder/tickets/A6a-2.md\` (initial A6a-2 design intent), change \`fix-openspec-doc-bugs\` design.md (Decision 1, 2)` has only TWO top-level items, not four)
- **AND** the lint script's split is code-span atomic: a comma inside `` `...` `` does NOT split (e.g. `**Source:** \`wayfinder/tickets/A2-1.md\`, change \`foo, bar, baz\` design.md (Decision 1)` has only TWO top-level items, not four)
- **AND** the scenario is verified by `tests/test_lint_no_source_field_drift.py::test_split_top_level_items_paren_depth` and `::test_first_item_must_be_primary_reverse_link`

#### Scenario: secondary references in parenthetical annotations use bare ticket IDs

- **WHEN** a `**Source:**` line's primary reverse-link is backtick-wrapped as the first top-level item, and a parenthetical annotation immediately following the primary contains a ticket reference (e.g. a `supersedes` or `compare with` clause)
- **THEN** the annotation's ticket reference MUST be written as a bare ticket ID (e.g. `A6a-2.md`), NOT as a backtick-prefixed full path (e.g. `` `wayfinder/tickets/A6a-2.md` ``)
- **AND** the reason is: a bare full-path reference inside a paren annotation would (under the strict reading of check ② "every occurrence of the per-capability required primary reverse-link substring MUST appear inside a backtick-delimited code span") trigger an `unbackticked reverse-link` violation on the secondary occurrence — because `wayfinder/tickets/` is a substring prefix that appears in any full-path ticket reference
- **AND** the canonical live example is `openspec/specs/wayfinder/spec.md` L251: ``**Source:** `wayfinder/tickets/A6a-2.md` (historical, threshold `1/128`), change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold superseded by `1/(2·N_e)`)`` — the paren annotation uses bare `1/128` (the value), bare `1/(2·N_e)` (the superseding formula), and bare ticket IDs in change-decision clauses; it MUST NOT use `` `wayfinder/tickets/...` `` in any non-first-item paren annotation
- **AND** the scenario is verified by `tests/test_lint_no_source_field_drift.py::test_first_item_is_primary_with_historical_annotation`

#### Scenario: tokenizer handles single-backtick code spans only

- **WHEN** a `**Source:**` line uses Markdown constructs that the lint script's hand-rolled tokenizer does NOT support — namely double-backtick code spans (`` ``...`` ``), backslash-escaped backticks (`\\\``), or multi-line Source fields whose `,` / `;` delimiters appear on subsequent lines
- **THEN** the lint script MUST report a violation for the line (rather than silently passing or raising an unhandled exception)
- **AND** the canonical double-backtick behavior: a `` `` `` toggles `in_code_span` to False immediately, so all subsequent text is treated as outside code span. A Source line written with double-backtick spans will be parsed by the lint as if it used single-backtick spans — which will likely produce a false-positive `unbackticked reverse-link` violation on the second half of the double-backtick span content
- **AND** the canonical backslash-escape behavior: `\`` is treated as a regular character (the escape is not recognized), so the next backtick will toggle `in_code_span` normally — producing unpredictable parse state
- **AND** the canonical multi-line behavior: the lint script reads `**Source:**` lines one line at a time; a Source field whose content continues onto subsequent lines is NOT concatenated — the subsequent lines are scanned as separate `**Source:**` lines (none of which will match the regex), and the original line's body is processed as a self-contained single-line Source field, almost certainly failing check ① because the body is incomplete
- **AND** the convention enforced by this Scenario is: Source fields MUST use single-backtick code spans exclusively, MUST NOT use backslash-escapes inside backticks, and MUST be written on a single line. Any violation of these conventions MUST be fixed by rewriting the line, not by expecting the lint script to handle the edge case
