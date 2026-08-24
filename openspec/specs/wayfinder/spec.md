# wayfinder Specification

## Purpose
将 DecompMoE（"decomposed Mixture of Experts"）的设计资产以 OpenSpec capability 形式固化，作为 Decoder-Only Llama 框架内 Post-FFN 几何路由（geometric routing）的唯一形式化真相源。该 capability 覆盖命名/术语、拓扑挂载点、C 签名提取算子、几何门控、专家结构、损失与数值稳定、5 阶段时间驱动调度、Prefill/Decode 解耦推理、6 类 baseline 与 8 项几何量化指标；显式排除 Linear Attention / SSM / RNN、训练执行、论文写作与从 dense / 其他 MoE 的 checkpoint 转换。

## Requirements

<a id="req-1"></a>

### Requirement: Naming And Alias Convention

The system MUST adopt **DecompMoE** as the canonical project name and MUST preserve **GeoMoE** as a documented alias.

**Source:** `wayfinder/tickets/A0-1.md`

#### Scenario: Canonical reference resolution
- **WHEN** any artifact, doc, or code comment refers to the project
- **THEN** the reference uses "DecompMoE" as the primary name, with "GeoMoE" only as a secondary alias inside design prose

<a id="req-2"></a>

### Requirement: Formal Symbols And Code Naming

The system MUST use formal symbol `Σ_i` (per-expert covariance), `P_i = Σ_i^{-1}` (precision matrix), and the subscript convention `(i, l, h, t)` for expert / layer / head / token. Under per-layer head-aggregation, head subscript `h` MUST be elided and symbols MUST collapse to per-layer `C_t^l`, `c_i^l`, `Σ_i^l`, `P_i^l`. Code identifiers MUST map to: `GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding`, `territory_collapse`.

**Source:** `wayfinder/tickets/A1-1.md`, `wayfinder/tickets/A2-2.md`

#### Scenario: Notation is unambiguous
- **WHEN** a formula appears in a spec, design, or doc
- **THEN** the formula uses the locked subscripts and matches the code-identifier mapping table

<a id="req-3"></a>

### Requirement: Post-FFN Geometric Mount Point

The system MUST mount the geometric routing chain at the **Post-FFN** position of each Decoder-Only Llama block. The system MUST NOT introduce Pre-Attention Dynamic Bias as a routing mechanism. FlashAttention, PagedAttention, and expert-parallel frameworks MUST remain untouched.

**Source:** `wayfinder/tickets/A2-1.md`

#### Scenario: Mount point preserves attention subsystem
- **WHEN** the routing chain executes for a token
- **THEN** it consumes the Post-FFN residual stream output and produces a residual-stream add, leaving Q/K/V paths and the attention subsystem unmodified

#### Scenario: Pre-Attention Dynamic Bias is out of scope
- **WHEN** the spec is reviewed
- **THEN** Pre-Attention Dynamic Bias appears only in Future Work notes and not as an active requirement

<a id="req-4"></a>

### Requirement: Layer-Wise Head-Aggregated Routing

The system MUST compute **one** per-layer territory signature `C_t^l ∈ S^{d_c-1}` by aggregating the per-head projected-and-normalized signatures with a cross-head mean. Per-head territory routing and cross-layer KV conditioning MUST NOT be in scope.

**Source:** `wayfinder/tickets/A2-2.md`

#### Scenario: One C per layer per token
- **WHEN** a token passes through layer `l`
- **THEN** exactly one `C_t^l` exists and is consumed by the gating function of layer `l`

<a id="req-5"></a>

### Requirement: Spherical Normalized C Extraction

The system MUST extract `C_t^l` using a four-step pipeline that enforces spherical geometry throughout: (1) per-head low-rank projection `z_t^{l,h} = W_{l,h}^K · k_t^{l,h} + W_{l,h}^V · v_t^{l,h} + b_{l,h}`; (2) per-head spherical projection `C_t^{l,h} = z_t^{l,h} / (||z_t^{l,h}|| + ε)`; (3) cross-head mean `z̄_t^l = (1/H_kv) · Σ_h C_t^{l,h}`; (4) final spherical projection `C_t^l = z̄_t^l / (||z̄_t^l|| + ε)`. The pipeline MUST be Grouped-Query-Attention aware (using `H_kv`). The per-token time complexity MUST be `O(H_kv · d_c · d_k)` and space MUST be `O(d_c)`.

**Source:** `wayfinder/tickets/A3-1.md`

#### Scenario: Output stays on the unit sphere
- **WHEN** the pipeline produces `C_t^l`
- **THEN** `||C_t^l||₂ = 1` (within floating-point tolerance) and `C_t^l ∈ S^{d_c-1}`

