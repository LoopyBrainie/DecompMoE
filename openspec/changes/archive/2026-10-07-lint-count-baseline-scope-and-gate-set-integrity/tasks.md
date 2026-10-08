# Tasks

## 1. Pattern changes in `lint_no_baseline_counts.py`

- [x] 1.1 D1 ratio pattern: add the `(?<!Phase\s)(?<!Step\s)(?<!阶段\s)` lookbehinds, keeping the
      remainder of the pattern byte-identical
- [x] 1.2 D3 commit-hash baseline: require at least one digit in the matched run
- [x] 1.3 D4 exemption: `histor` → `historical`; split `has_exemption` so ASCII markers match on a
      word boundary and CJK markers keep substring matching
- [x] 1.4 D2 baseline scope: test exemption/baseline against the count's own line, retaining the
      contiguous `|` run as the block for table rows
- [x] 1.5 Correct the `find_unbaselined_counts` docstring, which currently describes per-count
      baselining while the code does per-block

## 2. Gate runner

- [x] 2.1 D5 add `gate_digest` (sha256 over sorted lint names + bytes) as a fourth
      `worktree_snapshot` component and compare it in `_snapshot_differs`
- [x] 2.2 D5 replace the printed lint count with the recorded names
- [x] 2.3 D6 reconfigure stdout/stderr in `main()` so a failing gate can print its report on GBK

## 3. Tests

- [x] 3.1 D1 `Phase 2/3` is silent while `3/16`, `2/3` and `48 / loose 48` still fire
- [x] 3.2 D3 `defaced` / `effaced` / `feedbac` confer no baseline while `82b84d6` / `051f247` /
      the full 40-char hash still do
- [x] 3.3 D4 `histor` / `history` / `historian` are not exempt while `historical`, `不可复算`,
      `无法复算` and `not reconstructible` still are
- [x] 3.4 D2 a baseline on the last line of a multi-count paragraph no longer blesses the paragraph
- [x] 3.5 D2 a table row still accepts a baseline named in its header row
- [x] 3.6 D5 `worktree_snapshot()` carries a `gate_digest` key and two different lint sets produce
      different digests
- [x] 3.7 each of 3.1–3.6 is asserted by hard equality with the actual value in the failure message

## 4. Verification

- [x] 4.1 `run_gates.py` exits 0 in a detached worktree
- [x] 4.2 re-measure the corpus counts as of `2026-10-07-lint-count-baseline-scope-and-gate-set-integrity`: D1 504 / D3 505 / D4 510 / D2 955
- [x] 4.3 confirm the lint's own `docs/` scan is still 0 findings
## 5. Post-implementation review findings (independent review of this change)

Every item below was raised against the landed change, independently re-derived, and fixed.
Measurement base is pinned: the pre-change pattern set unless a row says otherwise.

- [x] 5.1 the FAIL summary named `openspec validate --specs --strict` while the argv at the call site
      no longer passes `--strict` — the gate misreported the command it ran on failure
- [x] 5.2 `design.md` reported `505 → 955 (+450)`, a cross-base subtraction comparing pre-change
      patterns against post-change patterns. Re-derived on one base for
      `2026-10-07-lint-count-baseline-scope-and-gate-set-integrity`: baseline scope alone is **+388**
      and the shipped total is **904**. Whole chain now tabulated
- [x] 5.3 `design.md` claimed the table exception "changes nothing on this corpus". False: dropping it
      adds **46** (939 vs 893). Claim replaced with the measurement
- [x] 5.4 exemptions had silently been narrowed to per-line alongside baselines, unprobed. Measured
      113 own-line vs 174 elsewhere, so **exemptions return to block scope** and the asymmetry is now
      deliberate, stated in `_is_baselined`, and pinned in both directions
- [x] 5.5 the report quoted the block's first count line rather than the line that failed, so triage
      regularly quoted a line visibly carrying the baseline. Now reports line `i`; regression pinned
- [x] 5.6 granularity is per line, not per count — the code comment claimed "every count". Comment
      corrected and `test_baseline_scope_is_per_line` pins the choice
- [x] 5.7 the discriminative half of `test_red_on_real_instance_and_green_once_baselined` had
      inverted without the module docstring saying so. Docstring now states which half discriminates
      and why a silent assertion cannot
- [x] 5.8 the 857 intermediate was measured on a different base than the 943; same-base re-measure
      reads 852. Recorded rather than deleted
- [x] 5.9 `proposal.md` claimed no archived file triggers the lint's non-UTF-8 read. One does —
      `archive/2026-09-23-07-fix-spec-territory-seeding-phase-0/tasks.md` at bytes 32-33. Corrected:
      it is harmless only because the archive is never read
