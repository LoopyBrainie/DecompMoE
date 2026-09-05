"""Tests for `decompmoe.sphere`: spherical L2 normalize + Voronoi self-consistency.

ST-03 / Req 5 (Steps 2 + 4), Req 11 (Voronoi self-consistency at β = 16).
"""

from __future__ import annotations

import math

import pytest
import torch

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
    original table wrongly held at 52°. Expected constants come from
    INDEPENDENT root-finding (continued-fraction regularized incomplete
    beta + bisection), NOT from `canonical_voronoi_angle()` output:
        N_e=16 → θ ≈ 1.173547 rad (67.239°)
        N_e=17 → θ ≈ 1.165848 rad (66.798°)
    """
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    theta_17 = sphere.canonical_voronoi_angle(num_experts=17, signature_dim=16)
    assert theta_16 == pytest.approx(1.173547, abs=1e-4), f"got {theta_16}"
    assert theta_17 == pytest.approx(1.165848, abs=1e-4), f"got {theta_17}"
    assert theta_17 < theta_16, "θ_Voronoi must be strictly monotone in N_e"


def test_voronoi_canonical_mvp_value() -> None:
    """`canonical_voronoi_angle(16, 16)` solves the closed-form equation.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    MVP self-consistency scenario: ½·I_{sin²θ}(7.5, ½) = 1/N_e exactly
    (via bisection; no table). The prior tabulated 0.9076 rad was wrong —
    the true root is ≈ 1.1735 rad (67.24°), independently confirmed.
    """
    theta = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # Closed-form equation check at the returned angle (residual < 1e-9).
    s2 = math.sin(theta) ** 2
    residual = 0.5 * sphere._betainc_regularized(s2, 7.5, 0.5) - 1.0 / 16.0
    assert abs(residual) < 1e-9, f"residual {residual:.3e}"


def test_voronoi_canonical_N_e_dependence() -> None:
    """`canonical_voronoi_angle(64, 16)` solves the equation with its own root.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    Scenario `N_e dependence of voronoi_angle`. The function MUST depend
    on both arguments (N_e and d_c), not d_c alone. Independent truth for
    N_e=64: θ ≈ 1.020507 rad (58.47°).
    """
    theta_64 = sphere.canonical_voronoi_angle(num_experts=64, signature_dim=16)
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    assert theta_64 == pytest.approx(1.020507, abs=1e-4), f"got {theta_64}"
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
    assert abs(theta - canonical) < math.pi / 2, (
        f"realized θ = {math.degrees(theta):.2f}° should be within π/2 "
        f"of canonical {math.degrees(canonical):.2f}°"
    )


def test_versine_voronoi_closed_form() -> None:
    """Audit findings MAJ-M1 / MAJ-M2: versine_Voronoi closed-form values.

    versine_Voronoi(N_e, d_c) = 1 − cos(canonical_voronoi_angle(N_e, d_c)).
    Ground-truth (verified independently via mpmath bisection):
    - versine_Voronoi(16, 16) ≈ 0.61312 (spec 0.6131, old 0.6127 off by 0.068%)
    - versine_Voronoi(64, 16) ≈ 0.47707 (spec 0.4771, old 0.4776 off by 0.112%)
    """
    v_16_16 = 1.0 - math.cos(sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16))
    v_64_16 = 1.0 - math.cos(sphere.canonical_voronoi_angle(num_experts=64, signature_dim=16))
    assert v_16_16 == pytest.approx(0.61312, abs=1e-4)
    assert v_64_16 == pytest.approx(0.47707, abs=1e-4)
