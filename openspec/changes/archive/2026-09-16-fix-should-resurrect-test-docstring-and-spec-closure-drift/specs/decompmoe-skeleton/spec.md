## MODIFIED Requirements

### Requirement: Five Numerical Safeguard Helpers

The package SHALL provide five standalone helpers in `safeguards.py`: (1) `clip_global_grad_norm_(params, max_norm: float = 1.0) -> float` returning the pre-clip norm as a `float` (NOT `Tensor` — code-review N6 fix: `src/decompmoe/safeguards.py:54` returns `float(pre_clip_norm.item() ...)`); (2) `nan_ladder(consecutive_nan) -> tuple[str, float, bool]` returning `(action, lr_scale, halt)` where `action ∈ {"skip", "div_lr_10", "halt"}` for counts `(1, 3, 10)` respectively; (3) `should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]`; when `threshold=None`, the implementation calls `_dead_expert_threshold(N_e) = 1/(2·N_e)` to derive the effective threshold (at MVP `N_e = 16`, this yields `1/32`); (4) `beta_saturation_warning(β_per_expert: Tensor) -> bool` returning `True` when any `β_i > BETA_SATURATION_WARN = 30.4` (= `0.95 · BETA_MAX = 0.95 · 32`) — there is NO `β_max` parameter (code-review N7 fix: `src/decompmoe/safeguards.py:211` signature has no `β_max`; the warning threshold is sourced from the module-level `BETA_MAX` constant via `BETA_SATURATION_WARN: Final[float] = 0.95 * BETA_MAX`); (5) `loss_spike_defense(L_task: float, L_task_ema: float, phase: int, ratio: float = LOSS_SPIKE_RATIO) -> bool` returning `True` when `phase ≥ 3 and L_task > ratio · L_task_ema` — there is NO `*` keyword-only separator before `ratio` (code-review N8 fix: `src/decompmoe/safeguards.py:222` defines `ratio: float = LOSS_SPIKE_RATIO` as POSITIONAL_OR_KEYWORD); the function ONLY returns the boolean — the LR-scaling action (`LR × LOSS_SPIKE_LR_SCALE = LR × 0.8`) is the CALLER's responsibility (the function emits a "should scale" signal, not the scaling itself). The dead-expert threshold `1/(2·N_e)` replaces the previous hardcoded `1/128` (which was the `N_e=64` instantiation of the same `1/(2·N_e)` rule); at MVP `N_e = 16` this evaluates to `1/32`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200`, `RESURRECTION_RATE_LIMIT_STEPS = 1000`, `LOSS_SPIKE_RATIO = 2.5`, `LOSS_SPIKE_LR_SCALE = 0.8`, `BETA_SATURATION_WARN = 30.4`, `BETA_SATURATION_HALVE = 28.8` are `Final[int]` / `Final[float]` module-level constants (see `src/decompmoe/safeguards.py:23-41`); the spec references the constant identifiers rather than literal values. The standard step order SHALL be: `Backward → clip_grad_norm(1.0) → optimizer.step() → L2_norm(c_i)` (asserted via documented ordering constant `STEP_ORDER`).

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `src/decompmoe/safeguards.py:71-80` at commit `d3689a1`. The `nan_ladder` action Literal member `div_lr_10` (formerly `halve_lr` before archived change `2026-09-13-fix-nan-ladder-action-name-and-loss-spike-test-coverage`) carries the `lr_scale = 0.1` value (LR ÷ 10 per wayfinder L249 wording, NOT LR ÷ 2 as the legacy name suggested); renaming aligns action name with actual scaling math.

#### Scenario: Global clip threshold
- **WHEN** `clip_global_grad_norm_(params, max_norm=1.0)` is called with `‖g‖₂ > 1.0`
- **THEN** all gradients are scaled to `‖g‖₂ ≤ 1.0`

