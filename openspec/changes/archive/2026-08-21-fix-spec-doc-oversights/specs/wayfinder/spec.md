## MODIFIED Requirements

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

---

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
