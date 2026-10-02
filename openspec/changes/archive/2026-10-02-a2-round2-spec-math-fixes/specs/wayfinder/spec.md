# Spec Delta

## MODIFIED Requirements

<a id="req-11"></a>

### Requirement: 4070 MVP Hyperparameter Set

The system MUST, for the 4070 8 GB MVP target, adopt `d_model = 1024`, `N_e = 16`, `k = 2`, `d_ffn = 2048`, `L = 4`, `d_c = 16`, `H = 8`, `H_kv = 8`, `d_k = 128`, `V = 32_000`. Total parameters ≈ 452 M and active parameters ≈ 100 M. The MoE active FLOPs MUST be 1:1 with a Dense baseline whose `d_ffn_dense = 4096` (each MoE token performs exactly two expert FFNs of width 2048). The geometric self-consistency check MUST hold (`θ_Voronoi > θ_{1/e}` strictly under the MVP configuration, with the closed-form residual `½ · I_{sin²θ}((d_c−1)/2, 1/2) − 1/N_e` evaluating to less than `1e-9` **in the impl-internal frame** — i.e. against the same `_betainc_regularized` quadrature that produced `θ`, which measures `1.16e-14` at `θ = 1.1735482746999482 rad` — and this bound MUST NOT be read in the true closed-form frame, where the same residual measures `4.15e-7` at `(N_e=16, d_c=16)` and `1.43e-9` at `(N_e=64, d_c=16)`, neither of which meets `< 1e-9`; the frame MUST be named on every such claim per `openspec/specs/governance/spec.md` req-gov-1 obligation 4).

