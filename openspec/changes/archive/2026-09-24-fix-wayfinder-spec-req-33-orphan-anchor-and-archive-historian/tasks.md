# Tasks

## 1. Verify baseline state before edit

- [x] 1.1 Run `grep -nE '<a id="req-33"' openspec/specs/wayfinder/spec.md` and verify it returns exactly 1 match at L740 (the orphan anchor). Verify: grep output contains `L740` and only that line; no `### Requirement:` title follows within 5 lines after L740.

- [x] 1.2 Run `grep -nE 'req-33' openspec/specs/wayfinder/spec.md` and verify only L740 (anchor) and L823 (text inside req-36 referencing req-20, unrelated) match. L823 reference to `req-20` is unrelated to the req-33 anchor cleanup. Verify: grep output returns at most 2 lines (L740 + L823), and L823 mentions `req-20` not `req-33` as the reference.

- [x] 1.3 Read `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` and verify it currently lacks a `(historical, ...)` annotation block at top. Verify: first 5 lines of the file contain only the original `## ADDED Requirements` and `### Requirement: Test Guard Precision for Closed-Form Numerical Claims` headers with no annotation block.

## 2. Delete orphan anchor in `wayfinder/spec.md`

- [x] 2.1 Edit `openspec/specs/wayfinder/spec.md` to delete the single line `<a id="req-33"></a>` at L740. Use Edit tool with `old_string` matching only that line and `new_string` empty. Verify: `grep -nE '<a id="req-33"' openspec/specs/wayfinder/spec.md` returns 0 matches (anchor cleanup confirmed).

- [x] 2.2 Re-grep `req-33` in `openspec/specs/wayfinder/spec.md` to confirm only the L823 unrelated reference to `req-20` remains (1 match max). Verify: grep output does not contain L740 anymore; the L823 match (inside req-36 text) is preserved.

## 3. Annotate archive delta file with historical supersede

- [x] 3.1 Prepend a `(historical, ...; superseded by ...)` annotation block to `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md`, placed before the existing `## ADDED Requirements` header. The annotation block uses the same pattern as `wayfinder/tickets/A8-2.md` L70 + L74 and `governance/spec.md` req-gov-2 description. Use Edit tool with `old_string` matching the existing first line and `new_string` adding the annotation block followed by the original first line. Verify: first 30 lines of the file now start with `(historical, ...)` pattern mentioning `(i) original 2026-09-06 proposal`, `(ii) policy reversal by commits bec147d + 83a0503`, `(iii) final landing as governance/req-gov-1 via migrate-l678-source (commit 34b37be)`.

- [x] 3.2 Re-read the full archive delta file and verify the original `## ADDED Requirements` + `### Requirement: Test Guard Precision for Closed-Form Numerical Claims` body is preserved untouched (annotation is metadata, not a modification of original delta content). Verify: `git diff -- openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` shows only the new annotation block at top; original body content unchanged.

## 4. Lint and validate

- [x] 4.1 Run `python scripts/lint_no_source_field_drift.py` and verify exit code is 0. Verify: command output ends with `0 violations across governance / wayfinder / decompmoe-skeleton` (or equivalent zero-violation summary).

- [x] 4.2 Run `openspec validate --specs` and verify exit code is 0. Verify: command output ends with pass summary (no validation errors).

- [x] 4.3 Run `openspec validate --change fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` and verify exit code is 0. Verify: command output ends with pass summary for this change.

## 5. Post-edit sanity check

- [x] 5.1 Run `git diff --stat openspec/specs/wayfinder/spec.md openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` and verify exactly 2 files changed, with `wayfinder/spec.md` showing deletions only (-1 line) and archive delta showing insertions only (+N lines, where N is the annotation block size). Verify: 2 files in diff stat, surgical edit scope confirmed.

- [x] 5.2 Byte-level CRLF check on both edited files (per `.audit/` hygiene lessons re Windows Edit tool + non-ASCII content). Verify: `python -c "import sys; data = open(sys.argv[1], 'rb').read(); print(f'CRLF count: {data.count(b\"\\r\\n\")}')" openspec/specs/wayfinder/spec.md` returns `CRLF count: 0`; same check on archive delta file also returns 0.

- [x] 5.3 Confirm no live spec, ticket, code, or test file is touched outside the 2 declared edit targets. Verify: `git diff --stat` shows only the 2 files; no other path appears in `git status --porcelain` after edits.

## 6. Post-review precision fix

- [x] 6.1 Update archive annotation block to use precise pre-migration line range for req-33 (initially cited `L662-L704`, but reviewer flagged minor precision nuance: actual is `L662-L705` for full block = 44 lines including 2 trailing blanks; body proper is `L664-L703`). Verified via `git show 34b37be~1:openspec/specs/wayfinder/spec.md`. Edit replaced `L662-L704` reference with full range + body proper + verification provenance. Re-run lint + validate: `lint_no_source_field_drift.py` exit=0; `openspec validate --specs` 3 passed 0 failed.

> **Note**: Reviewer's O1 + O2 observations (orphan Requirements in `wayfinder/spec.md` L195/L351/L520 and missing `req-13` anchor in `decompmoe-skeleton/spec.md` L293) are pre-existing defects, **NOT in this change's scope** per `CLAUDE.md` §3 "Touch only what you must". Per user decision (2026-09-24), O1/O2 are temporarily ignored. No follow-up change opened at this time.