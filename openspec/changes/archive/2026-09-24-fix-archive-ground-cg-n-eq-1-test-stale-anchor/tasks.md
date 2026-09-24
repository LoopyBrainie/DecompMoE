# Tasks

## 1. Verify baseline state before edit

- [x] 1.1 Run `grep -nE '<a id="req-(34|35)"' "openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md"` and verify only `<a id="req-34">` matches (1 line at L5). Verify: grep output contains exactly 1 line containing L5 with `<a id="req-34">`. ✅ (verified 2026-09-24: 1 hit at L5)

- [x] 1.2 Run `grep -nE '<a id="req-35"' openspec/specs/wayfinder/spec.md` and verify it returns exactly 1 hit at live L496 (anchor for "CG n=1 boundary behavior" Requirement). Verify: grep output contains L496 only. ✅ (verified 2026-09-24: 1 hit at L496)

- [x] 1.3 Run `grep -nE 'req-34' openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/*.md openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` and verify it returns **9 occurrences** total: spec.md:5 (anchor) + tasks.md L3, L4 + design.md L7, L12, L76, L88 + proposal.md L7, L24. ✅ (verified 2026-09-24: exactly 9 hits — design.md:7,12,76,88 + proposal.md:7,24 + tasks.md:3,4 + spec.md:5; `proposal.md` L19 (req-35 post-889d81c) correctly absent from list)

- [x] 1.4 Read the first 10 lines of `archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` and verify the file currently starts with `# wayfinder Specification (delta)` on line 1 (no annotation block present). Verify: line 1 is the heading, lines 2-5 are blank/`## ADDED Requirements`/`\n`/`<a id="req-34"></a>`. ✅ (verified 2026-09-24: L1=`# wayfinder Specification (delta)`, no annotation block)

- [x] 1.5 Read `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` lines 1-15 to verify the precedent annotation block format. ✅ (verified 2026-09-24: precedent uses multi-line HTML comment `<!--` … `(historical, …; superseded by …)` … `-->` pattern; will mirror in Task 2.1)

## 2. Edit archive spec delta file: anchor relabel + annotation prepend

- [x] 2.1 ✅ (verified 2026-09-24: 8 annotation lines + 1 blank prepended; annotation block opens with `<!--` on L1, contains `(historical, anchor was <a id="req-34"> at L442` and `(superseded by fix-cg-n-1-test-anchor-collision-and-math-coverage commit f16cb12` substrings, closes with `-->`, then blank, then original L1 heading)
- [x] 2.2 ✅ (verified 2026-09-24: anchor `<a id="req-34">` → `<a id="req-35">` in archive spec.md)
- [x] 2.3 ✅ (verified 2026-09-24 via `git diff`: +8 annotation lines + 1 blank line (top of file), 1 line modification (anchor), Requirement body / 4 Scenarios / `**Source:**` field preserved verbatim — no further changes)

## 3. Edit 8 prose references for intra-doc consistency

- [x] 3.1 ✅ (verified 2026-09-24: tasks.md L3 `req-34` → `req-35`; 0 hits for `req-34` post-edit confirmed)
- [x] 3.2 ✅ (verified 2026-09-24: tasks.md L4 `req-34` → `req-35`; 0 hits for `req-34` post-edit confirmed)
- [x] 3.3 ✅ (verified 2026-09-24: design.md L7 `req-34` → `req-35`)
- [x] 3.4 ✅ (verified 2026-09-24: design.md L12 `req-34` → `req-35`)
- [x] 3.5 ✅ (verified 2026-09-24: design.md L76 `req-34` → `req-35`)
- [x] 3.6 ✅ (verified 2026-09-24: design.md L88 `req-34` → `req-35`; 0 hits for `req-34` in design.md post-edit confirmed)
- [x] 3.7 ✅ (verified 2026-09-24: proposal.md L7 `req-34` → `req-35`)
- [x] 3.8 ✅ (verified 2026-09-24: proposal.md L24 `req-34` → `req-35`; 0 hits for `req-34` in proposal.md post-edit confirmed)
- [x] 3.9 ✅ (verified 2026-09-24: only `req-34` matches are inside archive spec.md annotation block L2 + L4 — both intentional historical-recording prose; tasks/design/proposal all 0 hits)
- [x] 3.10 ✅ (verified 2026-09-24: 12 `req-35` hits total across 4 files — design.md:4 + proposal.md:3 + tasks.md:2 + spec.md:3; 12 ≥ 9 confirms broad consistency; archive spec.md L13 anchor is `<a id="req-35">`)

## 4. Lint and validate

- [x] 4.1 ✅ (verified 2026-09-24: `lint_no_source_field_drift.py` exit=0 — `OK (3 file(s) scanned, no violations)`)
- [x] 4.2 ✅ (verified 2026-09-24: `openspec validate --specs` exit=0 — `Totals: 3 passed, 0 failed (3 items)`)
- [x] 4.3 ✅ (verified 2026-09-24: `openspec validate <name> --type change` → `Change 'fix-archive-ground-cg-n-eq-1-test-stale-anchor' is valid`)
- [x] 4.4 ✅ (verified 2026-09-24: status → `Progress: 3/3 artifacts complete (1 skipped)`)

