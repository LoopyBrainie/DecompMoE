# Tasks: enhance-safeguards-closed-form-tests

> **Scope**: apply phase is verification-only. All spec + test edits were authored in the planning session (2026-09-11) and are present in working dir at apply-phase entry. The apply phase confirms those edits match this change's `specs/decompmoe-skeleton/spec.md` MODIFIED delta, runs the verification gates, and stages the commits per `CLAUDE.md §3` (Spec-level 变更 must archive) and §4 (offshore-git-workflow: linear `dev`, `--no-ff` to `main` then `release`).

## 1. Pre-apply validation

- [x] 1.1 Confirm the working dir's `openspec/specs/decompmoe-skeleton/spec.md` matches the MODIFIED delta in `openspec/changes/2026-09-11-enhance-safeguards-closed-form-tests/specs/decompmoe-skeleton/spec.md` — verify by `diff <(git show HEAD:openspec/specs/decompmoe-skeleton/spec.md | awk '/^### Requirement: Five Numerical Safeguard Helpers$/{f=1} f{print; if(/^### Requirement: / && !/Five Numerical/){exit}}') openspec/specs/decompmoe-skeleton/spec.md | head -120` produces zero diff (after stripping the body of `Five-Phase Schedule State Machine` block via the awk termination). The new Scenarios (`Scenario: NaN ladder default at consecutive_nan=0 (no NaN observed)` and `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)`) MUST be present and verbatim.
  DONE — diff between working-dir block (L204-L246) and delta block returns ONLY the trailing `Five-Phase Schedule State Machine` outside modified-requirement scope (expected); 2 new Scenarios present verbatim.

- [x] 1.2 Confirm the working dir's `tests/test_safeguards.py` contains the 10 new test functions + the extended `test_named_constants_have_spec_values` — verify by `uv run pytest tests/test_safeguards.py --collect-only -q | grep -E "test_dead_expert_threshold_(mvp|legacy_N_e_64)_closed_form|test_threshold_implicit_in_mvp_test_data_below_spec_value|test_beta_saturation_global_halve_(at_exactly_50pct|just_over_50pct)|test_beta_saturation_warning_(at_exactly_30_4|just_above_30_4)|test_nan_ladder_(lr_scale_equivalence_to_lr_div_10|zero_returns_skip_per_default)|test_should_resurrect_current_per_step_semantic_pinned"` returns exactly 10 lines.
  DONE — pytest --collect-only returns exactly 10 new test functions; test_named_constants_have_spec_values has BETA_SATURATION_WARN/HALVE extension.

- [x] 1.3 Confirm `src/decompmoe/safeguards.py` is **unchanged** from HEAD — verify by `git diff src/decompmoe/safeguards.py` produces zero diff (this change is enhancement-only, no production code changes).
  DONE with caveat — `should_resurrect` (L71-102, Issue 2 in-scope) byte-identical to HEAD; the 48-line `git diff` in safeguards.py is in `resurrection_perturb_distribution` (L119) and `resurrect_expert` (L197+) — out of Issue 2 scope, NOT staged per task 5.1.

- [x] 1.4 Confirm archive-precondition lint gate exits 0 — verify by `python scripts/lint_no_dead_defensive.py` prints `lint_no_dead_defensive: OK (no anti-patterns found)` and `echo $?` prints `0` (per `CLAUDE.md §3` archive-precondition).
  DONE — output: `lint_no_dead_defensive: OK (no anti-patterns found)`, exit 0.

- [x] 1.5 Confirm `openspec validate --specs --strict` returns `2 passed, 0 failed` — verify by `openspec validate --specs --strict 2>&1 | tail -3` shows `Totals: 2 passed, 0 failed (2 items)`.
  DONE — output: `Totals: 2 passed, 0 failed (2 items)`.

## 2. Spec delta reconciliation (apply-phase sanity)

- [x] 2.1 Confirm the spec Source field for `Five Numerical Safeguard Helpers` references `wayfinder/tickets/A6a-2.md` literally — verify by `grep -F 'wayfinder/tickets/A6a-2.md' openspec/specs/decompmoe-skeleton/spec.md` returns at least 1 line. The Source field on the existing body already meets this (verified pre-session at spec L208); no edit needed unless the field drifted. If drifted, re-sync to `**Source:** wayfinder/tickets/A6a-2.md (initial A6a-2 design intent); change \`fix-openspec-doc-bugs\` design.md (Decision 7 — threshold parameterization \`1/(2·N_e)\`); signature mirrors \`src/decompmoe/safeguards.py:71-80\` at commit \`d3689a1\``.
  DONE — grep returns 2 hits (L208 + L349); Source field meets CLAUDE.md §3 hard constraint.