#### Scenario: Complexity budget holds
- **WHEN** `H_kv`, `d_c`, `d_k` are concrete values (e.g. `H_kv=8, d_c=16, d_k=128`)
- **THEN** per-token compute is O(`H_kv · d_c · d_k`) and resident memory for the activation is O(`d_c`)

<a id="req-6"></a>

### Requirement: C Extraction Differentiability And Centroid Lifecycle

The system MUST compute the extraction in a fully differentiable manner (the D-path, no Straight-Through Estimator). The per-expert territory centroids `c_i^l` MUST evolve through a five-phase dual-channel lifecycle, strictly separating two orthogonal update channels:

**Driver Channel (CentroidDriver, gradient-free)**: responsible for centroid updates under explicit, deterministic rules.
- **Phase 0** — Spherical K-Means seeding (no gradient, no EMA): `c_i^(t+1) = KMeans(C)` initialization.
- **Phase 1** — Masked Spherical EMA at `α = 0.90` (`c_i^(t+1) = Normalize(0.90·c_i^(t) + 0.10·m_i^(t))`); driver channel Active; this is the "Fast Adapt (Warmup)" stage.
- **Phase 2** — Masked Spherical EMA at `α = 0.95` (`c_i^(t+1) = Normalize(0.95·c_i^(t) + 0.05·m_i^(t))`); driver channel Active; "Coarse Align" stage.
- **Phase 3** — Masked Spherical EMA at `α = 0.99` (`c_i^(t+1) = Normalize(0.99·c_i^(t) + 0.01·m_i^(t))`); driver channel Active; "High-Inertia Annealing (Pre-SGD)" stage.
- **Phase 4** — Projected SGD + L2 re-projection (`c_i^(t+1) = c_i^(t) − η·grad_c_i L_routing`, then `c_i^(t+1) ← c_i^(t+1) / ‖c_i^(t+1)‖₂`); driver channel Active and under gradient descent.

**Gradient Channel (AdamW optimizer)**: governs `c_i.requires_grad` and across-P AdamW registration. Phase 0–3 the gradient channel is **Frozen** (`c_i.requires_grad = False`, `c_i` NOT in AdamW parameter group). Phase 4 the gradient channel is **Active** (`c_i.requires_grad = True`, `c_i` IS in AdamW parameter group). Freezing the gradient channel MUST NOT propagate to the driver channel — Phase 1–3 driver channel remains Active even when the gradient channel is Frozen.

**Empty-Cell Invariant (Invariant 1)**: If for any expert `i` the assigned token count in the current batch `n_i = |T_i| = Σ_t I[i ∈ Top-k(C_t)]` is zero, the per-expert mean MUST default to the previous centroid: `m_i^(t) ≡ c_i^(t−1)`, which yields `c_i^(t+1) = c_i^(t)`. The implementation MUST NOT use `assignment_mask.sum().clamp_min(1e-9)` style normalization; such normalization introduces direction randomization on empty cells and breaks Dead Expert Resurrection.

**Spherical Re-projection Invariant (Invariant 2)**: After every driver-channel update, the centroid MUST satisfy `‖c_i^(t+1)‖₂ ≡ 1.0`. If the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse), the implementation MUST fall back to the previous centroid `c_i^(t+1) = c_i^(t)` to prevent NaN and preserve the geometric boundedness of `logit = β·(C^T c − 1) ∈ [−2β, 0]`.

**Source:** `wayfinder/tickets/A3-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: No STE in forward or backward
- **WHEN** gradients are back-propagated through the extraction
- **THEN** every step of the pipeline contributes a finite gradient; no surrogate (STE) is inserted between `z` and `C`

#### Scenario: Phase transition updates the centroid driver
- **WHEN** training crosses a phase boundary defined in the schedule
- **THEN** the driver-channel update rule switches (K-Means → EMA 0.90 → EMA 0.95 → EMA 0.99 → Projected SGD) without altering the extraction math; the gradient-channel `requires_grad` flag switches from `False` (Phases 0–3) to `True` (Phase 4) at the Phase 3 → Phase 4 boundary

#### Scenario: Empty-cell preserves centroid
- **WHEN** the driver channel receives a batch with `n_i = 0` for some expert `i`
- **THEN** `c_i^(t+1) == c_i^(t)` element-wise within FP tolerance (no direction randomization, no `.detach()` boundary leak)

#### Scenario: Spherical re-projection holds after every update
- **WHEN** the driver channel completes a step in any Phase
- **THEN** `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, `c_i^(t+1) == c_i^(t)` and no NaN is produced

<a id="req-7"></a>

