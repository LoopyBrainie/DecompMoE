# Proposal: enhance-safeguards-closed-form-tests

## Why

The `Five Numerical Safeguard Helpers` Requirement (`decompmoe-skeleton` L204) has two open gaps surfaced by code review: (1) wayfinder L249's `f_i^avg < 1/(2·N_e) for 200 consecutive steps` is ambiguous between per-step and avg-window readings; the current code uses per-step but the spec body does not commit to either, so downstream callers cannot rely on the trigger for non-constant history. (2) Per `CLAUDE.md §6` last bullet ("every spec formula with concrete numeric values MUST have a `pytest.approx` or exact `==` direct guard"), the existing test file has 9 docstring references to `1/32` / `0.03125` but **zero** `assert` statements that pin `_dead_expert_threshold(16) = 1/(2·16) = 1/32 = 0.03125`; similarly `BETA_SATURATION_WARN = 30.4`, `BETA_SATURATION_HALVE = 28.8`, the `50%` boundary, the `30.4` strict-greater-than boundary, `nan_ladder(0)` default, and the `LR ÷ 10 ≡ 0.1` closed-form are not asserted. This change closes both gaps by adding 2 spec Scenarios + 10 new tests + 1 extended test.

## What Changes

- **`openspec/specs/decompmoe-skeleton/spec.md`** — append 2 new `#### Scenario:` blocks under the `Five Numerical Safeguard Helpers` Requirement body:
  - `Scenario: NaN ladder default at consecutive_nan=0 (no NaN observed)` — documents the spec-implicit default of `("skip", 1.0, False)` and the strict-greater-than ladder tiers for `c ∈ [1,2]`, `c ∈ [3,9]`, `c ≥ 10`.
  - `Scenario: should_resurrect semantic interpretation (per-step vs avg-window)` — pins the current per-step strict-less-than interpretation as canonical; explicitly notes the avg-window reading as **open follow-up** (separate ticket required) and references the new guard test `test_should_resurrect_current_per_step_semantic_pinned`.

- **`tests/test_safeguards.py`** — add 10 new test functions + extend 1 existing test:
  - `test_dead_expert_threshold_mvp_closed_form` — `_dead_expert_threshold(16) == 1/(2·16) ≈ 1/32 ≈ 0.03125` (closed-form + literal-evaluated, `abs=1e-12`).
  - `test_dead_expert_threshold_legacy_N_e_64_closed_form` — `_dead_expert_threshold(64) ≈ 1/128 ≈ 0.0078125`.
  - `test_threshold_implicit_in_mvp_test_data_below_spec_value` — pins the implicit mathematical premise `0.02 < threshold` (and the symmetric `0.05 > threshold`) used in `test_resurrection_threshold_mvp_value`.
  - `test_beta_saturation_global_halve_at_exactly_50pct_returns_false` — pins the strict-`>` boundary on wayfinder "more than 50%".
  - `test_beta_saturation_global_halve_just_over_50pct_returns_true` — companion case (9/16 > 28.8).
  - `test_beta_saturation_warning_at_exactly_30_4_returns_false` — pins the strict-`>` boundary on wayfinder `β_i > 30.4`.
  - `test_beta_saturation_warning_just_above_30_4_returns_true` — companion case (`β_i = 30.5`).
  - `test_nan_ladder_lr_scale_equivalence_to_lr_div_10` — closed-form `lr_scale × 10 ≈ 1.0` + `0.1 ≈ 1/10` (wayfinder "LR ÷ 10" wording).
  - `test_nan_ladder_zero_returns_skip_per_default` — pins `nan_ladder(0) → ("skip", 1.0, False)`.
  - `test_should_resurrect_current_per_step_semantic_pinned` — pins current per-step semantics with a non-constant history that would diverge under avg-window reading; documents the pending-ticket decision.
  - Extend `test_named_constants_have_spec_values` to also assert `BETA_SATURATION_WARN == 0.95 × 32` and `BETA_SATURATION_HALVE == 0.90 × 32` (closed-form) plus the MVP-evaluated literals `30.4` and `28.8`.

- **No code changes in `src/decompmoe/safeguards.py`** — the current implementation is correct under the chosen per-step interpretation; this change is test + spec only.

- **No code changes in `src/decompmoe/{beta,schedule,...}.py`** — out of scope.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `decompmoe-skeleton`: add 2 new `#### Scenario:` blocks under the `Five Numerical Safeguard Helpers` Requirement body (L204). No `### Requirement:` body changes — the existing body wording correctly describes the 5 helpers per the post-`d3689a1` code reality, and the new Scenarios are pure additions that pin interpretation defaults and mark a pending decision.

## Impact

- `openspec/specs/decompmoe-skeleton/spec.md`: +2 `#### Scenario:` blocks (~40 lines). No existing requirement body or scenario changed.
- `tests/test_safeguards.py`: +10 new tests + 1 test extended (+~250 net lines). No existing test modified except `test_named_constants_have_spec_values` (extended with 4 additional `assert` statements).
- `src/`: 0 changes.
- `wayfinder/tickets/`: 0 changes (per `CLAUDE.md` §8 裁决 — tickets are reference-only, not authoritative).
- `archive/2026-09-10-fix-safeguards-should-resurrect-signature-drift/`: 0 changes (historical record left intact; its `tasks.md` caveat about apply-stage is a separate concern, not addressed in this change).

**Cross-change coordination**: this change is **enhancement-only** — it does NOT re-apply the original Issue 2 fix from `archive/2026-09-10-fix-safeguards-should-resurrect-signature-drift/` (whose apply-stage to main tree was botched in commit `8b9fb72`). The original Issue 2 signature drift is independently already-correct in working dir (verified by `git diff openspec/specs/decompmoe-skeleton/spec.md` showing the new signature wording) and the working dir's `tests/test_safeguards.py` already contains the two original-issue tests (`test_no_other_module_defines_should_resurrect`, `test_named_constants_have_spec_values`). This change builds on that prior state — it does not retry or redo it.