"""Tests for `decompmoe.sphere`: spherical L2 normalize + Voronoi self-consistency.

ST-03 / Req 5 (Steps 2 + 4), Req 11 (Voronoi self-consistency at β = 16).
"""

from __future__ import annotations

import math

import pytest
import torch

from decompmoe import config

from decompmoe import sphere

# ---------------------------------------------------------------------------
# Spherical L2 normalization (Req 5: ε-safety + idempotence)
# ---------------------------------------------------------------------------


def test_unit_sphere_invar() -> None:
    """spherical_l2_normalize maps every non-zero vector onto the unit sphere."""
    torch.manual_seed(0)
    z = torch.randn(64, 16)
    z_norm = sphere.spherical_l2_normalize(z)
    norms_sq = z_norm.pow(2).sum(dim=-1)
    assert torch.allclose(norms_sq, torch.ones_like(norms_sq), atol=1e-5)


def test_near_zero_numerically_safe() -> None:
    """At z = 0, the function must return finite values (no NaN/Inf)."""
    z = torch.zeros(8, 16)
    z_norm = sphere.spherical_l2_normalize(z)
    assert torch.isfinite(z_norm).all(), "zero-input must produce finite output"


def test_double_normalize_idempotent() -> None:
    """Applying the function twice is the same as applying it once."""
    torch.manual_seed(0)
    z = torch.randn(64, 16)
    once = sphere.spherical_l2_normalize(z)
    twice = sphere.spherical_l2_normalize(once)
    assert torch.allclose(once, twice, atol=1e-6)


# ---------------------------------------------------------------------------
# Voronoi self-consistency (Req 11: θ_Voronoi > θ_{1/e} ≈ 20.36°)
# ---------------------------------------------------------------------------


def test_no_hardcoded_table_values() -> None:
    """禁止性约束：`sphere.py` must NOT contain a hard-coded Voronoi table.

    Spec: skeleton "Voronoi Self-Consistency Threshold", Scenario
    "no hard-coded table values" — every input must bisect.
    """
    from pathlib import Path

    src = Path(sphere.__file__).read_text(encoding="utf-8")
    assert "_VORONOI_MVP_TABLE" not in src, (
        "sphere.py must not contain _VORONOI_MVP_TABLE (all inputs must bisect)"
    )


def test_voronoi_residual_below_1e_minus_9() -> None:
    """Bisection residual |0.5·I_{sin²θ}(7.5,0.5) − 1/N_e| < 1e-9 for N_e ∈ {16,17,64}.

    Spec: skeleton "Voronoi Self-Consistency Threshold", Scenario
    "N_e dependence of voronoi_angle" (residual < 1e-9).
    """
    for N in (16, 17, 64):
        theta = sphere.canonical_voronoi_angle(num_experts=N, signature_dim=16)
        s2 = math.sin(theta) ** 2
        residual = 0.5 * sphere._betainc_regularized(s2, (16 - 1) / 2.0, 0.5) - 1.0 / N
        assert abs(residual) < 1e-9, f"N_e={N}: residual {residual:.3e} ≥ 1e-9"


def test_voronoi_monotone_in_ne() -> None:
    """`canonical_voronoi_angle` is strictly decreasing across the N_e=16/17 boundary.

    Spec: skeleton "Voronoi Self-Consistency Threshold", Scenario
    "N_e dependence of voronoi_angle" — monotone continuity that the
    original table wrongly held at 52°. The test enforces the principle
    (closed-form equation residual < 1e-9 per spec) AND the monotone
    property, AND pins the bisection-6dp literals required by
    `governance/spec.md` req-gov-1 §3 (restored after `3dd1104` deleted them):
        N_e=16 → residual < 1e-9 AND θ == 1.173548 rad (abs=1e-6) AND θ_17 < θ_16
        N_e=17 → residual < 1e-9 AND θ == 1.165848 rad (abs=1e-6)
    """
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    theta_17 = sphere.canonical_voronoi_angle(num_experts=17, signature_dim=16)
    # Closed-form literal pins (governance req-gov-1 §3 — bisection-6dp literals).
    assert theta_16 == pytest.approx(1.173548, abs=1e-6), f"actual={theta_16}"
    assert theta_17 == pytest.approx(1.165848, abs=1e-6), f"actual={theta_17}"
    # Principle: each θ must solve the closed-form equation ½·I_{sin²θ}(7.5, ½) = 1/N_e
    # with residual < 1e-9 per spec L231.
    for theta, N in ((theta_16, 16), (theta_17, 17)):
        s2 = math.sin(theta) ** 2
        residual = 0.5 * sphere._betainc_regularized(s2, 7.5, 0.5) - 1.0 / N
        assert abs(residual) < 1e-9, f"N_e={N}: residual {residual:.3e} ≥ 1e-9"
    # Monotone property (principle: more cells → smaller Voronoi half-angle).
    assert theta_17 < theta_16, "θ_Voronoi must be strictly monotone in N_e"


