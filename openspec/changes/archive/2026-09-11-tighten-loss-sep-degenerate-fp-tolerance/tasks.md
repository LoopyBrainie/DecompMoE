## 1. Code Change

- [x] 1.1 Edit `tests/test_loss.py` line 132: replace `assert parts.L_sep.item() == 0.0, (` with `assert parts.L_sep.item() == pytest.approx(0.0, abs=1e-12), (`; verify by re-reading the file post-edit and confirming the literal `0.0` is now wrapped in `pytest.approx(..., abs=1e-12)` with the same `abs=1e-12` tolerance as line 183.

## 2. Verification

- [x] 2.1 Run `uv run pytest tests/test_loss.py -v` and verify all tests in `tests/test_loss.py` pass (≥ 9 tests, including `test_lambda_zero_phase_1_2` for both `phase=1` and `phase=2` iterations, and `test_sep_formula_orthonormal_degenerate`); verify by exit code = 0 and zero `FAILED`/`ERROR` lines in stdout.

- [x] 2.2 Run `uv run pytest tests/ -v` and verify the full test suite passes; verify by exit code = 0 and zero `FAILED`/`ERROR` lines in stdout (proves the `abs=1e-12` tolerance does not regress any other test).

## 3. Archive Gate

- [x] 3.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit code = 0 (per `CLAUDE.md` §3 `/opsx:archive` pre-condition: lint gate must `exit=0` to avoid archived change leaving lint red; precedent: `db14222` fix for the `12f673d` vulnerability).

- [x] 3.2 Run `git status` and verify only `tests/test_loss.py` is modified (no production code in `src/decompmoe/` changed); verify by listing the modified files and confirming `src/decompmoe/loss.py` is absent.

- [x] 3.3 Run `git diff openspec/specs/decompmoe-skeleton/spec.md` post-archive and verify the Scenario `Lambda zero in phases 1 and 2` THEN 子句 is now "equals `0.0` within `abs=1e-12`" (matching the modified delta's wording); verify by grep matching `within `abs=1e-12`` on the modified scenario line.
