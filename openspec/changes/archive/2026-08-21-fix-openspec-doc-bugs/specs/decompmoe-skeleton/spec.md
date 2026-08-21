## MODIFIED Requirements

### Requirement: Active FLOPs Parity Against Dense Baseline

The package SHALL provide `flops_per_token(cfg, arch) -> int` whose canonical per-token active-FLOPs formula is symmetric across MoE and Dense sides:
- **MoE** (per token, per layer): `FLOPs_MoE,core^(l) = 8 · d_model² + k · 6 · d_model · d_ffn^Expert` (attention Q/K/V/O + top-k SwiGLU expert FFNs).
- **Dense** (per token, per layer): `FLOPs_Dense,core^(l) = 8 · d_model² + 6 · d_model · d_ffn^Dense`.

The parity constraint `d_ffn^Dense ≡ k · d_ffn^Expert` MUST hold; at MVP this evaluates to `4096 = 2 · 2048` (exact 1:1). Explicit exclusions (symmetric on both sides, NOT in parity accounting): Attention `Q K^T` and `Attn · V` (sequence-length-dependent), and the output `lm_head`. Routing overhead is reported separately as `FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c` (≈ 66_048 FLOPs/layer at MVP, ≈ 0.26% of active-core), within the `0.3%` allowance; it MUST NOT enter parity.

#### Scenario: MoE vs dense 1:1
- **WHEN** `flops_per_token(cfg, MOE_MVP)` is compared to `flops_per_token(cfg, DENSE_4096)`
- **THEN** the two active-core values are equal (exact parity); routing overhead is reported as a separate line item

---

### Requirement: Voronoi Self-Consistency Threshold

The package SHALL provide `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` returning the closed-form Voronoi half-angle on `S^{signature_dim − 1}`, computed as the unique `θ ∈ (0, π)` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e` (regularized incomplete beta function). The package SHALL also provide `voronoi_angle(centroids: Tensor) -> float` for the offline measurement layer (computes the realized half-angle from an actual centroid tensor; NOT for use in the training hot path). At MVP `d_c = 16`, `canonical_voronoi_angle(N_e=16, d_c=16)` SHALL return ≈ 52.00° (0.9076 rad), strictly greater than the specialist-collapse boundary `θ_{1/e}(β=16) = arccos(1 − 1/β) = arccos(15/16) ≈ 20.36°`. The previous closed-form bound `arctan(π / √d_c) ≈ 38.146°` is incorrect (depends on `d_c` only, contradicts MVP geometry, and self-contradicts the same-sentence `θ_{1/e} ≈ 20.36°` value via the wrong formula `arctan(1/β) = 3.58°`); it MUST NOT appear in any implementation.

#### Scenario: MVP self-consistency
- **WHEN** `canonical_voronoi_angle(num_experts=16, signature_dim=16)` is called
- **THEN** the returned angle is `≈ 52.00°` and exceeds `θ_{1/e}(β=16) ≈ 20.36°` (the specialist-collapse boundary)

#### Scenario: N_e dependence of voronoi_angle
- **WHEN** `canonical_voronoi_angle(num_experts=64, signature_dim=16)` is called
- **THEN** the returned angle is `≈ 25.45°` (the function depends on both `num_experts` and `signature_dim`, not `signature_dim` alone)

---

### Requirement: Centroid Four-Phase Lifecycle Driver

The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask) -> Tensor` method MUST apply, per phase:

