# decompmoe-skeleton Specification

## Purpose
Defines the observable, testable behavior of the DecompMoE skeleton: type-safe contracts (`MVPConfig`, Protocol stubs for `GeometricRouter` / `TerritoryHolder` / `BlockAdapter`) and pure-function mathematical primitives that materialize the 21 Requirements × 34 Scenarios of the main `wayfinder` spec into Python. The skeleton is formalize-only — no executable forward/backward; every public symbol carries a behavioral contract that downstream changes (training, inference, baselines) MUST honor.

## Requirements

### Requirement: Canonical Package And Version Identifier

The package SHALL expose `decompmoe.__canonical_name__ == "DecompMoE"`, `decompmoe.__alias__ == "GeoMoE"`, and `decompmoe.__version__` as a `str` matching PEP 440 semantics. The package SHALL expose a stable `__all__` listing every public symbol introduced by this skeleton. The alias SHALL NOT appear as a code identifier anywhere in the package (only in design prose / docstrings).

#### Scenario: Name resolution
- **WHEN** `decompmoe.__canonical_name__` is accessed
- **THEN** it returns the literal string `"DecompMoE"`

#### Scenario: Alias preserved
- **WHEN** `decompmoe.__alias__` is accessed
- **THEN** it returns the literal string `"GeoMoE"` for documentation continuity

### Requirement: Frozen MVP Hyperparameter Set

The package SHALL provide a `MVPConfig` frozen dataclass whose locked constants equal: `d_model == 1024`, `N_e == 16`, `k == 2`, `d_ffn == 2048`, `L == 4`, `d_ffn_dense == 4096`, `d_c == 16`, `H_kv == 8`, `d_k == 128`, `β_min == 0.1`, `β_max == 32`, `β_initial == 1.0`. Attempting to mutate any field SHALL raise `dataclasses.FrozenInstanceError`. A factory function `MVPConfig()` SHALL return an instance with all default values.

#### Scenario: Field defaults locked
- **WHEN** `MVPConfig()` is constructed
- **THEN** `cfg.d_model == 1024 and cfg.N_e == 16 and cfg.k == 2 and cfg.d_ffn == 2048 and cfg.L == 4`

#### Scenario: Mutation rejected
- **WHEN** any field is assigned after construction
- **THEN** `dataclasses.FrozenInstanceError` is raised

### Requirement: Total And Active Parameter Estimator

The package SHALL provide `compute_total_and_active(cfg) -> tuple[int, int]` whose first element is the total parameter count (dense embeddings + attention + all N_e SwiGLU experts + geometric router) and second element is the per-token active parameter count (attention + k experts at width `d_ffn`). Both values SHALL be within ±1% of `452_000_000` and `100_000_000` respectively when `cfg == MVPConfig()`.

#### Scenario: 452M / 100M agreement
- **WHEN** `compute_total_and_active(MVPConfig())` is called
- **THEN** the first value lies in `[448_000_000, 456_000_000]` and the second in `[99_000_000, 101_000_000]`

### Requirement: Active FLOPs Parity Against Dense Baseline

The package SHALL provide `flops_per_token(cfg, arch) -> int` whose canonical per-token active-FLOPs formula is symmetric across MoE and Dense sides:
- **MoE** (per token, per layer): `FLOPs_MoE,core^(l) = 8 · d_model² + k · 6 · d_model · d_ffn^Expert` (attention Q/K/V/O + top-k SwiGLU expert FFNs).
- **Dense** (per token, per layer): `FLOPs_Dense,core^(l) = 8 · d_model² + 6 · d_model · d_ffn^Dense`.

