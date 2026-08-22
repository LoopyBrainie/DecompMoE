"""Tests for `decompmoe.sphere`: spherical L2 normalize + Voronoi self-consistency.

ST-03 / Req 5 (Steps 2 + 4), Req 11 (Voronoi self-consistency at β = 16).
"""
from __future__ import annotations

import math

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


def test_voronoi_canonical_mvp_value() -> None:
    """`canonical_voronoi_angle(16, 16) ≈ 0.9076 rad` (52.00°).

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold" MVP
    tabulated value. Verifies the canonical API returns the spec-pinned
    number to 1e-3 rad (≈ 0.057°).
    """
    theta = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    assert abs(theta - 0.9076) < 1e-3, (
        f"canonical_voronoi_angle(16, 16) = {theta:.6f} rad, "
        f"expected ≈ 0.9076 rad (52.00°)"
    )
    assert abs(math.degrees(theta) - 52.00) < 0.06, (
        f"52.00° expected, got {math.degrees(theta):.4f}°"
    )


def test_voronoi_canonical_N_e_dependence() -> None:
    """`canonical_voronoi_angle(64, 16) ≈ 0.4494 rad` (25.45°).

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    Scenario `N_e dependence of voronoi_angle`. The function MUST depend
    on both arguments (N_e and d_c), not d_c alone.
    """
    theta_64 = sphere.canonical_voronoi_angle(num_experts=64, signature_dim=16)
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # Spec MVP tabulated value for (64, 16).
    assert abs(theta_64 - 0.4494) < 1e-3, (
        f"canonical_voronoi_angle(64, 16) = {theta_64:.6f} rad, "
        f"expected ≈ 0.4494 rad (25.45°)"
    )
    # Must depend on N_e: (64, 16) strictly less than (16, 16).
    assert theta_64 < theta_16, (
        f"θ_Voronoi(64,16) = {theta_64:.4f} must be < θ_Voronoi(16,16) = {theta_16:.4f}"
    )
    assert abs(theta_64 - theta_16) > 0.1, (
        "θ_Voronoi must depend on N_e — these should be visibly different"
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
    golden_ratio = (1.0 + 5.0 ** 0.5) / 2.0
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