# wayfinder Specification (delta)

## MODIFIED Requirements

### Requirement: 4070 MVP Hyperparameter Set

The system MUST, for the 4070 8 GB MVP target, adopt `d_model = 1024`, `N_e = 16`, `k = 2`, `d_ffn = 2048`, `L = 4`, `d_c = 16`, `H = 8`, `H_kv = 8`, `d_k = 128`, `V = 32_000`. Total parameters ≈ 452 M and active parameters ≈ 100 M. The MoE active FLOPs MUST be 1:1 with a Dense baseline whose `d_ffn_dense = 4096` (each MoE token performs exactly two expert FFNs of width 2048). The geometric self-consistency check MUST hold (`θ_Voronoi > θ_{1/e}` strictly under the MVP configuration, with the closed-form residual `½ · I_{sin²θ}((d_c−1)/2, 1/2) − 1/N_e` evaluating to less than `1e-9` for the reported `θ`).

**Closed-form Voronoi half-angle (definitional layer)**: For N_e equal-area cells on `S^{d_c − 1}`, `θ_Voronoi(N_e, d_c)` is the unique `θ ∈ (0, π/2]` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e`, where `I_x(a, b)` is the regularized incomplete beta function. Equivalently, `versine_Voronoi(N_e, d_c) = 1 − cos θ_Voronoi` is the per-expert spherical **versine** (cap height, `1 − cos θ`); it MUST NOT be confused with `D_chord = √(2(1 − cos θ))` which uses the same `(1 − cos θ)` base but takes the square root to obtain chord length. MVP tabulated values (independent root-finding, residual `< 1e-9`):
- `θ_Voronoi(16, 16) ≈ 67.24° (1.1736 rad)`, `versine_Voronoi(16, 16) ≈ 0.6127`.
- `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`, `versine_Voronoi(64, 16) ≈ 0.4776`.

The canonical configuration-layer API `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` MUST return this closed-form value (computed via bisection on the equation, NOT via a hard-coded table). The measurement-layer API `voronoi_angle(centroids: Tensor) -> float` MUST compute the realized Voronoi half-angle from an actual centroid tensor (offline use only, never in the training hot path). The specialist-collapse boundary `θ_{1/e}(β) = arccos(1 − 1/β)` MUST strictly satisfy `θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16) ≈ 20.36°`.

**Parameter-count accounting (four explicit assumptions, MVP scale)**:
1. **Weight tying** — input embedding `W_emb ∈ R^{V × d_model}` is shared with `lm_head` (no extra lm_head parameter). Without tying, total grows from 452 M to ≈ 484 M.
2. **GQA degenerates to MHA at MVP scale** — `H_kv · d_k = 8 · 128 = 1024 = d_model`, so attention parameters reduce to `4 · d_model²` per layer exactly; if true GQA is later enabled (`H_kv · d_k < d_model`), the formula `P_attn/layer = 2 · d_model² + 2 · d_model · d_kv` (with `d_kv = H_kv · d_k`) MUST be used.
3. **No Q/K/V/O biases** — `W^Q, W^K, W^V, W^O` carry no bias term.
4. **Router term — exact, not rounding residual** — the low-rank routing projections `W^K, W^V ∈ R^{d_c × d_k}` (one per H_kv head) and bias `b ∈ R^{d_c}` contribute **exactly** `P_router/layer = H_kv · (2 · d_k · d_c + d_c) = 8 · (2 · 128 · 16 + 16) = 32_896` parameters, totaling `P_router = L · 32_896 = 131_584` across the model. LayerNorm gains, `β_i`, `c_i`, `W^O` are all excluded from the estimator (`MVPConfig` does not currently expose them as learnable parameters at MVP scale).

**Closed-form parameter totals**: `P_expert = 3 · d_model · d_ffn = 3 · 1024 · 2048 = 6_291_456` (SwiGLU 3-matrix); `P_total = P_emb + L · (4 · d_model² + N_e · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 100_663_296 + 32_896) = 32_768_000 + 4 · 104_890_496 = 32_768_000 + 419_561_984 = 452_329_984` exactly; `P_active = P_emb + L · (4 · d_model² + k · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 12_582_912 + 32_896) = 32_768_000 + 4 · 16_810_112 = 32_768_000 + 67_240_448 = 100_008_448` exactly.

**Source:** `wayfinder/tickets/A5-3.md`, `wayfinder/tickets/A8-1.md`, change `fix-openspec-doc-bugs` design.md (Decision 4, 8), change `fix-math-consistency-audit-2026-08` design.md (Decision 1)

#### Scenario: Active FLOPs parity
- **WHEN** MoE active FLOPs per token are computed against a Dense baseline
- **THEN** MoE per-token active FLOPs equal Dense per-token active FLOPs within the agreed alignment accounting

#### Scenario: Geometric self-consistency
- **WHEN** the boundary threshold `θ_{1/e}` is evaluated under `β = 16`
- **THEN** the per-layer Voronoi angle `θ_Voronoi(16, 16)` from `canonical_voronoi_angle(16, 16)` exceeds `θ_{1/e}` by a margin that prevents specialist collapse

#### Scenario: Voronoi angle is N_e- and d_c-dependent
- **WHEN** `canonical_voronoi_angle(N_e, d_c)` is evaluated at `(64, 16)`
- **THEN** the result is `≈ 58.47°`, distinct from `canonical_voronoi_angle(16, 16) ≈ 67.24°` (the function depends on both arguments, not `d_c` alone)

#### Scenario: Voronoi closed-form residual is bounded
- **WHEN** the returned `θ` from `canonical_voronoi_angle(N_e, d_c)` is substituted into `½ · I_{sin²θ}((d_c − 1)/2, 1/2)`
- **THEN** the residual `|½ · I_{sin²θ}((d_c − 1)/2, 1/2) − 1/N_e| < 1e-9` (proves the value is actually a root of the spec's equation, not a hard-coded constant)

---

### Requirement: Eight Geometric Quantification Metrics

The system MUST report eight metrics in two classes, each with a precise closed-form definition.

**Realtime Tier (computed every step)**
| Metric | Definition | Range / Notes |
|---|---|---|
| `L_sep` | `L_sep = (‖C^T C‖_F² − N_e) / (N_e · (N_e − 1))` (Frobenius form; equivalent `(2/(N_e(N_e−1))) · Σ_{i<j} (c_i^T c_j)²`) | References Req 12; positive scalar |
| `R_H` | `R_H = −(1 / ln N_e) · Σ_{i=1}^{N_e} f_i · ln f_i` | `f_i` = per-expert normalized routing fraction over a sliding window; `R_H ∈ [0, 1]` (1 = uniform, 0 = degenerate) |
| `S_load` | `S_load = N_e · max_{1 ≤ i ≤ N_e} f_i` | `1` at perfect uniformity, `N_e` at full collapse to a single expert |
| `UR` | `UR = (1 / N_e) · Σ_{i=1}^{N_e} I[f_i > 0]` over the most recent W = 100 steps | fraction of experts actually selected |

**Offline Tier (computed during diagnostic runs, NOT every step)**
| Metric | Definition | Range / Notes |
|---|---|---|
| `SP_i` | `SP_i = (1 / ‖T_i‖₁) · Σ_{t ∈ T_i} c_i^T C_t`; aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` (skip experts with empty `T_i`) | `T_i` = set of tokens routed to expert `i`. If `‖T_i‖₁ = 0`, `SP_i` is excluded; SP MUST NOT be reported as `0` |
| `D_chord` | `D_chord = (2 / (N_e(N_e−1))) · Σ_{i<j} √(2(1 − c_i^T c_j))` | mean spherical chord between off-diagonal centroid pairs; note: `D_chord = √(2 · versine)` |
| `MCI` | `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / \|T\|) · Σ_{t ∈ T} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`) | effective-dimensionality fraction; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `\|T\| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range); `MCI = 1.0` when `M` is proportional to identity (uniform token-distribution across the `d_c` basis), `MCI = 1/d_c` when `M` is rank-1 |
| `CG` | `CG = ‖∇_{W^{K, V, b}} L_total‖₂` | debug-only stability probe; non-negative; MUST NOT enter quality acceptance |

**Source:** `wayfinder/tickets/A8-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 8), change `fix-math-consistency-audit-2026-08` design.md (Decision 5)