The parity constraint `d_ffn^Dense ≡ k · d_ffn^Expert` MUST hold; at MVP this evaluates to `4096 = 2 · 2048` (exact 1:1). Explicit exclusions (symmetric on both sides, NOT in parity accounting): Attention `Q K^T` and `Attn · V` (sequence-length-dependent), and the output `lm_head`. Routing overhead is reported separately as `FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c` (≈ 66_048 FLOPs/layer at MVP, ≈ 0.20% of active-core), within the `0.3%` allowance; it MUST NOT enter parity. (The previous figure `0.26%` was arithmetically inconsistent with the active-core definition in this paragraph; the corrected figure `0.20%` is `66_048 / 33_554_432 ≈ 0.001968`.)

#### Scenario: MoE vs dense 1:1
- **WHEN** `flops_per_token(cfg, MOE_MVP)` is compared to `flops_per_token(cfg, DENSE_4096)`
- **THEN** the two active-core values are equal (exact parity); routing overhead is reported as a separate line item

### Requirement: Wire-Level Contracts

The package SHALL provide `Protocol` classes `GeometricRouter`, `TerritoryHolder`, and `BlockAdapter` that expose ONLY the methods/attributes required by Req 3, 4, 16, 17, 18. `GeometricRouter` SHALL declare `extract_C(K, V) -> Tensor`, `gating_logits(C) -> Tensor`, `route(x, logits) -> Tensor`. `GeometricRouter` SHALL NOT declare any `kv_cache_c` attribute (Req 16 / 17 violation would be caught statically). `TerritoryHolder` SHALL declare `territory_volume() -> float`, `active_territories() -> set[int]`, `coverage_balance_loss() -> Tensor`. `BlockAdapter` SHALL declare `forward_residual(x, ...) -> Tensor`. None of these Protocols SHALL contain an executable body (signatures only).

#### Scenario: Router signatures present
- **WHEN** `GeometricRouter` is inspected via `typing.get_type_hints` or `inspect.signature`
- **THEN** `extract_C`, `gating_logits`, `route` are listed and `kv_cache_c` is absent from the annotation set

### Requirement: Inverse-Temperature Sigmoid With Gradient Bounds

The package SHALL provide `inverse_temperature(γ) -> Tensor` implementing `β = β_min + (β_max − β_min) · σ(γ)`, where `β_min == 0.1` and `β_max == 32`. The function SHALL be implemented with `torch.sigmoid` and SHALL be fully differentiable with respect to `γ`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (= `0.5 · (β_max − β_min)`).

#### Scenario: Endpoint agreement
- **WHEN** `γ → −∞` (e.g. `γ = −50.0`)
- **THEN** `inverse_temperature(γ) ≈ 0.1` within `1e-3`

#### Scenario: Upper endpoint agreement
- **WHEN** `γ → +∞` (e.g. `γ = 50.0`)
- **THEN** `inverse_temperature(γ) ≈ 32.0` within `1e-3`

#### Scenario: Monotonicity
- **WHEN** `γ₁ < γ₂`
- **THEN** `inverse_temperature(γ₁) < inverse_temperature(γ₂)`

#### Scenario: Gradient bound on ∂logit/∂C
- **WHEN** `torch.autograd.gradcheck` is run on `logit = β · (Cᵀc − 1)` with `β ≤ β_max`
- **THEN** `‖∂logit/∂C‖₂ ≤ β_max = 32.0`

### Requirement: Spherical L2 Normalization

The package SHALL provide `spherical_l2_normalize(z, eps=1e-6) -> Tensor` returning `z / (‖z‖₂ + eps)` along the last dimension. The default `eps` SHALL equal `1e-6`. The function SHALL be safe at `z = 0` (no NaN / Inf in output).

#### Scenario: Output on unit sphere
- **WHEN** `spherical_l2_normalize(z)` is called for arbitrary `z` with `‖z‖₂ > eps`
- **THEN** the result's `pow(2).sum(-1) == 1.0` within `1e-5`

#### Scenario: Zero-tensor safe
- **WHEN** `z = 0` is fed in
- **THEN** the output is finite (no NaN, no Inf) and equals `z / eps`

#### Scenario: Idempotence
- **WHEN** the function is applied twice in succession
- **THEN** the second application leaves the output unchanged

