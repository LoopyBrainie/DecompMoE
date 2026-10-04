# decompmoe-skeleton Specification

## Purpose
Defines the observable, testable behavior of the DecompMoE skeleton: type-safe contracts (`MVPConfig`, Protocol stubs for `GeometricRouter` / `TerritoryHolder` / `BlockAdapter`) and pure-function mathematical primitives that materialize the geometric-routing design of the main `wayfinder` spec into Python. The skeleton is formalize-only — no executable forward/backward; every public symbol carries a behavioral contract that downstream changes (training, inference, baselines) MUST honor.

## Requirements

<a id="req-1"></a>

### Requirement: Canonical Package And Version Identifier

The package SHALL expose `decompmoe.__canonical_name__ == "DecompMoE"`, `decompmoe.__alias__ == "GeoMoE"`, and `decompmoe.__version__` as a `str` matching PEP 440 semantics. The package SHALL expose a stable `__all__` listing every public symbol introduced by this skeleton. **De-duplication rule (normative):** "every public symbol" means the **de-duplicated union** of the `__all__` entries declared by the 13 submodules — a name declared in more than one submodule counts **once**. At MVP that union is exactly **75** names; together with the 3 package dunders (`__version__`, `__canonical_name__`, `__alias__`) the package-level `__all__` therefore has **78** entries. The **only** cross-module name collision at MVP is `flops_per_token`, declared in both `config` and `metrics` (the `metrics` definition is a passthrough wrapper that mirrors `config.flops_per_token`); the package-level `__all__` MUST bind that name to the `config` definition, and the `metrics` definition MUST remain reachable as `decompmoe.metrics.flops_per_token`. **MUST NOT:** summing the 13 per-module counts without de-duplication yields **76** and is not the expected total. The alias SHALL NOT appear as a code identifier anywhere in the package (only in design prose / docstrings).

#### Scenario: Name resolution
- **WHEN** `decompmoe.__canonical_name__` is accessed
- **THEN** it returns the literal string `"DecompMoE"`

#### Scenario: Alias preserved
- **WHEN** `decompmoe.__alias__` is accessed
- **THEN** it returns the literal string `"GeoMoE"` for documentation continuity

<a id="req-2"></a>

### Requirement: Total And Active Parameter Estimator

The package SHALL provide `compute_total_and_active(cfg) -> tuple[int, int]` whose first element is the total parameter count (dense embeddings + attention + all N_e SwiGLU experts + geometric router) and second element is the per-token active parameter count (attention + k experts at width `d_ffn`). Both values SHALL equal the closed-form totals exactly when `cfg == MVPConfig()`: `total == 452_329_984` and `active == 100_008_448`. The accounting MUST derive each term exactly:
- `P_emb = V · d_model = 32_000 · 1024 = 32_768_000`
- `P_attn/layer = 4 · d_model² = 4_194_304` (Q/K/V/O; GQA degenerates to MHA at MVP since `H_kv · d_k = d_model`)
- `P_expert = 3 · d_model · d_ffn = 6_291_456` (SwiGLU 3-matrix)
- `P_router/layer = H_kv · (2 · d_k · d_c + d_c) = 8 · (2 · 128 · 16 + 16) = 32_896` (W^K, W^V projections + bias; NOT a rounding residual — this is exact)
- `P_total = P_emb + L · (P_attn/layer + N_e · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 100_663_296 + 32_896) = 452_329_984`
- `P_active = P_emb + L · (P_attn/layer + k · P_expert + P_router/layer) = 32_768_000 + 4 · (4_194_304 + 12_582_912 + 32_896) = 100_008_448`

LayerNorm gains, `β_i`, `c_i` are excluded from the estimator (not exposed as learnable parameters in `MVPConfig` at MVP scale). **`W^O` is NOT excluded**: it is included in `P_attn/layer = 4 · d_model²` (Q/K/V/O) in the accounting above. Excluding it would give `452_329_984 − L·d_model² = 452_329_984 − 4_194_304 = 448_135_680` (−0.9273%), which is **not** the closed form; the implementation and all tests stand on the closed-form side. (This line restates master `wayfinder` Req 11 assumption 4 rather than copying it verbatim, and no longer claims a verbatim match.)

#### Scenario: 452M / 100M agreement
- **WHEN** `compute_total_and_active(MVPConfig())` is called
- **THEN** the first value equals `452_329_984` exactly and the second equals `100_008_448` exactly (closed-form, no interval; each term derived from the four accounting assumptions)

<a id="req-3"></a>

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

<a id="req-4"></a>

### Requirement: Wire-Level Contracts

The package SHALL provide `Protocol` classes `GeometricRouter`, `TerritoryHolder`, and `BlockAdapter` that expose ONLY the methods/attributes required by Req 3, 4, 16, 17, 18. `GeometricRouter` SHALL declare `extract_C(K, V) -> Tensor`, `gating_logits(C) -> Tensor`, `route(x, logits) -> Tensor`. `GeometricRouter` SHALL NOT declare any `kv_cache_c` attribute (Req 16 / 17 violation would be caught statically). `TerritoryHolder` SHALL declare `territory_volume() -> float`, `active_territories() -> set[int]`, `coverage_balance_loss() -> Tensor`. `BlockAdapter` SHALL declare `forward_residual(x, ...) -> Tensor`. None of these Protocols SHALL contain an executable body (signatures only).

#### Scenario: Router signatures present
- **WHEN** `GeometricRouter` is inspected via `typing.get_type_hints` or `inspect.signature`
- **THEN** `extract_C`, `gating_logits`, `route` are listed and `kv_cache_c` is absent from the annotation set

<a id="req-5"></a>

### Requirement: Inverse-Temperature Sigmoid With Gradient Bounds

The package SHALL provide `inverse_temperature(γ) -> Tensor` implementing `β = β_min + (β_max − β_min) · σ(γ)`, where `β_min == 0.1` and `β_max == 32`. The function SHALL be implemented with `torch.sigmoid` and SHALL be fully differentiable with respect to `γ`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (= `0.5 · (β_max − β_min)`).

#### Scenario: Endpoint agreement
- **WHEN** `γ → −∞` (e.g. `γ = −50.0`)
- **THEN** `inverse_temperature(γ) ≈ 0.1` within `1e-3`

#### Scenario: Upper endpoint agreement
- **WHEN** `γ → +∞` (e.g. `γ = 50.0`)
- **THEN** `inverse_temperature(γ) ≈ 32.0` within `1e-3`

#### Scenario: Monotonicity
- **WHEN** `γ₁ < γ₂`
- **THEN** `inverse_temperature(γ₁) < inverse_temperature(γ₂)`

#### Scenario: Gradient bound on ∂logit/∂C
- **WHEN** `torch.autograd.gradcheck` is run on `logit = β · (Cᵀc − 1)` with `β ≤ β_max`
- **THEN** `‖∂logit/∂C‖₂ ≤ β_max = 32.0`

<a id="req-6"></a>

### Requirement: Voronoi Self-Consistency Threshold

