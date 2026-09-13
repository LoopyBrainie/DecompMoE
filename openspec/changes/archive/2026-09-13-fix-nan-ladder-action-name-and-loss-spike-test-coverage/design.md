## Context

See `proposal.md - Why` for motivation. The change operates on the `nan_ladder` action string (`halve_lr` → `div_lr_10`) + TDD math constraint coverage (`loss_spike_defense` boundary + closure-form guard).

## Goals / Non-Goals

**Goals:**
- Rename `nan_ladder(c=3)` action string from `halve_lr` to `div_lr_10` to align with the actual `lr_scale = 0.1` value (= LR ÷ 10 per wayfinder L249).
- Add explicit `pytest.approx(2.5, abs=1e-12)` closure-form guard in `test_loss_spike_defense_phase3plus` so the magic number `2.5` in the test input is anchored to `LOSS_SPIKE_RATIO` spec constant.
- Add new test `test_loss_spike_defense_at_ratio_boundary_returns_false` to pin spec's strict `>` (not `>=`) at `L_task == ratio · L_task_ema` boundary.

**Non-Goals:**
- Renaming `beta_saturation_global_halve` (which DOES halve LR to LR × 0.5; name is correct, leave alone).
- Changing the `lr_scale = 0.1` value (numeric value is correct per wayfinder L249).
- Touching wayfinder spec (already says "LR ÷ 10").
- Touching `loss_spike_defense` signature (already correct: `phase: int, ratio: float = LOSS_SPIKE_RATIO`).

## Decisions

### Decision 1: Action name `div_lr_10` over alternatives

**Alternatives considered**:
- `div_lr_10` (chosen) — explicit ÷ 10, mirrors wayfinder L249 wording "LR ÷ 10"
- `divide_lr_by_10` (rejected) — too verbose for a Literal type member
- `lr_x_0_1` (rejected) — leaky abstraction (couples name to FP literal value)
- `lr_scale_10pct` (rejected) — ambiguous (could be interpreted as "10% remaining" or "10% of original")

### Decision 2: Closure-form anchor via `LOSS_SPIKE_RATIO` (not hard-coded `2.5`)

The test input `2.5` is now anchored to `safeguards.LOSS_SPIKE_RATIO` via `pytest.approx(LOSS_SPIKE_RATIO, abs=1e-12)` first, then `LOSS_SPIKE_RATIO` is also pinned to spec closed-form `2.5` via the existing `test_named_constants_have_spec_values`. This double-anchor ensures: (a) test data follows spec, (b) test result (`5.0 > ratio * 1.0`) is computed from spec constant, not magic number. Single point of failure removed.

### Decision 3: Boundary test uses equality at the ratio boundary

`L_task = 2.5` and `L_task_ema = 1.0` with `ratio = 2.5` (default `LOSS_SPIKE_RATIO`) ⇒ `ratio * L_task_ema = 2.5` ⇒ `L_task == ratio * L_task_ema` ⇒ strict `>` returns False. This pins the spec's `>` (not `>=`) semantics at the equality boundary.

## Risks / Trade-offs

- **[Risk] External caller pattern-matches on `"halve_lr"`** → breaks at import / runtime.
  - **Mitigation**: grep `openspec/` confirms zero external callers pattern-match the literal. Test side updates both assertions. The only references are inside `safeguards.py` (definition + return) and `tests/test_safeguards.py` (assertions).
  - **Long-term mitigation**: `NaNAction` Literal type membership is now self-documenting (`div_lr_10`); callers who import the type get compile-time help.

- **[Risk] Docstring L8 + return-tuple L62 both rename must stay in sync** → drift if one is forgotten.
  - **Mitigation**: Both edits are part of the same diff, reviewed together. `grep 'halve_lr' openspec/` post-apply returns 0 matches (verification command in tasks.md 1.1).

## Migration Plan

Single-commit migration. Steps:

1. Apply 4 edits to `src/decompmoe/safeguards.py` (module docstring L8, `NaNAction` Literal L53, return tuple L62, plus optional module-level comment cleanup).
2. Apply 2 edits to `tests/test_safeguards.py` (`test_nan_ladder` exact-tuple, `test_nan_ladder_lr_scale_equivalence_to_lr_div_10` action string).
3. Add 1 line closure-form guard + 1 new test function to `tests/test_safeguards.py`.
4. Run `python -m pytest tests/test_safeguards.py -v` — must show 30/30 PASSED (was 29/29; +1 from new boundary test).
5. Run `python scripts/lint_no_source_field_drift.py` and `python scripts/lint_no_dead_defensive.py` — both exit=0.
6. Apply spec delta via `openspec archive`.

**Rollback**: revert single commit. API surface (`NaNAction` Literal members) returns to pre-change state.

## Open Questions

(none — all design choices are deterministic given the existing wayfinder init decision and the spec/code/test ecosystem already in place)