- Phase 0 (SEEDING): `c_i ← KMeans(C)` initialization, `c_i.requires_grad = False`.
- Phase 1 (EMA_090): `c_i ← Normalize(0.90 · c_i + 0.10 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 2 (EMA_095): `c_i ← Normalize(0.95 · c_i + 0.05 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 3 (EMA_099): `c_i ← Normalize(0.99 · c_i + 0.01 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 4 (PROJECTED_SGD): `c_i ← (c_i − η · ∇_{c_i} L_routing) / ‖·‖₂`, driver Active, gradient channel Active.

The `m_i` is the masked-mean over tokens assigned to expert `i`. The driver MUST enforce the empty-cell invariant: if `n_i = |T_i| = 0`, then `m_i ≡ c_i^(t−1)` (no `clamp_min(ε)` denominator). The driver MUST enforce the spherical re-projection invariant: `‖c_i^(t+1)‖₂ ≡ 1.0` after every step; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)`. The driver SHALL expose a `should_resurrect(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/(2·N_e), consec=200) -> set[int]` helper that flags expert indices whose mask-fraction `f_i` was below `1/(2·N_e)` for `200` consecutive steps (rate-limited to once per `1000`-step window). At MVP `N_e = 16`, `1/(2·N_e) = 1/32`; the rule is parameterized by `N_e`, not a hardcoded `1/128`.

#### Scenario: Phase-0 non-differentiable
- **WHEN** `CentroidDriver(SEEDING).step(...)` is called
- **THEN** no gradient is registered on the input `centroids` (`requires_grad` not propagated)

#### Scenario: Phase-1 EMA coefficient
- **WHEN** `CentroidDriver(EMA_090).step(centroids, X, mask)` is called with `n_i > 0` for all experts
- **THEN** `step` returns `Normalize(0.90 · centroids + 0.10 · masked_mean(X)) / ‖·‖₂` (within FP tolerance, post-normalization)

#### Scenario: Phase-4 re-projection
- **WHEN** `CentroidDriver(PROJECTED_SGD).step(...)` is called
- **THEN** the output `centroids` satisfy `‖c_i‖₂ = 1.0` within `1e-7` after retraction

#### Scenario: Phase-1 driver Active despite gradient Frozen
- **WHEN** `CentroidDriver(EMA_090).step(...)` is called and the gradient channel is Frozen for `c_i`
- **THEN** the driver still updates `c_i` per the EMA rule; `c_i.requires_grad` remains `False`; `c_i` is NOT in the AdamW parameter group

---

### Requirement: Loss Composition With Staged Lambda

The package SHALL provide `L_total(task_logits, targets, f_per_expert, p_per_expert, c_centroids, phase, step, *, cfg) -> LossParts` returning a dataclass with `.L_CE`, `.L_lb`, `.L_sep`, `.L_total` fields. The constants SHALL be: `α = 0.01` (Switch-style fixed weight on `L_lb`), `λ(t)` schedule = `0` for `phase ∈ {1, 2}`, cosine ramp `0 → 0.001` during `phase == 3`, and `0.001` fixed for `phase == 4`. The `L_lb` closed form MUST be `L_lb = N_e · Σ_i f_i.detach() · P_i`, where `P_i = (1/T) · Σ_t p_i(C_t)` is the per-expert differentiable soft routing probability; gradient MUST flow through `P_i` and be blocked through `f_i.detach()`. The previous "verified by source grep" acceptance is incorrect (permits any expression containing `.detach()`); it MUST be replaced by the testable invariant `∂L_lb / ∂P_i ≠ 0` AND `∂L_lb / ∂f_i ≡ 0`. `L_sep` SHALL equal `(‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form); the `Σ_{i<j}` equivalent form MUST use factor `2/(N_e(N_e − 1))` — the factor `1/(N_e(N_e − 1))` is INCORRECT and MUST NOT appear.

#### Scenario: Alpha pinned to 0.01
- **WHEN** `L_total(...)` is evaluated
- **THEN** the `L_lb` contribution equals `0.01 · L_lb_raw` regardless of phase

#### Scenario: Lambda zero in phases 1 and 2
- **WHEN** `phase ∈ {1, 2}`
- **THEN** the `L_sep` contribution is exactly `0.0` (i.e. `λ(t) == 0`)

#### Scenario: Lambda fixed in phase 4
- **WHEN** `phase == 4`
- **THEN** `λ(t) == 0.001` constant across `step`

#### Scenario: L_sep closed form
- **WHEN** `c_centroids ∈ R^{N_e × d_c}` is on the unit sphere
- **THEN** `L_sep == (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` within `1e-6`

#### Scenario: L_lb gradient flows through P_i only
- **WHEN** `L_lb` is back-propagated
- **THEN** `∂L_lb / ∂P_i ≠ 0` (differentiable through `P_i`) and `∂L_lb / ∂f_i ≡ 0` (blocked by `.detach()`)

---

### Requirement: Five Numerical Safeguard Helpers

The package SHALL provide five standalone helpers in `safeguards.py`: (1) `clip_global_grad_norm_(params, max_norm=1.0) -> Tensor` returning the pre-clip norm; (2) `nan_ladder(consecutive_nan) -> tuple[str, float, bool]` returning `(action, lr_scale, halt)` where `action ∈ {"skip", "halve_lr", "halt"}` for counts `(1, 3, 10)` respectively; (3) `should_resurrect(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/(2·N_e), consec=200) -> set[int]` rate-limited to once per 1000 steps; (4) `beta_saturation_warning(β_per_expert, *, β_max=32) -> bool` returning `True` when any `β_i > 0.95 · β_max = 30.4`; (5) `loss_spike_defense(L_task, L_task_ema, phase, *, ratio=2.5) -> bool` returning `True` and signalling `LR × 0.8` when `phase ≥ 3 and L_task > ratio · L_task_ema`. The threshold `1/(2·N_e)` replaces the previous hardcoded `1/128` (which was the `N_e=64` instantiation of the same `1/(2·N_e)` rule); at MVP `N_e = 16` this evaluates to `1/32`. The standard step order SHALL be: `Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i)` (asserted via documented ordering constant `STEP_ORDER`).

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

---

### Requirement: Five-Phase Schedule State Machine

The package SHALL provide `phase_id(step: int) -> int` returning `0` for `step ∈ [0, 999]`, `1` for `[1_000, 5_999]`, `2` for `[6_000, 25_999]`, `3` for `[26_000, 55_999]`, `4` for `[56_000, 100_000]`. The package SHALL provide `phase_step_frozen_names(phase: int) -> set[str]` returning the **gradient-channel** parameter-name set to freeze per phase (`{"c_i", "beta_i", "W_K", "W_V", "b"}` for phase 1; `{"c_i", "beta_i"}` for phase 2 — `W_K/W_V/b` are unfrozen in phase 2 to allow them to train under the EMA; `{"c_i"}` for phase 3 — `beta_i` is unfrozen; empty for phases 0/4). The package SHALL provide `should_reset_adam(prev_phase: int, next_phase: int) -> bool` returning `True` exactly when `prev_phase == 3 and next_phase == 4`. The advisory signals (`R_H`, `S_load`, `R_β-sat`, `L_sep/WB`) SHALL be exposed via `advisory_signals(...)` but SHALL NEVER trigger phase transitions (state-machine invariance under perturbed advisory is asserted).

#### Scenario: Phase boundaries at 100K
- **WHEN** `total_steps == 100_000`
- **THEN** the phase boundaries are `(1_000, 6_000, 26_000, 56_000, 100_000)` and phase `0 / 1 / 2 / 3 / 4` step ratios are `1% / 5% / 20% / 30% / 44%`

#### Scenario: Phase-1 router freeze
- **WHEN** `phase_step_frozen_names(1)` is called
- **THEN** the result equals `{"c_i", "beta_i", "W_K", "W_V", "b"}` (the gradient-channel frozen set; driver channel still updates `c_i` via EMA at `α = 0.90`)

#### Scenario: Phase-2 expert freeze
- **WHEN** `phase_step_frozen_names(2)` is called
- **THEN** the result equals `{"c_i", "beta_i"}` (gradient-channel frozen; `W_K/W_V/b` are unfrozen to learn under the driver-channel EMA at `α = 0.95`)

#### Scenario: Adam reset boundary
- **WHEN** `should_reset_adam(3, 4)` is called
- **THEN** it returns `True`; for every other `(prev, next)` pair it returns `False`

---

### Requirement: Eight Metrics And Classification

The package SHALL provide eight metric functions (`L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_c`, `MCI`, `CG`) whose closed forms MUST match the master `wayfinder` Req 20 verbatim:

**Realtime Tier** (every step):
- `L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form).
- `R_H = −(1 / ln N_e) · Σ_i f_i · ln f_i`, normalized entropy; `R_H ∈ [0, 1]`.
- `S_load = N_e · max_i f_i`; `1` at perfect uniformity, `N_e` at full collapse.
- `UR = (1 / N_e) · Σ_i I[f_i > 0]` over the most recent W = 100 steps.