#### Scenario: Realtime vs offline classification
- **WHEN** metrics are reported
- **THEN** `L_sep`, `R_H`, `S_load`, `UR` are available every step; `SP`, `D_chord`, `MCI`, `CG` are computed offline

#### Scenario: L_sep Frobenius consistency
- **WHEN** `L_sep` from the metrics module is compared to `L_sep` from the loss module under the same `c_centroids`
- **THEN** the two values are equal within `1e-6`

#### Scenario: Dead-expert SP is undefined
- **WHEN** an expert `i` has `‖T_i‖₁ = 0` in the current offline window
- **THEN** `SP_i` is reported as `undefined` (e.g. `NaN` with a `dead=True` flag, or omitted), NOT as `0.0`; the aggregated `SP` excludes this expert

#### Scenario: R_H is bounded
- **WHEN** `R_H(p)` is computed for any probability vector `p` over `N_e` experts
- **THEN** `R_H ∈ [0, 1]` within `1e-6`

#### Scenario: SP closed-form on orthonormal-aligned inputs
- **WHEN** `SP(orthonormal_centroids, assignments, signatures)` is called with every assigned token's signature exactly aligned with its centroid (`C_t = c_{a(t)}` for all `t ∈ T_i`)
- **THEN** the aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` equals `1.0` within `abs=1e-6` (each `SP_i = c_i^T c_i = 1`)

#### Scenario: SP closed-form on 60° offset
- **WHEN** `SP` is called with every assigned token's signature at `60°` from its centroid (`c_i^T C_t = cos 60° = 0.5` for all `t ∈ T_i`)
- **THEN** the aggregated `SP` equals `0.5` within `abs=1e-6`

#### Scenario: SP range bound
- **WHEN** `SP(any_centroids, any_assignments, any_signatures)` is called
- **THEN** `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6` (cosine-kernel range, exact up to FP error; SP negative when most signatures lie on the antipodal side of their centroid)

#### Scenario: D_chord closed-form on orthonormal basis
- **WHEN** `D_chord(c_centroids)` is called with `centroids ∈ R^{N_e × d_c}` forming an orthonormal subset (e.g. first `d_c` rows of `I_{d_c}` when `N_e = d_c`)
- **THEN** the result equals `sqrt(2)` within `abs=1e-6` (mean of `√(2·1)` over `c_i^T c_j = 0` pairs)

#### Scenario: MCI closed-form on uniform token distribution
- **WHEN** `MCI(token_signatures)` is called with `|T| = d_c · k` signatures, each `e_j ∈ R^{d_c}` (the `d_c` standard basis vectors) represented exactly `k` times (so the uncentered second moment `M = (1/|T|) · Σ_t C_t C_tᵀ = I/d_c` exactly)
- **THEN** the result equals `1.0` exactly within `abs=1e-12` (every dimension equally active ⇒ `Σλ̃² = 1/d_c` ⇒ `MCI = 1/(d_c · 1/d_c) = 1.0`)

#### Scenario: MCI closed-form on rank-1 token distribution
- **WHEN** `MCI(token_signatures)` is called with all `|T|` signatures equal to the same unit vector `e_1` (so `M = e_1 e_1ᵀ` is rank-1 with eigenvalues `{1, 0, ..., 0}`)
- **THEN** the result equals `1/d_c` exactly within `abs=1e-12` (one dimension active ⇒ `Σλ̃² = 1` ⇒ `MCI = 1/d_c` — the lower endpoint of the declared `[1/d_c, 1]` range, attained)

#### Scenario: CG zero-gradient invariance
- **WHEN** `CG(zero_grad)` is called with all-zero input gradient
- **THEN** the result equals `0.0` exactly within `abs=1e-12` (L2 norm of the zero vector is zero)

#### Scenario: CG positive homogeneity
- **WHEN** `CG(g)` and `CG(2·g)` are both evaluated for any non-zero gradient `g`
- **THEN** `|CG(2·g) − 2·CG(g)| < 1e-6` (L2 norm is positively homogeneous of degree 1)

---

## ADDED Requirements

### Requirement: Operational Domain γ' Reset Closed-Form Worked Example

On entering Phase 4, the system MUST reset `γ` to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so that `β^eff` is continuous at the Phase 3 → 4 boundary. The worked example for `β_{p3} = 16.0` MUST evaluate to `γ' = ln(15/16) ≈ −0.064538...`. AdamW momentum for `γ` MUST be reset on the same boundary. The closed form is pinned: `gamma_reset_for_phase4(16.0) ≈ −0.0645` within `abs=1e-4`. (References Req 7 Invariant 3 / Req 24.)

