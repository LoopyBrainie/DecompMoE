## MODIFIED Requirements

### Requirement: Five Numerical Safeguard Helpers


The package SHALL provide five standalone helpers in `safeguards.py`: (1) `clip_global_grad_norm_(params, max_norm: float = 1.0) -> float` returning the pre-clip norm as a `float` (NOT `Tensor` — code-review N6 fix: `src/decompmoe/safeguards.py:54` returns `float(pre_clip_norm.item() ...)`); (2) `nan_ladder(consecutive_nan) -> tuple[str, float, bool]` returning `(action, lr_scale, halt)` where `action ∈ {"skip", "div_lr_10", "halt"}` for counts `(1, 3, 10)` respectively; (3) `should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]`; when `threshold=None`, the implementation calls `_dead_expert_threshold(N_e) = 1/(2·N_e)` to derive the effective threshold (at MVP `N_e = 16`, this yields `1/32`); (4) `beta_saturation_warning(β_per_expert: Tensor) -> bool` returning `True` when any `β_i > BETA_SATURATION_WARN = 30.4` (= `0.95 · BETA_MAX = 0.95 · 32`) — there is NO `β_max` parameter (code-review N7 fix: `src/decompmoe/safeguards.py:211` signature has no `β_max`; the warning threshold is sourced from the module-level `BETA_MAX` constant via `BETA_SATURATION_WARN: Final[float] = 0.95 * BETA_MAX`); (5) `loss_spike_defense(L_task: float, L_task_ema: float, phase: int, ratio: float = LOSS_SPIKE_RATIO) -> bool` returning `True` when `phase ≥ 3 and L_task > ratio · L_task_ema` — there is NO `*` keyword-only separator before `ratio` (code-review N8 fix: `src/decompmoe/safeguards.py:222` defines `ratio: float = LOSS_SPIKE_RATIO` as POSITIONAL_OR_KEYWORD); the function ONLY returns the boolean — the LR-scaling action (`LR × LOSS_SPIKE_LR_SCALE = LR × 0.8`) is the CALLER's responsibility (the function emits a "should scale" signal, not the scaling itself). The dead-expert threshold `1/(2·N_e)` replaces the previous hardcoded `1/128` (which was the `N_e=64` instantiation of the same `1/(2·N_e)` rule); at MVP `N_e = 16` this evaluates to `1/32`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200`, `RESURRECTION_RATE_LIMIT_STEPS = 1000`, `LOSS_SPIKE_RATIO = 2.5`, `LOSS_SPIKE_LR_SCALE = 0.8`, `BETA_SATURATION_WARN = 30.4`, `BETA_SATURATION_HALVE = 28.8` are `Final[int]` / `Final[float]` module-level constants (see `src/decompmoe/safeguards.py:23-41`); the spec references the constant identifiers rather than literal values. The standard step order SHALL be: `Backward → clip_grad_norm(1.0) → optimizer.step() → L2_norm(c_i)` (asserted via documented ordering constant `STEP_ORDER`).

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `src/decompmoe/safeguards.py:71-80` at commit `d3689a1`. The `nan_ladder` action Literal member `div_lr_10` (formerly `halve_lr` before archived change `2026-09-13-fix-nan-ladder-action-name-and-loss-spike-test-coverage`) carries the `lr_scale = 0.1` value (LR ÷ 10 per `wayfinder Req 13 Numerical Safeguards (#req-13)` wording, NOT LR ÷ 2 as the legacy name suggested); renaming aligns action name with actual scaling math.; change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` design.md (Decision 1 — rate-limit boundary pinned: guard defers iff `Δ < R`; `Δ = R` is not deferred; window-partition claim withdrawn as false)

#### Scenario: Global clip threshold
- **WHEN** `clip_global_grad_norm_(params, max_norm=1.0)` is called with `‖g‖₂ > 1.0`
- **THEN** all gradients are scaled to `‖g‖₂ ≤ 1.0`

#### Scenario: NaN escalation ladder
- **WHEN** `nan_ladder(c)` is called for `c ∈ {1, 3, 10}`
- **THEN** the returned tuple is `("skip", 1.0, False)` / `("div_lr_10", 0.1, False)` / `("halt", 1.0, True)` respectively

#### Scenario: NaN ladder default at consecutive_nan=0 (no NaN observed)
- **WHEN** `nan_ladder(0)` is called
- **THEN** the returned tuple is `("skip", 1.0, False)` — defensive default: when no NaN has been observed yet, the ladder falls back to skip-and-keep-LR (caller is expected to call only when a NaN flag has been raised). For `c ∉ {1, 3, 10}` and `c > 0` (e.g. `c=2`, `c=5`, `c=9`), the ladder returns the highest-priority tier that has been crossed: `c ∈ [1, 2] → ("skip", 1.0, False)`; `c ∈ [3, 9] → ("div_lr_10", 0.1, False)`; `c ≥ 10 → ("halt", 1.0, True)` (this matches wayfinder Req 13 'Numerical Safeguards' strict-greater-than ladder tiers (anchor `#req-13`) and is the implementation in `safeguards.py::nan_ladder`).

