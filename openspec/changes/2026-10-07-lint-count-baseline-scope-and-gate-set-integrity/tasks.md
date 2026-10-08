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