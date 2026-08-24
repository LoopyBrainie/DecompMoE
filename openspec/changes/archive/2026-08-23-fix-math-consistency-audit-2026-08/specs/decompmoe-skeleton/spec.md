# decompmoe-skeleton Specification (delta)

## MODIFIED Requirements

### Requirement: Voronoi Self-Consistency Threshold

The package SHALL provide `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` returning the closed-form Voronoi half-angle on `S^{signature_dim − 1}`, computed as the unique `θ ∈ (0, π/2]` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e` (regularized incomplete beta function). The implementation MUST compute this value via bisection on the equation (residual `< 1e-9`), NOT via a hard-coded table. The package SHALL also provide `voronoi_angle(centroids: Tensor) -> float` for the offline measurement layer (computes the realized half-angle from an actual centroid tensor; NOT for use in the training hot path). At MVP `d_c = 16`, `canonical_voronoi_angle(N_e=16, d_c=16)` SHALL return `≈ 1.1736 rad (≈ 67.24°)` (within `abs=1e-4` rad on the residual `< 1e-9` criterion), strictly greater than the specialist-collapse boundary `θ_{1/e}(β=16) = arccos(1 − 1/β) = arccos(15/16) ≈ 20.36°`. `canonical_voronoi_angle(N_e=64, d_c=16)` SHALL return `≈ 1.0205 rad (≈ 58.47°)` (within the same residual bound). The associated `versine_Voronoi = 1 − cos θ` (NOT `D_chord` which is the square root `√(2(1 − cos θ))`) is the cap height / spherical versine. The previous closed-form bound `arctan(π / √d_c) ≈ 38.146°` is incorrect (depends on `d_c` only, contradicts MVP geometry, and self-contradicts the same-sentence `θ_{1/e} ≈ 20.36°` value via the wrong formula `arctan(1/β) = 3.58°`); it MUST NOT appear in any implementation. (Matches master `wayfinder` Req 11 verbatim.)

#### Scenario: MVP self-consistency
- **WHEN** `canonical_voronoi_angle(num_experts=16, signature_dim=16)` is called
- **THEN** the returned angle satisfies `|½ · I_{sin²θ}(7.5, 0.5) − 1/16| < 1e-9` AND equals `≈ 1.1736 rad (≈ 67.24°)` AND exceeds `θ_{1/e}(β=16) ≈ 20.36°` (the specialist-collapse boundary)

#### Scenario: N_e dependence of voronoi_angle
- **WHEN** `canonical_voronoi_angle(num_experts=64, signature_dim=16)` is called
- **THEN** the returned angle satisfies `|½ · I_{sin²θ}(7.5, 0.5) − 1/64| < 1e-9` AND equals `≈ 1.0205 rad (≈ 58.47°)` (the function depends on both `num_experts` and `signature_dim`, not `signature_dim` alone)

#### Scenario: no hard-coded table values
- **WHEN** `src/decompmoe/sphere.py` is grepped for the MVP values `0.9076`, `0.4494`, `0.380`, `0.0971`
- **THEN** zero matches (no fast-path table — every input must bisect)

---

### Requirement: Total And Active Parameter Estimator

The package SHALL provide `compute_total_and_active(cfg) -> tuple[int, int]` whose first element is the total parameter count (dense embeddings + attention + all N_e SwiGLU experts + geometric router) and second element is the per-token active parameter count (attention + k experts at width `d_ffn`). Both values SHALL equal the closed-form totals exactly when `cfg == MVPConfig()`: `total == 452_329_984` and `active == 100_008_448`. The accounting MUST derive each term exactly:
- `P_emb = V · d_model = 32_000 · 1024 = 32_768_000`
- `P_attn/layer = 4 · d_model² = 4_194_304` (Q/K/V/O; GQA degenerates to MHA at MVP since `H_kv · d_k = d_model`)
- `P_expert = 3 · d_model · d_ffn = 6_291_456` (SwiGLU 3-matrix)
- `P_router/layer = H_kv · (2 · d_k · d_c + d_c) = 8 · (2 · 128 · 16 + 16) = 32_896` (W^K, W^V projections + bias; NOT a rounding residual — this is exact)
- `P_total = P_emb + L · (P_attn/layer + N_e · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 100_663_296 + 32_896) = 452_329_984`
- `P_active = P_emb + L · (P_attn/layer + k · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 12_582_912 + 32_896) = 100_008_448`

LayerNorm gains, `β_i`, `c_i`, `W^O` are excluded from the estimator (not exposed as learnable parameters in `MVPConfig` at MVP scale). (Matches master `wayfinder` Req 11 verbatim.)

#### Scenario: 452M / 100M agreement
- **WHEN** `compute_total_and_active(MVPConfig())` is called
- **THEN** the first value equals `452_329_984` exactly and the second equals `100_008_448` exactly (closed-form, no interval; each term derived from the four accounting assumptions)

---

### Requirement: Active FLOPs Parity Against Dense Baseline

The package SHALL provide `flops_per_token(cfg, arch) -> int` whose canonical per-token active-FLOPs formula is symmetric across MoE and Dense sides:
- **MoE** (per token, per layer): `FLOPs_MoE,core^(l) = 8 · d_model² + k · 6 · d_model · d_ffn^Expert` (attention Q/K/V/O + top-k SwiGLU expert FFNs).
- **Dense** (per token, per layer): `FLOPs_Dense,core^(l) = 8 · d_model² + 6 · d_model · d_ffn^Dense`.

At MVP with `d_model=1024, N_e=16, k=2, d_ffn=2048, d_ffn_dense=4096, L=4` the per-layer active-core FLOPs MUST equal `33_554_432` exactly and the `L=4` total MUST equal `134_217_728` exactly (closed-form: `8 · 1024² + 2 · 6 · 1024 · 2048 = 8_388_608 + 25_165_824 = 33_554_432` for MoE per layer; same for Dense under the parity constraint). The parity constraint `d_ffn^Dense ≡ k · d_ffn^Expert` MUST hold; at MVP this evaluates to `4096 = 2 · 2048` (exact 1:1). Explicit exclusions (symmetric on both sides, NOT in parity accounting): Attention `Q K^T` and `Attn · V` (sequence-length-dependent), and the output `lm_head`. Routing overhead is reported separately as `FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c` (≈ 66_048 FLOPs/layer at MVP, ≈ 0.20% of active-core), within the `0.3%` allowance; it MUST NOT enter parity. (Matches master `wayfinder` Req 19 verbatim.)

#### Scenario: MoE vs dense 1:1
- **WHEN** `flops_per_token(cfg, MOE_MVP)` is compared to `flops_per_token(cfg, DENSE_4096)`
- **THEN** the two active-core values are equal (exact parity); routing overhead is reported as a separate line item

#### Scenario: per-layer absolute FLOPs at MVP
- **WHEN** `flops_per_token(cfg, MOE_MVP)` is divided by `cfg.L`
- **THEN** the result equals `33_554_432` exactly (closed-form: `8 · d_model² + k · 6 · d_model · d_ffn` at MVP)

#### Scenario: total FLOPs at MVP across L=4 layers
- **WHEN** `flops_per_token(cfg, MOE_MVP)` is called with `cfg.L == 4`
- **THEN** the result equals `134_217_728` exactly (= `4 · 33_554_432`)

---

### Requirement: Standard SwiGLU Expert With No Shared Branch

The package SHALL provide `SwiGLUExpert(cfg) -> nn.Module` whose `forward(x)` computes `(SiLU(x W^g) ⊙ x W^u) W^d`. The `SwiGLUExpert` forward signature SHALL accept ONLY `x` (no `C`, no `c_i`, no router-derived signal). The package SHALL provide `ExpertPool(cfg) -> nn.Module` whose only public attribute is `experts: nn.ModuleList[SwiGLUExpert]` — NO `shared` attribute, NO shared-expert slot, NO plain-Python `list` (the container MUST be `nn.ModuleList` so `ExpertPool.parameters()` reaches the per-expert `W^g, W^u, W^d`). `ExpertPool(MVPConfig())` MUST satisfy `sum(p.numel() for p in pool.parameters()) == N_e · 3 · d_model · d_ffn == 16 · 6_291_456 == 100_663_296` exactly. The `experts` module SHALL NOT import `torch.utils.cpp_extension` or `triton`. (Matches master `wayfinder` Req 9 / Req 10 verbatim.)

#### Scenario: Parameter count per expert
- **WHEN** `SwiGLUExpert(MVPConfig()).parameters()` is summed
- **THEN** the count equals `3 · d_model · d_ffn = 3 · 1024 · 2048 = 6_291_456` exactly

#### Scenario: ExpertPool is an nn.Module with ModuleList
- **WHEN** `ExpertPool(MVPConfig())` is constructed
- **THEN** `isinstance(pool, nn.Module)` is `True` AND `isinstance(pool.experts, nn.ModuleList)` is `True`

#### Scenario: ExpertPool total parameter count
- **WHEN** `sum(p.numel() for p in ExpertPool(MVPConfig()).parameters())` is computed
- **THEN** the count equals `N_e · 3 · d_model · d_ffn = 16 · 6_291_456 = 100_663_296` exactly

#### Scenario: No shared-expert slot
- **WHEN** `ExpertPool(MVPConfig())` is inspected
- **THEN** it exposes `experts` but does NOT expose `shared`, `shared_expert`, or any analogous attribute

#### Scenario: No custom kernel import
- **WHEN** `experts.py` is grepped for `cpp_extension` and `triton`
- **THEN** zero matches

---

### Requirement: Loss Composition With Staged Lambda

The package SHALL provide `L_total(task_logits, targets, f_per_expert, p_per_expert, c_centroids, phase, step, *, cfg) -> LossParts` returning a dataclass with `.L_CE`, `.L_lb`, `.L_sep`, `.L_total` fields. The constants SHALL be: `α = 0.01` (Switch-style fixed weight on `L_lb`), `λ(t)` schedule = `0` for `phase ∈ {1, 2}`, cosine ramp `0 → 0.001` during `phase == 3`, and `0.001` fixed for `phase == 4`. The `L_lb` closed form MUST be `L_lb = N_e · Σ_i f_i.detach() · P_i`, where `P_i = (1/T) · Σ_t p_i(C_t)` is the per-expert differentiable soft routing probability; gradient MUST flow through `P_i` and be blocked through `f_i.detach()`. The previous "verified by source grep" acceptance is incorrect (permits any expression containing `.detach()`); it MUST be replaced by the testable invariant `∂L_lb / ∂P_i ≠ 0` AND `∂L_lb / ∂f_i ≡ 0`. `L_sep` SHALL equal `(‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form); the `Σ_{i<j}` equivalent form MUST use factor `2/(N_e(N_e − 1))` — the factor `1/(N_e(N_e − 1))` is INCORRECT and MUST NOT appear. (Matches master `wayfinder` Req 12 verbatim.)

