## Why

After the math direction correction (`2026-09-12-fix-spec-resurrection-math-direction-2026-09-12`) and the Counterexample B `⊊` misuse fix (`fix(test): 修正 Counterexample B 注释的 ⊊ 误用`, commit `0dc7ded`), the `should_resurrect` math derivation block in `decompmoe-skeleton` spec L266-286 is **mathematically** closed-form correct and all `pytest.approx` assertions in `tests/test_safeguards.py::test_should_resurrect_per_step_is_strict_subset_of_avg_window_for_monotonic_history` PASS (5 sub-assertions including universal-direction positive example). However a scope-bounded audit (2026-09-16) revealed six residual drift issues in the change's own scope:

- **A1**: `tests/test_safeguards.py:679-680` guard-test docstring cites `Per wayfinder L249` — but the current wayfinder spec uses `<a id="req-13">` (`wayfinder Req 13`) anchor scheme; L249 is the legacy pre-anchor line number.
- **A2**: `tests/test_safeguards.py:682` guard-test docstring cites `current code (L97-L101)` — but `def should_resurrect` lives at `src/decompmoe/safeguards.py:71` (signature spans L71-80).
- **A3**: `tests/test_safeguards.py:707` guard-test failure-message string contains `update spec L206, wayfinder L249` — both halves stale (spec L266-286 / wayfinder anchor `req-13`).
- **A4**: `tests/test_safeguards.py:726` new-test docstring cites `current code at src/decompmoe/safeguards.py:97-101` — same drift as A2.
- **A5**: `tests/test_safeguards.py:767` Sub-assertion-5 docstring asserts `H = [0.03125]*200` but the actual code at L907 builds `H_boundary` with `range(250)` — a self-inconsistency introduced by commit `e9fc2b9` itself.
- **B1**: spec scenario L266-286 body gives closed-form arithmetic for `0.009925` (Counterexample A) and `0.049775` (Counterexample B), but the universal-direction positive example arithmetic `0.001145` (Sub-assertion 4, added by `e9fc2b9`) appears only in `tests/test_safeguards.py` and not in the spec body. This is a one-way coverage gap: spec ↔ test triple consistency is one-directional (spec → test for two examples; test → spec closure is missing for the third).

Total: 5 docstring / line-ref fixes + 1 self-inconsistency code length fix + 1 spec closed-form addition. Zero production-code behavior change. The drift does **not** affect any `assert` correctness (both tests pass), but it degrades auditability and makes every "follow the cross-reference" walk-thru land in the wrong place.

## What Changes

- **Modify** `decompmoe-skeleton` spec, `Five Numerical Safeguard Helpers` Requirement, `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)` (L266-286 in main spec): insert a new bullet **"Universal-direction positive worked example (algebra proof's positive complement to Counterexample A)"** between the existing "Both readings agree on constant history" paragraph (L282) and the "Notational pin on `f_i^avg`" paragraph (L284). The new bullet closes the spec ↔ test closure gap for Sub-assertion 4 by spelling out the closed-form arithmetic `(199·0.001 + 1·0.030) / 200 = 0.001145` together with its TRIGGER verdict. No Requirement body change; no other Scenario change; no Source-field change.
- **Modify** `tests/test_safeguards.py` `test_should_resurrect_current_per_step_semantic_pinned` (L676-716) docstring only — 3 string edits:
  - L679-680: `Per wayfinder L249: ... 200 consecutive steps` → `Per wayfinder Req 13 (anchor #req-13): ... 200 consecutive steps`
  - L682: `implements (a): every snapshot in the last consec steps ... (L97-L101)` → `(L71-80)` to match `should_resurrect` actual signature location
  - L707 (in failure-message f-string): `spec L206, wayfinder L249, and this test consistently` → `spec L266-286, wayfinder Req 13 (anchor #req-13), and this test consistently`
- **Modify** `tests/test_safeguards.py` `test_should_resurrect_per_step_is_strict_subset_of_avg_window_for_monotonic_history` (L719+) docstring + 1 code line:
  - L726 docstring: `current code at src/decompmoe/safeguards.py:97-101` → `current code at src/decompmoe/safeguards.py:71-80`
  - L907 code: `H_boundary = [[threshold] * N_e for _ in range(250)]` → `range(200)` to match docstring L767 + canonical `consec = DEAD_EXPERT_CONSEC_STEPS = 200` (the test outcome is invariant under window length because every snapshot is exactly at threshold, but code/docstring inconsistency damages reader trust)
- **Re-no-op** every `assert` statement in both tests (no behavior change; `2 passed, 28 deselected` must remain after archive).

No `**Source:**` clause introduced at Scenario level (per `2026-09-12-add-should-resurrect-per-step-math-derivation design.md` Decision 1 governance precedent — Scenario-level Source replicates the wayfinder drift pattern `scripts/lint_no_source_field_drift.py` was written to prevent; the parent Requirement L228's existing Source field already carries `src/decompmoe/safeguards.py:71-80` which is now correctly aligned).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `decompmoe-skeleton`: extend `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)` (L266-286) by inserting one additional worked-example bullet carrying the closed-form arithmetic for Sub-assertion 4 (`0.001145`). The Requirement body is unchanged; no other Scenario touched; the existing `f_i^avg` notational pin (L284) is preserved verbatim.

## Impact

- **Spec artifacts**: `openspec/specs/decompmoe-skeleton/spec.md` (one Scenario extended by one bullet; the bullet corresponds to Sub-assertion 4 in `tests/test_safeguards.py`)
- **Test artifacts**: `tests/test_safeguards.py` — 5 docstring / error-message edits + 1 code-line length fix (`range(250) → 200`)
- **Production code**: zero changes to `src/decompmoe/safeguards.py` (canonical reference; this change documents its semantics, does not alter it)
- **Wayfinder spec**: NOT modified (the spec scenario already cross-references `wayfinder Req 13` consistently)
- **Lint / archive preconditions**: must satisfy CLAUDE.md §3 archive gate — `python scripts/lint_no_dead_defensive.py` exit=0 + `python scripts/lint_no_source_field_drift.py` exit=0; no new Source fields introduced
- **Test outcome parity**: `uv run pytest tests/test_safeguards.py -k "per_step" -v` must remain `2 passed, 28 deselected` (both edits are textual or length-invariant; the boundary assertion at L925-928 is invariant under window length because every snapshot has every `f_i == threshold` exactly)
