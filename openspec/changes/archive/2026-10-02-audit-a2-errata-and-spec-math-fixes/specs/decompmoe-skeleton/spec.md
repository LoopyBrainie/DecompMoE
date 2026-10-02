# Spec Delta

## MODIFIED Requirements

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

<a id="req-6"></a>

### Requirement: Voronoi Self-Consistency Threshold

The package SHALL provide `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` returning the closed-form Voronoi half-angle on `S^{signature_dim − 1}`, computed as the unique `θ ∈ (0, π/2]` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e` (regularized incomplete beta function). The implementation MUST compute this value via bisection on the equation (residual `< 1e-9`, impl-internal frame per `openspec/specs/governance/spec.md` req-gov-1 §4 — `1.16e-14` at `(N_e=16, d_c=16)`, `1.94e-15` at `(N_e=64, d_c=16)`; the true closed-form frame instead yields `4.15e-7` / `1.43e-9` and does **not** meet `< 1e-9`), NOT via a hard-coded table. The package SHALL also provide `voronoi_angle(centroids: Tensor) -> float` for the offline measurement layer (NOT for use in the training hot path). It MUST return the mean per-cell equivalent-cap radius `θ̂ = (1/N_e) · Σ_i G⁻¹(A_i)` over the realised spherical Voronoi cells, where `A_i` is the area fraction of cell `i` and `G(θ) = ½ · I_{sin²θ}((d_c − 1)/2, 1/2)` for `θ ∈ (0, π/2]` with the reflected branch `G(θ) = 1 − ½ · I_{sin²θ}((d_c − 1)/2, 1/2)` for `θ ∈ (π/2, π)`. The reflected branch is REQUIRED for totality: the small-cap branch saturates at `G(π/2) = 0.5`, so any cell holding more than half the sphere is invertible only through it (guarded by `tests/test_sphere.py::test_voronoi_angle_reflected_cap_branch_n_e_2`). `A_i` MUST be estimated by seeded Monte-Carlo over `VORONOI_AREA_SAMPLES` uniform probes on `S^{d_c − 1}`, each assigned to its `argmax` site, with the sample count and the seed fixed as module constants (`1_000_000` and `20260929`) so the returned value is deterministic. `centroids` MUST be unit-norm (`‖c_i‖₂ = 1`, tolerance `1e-6`): the owner of a probe is `argmax_i (p̂ · c_i)`, which selects the nearest site BY ANGLE only when every norm is `1`, since otherwise the inner product is scaled by `‖c_i‖₂` and the realised tessellation silently differs from the caller's intent; a deviation beyond the tolerance MUST be rejected with `ValueError` rather than absorbed. The probe block MUST be cast to `centroids.dtype` so a `float64` tensor is accepted and agrees with the `float32` result (guarded by `tests/test_sphere.py::test_voronoi_angle_rejects_non_unit_centroids` and `tests/test_sphere.py::test_voronoi_angle_honours_centroid_dtype`). Because `canonical_voronoi_angle(N_e, d_c) = G⁻¹(1/N_e)`, the deviation `D := canonical_voronoi_angle(N_e, d_c) − θ̂` is an equal-area deviation that vanishes at the equal-area ideal. When every realised cell is smaller than a hemisphere, `∀i: A_i < 0.5` — the only precondition the one-sided bound needs, because `G` is STRICTLY CONVEX on the whole of `(0, π/2)`: differentiating the defining closed form gives `G'(t) = sin^(d_c−2)(t) / B((d_c−1)/2, ½)` and `G''(t) = (d_c−2)·sin^(d_c−3)(t)·cos(t) / B((d_c−1)/2, ½)`, and every factor is strictly positive for `d_c ≥ 3` and `0 < t < π/2`, so `G''` has NO interior zero; extending to the reflected branch (`t ∈ (π/2, π)`, where only `cos t` changes sign) the unique zero of `G''` on `(0, π)` is `t = π/2`, a smooth inflection point rather than a branch end. **Degenerate case `d_c = 2`**: `signature_dim = 2` is a reachable input (the implementation rejects only values `< 2`), and then `G(θ) = θ/π` is affine with `G'' ≡ 0`; strict convexity degenerates to an identity, Jensen's inequality becomes an equality, and the one-sidedness bound above LOSES ITS DERIVATION PRECONDITION — for `d_c = 2` it MUST be carried by `∀i: A_i < 0.5` alone. Guarded by `tests/test_sphere.py::test_voronoi_angle_precondition_is_area_below_half`. Therefore `G⁻¹` is concave on the matching area interval `(0, 0.5)`, and Jensen's inequality gives `θ̂ ≤ G⁻¹((1/N_e)·Σ_i A_i) = G⁻¹(1/N_e) = canonical_voronoi_angle(N_e, d_c)` with equality iff `A_1 = ⋯ = A_{N_e}`, so `D ∈ [0, canonical_voronoi_angle(N_e, d_c)]`. `G⁻¹`'s concavity does NOT extend past a hemisphere: for `A_i > 0.5` the reflected branch takes over. The one-sided bound MUST therefore NOT be asserted unconditionally — beyond a hemisphere it is OBSERVED BEHAVIOUR, NOT A THEOREM, and is guarded as a direction check by `tests/test_sphere.py::test_voronoi_angle_one_sided_gap`. A cell capturing no probe has `A_i = 0` and contributes `G⁻¹(0) = 0` to the mean, biasing `θ̂` downward; this is mathematically correct (a zero-area cell has zero equivalent-cap radius), is REQUIRED because the one-sidedness witnesses deliberately pass exact duplicate sites, and signals a degenerate tessellation rather than a sampler failure. The per-cell form is load-bearing: spherical Voronoi cell areas always sum to 1, so `G⁻¹((1/N_e)·Σ_i A_i) ≡ G⁻¹(1/N_e)` for EVERY centroid set, and an implementation that inverts the mean area instead of inverting per cell returns the canonical angle unconditionally — a constant that certifies nothing and is guarded by `tests/test_sphere.py::test_voronoi_angle_not_degenerate_mean_area_form`. At MVP `d_c = 16`, `canonical_voronoi_angle(N_e=16, d_c=16)` SHALL return `1.173548 rad` (within `abs=1e-6` rad per `openspec/specs/governance/spec.md` req-gov-1 §3, with the bisection residual `< 1e-9` in the impl-internal frame per `openspec/specs/governance/spec.md` req-gov-1 §4); its 4-decimal prose display `≈ 1.1735 rad (≈ 67.24°)` is the canonical spec form frozen in `CLAUDE.md` §5 and MUST NOT be paired with the `abs=1e-6` tolerance, because the impl bisection output `1.1735482746999482` is `4.83e-5` away from that 4-decimal literal (`48×` the tolerance) — the 4-decimal display is instead guarded by exact `round(θ, 4) == 1.1735` and `round(math.degrees(θ), 2) == 67.24`. The returned angle is strictly greater than the specialist-collapse boundary `θ_{1/e}(β=16) = arccos(1 − 1/β) = arccos(15/16) ≈ 20.36°`. `canonical_voronoi_angle(N_e=64, d_c=16)` SHALL return `1.020506 rad` (within the same `abs=1e-6` bound), displayed as `≈ 1.0205 rad (≈ 58.47°)` and guarded by `round(θ, 4) == 1.0205` / `round(math.degrees(θ), 2) == 58.47`. The associated `versine_Voronoi = 1 − cos θ` (NOT `D_chord` which is the square root `√(2(1 − cos θ))`) is the cap height / spherical versine. The previous closed-form bound `arctan(π / √d_c) ≈ 38.146°` is incorrect (depends on `d_c` only, contradicts MVP geometry, and self-contradicts the same-sentence `θ_{1/e} ≈ 20.36°` value via the wrong formula `arctan(1/β) = 3.58°`); it MUST NOT appear in any implementation. (The 6-decimal test literals and their 4-decimal canonical spec display are disambiguated in `openspec/specs/governance/spec.md` req-gov-1 §3; `wayfinder` Req 11 states the same two-tier contract in its own prose and is NOT a verbatim mirror of this paragraph.)

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
  - The impl bisection OUTPUT is `1.1735482746999482 rad` (N_e=16) / `1.0205068335735599 rad` (N_e=64) at 16-digit precision
  - The impl-internal residual vs `src/decompmoe/sphere.py::_betainc_regularized` at the impl output is `1.16e-14` (N_e=16) / `1.94e-15` (N_e=64). The bound actually pinned by `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` is `< 1e-9`, which holds with ~5 orders of magnitude of margin; the tighter `< 1e-14` figure previously quoted here was NOT satisfied at N_e=16 and is guarded by no test
  - The true closed-form residual vs mpmath `betainc(regularized=True)` at the impl output is `4.15e-7` (N_e=16) / `1.43e-9` (N_e=64); the N_e=64 impl output sits just above the `< 1e-9` reference floor at `1.43e-9` (close to the bisection noise floor; NOT below it, despite the small magnitude), while the N_e=16 impl output has larger residual (~`4e-7`) but still well within the `< 1e-6` spec tolerance per `openspec/specs/governance/spec.md` req-gov-1 §3
  - The discrepancy `~8.49e-7 rad` (N_e=16) / `~8.79e-9 rad` (N_e=64) between mpmath true bisection solve and impl output reflects the systematic error of `_betainc_regularized`, which applies a **single** 8-point Gauss–Legendre panel on `[0, x]` with no subdivision. The θ-discrepancy is bounded to `< 1 ppm` (`0.72 ppm` at N_e=16, `0.0086 ppm` at N_e=64, relative to θ); this bound is on the **θ** discrepancy and NOT on `_betainc_regularized`'s own relative error, which is `6.63 ppm` at N_e=16

