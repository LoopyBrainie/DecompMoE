## Context

See `proposal.md` for motivation. Brief restatement of constraints that shape the design:

- The lint script is `python scripts/lint_no_source_field_drift.py` — content-based, no CLI flags, no env vars, no exemption registry, exit-code-only. All of these constraints must be preserved (the source-change `fix-wayfinder-spec-source-field-drift` design.md explicitly forbids exemption-table rot, CLI toggles, and per-line `# noqa`).
- The project has only `torch` + `torchvision` in `pyproject.toml` dependencies. Adding `mistune` or `markdown-it-py` for a one-script Markdown parser is rejected on dependency-surface cost.
- The lint script is a `/opsx:archive` gate precondition per CLAUDE.md §3 (wired by `migrate-l678-source`). Tightening it changes the gate's behavior: any change introducing an unbackticked reverse-link OR a `change \`foo\` ...`-first Source line will be rejected at archive time. The pre-archive patch in `proposal.md` Impact (4 lines: `wayfinder/spec.md` L577/L639 + `decompmoe-skeleton/spec.md` L208/L377) brings the live spec tree back to gate-passing state before the lint upgrade is enforced.
- The four live violations (2 wayfinder + 2 decompmoe-skeleton, all on the same `wayfinder/tickets/A6a-2.md` reverse-link) are fact-checked at 2026-09-14 via the synthetic-test methodology in the proposal — adding backticks to those four lines simultaneously closes both ② and ③ because each violation's "first code span" is also missing (no backtick span at all on the first item).
- `openspec/specs/governance/spec.md` Source line already passes all three checks; no governance patch is needed.

## Goals / Non-Goals

**Goals:**
- Add two pure-function helpers to `scripts/lint_no_source_field_drift.py`:
  - `_unbackticked_refs(body: str, required_substring: str) -> list[str]` — returns every occurrence of `required_substring` that lives OUTSIDE a backtick-delimited code span. Empty list = all occurrences are backtick-wrapped.
  - `_split_top_level_items(body: str) -> list[str]` — splits the line body by `,` or `;` at paren-depth 0 with code-span atomicity. The first item is the "primary reverse-link container".
- Extend `lint_file()` to call both helpers and emit per-violation reason codes: `"unbackticked reverse-link: <substring>"` (from `_unbackticked_refs`) and `"first item is not the primary reverse-link (first code span = <...>, required substring = <required>)"` (from `_split_top_level_items` + first-code-span extraction).
- Add `tests/test_lint_no_source_field_drift.py` with 14 tests: 5 helper tests + 7 orchestrator tests (per-scenario coverage matching the new req-34 Scenarios) + 2 regression tests against the live repo state (post-fix).
- Pre-archive patch: wrap the `wayfinder/tickets/A6a-2.md` reverse-link in backticks at `wayfinder/spec.md` L577, L639 and `decompmoe-skeleton/spec.md` L208, L377. The patch is recorded in `tasks.md` §2 as the inline-text edit step before the lint script upgrade; it is not a separate change.
- Preserve the existing exit-code-on-stdout convention, the per-line violation report format, and the `required_substring_for()` per-capability dispatch.

**Non-Goals:**
- No new dependencies (`pyproject.toml` unchanged).
- No full Markdown parser (no `mistune`, `markdown-it-py`, `commonmark`, or `markdown`). The hand-rolled tokenizer is a single-pass scan over a single `**Source:**` line, which is the only Markdown structure the lint cares about.
- No multiline Source-field parser. Source fields are single-line by convention (existing 36 Source lines in the live spec tree are all single-line); the lint script will NOT handle multi-line Source fields and will report them as violations if encountered (a `**Source:**` line whose `,` splits appear on subsequent lines will not be parseable; the script will report the line as a structural violation rather than attempting to concatenate).
- No new exemption mechanism. The script remains zero-exemption: every violation is reported, no `# noqa`, no env-var skip.
- No extension of the lint to non-Source-field Markdown structures (e.g. inline code spans in Scenario bodies). The script's contract is `**Source:**` lines only.
- No modification to the `migrate-l678-source` design.md constraints (no exemption table, no CLI flag, no env var) — these are inherited verbatim.

## Decisions

### Decision 1: hand-rolled single-line tokenizer, not a Markdown library

