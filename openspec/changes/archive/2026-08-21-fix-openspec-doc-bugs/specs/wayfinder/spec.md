## MODIFIED Requirements

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

---

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

---

### Requirement: 4070 MVP Hyperparameter Set

The system MUST, for the 4070 8 GB MVP target, adopt `d_model = 1024`, `N_e = 16`, `k = 2`, `d_ffn = 2048`, `L = 4`, `d_c = 16`, `H = 8`, `H_kv = 8`, `d_k = 128`, `V = 32_000`. Total parameters ≈ 452 M and active parameters ≈ 100 M. The MoE active FLOPs MUST be 1:1 with a Dense baseline whose `d_ffn_dense = 4096` (each MoE token performs exactly two expert FFNs of width 2048). The geometric self-consistency check MUST hold (`θ_Voronoi ≈ 52°` strictly greater than the `β = 16` boundary `θ_{1/e} ≈ 20.36°`).

**Closed-form Voronoi half-angle (definitional layer)**: For N_e equal-area cells on `S^{d_c − 1}`, `θ_Voronoi(N_e, d_c)` is the unique `θ ∈ (0, π)` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e`, where `I_x(a, b)` is the regularized incomplete beta function. Equivalently, `r_Voronoi(N_e, d_c) = 1 − cos θ_Voronoi` is the per-expert spherical-chord radius. MVP tabulated values:
- `θ_Voronoi(16, 16) ≈ 52.00° (0.9076 rad)`, `r_Voronoi(16, 16) ≈ 0.380`.
- `θ_Voronoi(64, 16) ≈ 25.45° (0.4494 rad)`, `r_Voronoi(64, 16) ≈ 0.0971`.

The canonical configuration-layer API `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` MUST return this closed-form value. The measurement-layer API `voronoi_angle(centroids: Tensor) -> float` MUST compute the realized Voronoi half-angle from an actual centroid tensor (offline use only, never in the training hot path). The specialist-collapse boundary `θ_{1/e}(β) = arccos(1 − 1/β)` MUST strictly satisfy `θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16) ≈ 20.36°`.

**Parameter-count accounting (four explicit assumptions, MVP scale)**:
1. **Weight tying** — input embedding `W_emb ∈ R^{V × d_model}` is shared with `lm_head` (no extra lm_head parameter). Without tying, total grows from 452 M to ≈ 484 M.
2. **GQA degenerates to MHA at MVP scale** — `H_kv · d_k = 8 · 128 = 1024 = d_model`, so attention parameters reduce to `4 · d_model²` per layer exactly; if true GQA is later enabled (`H_kv · d_k < d_model`), the formula `P_attn/layer = 2 · d_model² + 2 · d_model · d_kv` (with `d_kv = H_kv · d_k`) MUST be used.
3. **No Q/K/V/O biases** — `W^Q, W^K, W^V, W^O` carry no bias term.
4. **Rounding residual** — the claimed ≈ 452 M / ≈ 100 M figures absorb routing low-rank projections `W^K, W^V, b`, LayerNorm gains, and `β_i, c_i` micro-parameters (< 0.1 M per layer) as rounding.

**Closed-form parameter totals**: `P_expert = 3 · d_model · d_ffn = 3 · 1024 · 2048 = 6_291_456` (SwiGLU 3-matrix); `P_total = P_emb + L · 4 · d_model² + L · N_e · P_expert = 32.77 M + 16.78 M + 402.65 M ≈ 452.20 M`; `P_active = P_emb + L · 4 · d_model² + L · k · P_expert = 32.77 M + 16.78 M + 50.33 M ≈ 99.88 M`.

**Source:** `wayfinder/tickets/A5-3.md`, `wayfinder/tickets/A8-1.md`, change `fix-openspec-doc-bugs` design.md (Decision 4, 8)

#### Scenario: Active FLOPs parity
- **WHEN** MoE active FLOPs per token are computed against a Dense baseline
- **THEN** MoE per-token active FLOPs equal Dense per-token FLOPs within the agreed alignment accounting

#### Scenario: Geometric self-consistency
- **WHEN** the boundary threshold `θ_{1/e}` is evaluated under `β = 16`
- **THEN** the per-layer Voronoi angle `θ_Voronoi(16, 16)` from `canonical_voronoi_angle(16, 16)` exceeds `θ_{1/e}` by a margin that prevents specialist collapse

#### Scenario: Voronoi angle is N_e- and d_c-dependent
- **WHEN** `canonical_voronoi_angle(N_e, d_c)` is evaluated at `(64, 16)`
- **THEN** the result is `≈ 25.45°`, distinct from `canonical_voronoi_angle(16, 16) ≈ 52.00°` (the function depends on both arguments, not `d_c` alone)

---

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

---

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

---

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

---

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
`FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c`, where `4 · d_c · H_kv · d_k` accounts for `W^K, W^V` low-rank projections (each `2 · H_kv · 2 · d_k · d_c`), and `2 · N_e · d_c` accounts for the gating similarity dot product `C^T c_i`. At MVP this evaluates to `4·16·8·128 + 2·16·16 = 65_536 + 512 = 66_048` FLOPs/layer; `L = 4` layers yields `264_192` FLOPs/token, which is `≈ 0.26%` of `FLOPs_MoE,core`, within the `0.3%` allowance.

**Source:** `wayfinder/tickets/A8-1.md`

#### Scenario: Active FLOPs parity across baselines
- **WHEN** per-token active FLOPs are tabulated for each baseline
- **THEN** every MoE entry equals the Dense baseline's per-token active FLOPs within the agreed accounting

#### Scenario: Routing overhead is reported separately
- **WHEN** the routing overhead is computed alongside the active-core FLOPs
- **THEN** `FLOPs_Routing` is reported as a standalone line item and MUST NOT enter the parity equation

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
| `SP_i` | `SP_i = (1 / ‖T_i‖₁) · Σ_{t ∈ T_i} c_i^T C_t` | `T_i` = set of tokens routed to expert `i`. If `‖T_i‖₁ = 0` (dead expert), `SP_i ≡ undefined` and MUST NOT be reported as `0` |
| `D_chord` | `D_chord = (2 / (N_e(N_e−1))) · Σ_{i<j} √(2(1 − c_i^T c_j))` | mean spherical chord between off-diagonal centroid pairs. The geodesic angle version is `arccos(c_i^T c_j)`; chord distance uses `√(2(1 − cos θ))` |
| `MCI` | `MCI = (1 / d_c) · Σ_{j=1}^{d_c} 1 / λ̃_j²`, with `λ̃_j = λ_j / Σ_r λ_r` | eigenvalues of `Cov(C)` over the routed-token set; `MCI ∈ (1/d_c, 1]` |
| `CG` | `CG = ‖∇_{W^{K, V, b}} L_total‖₂` | debug-only stability probe; MUST NOT enter quality acceptance |

**Source:** `wayfinder/tickets/A8-2.md`

#### Scenario: Realtime vs offline classification
- **WHEN** metrics are reported
- **THEN** `L_sep`, `R_H`, `S_load`, `UR` are available every step; `SP`, `D_c`, `MCI`, `CG` are computed offline

#### Scenario: L_sep Frobenius consistency
- **WHEN** `L_sep` from the metrics module is compared to `L_sep` from the loss module under the same `c_centroids`
- **THEN** the two values are equal within `1e-6`

#### Scenario: Dead-expert SP is undefined
- **WHEN** an expert `i` has `‖T_i‖₁ = 0` in the current offline window
- **THEN** `SP_i` is reported as `undefined` (e.g. `NaN` with a `dead=True` flag, or omitted), NOT as `0.0`

#### Scenario: R_H is bounded
- **WHEN** `R_H(p)` is computed for any probability vector `p` over `N_e` experts
- **THEN** `R_H ∈ [0, 1]` within `1e-6`

## ADDED Requirements

### Requirement: Empty-Cell Fallback Invariant

For any expert `i` whose assigned token count `n_i = |T_i| = Σ_t I[i ∈ Top-k(C_t)]` is zero in the current batch, the per-expert mean MUST default to the previous centroid: `m_i^(t) ≡ c_i^(t−1)`, which yields `c_i^(t+1) = c_i^(t)`. Implementations MUST NOT use `assignment_mask.sum().clamp_min(ε)` style normalization on empty cells: dividing by a clamped epsilon produces a direction-randomized unit vector (or zero divided by epsilon) that introduces phantom expert drift and breaks Dead Expert Resurrection. Hard guarantee: `c_i^(t+1) == c_i^(t)` element-wise within FP tolerance whenever `n_i = 0`.

**Source:** `wayfinder/tickets/A3-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: Empty-cell preserves centroid exactly
- **WHEN** the driver channel receives a batch where expert `i` has `n_i = 0`
- **THEN** the post-step centroid satisfies `‖c_i^(t+1) − c_i^(t)‖₂ < 10⁻¹²` (machine-epsilon identity)