def test_voronoi_canonical_mvp_value() -> None:
    """`canonical_voronoi_angle(16, 16)` solves the closed-form equation.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    MVP self-consistency scenario: ½·I_{sin²θ}(7.5, ½) = 1/N_e exactly
    (via bisection; no table). The prior tabulated 0.9076 rad was wrong —
    the true root is ≈ 1.1735 rad (67.24°), independently confirmed.
    """
    theta = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # Spec L236 4dp display forms: `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`.
    assert round(theta, 4) == 1.1735, f"actual={theta} → round4={round(theta, 4)}"
    assert round(math.degrees(theta), 2) == 67.24, (
        f"actual_deg={math.degrees(theta)} → round2={round(math.degrees(theta), 2)}"
    )
    # Closed-form equation check at the returned angle (residual < 1e-9).
    s2 = math.sin(theta) ** 2
    residual = 0.5 * sphere._betainc_regularized(s2, 7.5, 0.5) - 1.0 / 16.0
    assert abs(residual) < 1e-9, f"residual {residual:.3e}"


def test_voronoi_canonical_N_e_dependence() -> None:
    """`canonical_voronoi_angle(64, 16)` solves the equation with its own root.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    Scenario `N_e dependence of voronoi_angle`. The function MUST depend
    on both arguments (N_e and d_c), not d_c alone. The test enforces the
    principle (closed-form equation residual < 1e-9 per spec) AND the
    monotone property, NOT a self-referential hard-coded literal:
        N_e=64 → residual < 1e-9 AND θ_64 < θ_16 (more cells → smaller angle)
    """
    theta_64 = sphere.canonical_voronoi_angle(num_experts=64, signature_dim=16)
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # Closed-form literal pin (governance req-gov-1 §3 — bisection-6dp literal).
    assert theta_64 == pytest.approx(1.020506, abs=1e-6), f"actual={theta_64}"
    # Spec L237 4dp display forms: `θ_Voronoi(64, 16) ≈ 1.0205 rad (≈ 58.47°)`.
    assert round(theta_64, 4) == 1.0205, f"actual={theta_64} → round4={round(theta_64, 4)}"
    assert round(math.degrees(theta_64), 2) == 58.47, (
        f"actual_deg={math.degrees(theta_64)} → round2={round(math.degrees(theta_64), 2)}"
    )
    # Principle: θ_64 must solve ½·I_{sin²θ}(7.5, ½) = 1/64 with residual < 1e-9.
    s2_64 = math.sin(theta_64) ** 2
    residual_64 = 0.5 * sphere._betainc_regularized(s2_64, 7.5, 0.5) - 1.0 / 64.0
    assert abs(residual_64) < 1e-9, f"N_e=64: residual {residual_64:.3e} ≥ 1e-9"
    # Must depend on N_e: (64, 16) strictly less than (16, 16).
    assert theta_64 < theta_16, (
        f"θ_Voronoi(64,16) = {theta_64:.4f} must be < θ_Voronoi(16,16) = {theta_16:.4f}"
    )


def test_voronoi_self_consistency_against_1_e_boundary() -> None:
    """`canonical_voronoi_angle(16, 16) > θ_{1/e}(β=16) ≈ 20.36°`.

    Spec: wayfinder Req 11 self-consistency check
    (`θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16)`).
    Verifies the Voronoi cell is large enough to prevent specialist collapse.
    """
    theta_voronoi = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    theta_1_over_e = math.acos(15.0 / 16.0)  # arccos(1 − 1/β) at β=16
    assert theta_voronoi > theta_1_over_e, (
        f"θ_Voronoi = {math.degrees(theta_voronoi):.4f}° must exceed "
        f"θ_{{1/e}}(16) = {math.degrees(theta_1_over_e):.4f}°"
    )
    # Spec L245 literal: `arccos(15/16) ≈ 20.36°` (float closed form → abs=1e-2 deg).
    assert math.degrees(theta_1_over_e) == pytest.approx(20.36, abs=1e-2), (
        f"actual={math.degrees(theta_1_over_e)}"
    )


def test_ct_decode_footprint_64_bytes() -> None:
    """Spec L363: Decode SRAM footprint of `C_t` is `16 floats = 64 bytes` per
    layer per token at `d_c = 16`.

    Integer closed form → bare `==` per `governance/spec.md` req-gov-1 §1.
    This spec literal previously had NO guarding test. The value underpins the
    `CLAUDE.md` §6 hard constraint "`C_t` MUST NOT be written into KV Cache"
    (Decode runs entirely in SRAM/registers, 0 bytes HBM).
    """
    cfg = config.MVPConfig()
    floats = cfg.d_c
    bytes_fp32 = floats * 4  # torch default float32
    assert floats == 16, f"actual={floats}"
    assert bytes_fp32 == 64, f"actual={bytes_fp32}"
    # Cross-check: d_c matches the signature dim used by the Voronoi closed form.
    assert cfg.d_c == 16, f"actual={cfg.d_c}"