### Requirement: Isotropic Squared-Chord Distance And Bounded Beta

The system MUST measure distance between `C_t^l` and `c_i^l` using the isotropic squared-chord distance `d(C, c_i) = 1 − C^T c_i ∈ [0, 2]`. The system MUST parameterize the inverse-temperature using the **parameterization-space** form `β^param(γ) = β_min + (β_max − β_min) · Sigmoid(γ)` with `β_min = 0.1` and `β_max = 32`. The corresponding logit MUST be `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The system MUST bound `‖∂logit/∂C‖₂` and `‖∂logit/∂c_i‖₂` by ` ≤ β_max = 32`, and `|∂logit/∂γ_i|` by ` ≤ 0.5(β_max − β_min) = 15.95`, as hard numerical-stability guarantees derived from ticket A4-1.

**Operational-domain override (Invariant 3)**: per-phase effective β MUST be:
- **Phase 1**: `β^eff = 1.0` (fixed, regardless of `γ`).
- **Phase 2–3**: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase-driven schedule (`1.0 → 4.0` in Phase 2, `4.0 → 16.0` in Phase 3).
- **Phase 4**: `β^eff = 1.0 + 31.0 · Sigmoid(γ')` — continuous reparameterization. On entering Phase 4, `γ` MUST be reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum MUST be reset for `γ` (per A6b-1).

`β_min = 0.1` exists to keep `σ'(γ)` non-degenerate in the parameterization space (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.0284`). The operational-domain floor `1.0` in Phase 4 is independent and exists to prevent routing resonance.

Per-expert scalar weights `w_i` MUST NOT appear in the logit; the mixing weight for top-k routing IS the softmax probability `p_i` (per A4-2 and CLAUDE.md §6). `w_i` MUST NOT appear in any stage, in any formulation, in any reserved form.

**Source:** `wayfinder/tickets/A4-1.md`

#### Scenario: Distance is bounded and gradient-safe
- **WHEN** any `(C, c_i)` pair on the unit sphere is fed into the gating function
- **THEN** the distance lies in `[0, 2]` and the per-component gradient magnitude stays below or equal to `β_max = 32`

#### Scenario: w_i is absent from the logit
- **WHEN** the logit is computed for gating
- **THEN** no learnable per-expert scalar weight `w_i` participates in `logit = β(C^T c − 1)`; mixing weights are exactly the softmax probabilities `p_i`

<a id="req-8"></a>

### Requirement: Top-K Sparse Mask With Local Softmax Gating

The system MUST route each token through exactly **k = 2** experts using a pure geometric convex combination. The forward equation MUST be `x_out = x + Σ_{i ∈ I_k} p_i · Expert_i(x)` where `I_k` is the top-k logit index set and `p_i = softmax(logit_j)_{j ∈ I_k}` is a local softmax restricted to `I_k`, guaranteeing `Σ p_i ≡ 1`. Non-top-k experts MUST be masked with logit `−∞` (a non-finite sentinel, not a large negative finite value) so their probabilities and gradients are exactly zero without a Straight-Through Estimator.

**Source:** `wayfinder/tickets/A4-2.md`

#### Scenario: Native sparse sub-gradient
- **WHEN** back-propagation reaches the masking step
- **THEN** non-top-k experts receive exactly zero gradient; top-k experts receive standard softmax-Jacobian gradients

#### Scenario: Convex combination constraint
- **WHEN** the gate emits `p_i`
- **THEN** `Σ_{i ∈ I_k} p_i = 1.0` and the residual stream add is `x + Σ p_i · Expert_i(x)`

<a id="req-9"></a>

### Requirement: Standard SwiGLU FFN Expert

The system MUST implement each expert as a Standard SwiGLU FFN, isomorphic to the Llama baseline FFN: `Expert_i(x) = (SiLU(x W_i^g) ⊙ x W_i^u) W_i^d`. Each expert MUST consume `3 · d_model · d_ffn` parameters and `k · 3 · d_model · d_ffn` activations per routed token. The expert MUST receive zero `C`-derived injection, so that performance differences are attributable solely to the routing chain (A0–A4). The system MUST NOT introduce a custom kernel for the SwiGLU FFN; standard vLLM / Megatron / DeepSpeed SwiGLU kernels MUST be reusable.

**Source:** `wayfinder/tickets/A5-1.md`

#### Scenario: No C injection inside experts
- **WHEN** `Expert_i(x)` is computed
- **THEN** the input `x` is the Post-FFN residual stream at the mount point and no `C` or `c_i` derived signal enters the expert

#### Scenario: SwiGLU kernel reuse
- **WHEN** the system is deployed on a supported framework
- **THEN** the SwiGLU FFN runs through that framework's fused SwiGLU kernel with no custom CUDA / / retargeting replacement

<a id="req-10"></a>

### Requirement: No Shared Expert (Pure Geometric Routing)

The system MUST NOT include a shared expert. The forward equation MUST remain exactly `x_out = x + Σ_{i ∈ I_k} p_i · Expert_i(x)`. The system MUST preserve three mathematical guarantees: (1) no variance drift `Var[Δx | x] ≤ σ_e²`; (2) no slot encroachment between experts; (3) alignment with Mixtral's active-parameter accounting. The guarantees depend on the dual premise that experts are independently initialized and the training run is long enough for them to differentiate; the cross-covariance being approximately zero is a derived property, not an enforced one.

**Source:** `wayfinder/tickets/A5-2.md`

#### Scenario: Forward formula strictness
- **WHEN** the routing layer is reviewed
- **THEN** the only summand over experts is `Σ_{i ∈ I_k} p_i · Expert_i(x)`;` no separate shared branch exists

<a id="req-11"></a>

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
<a id="req-12"></a>

### Requirement: Loss Composition

The system MUST train with `L_total = L_CE + α · L_lb + λ(t) · L_sep`, where `α = 0.01` is the Switch-style fixed weight on `L_lb`, and `λ(t)` follows a staged schedule: `0` in Phases 1–2, a cosine ramp from `0` to `0.001` during Phase 3, and `0.001` fixed in Phase 4.

**L_lb closed form**: `L_lb = N_e · Σ_i f_i.detach() · P_i`, where `f_i ∈ [0, 1]` is the per-expert hard routing fraction (averaged over the batch), `f_i.detach()` blocks gradient flow through `f_i`, and `P_i = (1/T) · Σ_t p_i(C_t)` is the per-expert differentiable soft routing probability averaged over the T tokens. The gradient path MUST run through `P_i` only (back into `logit → (C, c_i, β)`); `f_i` is treated as a non-differentiable importance weight.

**L_sep closed form (canonical Frobenius form)**: `L_sep = (‖C^T C‖_F² − N_e) / (N_e · (N_e − 1))`. The diagonal of `C^T C` contributes `N_e · 1` to the squared Frobenius norm (subtracted out), and each off-diagonal pair `(c_i, c_j)` with `i ≠ j` is counted twice (once as `(i, j)`, once as `(j, i)`). The equivalent `Σ_{i<j}` form MUST be `L_sep = (2/(N_e(N_e − 1))) · Σ_{i<j} (c_i^T c_j)²`; the `Σ_{i<j}` form with factor `1/(N_e(N_e − 1))` (half the canonical) is INCORRECT and MUST NOT appear.

The system MUST keep the notation distinction between per-token `C_t^l` and per-expert `C` matrix unambiguous.

**Source:** `wayfinder/tickets/A6a-1.md`

#### Scenario: Phase-driven lambda schedule
- **WHEN** training progresses through the schedule
- **THEN** `λ(t)` equals the staged values (0 / cosine ramp / 0.001 fixed) and the separation term is never non-zero in Phases 1–2

#### Scenario: L_lb gradient flows through P_i
- **WHEN** `L_total` is back-propagated
- **THEN** `∂L_lb / ∂P_i ≠ 0` (the `P_i` path is differentiable), while `∂L_lb / ∂f_i ≡ 0` (the `f_i.detach()` path is blocked)

#### Scenario: L_sep closed form (Frobenius)
- **WHEN** `c_centroids ∈ R^{N_e × d_c}` lies on the unit sphere
- **THEN** `L_sep == (‖C^T C‖_F² − N_e) / (N_e · (N_e − 1))` within `1e-6`; the diagonal `N_e` term is subtracted exactly once

<a id="req-13"></a>

### Requirement: Numerical Safeguards

The system MUST execute the standard training step as `Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i)`, which is a first-order Riemannian SGD equivalent on the spherical constraint. The system MUST implement all five safeguards: (1) Global Gradient Clipping at threshold `1.0` covering all learnable parameters; (2) NaN Detection & Escalation with `1 skip → 3 consecutive NaN trigger LR ÷ 10 → 10 consecutive NaN halt training`; (3) Dead Expert Splitting Resurrection triggered when `f_i^avg < 1 / (2 · N_e)` for 200 consecutive steps (clones `j* = argmax f_j^avg`, perturbs with `ε ~ N(0, 0.05² I)`, sets `β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`, rate-limited to once per 1000 steps). At MVP scale `N_e = 16`, `1/(2 · N_e) = 1/32`; the rule is `f_threshold = 1/(2 · N_e)` parameterized by `N_e`, not a hardcoded `1/128` from a prior `N_e = 64` design; (4) β Saturation Guard with warning at `β_i > 30.4` (95% of `β_max`) and global `LR ÷ 2` when more than 50% of experts have `β_i > 28.8` (90% of `β_max`); (5) Loss Spike Defense in Phase 3+ with `L_task > 2.5 · EMA(L_task)` triggering `LR × 0.8`.

**Source:** `wayfinder/tickets/A6a-2.md` (historical, threshold `1/128`), change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold superseded by `1/(2·N_e)`)

#### Scenario: Standard step ordering
- **WHEN** a training step completes
- **THEN** the order is `Backward → clip(1.0) → step → L2_norm(c_i)` and `c_i` lies on the unit sphere after the step

#### Scenario: NaN escalation ladder
- **WHEN** consecutive NaN step counts are 1, 3, and 10 respectively
- **THEN** the responses are: skip + zero_grad (+ AMP scaler decay); `LR ÷ 10`; halt and alert

#### Scenario: Resurrection respects rate limit
- **WHEN** two experts meet the dead-expert trigger within the same 1000-step window
- **THEN** only one resurrection event executes; the second is deferred

#### Scenario: Beta saturation guard
- **WHEN** any single executor reaches `β_i > 30.4` or more than 50% of experts cross `β_i > 28.8`
- **THEN** the system logs a warning or halves the global learning rate respectively

<a id="req-14"></a>

### Requirement: Five-Phase Time-Driven Schedule

The system MUST partition training into five phases with the fixed duration ratios `1% / 5% / 20% / 30% / 44%` (i.e., 1 K / 5 K / 20 K / 30 K / 44 K steps under a 100 K total). The phase boundary timestamps MUST be `1 K / 6 K / 26 K / 56 K / 100 K`. Phase 0 MUST be Spherical K-Means seeding (driver Active, gradient Frozen). Phase 1 MUST freeze the gradient channel for `(c_i, β_i, W^K, W^V, b)` and train the expert FFNs only, with `L_lb` logged but not back-propagated; the driver channel remains Active and executes Masked Spherical EMA at `α = 0.90`. Phase 1 β MUST be 1.0 (fixed). Phase 2 MUST freeze the gradient channel for `(c_i, β_i)` (unfreezing `W^{K, V, b}`), train the router via driver-channel Masked Spherical EMA at `α = 0.95`, with operational `β` ramping `1.0 → 4.0` and Dead Expert Resurrection active. Phase 3 MUST continue router training via driver-channel Masked Spherical EMA at `α = 0.99`, with operational `β` ramping `4.0 → 16.0`, `λ(t)` cosine-ramping `0 → 0.001`, and Loss Spike Defense plus β Saturation Guard active; the gradient channel remains Frozen for `(c_i)` (only `β_i` is unfrozen). Phase 4 MUST unfreeze the entire gradient channel (small learning rate), use Projected SGD + L2 re-projection for `c_i`, switch to the continuous reparameterization `β^eff = 1 + 31 · σ(γ')` (with `γ'` reset on entry for continuity, see Req 7 Invariant 3), fix `λ = 0.001`, and MUST reset Adam's momentum state at the Phase 3 → 4 boundary.

**Source:** `wayfinder/tickets/A6b-1.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: Phase boundary timestamps
- **WHEN** training crosses 1 K, 6 K, 26 K, 56 K, or 100 K steps
- **THEN** the system transitions to Phase 1, 2, 3, 4, or END respectively

#### Scenario: Adam momentum reset on Phase 4 entry
- **WHEN** the schedule enters Phase 4
- **THEN** Adam's first and second moment buffers for all learnable parameters are reset before the first Phase 4 step, and `γ` is reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary

#### Scenario: Gradient channel Frozen does not block driver channel
- **WHEN** training is in Phase 1, 2, or 3 with the gradient channel Frozen for the relevant parameter
- **THEN** the driver channel still updates `c_i` via Masked Spherical EMA (Phases 1–3) at the prescribed `α`, while `c_i.requires_grad = False`; `c_i` is NOT registered in the AdamW parameter group

<a id="req-15"></a>

### Requirement: Hybrid Three-Layer Phase Triggers

The system MUST combine three trigger layers: (Layer 1) Time-Driven hard cut at the 1 K / 6 K / 26 K / 56 K / 100 K boundaries; (Layer 2) State-Driven Advisory signals — normalized entropy `R_H`, load skew `S_load`, β saturation ratio `R_β-sat`, and overlap index `L_sep / WB` — read-only and advisory only (never auto-trigger a transition); (Layer 3) Hard Cutoff at 100 K steps. Real-time monitoring of `D_c` (per-expert geodesic spread) MUST be excluded;` `D_c` remains an offline metric due to its `O(N_e²)` cost and unstable threshold.

**Source:** `wayfinder/tickets/A6b-2.md`

#### Scenario: Advisory signals not to auto-trigger
- **WHEN** an advisory signal crosses any threshold before its corresponding time-driven boundary
- **THEN** the system logs the advisory but nots NOT advance the phase

<a id="req-16"></a>

### Requirement: Prefill And Decode Share The Same Algorithm

The system MUST use the same extraction algorithm for Prefill and Decode with zero branching. The system MUST project onto `(L')` and apply two spherical normalizations in both modes. The system MUST NOT write `C_t^l` into the KV Cache. During Decode, `C_t^l` MUST live in SRAM / registers only (16 floats = 64 bytes per layer per token for `d_c = 16`);` during Prefill, `C_t^l` MAY live in HBM because the backward graph must retain it.

**Source:** `wayfinder/tickets/A7-1.md`

#### Scenario: Single algorithm path
- **WHEN** the extraction runs in Prefill or Decode mode
- **THEN** the same four-step pipeline executes;` only the residency (SRAM vs HBM) and the backward-graph retention differ

<a id="req-17"></a>

### Requirement: Stateless Per-Frame C Recomputation

The system MUST recompute `C_t^l` every Decode step from `(K_t, V_t)` with no carry-over state, using the formula `C_t = L2_Norm((1/H_kv) · Σ_h L2_Norm(W_h^K k_t^{(h)} + W_h^V v_t^{(h)} + b_h))`. The recomputation MUST cost approximately 65.5 K FLOPs per token (with `H_kv = 8`, `d_k = 128`, `d_c = 16`) and MUST introduce 0 bytes of additional HBM traffic because all activations fit in registers / SRAM. The recomputation MUST keep C-extraction overhead under 0.5% of total decoder latency.

**Source:** `wayfinder/tickets/A7-2.md`

#### Scenario: No C caching
- **WHEN** a Decode step completes
- **THEN** no per-token C state survives into the next step;` the next step recomputes from fresh `(K_t, V_t)`

#### Scenario: Decoder latency budget
- **WHEN** decoder latency is profiled on the MVP configuration
- **THEN** the C-extraction slice is below 0.5% of total decoder time

<a id="req-18"></a>

### Requirement: Hardware And Kernel Friendliness

The system MUST keep `W_proj = {W^K, W^V, b}` (≈ 64 KB in BF16) 100% resident in L2 cache and the activations (`z`, `ẑ`, `z̄`, `C`, ≈ 4 KB total) 100% resident in SRAM / registers, with zero additional HBM traffic attributable to the geometric routing chain. The system MUST be compatible — without custom kernels — with FlashDecoding, PagedAttention, vLLM, TGI, SGLang, TensorRT-LLM, Megatron-LM, and DeepSpeed-MoE. `torch.compile` is an optional optimization path (Inductor can auto-fuse the four native ops) but MUST NOT be required for MVP correctness.

**Source:** `wayfinder/tickets/A7-3.md`

#### Scenario: No custom kernel required
- **WHEN** the system runs under any supported framework
- **THEN** it operates correctly using the framework's standard fused SwiGLU kernel and standard attention kernels with no project-specific CUDA or retargeting replacement

#### Scenario: Zero HBM delta
- **WHEN** HBM traffic is profiled for the geometric routing chain
- **THEN** the additional HBM bytes per token attributable to the chain equal zero (all intermediate state is on-chip)

<a id="req-19"></a>

### Requirement: Six Baseline Set On 4070 MVP

The system MUST, for evaluation on the 4070 8 GB MVP, hold active FLOPs strictly 1:1 between the MoE system and the Dense baseline, and MUST report results against six baselines: (Primary, E) Dense SwiGLU `d_ffn = 4096`; (Primary, M′) Mixtral reproduction with `N_e = 8`, `k = 2`; (Primary, Q1) Qwen1.5-MoE-A2.7B compressed via QLoRA; (Direct, G) GMoE with X-space Euclidean distance; (Ablation, R) Random Routing; (Ablation, S′) Random Centroids (isolates the centroid-learning contribution per A3-2).

**Active-Core FLOPs canonical formula (per token, per layer)**:
- MoE: `FLOPs_MoE,core^(l) = 8 · d_model² + k · 6 · d_model · d_ffn^Expert` (attention Q/K/V/O + top-k SwiGLU expert FFNs).
- Dense: `FLOPs_Dense,core^(l) = 8 · d_model² + 6 · d_model · d_ffn^Dense`.

**Parity constraint**: `d_ffn^Dense ≡ k · d_ffn^Expert`. At MVP this is `4096 = 2 · 2048`, yielding exact 1:1 parity.

**Explicit exclusions** (symmetric on both sides, hence not in parity accounting):
- Attention `Q K^T` and `Attn · V` (sequence-length-dependent, `4 · S · d_model` per layer).
- Output lm_head (`2 · d_model · V_vocab`).

**Routing overhead, reported separately (not part of parity)**:
`FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c`, where `4 · d_c · H_kv · d_k` accounts for the `W^K, W^V` low-rank projections (each projection is a forward GEMM of `2 · H_kv · d_k · d_c`; two projections sum to `4 · d_c · H_kv · d_k`), and `2 · N_e · d_c` accounts for the gating similarity dot product `C^T c_i`. At MVP this evaluates to `4·16·8·128 + 2·16·16 = 65_536 + 512 = 66_048` FLOPs/layer; `L = 4` layers yields `264_192` FLOPs/token. Against the active-core denominator `FLOPs_MoE,core^(l) = 8·d_model² + k·6·d_model·d_ffn^Expert = 33_554_432` per layer, the ratio is `66_048 / 33_554_432 ≈ 0.001968 → ≈ 0.20%` (the previous figure `0.26%` was arithmetically inconsistent with the same-paragraph `FLOPs_MoE,core` definition; it is now corrected), within the `0.3%` allowance.

**Source:** `wayfinder/tickets/A8-1.md`

#### Scenario: Active FLOPs parity across baselines
- **WHEN** per-token active FLOPs are tabulated for each baseline
- **THEN** every MoE entry equals the Dense baseline's per-token active FLOPs within the agreed accounting

#### Scenario: Routing overhead is reported separately
- **WHEN** the routing overhead is computed alongside the active-core FLOPs
- **THEN** `FLOPs_Routing` is reported as a standalone line item and MUST NOT enter the parity equation

<a id="req-20"></a>

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
<a id="req-21"></a>

### Requirement: Six-Module Visualization Toolchain

The system MUST provide a production-ready visualization toolchain with six modules: 3D PCA scatter (fixed camera angles 25°/135°);` `D_c` heatmap with Optimal Leaf Ordering;` 2D Voronoi tessellation with elliptical β fitting;` trajectory animation with fixed `W_PCA` across frames;` TensorBoard dashboard;` and PlantUML diagram documentation. The implementation stack MUST be `matplotlib`, `scikit-learn`, `scipy`, `imageio`, `tensorboard`, and `plantuml`.

**Source:** `wayfinder/tickets/A8-3.md`

#### Scenario: Toolchain completeness
- **WHEN** an experimenter needs to inspect a trained model
- **THEN** each of the six modules is available without bespoke scripting beyond their public APIs

<a id="req-22"></a>

### Requirement: Empty-Cell Fallback Invariant

For any expert `i` whose assigned token count `n_i = |T_i| = Σ_t I[i ∈ Top-k(C_t)]` is zero in the current batch, the per-expert mean MUST default to the previous centroid: `m_i^(t) ≡ c_i^(t−1)`, which yields `c_i^(t+1) = c_i^(t)`. Implementations MUST NOT use `assignment_mask.sum().clamp_min(ε)` style normalization on empty cells: dividing by a clamped epsilon produces a direction-randomized unit vector (or zero divided by epsilon) that introduces phantom expert drift and breaks Dead Expert Resurrection. Hard guarantee: `c_i^(t+1) == c_i^(t)` element-wise within FP tolerance whenever `n_i = 0`.

**Source:** `wayfinder/tickets/A3-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: Empty-cell preserves centroid exactly
- **WHEN** the driver channel receives a batch where expert `i` has `n_i = 0`
- **THEN** the post-step centroid satisfies `‖c_i^(t+1) − c_i^(t)‖₂ < 10⁻¹²` (machine-epsilon identity)

#### Scenario: No phantom updates from clamped normalization
- **WHEN** an implementation is audited via source grep
- **THEN** there is no `.clamp_min(1e-9)` / `.clamp_min(ε)` call whose result is used as a denominator in the empty-cell branch (denominator-zero would propagate and break the invariant)

<a id="req-23"></a>

### Requirement: Spherical Re-Projection And Zero-Vector Invariant

After every driver-channel update, the centroid MUST satisfy `‖c_i^(t+1)‖₂ ≡ 1.0` (within `1e-7` FP tolerance). If the unnormalized candidate `u_i` satisfies `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse from the spherical EMA), the implementation MUST fall back to the previous centroid `c_i^(t+1) = c_i^(t)` to prevent NaN propagation and preserve the geometric boundedness of `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The hard guarantee `‖c_i‖₂ = 1` is required by Req 7 (`d ∈ [0, 2]`, `‖∂logit/∂C‖ ≤ β_max = 32`).

**Source:** `wayfinder/tickets/A3-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: Spherical norm is strictly one
- **WHEN** the driver channel completes a step in any Phase (0 K-Means, 1–3 EMA, 4 Projected SGD)
- **THEN** `max_i |‖c_i‖₂ − 1.0| < 1e-7` over all experts