**Offline Tier** (diagnostic runs):
- `SP_i = (1 / ‖T_i‖₁) · Σ_{t ∈ T_i} c_iᵀ C_t`; if `‖T_i‖₁ = 0`, `SP_i ≡ undefined`.
- `D_chord = (2 / (N_e(N_e−1))) · Σ_{i<j} √(2(1 − c_iᵀ c_j))`.
- `MCI = (1 / d_c) · Σ_j 1 / λ̃_j²`, `λ̃_j = λ_j / Σ_r λ_r`; `MCI ∈ (1/d_c, 1]`.
- `CG = ‖∇_{W^{K, V, b}} L_total‖₂` (debug-only).

The package SHALL expose `REALTIME = frozenset({"L_sep", "R_H", "S_load", "UR"})` and `OFFLINE = frozenset({"SP", "D_c", "MCI", "CG"})`. `L_sep` from the metrics module SHALL be numerically equivalent to `L_sep` from the loss module under the same input. `R_H` SHALL lie in `[0, 1]` when fed a normalized probability distribution over `N_e` experts.

#### Scenario: Metric classification
- **WHEN** `metrics.REALTIME ∪ metrics.OFFLINE` is computed
- **THEN** the union has cardinality exactly `8` and equals the eight metric names

#### Scenario: R_H bounded
- **WHEN** `R_H(p)` is called for any probability vector `p`
- **THEN** the result lies in `[0, 1]` within `1e-6`