**Source:** change `fix-math-consistency-audit-2026-08` design.md (Decision 2)

#### Scenario: gamma reset is a real root of the boundary continuity equation
- **WHEN** the schedule enters Phase 4 with `β_{p3} = 16.0`
- **THEN** `γ' = ln((16 − 1) / (32 − 16)) = ln(15/16) ≈ −0.0645385...` and the resulting `β^eff(Phase 4, t=0) = 1 + 31 · σ(γ') = 16.0` exactly (continuity at the boundary)

---

### Requirement: Phase 2 β Box Equality

The operational `β_max(t)` box for Phase 2 MUST be `(1.0, 4.0)`, NOT `(1.0, 32.0)`. The Phase 3 box MUST be `(4.0, 16.0)` (unchanged from prior revisions). The configuration-layer API `phase_beta_box(phase: int) -> tuple[float, float]` MUST return these values verbatim, and MUST NOT fall through to a default `(1.0, 32.0)` for Phase 2. The schedule-time-varying API `phase_beta_max(phase, step)` MUST return the time-varying upper bound `β_max(t)` that ramps `1.0 → 4.0` across Phase 2 and `4.0 → 16.0` across Phase 3 (linear in step between box endpoints), distinct from the static `phase_beta_box(phase).hi`. (References Req 14.)