### Requirement: Voronoi Self-Consistency Threshold

The package SHALL provide `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` returning the closed-form Voronoi half-angle on `S^{signature_dim − 1}`, computed as the unique `θ ∈ (0, π)` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e` (regularized incomplete beta function). The package SHALL also provide `voronoi_angle(centroids: Tensor) -> float` for the offline measurement layer (computes the realized half-angle from an actual centroid tensor; NOT for use in the training hot path). At MVP `d_c = 16`, `canonical_voronoi_angle(N_e=16, d_c=16)` SHALL return ≈ 52.00° (0.9076 rad), strictly greater than the specialist-collapse boundary `θ_{1/e}(β=16) = arccos(1 − 1/β) = arccos(15/16) ≈ 20.36°`. The previous closed-form bound `arctan(π / √d_c) ≈ 38.146°` is incorrect (depends on `d_c` only, contradicts MVP geometry, and self-contradicts the same-sentence `θ_{1/e} ≈ 20.36°` value via the wrong formula `arctan(1/β) = 3.58°`); it MUST NOT appear in any implementation.

#### Scenario: MVP self-consistency
- **WHEN** `canonical_voronoi_angle(num_experts=16, signature_dim=16)` is called
- **THEN** the returned angle is `≈ 52.00°` and exceeds `θ_{1/e}(β=16) ≈ 20.36°` (the specialist-collapse boundary)

#### Scenario: N_e dependence of voronoi_angle
- **WHEN** `canonical_voronoi_angle(num_experts=64, signature_dim=16)` is called
- **THEN** the returned angle is `≈ 25.45°` (the function depends on both `num_experts` and `signature_dim`, not `signature_dim` alone)

### Requirement: C Extraction Four-Step Pipeline

The package SHALL provide `extract_C(K, V, proj_W_K, proj_W_V, proj_b, *, H_kv, d_c, eps=1e-6) -> Tensor` implementing the spec's exact four-step pipeline: (1) per-head projection `z^{l,h} = W_K^{l,h} · k^{l,h} + W_V^{l,h} · v^{l,h} + b^{l,h}`; (2) per-head spherical projection; (3) cross-head mean with `1/H_kv` factor; (4) final spherical projection. The pipeline SHALL be fully differentiable (D-path, no Straight-Through Estimator; no `.detach()` between intermediate tensors).

#### Scenario: Output shape on unit sphere
- **WHEN** `K ∈ R^{B × H_kv × N × d_k}` and `V ∈ R^{B × H_kv × N × d_k}` are fed in
- **THEN** `C ∈ R^{B × N × d_c}` and `‖C_t‖₂ = 1` for every token (within `1e-5`)

#### Scenario: Fully differentiable
- **WHEN** `torch.autograd.gradcheck` is run on `extract_C` with random `K`, `V` and the projection parameters
- **THEN** the gradient check passes with ATOL `1e-5` and no NaN

#### Scenario: Cross-head awareness
- **WHEN** `H_kv = 8` GQA input is processed
- **THEN** the cross-head mean uses the `1/H_kv` factor (mathematical equivalence to a manual `mean(..., dim=1)`)

### Requirement: Centroid Four-Phase Lifecycle Driver

The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask) -> Tensor` method MUST apply, per phase:

- Phase 0 (SEEDING): `c_i ← c_i.detach()` (driver is a no-op returning the input centroids detached from the autograd graph); `c_i.requires_grad = False`. Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds (the `‖c_i‖₂ ≡ 1.0` invariant for Phase 0 is the caller's responsibility, not the driver's).
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

### Requirement: Isotropic Squared-Chord Distance And Logit

The package SHALL provide `squared_chord(C, c_i) -> Tensor = 1 − Cᵀc_i` and `logit(C, c_i, β) -> Tensor = β · (Cᵀc_i − 1)`. The `logit` function signature SHALL NOT contain a parameter named `w_i` (A4-2 / CLAUDE.md §6 invariant). The output range of `squared_chord` SHALL be `[0, 2]`; the output range of `logit` SHALL be `[−2β, 0]`.

