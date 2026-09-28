# `decompmoe-skeleton/spec.md` delta — change `2026-09-28-fix-skeleton-l98-residual-frame-tagging`

> **delta type**: MODIFIED
> **affected requirement**: "Voronoi Self-Consistency Threshold" (`openspec/specs/decompmoe-skeleton/spec.md` L96)
> **affected lines**: L98 only (Requirement body, single long prose line) — 2 inline `< 1e-9` clauses
> **root cause**: both `< 1e-9` claims on L98 state the bound without naming the reference regularized incomplete beta implementation, which `governance` req-gov-1 §4 (obligation 4) requires: "Spec MUST clarify which frame is used for '< 1e-9' claims." The claims hold in the impl-internal frame and fail in the true closed-form frame, so the defect is labelling, not arithmetic.
> **anchor**: UNCHANGED. No new `<a id="req-N">` anchor is introduced; the delta stays inside the existing `req-6` body.

## MODIFIED Requirements

### Requirement: Voronoi Self-Consistency Threshold

The package SHALL provide `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float` returning the closed-form Voronoi half-angle on `S^{signature_dim − 1}`, computed as the unique `θ ∈ (0, π/2]` solving `½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1/N_e` (regularized incomplete beta function). The implementation MUST compute this value via bisection on the equation (residual `< 1e-9`, impl-internal frame per `openspec/specs/governance/spec.md` req-gov-1 §4 — `1.16e-14` at `(N_e=16, d_c=16)`, `1.94e-15` at `(N_e=64, d_c=16)`; the true closed-form frame instead yields `4.15e-7` / `1.43e-9` and does **not** meet `< 1e-9`), NOT via a hard-coded table. The package SHALL also provide `voronoi_angle(centroids: Tensor) -> float` for the offline measurement layer (computes the realized half-angle from an actual centroid tensor; NOT for use in the training hot path). At MVP `d_c = 16`, `canonical_voronoi_angle(N_e=16, d_c=16)` SHALL return `1.173548 rad` (within `abs=1e-6` rad per `openspec/specs/governance/spec.md` req-gov-1 §3, with the bisection residual `< 1e-9` in the impl-internal frame per `openspec/specs/governance/spec.md` req-gov-1 §4); its 4-decimal prose display `≈ 1.1735 rad (≈ 67.24°)` is the canonical spec form frozen in `CLAUDE.md` §5 and MUST NOT be paired with the `abs=1e-6` tolerance, because the impl bisection output `1.1735482746999482` is `4.83e-5` away from that 4-decimal literal (`48×` the tolerance) — the 4-decimal display is instead guarded by exact `round(θ, 4) == 1.1735` and `round(math.degrees(θ), 2) == 67.24`. The returned angle is strictly greater than the specialist-collapse boundary `θ_{1/e}(β=16) = arccos(1 − 1/β) = arccos(15/16) ≈ 20.36°`. `canonical_voronoi_angle(N_e=64, d_c=16)` SHALL return `1.020506 rad` (within the same `abs=1e-6` bound), displayed as `≈ 1.0205 rad (≈ 58.47°)` and guarded by `round(θ, 4) == 1.0205` / `round(math.degrees(θ), 2) == 58.47`. The associated `versine_Voronoi = 1 − cos θ` (NOT `D_chord` which is the square root `√(2(1 − cos θ))`) is the cap height / spherical versine. The previous closed-form bound `arctan(π / √d_c) ≈ 38.146°` is incorrect (depends on `d_c` only, contradicts MVP geometry, and self-contradicts the same-sentence `θ_{1/e} ≈ 20.36°` value via the wrong formula `arctan(1/β) = 3.58°`); it MUST NOT appear in any implementation. (The 6-decimal test literals and their 4-decimal canonical spec display are disambiguated in `openspec/specs/governance/spec.md` req-gov-1 §3; `wayfinder` Req 11 states the same two-tier contract in its own prose and is NOT a verbatim mirror of this paragraph.)

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
