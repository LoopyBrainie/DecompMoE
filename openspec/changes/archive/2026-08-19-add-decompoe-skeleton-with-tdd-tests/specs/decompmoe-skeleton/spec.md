## Purpose

Defines the observable, testable behavior of the DecompMoE skeleton: type-safe contracts (`MVPConfig`, Protocol stubs for `GeometricRouter` / `TerritoryHolder` / `BlockAdapter`) and pure-function mathematical primitives that materialize the 21 Requirements × 34 Scenarios of the main `wayfinder` spec into Python. The skeleton is formalize-only — no executable forward/backward; every public symbol carries a behavioral contract that downstream changes (training, inference, baselines) MUST honor.

## ADDED Requirements

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

The package SHALL provide `flops_per_token(arch) -> int` such that, when `arch` corresponds to the MoE MVP (`d_ffn == 2048`, `k == 2`, `N_e == 16`) the per-token active FLOPs equal those of a Dense baseline with `d_ffn_dense == 4096` (within the agreed accounting: `2 · d_model · d_ffn · 2 + d_model · d_ffn_dense · 2` is the canonical formula; the function SHALL use the same accounting on both sides).

#### Scenario: MoE vs dense 1:1
- **WHEN** `flops_per_token(MOE_MVP)` is compared to `flops_per_token(DENSE_4096)`
- **THEN** the two values are equal

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

The package SHALL provide `voronoi_angle(centroids) -> Tensor` returning `arctan(π / √d_c)` for `N_e ≥ 2` uniform-spread centroids on `S^{d_c−1}` (closed-form bound). With `d_c = 16`, the returned angle SHALL be `> θ_{1/e} ≈ 20.36°` (where `θ_{1/e} = arctan(1 / β)` for `β = 16`).

#### Scenario: MVP self-consistency
- **WHEN** `voronoi_angle(centroids_uniform(N_e=16, d_c=16))` is called
- **THEN** the angle exceeds `20.36°` (the `β = 16` specialist-collapse boundary)

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