**Chosen**: The two helpers (`_unbackticked_refs`, `_split_top_level_items`) are implemented as a single-pass scan over a single `**Source:**` line body. The scan maintains two boolean counters: `in_code_span` (toggled by each backtick outside `in_code_span` itself) and `paren_depth` (incremented by `(`, decremented by `)`). A delimiter character (`,` or `;`) only acts as a top-level separator when `paren_depth == 0 AND NOT in_code_span`. A backtick toggles `in_code_span` only when `paren_depth` does not contain a code-span-internal state — i.e. the standard inline-code-span rules apply (no escaped backticks, no double-backtick code spans, no fence-delimited code blocks within a single line).

**Rationale**:
- The full Source-field grammar is bounded: it contains backtick-delimited file paths, parens around annotation clauses (`(historical, ...)`, `(Decision N)`), and `,` / `;` between top-level items. No nesting beyond `(...)`, no escape sequences in practice.
- The 36 live Source lines in the repo (`grep -c '^\*\*Source:\*\*' openspec/specs/**/spec.md`) use only this bounded grammar; expanding to a full Markdown parser buys nothing for the live data and adds a 100+ KB dependency for a 200-line lint script.
- The hand-rolled tokenizer is testable: each helper is a pure function of `(line_body) -> list[str]`, no I/O, no module-level state. The 14-test suite gives the spec-level Scenarios a direct mapping to test names.

**Alternatives considered**:
- *A (rejected)*: `markdown-it-py`. CommonMark-compliant, well-tested, handles edge cases (escape sequences, double-backtick code spans, HTML entities). Cost: a new dependency for a one-script parser; pyproject.toml grows by ~50 KB of transitive deps; the lint script becomes coupled to the parser's version-specific token shapes.
- *B (rejected)*: `mistune`. Faster than markdown-it-py, but the same dependency cost. Has a "pure-Python" mode and a "C-extension" mode; the C-extension mode would require a build step in CI.
- *C (rejected)*: AST-style full-document parse (via `mistune`'s AST renderer or `markdown-it-py`'s token stream). Overkill for a single-line check; parses the entire spec file to extract one line's tokens.
- *D (rejected)*: regex with negative lookahead (`r'(?<!`)<required-substring>(?!`)'`). Cannot correctly handle a code span that contains a `,` (e.g. `` `wayfinder/tickets/A2-1.md, wayfinder/tickets/A2-2.md` `` would not be in the live spec but is theoretically possible); also fails when the code span is split across the line boundary.

### Decision 2: violation reason codes are strings, not enum values

**Chosen**: The `lint_file()` function returns `list[tuple[int, str, str]]` where the third element is a human-readable reason string. The three reason codes are:
- `"source field missing required reverse-link <required> for capability"` (existing; preserved verbatim from `migrate-l678-source`)
- `"unbackticked reverse-link: <substring>"` (new; one entry per unbackticked occurrence of the required substring)
- `"first item is not the primary reverse-link (first code span = <first_span>, required substring = <required>)"` (new; one entry per Source line whose first top-level item fails the primary check)

**Rationale**:
- Strings preserve the existing tuple-of-tuples return shape; the `main()` function's stdout printer can print them verbatim with no schema migration.
- A reader of the lint output can grep for the leading reason fragment (`unbackticked reverse-link` / `first item is not the primary reverse-link`) to group violations by class; a CI script can parse the reason string if needed (the existing tests demonstrate this pattern).
- Enum-based reason codes would force `lint_file()` to return a dataclass instead of a tuple, breaking the existing test convention (`tests/test_lint_no_source_field_drift.py::test_*` — when added — would need a new fixture shape).

**Alternatives considered**:
- *A (rejected)*: `class LintReason(Enum)` with `MISSING_SUBSTRING`, `UNBACKTICKED_REF`, `FIRST_ITEM_NOT_PRIMARY`. Cleaner type safety; cost: requires modifying `lint_file()`'s return shape from `tuple[int, str, str]` to `tuple[int, str, LintReason]` or `tuple[int, str, Violation]` dataclass, which forces `main()` to learn `.reason.value` accessors and breaks the existing per-line printer.
- *B (rejected)*: `(class, message)` two-element reason where `class` is an integer code. Adds a code-book to the docstring with no consumer benefit (no CI script currently exists that would key off the integer code).

### Decision 3: paren-depth + code-span atomicity, NOT regex

**Chosen**: The `_split_top_level_items()` helper is a state machine, not a regex. State variables:
- `in_code_span: bool` — toggled by each backtick
- `paren_depth: int` — incremented by `(`, decremented by `)`
- `buf: list[str]` — current item being built
- `items: list[str]` — completed items

The split delimiter set is `{',', ';'}` (matching the Source-field convention; semicolons are used in the governance spec to separate CLAUDE.md lineage from change-decision 反链). When `ch` is a delimiter AND `paren_depth == 0` AND `NOT in_code_span`, flush `buf` to `items` and reset `buf`.