#### Scenario: Near-zero candidate falls back
- **WHEN** the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹`
- **THEN** the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears in the centroid tensor

<a id="req-24"></a>

### Requirement: Beta Parameterization Space vs Operational Domain

The system MUST maintain a clean separation between two domains: the **parameterization space** (`β^param(γ) = 0.1 + 31.9 · σ(γ)`, theoretical interval `[0.1, 32]`) and the **operational domain** (per-phase effective `β^eff`). `β_min = 0.1` exists in parameterization space to keep `σ'(γ)` non-degenerate in the cold-start region (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.0284`; lowering the floor to `1.0` (i.e., switching to the counterfactual parameterization `β = 1.0 + 31.0 · σ(γ)`) would require `γ_init ≈ −6.785`, with `σ'(−6.785) ≈ 1.128e-3`, a 25× gradient starvation). The operational floor `1.0` is independent and exists to prevent routing resonance at runtime. Per-phase effective `β^eff`:

- Phase 1: `β^eff = 1.0` (fixed, regardless of `γ`).
- Phase 2–3: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase schedule (`1.0 → 4.0` Phase 2, `4.0 → 16.0` Phase 3).
- Phase 4: `β^eff = 1.0 + 31.0 · σ(γ')` — continuous reparameterization. On Phase 4 entry, `γ` is reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum for `γ` is reset. This avoids the hard-clamp gradient-zero trap at the `[1.0, 32.0]` box boundary.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A6b-1.md`

#### Scenario: Parameterization floor preserves cold-start gradient
- **WHEN** `γ` is initialized to `γ_init ≈ −3.5`
- **THEN** `β_0 ≈ 1.035` and `σ'(γ_init) ≥ 0.02` (healthy gradient in the cold-start region)

#### Scenario: Phase 3 → 4 transition is continuous
- **WHEN** Phase 4 is entered at `β_{p3} = 16.0`
- **THEN** `γ' = ln(15/16) ≈ −0.0645` is set, AdamW momentum for `γ` is reset, and `β^eff(Phase 4, t=0) = 16.0` exactly (continuity)

<a id="req-25"></a>

### Requirement: CentroidDriver Dual-Channel Architecture Contract

The system MUST unify all centroid `c_i` lifecycle updates through a single `CentroidDriver` abstraction, with strictly orthogonal Driver Channel (gradient-free) and Gradient Channel (AdamW) responsibilities:

| Phase | Driver Channel (CentroidDriver) | Gradient Channel (AdamW) | EMA α | Physical meaning |
|---|---|---|---|---|
| 0 | K-Means seeding | Frozen (`requires_grad=False`) | N/A | Topological manifold init |
| 1 | Masked Spherical EMA | Frozen | `0.90` | Fast feature alignment (warmup) |
| 2 | Masked Spherical EMA | Frozen | `0.95` | Coarse manifold convergence |
| 3 | Masked Spherical EMA | Frozen | `0.99` | High-inertia annealing (pre-SGD) |
| 4 | Projected SGD + L2 re-projection | Active (`requires_grad=True`) | N/A | End-to-end joint optimization |

Driver Channel guarantees: phases 1–3 execute Masked Spherical EMA at the prescribed `α` even when the Gradient Channel is Frozen (the previous "Phase 1 Frozen rule" matrix cell in A6b-1 is hereby superseded). Gradient Channel guarantees: phases 0–3 set `c_i.requires_grad = False` and exclude `c_i` from the AdamW parameter group; phase 4 sets `c_i.requires_grad = True` and registers `c_i` in AdamW.

**Source:** change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: Driver Channel Active during Gradient Channel Frozen
- **WHEN** training is in Phase 1, 2, or 3 with the gradient channel Frozen for `c_i`
- **THEN** the driver channel updates `c_i` per the table above; `c_i.requires_grad = False`; `c_i` is NOT in the AdamW parameter group; the empty-cell and spherical re-projection invariants (Reqs above) hold

#### Scenario: Phase 4 switches Gradient Channel to Active
- **WHEN** training enters Phase 4
- **THEN** `c_i.requires_grad = True` and `c_i` is registered in the AdamW parameter group; the Adam momentum buffers are reset; `γ` is reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`

---

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


