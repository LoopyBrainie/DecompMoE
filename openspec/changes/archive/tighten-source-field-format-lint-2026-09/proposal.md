## Why

`scripts/lint_no_source_field_drift.py`(introduced by `fix-wayfinder-spec-source-field-drift`, hardened by `migrate-l678-source` into the `/opsx:archive` gate per CLAUDE.md §3) currently enforces Source-field correctness at the **pure-substring layer only**: it checks `if required not in line:` on a `**Source:**` line, where `required` is per-capability (`CLAUDE.md` for governance, `wayfinder/tickets/` for everything else). This is sufficient for **presence** but insufficient for **format**: a `**Source:**` line whose primary reverse-link is `wayfinder/tickets/A6a-2.md (initial A6a-2 design intent)` (no backticks) passes today's lint, and a line whose first item is a `change \`foo\` design.md (Decision N)` clause (with the ticket reverse-link later) also passes — both are non-conforming under the convention that reverse-links are **backtick-wrapped code spans** and that the **primary reverse-link is the first top-level item**.

Fact-check of the lint script (2026-09-14, performed against the live spec tree) confirms:
- **4 unbackticked Source lines** today (already passed the substring check but violate the backtick convention): `openspec/specs/wayfinder/spec.md` L577 + L639, `openspec/specs/decompmoe-skeleton/spec.md` L208 + L377.
- **0 governance violations** (the single governance Source line at `openspec/specs/governance/spec.md` is fully backtick-wrapped and has `CLAUDE.md` as its first item).
- Each unbackticked line's `first code span` is also missing (no code span at all on the first item), so adding backticks fixes both ② and ③ for the same line in a single edit.

We need ① capability-aware (already in place since `migrate-l678-source`), ② backtick-wrapped reverse-links (currently absent), ③ primary-reverse-link-must-be-first (currently absent). The change tightens `lint_no_source_field_drift.py` to enforce ②③ structurally (single-line tokenizer with code-span atomicity + paren-depth-aware comma/semicolon split) so the lint gate catches the 4 live violations **and** prevents future reintroduction. The script gains two pure-function helpers (`_unbackticked_refs`, `_split_top_level_items`) that can be unit-tested independently of the lint orchestration, giving the spec-level ②③ Scenarios a direct `pytest.approx`-equivalent target.

## What Changes