**Rationale**:
- The paren-depth state is required by Scenario 5 in the new req-34 (the live L577 / L639 / L208 / L377 violations all have `(initial A6a-2 design intent)` as a paren-balanced annotation after the reverse-link; a flat split would treat the inner space as an item boundary).
- The code-span atomicity state is required by Scenario 5's other clause: a `change \`foo, bar, baz\` design.md (Decision N)` clause has commas inside the code span that MUST NOT split. (No live spec line uses this form, but the helper must handle it for future-proofing per the req-34 Scenario spec.)
- The state machine is 20 lines of Python; a regex equivalent would require either balanced-paren matching (which Python `re` cannot do without recursion) or a lookahead-anchored non-greedy pattern that breaks on the live spec's annotation clauses.

**Alternatives considered**:
- *A (rejected)*: regex with negative-lookahead for code-span boundaries. Cannot correctly handle code spans whose contents contain a delimiter (the `\``,` delimiter inside `` `change \`foo, bar\` design.md` `` case).
- *B (rejected)*: recursive descent parser. Overkill — the grammar has no recursion beyond `(...)`, and a recursive descent parser would require a parser class with methods, increasing the lint script's surface area for no functional gain.

### Decision 4: pre-archive patch is 4 inline-text edits, not a separate change

**Chosen**: The 4 unbackticked Source lines (`wayfinder/spec.md` L577, L639 + `decompmoe-skeleton/spec.md` L208, L377) are patched in this same change, as a `tasks.md` step §2.1 that runs BEFORE the lint script upgrade step §2.2. The patch is one-token-per-line: wrap `wayfinder/tickets/A6a-2.md` in backticks. No semantic content changes; no `(historical, ...)` annotation needed because the ticket value is current-value-correct (the perturbation contract referenced is the same as the spec's current text).

**Rationale**:
- Splitting the patch into a separate change would create the same intermediate-state failure mode that `migrate-l678-source` design.md Decision 4 explicitly forbids: the lint gate would reject any change that archives between the patch and the lint-upgrade, because the live state would already have unbackticked lines failing the new structural check.
- The patch is provably semantically a no-op: the unbackticked substring `wayfinder/tickets/A6a-2.md` is the same file path the backticked form refers to; adding backticks changes only the Markdown rendering (italics/code styling), not the referenced artifact. A test (`tests/test_lint_no_source_field_drift.py::test_no_violations_after_pre_archive_patch`) verifies the post-patch state by re-running the lint script and asserting 0 violations.

**Alternatives considered**:
- *A (rejected)*: Open a separate `fix-spec-source-backticks-2026-09` change for the 4-line patch. Defeats atomicity; introduces a window where the lint gate (post-this-change) would reject any other change that archives between the two changes' archives.
- *B (rejected)*: Skip the patch and accept that the lint gate rejects the live spec tree. Defeats the gate's purpose (gate must pass for the change to archive); the change would archive `exit=1` and fail its own precondition.
- *C (rejected)*: Add a per-line `# noqa: lint-no-source-field-drift` exemption. Forbidden by the source-change `migrate-l678-source` design.md Decision 3 (zero-exemption rule) and by `fix-wayfinder-spec-source-field-drift` design.md (no exemption table).

## Risks / Trade-offs

- [R1: Hand-rolled tokenizer edge cases (escaped backticks, double-backtick code spans, HTML entities inside Source fields)] → Mitigation: the live spec tree uses NONE of these edge cases (verified by `grep -P '\\\\\`' openspec/specs/**/spec.md` returning 0 hits; `grep -P '\`\`' openspec/specs/**/spec.md` showing only multi-line code-block starts/ends, never inline double-backtick). If a future change introduces an edge case, the helper's `in_code_span` toggle logic will silently treat the second backtick of a double-backtick span as a code-span exit, which is incorrect for CommonMark double-backtick spans. The mitigation is: if a future spec uses double-backtick spans inside Source fields, the spec author should rewrite to single-backtick (the Source-field convention is single-backtick per the live spec's 36 lines). The lint script's docstring will document this limitation explicitly.
- [R2: Multiline Source-field lines (a `,` or `;` on the next line) are NOT supported] → Mitigation: the live spec tree uses single-line Source fields exclusively (verified by `grep -A1 '^\*\*Source:\*\*' openspec/specs/**/spec.md | grep -c '^---'` returning 0 hits, i.e. no Source line continues onto the next line). If a future spec violates this convention, the lint script will report the line as failing the first-item check (because the first item will be the entire line body up to the first paren-depth-0 / non-code-span delimiter on the SAME line, which may not be the primary reverse-link). The spec author must rewrite to single-line.
- [R3: The two helpers are not used by any other script in the repo (lint script is a single-file CLI tool)] → Mitigation: the helpers are private (`_unbackticked_refs`, `_split_top_level_items`, leading underscore), so they are documented as internal to the lint script. If a future change needs the same helpers (e.g. a different lint script that also parses Source fields), the helper module can be extracted to `scripts/_source_field_tokenizer.py` as a follow-up; this change does NOT pre-extract (premature abstraction per CLAUDE.md global guideline 2 "Simplicity First").
- [R4: The `test_no_violations_after_pre_archive_patch` regression test depends on the live spec tree being patched] → Mitigation: the test runs `lint_no_source_field_drift.lint_file(Path("openspec/specs/wayfinder/spec.md"))` against the live file (post-patch) and asserts `len(violations) == 0`. If the patch is reverted in a future change, the test will fail and signal the drift. The test does NOT require network or external state; it is hermetic to the file system.
- [R5: The 14-test count is a soft target, not a hard SLO] → Mitigation: the tests are listed by name in `tasks.md` §3.2, but the change may legitimately grow the count if a helper edge case surfaces during implementation. The hard target is "every Scenario in the modified req-34 is covered by at least one test"; the 14-test count is a planning estimate.
- [R6: `_unbackticked_refs()` uses `re.sub(r'\`[^\`]*\`', '', body)` to strip code spans, which fails for double-backtick spans] → Same mitigation as R1 — single-backtick is the convention; the docstring documents the limitation. If a future spec uses double-backtick, the regex must be upgraded to a state machine. The current `_unbackticked_refs` implementation uses the same single-pass scan as `_split_top_level_items` for consistency; the regex form is documented as an alternative implementation that is simpler but more fragile.

