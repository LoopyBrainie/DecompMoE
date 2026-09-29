# Spec Delta — `wayfinder`

## MODIFIED Requirements

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

The canonical configuration-layer API `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` MUST return this closed-form value (computed via bisection on the equation, NOT via a hard-coded table). The measurement-layer API `voronoi_angle(centroids: Tensor) -> float` MUST compute the realized Voronoi half-angle from an actual centroid tensor (offline use only, never in the training hot path). The specialist-collapse boundary `θ_{1/e}(β) = arccos(1 − 1/β)` MUST strictly satisfy `θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16) ≈ 20.36°`.

**Parameter-count accounting (four explicit assumptions, MVP scale)**:
1. **Weight tying** — input embedding `W_emb ∈ R^{V × d_model}` is shared with `lm_head` (no extra lm_head parameter). Without tying, total grows from 452 M to ≈ 484 M.
2. **GQA degenerates to MHA at MVP scale** — `H_kv · d_k = 8 · 128 = 1024 = d_model`, so attention parameters reduce to `4 · d_model²` per layer exactly; if true GQA is later enabled (`H_kv · d_k < d_model`), the formula `P_attn/layer = 2 · d_model² + 2 · d_model · d_kv` (with `d_kv = H_kv · d_k`) MUST be used.
3. **No Q/K/V/O biases** — `W^Q, W^K, W^V, W^O` carry no bias term.
4. **Router term — exact, not rounding residual** — the low-rank routing projections `W^K, W^V ∈ R^{d_c × d_k}` (one per H_kv head) and bias `b ∈ R^{d_c}` contribute **exactly** `P_router/layer = H_kv · (2 · d_k · d_c + d_c) = 8 · (2 · 128 · 16 + 16) = 32_896` parameters, totaling `P_router = L · 32_896 = 131_584` across the model. LayerNorm gains, `β_i`, `c_i`, `W^O` are all excluded from the estimator (`MVPConfig` does not currently expose them as learnable parameters at MVP scale).

**Closed-form parameter totals**: `P_expert = 3 · d_model · d_ffn = 3 · 1024 · 2048 = 6_291_456` (SwiGLU 3-matrix); `P_total = P_emb + L · (4 · d_model² + N_e · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 100_663_296 + 32_896) = 32_768_000 + 4 · 104_890_496 = 32_768_000 + 419_561_984 = 452_329_984` exactly; `P_active = P_emb + L · (4 · d_model² + k · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 12_582_912 + 32_896) = 32_768_000 + 4 · 16_810_112 = 32_768_000 + 67_240_448 = 100_008_448` exactly.

**Source:** `wayfinder/tickets/A5-3.md`, `wayfinder/tickets/A8-1.md`, change `fix-openspec-doc-bugs` design.md (Decision 4, 8), change `fix-math-consistency-audit-2026-08` design.md (Decision 1), change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` design.md (Decision 2 — angle-domain bias disclosure aligned with `decompmoe-skeleton` req-6)

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
<a id="req-12"></a>

### Requirement: Beta Parameterization Space vs Operational Domain

The system MUST maintain a clean separation between two domains: the **parameterization space** (`β^param(γ) = 0.1 + 31.9 · σ(γ)`, theoretical interval `[0.1, 32]`) and the **operational domain** (per-phase effective `β^eff`). `β_min = 0.1` exists in parameterization space to keep `σ'(γ)` non-degenerate in the cold-start region (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.02845`, verified at 50-digit mpmath precision `σ'(−3.5) = 0.02845302387973555984`; lowering the floor to `1.0` (i.e., switching to the counterfactual parameterization `β = 1.0 + 31.0 · σ(γ)`) would require `γ_init ≈ −6.7835`, with `σ'(-6.7835) ≈ 1.130e-3`, a 25× gradient starvation). The operational floor `1.0` is independent and exists to prevent routing resonance at runtime. Per-phase effective `β^eff`:

- Phase 1: `β^eff = 1.0` (fixed, regardless of `γ`).
- Phase 2–3: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase schedule (`1.0 → 4.0` Phase 2, `4.0 → 16.0` Phase 3).
- Phase 4: `β^eff = 1 + 31.0 · σ(γ')` — continuous reparameterization. On Phase 4 entry, `γ` is reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum for `γ` is reset. This avoids the hard-clamp gradient-zero trap at the `[1.0, 32.0]` box boundary.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A6b-1.md`, change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` design.md (Decision 3 — counterfactual `γ_init` last-digit rounding correction; exact 50-digit mpmath value `−6.783545399795103364342` derived from `β_0 = 0.1 + 31.9·σ(−3.5) = 1.035060160968266571803`)

#### Scenario: Parameterization floor preserves cold-start gradient

- **WHEN** `γ` is initialized to `γ_init ≈ −3.5`
- **THEN** `β_0 ≈ 1.035` and `σ'(γ_init) ≥ 0.02` (healthy gradient in the cold-start region)

#### Scenario: Phase 3 → 4 transition is continuous

- **WHEN** Phase 4 is entered at `β_{p3} = 16.0`
- **THEN** `γ' = ln(15/16) ≈ −0.0645385...` is set, AdamW momentum for `γ` is reset, and `β^eff(Phase 4, t=0) = 16.0` exactly (continuity)

#### Scenario: Counterfactual β_min = 1.0 forces a 5-significant-figure γ_init

- **WHEN** the counterfactual parameterization `β = 1.0 + 31.0 · σ(γ)` is required to reproduce the same `β_0` as the adopted `β^param(γ) = 0.1 + 31.9 · σ(γ)` at `γ_init ≈ −3.5`
- **THEN** the required `γ_init` is `≈ −6.7835` (exact 50-digit mpmath value `−6.783545399795103364342`), NOT `−6.7836` — the latter back-substitutes to `β_0 = 1.0350582488933886469` instead of the spec's `β_0 = 1.035060160968266571803`
- **AND** the test guarding this claim MUST derive `β_0` independently from the adopted-path declaration `γ_init ≈ −3.5` and then invert it to the counterfactual `γ_init` (a cross-reconciliation of two separate spec declarations, not a re-statement of the asserted expression), and MUST assert the 5-sig literal form via `round(γ_full, 4) == -6.7835` so that a half-up rounding of the exact value to `-6.7836` fails the guard
- **AND** the guard tolerance MUST accommodate the rounding error of the 5-sig literal `−6.7835`, stated with its reference frame explicit rather than as a single unlabelled number: in **γ-space** the literal sits `4.54e-5` from the exact root (`|−6.7835 − (−6.783545399795103364342)| = 4.5399795e-5`), and it is this γ-space gap that the normative `abs=1e-4` tolerance bounds (`2.2×` the gap); the *same* discrepancy expressed in **β-space** is `|β(−6.7835) − β_0| = 1.5899599e-6`, consistent with the γ-gap times the local slope `|dβ/dγ| = 31 · σ'(−6.7835) = 0.0350220952386` (`4.5399795e-5 × 0.0350220952386 = 1.5899959e-6`, matching the exact β residual to `2.3e-5` relative). A tolerance near machine epsilon is NOT valid for a 5-significant-figure literal. (For contrast the rejected `−6.7836` literal has β-space residual `1.9120749e-6` at slope `0.0350186011251` — only `20%` larger than the `−6.7835` residual — while its γ-space gap is `5.46e-5` rather than `4.54e-5`. A β-space guard therefore does **not** separate the two literals: any `abs` that admits `1.5899599e-6` also admits `1.9120749e-6`, so the discriminating assertion is necessarily in γ-space — the `round(γ_full, 4) == -6.7835` guard above, which `−6.7836` fails by `1e-4`.)
<a id="req-27"></a>