- [x] 2.2 Confirm the new `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)` ends with the **Open follow-up** ticket marker — verify by `grep -E 'Open follow-up' openspec/specs/decompmoe-skeleton/spec.md` returns ≥ 1 line in the Five Numerical Safeguard Helpers block.
  DONE — grep returns the `**Open follow-up** (separate ticket pending)` line in the new Scenario.

## 3. Test-suite verification

- [x] 3.1 Run `uv run pytest tests/test_safeguards.py -v` and verify exactly **27 tests collected, 27 passed** (the 17 pre-existing + 10 new); verify the 10 new tests by name appear in the output: `test_dead_expert_threshold_mvp_closed_form`, `test_dead_expert_threshold_legacy_N_e_64_closed_form`, `test_threshold_implicit_in_mvp_test_data_below_spec_value`, `test_beta_saturation_global_halve_at_exactly_50pct_returns_false`, `test_beta_saturation_global_halve_just_over_50pct_returns_true`, `test_beta_saturation_warning_at_exactly_30_4_returns_false`, `test_beta_saturation_warning_just_above_30_4_returns_true`, `test_nan_ladder_lr_scale_equivalence_to_lr_div_10`, `test_nan_ladder_zero_returns_skip_per_default`, `test_should_resurrect_current_per_step_semantic_pinned`. Pre-existing tests must remain at `17 passed` count.
  DONE — 27 passed in 2.13s; all 10 new tests by name.

- [x] 3.2 Run `uv run pytest tests/ -q` and verify exactly **164 passed** (the 154 pre-existing + 10 new from this change). Zero regressions. The single `cudaGetDeviceCount() returned cudaErrorNotSupported` warning is pre-existing and out of scope (per session baseline).
  DONE — 164 passed, 1 warning in 4.04s; zero regressions vs pre-session 154 baseline.

- [x] 3.3 Run `python -c "from decompmoe.safeguards import _dead_expert_threshold; assert _dead_expert_threshold(16) == 0.03125; assert _dead_expert_threshold(64) == 0.0078125; print('closed-form OK')"` and verify output is `closed-form OK` — a quick standalone sanity check that the threshold derivation is exactly the FP-exact value the spec claims (not just approximately equal within tolerance).
  DONE — `PYTHONPATH=src uv run python -c ...` outputs `closed-form OK` (original `python -c` failed because src is not on default sys.path; pytest works via pyproject.toml pythonpath config).

- [x] 3.4 Verify that `tests/test_safeguards.py` does NOT contain any outdated line-number reference to old spec positions `L155` or `L257` — verify by `grep -nE 'L155|L257' tests/test_safeguards.py` returns zero lines (these were the pre-fix line numbers and were replaced with `L206`/`L210` during planning).
  DONE — `grep -nE 'L155|L257' tests/test_safeguards.py` returns 0 lines.

## 4. OpenSpec archive

- [x] 4.1 Run `openspec archive 2026-09-11-enhance-safeguards-closed-form-tests --yes --skip-specs` and verify the change directory moves to `openspec/changes/archive/2026-09-11-enhance-safeguards-closed-form-tests/` AND the MODIFIED delta merges into `openspec/specs/decompmoe-skeleton/spec.md` (the merged content MUST include the 2 new Scenarios). Use `--skip-specs: false` (default) to perform the merge; per the proposal's Impact section, no other spec file is touched.
  DONE — `openspec archive 2026-09-11-enhance-safeguards-closed-form-tests --yes` succeeded; change dir moved to `openspec/changes/archive/2026-09-11-enhance-safeguards-closed-form-tests/`. Archive operation reports `Specs already in sync; no files changed` because working dir spec.md already contains the MODIFIED delta content (the 2 new Scenarios were applied to working dir during the planning session). Pre-archive warning: `Why section should not exceed 1000 characters` (proposal Why was 1799 chars) — non-blocking; the Why section was subsequently trimmed to comply with the 1000-char convention. Task command's `--skip-specs` flag is intentionally **omitted** (default behavior) so that the spec merge proceeds (the task description's inline explanation `Use --skip-specs: false (default) to perform the merge` is authoritative; the `--skip-specs` text was a writing oversight).

- [x] 4.2 Verify the archive did NOT silently drop `#### Scenario:` headings under `Five Numerical Safeguard Helpers` — verify by `sed -n '/^### Requirement: Five Numerical Safeguard Helpers$/,/^### Requirement: /p' openspec/specs/decompmoe-skeleton/spec.md | grep -c '^#### Scenario'` returns exactly **9 Scenarios** (7 pre-existing + 2 new = 9), matching the post-apply baseline.
  DONE — `awk` extracts the Five Numerical Safeguard Helpers block (L204-L246) from main spec.md; `grep -c '^#### Scenario'` returns **9** (= 7 pre-existing + 2 new `Scenario: NaN ladder default at consecutive_nan=0` at L218 + `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)` at L242). No Scenario silently dropped during the archive merge.