#### Scenario: Alpha pinned to 0.01
- **WHEN** `L_total(...)` is evaluated with uniform `f = P = 1/N_e`
- **THEN** `L_lb_raw = N_e · Σ (1/N_e) · (1/N_e) = 1.0` exactly and the `L_lb` contribution equals `0.01 · 1.0 = 0.01` exactly regardless of phase

#### Scenario: Lambda zero in phases 1 and 2
- **WHEN** `phase ∈ {1, 2}`
- **THEN** the `L_sep` contribution is exactly `0.0` (i.e. `λ(t) == 0`)

#### Scenario: Lambda cosine ramp endpoints in phase 3
- **WHEN** `phase == 3` and `step ∈ {26_000, 41_000, 55_999}` (phase boundary, midpoint, near-end)
- **THEN** `λ(26_000) == 0.0` (cosine starts at `0`) AND `λ(41_000) ≈ 5e-4` (cosine midpoint, `0.5 · (1 − cos(π/2)) · 0.001`) AND `λ(55_999) ≈ 0.001` (cosine reaches asymptote)

#### Scenario: Lambda fixed in phase 4
- **WHEN** `phase == 4`
- **THEN** `λ(t) == 0.001` constant across `step`

#### Scenario: L_sep closed form
- **WHEN** `c_centroids ∈ R^{N_e × d_c}` is on the unit sphere AND forms an orthogonal basis (e.g. `c = I_d` truncated to `N_e` rows when `N_e = d_c`)
- **THEN** `L_sep == (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1)) == 0.0` exactly (within `abs=1e-12`)

