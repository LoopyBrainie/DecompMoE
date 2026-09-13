## 1. Spec edit (decompmoe-skeleton)

- [ ] 1.1 Apply 2 textual replacements in `openspec/specs/decompmoe-skeleton/spec.md` body (L208 Literal type member + L219 tier entry within Scenario `NaN ladder default`): rename `"halve_lr"` → `"div_lr_10"` (2 occurrences total); verify by `grep -nE '"halve_lr"|halve_lr' openspec/specs/decompmoe-skeleton/spec.md` returning **zero matches** AND `grep -cE 'div_lr_10' openspec/specs/decompmoe-skeleton/spec.md` returning **2 matches** (L208 + L219).

## 2. Code edits (src/decompmoe/safeguards.py)

- [ ] 2.1 Apply 3 textual replacements in `src/decompmoe/safeguards.py`: (a) module docstring L8 `"3 → halve_lr"` → `"3 → div_lr_10"`, (b) `NaNAction = Literal["skip", "halve_lr", "halt"]` L53 → `Literal["skip", "div_lr_10", "halt"]`, (c) `return ("halve_lr", 0.1, False)` L62 → `return ("div_lr_10", 0.1, False)`; verify by `grep -nE 'halve_lr' src/decompmoe/safeguards.py` returning **zero matches** AND `grep -cE 'div_lr_10' src/decompmoe/safeguards.py` returning **3 matches** (docstring + Literal + return).

## 3. Test edits (tests/test_safeguards.py)

- [ ] 3.1 Update 2 existing assertions in `tests/test_safeguards.py`: (a) `test_nan_ladder` line ~143 `assert safeguards.nan_ladder(3) == ("halve_lr", 0.1, False)` → `("div_lr_10", 0.1, False)`; (b) `test_nan_ladder_lr_scale_equivalence_to_lr_div_10` line ~478 `assert action == "halve_lr"` → `assert action == "div_lr_10"`; verify by `grep -nE '"halve_lr"' tests/test_safeguards.py` returning **zero matches** AND `grep -cE '"div_lr_10"' tests/test_safeguards.py` returning **≥ 2 matches** (one per updated test).
- [ ] 3.2 Add explicit closure-form anchor in `tests/test_safeguards.py::test_loss_spike_defense_phase3plus` (Finding 2): insert before the existing 3 assertions a `pytest.approx(2.5, abs=1e-12)` closure check for `safeguards.LOSS_SPIKE_RATIO` so the magic number `2.5` used in the test is anchored to the spec constant; verify by reading the test source and confirming the closure line is present.
- [ ] 3.3 Add new test `test_loss_spike_defense_at_ratio_boundary_returns_false` to `tests/test_safeguards.py` (Finding 3): assert `safeguards.loss_spike_defense(L_task=2.5, L_task_ema=1.0, phase=3) is False` to pin the strict `>` (not `>=`) at the equality boundary `L_task == ratio · L_task_ema`; verify by counting test functions: `grep -c '^def test_' tests/test_safeguards.py` returning **30** (was 29).

## 4. Verification gates (pre-archive)

- [ ] 4.1 Run `python -m pytest tests/test_safeguards.py -v`; verify **30/30 tests PASSED** (29 existing + 1 new boundary test); verify specifically `test_nan_ladder` and `test_nan_ladder_lr_scale_equivalence_to_lr_div_10` and `test_loss_spike_defense_phase3plus` and `test_loss_spike_defense_at_ratio_boundary_returns_false` all PASS.
- [ ] 4.2 Run `python scripts/lint_no_source_field_drift.py`; verify `exit=0` AND stdout contains `lint_no_source_field_drift: OK`.
- [ ] 4.3 Run `python scripts/lint_no_dead_defensive.py`; verify `exit=0` AND stdout contains `lint_no_dead_defensive: OK`.
- [ ] 4.4 Run `grep -rnE '"halve_lr"|halve_lr' openspec/ src/ tests/`; verify **zero matches** post-rename (only `div_lr_10` remains).

## 5. Archive via OpenSpec workflow

- [ ] 5.1 Run `openspec archive --change 2026-09-13-fix-nan-ladder-action-name-and-loss-spike-test-coverage`; verify delta spec merges into `openspec/specs/decompmoe-skeleton/spec.md` (the `## MODIFIED Requirements` block overwrites the matching Requirement body in the main spec) and the change folder moves to `openspec/changes/archive/`.
- [ ] 5.2 Post-archive verification: re-run `python -m pytest tests/test_safeguards.py` (30/30 PASSED), `python scripts/lint_no_source_field_drift.py` (exit=0), `grep -rnE 'halve_lr' openspec/` (zero matches); verify archive folder contains the 4 artifacts (`proposal.md`, `design.md`, `tasks.md`, `specs/decompmoe-skeleton/spec.md`).