#### Scenario: NaN escalation ladder
- **WHEN** `nan_ladder(c)` is called for `c ∈ {1, 3, 10}`
- **THEN** the returned tuple is `("skip", 1.0, False)` / `("div_lr_10", 0.1, False)` / `("halt", 1.0, True)` respectively

#### Scenario: NaN ladder default at consecutive_nan=0 (no NaN observed)
- **WHEN** `nan_ladder(0)` is called
- **THEN** the returned tuple is `("skip", 1.0, False)` — defensive default: when no NaN has been observed yet, the ladder falls back to skip-and-keep-LR (caller is expected to call only when a NaN flag has been raised). For `c ∉ {1, 3, 10}` and `c > 0` (e.g. `c=2`, `c=5`, `c=9`), the ladder returns the highest-priority tier that has been crossed: `c ∈ [1, 2] → ("skip", 1.0, False)`; `c ∈ [3, 9] → ("div_lr_10", 0.1, False)`; `c ≥ 10 → ("halt", 1.0, True)` (this matches wayfinder Req 13 'Numerical Safeguards' strict-greater-than ladder tiers (anchor `#req-13`) and is the implementation in `src/decompmoe/safeguards.py:62-72`).

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

#### Scenario: `should_resurrect` semantic interpretation (per-step vs avg-window)
- **WHEN** the dead-expert trigger is evaluated at time `t` with `f_history` containing the last `consec` snapshots
- **THEN** expert `i` is flagged iff every snapshot `f_history[-consec:][j][i]` satisfies `f_history[-consec:][j][i] < threshold` (per-step strict less-than interpretation). The wayfinder Req 13 wording `f_i^avg < 1/(2·N_e)` for 200 consecutive steps is interpreted as "per-step `f_i < threshold` sustained over the 200-snapshot window" rather than "literal mean-over-window `< threshold`". **Mathematical equivalence disambiguation**: let `H = f_history[-consec:]` be the last `consec` snapshots and `T = threshold`. Two readings are mathematically distinct:
  - **avg-window reading**: `flag_avg(i) ⟺ (1/consec) · Σ_{j=0..consec-1} H[j][i] < T` — i.e., the **windowed temporal mean** of `f_i` falls below threshold.
  - **per-step reading (current code)**: `flag_step(i) ⟺ ∀ j ∈ [0, consec): H[j][i] < T` — i.e., **every** per-step value falls strictly below threshold.

  The relationship is one-directional in general: `flag_step ⟹ flag_avg` **IS** universally true (proved by elementary algebra: `∀ j: H[j][i] < T` ⇒ `Σ_{j=0..consec-1} H[j][i] < consec · T` ⇒ `(1/consec) · Σ_{j=0..consec-1} H[j][i] < T`); the **non-universal** direction is `flag_avg ⟹ flag_step`, demonstrated by the counterexample below. However, on **constant history** (`H[j][i] = v` for all `j`) the two readings agree (both reduce to `v < T`); on **non-constant history** they can disagree. The per-step reading is therefore the **strictly tighter trigger**: any history flagged by per-step is also flagged by avg-window — written as **per-step ⊊ avg-window** (per-step triggers a **strict subset** of the histories that avg-window triggers on; per-step never triggers on a history that avg-window misses, but the converse fails). The current implementation commits to the per-step reading because (a) at MVP `N_e = 16`, the per-expert routing fraction `f_i` already aggregates token-level routing information per step (one snapshot = one batch's per-expert top-k fraction), leaving no temporal smoothing to perform; (b) a single transient spike `f_i ≥ threshold` above the dead-expert threshold within the window correctly suppresses resurrection under per-step, matching the wayfinder Req 13 wording's "for 200 consecutive steps" temporal qualifier (every step must be below, not merely the average over the window).

  **Worked counterexample (per-step vs avg-window divergence on non-constant history)**: let `consec = 200`, `threshold = 1/(2·N_e) = 1/32 ≈ 0.03125`, and consider the history `H[j][i] = 0.005` for `j ∈ [0, 198]` and `H[199][i] = 0.99` (199 sub-threshold steps followed by one super-threshold spike):
  - avg-window: `(199 · 0.005 + 1 · 0.99) / 200 = (0.995 + 0.99) / 200 = 1.985 / 200 = 0.009925` — `0.009925 < 0.03125` ⇒ TRIGGER (resurrect).
  - per-step: `199` sub-threshold checks pass, `0.99 < 0.03125` is FALSE ⇒ NO TRIGGER (do not resurrect).

  Reverse direction: history `H[j][i] = 0.05` for `j ∈ [0, 198]` and `H[199][i] = 0.005` (199 super-threshold steps followed by one sub-threshold step):
  - avg-window: `(199 · 0.05 + 1 · 0.005) / 200 = (9.95 + 0.005) / 200 = 9.955 / 200 = 0.049775` — `0.049775 < 0.03125` is FALSE ⇒ NO TRIGGER.
  - per-step: `199` super-threshold checks fail (`0.05 < 0.03125` FALSE) ⇒ NO TRIGGER.

  Both readings agree on constant history (`H[j][i] = 0.005` everywhere): avg-window `= 0.005 < 0.03125` ⇒ TRIGGER; per-step `0.005 < 0.03125` for every `j` ⇒ TRIGGER.

  **Universal-direction positive worked example (algebra proof's positive complement to Counterexample A; verifies `flag_step ⟹ flag_avg` on non-constant history)**: let `consec = 200`, `threshold = 1/(2·N_e) = 1/32 ≈ 0.03125`, and consider the history `H[j][i] = 0.001` for `j ∈ [0, 198]` and `H[199][i] = 0.030` (every snapshot has every `f_i` strictly below threshold, but the values are non-constant across the window):
  - per-step: every snapshot has every `f_i = 0.001 < 0.03125` AND the final snapshot `f_i = 0.030 < 0.03125` ⇒ all 16 experts TRIGGER.
  - avg-window: `(199 · 0.001 + 1 · 0.030) / 200 = (0.199 + 0.030) / 200 = 0.229 / 200 = 0.001145` — `0.001145 < 0.03125` ⇒ TRIGGER (resurrect).
  - Both readings agree on the TRIGGER side on this non-constant history, confirming the algebra proof's universal direction `flag_step ⟹ flag_avg`: every history that per-step flags is also flagged by avg-window. This is the **positive** counterpoint to Counterexample A's **negative** — together they establish `per-step ⊊ avg-window` (per-step ⊊ set-of-flags-by-avg-window; per-step is a strict subset, not a strict superset and not co-extensive).

  **Notational pin on `f_i^avg`** (wayfinder Req 13): the superscript `avg` is **NOT** "averaged over the 200-step window". It denotes **averaged across experts** (i.e., `f_i` is itself the per-expert routing fraction, an average across tokens within the batch, normalized to sum to 1 across all `N_e` experts at each step). The trigger condition reads in unambiguous form: "the per-expert routing fraction `f_i` (already a cross-expert average within a single step) stays below `1/(2·N_e)` for 200 consecutive steps". The "200 consecutive steps" temporal qualifier pins the per-step reading; a windowed temporal mean would require the qualifier "for 200 steps on average", which the wayfinder Req 13 wording does not contain. Cross-reference: wayfinder Req 13's `f_i^avg` notation is used identically in the `R_H` formula `R_H = −(1/ln N_e) · Σ_i f_i · ln f_i` (wayfinder Req 20 metric definition) where `f_i` is unambiguously a per-step per-expert fraction; the same notation must carry the same meaning in Req 13's `f_i^avg < 1/(2·N_e)` trigger.

  **Open follow-up**: a future ticket adopting avg-window semantics would re-evaluate the trigger condition as `flag_avg(i)` above, and MUST update spec + code + the `test_should_resurrect_current_per_step_semantic_pinned` guard test atomically; the existing guard test in `tests/test_safeguards.py` continues to pin the current per-step behavior.
