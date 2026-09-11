# Proposal: fix-safeguards-should-resurrect-signature-drift

## Why

The skeleton spec's `Five Numerical Safeguard Helpers` Requirement body (`openspec/specs/decompmoe-skeleton/spec.md` L257) has been out of sync with the actual implementation at `src/decompmoe/safeguards.py:23-228` since the skeleton's initial commit `0d87e32` (2026-08-21). Code-side signature refactors at `d3689a1` (2026-08-22, `N_e` promoted to mandatory keyword-only, `threshold` default switched to `None` and derived from `N_e`) and at the subsequent safe-API cleanups were never propagated to the spec. The skeleton spec also has internal contradictions / typos in items (1), (4), (5):

- Item (1) `clip_global_grad_norm_(params, max_norm=1.0) -> Tensor` — but code returns `float` (not `Tensor`).
- Item (4) `beta_saturation_warning(β_per_expert, *, β_max=32) -> bool` — but code has no `β_max` parameter; the warning threshold is sourced from `BETA_MAX` via `BETA_SATURATION_WARN`.
- Item (5) `loss_spike_defense(L_task, L_task_ema, phase, *, ratio=2.5) -> bool` — but code's `ratio` is `POSITIONAL_OR_KEYWORD` (no `*` separator). The "signalling `LR × 0.8`" wording is ambiguous about caller-vs-function responsibility.

**Scope-down history** (2026-09-09): the original change scope included three additional MODIFIED Requirements that were removed before archive due to cross-session conflict:

1. **`decompmoe-skeleton::Centroid Four-Phase Lifecycle Driver` (original L155)**: another session's parallel cleanup (Task 2.3) deleted this Requirement header from the main spec before this change could archive; the surviving `### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension` (which subsumes the lifecycle driver) was independently corrected by that same parallel change. Keeping this MODIFIED block would have caused `openspec archive` to reject with `header ... not found`.
2. **`wayfinder::Resurrection Perturbation Per-Expert Contract` (L577)** and **`wayfinder::Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper` (L642)**: another session's parallel fix (Tasks 3.1 / 3.2) had already updated the L577/L642 Requirement bodies to the correct 4-arg form (`f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None`). This change would have re-applied an already-applied fix.

The remaining scope of this change is therefore the single Requirement **`Five Numerical Safeguard Helpers`** in `decompmoe-skeleton`, where the post-`d3689a1` signature alignment is still missing and not covered by any other open change.

## What Changes

- `decompmoe-skeleton` requirement `Five Numerical Safeguard Helpers` (originally L257, now at L201 in the post-cleanup main spec): align all five helper signature descriptions to the code-side reality at `src/decompmoe/safeguards.py:23-228`:
  - (1) `clip_global_grad_norm_(params, max_norm: float = 1.0) -> float` — code-review N6 fix
  - (2) `nan_ladder(consecutive_nan) -> tuple[str, float, bool]` — preserved (no drift)
  - (3) `should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]`; threshold=None dispatches via `_dead_expert_threshold(N_e) = 1/(2·N_e)` — code-review C1 + M3 fixes
  - (4) `beta_saturation_warning(β_per_expert: Tensor) -> bool`; threshold sourced from `BETA_SATURATION_WARN = 0.95 · BETA_MAX` constant (no `β_max` parameter) — code-review N7 fix
  - (5) `loss_spike_defense(L_task: float, L_task_ema: float, phase: int, ratio: float = LOSS_SPIKE_RATIO) -> bool`; function ONLY returns the boolean — caller responsibility to apply `LR × LOSS_SPIKE_LR_SCALE = LR × 0.8` — code-review N8 + L2 fixes
- All 7 `#### Scenario:` headings under `Five Numerical Safeguard Helpers` are preserved verbatim to avoid the fix-openspec-doc-bugs §2.6 archive rejection (block-replacement of a Requirement body silently removes Scenario titles).
- Source citation updated to include `wayfinder/tickets/A6a-2.md` (initial design intent) alongside the existing `change fix-openspec-doc-bugs design.md (Decision 7)` — code-review L1 fix.
- New behavioral assertions in `tests/test_safeguards.py`:
  - `test_no_other_module_defines_should_resurrect` (code-review M2 fix) — uses `pkgutil.iter_modules(decompmoe.__path__)` (code-review N4 fix) to enumerate all 13 submodules and assert none defines a `should_resurrect` attribute.
  - `test_named_constants_have_spec_values` (code-review N5 fix) — guards the 4 spec-anchored numerical claims (`DEAD_EXPERT_CONSEC_STEPS = 200`, `RESURRECTION_RATE_LIMIT_STEPS = 1000`, `LOSS_SPIKE_RATIO = 2.5`, `LOSS_SPIKE_LR_SCALE = 0.8`) with bare `==` for integers and `pytest.approx(value, abs=1e-12)` for floats per CLAUDE.md §6 last bullet.
- No code changes.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `decompmoe-skeleton`: align the signature description of all five helpers in the `Five Numerical Safeguard Helpers` Requirement to the code-side reality at `src/decompmoe/safeguards.py:23-228` (commits `d3689a1` and related). The five drifts fixed are: `clip_global_grad_norm_` return-type (`Tensor` → `float`), `should_resurrect` signature (`N_e` keyword-only + `threshold=None` dispatch + named-constant defaults), `beta_saturation_warning` removal of `β_max` parameter, `loss_spike_defense` removal of `*` keyword-only separator + clarification of caller-responsibility for `LR × 0.8`. Constants referenced by identifier rather than literal value to keep spec in lock-step with `Final[int]` / `Final[float]` constants if retuned.

## Impact

- `openspec/specs/decompmoe-skeleton/spec.md`: 1 surgical Requirement-body edit (signature description rewrite for 5 helpers + named-constant references + Source citation update); no Scenario heading changes; no new Requirements added.
- `src/`: 0 changes.
- `tests/test_safeguards.py`: +2 new tests (`test_no_other_module_defines_should_resurrect` per code-review M2/N4, `test_named_constants_have_spec_values` per code-review N5); no existing test modified.
- `wayfinder/tickets/`: 0 changes (per CLAUDE.md §8 裁决 — tickets are reference-only, not authoritative).
- 9 new verify tasks added to `tasks.md` (signature introspection assertions; new pytest filter `-k "resurrect"` per code-review C2; sed-based per-Requirement scenario count per code-review N3; new constant-value assertions per code-review N5).
- **Cross-session coordination note**: 3 of the originally targeted Requirements (`Centroid Four-Phase Lifecycle Driver` in `decompmoe-skeleton`; `Resurrection Perturbation Per-Expert Contract` + `Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper` in `wayfinder`) were intentionally removed from scope because a parallel cleanup change by another session had already addressed them (Task 2.3 + 3.1 + 3.2). This change does NOT re-apply those fixes.
