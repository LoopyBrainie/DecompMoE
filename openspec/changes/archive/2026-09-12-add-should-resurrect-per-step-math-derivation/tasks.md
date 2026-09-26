# Tasks: add-should-resurrect-per-step-math-derivation

## 1. Verify planning artifacts match audit conclusions

- [x] 1.1 Verify `proposal.md` correctly cites S1.a / S1.b / S1.c findings and lists Modified Capability `decompmoe-skeleton` with the per-step Scenario extension scope; verify by `cat openspec/changes/add-should-resurrect-per-step-math-derivation/proposal.md` and grep `S1\.[abc]`.
- [x] 1.2 Verify `specs/decompmoe-skeleton/spec.md` preserves all 7 existing `#### Scenario:` headings under `Five Numerical Safeguard Helpers` verbatim and only the `should_resurrect semantic interpretation (per-step vs avg-window)` Scenario's THEN clause is extended with the math derivation block + notational pin; verify by `grep -c '^#### Scenario' openspec/changes/add-should-resurrect-per-step-math-derivation/specs/decompmoe-skeleton/spec.md` returning 7.
- [x] 1.3 Verify `design.md` Decision 1 carries the full math derivation (formal definitions + 2 counterexamples + constant-history agreement proof + notational pin) and Decision 2 specifies the test design; verify by reading Decision 1 and Decision 2 sections.

## 2. Implement the new test (no production code touched)

- [x] 2.1 Add `test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history` to `tests/test_safeguards.py` immediately after the existing `test_should_resurrect_current_per_step_semantic_pinned` test; verify by `grep -n "test_should_resurrect_per_step_is_strict_superset" tests/test_safeguards.py` returning a single line number.
- [x] 2.2 Implement the three sub-assertions in the new test: (a) constant-history agreement (`H = [0.005] * 200`), (b) Counterexample A divergence (`H = [0.005] * 199 + [0.99]`, assert `pytest.approx(0.009925, abs=1e-6)` for avg-window mean and assert `should_resurrect` does NOT flag for per-step), (c) Counterexample B divergence (`H = [0.05] * 199 + [0.005]`, assert `pytest.approx(0.049775, abs=1e-6)` for avg-window mean and assert `should_resurrect` does NOT flag for per-step); verify by running the test in isolation: `uv run pytest tests/test_safeguards.py::test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history -v` exits 0.
- [x] 2.3 Add a docstring to the new test explaining WHY each counterexample is constructed (per `2026-09-11-enhance-safeguards-closed-form-tests design.md` Decision 3 *Alternatives considered*); verify by reading the test source and confirming the docstring opens with "Per-step reading is the canonical interpretation of wayfinder L249's `f_i^avg < 1/(2·N_e) for 200 consecutive steps` trigger...".

## 3. Lint gate (per CLAUDE.md §3 archive precondition)

- [x] 3.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0; if exit≠0, fix the lint violation or escalate before proceeding (per `2026-09-10-fix-safeguards-should-resurrect-signature-drift design.md` Decision R4 mitigation).

## 4. Pre-archive regression gate

- [x] 4.1 Run `uv run pytest tests/test_safeguards.py -k "per_step" -v` and verify 100% PASS (2 tests: existing `test_should_resurrect_current_per_step_semantic_pinned` + new `test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history`); record the PASS count for the post-archive independent verification (§5.3).
- [x] 4.2 Run the full test suite `uv run pytest tests/test_safeguards.py -v` and verify 100% PASS (≥18 tests: 17 existing from `2026-09-11-enhance-safeguards-closed-form-tests` + 1 new); if any test fails, fix the failure mode without altering test assertions (per `2026-09-10-fix-safeguards-should-resurrect-signature-drift design.md` R1 mitigation).

## 5. Post-archive independent verification (per CLAUDE.md §3 "Post-archive 独立复核" 强制项)

- [x] 5.1 Verify `openspec validate --strict` accepts the change directory before archive; if validation fails, fix the structural issue (header mismatch, missing `WHEN`/`THEN`, etc.) and re-run.
- [x] 5.2 After archive, re-run `grep -E "deriv|proof|mathematically" openspec/specs/decompmoe-skeleton/spec.md` against the merged main spec; verify the `Five Numerical Safeguard Helpers` block (L206–L248) now returns at least one hit (the new math derivation mentions "mathematically distinct" or equivalent) — this closes the audit S1.b finding.
- [x] 5.3 After archive, re-run `uv run pytest tests/test_safeguards.py -k "per_step" -v` against the merged main test suite; verify 100% PASS (audit S1.c finding closed: spec + design + test combination now establishes mathematical basis for per-step, not merely policy + code-first).

## 6. Archive

- [x] 6.1 Run `/opsx:archive` (or `openspec archive add-should-resurrect-per-step-math-derivation` if CLI invocation is preferred); verify by `ls openspec/changes/archive/2026-09-XX-add-should-resurrect-per-step-math-derivation/` (where XX is the archive date).
- [x] 6.2 Verify the merge commit on `dev` carries the new Scenario verbatim (no character drift); verify by `git log -p dev -- openspec/specs/decompmoe-skeleton/spec.md | grep -A 3 "should_resurrect semantic interpretation"` showing the new math derivation block.

## 7. Post-archive self-audit (2026-09-12, per CLAUDE.md §3 "Post-archive 独立复核" 强制项)

Independent review confirms the archive's binding criteria:
- [x] 7.1 **S1.b audit closed**: main spec `openspec/specs/decompmoe-skeleton/spec.md` now returns grep hits for `mathematically` (line 242 + 244 — "Two readings are mathematically distinct" in the per-step Scenario's math derivation block). Was 0 hits pre-change, now >=1 hit.
- [x] 7.2 **S1.c audit closed**: spec + design + new test (`test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history`) combination now establishes mathematical basis for per-step reading (formal definition + 2 worked counterexamples + 3 sub-assertions verifying `pytest.approx(0.009925, abs=1e-6)` and `pytest.approx(0.049775, abs=1e-6)` per spec's float-closed-form convention).
- [x] 7.3 **Source-field governance intact**: delta spec added NO `**Source:**` line (per Option 1 review fix); post-archive `lint_no_source_field_drift.py` exit=0 across 3 capability files.
- [x] 7.4 **Both lint gates pass**: `lint_no_dead_defensive.py` exit=0 + `lint_no_source_field_drift.py` exit=0 (the latter newly wired into archive gate by the previous `migrate-l678-source` change).