#### Scenario: no hard-coded table values
- **WHEN** `src/decompmoe/sphere.py` is grepped for the MVP values `0.9076`, `0.4494`, `0.380`, `0.0971`
- **THEN** zero matches (no fast-path table — every input must bisect)

#### Scenario: Realized measurement layer reproduces the canonical angle on an exactly equal-area tessellation

- **WHEN** `voronoi_angle(centroids)` is called on any exactly equal-area spherical Voronoi tessellation of `S^{d_c − 1}` — concretely the 32 crosspolytope vertices `±e_i` at `(N_e=32, d_c=16)`, and `N = 16` / `N = 8` equally spaced sites on a single great circle
- **THEN** the returned `θ̂` reproduces `canonical_voronoi_angle(N_e, d_c)` within the statistical tolerance `abs=1e-3` degrees prescribed by `openspec/specs/governance/spec.md` req-gov-1 obligation 7 (measured gaps `6.5e-5°`, `1.0e-4°` and `0.0°` respectively at `VORONOI_AREA_SAMPLES = 1_000_000`)
- **AND** the great-circle cases are part of this Scenario because the point set is degenerate — it spans 2 of `d_c` dimensions — while the tessellation is still exactly equal-area, so the Scenario separates "the sites look spread out" from "the cells are equal-area", which is the distinction a Voronoi-based self-consistency measure must track
- **AND** `tests/test_sphere.py::test_voronoi_angle_known_answer_crosspolytope` additionally guards that neither superseded output reappears: `115.6651°` (mean pairwise chord fed into the versine slot) and `91.5415°` (the same defect with a corrected inversion) are each more than `1°` away from the returned value