The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask) -> Tensor` method SHALL apply: `no_grad spherical k-means` for Phase 0; masked EMA `α=0.90` for Phase 1; `α=0.95` for Phase 2; `α=0.99` for Phase 3; projected SGD with L2 retraction (`c_i ← c_i / ‖c_i‖₂`) for Phase 4. The driver SHALL expose a `should_resurrect(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/128, consec=200) -> set[int]` helper that flags expert indices whose mask-fraction `f_i` was below `1/128` for `200` consecutive steps (rate-limited to once per `1000`-step window).

#### Scenario: Phase-0 non-differentiable
- **WHEN** `CentroidDriver(SEEDING).step(...)` is called
- **THEN** no gradient is registered on the input `centroids` (`requires_grad` not propagated)

#### Scenario: Phase-1 EMA coefficient
- **WHEN** `CentroidDriver(EMA_090).step(centroids, X, mask) == 0.90 · centroids + 0.10 · masked_mean(X)` (within FP tolerance)

#### Scenario: Phase-4 re-projection
- **WHEN** `CentroidDriver(PROJECTED_SGD).step(...)` is called
- **THEN** the output `centroids` have `‖c‖₂ ≈ 1.0` after retraction

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

The package SHALL provide `L_total(task_logits, targets, f_per_expert, c_centroids, phase, step, *, cfg) -> LossParts` returning a dataclass with `.L_CE`, `.L_lb`, `.L_sep`, `.L_total` fields. The constants SHALL be: `α = 0.01` (Switch-style fixed weight on `L_lb`), `λ(t)` schedule = `0` for `phase ∈ {1, 2}`, cosine ramp `0 → 0.001` during `phase == 3`, and `0.001` fixed for `phase == 4`. The `L_lb` computation SHALL use `f_i.detach()` (verified by source grep). `L_sep` SHALL equal `(‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (equivalently `(1/(N_e (N_e−1))) · Σ_{i<j} (c_iᵀ c_j)²`).

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

### Requirement: Five Numerical Safeguard Helpers

The package SHALL provide five standalone helpers in `safeguards.py`: (1) `clip_global_grad_norm_(params, max_norm=1.0) -> Tensor` returning the pre-clip norm; (2) `nan_ladder(consecutive_nan) -> tuple[str, float, bool]` returning `(action, lr_scale, halt)` where `action ∈ {"skip", "halve_lr", "halt"}` for counts `(1, 3, 10)` respectively; (3) `should_resurrect(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/128, consec=200) -> set[int]` rate-limited to once per 1000 steps; (4) `beta_saturation_warning(β_per_expert, *, β_max=32) -> bool` returning `True` when any `β_i > 0.95 · β_max = 30.4`; (5) `loss_spike_defense(L_task, L_task_ema, phase, *, ratio=2.5) -> bool` returning `True` and signalling `LR × 0.8` when `phase ≥ 3 and L_task > ratio · L_task_ema`. The standard step order SHALL be: `Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i)` (asserted via documented ordering constant `STEP_ORDER`).

#### Scenario: Global clip threshold
- **WHEN** `clip_global_grad_norm_(params, max_norm=1.0)` is called with `‖g‖₂ > 1.0`
- **THEN** all gradients are scaled to `‖g‖₂ ≤ 1.0`

#### Scenario: NaN escalation ladder
- **WHEN** `nan_ladder(c)` is called for `c ∈ {1, 3, 10}`
- **THEN** the returned tuple is `("skip", 1.0, False)` / `("halve_lr", 0.1, False)` / `("halt", 1.0, True)` respectively

#### Scenario: Resurrection rate-limited
- **WHEN** two dead-expert events occur within the same 1000-step window
- **THEN** only one resurrection is emitted; the second is deferred (the helper returns at most one set of indices per call respecting the rate limit)

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

The package SHALL provide `phase_id(step: int) -> int` returning `0` for `step ∈ [0, 999]`, `1` for `[1_000, 5_999]`, `2` for `[6_000, 25_999]`, `3` for `[26_000, 55_999]`, `4` for `[56_000, 100_000]`. The package SHALL provide `phase_step_frozen_names(phase: int) -> set[str]` returning the parameter-name set to freeze per phase (`{"c_i", "beta_i", "W_K", "W_V", "b"}` for phase 1; `{"W_g", "W_u", "W_d"}` for phase 2; empty for phases 0/3/4). The package SHALL provide `should_reset_adam(prev_phase: int, next_phase: int) -> bool` returning `True` exactly when `prev_phase == 3 and next_phase == 4`. The advisory signals (`R_H`, `S_load`, `R_β-sat`, `L_sep/WB`) SHALL be exposed via `advisory_signals(...)` but SHALL NEVER trigger phase transitions (state-machine invariance under perturbed advisory is asserted).

#### Scenario: Phase boundaries at 100K
- **WHEN** `total_steps == 100_000`
- **THEN** the phase boundaries are `(1_000, 6_000, 26_000, 56_000, 100_000)` and phase `0 / 1 / 2 / 3 / 4` step ratios are `1% / 5% / 20% / 30% / 44%`

#### Scenario: Phase-1 router freeze
- **WHEN** `phase_step_frozen_names(1)` is called
- **THEN** the result equals `{"c_i", "beta_i", "W_K", "W_V", "b"}`

#### Scenario: Phase-2 expert freeze
- **WHEN** `phase_step_frozen_names(2)` is called
- **THEN** the result equals `{"W_g", "W_u", "W_d"}`

#### Scenario: Adam reset boundary
- **WHEN** `should_reset_adam(3, 4)` is called
- **THEN** it returns `True`; for every other `(prev, next)` pair it returns `False`

### Requirement: Eight Metrics And Classification

The package SHALL provide eight metric functions (`L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_c`, `MCI`, `CG`) and SHALL expose `REALTIME = frozenset({"L_sep", "R_H", "S_load", "UR"})` and `OFFLINE = frozenset({"SP", "D_c", "MCI", "CG"})`. `L_sep` from the metrics module SHALL be numerically equivalent to `L_sep` from the loss module under the same input. `R_H` SHALL lie in `[0, 1]` when fed a normalized probability distribution over `N_e` experts.

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

The package SHALL satisfy the following source-level invariants, asserted by grep tests:
- NO occurrence of `StraightThroughEstimator` or `straight_through` in `src/decompmoe/`
- NO occurrence of `w_i` in the body of `distance.logit` (signature-level invariant already covered)
- NO occurrence of `shared` attribute in `ExpertPool`
- NO import of `torch.utils.cpp_extension` or `triton` in `experts.py`
- NO field `kv_cache_c` in `GeometricRouter` Protocol

#### Scenario: Hard constraints hold
- **WHEN** the grep invariants above are evaluated against `src/decompmoe/`
- **THEN** every constraint returns zero matches