The package SHALL provide `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` returning the closed-form Voronoi half-angle on `S^{signature_dim − 1}`, computed as the unique `θ ∈ (0, π/2]` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e` (regularized incomplete beta function). The implementation MUST compute this value via bisection on the equation (residual `< 1e-9`, holding in **both** reference frames of `openspec/specs/governance/spec.md` req-gov-1 §4 — once `src/decompmoe/sphere.py::_betainc_regularized` conforms to its declared intent the two frames coincide, so no systematic frame offset remains to disambiguate), NOT via a hard-coded table. The package SHALL also provide `voronoi_angle(centroids: Tensor) -> float` for the offline measurement layer (NOT for use in the training hot path). It MUST return the mean per-cell equivalent-cap radius `θ̂ = (1/N_e) · Σ_i G⁻¹(A_i)` over the realised spherical Voronoi cells, where `A_i` is the area fraction of cell `i` and `G(θ) = ½ · I_{sin²θ}((d_c − 1)/2, 1/2)` for `θ ∈ (0, π/2]` with the reflected branch `G(θ) = 1 − ½ · I_{sin²θ}((d_c − 1)/2, 1/2)` for `θ ∈ (π/2, π)`. The reflected branch is REQUIRED for totality: the small-cap branch saturates at `G(π/2) = 0.5`, so any cell holding more than half the sphere is invertible only through it (guarded by `tests/test_sphere.py::test_voronoi_angle_reflected_cap_branch_n_e_2`). `A_i` MUST be estimated by seeded Monte-Carlo over `VORONOI_AREA_SAMPLES` uniform probes on `S^{d_c − 1}`, each assigned to its `argmax` site, with the sample count and the seed fixed as module constants (`1_000_000` and `20260929`) so the returned value is deterministic. `centroids` MUST be unit-norm (`‖c_i‖₂ = 1`, tolerance `1e-6`): the owner of a probe is `argmax_i (p̂ · c_i)`, which selects the nearest site BY ANGLE only when every norm is `1`, since otherwise the inner product is scaled by `‖c_i‖₂` and the realised tessellation silently differs from the caller's intent; a deviation beyond the tolerance MUST be rejected with `ValueError` rather than absorbed. The probe block MUST be cast to `centroids.dtype` so a `float64` tensor is accepted and agrees with the `float32` result (guarded by `tests/test_sphere.py::test_voronoi_angle_rejects_non_unit_centroids` and `tests/test_sphere.py::test_voronoi_angle_honours_centroid_dtype`). Because `canonical_voronoi_angle(N_e, d_c) = G⁻¹(1/N_e)`, the deviation `D := canonical_voronoi_angle(N_e, d_c) − θ̂` is an equal-area deviation that vanishes at the equal-area ideal. When every realised cell is smaller than a hemisphere, `∀i: A_i < 0.5` — the only precondition the one-sided bound needs, because `G` is STRICTLY CONVEX on the whole of `(0, π/2)`: differentiating the defining closed form gives `G'(t) = sin^(d_c−2)(t) / B((d_c−1)/2, ½)` and `G''(t) = (d_c−2)·sin^(d_c−3)(t)·cos(t) / B((d_c−1)/2, ½)`, and every factor is strictly positive for `d_c ≥ 3` and `0 < t < π/2`, so `G''` has NO interior zero; extending to the reflected branch (`t ∈ (π/2, π)`, where only `cos t` changes sign) the unique zero of `G''` on `(0, π)` is `t = π/2`, a smooth inflection point rather than a branch end. **Degenerate case `d_c = 2`**: `signature_dim = 2` is a reachable input (the implementation rejects only values `< 2`), and then `G(θ) = θ/π` is affine with `G'' ≡ 0`; strict convexity degenerates to an identity, Jensen's inequality becomes an equality, and the one-sidedness bound above LOSES ITS DERIVATION PRECONDITION — for `d_c = 2` it MUST be carried by `∀i: A_i < 0.5` alone. Guarded by `tests/test_sphere.py::test_voronoi_angle_precondition_is_area_below_half`. Therefore `G⁻¹` is concave on the matching area interval `(0, 0.5)`, and Jensen's inequality gives `θ̂ ≤ G⁻¹((1/N_e)·Σ_i A_i) = G⁻¹(1/N_e) = canonical_voronoi_angle(N_e, d_c)` with equality iff `A_1 = ⋯ = A_{N_e}`, so `D ∈ [0, canonical_voronoi_angle(N_e, d_c)]`. `G⁻¹`'s concavity does NOT extend past a hemisphere: for `A_i > 0.5` the reflected branch takes over. The one-sided bound MUST therefore NOT be asserted unconditionally — beyond a hemisphere it is OBSERVED BEHAVIOUR, NOT A THEOREM, and is guarded as a direction check by `tests/test_sphere.py::test_voronoi_angle_one_sided_gap`. A cell capturing no probe has `A_i = 0` and contributes `G⁻¹(0) = 0` to the mean, biasing `θ̂` downward; this is mathematically correct (a zero-area cell has zero equivalent-cap radius), is REQUIRED because the one-sidedness witnesses deliberately pass exact duplicate sites, and signals a degenerate tessellation rather than a sampler failure. The per-cell form is load-bearing: spherical Voronoi cell areas always sum to 1, so `G⁻¹((1/N_e)·Σ_i A_i) ≡ G⁻¹(1/N_e)` for EVERY centroid set, and an implementation that inverts the mean area instead of inverting per cell returns the canonical angle unconditionally — a constant that certifies nothing and is guarded by `tests/test_sphere.py::test_voronoi_angle_not_degenerate_mean_area_form`. At MVP `d_c = 16`, `canonical_voronoi_angle(N_e=16, d_c=16)` SHALL return `1.173548 rad` (within `abs=1e-6` rad per `openspec/specs/governance/spec.md` req-gov-1 §3, with the bisection residual `< 1e-9` in the impl-internal frame per `openspec/specs/governance/spec.md` req-gov-1 §4); its 4-decimal prose display `≈ 1.1735 rad (≈ 67.24°)` is the canonical spec form frozen in `CLAUDE.md` §5 and MUST NOT be paired with the `abs=1e-6` tolerance, because the canonical value `1.1735474259197175` is `4.74e-5` away from that 4-decimal literal (`47×` the tolerance) — the 4-decimal display is instead guarded by exact `round(θ, 4) == 1.1735` and `round(math.degrees(θ), 2) == 67.24`. The returned angle is strictly greater than the specialist-collapse boundary `θ_{1/e}(β=16) = arccos(1 − 1/β) = arccos(15/16) ≈ 20.36°`. `canonical_voronoi_angle(N_e=64, d_c=16)` SHALL return `1.020506 rad` (within the same `abs=1e-6` bound), displayed as `≈ 1.0205 rad (≈ 58.47°)` and guarded by `round(θ, 4) == 1.0205` / `round(math.degrees(θ), 2) == 58.47`. The associated `versine_Voronoi = 1 − cos θ` (NOT `D_chord` which is the square root `√(2(1 − cos θ))`) is the cap height / spherical versine. The previous closed-form bound `arctan(π / √d_c) ≈ 38.146°` is incorrect (depends on `d_c` only, contradicts MVP geometry, and self-contradicts the same-sentence `θ_{1/e} ≈ 20.36°` value via the wrong formula `arctan(1/β) = 3.58°`); it MUST NOT appear in any implementation. (The 6-decimal test literals and their 4-decimal canonical spec display are disambiguated in `openspec/specs/governance/spec.md` req-gov-1 §3; `wayfinder` Req 11 states the same two-tier contract in its own prose and is NOT a verbatim mirror of this paragraph.)