**Source:** change `fix-math-consistency-audit-2026-08` design.md (Decision 3)

#### Scenario: phase_beta_box returns the per-phase box, not the global [1, 32]
- **WHEN** `phase_beta_box(2)` is called
- **THEN** the result equals `(1.0, 4.0)` exactly
- **AND WHEN** `phase_beta_box(3)` is called
- **THEN** the result equals `(4.0, 16.0)` exactly

#### Scenario: phase_beta_max is time-varying with pinned linear convention
- **WHEN** `phase_beta_max(2, step)` is evaluated under the **pinned** linear-interpolation convention `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive (Phase 2 range `[6_000, 26_000)`, Phase 3 range `[26_000, 56_000)`)
- **THEN** the exact-value assertions at canonical step positions hold: `phase_beta_max(2, 6_000) == 1.0` (boundary start), `phase_beta_max(2, 16_000) == 2.5` (midpoint: `1 + 3·10_000/20_000`), `phase_beta_max(3, 26_000) == 4.0` (Phase 3 boundary start = box(3).lo), `phase_beta_max(3, 41_000) == 10.0` (midpoint: `4 + 12·15_000/30_000`) — all within `abs=1e-9`

---

### Requirement: Resurrection Perturbation Per-Expert Contract

The Dead Expert Splitting Resurrection pathway (Req 13) MUST perturb the **single cloned expert** (centroid and/or expert weights) — not the per-expert routing frequency vector `f_per_expert`. The perturbation API `resurrection_perturb_distribution(target_idx, *, eps_std=0.05)` MUST return a tensor whose leading dimension corresponds to a single expert slot (centroid shape `(d_c,)` for centroid perturbation, or expert-weight shape `(d_model · d_ffn,)` for weight perturbation), NOT the `(N_e,)` shape of `f_per_expert`. The accompanying `β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}` mutation MUST execute as part of the same resurrection event. (References Req 13.)

**Source:** change `fix-math-consistency-audit-2026-08` design.md (Decision 4)

#### Scenario: perturbation output shape matches a single expert slot
- **WHEN** `resurrection_perturb_distribution(target_idx=3, eps_std=0.05)` is called
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

---

### Requirement: β^eff Phase 3 → 4 Continuity Closed-Form

On entering Phase 4 with `β_{p3} = 16.0`, the operational effective β MUST equal `16.0` exactly at `t = 0` of Phase 4. This pins the closed form `β^eff(Phase 4, t=0) = 1 + 31 · σ(γ'(β_{p3}))` with `γ'(β_{p3}) = ln((β_{p3} − 1) / (32 − β_{p3}))`. The hard-clamp gradient-zero trap at the `[1.0, 32.0]` box boundary is intentionally avoided by the continuous reparameterization. **Limit-continuity note**: under the pinned `phase_end`-exclusive convention (see "Phase 2 β Box Equality"), Phase 3's `β_max` asymptotically approaches `16.0` from below as `step → 56_000⁻` (the last attainable value is `phase_beta_max(3, 55_999) = 15.9996`); the jump at the boundary is `4.0e-4`, which is small enough to be benign for gradient flow but large enough to require the limit-style wording. (References Req 7 Invariant 3 / Req 24.)

**Source:** change `fix-math-consistency-audit-2026-08` design.md (Decision 2)

#### Scenario: β^eff is continuous at Phase 3 → 4 boundary
- **WHEN** the schedule transitions from Phase 3 to Phase 4 with `β_{p3} = 16.0`
- **THEN** `β^eff(Phase 4, t=0) = 1 + 31 · σ(ln(15/16)) = 16.0` exactly, and `|β_max(Phase 3, step=55_999) − β^eff(Phase 4, step=56_000)| < 5e-4` (limit-continuity: Phase 3 `β_max` approaches `16.0` as `step → 56_000⁻`, residual at the boundary is `16.0 − 15.9996 = 4e-4`; no hard-clamp gradient-zero trap)

---

### Requirement: Closed-Form Gradient Bound Worst Case

The bound `‖∂logit/∂C‖₂ ≤ β_max = 32` in Req 7 MUST be attained (not merely bounded above) at the worst-case configuration: `β = β_max = 32`, `‖C‖₂ = 1`, `‖c‖₂ = 1`, `c ⟂ C`. Under this configuration, `logit = β · (C^T c − 1) = 32 · (0 − 1) = −32` and `∂logit/∂C = β · c / ‖C‖ = 32 · c` so `‖∂logit/∂C‖₂ = 32.0` exactly. The bound `|∂logit/∂γ| ≤ 0.5 · (β_max − β_min) = 15.95` in Req 7 MUST be attained at `γ = 0, c = −C` (so `β = 16.05`, `inner = −1`, `(β_max − β_min) · σ'(γ) · (inner − 1) = 31.9 · 0.25 · (−2) = −15.95`). (References Req 7.)

**Source:** change `fix-math-consistency-audit-2026-08` design.md (Decision 6)

#### Scenario: gradient bound is tight at orthogonal unit vectors
- **WHEN** `logit = β_max · (C^T c − 1)` with `C = e_1`, `c = e_2`, `β = β_max`
- **THEN** `‖∂logit/∂C‖₂ == 32.0` within `abs=1e-4`

#### Scenario: gamma-gradient bound is tight at antipodal config
- **WHEN** `logit = inverse_temperature(γ=0) · (inner − 1)` with `C = e_1`, `c = −e_1`
- **THEN** `|∂logit/∂γ| == 15.95` within `abs=1e-3`

---

### Requirement: Forward Formula Numerical Verification (Routing Layer)

The forward equation `x_out = x + Σ_{i ∈ I_k} p_i · Expert_i(x)` in Req 8 / Req 10 MUST hold bit-exactly under any `x`, any top-k selection `I_k`, any soft mixing `p_i`. The verification is **numerical**, not a source-grep test: given a stub `ExpertPool` whose `experts[i](x) = E_i` (fixed per expert), the gate's `x_out` MUST equal `x + Σ_{i ∈ I_k} p_i · E_i` within `1e-6`. (References Req 8.)

**Source:** change `fix-math-consistency-audit-2026-08` design.md (Decision 7)

#### Scenario: x_out is the closed-form residual add
- **WHEN** the gate emits `x_out` for fixed `x`, `I_k`, `p_i`, and stub experts `E_i`
- **THEN** `x_out == x + Σ_{i ∈ I_k} p_i · E_i` within `abs=1e-6`