#### Scenario: L_lb gradient flows through P_i only
- **WHEN** `L_lb` is back-propagated
- **THEN** `∂L_lb / ∂P_i ≠ 0` (differentiable through `P_i`) and `∂L_lb / ∂f_i ≡ 0` (blocked by `.detach()`)

---

### Requirement: Centroid Driver Semantic Invariants

The package's `CentroidDriver` SHALL enforce four semantic invariants that **cannot be verified by literal-token grep alone** (data-flow analysis, runtime observation, and arithmetic comparison are required). These are the **semantic counterpart** to Requirement "Hard-Constraint Grep Invariants":

1. **Empty-cell fallback**: `CentroidDriver.step(centroids, X, mask)` with `n_i = |T_i| = 0` MUST preserve `c_i^(t+1) == c_i^(t)` element-wise (no direction randomization). The driver MUST NOT use `.clamp_min(ε)` as a denominator in the empty-cell branch. Verified by `test_empty_cell_preserves_centroid`.

2. **Spherical re-projection (driver output invariant)**: After every `CentroidDriver.step(...)` call across all four active phases, `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`. Verified by `test_spherical_norm_is_strictly_one`.

3. **Near-zero candidate fallback (EMA phases 1–3)**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse) during Phases 1–3 EMA, `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears. Verified by `test_near_zero_candidate_fallback`.

4. **Near-zero candidate fallback (Phase 4 PROJECTED_SGD)**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` during Phase 4 projected SGD, the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears (the same `torch.where(use_old, prev, normalize(...))` guard pattern used in EMA must apply to Phase 4 — `centroids / ‖centroids‖.clamp_min(eps)` does NOT satisfy this invariant). Verified by `test_near_zero_candidate_fallback_phase4`.