**Closed-form Voronoi half-angle (definitional layer)**: For N_e equal-area cells on `S^{d_c − 1}`, `θ_Voronoi(N_e, d_c)` is the unique `θ ∈ (0, π/2]` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e`, where `I_x(a, b)` is the regularized incomplete beta function. Equivalently, `versine_Voronoi(N_e, d_c) = 1 − cos θ_Voronoi` is the per-expert spherical **versine** (cap height, `1 − cos θ`); it MUST NOT be confused with `D_chord = √(2(1 − cos θ))` which uses the same `(1 − cos θ)` base but takes the square root to obtain chord length. MVP tabulated values (independent root-finding, impl-internal residual `< 1e-9` per `src/decompmoe/sphere.py::_betainc_regularized`; true closed-form residual vs mpmath at the bisection output is `≈ 4.15e-7` for `(N_e=16, d_c=16)` and `≈ 1.43e-9` for `(N_e=64, d_c=16)`, and the corresponding **angle-domain bias** of the impl bisection output from the exact equation root is `≈ 8.49e-7 rad` for `(N_e=16, d_c=16)` and `≈ 8.79e-9 rad` for `(N_e=64, d_c=16)` (`8.4878023e-7 rad` and `8.7898467e-9 rad` respectively at 50-digit mpmath precision) — a property of the impl's `_betainc_regularized` systematic error, which applies a **single** 8-point Gauss–Legendre panel on `[0, x]` with no subdivision, and the same two values already disclosed by `openspec/specs/decompmoe-skeleton/spec.md` req-6 "Bisection output + narrative precision disclosure". This angle-domain bias is far below the 4-decimal-radian and 2-decimal-degree display resolution, so every tabulated display form below is frame-independent, and the bias is likewise well within the `< 1e-6` test tolerance prescribed by `openspec/specs/governance/spec.md` req-gov-1 §3 — see the frame-disambiguation obligation in req-gov-1 §4):
- `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`, `versine_Voronoi(16, 16) ≈ 0.6131`.
- `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`, `versine_Voronoi(64, 16) ≈ 0.4771`.

> **Display precision note**:
> - `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`: `67.24°` (4-decimal-degree = ~4-sig-fig for angle) and `≈ 1.1735 rad` (4-decimal-rad = ~5-sig-fig for rad) are dual prose forms referring to the same impl bisection output `1.1735482746999482 rad = 67.23936319516639°` (`math.degrees(1.1735482746999482)` computed exactly; the `≈` signals 4-decimal-degree prose rounding to `67.24°`). The two displays differ by `67.24° × π/180 − 1.1735 ≈ 5.94e-5 rad` due to independent prose rounding. This is a **prose-to-prose** display gap and is **NOT bounded by any test tolerance** — the 4-decimal form is asserted, but by bare equality on rounded values, not by a tolerance. The gap is `59×` the `abs=1e-6` tolerance that req-gov-1 §3 prescribes; separately, the impl bisection output `1.1735482746999482` is `48×` that tolerance away from the 4-decimal literal (`4.83e-5`, a different quantity from this `5.94e-5` prose gap). Either way the 4-decimal form MUST NOT be paired with that tolerance. The guards are the exact `round(θ, 4) == 1.1735` / `round(math.degrees(θ), 2) == 67.24` (bare `==`, per the `decompmoe-skeleton` req-6 Scenario "Bisection output + narrative precision disclosure") and the `pytest.approx(1.173548, abs=1e-6)` 6-decimal test literal. For clarity on tolerance provenance: req-gov-1 §2 fixes the *assertion form* for a float closed-form claim but prescribes **no numeric tolerance value**; the `abs=1e-6` figure comes from req-gov-1 §3, which is scoped to the 6-decimal bisection literals, not to this 4-decimal display.
> - `θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)`: similar dual-prose pattern; impl output `1.0205068335735599 rad = 58.47073...°`; display diff `58.47° × π/180 − 1.0205 ≈ −5.99e-6 rad` (negative: `58.47° × π/180 = 1.0204940... rad < 1.0205 rad`), magnitude `|diff| ≈ 5.99e-6 rad`. As above, this is a prose-to-prose display gap with **no governing test tolerance**; the guards are the exact `round(θ, 4) == 1.0205` / `round(math.degrees(θ), 2) == 58.47` (bare `==`) and the `pytest.approx(1.020506, abs=1e-6)` 6-decimal test literal.
>
> The prose-form-vs-impl-output gap and the within-form dual-display gap together demonstrate that **prose angle precision ≠ impl-bit precision**: the `≈` symbol already signals spec-narrative precision disclosure, not strict equality. The angle-domain bias disclosed in the definitional-layer paragraph above is the *impl-frame vs exact-root* gap and is a distinct quantity from this prose-rounding gap; the two MUST NOT be conflated, and neither exceeds the display resolution of the tabulated forms.

The canonical configuration-layer API `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` MUST return this closed-form value (computed via bisection on the equation, NOT via a hard-coded table). The measurement-layer API `voronoi_angle(centroids: Tensor) -> float` MUST return the mean per-cell equivalent-cap radius of the realised spherical Voronoi cells, `θ̂ = (1/N_e) · Σ_i G⁻¹(A_i)`, and is thereby COMMENSURABLE with `canonical_voronoi_angle(N_e, d_c) = G⁻¹(1/N_e)` (offline use only, never in the training hot path); the cap-area function `G`, its reflected `θ > π/2` branch, the Monte-Carlo estimator of the cell areas `A_i`, the one-sidedness of `D := canonical_voronoi_angle(N_e, d_c) − θ̂` together with its precondition — `G` is strictly convex on all of `(0, π/2)`, so `G⁻¹` is concave on `(0, 0.5)` and the bound is a theorem exactly when every realised cell is smaller than a hemisphere, `∀i: A_i < 0.5` — and the load-bearing nature of the per-cell form are all specified in `openspec/specs/decompmoe-skeleton/spec.md` req-6; the statistical tolerance its test guards MUST use is specified in `openspec/specs/governance/spec.md` req-gov-1 obligation 7. The specialist-collapse boundary `θ_{1/e}(β) = arccos(1 − 1/β)` MUST strictly satisfy `θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16) ≈ 20.36°`.

**Parameter-count accounting (four explicit assumptions, MVP scale)**:
1. **Weight tying** — input embedding `W_emb ∈ R^{V × d_model}` is shared with `lm_head` (no extra lm_head parameter). Without tying, total grows from 452_329_984 to 452_329_984 + V·d_model = 452_329_984 + 32_768_000 = 485_097_984 (≈ 485.1 M), i.e. +32_768_000 parameters (+7.24%).
2. **GQA degenerates to MHA at MVP scale** — `H_kv · d_k = 8 · 128 = 1024 = d_model`, so attention parameters reduce to `4 · d_model²` per layer exactly; if true GQA is later enabled (`H_kv · d_k < d_model`), the formula `P_attn/layer = 2 · d_model² + 2 · d_model · d_kv` (with `d_kv = H_kv · d_k`) MUST be used.
3. **No Q/K/V/O biases** — `W^Q, W^K, W^V, W^O` carry no bias term.
LayerNorm gains, `β_i`, `c_i` are excluded from the estimator (`MVPConfig` does not currently expose them as learnable parameters at MVP scale). **`W^O` is NOT excluded**: it is included in `P_attn/layer = 4 · d_model²` (Q/K/V/O) per assumption 2. Excluding it would give `452_329_984 − L·d_model² = 452_329_984 − 4_194_304 = 448_135_680` (−0.9273%), which is **not** the closed form; the implementation and all tests stand on the closed-form side.

**Closed-form parameter totals**: `P_expert = 3 · d_model · d_ffn = 3 · 1024 · 2048 = 6_291_456` (SwiGLU 3-matrix); `P_total = P_emb + L · (4 · d_model² + N_e · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 100_663_296 + 32_896) = 32_768_000 + 4 · 104_890_496 = 32_768_000 + 419_561_984 = 452_329_984` exactly; `P_active = P_emb + L · (4 · d_model² + k · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 12_582_912 + 32_896) = 32_768_000 + 4 · 16_810_112 = 32_768_000 + 67_240_448 = 100_008_448` exactly.

**Source:** `wayfinder/tickets/A5-3.md`, `wayfinder/tickets/A8-1.md`, change `fix-openspec-doc-bugs` design.md (Decision 4, 8), change `fix-math-consistency-audit-2026-08` design.md (Decision 1), change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` design.md (Decision 2 — angle-domain bias disclosure aligned with `decompmoe-skeleton` req-6), change `2026-09-29-fix-voronoi-angle-measurement-layer-semantics` design.md (Decision 1 — measurement-layer commensurability contract), change `2026-10-02-audit-a2-errata-and-spec-math-fixes` design.md (Decision D6 — `W^O` exclusion reconciled with the `4·d_model²` closed form; D4 errata table row E10 — tying counterfactual restated as a closed form)