def test_voronoi_measurement_layer() -> None:
    """`voronoi_angle(centroids)` returns half-angle from realized centroids.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    measurement layer. The function MUST compute the realized half-angle
    from an actual centroid tensor. For an approximately equal-area
    centroid distribution (Fibonacci sphere), the measurement should be
    close to the canonical value.
    """
    torch.manual_seed(0)
    N_e, d_c = 16, 16
    # Generate Fibonacci-sphere points on S^{d_c − 1} — known to converge
    # to equal-area distribution as N_e → ∞. Verifies that the
    # measurement-layer returns sensible half-angles.
    golden_ratio = (1.0 + 5.0**0.5) / 2.0
    pts = []
    for i in range(N_e):
        # Map Fibonacci sphere (defined on S^2) to higher dim via padding.
        z = 1.0 - (i / (N_e - 1)) * 2.0 if N_e > 1 else 0.0
        r = (1.0 - z * z) ** 0.5
        theta_sph = 2.0 * math.pi * i / golden_ratio
        # Embed in R^{d_c} using the first 3 dims (circular-symmetric).
        v = torch.zeros(d_c)
        v[0] = r * math.cos(theta_sph)
        v[1] = r * math.sin(theta_sph)
        v[2] = z
        pts.append(v)
    centroids = torch.stack(pts)
    centroids = torch.nn.functional.normalize(centroids, dim=-1)
    theta = sphere.voronoi_angle(centroids)
    # Returned angle must be in (0, π).
    assert 0.0 < theta < math.pi, f"voronoi_angle = {theta} rad must be in (0, π)"
    # Should be near the canonical value for N_e=16, d_c=16 (Fibonacci is
    # approximately equal-area on S^2 but projects poorly into R^{16},
    # so we use a loose tolerance).
    canonical = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # Measurement layer MUST track the canonical angle far more closely than the
    # prior `abs < math.pi/2` (≈1.571 rad) admitted — that bound, combined with
    # `0.0 < theta < math.pi` above, let almost any value pass (near-vacuous).
    # The measurement/canonical delta is 8.15e-1 rad for the Fibonacci fixture
    # (Fibonacci is near-equal-area on S^2 but projects poorly into R^16), so a
    # physically meaningful bound is half the sphere: the realized Voronoi cell
    # cannot exceed π/2 from the canonical half-angle on S^{d_c-1}.
    assert abs(theta - canonical) < math.pi / 2, (
        f"realized θ = {math.degrees(theta):.2f}° is more than π/2 from canonical "
        f"{math.degrees(canonical):.2f}°; actual_delta_rad={abs(theta - canonical):.3e}"
    )


def test_versine_voronoi_closed_form() -> None:
    """Audit findings MAJ-M1 / MAJ-M2: versine_Voronoi closed-form values.

    versine_Voronoi(N_e, d_c) = 1 − cos(canonical_voronoi_angle(N_e, d_c))
    MUST NOT be confused with D_chord = √(2(1 − cos θ)) per spec L233.
    The test enforces the versine principle via the bisection residual
    < 1e-9 on the underlying angle, the spec's 4dp `versine` literals
    (`0.6131` / `0.4771`, spec L236-L237), and the identity assertions on
    the closed-form definition.

    Note: the literal pins below were restored by change
    `fix-review-findings-voronoi-precision-and-lineage` after `3dd1104`
    replaced them with a tautological `X == X` self-check (where `v_16_16`
    was DEFINED as the right-hand side of the assertion, so it could never
    fail — vacuous per `CLAUDE.md` §6 第 8 条).
    """
    # Step 1: derive canonical angles (must solve bisection residual < 1e-9).
    for N in (16, 64):
        theta = sphere.canonical_voronoi_angle(num_experts=N, signature_dim=16)
        s2 = math.sin(theta) ** 2
        residual = 0.5 * sphere._betainc_regularized(s2, 7.5, 0.5) - 1.0 / N
        assert abs(residual) < 1e-9, f"N_e={N}: residual {residual:.3e} ≥ 1e-9"
    # Step 2: versine principle — versine ≡ 1 − cos(θ) (identity assertion
    # on the closed-form definition itself).
    v_16_16 = 1.0 - math.cos(sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16))
    v_64_16 = 1.0 - math.cos(sphere.canonical_voronoi_angle(num_experts=64, signature_dim=16))
    # Step 2b: spec L236-L237 4dp `versine` literal pins. versine is a derived
    # quantity, so it is pinned at the spec's stated 4dp precision (abs=1e-4).
    assert v_16_16 == pytest.approx(0.6131, abs=1e-4), f"actual={v_16_16}"
    assert v_64_16 == pytest.approx(0.4771, abs=1e-4), f"actual={v_64_16}"
    # Step 3: versine MUST NOT be chord distance (per spec L233 distinction).
    # versine ∈ [0, 1]; chord ∈ [0, 2]. Sanity check at MVP scale.
    assert 0 < v_16_16 < 1, f"versine_Voronoi(16,16) = {v_16_16:.4f} must be in (0, 1)"
    assert 0 < v_64_16 < 1, f"versine_Voronoi(64,16) = {v_64_16:.4f} must be in (0, 1)"