## Migration Plan

1. **Pre-archive spec patch** (`tasks.md` §2.1): wrap `wayfinder/tickets/A6a-2.md` in backticks at `openspec/specs/wayfinder/spec.md` L577, L639 and `openspec/specs/decompmoe-skeleton/spec.md` L208, L377. Verify by `grep -n 'wayfinder/tickets/A6a-2.md' openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md` showing all four occurrences are now backtick-wrapped.
2. **Lint script upgrade** (`tasks.md` §2.2): add `_unbackticked_refs`, `_split_top_level_items`, and extend `lint_file()` to call them. Verify by `python scripts/lint_no_source_field_drift.py` exit=0 against the post-patch spec tree.
3. **Test addition** (`tasks.md` §2.3): add `tests/test_lint_no_source_field_drift.py` with 14 tests. Verify by `uv run pytest tests/test_lint_no_source_field_drift.py -v` 14/14 pass.
4. **Full repo lint regression** (`tasks.md` §2.4): re-run `python scripts/lint_no_source_field_drift.py` and confirm exit=0, 0 violations. (This is the same as step 2 but called out separately to emphasize the binding acceptance criterion.)
5. **Full repo pytest regression** (`tasks.md` §2.5): re-run `uv run pytest tests/` and confirm all pre-existing 43 tests still pass plus the new 14 tests pass (57 total).
6. **`/opsx:archive`** (`tasks.md` §2.6): archive runs both lint scripts as precondition; both must exit=0.
7. **Post-archive independent verification** (`tasks.md` §3): verify (a) `python scripts/lint_no_source_field_drift.py` exits 0 against the merged main spec tree, (b) `tests/test_lint_no_source_field_drift.py` 14/14 pass on the merged main branch, (c) the 4 patched lines in the merged main tree are backtick-wrapped (visible via `git log -p openspec/specs/wayfinder/spec.md` showing the diff for L577 and L639).
8. **Rollback strategy**: `git revert` the archive merge commit. Because the change is lint script + spec text + new test file only (no production code, no test code changes to existing tests), rollback is low-risk. The lint script's structural checks revert to substring-only (the `migrate-l678-source` form); the 4 patched lines revert to their pre-change unbackticked form (and would re-violate the substring-only check via no — substring check still passes — but would violate the structural check if re-applied). The 14 new tests would be removed by the revert. The system returns to the pre-change state with no behavioral regression beyond the lint script's stricter check being temporarily absent.

## Open Questions

(none) — all 4 decisions resolved; the proposal has the go-ahead from the user (A1 scope: zero-dep hand-rolled tokenizer, paren-depth + code-span atomic split, 14 tests covering the fact-check synthetic cases).