#### Scenario: Active FLOPs parity
- **WHEN** MoE active FLOPs per token are computed against a Dense baseline
- **THEN** MoE per-token active FLOPs equal Dense per-token active FLOPs within the agreed alignment accounting

#### Scenario: Geometric self-consistency
- **WHEN** the boundary threshold `θ_{1/e}` is evaluated under `β = 16`
- **THEN** the per-layer Voronoi angle `θ_Voronoi(16, 16)` from `canonical_voronoi_angle(16, 16)` exceeds `θ_{1/e}` by a margin that prevents specialist collapse

#### Scenario: Voronoi angle is N_e- and d_c-dependent
- **WHEN** `canonical_voronoi_angle(N_e, d_c)` is evaluated at `(64, 16)`
- **THEN** the result is `≈ 58.47°`, distinct from `canonical_voronoi_angle(16, 16) ≈ 67.24°` (the function depends on both arguments, not `d_c` alone)

#### Scenario: MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)
- **WHEN** any future implementation of Phase 0 Spherical K-Means seeding (per spec req-14 "Five-Phase Time-Driven Schedule" Phase 0 description) references wayfinder ticket `A6b-1.md` L100 (which historically stated `Spherical k-means 聚 N_e = 64 类`)
- **THEN** the implementation MUST use the MVP `N_e = 16` from this Requirement (and `d_c = 16` from this Requirement) — NOT the ticket's historical `N_e = 64` value. The historical 4.0x ratio (64/16) would produce `N_e = 64` clusters of which `64 − 16 = 48` are "orphan clusters" consistently receiving negligible routing probability mass under the MVP `k = 2` top-k routing (per this Requirement `k = 2`) — these 48 unused clusters still constitute a fatal topology mismatch because the implementation would violate the spec's `N_e = 16` invariant regardless of routing uniformity
- **AND** the `territory_seeding` code identifier from spec req-2 is the canonical name for the Phase 0 seeding module (track via a separate change for the Phase 0 K-Means implementation; this Scenario pins only the `N_e = 16` value, not the module name)

