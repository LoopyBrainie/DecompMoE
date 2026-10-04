# Tasks

## 1. Code — gate snapshot comparison (design D3)

- [x] 1.1 `scripts/run_gates.py` — remove `status_lines` from the compared-key tuple in
      `_snapshot_differs`, and add a comment at that site stating the exclusion and its
      reason (the surjectivity property from D3, **not** a "coarser function of the same
      string" claim, which is self-referential and false of the digests)
- [x] 1.2 `scripts/run_gates.py` — leave `worktree_snapshot()`'s returned key set at four
      keys and leave the `dirty_entries=` output intact; confirm by inspection that only
      the comparison tuple changed
- [x] 1.3 `scripts/run_gates.py` — change the `anchor-ledger --verify` summary line from
      "these two classes" to "these three classes" (design D4)

## 2. Tests

- [x] 2.1 `tests/test_run_gates.py` — in
      `test_snapshot_differs_names_every_moved_field`, change the expected count from 4 to
      3 and drop `status_lines` from the named-key loop, keeping the test's original
      intent (every *compared* field is named)
- [x] 2.2 `tests/test_run_gates.py` — add
      `test_derived_entry_count_alone_does_not_invalidate_the_run`: with `head`,
      `tracked_digest`, and `untracked_digest` held equal and only `status_lines`
      changed, `_snapshot_differs` MUST return `[]`. Assert the contract directly; do
      not assert the absence of a hypothetical counterexample (design D3, "Limits")
- [x] 2.3 `tests/test_run_gates.py` — in
      `test_genuine_loss_is_still_reported_when_a_removal_is_also_declared`, assert the
      summary line names three classes, and cross-check that number against the count of
      distinct class labels in `run_gates.py`'s source, so adding or dropping a class
      turns the test red instead of leaving the prose stale
- [x] 2.4 Confirm no test was deleted or skipped to make the suite pass; net test count
      must rise

## 3. Spec delta

- [x] 3.1 `specs/governance/spec.md` — `## MODIFIED Requirements` for `req-gov-10`:
      add the third `removed` class to the description, extend the `req-gov-10` Source
      line with this change's design reference, keep all six existing Scenario titles
      character-for-character, and add the new Scenario
- [x] 3.2 `specs/governance/spec.md` — `## MODIFIED Requirements` for `req-gov-11`:
      add the match-end-offset slicing invariant to the description, extend the
      `req-gov-11` Source line, keep all three existing Scenario titles
      character-for-character, and add the new Scenario
- [x] 3.3 Verify by script — not by eye — that every existing Scenario title in
      `openspec/specs/governance/spec.md` for `req-gov-10` and `req-gov-11` appears
      verbatim in the delta, and that each block gained exactly one title

## 4. Validation

- [x] 4.1 `bunx openspec validate <change> --type change --strict` → exit 0
- [x] 4.2 `uv run python scripts/lint_no_source_field_drift.py` → exit 0 (both
      `governance` Requirements must carry a compliant `**Source:**` reverse link)
- [x] 4.3 `uv run pytest tests/test_run_gates.py -q` → all green, then full
      `uv run pytest -q`. Measured: `tests/test_run_gates.py` 34 → 36 test
      functions, `tests/test_lint_no_source_field_drift.py` 37 → 38, so this
      change adds **3** and removes none. The full suite collects **430**
      (429 passed / 1 skipped) at the time of writing, but that absolute figure
      includes unrelated modifications another session has in the shared
      worktree, so the per-file delta above is the claim that belongs to this
      change, not the suite total.
- [x] 4.4 `uv run python scripts/run_gates.py --change <change>` → exit 0 on a
      quiesced worktree. Enumerate the untracked-file set before the run and
      produce no new untracked files while it is in flight, or the run reports
      `GATE RESULT INVALID` with exit 2 and its verdict is void. Note that all
      pytest/uv artifacts are gitignored, so they do not move the untracked
      digest; the risk is *new untracked files this session does not control*.
      Measured: `GATE OK`, exit 0, `head=fb79453`, 51 dirty entries, 4 lints +
      `openspec validate --specs --strict` + the change's own `--type change
      --strict` + anchor coverage (69 anchors / 3 capabilities) + pytest
      (429 passed, 1 skipped) all PASS. Exit 0 rather than 2 is the load-bearing
      part: it says the worktree did not move during the run, so unlike an
      INVALID verdict this result is reusable.

## 5. Post-review remediation (independent review, `agent-b1a39f2827bf`)

> Two modified files outside this change (`src/decompmoe/gating.py`,
> `wayfinder/tickets/WF-1.md`) are **not ours**. The `WF-1.md` working-tree edit
> deletes a `(historical, ...)` annotation that `req-gov-4` clause 4a mandates, and
> another session is actively churning that file. Escalated to the user; not fixed
> here, and excluded from staging in 6.2.

- [x] R.1 HIGH — the justification for dropping `status_lines` was malformed and
      self-referential ("a coarser function of the same porcelain string" is
      vacuous, and false if the referent is the compared digests, which are not
      functions of porcelain at all). Replace with the surjectivity form in
      `worktree_snapshot`'s docstring, at the comparison site, and in `design.md`
      D3. Record the measured result: 11 state transitions, zero counterexamples
      — empirically supported, still not a proof
- [x] R.2 MEDIUM — the `"three classes"` assertion froze wording without pinning
      the principle. Keep the normative wording check (the spec mandates it) and
      add a derived cross-check that the stated number equals the number of
      distinct class labels in `run_gates.py`'s source
- [x] R.3 MEDIUM — the new `req-gov-11` MUST about an unmatchable yielded line
      was unfalsifiable (no test, and the implementation calls the branch
      unreachable). Drive it with
      `test_lint_reports_a_source_line_yielded_without_matching_the_pattern`,
      which stubs `iter_source_lines`; verified by negative probe
- [x] R.4 LOW — the new derived-count test only drove the private helper, so a
      broken end-to-end verdict would still pass. Add
      `test_gates_stay_valid_when_only_the_derived_count_moves`, which goes
      through `cmd_gates` and asserts exit 0 / no `GATE RESULT INVALID` /
      `dirty_entries=` still surfaced; verified by negative probe
- [x] R.5 INFO — `design.md` D4 said the three lists are "on screen", but each is
      conditional. Restated as a statement about the code's class vocabulary, and
      the test now derives from the vocabulary rather than the per-run count
- [x] R.6 LOW — the archive-freeze check in 6.1 only compared content, so it was
      blind to a new untracked archive directory. Hardened to also compare the
      file list

## 6. Pre-commit

- [x] 6.1 Confirm nothing under `openspec/changes/archive/**` changed. Commit
      `5f3e286` froze archived changes and admits no exception. Check BOTH:
      - content: `git diff --quiet HEAD -- openspec/changes/archive`
      - file list: `git status --porcelain -uall -- openspec/changes/archive` for
        **untracked** entries, plus the tracked count against a prior revision

      Measured: archive content byte-identical to `HEAD`; tracked archive file count
      642 → 646, the +4 being a *concurrent session's* archive
      (`2026-10-04-close-round5-scope-pin-and-docstring-drift/`) that appeared
      untracked mid-session and was then committed by that session. This is exactly
      the case a content-only check cannot see, and the reason the file-list half is
      not optional. The one untracked archive entry left is the pre-existing
      `2026-10-01-audit-errata-a1-numeric-guard-list/`, which is NOT ours.
- [x] 6.2 Stage only this change's files: `scripts/run_gates.py`,
      `tests/test_run_gates.py`, `tests/test_lint_no_source_field_drift.py`, and the
      five files under this change's directory. Explicitly exclude
      `wayfinder/tickets/WF-1.md` and `src/decompmoe/gating.py` — they are another
      session's in-flight work, and a blanket `git add -A` would sweep them in.
      Done: the index was verified clean of anyone else's staged content first,
      then exactly 8 paths were staged and re-checked for the forbidden set
      (archive, `WF-1.md`, `gating.py`) before committing.
- [x] 6.3 Commit on `dev` **without** `--amend`. A concurrent session shares this
      worktree and the same index; amend rewrites another session's commit.
      Done: `1f2f13c`, 8 files. This tick is a separate follow-up commit rather
      than an amend, both because amend is forbidden here and because the point
      of the restructuring above is that the task list reaches 100% without
      rewriting history.

## Post-apply procedure — deliberately NOT tasks

**The archive is a lifecycle transition, not a work item, so it is not a checkbox
above.** An earlier draft of this file did put it in task 4.4. That was a
category error with a real failure mode:

- Ticking "archive" requires the archive to have happened.
- The archive freezes this directory (`5f3e286`: an archived change must not be
  modified), so the tick can never be written afterwards.
- The task list therefore can never reach 100%, and the apply progress counter is
  stuck below complete forever.

This is not hypothetical here: 21 archived changes in this repository carry
unticked tasks, and `2026-09-22-06-fix-spec-narrative-wording-batch` has
`- [ ] 2.10 archive 步骤:` — the same mistake, already institutionalized. If apply is
ever to report 100% meaningfully, those 21 are the debt to clear.

So the sequence is, with ownership split along the freeze line:

1. **apply** (this file, 100% of the checkboxes above) — implementation, tests,
   delta, validation, commit. Everything here happens *before* the freeze.
2. **`/opsx:archive`, user-driven, after the commit** — the five-step ledger
   procedure `req-gov-10` mandates: write the ledger, archive, compare the ledger
   item by item, restore any swallowed anchor **surgically**, re-verify. Re-running
   the archive to repair a lost anchor is forbidden: a second archive overwrites the
   first repair. Post-archive verification lives in the gate run, not here, because
   this file can no longer be edited to record it.