#### Scenario: Antipodal distance
- **WHEN** `C` and `c_i` are antipodal on `S^{d_c−1}` (e.g. `d_c = 2`, `C = [1, 0]`, `c_i = [−1, 0]`)
- **THEN** `squared_chord(C, c_i) == 2.0`

#### Scenario: Zero distance at alignment
- **WHEN** `C == c_i`
- **THEN** `squared_chord(C, c_i) == 0.0` and `logit(C, c_i, β) == 0.0`

#### Scenario: No w_i in signature
- **WHEN** `inspect.signature(logit)` is examined
- **THEN** no parameter named `w_i` (or any scalar per-expert weight) is present

### Requirement: Top-K Sparse Mask With Local Softmax

The package SHALL provide `topk_mask_with_neg_inf(logits, k) -> Tensor` masking non-top-k entries with `−float("inf")` (NOT a large finite negative). It SHALL provide `local_softmax(masked_logits) -> Tensor` that exponentiates only over the non-`-inf` entries and normalizes so `Σ_i p_i == 1` over the active set. The forward equation `x_out = x + Σ_{i ∈ I_k} p_i · Expert_i(x)` SHALL be the ONLY routing equation present in the `gating` module (grep test).

#### Scenario: Sentinel is −inf
- **WHEN** `topk_mask_with_neg_inf(logits, k=2)` is applied
- **THEN** non-top-k entries are exactly `-float("inf")` (verified via `torch.isinf` + sign check)

#### Scenario: Partition of unity
- **WHEN** `local_softmax(masked_logits)` is computed
- **THEN** `Σ_i p_i == 1.0` over the top-k active set (within `1e-6`)

#### Scenario: Zero gradient on masked entries
- **WHEN** `torch.autograd.grad(p_k, logits)` is called for masked indices
- **THEN** the gradient component is exactly `0.0`

### Requirement: Standard SwiGLU Expert With No Shared Branch

The package SHALL provide `SwiGLUExpert(cfg) -> nn.Module` whose `forward(x)` computes `(SiLU(x W^g) ⊙ x W^u) W^d`. The `SwiGLUExpert` forward signature SHALL accept ONLY `x` (no `C`, no `c_i`, no router-derived signal). The package SHALL provide `ExpertPool(cfg)` whose only public attribute is `experts: list[SwiGLUExpert]` — NO `shared` attribute, NO shared-expert slot. The `experts` module SHALL NOT import `torch.utils.cpp_extension` or `triton`.

#### Scenario: Parameter count per expert
- **WHEN** `SwiGLUExpert(MVPConfig()).parameters()` is summed
- **THEN** the count equals `3 · d_model · d_ffn = 3 · 1024 · 2048 = 6_291_456`

#### Scenario: No shared-expert slot
- **WHEN** `ExpertPool(MVPConfig())` is inspected
- **THEN** it exposes `experts` but does NOT expose `shared`, `shared_expert`, or any analogous attribute

#### Scenario: No custom kernel import
- **WHEN** `experts.py` is grepped for `cpp_extension` and `triton`
- **THEN** zero matches

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

### Requirement: Six Visualization Module Protocol Stubs

The package SHALL provide six `Protocol` stubs in `viz.py`: `PCA3D`, `DcHeatmap`, `Voronoi2D`, `TrajectoryAnimation`, `TensorBoardDashboard`, `PlantUMLDiagram`. Each SHALL expose a single method signature matching its public API (e.g. `PCA3D.render(centroids, *, camera_angles=(25.0, 135.0)) -> Figure`); `PCA3D.camera_angles` SHALL default to the tuple `(25.0, 135.0)`. The module SHALL export `IMPLEMENTATION_STACK = frozenset({"matplotlib", "scikit-learn", "scipy", "imageio", "tensorboard", "plantuml"})`. The `__all__` of `viz.py` SHALL contain exactly six module-level names.