#### Scenario: Resurrection rate-limited
- **WHEN** `should_resurrect(f_history, current_step, last_resurrection_step, ...)` is called, with `Δ := current_step − last_resurrection_step` and `R := RESURRECTION_RATE_LIMIT_STEPS` (at MVP `R = 1000`)
- **THEN** the rate-limit guard defers the call — returning `set()` at `safeguards.py::should_resurrect` (the rate_limit_steps branch) — **if and only if** `Δ < R`; for `Δ ≥ R` the guard does not defer and the call proceeds to the dead-expert trigger. `Δ = R` is therefore **not** deferred: it is the first step the guard lets through. The helper may still return `set()` for reasons unrelated to rate limiting — `len(f_history) < consec` (`safeguards.py::should_resurrect`, the consec branch), or no expert meeting the per-step trigger (`safeguards.py::should_resurrect`, the per-step f_i < threshold branch); those are not deferrals and are outside this Scenario. **Derivation**: the guard predicate `D(Δ) := [Δ < R]` is monotone non-increasing in `Δ` with exactly one jump point, so the deferred set `{Δ : Δ < R}` is a down-open ray and the passing set `{Δ : Δ ≥ R}` an up-closed ray; the two meet at `Δ = R`. The `R`-long half-open-window reading is equivalent to the guard **per pair**: two events `t₁ < t₂` lie in a common window `[t, t + R)` **iff** `∃t. t ≤ t₁ < t₂ < t + R`, which is `⟺ Δ < R`. (The family `{[t, t + R) : t ∈ ℤ}` is **overlapping, not a partition** — `[0, R)` and `[1, R+1)` share `R−1 = 999` elements — so the equivalence is the per-pair existence claim above and never a global block structure; the `R`-aligned blocks `{W_{kR}}` are a genuine partition but do **not** satisfy it, e.g. `t₁ = R−1, t₂ = R` has `Δ = 1 < R` yet straddles two blocks.) Which side `Δ = R` falls on is fixed by the counterexample, not by that reading: under the `≤` alternative the `R`-aligned event stream `0, R, 2R, 3R, …` has every `Δ = R` event deferred and **dropped outright** (the helper returns `set()` and holds no retry queue), so for any caller that advances `last_resurrection_step` no more often than it emits, the realised rate is strictly below one event per `R` steps, contradicting wayfinder Req 13's "rate-limited to once per 1000 steps". (No caller in this repository writes `last_resurrection_step`; the counterexample is therefore stated caller-model-independently rather than by a concrete period.) Guarded by `tests/test_safeguards.py::test_should_resurrect_rate_limit_boundary` (pins `Δ = R−1` → empty, `Δ = R` → non-empty, `Δ = R+1` → non-empty); the mutation that turns it red is flipping `safeguards.py::should_resurrect`'s `<` to `<=`.

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

<a id="req-13"></a>

### Requirement: Five-Phase Schedule State Machine