#### Scenario: No phantom updates from clamped normalization
- **WHEN** an implementation is audited via source grep
- **THEN** there is no `.clamp_min(1e-9)` / `.clamp_min(ε)` call whose result is used as a denominator in the empty-cell branch (denominator-zero would propagate and break the invariant)

---

### Requirement: Spherical Re-Projection And Zero-Vector Invariant

After every driver-channel update, the centroid MUST satisfy `‖c_i^(t+1)‖₂ ≡ 1.0` (within `1e-7` FP tolerance). If the unnormalized candidate `u_i` satisfies `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse from the spherical EMA), the implementation MUST fall back to the previous centroid `c_i^(t+1) = c_i^(t)` to prevent NaN propagation and preserve the geometric boundedness of `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The hard guarantee `‖c_i‖₂ = 1` is required by Req 7 (`d ∈ [0, 2]`, `‖∂logit/∂C‖ ≤ β_max = 32`).

**Source:** `wayfinder/tickets/A3-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: Spherical norm is strictly one
- **WHEN** the driver channel completes a step in any Phase (0 K-Means, 1–3 EMA, 4 Projected SGD)
- **THEN** `max_i |‖c_i‖₂ − 1.0| < 1e-7` over all experts

#### Scenario: Near-zero candidate falls back
- **WHEN** the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹`
- **THEN** the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears in the centroid tensor