#### Scenario: Semantic invariants are enforced by the named test scenarios
- **WHEN** the four named test scenarios (`test_empty_cell_preserves_centroid`, `test_spherical_norm_is_strictly_one`, `test_near_zero_candidate_fallback`, `test_near_zero_candidate_fallback_phase4`) all pass
- **THEN** the empty-cell fallback, spherical re-projection, and near-zero candidate fallback invariants hold for `CentroidDriver` across all four active phases

---

### Requirement: Eight Metrics And Classification

The package SHALL provide eight metric functions (`L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, `MCI`, `CG`) whose closed forms MUST match the master `wayfinder` Req 20 verbatim:

**Realtime Tier** (every step):
- `L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form).
- `R_H = −(1 / ln N_e) · Σ_i f_i · ln f_i`, normalized entropy; `R_H ∈ [0, 1]`.
- `S_load = N_e · max_i f_i`; `1` at perfect uniformity, `N_e` at full collapse.
- `UR = (1 / N_e) · Σ_i I[f_i > 0]` over the most recent W = 100 steps.

**Offline Tier** (diagnostic runs):
- `SP_i = (1 / ‖T_i‖₁) · Σ_{t ∈ T_i} c_iᵀ C_t`; aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` (skip experts with empty `T_i`). `SP ∈ [-1, 1]`.
- `D_chord = (2 / (N_e(N_e−1))) · Σ_{i<j} √(2(1 − c_iᵀ c_j))` (mean spherical chord).
- `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / |T|) · Σ_{t ∈ T} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`); **effective-dimensionality fraction**; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range). Uniform token distribution (each basis `e_j` equally represented in `T`) ⇒ `M = I/d_c` exactly ⇒ `MCI = 1.0`. Rank-1 token distribution (all `C_t = e_1`) ⇒ `M = e_1 e_1ᵀ` exactly ⇒ `MCI = 1/d_c`. The previous formula `(1/d_c) · Σ 1/λ̃²` was mathematically inconsistent with the declared range and MUST NOT appear. MCI takes **token signatures** as input (NOT centroids), per the definition.
- `CG = ‖∇_{W^{K, V, b}} L_total‖₂` (debug-only); non-negative; zero on zero gradient.

The four offline metric implementations MUST implement the closed forms above (and verify with the closed-form numerical Scenarios below — not the prior structural `!= torch.tensor(0.0)` assertion). The `OFFLINE` set in `metrics.__all__` MUST use the spec name `"D_chord"` (not the implementation alias `"D_c"`). The package SHALL expose `REALTIME = frozenset({"L_sep", "R_H", "S_load", "UR"})` and `OFFLINE = frozenset({"SP", "D_chord", "MCI", "CG"})`. `L_sep` from the metrics module SHALL be numerically equivalent to `L_sep` from the loss module under the same input. `R_H` SHALL lie in `[0, 1]` when fed a normalized probability distribution over `N_e` experts. (Matches master `wayfinder` Req 20 verbatim.)

#### Scenario: Metric classification
- **WHEN** `metrics.REALTIME ∪ metrics.OFFLINE` is computed
- **THEN** the union has cardinality exactly `8` and equals the eight metric names

#### Scenario: R_H bounded
- **WHEN** `R_H(p)` is called for any probability vector `p`
- **THEN** the result lies in `[0, 1]` within `1e-6`

#### Scenario: L_sep cross-module consistency
- **WHEN** `metrics.L_sep(c_centroids)` is compared to `loss.compute_L_sep(c_centroids)` under the same input
- **THEN** the two values are equal within `1e-6`

#### Scenario: SP closed-form on orthonormal-aligned inputs
- **WHEN** `SP(orthonormal_centroids, assignments, signatures)` is called with every assigned token's signature exactly aligned with its centroid (`C_t = c_{a(t)}` for all `t ∈ T_i`)
- **THEN** the aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` equals `1.0` within `abs=1e-6` (each `SP_i = c_i^T c_i = 1`)