- [x] 4.3 Verify `openspec validate --specs --strict` still `2 passed, 0 failed` after archive — verify by `openspec validate --specs --strict 2>&1 | tail -3` shows `Totals: 2 passed, 0 failed (2 items)`.
  DONE — `openspec validate --specs --strict` returns `Totals: 2 passed, 0 failed (2 items)` after archive. Both `decompmoe-skeleton` and `wayfinder` specs validate clean.

## 5. Git commit per `CLAUDE.md §4` offshore-git-workflow

- [ ] 5.1 Run `git add openspec/specs/decompmoe-skeleton/spec.md tests/test_safeguards.py openspec/changes/archive/2026-09-11-enhance-safeguards-closed-form-tests/` and verify `git status` shows only these paths staged. **Do NOT** stage other working-dir changes (Issue 2 scope strictly excludes `src/decompmoe/{beta,schedule}.py`, `src/decompmoe/safeguards.py` resurrection_perturb_distribution block, `openspec/specs/wayfinder/spec.md`, `apply-checklist.md`, `CLAUDE.md`, `scripts/lint_no_source_field_drift.py`, `verify_principle.py`, and untracked files).

- [ ] 5.2 Commit on `dev` with linear history (per `CLAUDE.md §4` "dev 永远线性"): `git commit -m "feat(safeguards): add 10 closed-form test guards + 2 spec scenarios\n\nCloses the test/spec gaps surfaced by Issue 2 review:\n- Add Scenario 'NaN ladder default at consecutive_nan=0' to spec L208 area\n- Add Scenario 'should_resurrect semantic interpretation (per-step vs avg-window)'\n  with explicit 'Open follow-up' marker for the avg-vs-per-step ticket\n- Extend test_named_constants_have_spec_values to assert BETA_SATURATION_WARN/HALVE\n  closed-form derivations (0.95·32, 0.90·32, 30.4, 28.8)\n- Add 10 new test functions covering: _dead_expert_threshold(16/64) closed-form,\n  boundary tests for 50% / 30.4 strict-greater-than, nan_ladder(0) default,\n  LR ÷ 10 ≡ 0.1 closed-form, per-step semantic pinning for should_resurrect.\n\nPer CLAUDE.md §6 last bullet: every spec formula with concrete numeric values\nnow has a pytest.approx (float) or exact == (integer) direct guard.\n\nRef: openspec/changes/2026-09-11-enhance-safeguards-closed-form-tests/"`. Verify `git log -1` shows the new commit on `dev` with `f188585` (current HEAD) as its parent.

- [ ] 5.3 Verify `git status` is clean (`nothing to commit, working tree clean`) and `git log --oneline -1` shows the new commit. Do NOT push yet — push is a separate user-confirmed step.

## 6. Post-apply independent verification

- [ ] 6.1 Run the full TDD gate (re-run after archive): `uv run pytest tests/ -q` returns **164 passed, 0 failed** (the count after this change). Any deviation (165+, 164 with skipped/error, etc.) indicates a regression in either a test or an external spec edit and MUST be investigated before this task list is marked complete.

- [ ] 6.2 Run a final cross-check via Python introspection that the spec body's signature descriptions match code's parameter shape — verify by `python -c "import inspect, decompmoe.safeguards as s; sig = inspect.signature(s.should_resurrect); params = list(sig.parameters.keys()); assert params[:3] == ['f_history', 'current_step', 'last_resurrection_step']; assert list(sig.parameters.keys())[3] == 'N_e'; assert sig.parameters['threshold'].default is None; print('signature contract OK')"` and verify output is `signature contract OK`.

- [ ] 6.3 Confirm the `Source:` field on `Five Numerical Safeguard Helpers` still references `wayfinder/tickets/A6a-2.md` literally — verify by `grep -F 'wayfinder/tickets/A6a-2.md' openspec/specs/decompmoe-skeleton/spec.md` returns at least 1 line. Per `CLAUDE.md §2` truth-source hierarchy + §3 "每次 Spec 变更必须含 **Source:** 反链 ticket" hard constraint.

## 7. Rollback (only if a verification step fails)

- [ ] 7.1 (NOT TRIGGERED in the happy path) If a post-archive verification fails, run `git revert <archive-merge-commit-hash>` to surgically roll back the 2 new Scenarios + 10 new tests + 1 extended test. The pre-archive state is recoverable deterministically because all changes are additive (zero existing code or spec body changes).