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

#### Scenario: NaN ladder default at consecutive_nan=0 (no NaN observed)
- **WHEN** `nan_ladder(0)` is called
- **THEN** the returned tuple is `("skip", 1.0, False)` — defensive default: when no NaN has been observed yet, the ladder falls back to skip-and-keep-LR (caller is expected to call only when a NaN flag has been raised). For `c ∉ {1, 3, 10}` and `c > 0` (e.g. `c=2`, `c=5`, `c=9`), the ladder returns the highest-priority tier that has been crossed: `c ∈ [1, 2] → ("skip", 1.0, False)`; `c ∈ [3, 9] → ("halve_lr", 0.1, False)`; `c ≥ 10 → ("halt", 1.0, True)` (this matches wayfinder L249 strict-greater-than ladder tiers and is the implementation in `src/decompmoe/safeguards.py:62-72`).

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
- **THEN** expert `i` is flagged iff every snapshot `f_history[-consec:][j][i]` satisfies `f_history[-consec:][j][i] < threshold` (per-step strict less-than interpretation). The wayfinder L249 wording `f_i^avg < 1/(2·N_e)` for 200 consecutive steps is interpreted as "per-step `f_i < threshold` sustained over the 200-snapshot window" rather than "literal mean-over-window `< threshold`". **Mathematical equivalence disambiguation**: let `H = f_history[-consec:]` be the last `consec` snapshots and `T = threshold`. Two readings are mathematically distinct:
  - **avg-window reading**: `flag_avg(i) ⟺ (1/consec) · Σ_{j=0..consec-1} H[j][i] < T` — i.e., the **windowed temporal mean** of `f_i` falls below threshold.
  - **per-step reading (current code)**: `flag_step(i) ⟺ ∀ j ∈ [0, consec): H[j][i] < T` — i.e., **every** per-step value falls strictly below threshold.

  The relationship is one-directional in general: `flag_step ⟹ flag_avg` **IS** universally true (proved by elementary algebra: `∀ j: H[j][i] < T` ⇒ `Σ_{j=0..consec-1} H[j][i] < consec · T` ⇒ `(1/consec) · Σ_{j=0..consec-1} H[j][i] < T`); the **non-universal** direction is `flag_avg ⟹ flag_step`, demonstrated by the counterexample below. However, on **constant history** (`H[j][i] = v` for all `j`) the two readings agree (both reduce to `v < T`); on **non-constant history** they can disagree. The per-step reading is therefore the **strictly tighter trigger**: any history flagged by per-step is also flagged by avg-window — written as **per-step ⊊ avg-window** (per-step triggers a **strict subset** of the histories that avg-window triggers on; per-step never triggers on a history that avg-window misses, but the converse fails). The current implementation commits to the per-step reading because (a) at MVP `N_e = 16`, the per-expert routing fraction `f_i` already aggregates token-level routing information per step (one snapshot = one batch's per-expert top-k fraction), leaving no temporal smoothing to perform; (b) a single transient spike `f_i ≥ threshold` above the dead-expert threshold within the window correctly suppresses resurrection under per-step, matching the wayfinder L249 wording's "for 200 consecutive steps" temporal qualifier (every step must be below, not merely the average over the window).

  **Worked counterexample (per-step vs avg-window divergence on non-constant history)**: let `consec = 200`, `threshold = 1/(2·N_e) = 1/32 ≈ 0.03125`, and consider the history `H[j][i] = 0.005` for `j ∈ [0, 198]` and `H[199][i] = 0.99` (199 sub-threshold steps followed by one super-threshold spike):
  - avg-window: `(199 · 0.005 + 1 · 0.99) / 200 = (0.995 + 0.99) / 200 = 1.985 / 200 = 0.009925` — `0.009925 < 0.03125` ⇒ TRIGGER (resurrect).
  - per-step: `199` sub-threshold checks pass, `0.99 < 0.03125` is FALSE ⇒ NO TRIGGER (do not resurrect).

  Reverse direction: history `H[j][i] = 0.05` for `j ∈ [0, 198]` and `H[199][i] = 0.005` (199 super-threshold steps followed by one sub-threshold step):
  - avg-window: `(199 · 0.05 + 1 · 0.005) / 200 = (9.95 + 0.005) / 200 = 9.955 / 200 = 0.049775` — `0.049775 < 0.03125` is FALSE ⇒ NO TRIGGER.
  - per-step: `199` super-threshold checks fail (`0.05 < 0.03125` FALSE) ⇒ NO TRIGGER.

  Both readings agree on constant history (`H[j][i] = 0.005` everywhere): avg-window `= 0.005 < 0.03125` ⇒ TRIGGER; per-step `0.005 < 0.03125` for every `j` ⇒ TRIGGER.

  **Notational pin on `f_i^avg`** (wayfinder L249): the superscript `avg` is **NOT** "averaged over the 200-step window". It denotes **averaged across experts** (i.e., `f_i` is itself the per-expert routing fraction, an average across tokens within the batch, normalized to sum to 1 across all `N_e` experts at each step). The trigger condition reads in unambiguous form: "the per-expert routing fraction `f_i` (already a cross-expert average within a single step) stays below `1/(2·N_e)` for 200 consecutive steps". The "200 consecutive steps" temporal qualifier pins the per-step reading; a windowed temporal mean would require the qualifier "for 200 steps on average", which the wayfinder L249 wording does not contain. Cross-reference: wayfinder L249's `f_i^avg` notation is used identically in the `R_H` formula `R_H = −(1/ln N_e) · Σ_i f_i · ln f_i` (wayfinder Req 20 metric definition) where `f_i` is unambiguously a per-step per-expert fraction; the same notation must carry the same meaning in L249's `f_i^avg < 1/(2·N_e)` trigger.

  **Open follow-up**: a future ticket adopting avg-window semantics would re-evaluate the trigger condition as `flag_avg(i)` above, and MUST update spec + code + the `test_should_resurrect_current_per_step_semantic_pinned` guard test atomically; the existing guard test in `tests/test_safeguards.py` continues to pin the current per-step behavior.

### Requirement: Beta Parameterization Operational Domain — D1 Module-Level Constants

The package SHALL provide `inverse_temperature(gamma) -> Tensor` implementing the **parameterization-space** form `β = β_min + (β_max − β_min) · σ(γ)` with `β_min == 0.1` and `β_max == 32`. The package SHALL additionally provide `phase4_inverse_temperature(gamma_p) -> Tensor` implementing the **operational-domain** form `β^eff = 1 + 31 · σ(γ')` used in Phase 4 (the parameterization-space floor `0.1` and the operational-domain floor `1.0` are intentionally decoupled — the latter prevents routing resonance at runtime, the former keeps `σ'(γ)` non-degenerate in the cold-start region). The package SHALL provide `gamma_reset_for_phase4(beta_p3) -> float` implementing `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`; the worked example `gamma_reset_for_phase4(16.0) ≈ −0.0645385...` MUST hold within `abs=1e-4`. The package SHALL provide `beta_effective(gamma, phase, step) -> Tensor` returning `1.0` for `phase == 1`, `Clamp(inverse_temperature(gamma), 1.0, phase_beta_max(phase, step))` for `phase ∈ {2, 3}` (where `phase_beta_max(phase, step)` is the **time-varying** schedule ramp under the **pinned** linear-interpolation convention `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive: Phase 2 range `[6_000, 26_000)` ramp `1.0 → 4.0` (so `phase_beta_max(2, 6_000) = 1.0` exact at boundary start, `phase_beta_max(2, 16_000) = 2.5` exact at midpoint, `phase_beta_max(2, 25_999) = 1 + 3·19_999/20_000 = 3.99985`); Phase 3 range `[26_000, 56_000)` ramp `4.0 → 16.0` (so `phase_beta_max(3, 26_000) = 4.0` exact at boundary start = `box(3).lo`, `phase_beta_max(3, 41_000) = 4 + 12·15_000/30_000 = 10.0` exact at midpoint, `phase_beta_max(3, 55_999) = 4 + 12·29_999/30_000 = 15.9996`). `phase_beta_max` is **distinct** from the static `phase_beta_box(phase).hi` and the `step` parameter is required), and `phase4_inverse_temperature(gamma_p)` for `phase == 4`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` (operational-domain worst case, all domains) and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (**parameterization-space** worst case derived as `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95`, where `σ'(0) = 0.25` is the sigmoid derivative at `γ = 0` and the inner-product factor `|Cᵀc − 1|_max = 2` is the antipodal extreme; the **operational-domain Phase 4** worst case is `σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` at `γ' = 0` (canonical export per `src/decompmoe/beta.py:50` `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`); the two constants live in different domains and MUST NOT be conflated).

**`beta_effective` signature is exactly 3 positional args `(gamma, phase, step)`** — there is no `cfg` keyword-only parameter. Per `design.md` Decision 1, the algorithmic constants `β_min = 0.1` and `β_max = 32` live as module-level `Final[float]` in `decompmoe/beta.py` (not in MVPConfig and not threaded through `cfg`). The signature intentionally avoids `cfg` to keep the call site focused on the schedule / phase decision and to avoid the indirection cost of looking up constants that are already canonically placed. The three constants `31` (Phase 4 span), `31.9` (parameterization span), and `1.0` (Phase 4 floor) likewise live in `decompmoe/beta.py`.

#### Scenario: Parameterization endpoints

- **WHEN** `inverse_temperature(gamma)` is called with `gamma ∈ {-50, 0, 50}`
- **THEN** the result is `≈ 0.1` / `16.05` (midpoint) / `≈ 32.0` respectively within `1e-3`

#### Scenario: gamma reset for phase 4 boundary continuity

- **WHEN** `gamma_reset_for_phase4(16.0)` is called
- **THEN** the result equals `ln(15/16) ≈ −0.0645385...` within `abs=1e-4`

#### Scenario: beta_effective is continuous at Phase 3 → 4 boundary

- **WHEN** `beta_effective(gamma_p=ln(15/16), phase=4, step=56_000)` is called
- **THEN** the result equals `1 + 31 · σ(ln(15/16)) = 16.0` exactly (continuity with Phase 3's terminal `β_max`)