---

### Requirement: Beta Parameterization Space vs Operational Domain

The system MUST maintain a clean separation between two domains: the **parameterization space** (`β^param(γ) = 0.1 + 31.9 · σ(γ)`, theoretical interval `[0.1, 32]`) and the **operational domain** (per-phase effective `β^eff`). `β_min = 0.1` exists in parameterization space to keep `σ'(γ)` non-degenerate in the cold-start region (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.0284`; lowering the floor to `1.0` would require `γ_init ≈ −6.94`, with `σ'(−6.94) ≈ 9.7e-4`, a 29× gradient starvation). The operational floor `1.0` is independent and exists to prevent routing resonance at runtime. Per-phase effective `β^eff`:

- Phase 1: `β^eff = 1.0` (fixed, regardless of `γ`).
- Phase 2–3: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase schedule (`1.0 → 4.0` Phase 2, `4.0 → 16.0` Phase 3).
- Phase 4: `β^eff = 1.0 + 31.0 · σ(γ')` — continuous reparameterization. On Phase 4 entry, `γ` is reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum for `γ` is reset. This avoids the hard-clamp gradient-zero trap at the `[1.0, 32.0]` box boundary.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A6b-1.md`

#### Scenario: Parameterization floor preserves cold-start gradient
- **WHEN** `γ` is initialized to `γ_init ≈ −3.5`
- **THEN** `β_0 ≈ 1.035` and `σ'(γ_init) ≥ 0.02` (healthy gradient in the cold-start region); the `[0.1, 32]` parameterization interval is preserved

#### Scenario: Phase 3 → 4 transition is continuous
- **WHEN** Phase 4 is entered at `β_{p3} = 16.0`
- **THEN** `γ' = ln(15/16) ≈ −0.0645` is set, AdamW momentum for `γ` is reset, and `β^eff(Phase 4, t=0) = 16.0` exactly (continuity)

---

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