The package SHALL provide `phase_id(step: int) -> int` returning `0` for `step ∈ [0, 999]`, `1` for `[1_000, 5_999]`, `2` for `[6_000, 25_999]`, `3` for `[26_000, 55_999]`, `4` for `[56_000, 100_000]`. The package SHALL provide `phase_step_frozen_names(phase: int) -> set[str]` returning the **gradient-channel** parameter-name set to freeze per phase (`{"c_i", "beta_i", "W_K", "W_V", "b"}` for phase 1; `{"c_i", "beta_i"}` for phase 2 — `W_K/W_V/b` are unfrozen in phase 2 to allow them to train under the EMA; `{"c_i"}` for phase 3 — `beta_i` is unfrozen; empty for phases 0/4). The package SHALL provide `should_reset_adam(prev_phase: int, next_phase: int) -> bool` returning `True` exactly when `prev_phase == 3 and next_phase == 4`. The advisory signals (`R_H`, `S_load`, `R_β-sat`, `L_sep/WB`) SHALL be exposed via `advisory_signals(...)` but SHALL NEVER trigger phase transitions (state-machine invariance under perturbed advisory is asserted).

#### Scenario: Phase boundaries at 100K
- **WHEN** `total_steps == 100_000`
- **THEN** the phase boundaries are `(1_000, 6_000, 26_000, 56_000, 100_000)` and phase `0 / 1 / 2 / 3 / 4` step ratios are `1% / 5% / 20% / 30% / 44%`

#### Scenario: Phase-0 and Phase-4 freeze-name set is empty
- **WHEN** `phase_step_frozen_names(0)` or `phase_step_frozen_names(4)` is called
- **THEN** the result is exactly `set()` in both cases — NOT `frozenset()`, NOT `None`, and NOT a non-empty set. Phase 0 is spherical K-Means seeding and has **no gradient channel at all** (`wayfinder` `#req-6` (Req 6 C Extraction Differentiability And Centroid Lifecycle): "Spherical K-Means seeding (no gradient, no EMA)"; the phase table under `wayfinder` `#req-27` (Req 27 CentroidDriver Dual-Channel Architecture Contract) records `| 0 | K-Means seeding | Frozen (requires_grad=False) | N/A |`), so the freeze-name set is vacuously empty. This is **not** "everything is frozen", which would instead be the full name set. Phase 4 unfreezes the entire gradient channel (wayfinder req-14), so nothing is frozen. Guarded by `tests/test_schedule.py::test_phase_step_frozen_names_phase_0_and_4_empty_set`.

#### Scenario: Phase-1 router freeze
- **WHEN** `phase_step_frozen_names(1)` is called
- **THEN** the result equals `{"c_i", "beta_i", "W_K", "W_V", "b"}` (the gradient-channel frozen set; driver channel still updates `c_i` via EMA at `α = 0.90`)

#### Scenario: Phase-2 expert freeze
- **WHEN** `phase_step_frozen_names(2)` is called
- **THEN** the result equals `{"c_i", "beta_i"}` (gradient-channel frozen; `W_K/W_V/b` are unfrozen to learn under the driver-channel EMA at `α = 0.95`)

#### Scenario: Adam reset boundary
- **WHEN** `should_reset_adam(3, 4)` is called
- **THEN** it returns `True`; for every other `(prev, next)` pair it returns `False`
<a id="req-14"></a>

### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension



