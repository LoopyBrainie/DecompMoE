# MODIFIED Requirements — decompmoe-skeleton

> **Delta scope**: align the signature description of all five helpers in the `Five Numerical Safeguard Helpers` Requirement to the code-side reality at `src/decompmoe/safeguards.py:23-228` (commit `d3689a1` and related). Specifically: (1) `clip_global_grad_norm_` return type corrected from `Tensor` to `float` (matches `float(pre_clip_norm.item())` at line 57); (3) `should_resurrect` signature parameterized by `N_e` keyword-only, threshold default `None` with prose explaining `_dead_expert_threshold(N_e) = 1/(2·N_e)` dispatch; (4) `beta_saturation_warning` has NO `β_max` parameter — threshold sourced from `BETA_MAX` constant via `BETA_SATURATION_WARN`; (5) `loss_spike_defense` `ratio` parameter is POSITIONAL_OR_KEYWORD, not keyword-only; constants referenced by identifier (`DEAD_EXPERT_CONSEC_STEPS`, `RESURRECTION_RATE_LIMIT_STEPS`, `LOSS_SPIKE_RATIO`, `LOSS_SPIKE_LR_SCALE`, `BETA_SATURATION_WARN`, `BETA_SATURATION_HALVE`) rather than by literal value.

> **Scope-down note** (2026-09-09): the original `## MODIFIED Requirements` block listed `Centroid Four-Phase Lifecycle Driver` (L155) as a second target. This block was REMOVED before archive because (a) a parallel cleanup change by another session (Task 2.3) deleted the original `### Requirement: Centroid Four-Phase Lifecycle Driver` header from the main spec; (b) the equivalent wording in the surviving `### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension` was already independently corrected by that same parallel change. Keeping the `Centroid Four-Phase Lifecycle Driver` MODIFIED block in this delta would have caused `OpenSpec archive` to reject the change with `header ... not found`. The 4 Scenarios under the deleted Requirement (`Phase-0 non-differentiable`, `Phase-1 EMA coefficient`, `Phase-4 re-projection`, `Phase-1 driver Active despite gradient Frozen`) are preserved in `Phase-4 SGD Step Extension` and are out of scope for this delta. The `should_resurrect` driver-call phrasing that was originally targeted at L155 is now addressed at L335 (`Phase-4 SGD Step Extension`) via the parallel change.

> All `#### Scenario:` headings under the surviving Requirement are preserved verbatim to avoid the fix-openspec-doc-bugs §2.6 archive rejection (block-replacement of a Requirement body silently removes Scenario titles).

## MODIFIED Requirements

### Requirement: Five Numerical Safeguard Helpers

The package SHALL provide five standalone helpers in `safeguards.py`: (1) `clip_global_grad_norm_(params, max_norm: float = 1.0) -> float` returning the pre-clip norm as a `float` (NOT `Tensor` — code-review N6 fix: `src/decompmoe/safeguards.py:54` returns `float(pre_clip_norm.item() ...)`); (2) `nan_ladder(consecutive_nan) -> tuple[str, float, bool]` returning `(action, lr_scale, halt)` where `action ∈ {"skip", "halve_lr", "halt"}` for counts `(1, 3, 10)` respectively; (3) `should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]`; when `threshold=None`, the implementation calls `_dead_expert_threshold(N_e) = 1/(2·N_e)` to derive the effective threshold (at MVP `N_e = 16`, this yields `1/32`); (4) `beta_saturation_warning(β_per_expert: Tensor) -> bool` returning `True` when any `β_i > BETA_SATURATION_WARN = 30.4` (= `0.95 · BETA_MAX = 0.95 · 32`) — there is NO `β_max` parameter (code-review N7 fix: `src/decompmoe/safeguards.py:211` signature has no `β_max`; the warning threshold is sourced from the module-level `BETA_MAX` constant via `BETA_SATURATION_WARN: Final[float] = 0.95 * BETA_MAX`); (5) `loss_spike_defense(L_task: float, L_task_ema: float, phase: int, ratio: float = LOSS_SPIKE_RATIO) -> bool` returning `True` when `phase ≥ 3 and L_task > ratio · L_task_ema` — there is NO `*` keyword-only separator before `ratio` (code-review N8 fix: `src/decompmoe/safeguards.py:222` defines `ratio: float = LOSS_SPIKE_RATIO` as POSITIONAL_OR_KEYWORD); the function ONLY returns the boolean — the LR-scaling action (`LR × LOSS_SPIKE_LR_SCALE = LR × 0.8`) is the CALLER's responsibility (the function emits a "should scale" signal, not the scaling itself). The dead-expert threshold `1/(2·N_e)` replaces the previous hardcoded `1/128` (which was the `N_e=64` instantiation of the same `1/(2·N_e)` rule); at MVP `N_e = 16` this evaluates to `1/32`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200`, `RESURRECTION_RATE_LIMIT_STEPS = 1000`, `LOSS_SPIKE_RATIO = 2.5`, `LOSS_SPIKE_LR_SCALE = 0.8`, `BETA_SATURATION_WARN = 30.4`, `BETA_SATURATION_HALVE = 28.8` are `Final[int]` / `Final[float]` module-level constants (see `src/decompmoe/safeguards.py:23-41`); the spec references the constant identifiers rather than literal values. The standard step order SHALL be: `Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i)` (asserted via documented ordering constant `STEP_ORDER`).

**Source:** wayfinder/tickets/A6a-2.md (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `src/decompmoe/safeguards.py:71-80` at commit `d3689a1`.

#### Scenario: Global clip threshold
- **WHEN** `clip_global_grad_norm_(params, max_norm=1.0)` is called with `‖g‖₂ > 1.0`
- **THEN** all gradients are scaled to `‖g‖₂ ≤ 1.0`

#### Scenario: NaN escalation ladder
- **WHEN** `nan_ladder(c)` is called for `c ∈ {1, 3, 10}`
- **THEN** the returned tuple is `("skip", 1.0, False)` / `("halve_lr", 0.1, False)` / `("halt", 1.0, True)` respectively

#### Scenario: Resurrection rate-limited
- **WHEN** two dead-expert events occur within the same 1000-step window
- **THEN** only one resurrection is emitted; the second is deferred

#### Scenario: Beta saturation warning threshold
- **WHEN** any single `β_i > 30.4`
- **THEN** `beta_saturation_warning` returns `True` (= 95% of `β_max = 32`)

#### Scenario: Beta saturation global halve threshold
- **WHEN** more than 50% of `β_i > 28.8` (= 90% of `β_max = 32`)
- **THEN** the global halving predicate returns `True`

#### Scenario: Loss spike defense gating
- **WHEN** `phase < 3` (i.e. phase ∈ {0, 1, 2})
- **THEN** `loss_spike_defense` returns `False` even if `L_task > 2.5 · L_task_ema` (defense is Phase-3+ only)

#### Scenario: Step ordering pinned
- **WHEN** `safeguards.STEP_ORDER` is accessed
- **THEN** it equals `("backward", "clip_grad_norm", "optimizer_step", "l2_norm")` exactly