#### Scenario: MVP self-consistency
- **WHEN** `canonical_voronoi_angle(num_experts=16, signature_dim=16)` is called
- **THEN** the returned angle satisfies `|½ · I_{sin²θ}(7.5, 0.5) − 1/16| < 1e-9` (impl-internal frame per this Requirement's body) AND has 4-decimal display `round(θ, 4) == 1.1735` / `round(math.degrees(θ), 2) == 67.24` AND exceeds `θ_{1/e}(β=16) ≈ 20.36°` (the specialist-collapse boundary)

#### Scenario: N_e dependence of voronoi_angle
- **WHEN** `canonical_voronoi_angle(num_experts=64, signature_dim=16)` is called
- **THEN** the returned angle satisfies `|½ · I_{sin²θ}(7.5, 0.5) − 1/64| < 1e-9` (impl-internal frame per this Requirement's body) AND has 4-decimal display `round(θ, 4) == 1.0205` / `round(math.degrees(θ), 2) == 58.47` (the function depends on both `num_experts` and `signature_dim`, not `signature_dim` alone)

#### Scenario: Bisection output + narrative precision disclosure

- **WHEN** reviewing the MVP self-consistency Scenario above (`≈ 1.1735 rad`) and the N_e-dependence Scenario above (`≈ 1.0205 rad`)
- **THEN** the reader understands:
  - `≈ 1.1735 rad` / `≈ 1.0205 rad` are narrative prose at ~4-decimal precision; NOT exact bisection values
  - The **canonical** Voronoi half-angle is the root of `½ · I_{sin²θ}(7.5, ½) = 1/N_e` — a mathematically-defined value, NOT the output of any particular implementation: `1.1735474259197175 rad` (N_e=16) / `1.0205068247837132 rad` (N_e=64) at 16-decimal precision. The implementation MUST reproduce it within `abs=1e-6` per `openspec/specs/governance/spec.md` req-gov-1 §3
  - The bisection residual `|½ · I_{sin²θ}(7.5, ½) − 1/N_e|` at that canonical root is `1.4635872379108090131680874e-17` (N_e=16) / `1.9420345120803994000206689e-18` (N_e=64) This quantity is set by the bisection stopping criterion (|G - 1/N_e| < 1e-13), not by float64 precision; provenance is mpmath betainc(a, b, 0, x, regularized=True) at dps=60, reproducible via change 2026-10-02-repair-spell-numeric-literal-provenance evidence/_alpha_forensics.py. — far below the `< 1e-9` bound pinned by `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9`, and identically so in the impl-internal frame because the two frames coincide. That residual test is therefore NOT an independent check on the integrator: its independent guard is the 6dp literal test, where the truncated literal `1.173547` sits `1.275e-6` from the pre-fix output `1.1735482746999482` (so it FAILS at `abs=1e-6`) and `4.259e-7` from the canonical value (so it PASSES)
  - **Units are not interchangeable.** §3's `< 1e-6` is an **angle** tolerance in **radians**; the residual above is a dimensionless **area fraction**. The like-for-like comparison is the angular deviation `1.275e-6 rad` between a 6dp literal and the implementation, which is what §3's tolerance actually bounds. **Superseded**: the earlier text compared the area-fraction residual `4.15e-7` against the `1e-6` angle tolerance, and cited "mpmath `betainc(regularized=True)`" — that 3-argument call returns `1 − I_x` (measured: `0.8691458` where `I_x = 0.1308542`), so the citation was wrong even though its number `4.15e-7` had in fact been computed with the correct 4-argument form `betainc(a, b, 0, x, regularized=True)`
  - **Superseded**: the previously quoted θ-discrepancy `~8.49e-7 rad` (N_e=16) / `~8.79e-9 rad` (N_e=64) and the `< 1 ppm` / `6.63 ppm` bounds were measures of `_betainc_regularized`'s systematic error (`8.29147e-7` in `I_x`; `0.72326 ppm` / `0.00861 ppm` in θ; `6.63313 ppm` relative in `I_x`). With the integrator conforming to its declared intent these collapse to the quadrature error of a single implementation, leaving the two-frame apparatus without content

#### Scenario: no hard-coded table values
- **WHEN** `src/decompmoe/sphere.py` is grepped for the MVP values `0.9076`, `0.4494`, `0.380`, `0.0971`
- **THEN** zero matches (no fast-path table — every input must bisect)

#### Scenario: Realized measurement layer reproduces the canonical angle on an exactly equal-area tessellation

- **WHEN** `voronoi_angle(centroids)` is called on any exactly equal-area spherical Voronoi tessellation of `S^{d_c − 1}` — concretely the 32 crosspolytope vertices `±e_i` at `(N_e=32, d_c=16)`, and `N = 16` / `N = 8` equally spaced sites on a single great circle
- **THEN** the returned `θ̂` reproduces `canonical_voronoi_angle(N_e, d_c)` within the statistical tolerance `abs=1e-3` degrees prescribed by `openspec/specs/governance/spec.md` req-gov-1 obligation 7 (measured gaps `6.4561e-5°`, `2.4817e-5°` and `2.2667e-5°` respectively at `VORONOI_AREA_SAMPLES = 1_000_000`, `VORONOI_AREA_SEED = 20260929`)
- **AND** the great-circle cases are part of this Scenario because the point set is degenerate — it spans 2 of `d_c` dimensions — while the tessellation is still exactly equal-area, so the Scenario separates "the sites look spread out" from "the cells are equal-area", which is the distinction a Voronoi-based self-consistency measure must track
- **AND** `tests/test_sphere.py::test_voronoi_angle_known_answer_crosspolytope` additionally guards that neither superseded output reappears: `115.6651°` (mean pairwise chord fed into the versine slot) and `91.5415°` (the same defect with a corrected inversion) are each more than `1°` away from the returned value

#### Scenario: Realized measurement layer is one-sided and not the degenerate mean-area form

- **WHEN** `voronoi_angle(centroids)` is called on configurations whose cells are far from equal-area — `8` exact duplicates of `e_1` among 16 sites, `4` duplicates among 16, and an antipodal pair `±e_1` with 14 sites squeezed near `e_1`
- **THEN** `canonical_voronoi_angle(N_e, d_c) − θ̂ ≥ 0` in every case (measured gaps `26.8528°`, `11.3373°` and `2.5047°`, i.e. `3.67e5×`, `1.55e5×` and `3.43e4×` of the estimator's `5σ = 7.31e-5°`, which is what makes a strict non-negativity assertion meaningful rather than flaky)
- **AND** for the same configurations `θ̂ < canonical_voronoi_angle(N_e, d_c) − 1.0°` (measured separations `26.85°` and `2.50°` against the `1.0°` threshold), which is the guard against the degenerate form `G⁻¹(mean_i A_i)`: that form returns the canonical angle for every input and would produce a separation of exactly `0`

#### Scenario: d_c = 2 affine degeneration

- **WHEN** `canonical_voronoi_angle(num_experts, signature_dim=2)` or `_cap_area(θ, 2)` is evaluated
- **THEN** in **exact real arithmetic** `G(θ) == θ/π` identically on `(0, π/2]` (because `I_x(½, ½) = 2·arcsin(√x)/π` and `x = sin²θ`), so `G'' ≡ 0`, `G` is affine, strict convexity degenerates to an identity, and `G(θ) = 1/N_e` solves to `θ = π/N_e` — in particular `canonical_voronoi_angle(N_e, 2) == π/2` exactly
- **AND** the one-sidedness bound `canonical_voronoi_angle(N_e, 2) − θ̂ ≥ 0` is NOT a theorem in this degenerate case: it rests only on `∀i: A_i < 0.5`, since strict convexity of `G` no longer holds
- **AND** the implementation DOES attain that identity. `_betainc_regularized` substitutes `t = sin²φ`, under which the integrand becomes `2·sin^(2a−1)φ·cos^(2b−1)φ dφ`; at `d_c = 2` the exponent is `2a−1 = 0`, so the `u^(−1/2)` left-endpoint singularity of the raw `t` integrand is removed EXACTLY rather than subdivided around, and an adaptive 8/16-point Gauss–Legendre rule covers what remains. Measured against exact `G` at the identical float argument the implementation consumed, the residual is flat at `≤ 3.23e-16` across this Scenario's own 9-point sweep (1° / 20° / 37° / 60° / 81.34° / 89° / 89.9° / 89.999° / 89.99999° — measured max `3.2294e-16` at 81.34°, and `≤ 3.3798e-16` over a dense 2001-point sweep of `(0°, 90°]`); against `θ/π` it rises to `7.60e-11` **relative to `θ/π`** (absolute `3.7976e-11`) at `θ = 89.99999°`, which is an ARGUMENT-conditioning artefact — `x = sin²θ` carries an absolute float64 error `~1.1e-16` that `1 − x` inherits in full near `π/2` and `G`'s sensitivity there is `~1/(2·sqrt(1−x))` — not a quadrature residual. `canonical_voronoi_angle(N_e, 2)` deviates from `π/N_e` by an amount **independent of `N_e`** (`≈ 4.46e-14` absolute at every `N_e` measured), because bisection converges on an absolute `θ` bracket (`break < 1e-13`); the RELATIVE deviation is therefore exactly proportional to `N_e` (`rel_dev / N_e = 1.42e-14` for `N_e = 4 / 8 / 16 / 32 / 64`) and has **no finite supremum**, which supersedes the retired “monotonically increasing toward 5.3994%” claim. The `N_e = 2` case still looks accurate (`6.71e-9` **relative to `π/N_e`**, absolute `1.0537e-8`) only because bisection lands on the `x >= 1.0` early-return plateau at `π/2` — i.e. on the plateau disclosed in `canonical_voronoi_angle` — not because the quadrature is accurate there. Tests MUST pin the same-argument residual and the cross-parameterization band SEPARATELY, and MUST re-verify the exact identity independently of the implementation (mpmath), so that a regression in the quadrature surfaces as a test failure instead of passing silently behind the conditioning band.

<a id="req-7"></a>

### Requirement: C Extraction Four-Step Pipeline

The package SHALL provide `extract_C(K, V, proj_W_K, proj_W_V, proj_b, *, H_kv, d_c, eps=1e-6) -> Tensor` implementing the spec's exact four-step pipeline: (1) per-head projection `z^{l,h} = W_K^{l,h} · k^{l,h} + W_V^{l,h} · v^{l,h} + b^{l,h}`; (2) per-head spherical projection; (3) cross-head mean with `1/H_kv` factor; (4) final spherical projection. The pipeline SHALL be fully differentiable (D-path, no Straight-Through Estimator; no `.detach()` between intermediate tensors).

#### Scenario: Output shape on unit sphere
- **WHEN** `K ∈ R^{B × H_kv × N × d_k}` and `V ∈ R^{B × H_kv × N × d_k}` are fed in
- **THEN** `C ∈ R^{B × N × d_c}` and `‖C_t‖₂ = 1` for every token (within `1e-5`), **provided the degenerate regime is excluded** — i.e. provided the **cross-head mean** `z̄_t^l = (1/H_kv) · Σ_h ẑ^{l,h}` satisfies `‖z̄_t^l‖₂ ≥ ε` with `ε = 1e-6` (req-19). This precondition is normative, not a caveat, and it MUST be stated on the **mean** rather than on the per-head terms: step 4 divides by `max(‖z̄‖₂, ε)`, so the quantity that decides the output norm is `‖z̄‖₂`, not any individual `‖z^{l,h}‖₂`. Conditioning on the per-head norms is **insufficient** — at `H_kv = 8` with four heads projecting to `+e₀` and four to `−e₀` (all `‖z^{l,h}‖₂ = 1.0`, so the per-head form of this precondition is satisfied) the mean is exactly `0` and `extract_C` returns `‖C_t‖₂ = 0.0`, violating this Scenario's own `‖C_t‖₂ = 1` bound. The per-head sub-epsilon regime `0 < ‖z^{l,h}‖₂ < ε` named in req-19 remains a separate, sufficient-to-violate case, and is subsumed by the mean form. This Scenario previously asserted unit norm **unconditionally**, which contradicted req-19; an earlier revision of this same correction conditioned on the per-head norms and was still falsifiable, which is why the condition is now on `z̄`.

#### Scenario: Fully differentiable
- **WHEN** `torch.autograd.gradcheck` is run on `extract_C` with random `K`, `V` and the projection parameters
- **THEN** the gradient check passes with ATOL `1e-5` and no NaN

#### Scenario: Per-token MAC closed form
- **WHEN** the per-token operation count of `extract_C` is computed under the pinned **MAC** convention (1 MAC = 1 multiply + 1 accumulate; FLOPs = 2·MACs)
- **THEN** per-token MACs equal `H_kv · (2 · d_k · d_c + d_c) + H_kv · d_c + H_kv · d_c + d_c` — i.e. (i) per-head K/V/bias projection: `H_kv · (2 · d_k · d_c + d_c)` MACs, (ii) per-head L2-normalization (numerator/denominator ops only; sqrt counts as 0 MAC): `H_kv · d_c` MACs, (iii) cross-head mean with the `1/H_kv` factor (step 3 of the pipeline: a `H_kv`-long accumulation and rescale, i.e. `H_kv` multiply-accumulates over `d_c` values each): `H_kv · d_c` MACs, (iv) final L2-normalization: `d_c` MACs. At MVP (`H_kv=8, d_k=128, d_c=16`) this evaluates to `8·4112 + 8·16 + 8·16 + 16 = 32_896 + 128 + 128 + 16 = 33_168` per-token MACs exactly (within `abs=1`). Tests MUST assert the closed form (or its MVP specialization), NOT a profiler-derived op count.

#### Scenario: Cross-head awareness
- **WHEN** `H_kv = 8` GQA input is processed
- **THEN** the cross-head mean uses the `1/H_kv` factor (mathematical equivalence to a manual `mean(..., dim=1)`)
<a id="req-8"></a>

### Requirement: Isotropic Squared-Chord Distance And Logit

The package SHALL provide `squared_chord(C, c_i) -> Tensor = 1 − Cᵀc_i` and `logit(C, c_i, β) -> Tensor = β · (Cᵀc_i − 1)`. The `logit` function signature SHALL NOT contain a parameter named `w_i` (A4-2 / CLAUDE.md §6 invariant). The output range of `squared_chord` SHALL be `[0, 2]`; the output range of `logit` SHALL be `[−2β, 0]`.

#### Scenario: Antipodal distance
- **WHEN** `C` and `c_i` are antipodal on `S^{d_c−1}` (e.g. `d_c = 2`, `C = [1, 0]`, `c_i = [−1, 0]`)
- **THEN** `squared_chord(C, c_i) == 2.0`

#### Scenario: Zero distance at alignment
- **WHEN** `C == c_i`
- **THEN** `squared_chord(C, c_i) == 0.0` and `logit(C, c_i, β) == 0.0`

#### Scenario: No w_i in signature
- **WHEN** `inspect.signature(logit)` is examined
- **THEN** no parameter named `w_i` (or any scalar per-expert weight) is present

<a id="req-9"></a>

### Requirement: Top-K Sparse Mask With Local Softmax

The package SHALL provide `topk_mask_with_neg_inf(logits, k) -> Tensor` masking non-top-k entries with `−float("inf")` (NOT a large finite negative). It SHALL provide `local_softmax(masked_logits) -> Tensor` that exponentiates only over the non-`-inf` entries and normalizes so `Σ_i p_i == 1` over the active set. The forward equation `x_out = x + Σ_{i ∈ I_k} p_i · Expert_i(x)` SHALL be the ONLY routing equation present in the `gating` module (grep test).

#### Scenario: Sentinel is −inf
- **WHEN** `topk_mask_with_neg_inf(logits, k=2)` is applied
- **THEN** non-top-k entries are exactly `-float("inf")` (verified via `torch.isinf` + sign check)

#### Scenario: Partition of unity
- **WHEN** `local_softmax(masked_logits)` is computed
- **THEN** `Σ_i p_i == 1.0` over the top-k active set (within `1e-6`)

#### Scenario: Zero gradient on masked entries
- **WHEN** `torch.autograd.grad(p_k, logits)` is called for masked indices
- **THEN** the gradient component is exactly `0.0`

<a id="req-10"></a>

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

<a id="req-11"></a>

### Requirement: Loss Composition With Staged Lambda

The package SHALL provide `L_total(task_logits, targets, f_per_expert, p_per_expert, c_centroids, phase, step, *, cfg) -> LossParts` returning a dataclass with `.L_CE`, `.L_lb`, `.L_sep`, `.L_total` fields. The constants SHALL be: `α = 0.01` (Switch-style fixed weight on `L_lb`), `λ(t)` schedule = `0` for `phase ∈ {1, 2}`, cosine ramp `0 → 0.001` during `phase == 3`, and `0.001` fixed for `phase == 4`. The `L_lb` closed form MUST be `L_lb = N_e · Σ_i f_i.detach() · P_i`, where `P_i = (1/T) · Σ_t p_i(C_t)` is the per-expert differentiable soft routing probability; gradient MUST flow through `P_i` and be blocked through `f_i.detach()`. The previous "verified by source grep" acceptance is incorrect (permits any expression containing `.detach()`); it MUST be replaced by the testable invariant `∂L_lb / ∂P_i ≠ 0` AND `∂L_lb / ∂f_i ≡ 0`. `L_sep` SHALL equal `(‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form); the `Σ_{i<j}` equivalent form MUST use factor `2/(N_e(N_e − 1))` — the factor `1/(N_e(N_e − 1))` is INCORRECT and MUST NOT appear. (Matches master `wayfinder` Req 12 verbatim.)

#### Scenario: Alpha pinned to 0.01
- **WHEN** `L_total(...)` is evaluated with uniform `f = P = 1/N_e`
- **THEN** `L_lb_raw = N_e · Σ (1/N_e) · (1/N_e) = 1.0` exactly and the `L_lb` contribution equals `0.01 · 1.0 = 0.01` exactly regardless of phase

#### Scenario: Lambda zero in phases 1 and 2
- **WHEN** `phase ∈ {1, 2}`
- **THEN** the `L_sep` contribution equals `0.0` within `abs=1e-12` (i.e. `λ(t) == 0`)

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

<a id="req-12"></a>

### Requirement: Five Numerical Safeguard Helpers

The package SHALL provide five standalone helpers in `safeguards.py`: (1) `clip_global_grad_norm_(params, max_norm: float = 1.0) -> float` returning the pre-clip norm as a `float` (NOT `Tensor` — code-review N6 fix: `src/decompmoe/safeguards.py::clip_global_grad_norm_` returns `float(pre_clip_norm.item() ...)`); (2) `nan_ladder(consecutive_nan) -> tuple[str, float, bool]` returning `(action, lr_scale, halt)` where `action ∈ {"skip", "div_lr_10", "halt"}` for counts `(1, 3, 10)` respectively; (3) `should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]`; when `threshold=None`, the implementation calls `_dead_expert_threshold(N_e) = 1/(2·N_e)` to derive the effective threshold (at MVP `N_e = 16`, this yields `1/32`); (4) `beta_saturation_warning(β_per_expert: Tensor) -> bool` returning `True` when any `β_i > BETA_SATURATION_WARN = 30.4` (= `0.95 · BETA_MAX = 0.95 · 32`) — there is NO `β_max` parameter (code-review N7 fix: `src/decompmoe/safeguards.py::beta_saturation_warning` signature has no `β_max`; the warning threshold is sourced from the module-level `BETA_MAX` constant via `BETA_SATURATION_WARN: Final[float] = 0.95 * BETA_MAX`); (5) `loss_spike_defense(L_task: float, L_task_ema: float, phase: int, ratio: float = LOSS_SPIKE_RATIO) -> bool` returning `True` when `phase ≥ 3 and L_task > ratio · L_task_ema` — there is NO `*` keyword-only separator before `ratio` (code-review N8 fix: `src/decompmoe/safeguards.py::loss_spike_defense` defines `ratio: float = LOSS_SPIKE_RATIO` as POSITIONAL_OR_KEYWORD); the function ONLY returns the boolean — the LR-scaling action (`LR × LOSS_SPIKE_LR_SCALE = LR × 0.8`) is the CALLER's responsibility (the function emits a "should scale" signal, not the scaling itself). The dead-expert threshold `1/(2·N_e)` replaces the previous hardcoded `1/128` (which was the `N_e=64` instantiation of the same `1/(2·N_e)` rule); at MVP `N_e = 16` this evaluates to `1/32`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200`, `RESURRECTION_RATE_LIMIT_STEPS = 1000`, `LOSS_SPIKE_RATIO = 2.5`, `LOSS_SPIKE_LR_SCALE = 0.8`, `BETA_SATURATION_WARN = 30.4`, `BETA_SATURATION_HALVE = 28.8` are `Final[int]` / `Final[float]` module-level constants (see `src/decompmoe/safeguards.py` 的模块级 `Final` 常量块（`BETA_SATURATION_WARN` / `DEAD_EXPERT_CONSEC_STEPS`）`); the spec references the constant identifiers rather than literal values. The standard step order SHALL be: `Backward → clip_grad_norm(1.0) → optimizer.step() → L2_norm(c_i)` (asserted via documented ordering constant `STEP_ORDER`).

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `src/decompmoe/safeguards.py:71-80` at commit `d3689a1`. The `nan_ladder` action Literal member `div_lr_10` (formerly `halve_lr` before archived change `2026-09-13-fix-nan-ladder-action-name-and-loss-spike-test-coverage`) carries the `lr_scale = 0.1` value (LR ÷ 10 per `wayfinder Req 13 Numerical Safeguards (#req-13)` wording, NOT LR ÷ 2 as the legacy name suggested); renaming aligns action name with actual scaling math.; change `2026-09-29-fix-b10-b11-b12-test-guard-fidelity` design.md (Decision 1 — rate-limit boundary pinned: guard defers iff `Δ < R`; `Δ = R` is not deferred; window-partition claim withdrawn as false)

#### Scenario: Global clip threshold
- **WHEN** `clip_global_grad_norm_(params, max_norm=1.0)` is called with `‖g‖₂ > 1.0`
- **THEN** all gradients are scaled to `‖g‖₂ ≤ 1.0`

#### Scenario: NaN escalation ladder
- **WHEN** `nan_ladder(c)` is called for `c ∈ {1, 3, 10}`
- **THEN** the returned tuple is `("skip", 1.0, False)` / `("div_lr_10", 0.1, False)` / `("halt", 1.0, True)` respectively

#### Scenario: NaN ladder default at consecutive_nan=0 (no NaN observed)
- **WHEN** `nan_ladder(0)` is called
- **THEN** the returned tuple is `("skip", 1.0, False)` — defensive default: when no NaN has been observed yet, the ladder falls back to skip-and-keep-LR (caller is expected to call only when a NaN flag has been raised). For `c ∉ {1, 3, 10}` and `c > 0` (e.g. `c=2`, `c=5`, `c=9`), the ladder returns the highest-priority tier that has been crossed: `c ∈ [1, 2] → ("skip", 1.0, False)`; `c ∈ [3, 9] → ("div_lr_10", 0.1, False)`; `c ≥ 10 → ("halt", 1.0, True)` (this matches wayfinder Req 13 'Numerical Safeguards' strict-greater-than ladder tiers (anchor `#req-13`) and is the implementation in `safeguards.py::nan_ladder`).

#### Scenario: Resurrection rate-limited
- **WHEN** `should_resurrect(f_history, current_step, last_resurrection_step, ...)` is called, with `Δ := current_step − last_resurrection_step` and `R := RESURRECTION_RATE_LIMIT_STEPS` (at MVP `R = 1000`)
- **THEN** the rate-limit guard defers the call — returning `set()` at `safeguards.py::should_resurrect` (the rate_limit_steps branch) — **if and only if** `Δ < R`; for `Δ ≥ R` the guard does not defer and the call proceeds to the dead-expert trigger. `Δ = R` is therefore **not** deferred: it is the first step the guard lets through. The helper may still return `set()` for reasons unrelated to rate limiting — `len(f_history) < consec` (`safeguards.py::should_resurrect`, the consec branch), or no expert meeting the per-step trigger (`safeguards.py::should_resurrect`, the per-step f_i < threshold branch); those are not deferrals and are outside this Scenario. **Derivation**: the guard predicate `D(Δ) := [Δ < R]` is monotone non-increasing in `Δ` with exactly one jump point, so the deferred set `{Δ : Δ < R}` is a down-open ray and the passing set `{Δ : Δ ≥ R}` an up-closed ray; the two meet at `Δ = R`. The `R`-long half-open-window reading is equivalent to the guard **per pair**: two events `t₁ < t₂` lie in a common window `[t, t + R)` **iff** `∃t. t ≤ t₁ < t₂ < t + R`, which is `⟺ Δ < R`. (The family `{[t, t + R) : t ∈ ℤ}` is **overlapping, not a partition** — `[0, R)` and `[1, R+1)` share `R−1 = 999` elements — so the equivalence is the per-pair existence claim above and never a global block structure; the `R`-aligned blocks `{W_{kR}}` are a genuine partition but do **not** satisfy it, e.g. `t₁ = R−1, t₂ = R` has `Δ = 1 < R` yet straddles two blocks.) Which side `Δ = R` falls on is fixed by the counterexample, not by that reading: under the `≤` alternative the `R`-aligned event stream `0, R, 2R, 3R, …` has every `Δ = R` event deferred and **dropped outright** (the helper returns `set()` and holds no retry queue), so for any caller that advances `last_resurrection_step` no more often than it emits, the realised rate is strictly below one event per `R` steps, contradicting wayfinder Req 13's "rate-limited to once per 1000 steps". (No caller in this repository writes `last_resurrection_step`; the counterexample is therefore stated caller-model-independently rather than by a concrete period.) Guarded by `tests/test_safeguards.py::test_should_resurrect_rate_limit_boundary` (pins `Δ = R−1` → empty, `Δ = R` → non-empty, `Δ = R+1` → non-empty); the mutation that turns it red is flipping `safeguards.py::should_resurrect`'s `<` to `<=`.

#### Scenario: Beta saturation warning threshold
- **WHEN** any single `β_i > 30.4`
- **THEN** `beta_saturation_warning` returns `True` (= 95% of `β_max = 32`)

#### Scenario: Beta saturation global halve threshold
- **WHEN** more than 50% of `β_i > 28.8` (= 90% of `β_max = 32`)
- **THEN** the global halving predicate returns `True`

#### Scenario: Loss spike defense gating
- **WHEN** `phase < 3` (i.e. phase ∈ {0, 1, 2})
- **THEN** `loss_spike_defense` returns `False` even if `L_task > 2.5 · L_task_ema` (defense is Phase-3+ only)

#### Scenario: Step ordering pinned
- **WHEN** `safeguards.STEP_ORDER` is accessed
- **THEN** it equals `("backward", "clip_grad_norm", "optimizer_step", "l2_norm")` exactly

#### Scenario: `should_resurrect` semantic interpretation (per-step vs avg-window)
- **WHEN** the dead-expert trigger is evaluated at time `t` with `f_history` containing the last `consec` snapshots
- **THEN** expert `i` is flagged iff every snapshot `f_history[-consec:][j][i]` satisfies `f_history[-consec:][j][i] < threshold` (per-step strict less-than interpretation). The wayfinder Req 13 wording `f_i^avg < 1/(2·N_e)` for 200 consecutive steps is interpreted as "per-step `f_i < threshold` sustained over the 200-snapshot window" rather than "literal mean-over-window `< threshold`". **Mathematical equivalence disambiguation**: let `H = f_history[-consec:]` be the last `consec` snapshots and `T = threshold`. Two readings are mathematically distinct:
  - **avg-window reading**: `flag_avg(i) ⟺ (1/consec) · Σ_{j=0..consec-1} H[j][i] < T` — i.e., the **windowed temporal mean** of `f_i` falls below threshold.
  - **per-step reading (current code)**: `flag_step(i) ⟺ ∀ j ∈ [0, consec): H[j][i] < T` — i.e., **every** per-step value falls strictly below threshold.

  The relationship is one-directional in general: `flag_step ⟹ flag_avg` **IS** universally true (proved by elementary algebra: `∀ j: H[j][i] < T` ⇒ `Σ_{j=0..consec-1} H[j][i] < consec · T` ⇒ `(1/consec) · Σ_{j=0..consec-1} H[j][i] < T`); the **non-universal** direction is `flag_avg ⟹ flag_step`, demonstrated by the counterexample below. However, on **constant history** (`H[j][i] = v` for all `j`) the two readings agree (both reduce to `v < T`); on **non-constant history** they can disagree. The per-step reading is therefore the **strictly tighter trigger**: any history flagged by per-step is also flagged by avg-window — written as **per-step ⊊ avg-window** (per-step triggers a **strict subset** of the histories that avg-window triggers on; per-step never triggers on a history that avg-window misses, but the converse fails). The current implementation commits to the per-step reading because (a) at MVP `N_e = 16`, the per-expert routing fraction `f_i` already aggregates token-level routing information per step (one snapshot = one batch's per-expert top-k fraction), leaving no temporal smoothing to perform; (b) a single transient spike `f_i ≥ threshold` above the dead-expert threshold within the window correctly suppresses resurrection under per-step, matching the wayfinder Req 13 wording's "for 200 consecutive steps" temporal qualifier (every step must be below, not merely the average over the window).

  **Worked counterexample (per-step vs avg-window divergence on non-constant history)**: let `consec = 200`, `threshold = 1/(2·N_e) = 1/32 ≈ 0.03125`, and consider the history `H[j][i] = 0.005` for `j ∈ [0, 198]` and `H[199][i] = 0.99` (199 sub-threshold steps followed by one super-threshold spike):
  - avg-window: `(199 · 0.005 + 1 · 0.99) / 200 = (0.995 + 0.99) / 200 = 1.985 / 200 = 0.009925` — `0.009925 < 0.03125` ⇒ TRIGGER (resurrect).
  - per-step: `199` sub-threshold checks pass, `0.99 < 0.03125` is FALSE ⇒ NO TRIGGER (do not resurrect).

  Reverse direction: history `H[j][i] = 0.05` for `j ∈ [0, 198]` and `H[199][i] = 0.005` (199 super-threshold steps followed by one sub-threshold step):
  - avg-window: `(199 · 0.05 + 1 · 0.005) / 200 = (9.95 + 0.005) / 200 = 9.955 / 200 = 0.049775` — `0.049775 < 0.03125` is FALSE ⇒ NO TRIGGER.
  - per-step: `199` super-threshold checks fail (`0.05 < 0.03125` FALSE) ⇒ NO TRIGGER.

  Both readings agree on constant history (`H[j][i] = 0.005` everywhere): avg-window `= 0.005 < 0.03125` ⇒ TRIGGER; per-step `0.005 < 0.03125` for every `j` ⇒ TRIGGER.

  **Universal-direction positive worked example (algebra proof's positive complement to Counterexample A; verifies `flag_step ⟹ flag_avg` on non-constant history)**: let `consec = 200`, `threshold = 1/(2·N_e) = 1/32 ≈ 0.03125`, and consider the history `H[j][i] = 0.001` for `j ∈ [0, 198]` and `H[199][i] = 0.030` (every snapshot has every `f_i` strictly below threshold, but the values are non-constant across the window):
  - per-step: every snapshot has every `f_i = 0.001 < 0.03125` AND the final snapshot `f_i = 0.030 < 0.03125` ⇒ all 16 experts TRIGGER.
  - avg-window: `(199 · 0.001 + 1 · 0.030) / 200 = (0.199 + 0.030) / 200 = 0.229 / 200 = 0.001145` — `0.001145 < 0.03125` ⇒ TRIGGER (resurrect).
  - Both readings agree on the TRIGGER side on this non-constant history, confirming the algebra proof's universal direction `flag_step ⟹ flag_avg`: every history that per-step flags is also flagged by avg-window. This is the **positive** counterpoint to Counterexample A's **negative** — together they establish `per-step ⊊ avg-window` (per-step ⊊ set-of-flags-by-avg-window; per-step is a strict subset, not a strict superset and not co-extensive).

  **Notational pin on `f_i^avg`** (wayfinder Req 13): the superscript `avg` is **NOT** "averaged over the 200-step window". It denotes **averaged across experts** (i.e., `f_i` is itself the per-expert routing fraction, an average across tokens within the batch, normalized to sum to 1 across all `N_e` experts at each step). The trigger condition reads in unambiguous form: "the per-expert routing fraction `f_i` (already a cross-expert average within a single step) stays below `1/(2·N_e)` for 200 consecutive steps". The "200 consecutive steps" temporal qualifier pins the per-step reading; a windowed temporal mean would require the qualifier "for 200 steps on average", which the wayfinder Req 13 wording does not contain. Cross-reference: wayfinder Req 13's `f_i^avg` notation is used identically in the `R_H` formula `R_H = −(1/ln N_e) · Σ_i f_i · ln f_i` (wayfinder Req 20 metric definition) where `f_i` is unambiguously a per-step per-expert fraction; the same notation must carry the same meaning in Req 13's `f_i^avg < 1/(2·N_e)` trigger.

  **Open follow-up**: a future ticket adopting avg-window semantics would re-evaluate the trigger condition as `flag_avg(i)` above, and MUST update spec + code + the `test_should_resurrect_current_per_step_semantic_pinned` guard test atomically; the existing guard test in `tests/test_safeguards.py` continues to pin the current per-step behavior.

<a id="req-13"></a>

### Requirement: Five-Phase Schedule State Machine

The package SHALL provide `phase_id(step: int) -> int` returning `0` for `step ∈ [0, 999]`, `1` for `[1_000, 5_999]`, `2` for `[6_000, 25_999]`, `3` for `[26_000, 55_999]`, `4` for `[56_000, 100_000]`. The package SHALL provide `phase_step_frozen_names(phase: int) -> set[str]` returning the **gradient-channel** parameter-name set to freeze per phase (`{"c_i", "beta_i", "W_K", "W_V", "b"}` for phase 1; `{"c_i", "beta_i"}` for phase 2 — `W_K/W_V/b` are unfrozen in phase 2 to allow them to train under the EMA; `{"c_i"}` for phase 3 — `beta_i` is unfrozen; empty for phases 0/4). The package SHALL provide `should_reset_adam(prev_phase: int, next_phase: int) -> bool` returning `True` exactly when `prev_phase == 3 and next_phase == 4`. The advisory signals (`R_H`, `S_load`, `R_β-sat`, `L_sep/WB`) SHALL be exposed via `advisory_signals(...)` but SHALL NEVER trigger phase transitions (state-machine invariance under perturbed advisory is asserted).

#### Scenario: Phase boundaries at 100K
- **WHEN** `total_steps == 100_000`
- **THEN** the phase boundaries are `(1_000, 6_000, 26_000, 56_000, 100_000)` and phase `0 / 1 / 2 / 3 / 4` step ratios are `1% / 5% / 20% / 30% / 44%`

#### Scenario: Phase-0 and Phase-4 freeze-name set is empty
- **WHEN** `phase_step_frozen_names(0)` or `phase_step_frozen_names(4)` is called
- **THEN** the result is exactly `set()` in both cases — NOT `frozenset()`, NOT `None`, and NOT a non-empty set. Phase 0 is spherical K-Means seeding and has **no gradient channel at all** (`wayfinder` `#req-6` (Req 6 C Extraction Differentiability And Centroid Lifecycle): "Spherical K-Means seeding (no gradient, no EMA)"; the phase table under `wayfinder` `#req-27` (Req 27 CentroidDriver Dual-Channel Architecture Contract) records `| 0 | K-Means seeding | Frozen (requires_grad=False) | N/A |`), so the freeze-name set is vacuously empty. This is **not** "everything is frozen", which would instead be the full name set. Phase 4 unfreezes the entire gradient channel (wayfinder req-14), so nothing is frozen. Guarded by `tests/test_schedule.py::test_phase_step_frozen_names_phase_0_and_4_empty_set`.

#### Scenario: Phase-1 router freeze
- **WHEN** `phase_step_frozen_names(1)` is called
- **THEN** the result equals `{"c_i", "beta_i", "W_K", "W_V", "b"}` (the gradient-channel frozen set; driver channel still updates `c_i` via EMA at `α = 0.90`)

#### Scenario: Phase-2 expert freeze
- **WHEN** `phase_step_frozen_names(2)` is called
- **THEN** the result equals `{"c_i", "beta_i"}` (gradient-channel frozen; `W_K/W_V/b` are unfrozen to learn under the driver-channel EMA at `α = 0.95`)

#### Scenario: Adam reset boundary
- **WHEN** `should_reset_adam(3, 4)` is called
- **THEN** it returns `True`; for every other `(prev, next)` pair it returns `False`
<a id="req-14"></a>

### Requirement: Six Visualization Module Protocol Stubs

The package SHALL provide six `Protocol` stubs in `viz.py`: `PCA3D`, `DcHeatmap`, `Voronoi2D`, `TrajectoryAnimation`, `TensorBoardDashboard`, `PlantUMLDiagram`. Each SHALL expose a single method signature matching its public API (e.g. `PCA3D.render(centroids, *, camera_angles=(25.0, 135.0)) -> Figure`); `PCA3D.camera_angles` SHALL default to the tuple `(25.0, 135.0)`. The module SHALL export `IMPLEMENTATION_STACK = frozenset({"matplotlib", "scikit-learn", "scipy", "imageio", "tensorboard", "plantuml"})`. The `__all__` of `viz.py` SHALL contain exactly six module-level names.

#### Scenario: Six modules present
- **WHEN** `viz.__all__` is enumerated
- **THEN** it contains exactly six module names matching `{"PCA3D", "DcHeatmap", "Voronoi2D", "TrajectoryAnimation", "TensorBoardDashboard", "PlantUMLDiagram"}`

#### Scenario: Camera angles fixed
- **WHEN** `PCA3D.camera_angles` is inspected
- **THEN** it equals `(25.0, 135.0)` (elevation 25°, azimuth 135°)

#### Scenario: Stack pinned
- **WHEN** `viz.IMPLEMENTATION_STACK` is inspected
- **THEN** it equals the six-element frozenset above

<a id="req-15"></a>

### Requirement: Hard-Constraint Grep Invariants

The package SHALL satisfy the following source-level invariants, asserted by **literal-token grep tests** (any invariant requiring data-flow / semantic analysis is NOT a grep invariant; see Requirement "Centroid Driver Semantic Invariants" for the semantic layer):
- NO occurrence of `StraightThroughEstimator` or `straight_through` in `src/decompmoe/`
- NO occurrence of `w_i` in the body of `distance.logit` (signature-level invariant already covered)
- NO occurrence of `shared` attribute in `ExpertPool`
- NO import of `torch.utils.cpp_extension` or `triton` in `experts.py`
- NO field `kv_cache_c` in `GeometricRouter` Protocol

(The two previously-listed invariants — `.clamp_min(ε)` empty-cell denominator and the literal `arctan(pi / sqrt(d_c))` token — are removed from this Requirement because they cannot be verified by literal grep alone: the former requires data-flow analysis (the `.clamp_min` call result must be checked to be a denominator), and the latter can be circumvented by a syntactically different but semantically equivalent expression. Both invariants are restated under decompmoe-skeleton Req 16 Centroid Driver Semantic Invariants (`#req-16`), each with its own named guard: the `.clamp_min(ε)` empty-cell denominator by Scenario "Semantic invariants are enforced by the named test scenarios" via `tests/test_schedule.py::test_empty_cell_preserves_centroid`, and the `arctan(pi / sqrt(d_c))` token by Scenario "Voronoi closed form is not the arctan shortcut" via `tests/test_sphere.py::test_canonical_voronoi_angle_not_arctan_shortcut`.)

#### Scenario: Hard constraints hold
- **WHEN** the literal-token grep invariants above are evaluated against `src/decompmoe/`
- **THEN** all invariants pass

<a id="req-16"></a>
### Requirement: Centroid Driver Semantic Invariants


The package's `CentroidDriver` SHALL enforce four semantic invariants that **cannot be verified by literal-token grep alone** (data-flow analysis, runtime observation, and arithmetic comparison are required). These are the **semantic counterpart** to Requirement "Hard-Constraint Grep Invariants" and are the landing site for the two invariants that req-15 removed from grep scope:

1. **Empty-cell fallback**: `CentroidDriver.step(centroids, X, mask)` with `n_i = |T_i| = 0` MUST preserve `c_i^(t+1) == c_i^(t)` element-wise (no direction randomization). The driver MUST NOT use `.clamp_min(ε)` as a denominator in the empty-cell branch. Verified by `test_empty_cell_preserves_centroid`.

2. **Spherical re-projection (driver output invariant)**: After every `CentroidDriver.step(...)` call across all four active phases, `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`. Verified by `test_spherical_norm_is_strictly_one`.

3. **Near-zero candidate fallback (EMA phases 1–3)**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse) during Phases 1–3 EMA, `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears. Verified by `test_near_zero_candidate_fallback`.

4. **Near-zero candidate fallback (Phase 4 PROJECTED_SGD)**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` during Phase 4 projected SGD, the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears (the same `torch.where(use_old, prev, normalize(...))` guard pattern used in EMA must apply to Phase 4 — `centroids / ‖centroids‖.clamp_min(eps)` does NOT satisfy this invariant). Verified by `test_near_zero_candidate_fallback_phase4`.

#### Scenario: Semantic invariants are enforced by the named test scenarios
- **WHEN** the four named test scenarios (`test_empty_cell_preserves_centroid`, `test_spherical_norm_is_strictly_one`, `test_near_zero_candidate_fallback`, `test_near_zero_candidate_fallback_phase4`) all pass
- **THEN** the empty-cell fallback, spherical re-projection, and near-zero candidate fallback invariants hold for `CentroidDriver` across all four active phases


#### Scenario: Voronoi closed form is not the arctan shortcut

- **WHEN** `canonical_voronoi_angle(N_e, d_c)` is evaluated at the MVP point `(N_e = 16, d_c = 16)`
- **THEN** it returns the root of the defining equation `½ · I_{sin²θ}((d_c − 1)/2, 1/2) = 1/N_e`, which is `1.173547425920 rad` (`67.239315°`) at `d_c = 16` — **NOT** the forbidden token `arctan(pi / sqrt(d_c))`, which evaluates to `0.665773750028 rad` (`38.146026°`) at the same point and MUST NOT be the implementation's closed form
- **AND** the returned value MUST satisfy `pytest.approx(1.173547, abs=1e-6)` (the 6dp spec literal, per governance req-gov-1 obligation 3) with the actual value embedded in the failure message as `f"actual={...}"`
- **AND** a substitution of the forbidden token MUST move the result outside that tolerance by at least `1e5` times (measured: `5.078e-01` absolute error at `N_e = 16`, i.e. `507_773×` the `abs=1e-6` tolerance), so the guard discriminates rather than merely passing
- **AND** the residual frame is named: `|½·I_{sin²θ}(7.5, 1/2) − 1/16| < 1e-9` measured against the implementation-internal reference `src/decompmoe/sphere.py::_betainc_regularized`
- **AND** this Scenario is the guard that Requirement "Hard-Constraint Grep Invariants" refers to when it states the removed invariants are enforced here; the referenced name MUST be `test_canonical_voronoi_angle_not_arctan_shortcut`

<a id="req-17"></a>

### Requirement: Centroid Driver Invariant Test Scenarios

The package's test suite SHALL include the following three tests, asserting the spherical re-projection and empty-cell fallback invariants on `CentroidDriver.step(...)`:

#### Scenario: test_empty_cell_preserves_centroid
- **WHEN** `CentroidDriver.step(centroids, X, mask)` is called with a mask where `n_i = 0` for some expert `i`
- **THEN** `‖c_i^(t+1) − c_i^(t)‖₂ < 10⁻¹²` (machine-epsilon identity; no direction randomization)

#### Scenario: test_spherical_norm_is_strictly_one
- **WHEN** `CentroidDriver.step(...)` is iterated over Phase 1 (EMA_090), Phase 2 (EMA_095), Phase 3 (EMA_099), and Phase 4 (PROJECTED_SGD)
- **THEN** after every step, `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷` for all experts

#### Scenario: test_near_zero_candidate_fallback
- **WHEN** `CentroidDriver.step(...)` is called with input features `X` that produce a degenerate per-expert mean `‖u_i‖₂ < 10⁻⁹` for some expert `i`
- **THEN** the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears in the centroid tensor

---

<a id="req-18"></a>
### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension


The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask, *, grad=None, eta=1e-2) -> Tensor` method MUST apply, per phase. **`mask` is a REQUIRED positional parameter and MUST NOT be given a default value:** per-expert masked means `m_i` are undefined without it, and a defaulted `mask=None` invites an implementation to substitute a whole-batch mean for `m_i`, which silently broadcasts one mean to every centroid and collapses all territories to a single point. An implementation MUST reject a missing `mask` rather than substitute one.

- Phase 0 (SEEDING): `c_i ← c_i.detach()` (driver is a no-op returning the input centroids detached from the autograd graph); `c_i.requires_grad = False`. Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds. **The caller MUST supply Phase 0 seeds already satisfying `‖c_i‖₂ ≡ 1.0`** — this is a normative obligation on the caller, not a description of the driver's behaviour, and the driver MUST NOT normalise, project, or otherwise repair Phase 0 inputs. This elevation is the deliberate half of a paired correction: `wayfinder` req-23 previously asserted the spherical-norm invariant for "any Phase (including 0 K-Means)" while simultaneously declaring this driver a no-op, giving two peer specs mutually exclusive MUSTs for the same quantity. `wayfinder` req-23 has since been narrowed to **Phase 1–4**; this Requirement is the corresponding owner of the Phase 0 obligation, and the two MUSTs are no longer in conflict.
- Phase 1 (EMA_090): `c_i ← Normalize(0.90 · c_i + 0.10 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 2 (EMA_095): `c_i ← Normalize(0.95 · c_i + 0.05 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 3 (EMA_099): `c_i ← Normalize(0.99 · c_i + 0.01 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 4 (PROJECTED_SGD): When `grad is not None`: `candidate_i = c_i − eta · grad_i`; then `c_i^(t+1) = candidate_i / ‖candidate_i‖₂`. When `grad is None`: `c_i^(t+1) = c_i / ‖c_i‖₂` (L2 retraction of the input only). Both branches apply the Invariant #4 guard pattern: when `‖candidate_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)` (no `clamp_min(ε)` denominator; the same `torch.where(use_old, prev, normalize(...))` pattern used in EMA). Driver Active, gradient channel Active.

The `m_i` is the masked-mean over tokens assigned to expert `i`. The driver MUST enforce the empty-cell invariant: if `n_i = |T_i| = 0`, then `m_i ≡ c_i^(t−1)` (no `clamp_min(ε)` denominator). The driver MUST enforce the spherical re-projection invariant: `‖c_i^(t+1)‖₂ ≡ 1.0` after every step; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)`. The driver MAY call `decompmoe.safeguards.should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]` for dead-expert detection; the function itself lives in `safeguards.py` and is *called* from the driver (the driver MUST NOT define a same-named helper). When `threshold=None` is passed, the implementation derives the effective threshold via the private helper `_dead_expert_threshold(N_e) = 1/(2·N_e)`; at MVP `N_e = 16` this yields `1/32`. The dead-expert rule is parameterized by `N_e`, not hardcoded `1/128`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200` and `RESURRECTION_RATE_LIMIT_STEPS = 1000` are `Final[int]` module-level constants (see `safeguards.py::DEAD_EXPERT_CONSEC_STEPS` and `safeguards.py::RESURRECTION_RATE_LIMIT_STEPS`); the spec references the constant identifiers rather than literal values to ensure the spec stays in lock-step with the code if these constants are retuned.

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `safeguards.py::clip_global_grad_norm_` as of commit `d3689a1`.

The `step` signature `(*, grad=None, eta=1e-2)` REPLACES the legacy `(centroids, X, mask, eps=1e-6)` contract: the `eps` parameter is removed (no longer used by any active phase); the `grad` keyword is REQUIRED for the projected SGD step (no positional gradient argument); the `eta` keyword defaults to `1e-2` (conservative; spec does not pin a specific value beyond the linear convention); when `grad is None` the P4 branch is the identity L2 retraction (no SGD step applied — this is the backward-compatible fallback for callers that do not provide a gradient). Callers that previously passed `eps=1e-6` will need to remove the kwarg (breaking change; no in-repo callers pass `eps`).

#### Scenario: Phase-4 SGD-1-step closed form

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called with `centroids ∈ R^{N_e × d_c}` (unit-norm rows), `grad ∈ R^{N_e × d_c}` with `‖grad_i‖₂ = 0.05` for all `i`, and `eta = 1e-2`
- **THEN** for every expert `i` where `‖centroids[i] − eta · grad[i]‖₂ ≥ 1e-9`: `c_i^(t+1) == (centroids[i] − eta · grad[i]) / ‖centroids[i] − eta · grad[i]‖₂` within `abs=1e-7` (closed-form SGD step followed by L2 retraction)
- **AND** for every expert `i`: `‖c_i^(t+1)‖₂ == 1.0` within `abs=1e-7` (spherical re-projection invariant holds after the full P4 path, including the SGD step)

#### Scenario: Phase-4 SGD with near-zero candidate falls back to c_i^(t)

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called and for some expert `i` the post-SGD candidate `‖centroids[i] − eta · grad[i]‖₂ < 1e-9` (e.g. `centroids[i] = +grad[i] / ‖grad[i]‖₂` and `eta · ‖grad[i]‖₂ = 1`)
- **THEN** `c_i^(t+1) == c_i^(t)` element-wise (Invariant #4 fallback applies to the full P4 path, not only to the EMA branches) and no NaN appears in the centroid tensor

#### Scenario: Phase-4 with `grad=None` preserves the legacy L2-retraction semantics

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask)` is called with the default `grad=None` and `eta=1e-2`
- **THEN** `c_i^(t+1) == centroids[i] / ‖centroids[i]‖₂` element-wise within `abs=1e-7` (the legacy P4 behavior — L2 retraction of the input — is preserved exactly when no gradient is provided; this is the backward-compatibility contract for callers predating the SGD step addition)

---

<a id="req-19"></a>

### Requirement: Spherical L2 Normalization — max(…z…, ε) Formula

The package SHALL provide `spherical_l2_normalize(z, eps=1e-6) -> Tensor` returning `z / max(‖z‖₂, eps)` along the last dimension. The default `eps` SHALL equal `1e-6`. The function SHALL be safe at `z = 0` (no NaN / Inf in output; returns the zero vector).

#### Scenario: Output norm equals 1.0 for `‖z‖₂ ≥ ε` (and 0 for `z = 0`)

- **WHEN** `spherical_l2_normalize(z)` is called for any `z` with `‖z‖₂ ≥ ε` (which subsumes the prior `‖z‖₂ ≥ 1 − ε` regime — the formula's relevant threshold is `ε`, not `1 − ε`)
- **THEN** **the Scenario heading's "equals 1.0" is a DISPLAY FORM, not a normative equality** — the normative claim is the bound below, not an `==`: `|pow(2).sum(-1) − 1.0| ≤ γ_{d_c} := (d_c − 1)·u / (1 − (d_c − 1)·u) ≤ d_c·eps` where `eps = 2.220446049250313e-16` is the float64 unit roundoff and `d_c` is the last-dimension width — **the bound is DIMENSION-DEPENDENT and no dimension-independent constant bound exists**: a length-`d_c` sum of squares carries relative error `γ_{d_c−1}`, so any claim of the form `≤ C·eps` for a fixed `C` is false for large `d_c`. (The `max(‖z‖₂, ε)` denominator equals `‖z‖₂` for `‖z‖₂ ≥ ε`, so `‖out‖₂ = ‖z‖₂ / ‖z‖₂ = 1` **in exact real arithmetic**; **the exact `== 1.0` equality holds only in exact real arithmetic**.) At the frozen MVP width `d_c = 16` the tight empirical envelope is `4·eps ≈ 8.88e-16` with worst observed `6.6613e-16`, but that 4-ulp constant is **valid only in the small-`d_c` regime and MUST NOT be generalised**: measured against `4·eps` the ratio reaches `1.00×` at `d_c = 512`, `1.12×` at `d_c = 1024`, `1.75×` at `d_c = 4096` and `3.00×` at `d_c = 16384` (float64; float32 first exceeds at `d_c = 4096` and reaches `1.75×` at `d_c = 16384`). Roughly half of all rows do not compare bit-equal to `1.0`, so this Scenario MUST NOT be restated as a bare `==`. `tests/test_sphere.py::test_spherical_l2_normalize_residual_dimension_dependent_bound` guards the dimension-dependent bound across `dim ∈ {8, 16, 32, 128, 512, 1024, 4096}` in both float64 and float32 and separately pins the 4-ulp envelope at the MVP width. The prior `[1 − 2ε, 1]` interval bound from the OLD `+ ε` formula is obsolete)

#### Scenario: Idempotence

- **WHEN** the function is applied twice in succession with input satisfying either `z = 0` (output is `0`) or `‖z‖₂ ≥ ε` (output norm is `1`)
- **THEN** the second application leaves the output unchanged (since for `z = 0` the output is `0` and the second `0 / max(0, ε) = 0` is the identity; for `‖z‖₂ ≥ ε` the first output has norm `1`, so the second `max(1, ε) = 1` denominator gives the identity map)
- **AND WHEN** the input is in the degenerate regime `0 < ‖z‖₂ < ε`
- **THEN** the first application yields `‖out‖₂ = ‖z‖₂ / ε < 1` (sub-unit norm), and the second application normalizes to norm `1` (NOT idempotent in this regime)

---

<a id="req-20"></a>

### Requirement: Beta Parameterization Operational Domain — D1 Module-Level Constants

The package SHALL provide `inverse_temperature(gamma) -> Tensor` implementing the **parameterization-space** form `β = β_min + (β_max − β_min) · σ(γ)` with `β_min == 0.1` and `β_max == 32`. The package SHALL additionally provide `phase4_inverse_temperature(gamma_p) -> Tensor` implementing the **operational-domain** form `β^eff = 1 + 31 · σ(γ')` used in Phase 4 (the parameterization-space floor `0.1` and the operational-domain floor `1.0` are intentionally decoupled — the latter prevents routing resonance at runtime, the former keeps `σ'(γ)` non-degenerate in the cold-start region). The package SHALL provide `gamma_reset_for_phase4(beta_p3) -> float` implementing `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`; the worked example `gamma_reset_for_phase4(16.0) ≈ −0.0645385...` MUST hold within `abs=1e-4`. The package SHALL provide `beta_effective(gamma, phase, step) -> Tensor` returning `1.0` for `phase == 1`, `Clamp(inverse_temperature(gamma), 1.0, phase_beta_max(phase, step))` for `phase ∈ {2, 3}` (where `phase_beta_max(phase, step)` is the **time-varying** schedule ramp under the **pinned** linear-interpolation convention `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive: Phase 2 range `[6_000, 26_000)` ramp `1.0 → 4.0` (so `phase_beta_max(2, 6_000) = 1.0` exact at boundary start, `phase_beta_max(2, 16_000) = 2.5` exact at midpoint, `phase_beta_max(2, 25_999) = 1 + 3·19_999/20_000 = 3.99985`); Phase 3 range `[26_000, 56_000)` ramp `4.0 → 16.0` (so `phase_beta_max(3, 26_000) = 4.0` exact at boundary start = `box(3).lo`, `phase_beta_max(3, 41_000) = 4 + 12·15_000/30_000 = 10.0` exact at midpoint, `phase_beta_max(3, 55_999) = 4 + 12·29_999/30_000 = 15.9996`). `phase_beta_max` is **distinct** from the static `phase_beta_box(phase).hi` and the `step` parameter is required), and `phase4_inverse_temperature(gamma_p)` for `phase == 4`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` (operational-domain worst case, all domains) and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (**parameterization-space** worst case derived as `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95`, where `σ'(0) = 0.25` is the sigmoid derivative at `γ = 0` and the inner-product factor `|Cᵀc − 1|_max = 2` is the antipodal extreme; the **operational-domain Phase 4** worst case is `σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` at `γ' = 0` (canonical export per `beta.py::MAX_GRAD_PER_GAMMA_PHASE4` `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`); the two constants live in different domains and MUST NOT be conflated).

**`beta_effective` signature is exactly 3 positional args `(gamma, phase, step)`** — there is no `cfg` keyword-only parameter. Per `design.md` Decision 1, the algorithmic constants `β_min = 0.1` and `β_max = 32` live as module-level `Final[float]` in `decompmoe/beta.py` (not in MVPConfig and not threaded through `cfg`). The signature intentionally avoids `cfg` to keep the call site focused on the schedule / phase decision and to avoid the indirection cost of looking up constants that are already canonically placed. The three constants `31` (Phase 4 span), `31.9` (parameterization span), and `1.0` (Phase 4 floor) likewise live in `decompmoe/beta.py`.

#### Scenario: Parameterization endpoints

- **WHEN** `inverse_temperature(gamma)` is called with `gamma ∈ {-50, 0, 50}`
- **THEN** the result is `≈ 0.1` / `16.05` (midpoint) / `≈ 32.0` respectively within `1e-3`

#### Scenario: gamma reset for phase 4 boundary continuity

- **WHEN** `gamma_reset_for_phase4(16.0)` is called
- **THEN** the result equals `ln(15/16) ≈ −0.0645385...` within `abs=1e-4`

#### Scenario: beta_effective is continuous at Phase 3 → 4 boundary

- **WHEN** `beta_effective(gamma_p=ln(15/16), phase=4, step=56_000)` is called
- **THEN** the result equals `1 + 31 · σ(ln(15/16)) = 16.0` exactly (continuity with Phase 3's terminal `β_max`)

---

<a id="req-21"></a>
### Requirement: Frozen MVP Hyperparameter Set — D1 Geometric-Only Fields


The package SHALL provide a `MVPConfig` frozen dataclass whose locked constants equal: `d_model == 1024`, `N_e == 16`, `k == 2`, `d_ffn == 2048`, `L == 4`, `d_ffn_dense == 4096`, `d_c == 16`, `H_kv == 8`, `d_k == 128`, `β_initial ≈ 1.035` (per wayfinder `Req 7` "Isotropic Squared-Chord Distance And Bounded Beta" (`#req-7`) closed-form `β_0 = 0.1 + 31.9·σ(γ_init)` with `γ_init ≈ −3.5`; 50-digit mpmath `β_0 = 1.0350601609682665718`). Attempting to mutate any field SHALL raise `dataclasses.FrozenInstanceError`. A factory function `MVPConfig()` SHALL return an instance with all default values.

**MVPConfig carries only GEOMETRIC constants** (model shape: `d_model`, `N_e`, `k`, `d_ffn`, `L`, `d_ffn_dense`, `d_c`, `H_kv`, `d_k`, `vocab_size`) **plus the specific initial value `β_initial ≈ 1.035`** (narrative 4-sig-fig; wayfinder `Req 7` "Isotropic Squared-Chord Distance And Bounded Beta" (`#req-7`) closed-form anchor). The algorithmic range constants `β_min = 0.1` and `β_max = 32` live as module-level `Final[float]` in `decompmoe/beta.py` (NOT in MVPConfig), per `design.md` Decision 1: "Algorithmic constants live with their usage site". MVPConfig does not carry `β_min` or `β_max` fields, and the canonical sources for those constants are `decompmoe.beta.BETA_MIN` and `decompmoe.beta.BETA_MAX`.

**Source:** `wayfinder/tickets/A4-1.md`, change `fix-math-consistency-audit-2026-08` design.md (Decision 1)

#### Scenario: Field defaults locked

- **WHEN** `MVPConfig()` is constructed
- **THEN** `cfg.d_model == 1024 and cfg.N_e == 16 and cfg.k == 2 and cfg.d_ffn == 2048 and cfg.L == 4`

#### Scenario: Mutation rejected

- **WHEN** any field is assigned after construction
- **THEN** `dataclasses.FrozenInstanceError` is raised

#### Scenario: MVPConfig field set is exactly the geometric constants plus β_initial

- **WHEN** the set of dataclass field names on `MVPConfig` is enumerated via `[f.name for f in dataclasses.fields(MVPConfig)]`
- **THEN** the set equals exactly `{'d_model', 'N_e', 'k', 'd_ffn', 'L', 'd_ffn_dense', 'd_c', 'H_kv', 'd_k', 'beta_initial', 'vocab_size'}` (11 fields; **`β_min` and `β_max` are NOT MVPConfig fields**; they live as `Final[float]` in `decompmoe/beta.py`)

#### Scenario: MVPConfig.beta_initial default matches spec closed-form derivation

- **WHEN** `MVPConfig().beta_initial` is compared against `0.1 + 31.9·σ(γ_init=−3.5)` evaluated via `torch.sigmoid`
- **THEN** `abs(MVPConfig().beta_initial − closed_form_value) ≤ 1e-3` (covers narrative 4-sig-fig truncation to 1.035 from 50-digit 1.0350601609682665718)
- **AND** the test does NOT degenerate to a self-referential check (i.e., `MVPConfig().beta_initial ≈ literal_value`); the closed form MUST be derived from `β_min + (β_max−β_min)·σ(γ_init)` per wayfinder `#req-7` Sigmoid 闭式

---

<a id="req-22"></a>

### Requirement: Eight Metrics And Classification — CG Type Guard

The package SHALL provide eight metric functions (`L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, `MCI`, `CG`) whose closed forms MUST match the master `wayfinder` Req 20 verbatim:

**Realtime Tier** (every step):
- `L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form).
- `R_H = −(1 / ln N_e) · Σ_i f_i · ln f_i`, normalized entropy; `R_H ∈ [0, 1]`.
- `S_load = N_e · max_i f_i`; `1` at perfect uniformity, `N_e` at full collapse.
- `UR = (1 / N_e) · Σ_i I[f_i > 0]` over the most recent W = 100 steps.

**Offline Tier** (diagnostic runs):
- `SP_i = (1 / ‖T_i‖₁) · Σ_{t ∈ T_i} c_iᵀ C_t`; aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` (skip experts with empty `T_i`). `SP ∈ [-1, 1]`.
- `D_chord = (2 / (N_e(N_e−1))) · Σ_{i<j} √(2(1 − c_iᵀ c_j))` (mean spherical chord).
- `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / |T|) · Σ_{t} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`); **effective-dimensionality fraction**; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range). Uniform token distribution (each basis `e_j` equally represented in `T`) ⇒ `M = I/d_c` exactly ⇒ `MCI = 1.0`. Rank-1 token distribution (all `C_t = e_1`) ⇒ `M = e_1 e_1ᵀ` exactly ⇒ `MCI = 1/d_c`. The previous formula `(1/d_c) · Σ 1/λ̃²` was mathematically inconsistent with the declared range and MUST NOT appear. MCI takes **token signatures** as input (NOT centroids), per the definition.
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

#### Scenario: SP closed-form on antipodal-aligned inputs

- **WHEN** `SP(centroids, assignments, signatures)` is called with every assigned token's signature equal to the antipode of its assigned centroid (`C_t = −c_{a(t)}` for all `t ∈ T_i`)
- **THEN** the aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` equals `−1.0` within `abs=1e-6` (each `SP_i = c_iᵀ (−c_i) = −1`)

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

#### Scenario: CG raises TypeError on non-floating-point input

- **WHEN** `CG(grad)` is called with `grad` not being a `torch.Tensor` (e.g. `list`, `np.ndarray`, `None`)
- **THEN** it raises `TypeError` referencing the closed form `CG = ‖∇_{W^{K, V, b}} L_total‖₂` (the gradient of a learnable parameter is necessarily a Tensor; non-Tensor inputs are a caller bug)
- **AND WHEN** `CG(grad)` is called with `grad` being a `torch.Tensor` of non-floating-point dtype (`int`, `bool`, etc.)
- **THEN** it raises `TypeError` (the `CG` definition is the `ℓ₂` norm of a learnable-parameter gradient — non-floating-point tensors cannot be such a gradient)

<a id="req-23"></a>
### Requirement: No decompmoe-skeleton spec changes required for cycle-12 finding 1 closure


The system SHALL NOT modify any `decompmoe-skeleton` spec Requirement as part of cycle-12 finding 1 closure. The cycle-12 finding 1 (historical: ticket A8-2 L70 centered-covariance + L74 CV/convex-hull vs `wayfinder Req 20 MCI row (#req-20-mci)` uncentered second moment) is **purely a wayfinder spec scope concern** — but `decompmoe-skeleton` **does** own a verbatim mirror of the wayfinder Req 20 closed-form definitions (see below), so this Requirement serves as an explicit declaration that the existing mirror is already aligned and no new mirror / no new behavior is being introduced by this change.

**Why no decompmoe-skeleton changes are needed**:

- `decompmoe-skeleton` Requirement `` `#req-22` `` ("Eight Metrics And Classification — CG Type Guard") **verbatim mirrors** `wayfinder` Req 20 closed-forms:
  - The closed-form table enumerates `L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, `MCI`, `CG` — the same 8 metric names wayfinder `Req 20` "Eight Geometric Quantification Metrics" (`#req-20`) defines
  - Each closed-form matches the corresponding wayfinder `#req-20` row verbatim (post-229016fe + 09-22 line-drift correction)
  - The Req 22 closed-form row explicitly mirrors the `MCI` row from `wayfinder` `#req-20-mci`, including the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (lower bound `1/d_c` on `S^{d_c−1}` makes `< 0.05` health target unreachable), the centered-covariance supersede reasoning (`(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations
- `decompmoe-skeleton` Requirement `` `#req-22` `` also defines `MCI closed-form on uniform token distribution` and `MCI closed-form on rank-1 token distribution` Scenarios (both `abs=1e-12`) — these mirror the two corresponding Scenarios under wayfinder `#req-20` verbatim
- cycle-12 finding 1 is specifically about `MCI` (an eight-metric row in `wayfinder `#req-20-mci`), implemented in `src/decompmoe/metrics.py` per `wayfinder` spec — `decompmoe-skeleton` mirrors the closed-form but does not own a separate MCI definition; both capabilities use the same uncentered second moment reading
- The `(historical, ...)` supersede annotations appended to ticket `wayfinder/tickets/A8-2.md` supersede annotations in this change apply to ticket lineage only; they do NOT modify the `decompmoe-skeleton` Req-22 mirror of the MCI closed-form (the mirror is already aligned with the canonical uncentered second moment reading)

**Source:** `wayfinder/tickets/A8-2.md` (cycle-12 finding 1 evidence — wayfinder `#req-20` owns the MCI closed-form; this capability's metric table is a verbatim mirror and is already flagged as a drift hazard)

#### Scenario: decompmoe-skeleton mirror of wayfinder Req 20 MCI closed-form is already aligned

- **WHEN** `decompmoe-skeleton` `#req-22` is read for the `MCI` closed-form
- **THEN** the Req 22 text verbatim contains the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (`replaces CV (whose lower bound 1/d_c on S^{d_c−1} made the original < 0.05 health target unreachable — see wayfinder/tickets/A8-2.md)`), the centered-covariance supersede reasoning (`The centered-covariance reading has its (1/d_c, 1] upper endpoint unreachable at |T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations — all mirroring wayfinder `#req-20-mci` verbatim
- **AND** the `MCI closed-form on uniform token distribution` and `MCI closed-form on rank-1 token distribution` Scenarios use `abs=1e-12` (mirroring the two corresponding Scenarios under wayfinder `#req-20`) — both endpoints of the declared `[1/d_c, 1]` range are guarded
- **AND** no `decompmoe-skeleton` Requirement is listed in the "Affected code / Affected Requirements" sections of `proposal.md` for this change (the mirror is unchanged)
- **AND** the `decompmoe-skeleton` spec.md anchor coverage remains unchanged (existing anchors per archived changes `2026-09-15-fix-skeleton-spec-duplicate-and-completeness-2026-09-15` + `2026-09-16-fill-skeleton-spec-leading-anchor-gaps` are not affected by this change)