#### Scenario: Six modules present
- **WHEN** `viz.__all__` is enumerated
- **THEN** it contains exactly six module names matching `{"PCA3D", "DcHeatmap", "Voronoi2D", "TrajectoryAnimation", "TensorBoardDashboard", "PlantUMLDiagram"}`

#### Scenario: Camera angles fixed
- **WHEN** `PCA3D.camera_angles` is inspected
- **THEN** it equals `(25.0, 135.0)` (elevation 25°, azimuth 135°)

#### Scenario: Stack pinned
- **WHEN** `viz.IMPLEMENTATION_STACK` is inspected
- **THEN** it equals the six-element frozenset above

### Requirement: Hard-Constraint Grep Invariants

The package SHALL satisfy the following source-level invariants, asserted by **literal-token grep tests** (any invariant requiring data-flow / semantic analysis is NOT a grep invariant; see Requirement "Centroid Driver Semantic Invariants" for the semantic layer):
- NO occurrence of `StraightThroughEstimator` or `straight_through` in `src/decompmoe/`
- NO occurrence of `w_i` in the body of `distance.logit` (signature-level invariant already covered)
- NO occurrence of `shared` attribute in `ExpertPool`
- NO import of `torch.utils.cpp_extension` or `triton` in `experts.py`
- NO field `kv_cache_c` in `GeometricRouter` Protocol

(The two previously-listed invariants — `.clamp_min(ε)` empty-cell denominator and the literal `arctan(pi / sqrt(d_c))` token — are removed from this Requirement because they cannot be verified by literal grep alone: the former requires data-flow analysis (the `.clamp_min` call result must be checked to be a denominator), and the latter can be circumvented by a syntactically different but semantically equivalent expression. Both invariants are restated under Requirement "Centroid Driver Semantic Invariants" where they are enforced by the corresponding named test scenario.)

#### Scenario: Hard constraints hold
- **WHEN** the literal-token grep invariants above are evaluated against `src/decompmoe/`
- **THEN** all invariants pass

### Requirement: Centroid Driver Semantic Invariants

The package's `CentroidDriver` SHALL enforce three semantic invariants that **cannot be verified by literal-token grep alone** (data-flow analysis, runtime observation, and arithmetic comparison are required). These are the **semantic counterpart** to Requirement "Hard-Constraint Grep Invariants":

1. **Empty-cell fallback (formerly grep bullet 6)**: `CentroidDriver.step(centroids, X, mask)` with `n_i = |T_i| = 0` MUST preserve `c_i^(t+1) == c_i^(t)` element-wise (no direction randomization). The driver MUST NOT use `.clamp_min(ε)` as a denominator in the empty-cell branch. Verified by `test_empty_cell_preserves_centroid` (see Requirement "Centroid Driver Invariant Test Scenarios").

2. **Spherical re-projection (driver output invariant)**: After every `CentroidDriver.step(...)` call across all four active phases, `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`. Verified by `test_spherical_norm_is_strictly_one` (see Requirement "Centroid Driver Invariant Test Scenarios").

3. **Near-zero candidate fallback**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse), `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears. Verified by `test_near_zero_candidate_fallback` (see Requirement "Centroid Driver Invariant Test Scenarios").

(Removed from the grep layer: the literal-token restriction `arctan(pi / sqrt(d_c))` is now enforced implicitly by the canonical Voronoi closed form contract in Requirement "Voronoi Self-Consistency Threshold"; grep-equivalent restrictions on the closed-form API name are added there if a future change requires them.)

#### Scenario: Semantic invariants are enforced by the named test scenarios
- **WHEN** the three named test scenarios (`test_empty_cell_preserves_centroid`, `test_spherical_norm_is_strictly_one`, `test_near_zero_candidate_fallback`) all pass
- **THEN** the empty-cell fallback, spherical re-projection, and near-zero candidate fallback invariants hold for `CentroidDriver`

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
