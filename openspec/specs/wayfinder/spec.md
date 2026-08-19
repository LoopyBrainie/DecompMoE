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

The system MUST compute the extraction in a fully differentiable manner (the D-path, no Straight-Through Estimator). The per-expert territory centroids `c_i^l` MUST evolve through a four-phase lifecycle: Phase 0 spherical k-means seeding (no gradient), Phase 1–3 masked spherical EMA with smoothing coefficients 0.90 → 0.95 → 0.99 plus dead-expert protection, Phase 4 projected SGD on the sphere via L2 retraction after the optimizer step.

**Source:** `wayfinder/tickets/A3-2.md`

#### Scenario: No STE in forward or backward
- **WHEN** gradients are back-propagated through the extraction
- **THEN** every step of the pipeline contributes a finite gradient; no surrogate (STE) is inserted between `z` and `C`

#### Scenario: Phase transition updates the centroid driver
- **WHEN** training crosses a phase boundary defined in the schedule
- **THEN** the centroid update rule switches (k-means → EMA 0.90 → EMA 0.95 → EMA 0.99 → projected SGD) without altering the extraction math

<a id="req-7"></a>

### Requirement: Isotropic Squared-Chord Distance And Bounded Beta

The system MUST measure distance between `C_t^l` and `c_i^l` using the isotropic squared-chord distance `d(C, c_i) = 1 − C^T c_i ∈ [0, 2]`. The system MUST parameterize the inverse-temperature as `β = β_min + (β_max − β_min) · Sigmoid(γ)` with `β_min = 0.1` and `β_max = 32`. The corresponding logit MUST be `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The system MUST bound `‖∂logit/∂C‖₂` and `‖∂logit/∂c_i‖₂` by ` ≤ β_max = 32`, and `|∂logit/∂γ_i|` by ` ≤ 0.5(β_max − β_min) = 15.95`, as hard numerical-stability guarantees derived from ticket A4-1. Per-expert scalar weights `w_i` MUST NOT appear in the logit; `w_i` is reserved for post-aggregation mixing decided elsewhere.

**Source:** `wayfinder/tickets/A4-1.md`

#### Scenario: Distance is bounded and gradient-safe
- **WHEN** any `(C, c_i)` pair on the unit sphere is fed into the gating function
- **THEN** the distance lies in `[0, 2]` and the per-component gradient magnitude stays below or equal to `β_max = 32`

#### Scenario: w_i is absent from the logit
- **WHEN** the logit is computed for gating
- **THEN** no learnable per-expert scalar weight `w_i` participates in `logit = β(C^T c − 1)`

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

The system MUST, for the 4070 8 GB MVP target, adopt `d_model = 1024`, `N_e = 16`, `k = 2`, `d_ffn = 2048`, `L = 4`, with total parameters ≈ 452 M and active parameters ≈ 100 M. The MoE active FLOPs MUST be 1:1 with a Dense baseline whose `d_ffn_dense = 4096` (each MoE token performs exactly two expert FFNs of width 2048). The geometric self-consistency check MUST hold (`θ_Voronoi ≈ 52°` strictly greater than the `β = 16` boundary `θ_{1/e} ≈ 20.36°`).

**Source:** `wayfinder/tickets/A5-3.md` (v2 section), `wayfinder/tickets/A8-1.md`

#### Scenario: Active FLOPs parity
- **WHEN** MoE active FLOPs per token are computed against a Dense baseline
- **THEN** MoE per-token active FLOPs equal Dense per-token FLOPs within the agreed alignment accounting

#### Scenario: Geometric self-consistency
- **WHEN** the boundary threshold `θ_{1/e}` is evaluated under `β = 16`
- **THEN** the per-layer Voronoi angle `θ_Voronoi` exceeds `θ_{1/e}` by a margin that prevents specialist collapse

<a id="req-12"></a>

### Requirement: Loss Composition

The system MUST train with `L_total = L_CE + α · L_lb + λ(t) · L_sep`, where `α = 0.01` (Switch-style fixed weight on `L_lb`, computed with detached per-expert fractions `f_i.detach()`), and `λ(t)` follows a staged schedule: `0` in Phases 1–2, a cosine ramp from `0` to `0.001` during Phase 3, and `0.001` fixed in Phase 4. `L_sep` MUST be the soft orthogonality loss `L_sep = (||C^T C||_F² − N_e) / (N_e · (N_e − 1))` (equivalently `(1/(N_e(N_e−1))) · Σ (c_i^T c_j)²` over off-diagonal pairs). The system MUST keep the notation distinction between per-token `C_t^l` and per-expert `C` matrix unambiguous.

**Source:** `wayfinder/tickets/A6a-1.md`

#### Scenario: Phase-driven lambda schedule
- **WHEN** training progresses through the schedule
- **THEN** `λ(t)` equals the staged values (0 / cosine ramp / 0.001 fixed) and the separation term is never non-zero in Phases 1–2

<a id="req-13"></a>

### Requirement: Numerical Safeguards

The system MUST execute the standard training step as `Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i)`, which is a first-order Riemannian SGD equivalent on the spherical constraint. The system MUST implement all five safeguards: (1) Global Gradient Clipping at threshold `1.0` covering all learnable parameters; (2) NaN Detection & Escalation with `1 skip → 3 consecutive NaN trigger LR ÷ 10 → 10 consecutive NaN halt training`; (3) Dead Expert Splitting Resurrection triggered when `f_i^avg < 1/128` for 200 consecutive steps (clones `j* = argmax f_j^avg`, perturbs with `ε ~ N(0, 0.05² I)`, sets `β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`, rate-limited to once per 1000 steps); (4) β Saturation Guard with warning at `β_i > 30.4` (95% of `β_max`) and global `LR ÷ 2` when more than 50% of experts have `β_i > 28.8` (90% of `β_max`); (5) Loss Spike Defense in Phase 3+ with `L_task > 2.5 · EMA(L_task)` triggering `LR × 0.8`.

**Source:** `wayfinder/tickets/A6a-2.md`

#### Scenario: Standard step ordering
- **WHEN** a training step completes
- **THEN** the order is `Backward → clip(1.0) → step → L2_norm(c_i)` and `c_i` lies on the unit sphere after the step

#### Scenario: NaN escalation ladder
- **WHEN** consecutive NaN step counts are 1, 3, and 10 respectively
- **THEN** the responses are: skip + zero_grad (+ AMP scaler decay); `LR ÷ 10`; halt and alert

#### Scenario: Resurrection respects rate limit
- **WHEN** two experts meet the dead-expert trigger within the same 1000-step window
- **THEN** only one resurrection event executes;` the second is deferred

