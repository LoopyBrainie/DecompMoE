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

**Cross-req consistency note (vs. Req 17 / `wayfinder/tickets/A7-2.md`)**: Req 17 L311 reports the *extract_C pipeline* cost as `33_040 MACs = 66_080 FLOPs`, which decomposes into projection-only `4·d_c·H_kv·d_k = 65_536 FLOPs` plus `+128 MACs` bias add and `+144 MACs` per-head L2-normalize (`+272 MACs = +544 FLOPs` on top of projection-only, at the convention `1 MAC = 2 FLOPs` used by Req 17). The routing-overhead line item reported here covers the *projection + gating similarity* slice and intentionally does **not** repackage the bias add or per-head L2-normalize as standalone line items; instead they remain attributable to Req 17's extract_C accounting. Net difference between the two specs at MVP is therefore `+32 FLOPs` (= `(128 + 144)·2 − 2·N_e·d_c = 544 − 512`), in the direction that **Req 17's extract_C total is 32 FLOPs higher** than the `FLOPs_Routing` value quoted here. This `+32 FLOPs` net is roughly `0.05%` of `FLOPs_Routing`, well under the `0.3%` allowance, and does NOT enter the parity equation under either spec. (Future revisions that consolidate the two cost items MUST retain the `0.3%` allowance invariant.)

**Source:** `wayfinder/tickets/A8-1.md`

#### Scenario: Active FLOPs parity across baselines
- **WHEN** per-token active FLOPs are tabulated for each baseline
- **THEN** every MoE entry equals the Dense baseline's per-token active FLOPs within the agreed accounting

#### Scenario: Routing overhead is reported separately
- **WHEN** the routing overhead is computed alongside the active-core FLOPs
- **THEN** `FLOPs_Routing` is reported as a standalone line item and MUST NOT enter the parity equation