- **Modify `scripts/lint_no_source_field_drift.py`** to add structural Source-field checks beyond substring presence:
  - **New helper `_unbackticked_refs(body: str, required_substring: str) -> list[str]`**: strips code spans from the line body, then returns every `required_substring`-bearing substring that **remained** (i.e. appeared OUTSIDE backticks). Empty list means every reference is backtick-wrapped.
  - **New helper `_split_top_level_items(body: str) -> list[str]`**: splits a `**Source:**` body by `,` or `;` at paren-depth 0, with code-span atomicity (a backtick toggles an atomic flag; a delimiter inside a code span does NOT split). Returns the top-level items in order; the first item is the "primary" reverse-link container.
  - **Modify `lint_file()`** to emit two new violation reason codes in addition to the existing "missing required substring" reason: `"unbackticked reverse-link: <substring>"` (from `_unbackticked_refs`) and `"first item is not the primary reverse-link (first code span = <...>, required substring = <required>)"` (from `_split_top_level_items` + first-code-span extraction).
  - **Preserve ① capability-aware rule** verbatim: `REQUIRED_SUBSTRING_BY_PATH_RELATIVE` + `required_substring_for(path)` + `DEFAULT_REQUIRED_SUBSTRING` are unchanged in semantics. The `governance` → `CLAUDE.md` and default → `wayfinder/tickets/` dispatch is the prerequisite for ②③ to be meaningful (each capability's "primary reverse-link" is its per-capability required substring).
- **Modify `openspec/specs/wayfinder/spec.md` req-34** `Source Field Format Invariant for OpenSpec Specs` to add two new Scenarios:
  - "Reverse-link must be wrapped in backticks" — every `**Source:**` line's reverse-link tokens (`wayfinder/tickets/<ID>.md` / `CLAUDE.md`) MUST appear inside a code span (backtick-delimited); a reverse-link that appears OUTSIDE a code span is a violation regardless of substring presence.
  - "Primary reverse-link must be the first top-level item" — the first top-level item (split by `,` / `;` at paren-depth 0, code-span atomic) MUST be a code span whose contents include the capability's required primary reverse-link substring; a `change \`foo\` design.md (Decision N)` clause MAY NOT precede the primary reverse-link.
- **Add `tests/test_lint_no_source_field_drift.py`** with 14 unit tests covering the helpers and the orchestrator against synthetic Source lines (fact-check cases from 2026-09-14: missing-backticks, change-first-ticket-second, paren-internal-comma-no-split, multi-ticket-first-item, governance/default capability dispatch, repo-wide regression on the post-fix spec tree). The test file's docstring back-links to the new req-34 Scenarios.
- **Pre-archive spec patch (inline in this change's spec delta)**: fix the 4 unbackticked Source lines by adding backticks around the `wayfinder/tickets/A6a-2.md` substring. After the patch, every existing Source line in the repo satisfies ① + ② + ③:
  - `openspec/specs/wayfinder/spec.md` L577, L639
  - `openspec/specs/decompmoe-skeleton/spec.md` L208, L377
  - The patch is one-token-per-line (`wayfinder/tickets/A6a-2.md` → `` `wayfinder/tickets/A6a-2.md` ``); no semantic change.

No new dependencies (`pyproject.toml` dependencies unchanged: torch + torchvision only). The tokenizer is a hand-rolled single-pass scan over a single `**Source:**` line — no `mistune` / `markdown-it-py` / AST parser. This is a deliberate cost/benefit trade-off: a one-lint-script Markdown parser is not worth the dependency surface for a project whose only Markdown structure the lint cares about is the inline code span + paren depth at the line level.

## Capabilities

### New Capabilities

(none) — no new behavioral capability. The change adds structural checks to an existing lint script and refines the existing `wayfinder` spec invariant.

### Modified Capabilities

- `wayfinder`: req-34 `Source Field Format Invariant for OpenSpec Specs` gains two new Scenarios covering ② (backtick wrapping) and ③ (primary-reverse-link-first). The Rule body itself is unchanged; only the Scenario coverage expands. No new Requirement, no removal. The `decompmoe-skeleton` and `governance` capabilities inherit the same rule by reference (req-34's Rule body is capability-agnostic; its Scenarios are the executable form) — no separate modification needed for those.

## Impact

- **Spec artifacts**:
  - `openspec/specs/wayfinder/spec.md` — req-34 gains 2 new Scenarios (~6-10 lines); the Source line for req-34 itself is unchanged (already backtick-wrapped).
  - `openspec/specs/wayfinder/spec.md` — L577, L639: 2 tokens wrapped in backticks (pre-archive patch; semantically a no-op).
  - `openspec/specs/decompmoe-skeleton/spec.md` — L208, L377: 2 tokens wrapped in backticks (pre-archive patch).
- **Tooling artifacts**:
  - `scripts/lint_no_source_field_drift.py` — adds 2 helpers + modifies `lint_file()` to call them; ~80 lines added. The existing `iter_source_lines`, `collect_paths`, `required_substring_for`, `_repo_root` are unchanged. The script remains a single-file `python -m` invocation, exit-code-based, no new CLI flags, no new env vars, no exemption registry.
  - `tests/test_lint_no_source_field_drift.py` — NEW file, ~150 lines, 14 tests, follows project test-file convention (docstring back-links to spec, `torch.manual_seed(0)`-style deterministic setup, `pytest.approx`-equivalent for invariant checks via direct equality on lists/strings).
- **Code layer**: zero changes (no `src/decompmoe/` edits).
- **Gate behavior**:
  - **Before** (current state, post-`migrate-l678-source`): `python scripts/lint_no_source_field_drift.py` → `exit=0, 0 violations` (substring check passes because 4 unbackticked lines still contain the substring).
  - **After (pre-archive)**: script detects 4 new violations (2 unbackticked-ref reasons for the 4 lines, where each line also gets 1 first-item-not-primary reason → 8 violations in the pre-patch state).
  - **After (post-patch + archive)**: `exit=0, 0 violations`. Future drift re-introducing either anti-pattern will be rejected at archive time.
- **Test layer**: `uv run pytest tests/test_lint_no_source_field_drift.py -v` → 14/14 passed (helper + orchestrator + regression on live repo). Existing 43 tests unchanged.