#### Scenario: SP closed-form on 60° offset
- **WHEN** `SP` is called with every assigned token's signature at `60°` from its centroid (`c_i^T C_t = cos 60° = 0.5`)
- **THEN** the aggregated `SP` equals `0.5` within `abs=1e-6`

#### Scenario: SP range bound
- **WHEN** `SP(any_centroids, any_assignments, any_signatures)` is called
- **THEN** `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6`

#### Scenario: D_chord closed-form on orthonormal basis
- **WHEN** `D_chord(c_centroids)` is called with `centroids ∈ R^{N_e × d_c}` forming an orthonormal subset
- **THEN** the result equals `sqrt(2)` within `abs=1e-6`

#### Scenario: MCI closed-form on uniform token distribution
- **WHEN** `MCI(token_signatures)` is called with `|T| = d_c · k` signatures, each `e_j ∈ R^{d_c}` (the `d_c` standard basis vectors) represented exactly `k` times (so the uncentered second moment `M = (1/|T|) · Σ_t C_t C_tᵀ = I/d_c` exactly)
- **THEN** the result equals `1.0` exactly within `abs=1e-12`

#### Scenario: MCI closed-form on rank-1 token distribution
- **WHEN** `MCI(token_signatures)` is called with all `|T|` signatures equal to the same unit vector `e_1` (so `M = e_1 e_1ᵀ` is rank-1)
- **THEN** the result equals `1/d_c` exactly within `abs=1e-12`