#### Scenario: Beta saturation guard
- **WHEN** any single one executor reaches `β_i > 30.4` or more than 50% of experts cross `β_i > 28.8`
- **THEN** the system logs a warning or halves the global learning rate respectively

<a id="req-14"></a>

### Requirement: Five-Phase Time-Driven Schedule

The system MUST partition training into five phases with the fixed duration ratios `1% / 5% / 20% / 30% / 44%` (i.e., 1 K / 5 K / 20 K / 30 K / 44 K steps under a 100 K total). The phase boundary timestamps MUST be `1 K / 6 K / 26 K / 56 K / 100 K`. Phase 0 MUST be Spherical K-Means seeding (no gradient). Phase 1 MUST freeze the router (`c_i`, `β_i`, `W^K`, `W^V`, `b`) and train the expert FFNs only, with `L_lb` logged but not back-propagated. Phase 1 β MUST be 1.0 (fixed). Phase 2 MUST freeze the experts and train the router via masked spherical EMA at `α = 0.95`, with `β` ramping `1.0 → 4.0` and Dead Expert Resurrection active. Phase 3 MUST continue router training via masked spherical EMA at `α = 0.99`, with `β` ramping `4.0 → 16.0`, `λ(t)` cosine-ramping `0 → 0.001`, and Loss Spike Defense plus β Saturation Guard active. Phase 4 MUST unfreeze everything (small learning rate), use Projected SGD for `c_i` with L2 re-normalization, allow `β` to roam in the dynamic box `[1.0, 32.0]`, fix `λ = 0.001`, and MUST reset Adam's momentum state at the Phase 3 → 4 boundary.

**Source:** `wayfinder/tickets/A6b-1.md`

#### Scenario: Phase boundary timestamps
- **WHEN** training crosses 1 K, 6 K, 26 K, 56 K, or 100 K steps
- **THEN** the system transitions to Phase 1, 2, 3, 4, or END respectively

#### Scenario: Adam momentum reset on Phase 4 entry
- **WHEN** the schedule enters Phase 4
- **THEN** Adam's first and second moment buffers for all learnable parameters are reset before the first Phase 4 step

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

The system MUST, for evaluation on the 4070 8 GB MVP, hold active FLOPs strictly 1:1 between the MoE system and the Dense baseline, and MUST report results against six baselines: (Primary, E) Dense SwiGLU `d_ffn = 4096`;` (Primary, M′) Mixtral reproduction with `N_e = 8`, `k = 2`;` (Primary, Q1) Qwen1.5-MoE-A2.7B compressed via QLoRA;` (Direct, G) GMoE with X-space Euclidean distance;` (Ablation, R) Random Routing;` (Ablation, S′) Random Centroids (isolates the centroid-learning contribution per A3-2).

**Source:** `wayfinder/tickets/A8-1.md`

#### Scenario: Active FLOPs parity across baselines
- **WHEN** per-token active FLOPs are tabulated for each baseline
- **THEN** every MoE entry equals the Dense baseline's per-token active FLOPs within the agreed accounting

<a id="req-20"></a>

### Requirement: Eight Geometric Quantification Metrics

The system MUST report eight metrics in two classes. Realtime metrics (every step): `L_sep = (1/(N_e(N_e−1))) · Σ_{i<j} (c_i^T c_j)²` (centroid spread);` `R_H` (normalized entropy of routing distribution);` `S_load` (load skew);` `UR` (utilization rate). Offline metrics: `SP` (specialization purity);` `D_c` (per-expert geodesic spread on the sphere);` `MCI` (effective-dimensionality fraction, replacing CV because the spherical lower bound is unreachable);` `CG` (debug-only chordogram).

**Source:** `wayfinder/tickets/A8-2.md`

#### Scenario: Realtime vs offline classification
- **WHEN** metrics are reported
- **THEN** `L_sep`, `R_H`, `S_load`, `UR` are available every step;` `SP`, `D_c`, `MCI`, `CG` are computed offline

<a id="req-21"></a>

### Requirement: Six-Module Visualization Toolchain

The system MUST provide a production-ready visualization toolchain with six modules: 3D PCA scatter (fixed camera angles 25°/135°);` `D_c` heatmap with Optimal Leaf Ordering;` 2D Voronoi tessellation with elliptical β fitting;` trajectory animation with fixed `W_PCA` across frames;` TensorBoard dashboard;` and PlantUML diagram documentation. The implementation stack MUST be `matplotlib`, `scikit-learn`, `scipy`, `imageio`, `tensorboard`, and `plantuml`.

**Source:** `wayfinder/tickets/A8-3.md`

#### Scenario: Toolchain completeness
- **WHEN** an experimenter needs to inspect a trained model
- **THEN** each of the six modules is available without bespoke scripting beyond their public APIs