#### Scenario: Voronoi closed-form residual is bounded
- **WHEN** the returned `θ` from `canonical_voronoi_angle(N_e, d_c)` is substituted into `½ · I_{sin²θ}((d_c − 1)/2, 1/2)`
- **THEN** the residual `|½ · I_{sin²θ}((d_c − 1)/2, 1/2) − 1/N_e| < 1e-9` **in the impl-internal frame** — the `_betainc_regularized` quadrature that produced `θ`, per `openspec/specs/governance/spec.md` req-gov-1 obligation 4, measured `1.16e-14` at `(N_e=16, d_c=16)` and guarded by `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` — which proves the returned value is a root of the spec's equation *as computed by the impl*, not a hard-coded constant
- **AND** the frame qualifier is load-bearing, not decorative: read in the **true closed-form frame** (mpmath `betainc(regularized=True)`) the same residual measures `4.15e-7` at `(16, 16)` and `1.43e-9` at `(64, 16)`, so the `< 1e-9` bound stated above is **false** in that frame. The `< 1e-9` (impl-internal, `½ · I` metric) and the `≈ 8.49e-7 rad` angle-domain bias disclosed by the next Scenario are distinct quantities in distinct frames and MUST NOT be conflated — the former is a residual in `½ · I`, the latter is a displacement in θ, and the true-CF residual at the impl output is `4.15e-7` at `(16, 16)` (`415×` the `1e-9` figure) and `1.43e-9` at `(64, 16)` (`1.43×`).

#### Scenario: Impl bisection output lies within 1e-6 rad of the exact equation root

- **WHEN** `canonical_voronoi_angle(N_e, d_c)` is compared against the exact real root of `½ · I_{sin²θ}((d_c−1)/2, ½) = 1/N_e` solved at 50-digit mpmath precision, for `(N_e, d_c) ∈ {(16, 16), (64, 16)}`
- **THEN** the angle-domain bias `|θ_impl − θ_exact|` is strictly positive AND strictly less than `1e-6 rad` (measured `8.4878023e-7 rad` for `(16, 16)` and `8.7898467e-9 rad` for `(64, 16)`)
- **AND** the guard MUST be expressed as a two-sided bound rather than an equality against a pinned bias value, so that a future accuracy improvement in `_betainc_regularized` that shrinks the bias toward zero does not require revising this Requirement

<a id="req-17"></a>

### Requirement: Stateless Per-Frame C Recomputation