#### Scenario: Realized measurement layer is one-sided and not the degenerate mean-area form

- **WHEN** `voronoi_angle(centroids)` is called on configurations whose cells are far from equal-area — `8` exact duplicates of `e_1` among 16 sites, `4` duplicates among 16, and an antipodal pair `±e_1` with 14 sites squeezed near `e_1`
- **THEN** `canonical_voronoi_angle(N_e, d_c) − θ̂ ≥ 0` in every case (measured gaps `26.8525°`, `11.3372°` and `2.4734°`, i.e. `3.7e5×`, `1.6e5×` and `3.4e4×` of the estimator's `5σ = 7.31e-5°`, which is what makes a strict non-negativity assertion meaningful rather than flaky)
- **AND** for the same configurations `θ̂ < canonical_voronoi_angle(N_e, d_c) − 1.0°` (measured separations `26.85°` and `2.47°` against the `1.0°` threshold), which is the guard against the degenerate form `G⁻¹(mean_i A_i)`: that form returns the canonical angle for every input and would produce a separation of exactly `0`

#### Scenario: d_c = 2 affine degeneration

- **WHEN** `canonical_voronoi_angle(num_experts, signature_dim=2)` or `_cap_area(θ, 2)` is evaluated
- **THEN** in **exact real arithmetic** `G(θ) == θ/π` identically on `(0, π/2]` (because `I_x(½, ½) = 2·arcsin(√x)/π` and `x = sin²θ`), so `G'' ≡ 0`, `G` is affine, strict convexity degenerates to an identity, and `G(θ) = 1/N_e` solves to `θ = π/N_e` — in particular `canonical_voronoi_angle(N_e, 2) == π/2` exactly
- **AND** the one-sidedness bound `canonical_voronoi_angle(N_e, 2) − θ̂ ≥ 0` is NOT a theorem in this degenerate case: it rests only on `∀i: A_i < 0.5`, since strict convexity of `G` no longer holds
- **AND** the implementation does **NOT** attain that identity. `_betainc_regularized` applies a single 8-point Gauss–Legendre panel with no subdivision, and at `d_c = 2` the panel integrand `u^(a−1)` has `a = (d_c−1)/2 = ½`, i.e. a `u^(−1/2)` square-root singularity at the panel's left endpoint. Every `d_c ≥ 3` gives `a ≥ 1` and a smooth integrand, so `d_c = 2` is the **only** signature dimension at which this panel fails on the small-`x` side — the mirror image of its `x → 1` failure. Measured implementation deviation from `θ/π` is `3.64%`–`6.41%` relative over `θ ∈ (0°, 90°)`, and `canonical_voronoi_angle(N_e, 2)` deviates from `π/N_e` by up to `5.39%` (at `N_e = 32`). The `N_e = 2` case looks accurate (`6.71e-9`) only because bisection lands on the `x >= 1.0` early-return plateau at `π/2` — i.e. on the discontinuity disclosed in `canonical_voronoi_angle` — not because the quadrature is accurate there. Tests MUST pin the deviation band rather than the closed form, and MUST re-verify the exact identity independently of the implementation (mpmath), so an accuracy improvement surfaces as a test failure instead of passing silently.

<a id="req-7"></a>

### Requirement: C Extraction Four-Step Pipeline

The package SHALL provide `extract_C(K, V, proj_W_K, proj_W_V, proj_b, *, H_kv, d_c, eps=1e-6) -> Tensor` implementing the spec's exact four-step pipeline: (1) per-head projection `z^{l,h} = W_K^{l,h} · k^{l,h} + W_V^{l,h} · v^{l,h} + b^{l,h}`; (2) per-head spherical projection; (3) cross-head mean with `1/H_kv` factor; (4) final spherical projection. The pipeline SHALL be fully differentiable (D-path, no Straight-Through Estimator; no `.detach()` between intermediate tensors).

#### Scenario: Output shape on unit sphere
- **WHEN** `K ∈ R^{B × H_kv × N × d_k}` and `V ∈ R^{B × H_kv × N × d_k}` are fed in
- **THEN** `C ∈ R^{B × N × d_c}` and `‖C_t‖₂ = 1` for every token (within `1e-5`)

#### Scenario: Fully differentiable
- **WHEN** `torch.autograd.gradcheck` is run on `extract_C` with random `K`, `V` and the projection parameters
- **THEN** the gradient check passes with ATOL `1e-5` and no NaN

#### Scenario: Per-token MAC closed form
- **WHEN** the per-token operation count of `extract_C` is computed under the pinned **MAC** convention (1 MAC = 1 multiply + 1 accumulate; FLOPs = 2·MACs)
- **THEN** per-token MACs equal `H_kv · (2 · d_k · d_c + d_c) + H_kv · d_c + H_kv · d_c + d_c` — i.e. (i) per-head K/V/bias projection: `H_kv · (2 · d_k · d_c + d_c)` MACs, (ii) per-head L2-normalization (numerator/denominator ops only; sqrt counts as 0 MAC): `H_kv · d_c` MACs, (iii) cross-head mean with the `1/H_kv` factor (step 3 of the pipeline: a `H_kv`-long accumulation and rescale, i.e. `H_kv` multiply-accumulates over `d_c` values each): `H_kv · d_c` MACs, (iv) final L2-normalization: `d_c` MACs. At MVP (`H_kv=8, d_k=128, d_c=16`) this evaluates to `8·4112 + 8·16 + 8·16 + 16 = 32_896 + 128 + 128 + 16 = 33_168` per-token MACs exactly (within `abs=1`). Tests MUST assert the closed form (or its MVP specialization), NOT a profiler-derived op count.

#### Scenario: Cross-head awareness
- **WHEN** `H_kv = 8` GQA input is processed
- **THEN** the cross-head mean uses the `1/H_kv` factor (mathematical equivalence to a manual `mean(..., dim=1)`)

<a id="req-19"></a>

### Requirement: Spherical L2 Normalization — max(…z…, ε) Formula

The package SHALL provide `spherical_l2_normalize(z, eps=1e-6) -> Tensor` returning `z / max(‖z‖₂, eps)` along the last dimension. The default `eps` SHALL equal `1e-6`. The function SHALL be safe at `z = 0` (no NaN / Inf in output; returns the zero vector).

#### Scenario: Output norm equals 1.0 for `‖z‖₂ ≥ ε` (and 0 for `z = 0`)

- **WHEN** `spherical_l2_normalize(z)` is called for any `z` with `‖z‖₂ ≥ ε` (which subsumes the prior `‖z‖₂ ≥ 1 − ε` regime — the formula's relevant threshold is `ε`, not `1 − ε`)
- **THEN** `|pow(2).sum(-1) − 1.0| ≤ 4·eps_f64 ≈ 8.88e-16` where `eps_f64 = 2.220446049250313e-16` (the `max(‖z‖₂, ε)` denominator equals `‖z‖₂` for `‖z‖₂ ≥ ε`, so `‖out‖₂ = ‖z‖₂ / ‖z‖₂ = 1` **in exact real arithmetic** (the `max(‖z‖₂, ε)` denominator equals `‖z‖₂` for `‖z‖₂ ≥ ε`); **the exact `== 1.0` equality holds only in exact real arithmetic** — IEEE-754 rounding leaves a worst observed deviation of `6.6613e-16` over 100 batches × 256 rows at `dim ∈ {8, 16, 32, 128}`, and roughly half of all rows do not compare bit-equal to `1.0`, so this Scenario MUST NOT be restated as a bare `==`; `tests/test_sphere.py` guards it with `pytest.approx(..., abs=1e-6)` — the prior `[1 − 2ε, 1]` interval bound from the OLD `+ ε` formula is obsolete)

#### Scenario: Idempotence

- **WHEN** the function is applied twice in succession with input satisfying either `z = 0` (output is `0`) or `‖z‖₂ ≥ ε` (output norm is `1`)
- **THEN** the second application leaves the output unchanged (since for `z = 0` the output is `0` and the second `0 / max(0, ε) = 0` is the identity; for `‖z‖₂ ≥ ε` the first output has norm `1`, so the second `max(1, ε) = 1` denominator gives the identity map)
- **AND WHEN** the input is in the degenerate regime `0 < ‖z‖₂ < ε`
- **THEN** the first application yields `‖out‖₂ = ‖z‖₂ / ε < 1` (sub-unit norm), and the second application normalizes to norm `1` (NOT idempotent in this regime)

---