## 5. Post-edit hygiene checks

- [x] 5.1 ✅ (verified 2026-09-24: byte-level CRLF check on all 4 archive files returns 0 pairs each — Windows Edit tool + non-ASCII content did not introduce CRLF pollution)
- [x] 5.2 ✅ (verified 2026-09-24: `git diff --stat` shows exactly 4 files modified under the folder: design.md +8/-4, proposal.md +2/-2, specs/wayfinder/spec.md +9/-1, tasks.md +2/-2; 17 insertions, 9 deletions total)
- [x] 5.3 ✅ (verified 2026-09-24: live spec has `<a id="req-35">` at L496 (CG n=1 boundary) and `<a id="req-34">` at L740 (Source Field Format Invariant); archive spec.md has `<a id="req-35">` at L13 (real anchor) + `<a id="req-34">` only inside annotation block prose at L2 — anchor symmetry between archive's "CG n=1 boundary" and live spec's "CG n=1 boundary" confirmed: BOTH are `req-35` now)
- [x] 5.4 ✅ (verified 2026-09-24: `git status --porcelain` for the 4 declared edit targets shows ` M design.md`, ` M proposal.md`, ` M specs/wayfinder/spec.md`, ` M tasks.md`; the change's own planning folder also appears as `?? openspec/changes/fix-archive-ground-cg-n-eq-1-test-stale-anchor/` (expected, since planning artifacts were just written); other porcelain entries (` M apply-checklist.md`, ` M .../2026-09-11-enhance-safeguards-closed-form-tests/tasks.md`, untracked files `?? .commit_msg_*.txt`, `?? tmp_verify.py`, etc.) are pre-existing workspace state, NOT introduced by this change)

## 6. Final archive change status check

- [x] 6.1 ✅ (verified 2026-09-24: `openspec list` shows `fix-archive-ground-cg-n-eq-1-test-stale-anchor` at `26/27 tasks just now`; other in-flight changes `fix-archive-tighten-test-precision-tolerance-req-claim-drift` (No tasks) + `2026-09-23-01-fix-ticket-stale-numerical-4file-batch` (Complete) do not touch `archive/2026-09-16-ground-cg-n-eq-1-test/`; no conflict)

## 7. Post-review findings fixes (scope expansion per user directive 2026-09-24 23:21)

**Scope expansion rationale**: Review of this change by the Python reviewer agent (`agent-b1a39f2827bf`) returned 1 MINOR + 1 INFO. Per user's explicit directive "修复本change内所有findings" at 2026-09-24 23:21, scope is widened to address both findings despite reviewer's "out-of-scope for this change" callouts. CLAUDE.md §3 "Surgical Changes" caveat noted and overridden by user decision. Tasks below execute MINOR-1 (test comment accuracy) and INFO-1 (test-side precision tightening) without touching live spec.md (verbatim-equivalence preserved — see Decision 4 in design.md).

- [x] 7.1 ✅ (verified 2026-09-24 23:21: comment at `tests/test_metrics.py:350-364` rewritten to acknowledge numel==1 coincidence + reference `test_cg_l2_norm_closed_form` (req-20) as L2 discriminator; false claim "pins the implementation path" removed; `Select-String -Path tests\test_metrics.py -Pattern 'pins the implementation path'` returns 0 hits; bare `==` assertion at L360-364 preserved with FP-exact equality claim)
- [x] 7.2 ✅ (verified 2026-09-24 23:21: 5 boundary assertions in `test_cg_n_eq_1_returns_magnitude` tightened `abs=1e-12` → `abs=1e-15` (L327 positive 1D, L332 negative 1D, L337 zero 1D, L344 multi-dim 2D, L348 multi-dim 3D); `pytest tests/test_metrics.py::test_cg_n_eq_1_returns_magnitude -v` PASSED; remaining 7 `abs=1e-12` instances are out-of-scope per Decision 4 alternatives (MCI tests L108/120/254/262, CG zero_grad tests L275/304, cache test L465, plus 2 docstring references at L103/L273 — all unrelated to CG n=1 boundary); archive spec.md body NOT touched (verbatim-equivalence with live spec preserved))
- [x] 7.3 ✅ (verified 2026-09-24 23:21: post-edit hygiene all green — (a) `pytest tests/test_metrics.py -v` → 29/29 PASSED with tightened abs values; (b) `python scripts/lint_no_source_field_drift.py` → exit=0 "3 file(s) scanned, no violations"; (c) `openspec validate --specs` → 3 passed, 0 failed (3 items); (d) byte-level CRLF check on `tests/test_metrics.py` → 0 pairs)