The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask, *, grad=None, eta=1e-2) -> Tensor` method MUST apply, per phase. **`mask` is a REQUIRED positional parameter and MUST NOT be given a default value:** per-expert masked means `m_i` are undefined without it, and a defaulted `mask=None` invites an implementation to substitute a whole-batch mean for `m_i`, which silently broadcasts one mean to every centroid and collapses all territories to a single point. An implementation MUST reject a missing `mask` rather than substitute one.

- Phase 0 (SEEDING): `c_i ← c_i.detach()` (driver is a no-op returning the input centroids detached from the autograd graph); `c_i.requires_grad = False`. Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds. **The caller MUST supply Phase 0 seeds already satisfying `‖c_i‖₂ ≡ 1.0`** — this is a normative obligation on the caller, not a description of the driver's behaviour, and the driver MUST NOT normalise, project, or otherwise repair Phase 0 inputs. This elevation is the deliberate half of a paired correction: `wayfinder` req-23 previously asserted the spherical-norm invariant for "any Phase (including 0 K-Means)" while simultaneously declaring this driver a no-op, giving two peer specs mutually exclusive MUSTs for the same quantity. `wayfinder` req-23 has since been narrowed to **Phase 1–4**; this Requirement is the corresponding owner of the Phase 0 obligation, and the two MUSTs are no longer in conflict.
- Phase 1 (EMA_090): `c_i ← Normalize(0.90 · c_i + 0.10 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 2 (EMA_095): `c_i ← Normalize(0.95 · c_i + 0.05 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 3 (EMA_099): `c_i ← Normalize(0.99 · c_i + 0.01 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 4 (PROJECTED_SGD): When `grad is not None`: `candidate_i = c_i − eta · grad_i`; then `c_i^(t+1) = candidate_i / ‖candidate_i‖₂`. When `grad is None`: `c_i^(t+1) = c_i / ‖c_i‖₂` (L2 retraction of the input only). Both branches apply the Invariant #4 guard pattern: when `‖candidate_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)` (no `clamp_min(ε)` denominator; the same `torch.where(use_old, prev, normalize(...))` pattern used in EMA). Driver Active, gradient channel Active.

The `m_i` is the masked-mean over tokens assigned to expert `i`. The driver MUST enforce the empty-cell invariant: if `n_i = |T_i| = 0`, then `m_i ≡ c_i^(t−1)` (no `clamp_min(ε)` denominator). The driver MUST enforce the spherical re-projection invariant: `‖c_i^(t+1)‖₂ ≡ 1.0` after every step; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)`. The driver MAY call `decompmoe.safeguards.should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]` for dead-expert detection; the function itself lives in `safeguards.py` and is *called* from the driver (the driver MUST NOT define a same-named helper). When `threshold=None` is passed, the implementation derives the effective threshold via the private helper `_dead_expert_threshold(N_e) = 1/(2·N_e)`; at MVP `N_e = 16` this yields `1/32`. The dead-expert rule is parameterized by `N_e`, not hardcoded `1/128`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200` and `RESURRECTION_RATE_LIMIT_STEPS = 1000` are `Final[int]` module-level constants (see `safeguards.py::DEAD_EXPERT_CONSEC_STEPS` and `safeguards.py::RESURRECTION_RATE_LIMIT_STEPS`); the spec references the constant identifiers rather than literal values to ensure the spec stays in lock-step with the code if these constants are retuned.

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `safeguards.py::clip_global_grad_norm_` as of commit `d3689a1`.

The `step` signature `(*, grad=None, eta=1e-2)` REPLACES the legacy `(centroids, X, mask, eps=1e-6)` contract: the `eps` parameter is removed (no longer used by any active phase); the `grad` keyword is REQUIRED for the projected SGD step (no positional gradient argument); the `eta` keyword defaults to `1e-2` (conservative; spec does not pin a specific value beyond the linear convention); when `grad is None` the P4 branch is the identity L2 retraction (no SGD step applied — this is the backward-compatible fallback for callers that do not provide a gradient). Callers that previously passed `eps=1e-6` will need to remove the kwarg (breaking change; no in-repo callers pass `eps`).

#### Scenario: Phase-4 SGD-1-step closed form

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called with `centroids ∈ R^{N_e × d_c}` (unit-norm rows), `grad ∈ R^{N_e × d_c}` with `‖grad_i‖₂ = 0.05` for all `i`, and `eta = 1e-2`
- **THEN** for every expert `i` where `‖centroids[i] − eta · grad[i]‖₂ ≥ 1e-9`: `c_i^(t+1) == (centroids[i] − eta · grad[i]) / ‖centroids[i] − eta · grad[i]‖₂` within `abs=1e-7` (closed-form SGD step followed by L2 retraction)
- **AND** for every expert `i`: `‖c_i^(t+1)‖₂ == 1.0` within `abs=1e-7` (spherical re-projection invariant holds after the full P4 path, including the SGD step)

