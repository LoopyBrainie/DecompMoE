## MODIFIED Requirements

### Requirement: Spherical Normalized C Extraction

The system MUST extract `C_t^l` using a four-step pipeline that enforces spherical geometry throughout: (1) per-head low-rank projection `z_t^{l,h} = W_{l,h}^K · k_t^{l,h} + W_{l,h}^V · v_t^{l,h} + b_{l,h}`; (2) per-head spherical projection `C_t^{l,h} = z_t^{l,h} / max(||z_t^{l,h}||₂, ε)`; (3) cross-head mean `z̄_t^l = (1/H_kv) · Σ_h C_t^{l,h}`; (4) final spherical projection `C_t^l = z̄_t^l / max(||z̄_t^l||₂, ε)`. The pipeline MUST be Grouped-Query-Attention aware (using `H_kv`). The per-token time complexity MUST be `O(H_kv · d_c · d_k)` and space MUST be `O(d_c)`.

**Source:** `wayfinder/tickets/A3-1.md`

#### Scenario: Output stays on the unit sphere
- **WHEN** the pipeline produces `C_t^l`
- **THEN** `||C_t^l||₂ = 1` (within floating-point tolerance) and `C_t^l ∈ S^{d_c-1}`

#### Scenario: Complexity budget holds
- **WHEN** `H_kv`, `d_c`, `d_k` are concrete values (e.g. `H_kv=8, d_c=16, d_k=128`)
- **THEN** per-token compute is O(`H_kv · d_c · d_k`) and resident memory for the activation is O(`d_c`)

### Requirement: Standard SwiGLU FFN Expert

The system MUST implement each expert as a Standard SwiGLU FFN, isomorphic to the Llama baseline FFN: `Expert_i(x) = (SiLU(x W_i^g) ⊙ x W_i^u) W_i^d`. Each expert MUST consume `3 · d_model · d_ffn` parameters and `k · 3 · d_model · d_ffn` active parameters per routed token (Mixtral-style active-parameter accounting; aligned with Req 10 guarantee (3) — "alignment with Mixtral's active-parameter accounting"). The expert MUST receive zero `C`-derived injection, so that performance differences are attributable solely to the routing chain (A0–A4). The system MUST NOT introduce a custom kernel for the SwiGLU FFN; standard vLLM / Megatron / DeepSpeed SwiGLU kernels MUST be reusable.

**Source:** `wayfinder/tickets/A5-1.md`

#### Scenario: No C injection inside experts
- **WHEN** `Expert_i(x)` is computed
- **THEN** the input `x` is the Post-FFN residual stream at the mount point and no `C` or `c_i` derived signal enters the expert

#### Scenario: SwiGLU kernel reuse
- **WHEN** the system is deployed on a supported framework
- **THEN** the SwiGLU FFN runs through that framework's fused SwiGLU kernel with no custom CUDA / / retargeting replacement

### Requirement: Hybrid Three-Layer Phase Triggers

The system MUST combine three trigger layers: (Layer 1) Time-Driven hard cut at the 1 K / 6 K / 26 K / 56 K / 100 K boundaries; (Layer 2) State-Driven Advisory signals — normalized entropy `R_H`, load skew `S_load`, β saturation ratio `R_β-sat`, and overlap index `L_sep / WB` (where `WB = 0.0476` is the natural baseline of the soft orthogonality loss, defined in `wayfinder/tickets/A6b-2.md` L52 and L89–L92 as the per-expert orthogonality baseline that the advisory ratio normalizes against; a ratio `> 2.0` indicates severe centroid clustering / territory overlap) — read-only and advisory only (never auto-trigger a transition); (Layer 3) Hard Cutoff at 100 K steps. Real-time monitoring of `D_c` (per-expert geodesic spread) MUST be excluded;` `D_c` remains an offline metric due to its `O(N_e²)` cost and unstable threshold.

**Source:** `wayfinder/tickets/A6b-2.md`

#### Scenario: Advisory signals not to auto-trigger
- **WHEN** an advisory signal crosses any threshold before its corresponding time-driven boundary
- **THEN** the system logs the advisory but does NOT advance the phase