#### Scenario: CG zero-gradient invariance
- **WHEN** `CG(zero_grad)` is called with all-zero input gradient
- **THEN** the result equals `0.0` exactly within `abs=1e-12`

#### Scenario: CG positive homogeneity
- **WHEN** `CG(g)` and `CG(2·g)` are both evaluated for any non-zero gradient `g`
- **THEN** `|CG(2·g) − 2·CG(g)| < 1e-6`

---

## ADDED Requirements

### Requirement: Beta Parameterization Operational Domain

The package SHALL provide `inverse_temperature(gamma) -> Tensor` implementing the **parameterization-space** form `β = β_min + (β_max − β_min) · σ(γ)` with `β_min == 0.1` and `β_max == 32`. The package SHALL additionally provide `phase4_inverse_temperature(gamma_p) -> Tensor` implementing the **operational-domain** form `β^eff = 1 + 31 · σ(γ')` used in Phase 4 (the parameterization-space floor `0.1` and the operational-domain floor `1.0` are intentionally decoupled — the latter prevents routing resonance at runtime, the former keeps `σ'(γ)` non-degenerate in the cold-start region). The package SHALL provide `gamma_reset_for_phase4(beta_p3) -> float` implementing `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`; the worked example `gamma_reset_for_phase4(16.0) ≈ −0.0645385...` MUST hold within `abs=1e-4`. The package SHALL provide `beta_effective(gamma, phase, step, *, cfg) -> Tensor` returning `1.0` for `phase == 1`, `Clamp(inverse_temperature(gamma), 1.0, phase_beta_max(phase, step))` for `phase ∈ {2, 3}` (where `phase_beta_max(phase, step)` is the **time-varying** schedule ramp under the **pinned** linear-interpolation convention `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive: Phase 2 range `[6_000, 26_000)` ramp `1.0 → 4.0` (so `phase_beta_max(2, 6_000) = 1.0` exact at boundary start, `phase_beta_max(2, 16_000) = 2.5` exact at midpoint, `phase_beta_max(2, 25_999) = 1 + 3·19_999/20_000 = 3.99985`); Phase 3 range `[26_000, 56_000)` ramp `4.0 → 16.0` (so `phase_beta_max(3, 26_000) = 4.0` exact at boundary start = `box(3).lo`, `phase_beta_max(3, 41_000) = 4 + 12·15_000/30_000 = 10.0` exact at midpoint, `phase_beta_max(3, 55_999) = 4 + 12·29_999/30_000 = 15.9996`). `phase_beta_max` is **distinct** from the static `phase_beta_box(phase).hi` and the `step` parameter is required), and `phase4_inverse_temperature(gamma_p)` for `phase == 4`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` (operational-domain worst case, all domains) and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (**parameterization-space** worst case `0.5 · (β_max − β_min)`; the **operational-domain Phase 4** worst case is `0.5 · 31 · 2 = 15.5` for `γ' = 0, inner = −1`; the two constants live in different domains and MUST NOT be conflated). (Matches master `wayfinder` Req 7 / Req 24 verbatim.)

#### Scenario: Parameterization endpoints
- **WHEN** `inverse_temperature(gamma)` is called with `gamma ∈ {-50, 0, 50}`
- **THEN** the result is `≈ 0.1` / `16.05` (midpoint) / `≈ 32.0` respectively within `1e-3`

#### Scenario: gamma reset for phase 4 boundary continuity
- **WHEN** `gamma_reset_for_phase4(16.0)` is called
- **THEN** the result equals `ln(15/16) ≈ −0.0645385...` within `abs=1e-4`

#### Scenario: beta_effective is continuous at Phase 3 → 4 boundary
- **WHEN** `beta_effective(gamma_p=ln(15/16), phase=4, step=56_000)` is called
- **THEN** the result equals `1 + 31 · σ(ln(15/16)) = 16.0` exactly (continuity with Phase 3's terminal `β_max`)