#### Scenario: Phase-4 SGD with near-zero candidate falls back to c_i^(t)

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called and for some expert `i` the post-SGD candidate `‖centroids[i] − eta · grad[i]‖₂ < 1e-9` (e.g. `centroids[i] = +grad[i] / ‖grad[i]‖₂` and `eta · ‖grad[i]‖₂ = 1`)
- **THEN** `c_i^(t+1) == c_i^(t)` element-wise (Invariant #4 fallback applies to the full P4 path, not only to the EMA branches) and no NaN appears in the centroid tensor

#### Scenario: Phase-4 with `grad=None` preserves the legacy L2-retraction semantics

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask)` is called with the default `grad=None` and `eta=1e-2`
- **THEN** `c_i^(t+1) == centroids[i] / ‖centroids[i]‖₂` element-wise within `abs=1e-7` (the legacy P4 behavior — L2 retraction of the input — is preserved exactly when no gradient is provided; this is the backward-compatibility contract for callers predating the SGD step addition)

---

<a id="req-19"></a>

### Requirement: Beta Parameterization Operational Domain — D1 Module-Level Constants


The package SHALL provide `inverse_temperature(gamma) -> Tensor` implementing the **parameterization-space** form `β = β_min + (β_max − β_min) · σ(γ)` with `β_min == 0.1` and `β_max == 32`. The package SHALL additionally provide `phase4_inverse_temperature(gamma_p) -> Tensor` implementing the **operational-domain** form `β^eff = 1 + 31 · σ(γ')` used in Phase 4 (the parameterization-space floor `0.1` and the operational-domain floor `1.0` are intentionally decoupled — the latter prevents routing resonance at runtime, the former keeps `σ'(γ)` non-degenerate in the cold-start region). The package SHALL provide `gamma_reset_for_phase4(beta_p3) -> float` implementing `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`; the worked example `gamma_reset_for_phase4(16.0) ≈ −0.0645385...` MUST hold within `abs=1e-4`. The package SHALL provide `beta_effective(gamma, phase, step) -> Tensor` returning `1.0` for `phase == 1`, `Clamp(inverse_temperature(gamma), 1.0, phase_beta_max(phase, step))` for `phase ∈ {2, 3}` (where `phase_beta_max(phase, step)` is the **time-varying** schedule ramp under the **pinned** linear-interpolation convention `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive: Phase 2 range `[6_000, 26_000)` ramp `1.0 → 4.0` (so `phase_beta_max(2, 6_000) = 1.0` exact at boundary start, `phase_beta_max(2, 16_000) = 2.5` exact at midpoint, `phase_beta_max(2, 25_999) = 1 + 3·19_999/20_000 = 3.99985`); Phase 3 range `[26_000, 56_000)` ramp `4.0 → 16.0` (so `phase_beta_max(3, 26_000) = 4.0` exact at boundary start = `box(3).lo`, `phase_beta_max(3, 41_000) = 4 + 12·15_000/30_000 = 10.0` exact at midpoint, `phase_beta_max(3, 55_999) = 4 + 12·29_999/30_000 = 15.9996`). `phase_beta_max` is **distinct** from the static `phase_beta_box(phase).hi` and the `step` parameter is required), and `phase4_inverse_temperature(gamma_p)` for `phase == 4`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` (operational-domain worst case, all domains) and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (**parameterization-space** worst case derived as `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95`, where `σ'(0) = 0.25` is the sigmoid derivative at `γ = 0` and the inner-product factor `|Cᵀc − 1|_max = 2` is the antipodal extreme; the **operational-domain Phase 4** worst case is `σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` at `γ' = 0` (canonical export per `beta.py::MAX_GRAD_PER_GAMMA_PHASE4` `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`); the two constants live in different domains and MUST NOT be conflated).

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

---

<a id="req-21"></a>
### Requirement: No decompmoe-skeleton spec changes required for cycle-12 finding 1 closure



The system SHALL NOT modify any `decompmoe-skeleton` spec Requirement as part of cycle-12 finding 1 closure. The cycle-12 finding 1 (historical: ticket A8-2 L70 centered-covariance + L74 CV/convex-hull vs `wayfinder Req 20 MCI row (#req-20-mci)` uncentered second moment) is **purely a wayfinder spec scope concern** — but `decompmoe-skeleton` **does** own a verbatim mirror of the wayfinder Req 20 closed-form definitions (see below), so this Requirement serves as an explicit declaration that the existing mirror is already aligned and no new mirror / no new behavior is being introduced by this change.

**Why no decompmoe-skeleton changes are needed**:

- `decompmoe-skeleton` Requirement `` `#req-22` `` ("Eight Metrics And Classification — CG Type Guard") **verbatim mirrors** `wayfinder` Req 20 closed-forms:
  - The closed-form table enumerates `L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, `MCI`, `CG` — the same 8 metric names wayfinder `Req 20` "Eight Geometric Quantification Metrics" (`#req-20`) defines
  - Each closed-form matches the corresponding wayfinder `#req-20` row verbatim (post-229016fe + 09-22 line-drift correction)
  - The Req 22 closed-form row explicitly mirrors the `MCI` row from `wayfinder` `#req-20-mci`, including the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (lower bound `1/d_c` on `S^{d_c−1}` makes `< 0.05` health target unreachable), the centered-covariance supersede reasoning (`(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations
- `decompmoe-skeleton` Requirement `` `#req-22` `` also defines `MCI closed-form on uniform token distribution` and `MCI closed-form on rank-1 token distribution` Scenarios (both `abs=1e-12`) — these mirror the two corresponding Scenarios under wayfinder `#req-20` verbatim
- cycle-12 finding 1 is specifically about `MCI` (an eight-metric row in `wayfinder `#req-20-mci`), implemented in `src/decompmoe/metrics.py` per `wayfinder` spec — `decompmoe-skeleton` mirrors the closed-form but does not own a separate MCI definition; both capabilities use the same uncentered second moment reading
- The `(historical, ...)` supersede annotations appended to ticket `wayfinder/tickets/A8-2.md` supersede annotations in this change apply to ticket lineage only; they do NOT modify the `decompmoe-skeleton` Req-22 mirror of the MCI closed-form (the mirror is already aligned with the canonical uncentered second moment reading)

**Source:** `wayfinder/tickets/A8-2.md` (cycle-12 finding 1 evidence — wayfinder `#req-20` owns the MCI closed-form; this capability's metric table is a verbatim mirror and is already flagged as a drift hazard)

#### Scenario: decompmoe-skeleton mirror of wayfinder Req 20 MCI closed-form is already aligned

- **WHEN** `decompmoe-skeleton` `#req-22` is read for the `MCI` closed-form
- **THEN** the Req 22 text verbatim contains the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (`replaces CV (whose lower bound 1/d_c on S^{d_c−1} made the original < 0.05 health target unreachable — see wayfinder/tickets/A8-2.md)`), the centered-covariance supersede reasoning (`The centered-covariance reading has its (1/d_c, 1] upper endpoint unreachable at |T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations — all mirroring wayfinder `#req-20-mci` verbatim
- **AND** the `MCI closed-form on uniform token distribution` and `MCI closed-form on rank-1 token distribution` Scenarios use `abs=1e-12` (mirroring the two corresponding Scenarios under wayfinder `#req-20`) — both endpoints of the declared `[1/d_c, 1]` range are guarded
- **AND** no `decompmoe-skeleton` Requirement is listed in the "Affected code / Affected Requirements" sections of `proposal.md` for this change (the mirror is unchanged)
- **AND** the `decompmoe-skeleton` spec.md anchor coverage remains unchanged (existing anchors per archived changes `2026-09-15-fix-skeleton-spec-duplicate-and-completeness-2026-09-15` + `2026-09-16-fill-skeleton-spec-leading-anchor-gaps` are not affected by this change)