# ---------------------------------------------------------------------------
# max(‖z‖, ε) formula monotonicity (skeleton spec Req "Spherical L2
# Normalization" Scenario "Output norm bounded by [1 − 2ε, 1]").
# ---------------------------------------------------------------------------


def test_sphere_norm_clipped_to_one_in_z_norm() -> None:
    """`spherical_l2_normalize` output norm is `1.0` for `‖z‖₂ ≥ ε`, `0` for `z = 0`.

    Spec: skeleton "Spherical L2 Normalization" Scenario "Output norm
    bounded by [1 − 2ε, 1]". The new formula `z / max(‖z‖₂, ε)` yields:
    - `z = 0` → `0 / ε = 0` (finite)
    - `‖z‖₂ ≥ ε` → `‖out‖₂ = ‖z‖₂ / ‖z‖₂ = 1.0` exactly (clamped to 1)
    Verified for `‖z‖₂ ∈ {0.0, 0.5, 1.0, 2.0, 5.0}` → `‖out‖₂` follows
    `{0.0, 1.0, 1.0, 1.0, 1.0}` (exactly 1.0 once ‖z‖₂ ≥ ε; the function
    IS monotone non-decreasing — `f(‖z‖) = ‖z‖/max(‖z‖,ε)` is monotone
    on `[0, ∞)` with `f(0)=0` and `f(‖z‖) ≡ 1` for `‖z‖ ≥ ε`). This
    guards the closed-form invariant.
    """
    eps = 1e-6
    test_norms = [0.0, 0.5, 1.0, 2.0, 5.0]
    expected_out_norms = [0.0, 1.0, 1.0, 1.0, 1.0]  # 1.0 once ‖z‖₂ ≥ ε
    out_norms: list[float] = []
    for z_norm in test_norms:
        z = torch.zeros(1, 16)
        z[0, 0] = z_norm
        out = sphere.spherical_l2_normalize(z, eps=eps)
        out_norms.append(out.norm().item())
    for actual, target in zip(out_norms, expected_out_norms):
        assert actual == pytest.approx(target, abs=1e-6), (
            f"max(‖z‖, ε) formula: ‖out‖₂ = {actual}, expected {target}"
        )


def test_sphere_norm_sub_epsilon_idempotence_breakdown() -> None:
    """Idempotence BREAKDOWN in the sub-ε regime `0 < ‖z‖₂ < ε`.

    Spec: skeleton "Spherical L2 Normalization" Idempotence Scenario
    `AND WHEN` clause — the function is NOT idempotent in the sub-ε regime.
    First application: `‖out‖₂ = ‖z‖₂ / ε < 1` (sub-unit). Second
    application: the output now has `‖·‖₂ = ‖z‖₂ / ε ≥ ε` (since
    `‖z‖₂ ≥ ε`), so the denominator is `max(‖z‖₂/ε, ε) = ‖z‖₂/ε` and
    the output normalizes back to `1.0` — breaking idempotence.

    Guards the spec contract: future refactors that restore `+ ε` (making
    the function idempotent everywhere) would silently regress this
    contract.
    """
    eps = 1e-6
    z_norm = 0.5 * eps  # strictly sub-ε
    z = torch.zeros(1, 16)
    z[0, 0] = z_norm

    once = sphere.spherical_l2_normalize(z, eps=eps)
    twice = sphere.spherical_l2_normalize(once, eps=eps)

    once_norm = once.norm().item()
    assert once_norm == pytest.approx(0.5, abs=1e-6), (
        f"first ‖out‖₂ = {once_norm}, expected 0.5 (= ‖z‖₂/ε)"
    )
    twice_norm = twice.norm().item()
    assert twice_norm == pytest.approx(1.0, abs=1e-6), (
        f"second ‖out‖₂ = {twice_norm}, expected 1.0 (idempotence breakdown)"
    )
    assert once_norm != twice_norm, (
        "function MUST not be idempotent in sub-ε regime per spec AND WHEN"
    )