The system MUST recompute `C_t^l` every Decode step from `(K_t, V_t)` with no carry-over state, using the formula `C_t = L2_Norm((1/H_kv) · Σ_h L2_Norm(W_h^K k_t^{(h)} + W_h^V v_t^{(h)} + b_h))`. The recomputation MUST cost approximately 65.5 K FLOPs per token projection-only (with `H_kv = 8`, `d_k = 128`, `d_c = 16`; the projection-only cost is `4·d_c·H_kv·d_k = 65_536` FLOPs — bias `H_kv·d_c = 128` MACs, per-head L2-normalize `H_kv·d_c = 128` MACs, the cross-head mean with the `1/H_kv` factor (pipeline step 3) `H_kv·d_c = 128` MACs, and final L2-normalize `d_c = 16` MACs (the two L2 steps combined: `+144` MACs) are reported separately and bring the full extract_C pipeline to `33_168 MACs = 66_336 FLOPs` per the skeleton spec, ~1.22% above the projection-only figure (`32_768` projection-only + `128` bias + `128` per-head L2 + `128` cross-head mean + `16` final L2 = `33_168`; the prior `33_040 MACs = 66_080 FLOPs` / `~0.83%` omitted the step-(3) cross-head mean) and MUST introduce 0 bytes of additional HBM traffic because all activations fit in registers / SRAM. The recomputation MUST keep C-extraction overhead under 0.5% of total decoder latency.

**Source:** `wayfinder/tickets/A7-2.md`, change `2026-09-28-fix-a7-flops-attribution-and-stale-ref` design.md (Decision 1 — 144 MAC 归属标注对齐 canonical 闭式), change `2026-10-02-audit-a2-errata-and-spec-math-fixes` design.md (Decision D5 — per-token MAC total corrected to `33_168 MACs = 66_336 FLOPs`; step-(3) cross-head mean `H_kv·d_c` added)

#### Scenario: No C caching
- **WHEN** a Decode step completes
- **THEN** no per-token C state survives into the next step;` the next step recomputes from fresh `(K_t, V_t)`

#### Scenario: Decoder latency budget
- **WHEN** decoder latency is profiled on the MVP configuration
- **THEN** the C-extraction slice is below 0.5% of total decoder time

<a id="req-18"></a>

### Requirement: Hardware And Kernel Friendliness

The system MUST keep `W_proj = {W^K, W^V, b}` (`H_kv·(2·d_k·d_c) + H_kv·d_c = 8·4096 + 8·16 = 32_896` parameters → `65_792 B = 64.25 KiB` in BF16, i.e. ≈ 64 KiB with 1 KiB = 1024 B) 100% resident in L2 cache and the per-head K/V workspace (`H_kv·d_k = 8·128 = 1024` elements × 4 B fp32 = `4_096 B = 4.00 KiB`) together with `z`, `ẑ`, `z̄` (per-head, hence `H_kv·d_c·4 = 512 B` each at MVP) and `C` (post-mean, hence `d_c·4 = 64 B`), i.e. `3·512 + 64 = 1_600 B` for the four listed tensors, 100% resident in SRAM / registers, with zero additional HBM traffic attributable to the geometric routing chain. **Correction to the prior wording**: the four listed tensors `z`, `ẑ`, `z̄`, `C` sum to exactly `1_600 B` at MVP and therefore do NOT account for the 4 KB figure — only the per-head K/V workspace `H_kv·d_k·4 B = 4_096 B` is exactly 4 KB. `H_kv`, `d_k` and `d_c` MUST be pinned by tests, because a silent drift in any of them invalidates both residency figures without turning any existing test red. The system MUST be compatible — without custom kernels — with FlashDecoding, PagedAttention, vLLM, TGI, SGLang, TensorRT-LLM, Megatron-LM, and DeepSpeed-MoE. `torch.compile` is an optional optimization path (Inductor can auto-fuse the four native ops) but MUST NOT be required for MVP correctness.

**Source:** `wayfinder/tickets/A7-3.md`, change `2026-10-02-audit-a2-errata-and-spec-math-fixes` design.md (D4 errata table row E12 — residency figures given as closed forms (`65_792 B` / `4_096 B`) with an explicit `H_kv`·`d_k`·`d_c` drift guard)

#### Scenario: No custom kernel required
- **WHEN** the system runs under any supported framework
- **THEN** it operates correctly using the framework's standard fused SwiGLU kernel and standard attention kernels with no project-specific CUDA or retargeting replacement

#### Scenario: Zero HBM delta
- **WHEN** HBM traffic is profiled for the geometric routing chain
- **THEN** the additional HBM bytes per token attributable to the chain equal zero (all intermediate state is on-chip)

<a id="req-19"></a>

### Requirement: Six Baseline Set On 4070 MVP

The system MUST, for evaluation on the 4070 8 GB MVP, hold active FLOPs strictly 1:1 between the MoE system and the Dense baseline, and MUST report results against six baselines: (Primary, E) Dense SwiGLU `d_ffn = 4096`; (Primary, M′) Mixtral reproduction with `N_e = 8`, `k = 2`; (Primary, Q1) Qwen1.5-MoE-A2.7B compressed via QLoRA; (Direct, G) GMoE with X-space Euclidean distance; (Ablation, R) Random Routing; (Ablation, S′) Random Centroids (isolates the centroid-learning contribution per A3-2).

**Representation and deferral**: only **(Primary, E) Dense SwiGLU `d_ffn = 4096`** and **(Primary, M′) Mixtral reproduction (`N_e = 8`, `k = 2`)** are representable by `flops_per_token`, whose `arch` argument admits exactly `MOE` and `DENSE`. The remaining four — **(Primary, Q1) Qwen1.5-MoE-A2.7B (QLoRA)**, **(Direct, G) GMoE**, **(Ablation, R) Random Routing**, **(Ablation, S′) Random Centroids** — have zero representation in `src` and `tests` and are **deferred to the training-time caller** (training and evaluation are out of scope per `CLAUDE.md` §7). The 1:1 contract of this Requirement therefore covers only the representable subset; a reader MUST NOT read it as a performance commitment for the deferred entries.

**Active-Core FLOPs canonical formula (per token, per layer)**:
- MoE: `FLOPs_MoE,core^(l) = 8 · d_model² + k · 6 · d_model · d_ffn^Expert` (attention Q/K/V/O + top-k SwiGLU expert FFNs).
- Dense: `FLOPs_Dense,core^(l) = 8 · d_model² + 6 · d_model · d_ffn^Dense`.

**Parity constraint**: `d_ffn^Dense ≡ k · d_ffn^Expert`. At MVP this is `4096 = 2 · 2048`, yielding exact 1:1 parity.

**Explicit exclusions** (symmetric on both sides, hence not in parity accounting):
- Attention `Q K^T` and `Attn · V` (sequence-length-dependent, `4 · S · d_model` per layer).
- Output lm_head (`2 · d_model · V_vocab`).

**Routing overhead, reported separately (not part of parity)**:
`FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c`, where `4 · d_c · H_kv · d_k` accounts for the `W^K, W^V` low-rank projections (each projection is a forward GEMM of `2 · H_kv · d_k · d_c`; two projections sum to `4 · d_c · H_kv · d_k`), and `2 · N_e · d_c` accounts for the gating similarity dot product `C^T c_i`. At MVP this evaluates to `4·16·8·128 + 2·16·16 = 65_536 + 512 = 66_048` FLOPs/layer; `L = 4` layers yields `264_192` FLOPs/token. Against the active-core denominator `FLOPs_MoE,core^(l) = 8·d_model² + k·6·d_model·d_ffn^Expert = 33_554_432` per layer, the ratio is `66_048 / 33_554_432 ≈ 0.001968 → ≈ 0.20%` (the previous figure `0.26%` was arithmetically inconsistent with the same-paragraph `FLOPs_MoE,core` definition; it is now corrected), within the `0.3%` allowance.

**Cross-req consistency note (vs. Req 17 / `wayfinder/tickets/A7-2.md`)**: Req 17 (anchored `<a id="req-17"></a>`) reports the *extract_C pipeline* cost as `33_168 MACs = 66_336 FLOPs`, which decomposes into projection-only `4·d_c·H_kv·d_k = 65_536 FLOPs` plus `+128 MACs` bias add, `+144 MACs` for the two L2-normalize steps (per-head `H_kv·d_c = 128` + final `d_c = 16`) and `+128 MACs` for the step-(3) cross-head mean with the `1/H_kv` factor (`+400 MACs = +800 FLOPs` on top of projection-only, at the convention `1 MAC = 2 FLOPs` used by Req 17). The routing-overhead line item reported here covers the *projection + gating similarity* slice and intentionally does **not** repackage the bias add, the per-head L2-normalize, the step-(3) cross-head mean, or the final L2-normalize as standalone line items; instead they remain attributable to Req 17's extract_C accounting. Net difference between the two specs at MVP is therefore `+288 FLOPs` (= `66_336 − 66_048`; decomposing the extract_C side as `(128 bias + 144 two L2 + 128 cross-head mean)·2 = 800 FLOPs` gives `800 − 512 = 288`, the prior `+32 FLOPs` having omitted the step-(3) cross-head mean's `128 MACs = 256 FLOPs`), in the direction that **Req 17's extract_C total is 288 FLOPs higher** than the `FLOPs_Routing` value quoted here. `288 / 66_048 ≈ 0.436%` is the ratio against `FLOPs_Routing` and is **not** the allowance's measure — the `0.3%` allowance is denominated in the active-core slice: `66_336 / 33_554_432 ≈ 0.1977% ≤ 0.3%`, which still holds. The prior wording conflated the two denominators, which is what made the smaller `+32 FLOPs` net read as "well under"; the allowance itself is unaffected and the net does NOT enter the parity equation under either spec. (Future revisions that consolidate the two cost items MUST retain the `0.3%` allowance invariant.)

**Source:** `wayfinder/tickets/A8-1.md`, change `2026-09-28-fix-a7-flops-attribution-and-stale-ref` design.md (Decision 1 — 144 MAC 归属标注对齐 canonical 闭式; Decision 2 — Req 17 引用改为 anchor 锚点引用（消除行号漂移脆弱性）), change `2026-10-02-audit-a2-errata-and-spec-math-fixes` design.md (D4 errata table row E11 — 1:1 assertion narrowed to parity-reparameterizable entries; D4 errata table row E12 — residency figures given as closed forms with a drift guard; four baselines marked deferred; Decision D5 — cross-Req-17 reconciliation re-anchored to the active-core denominator)

#### Scenario: Active FLOPs parity across baselines
- **WHEN** per-token active FLOPs are tabulated for each baseline
- **THEN** every MoE entry **admitting the parity reparameterization `d_ffn^Dense ≡ k · d_ffn^Expert`** equals the Dense baseline's per-token active FLOPs within the agreed accounting; entries that do not admit it (the deferred external QLoRA / GMoE checkpoints) MUST report their own stated reparameterization and MUST NOT be claimed at parity

#### Scenario: Routing overhead is reported separately
- **WHEN** the routing overhead is computed alongside the active-core FLOPs
- **THEN** `FLOPs_Routing` is reported as a standalone line item and MUST NOT enter the parity equation