#### Scenario: L_sep cross-module consistency
- **WHEN** `metrics.L_sep(c_centroids)` is compared to `loss.compute_L_sep(c_centroids)` under the same input
- **THEN** the two values are equal within `1e-6`

---

### Requirement: Hard-Constraint Grep Invariants

The package SHALL satisfy the following source-level invariants, asserted by grep tests:
- NO occurrence of `StraightThroughEstimator` or `straight_through` in `src/decompmoe/`
- NO occurrence of `w_i` in the body of `distance.logit` (signature-level invariant already covered)
- NO occurrence of `shared` attribute in `ExpertPool`
- NO import of `torch.utils.cpp_extension` or `triton` in `experts.py`
- NO field `kv_cache_c` in `GeometricRouter` Protocol
- **NO occurrence of `.clamp_min(1e-9)` (or any `.clamp_min(ε)` with `ε ≤ 1e-6`) in `extraction.py` whose result is used as a denominator on the empty-cell branch** (enforces the empty-cell fallback invariant — see also `test_empty_cell_preserves_centroid`).
- **NO occurrence of the literal token sequence `arctan(pi / sqrt(d_c))` (or `arctan(π / √d_c)`) in any module** (enforces the canonical Voronoi closed form).

#### Scenario: Hard constraints hold
- **WHEN** the grep invariants above are evaluated against `src/decompmoe/`
- **THEN** all invariants pass

## ADDED Requirements

### Requirement: Centroid Driver Invariant Test Scenarios

The package's test suite SHALL include the following three tests, asserting the spherical re-projection and empty-cell fallback invariants on `CentroidDriver.step(...)`:

#### Scenario: test_empty_cell_preserves_centroid
- **WHEN** `CentroidDriver.step(centroids, X, mask)` is called with a mask where `n_i = 0` for some expert `i`
- **THEN** `‖c_i^(t+1) − c_i^(t)‖₂ < 10⁻¹²` (machine-epsilon identity; no direction randomization)

#### Scenario: test_spherical_norm_is_strictly_one
- **WHEN** `CentroidDriver.step(...)` is iterated over Phase 1 (EMA_090), Phase 2 (EMA_095), Phase 3 (EMA_099), and Phase 4 (PROJECTED_SGD)
- **THEN** after every step, `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷` for all experts

#### Scenario: test_near_zero_candidate_fallback
- **WHEN** `CentroidDriver.step(...)` is called with input features `X` that produce a degenerate per-expert mean `‖u_i‖₂ < 10⁻⁹` for some expert `i`
- **THEN** the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears in the centroid tensor