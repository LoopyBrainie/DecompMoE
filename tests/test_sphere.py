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


def test_voronoi_angle_self_consistency() -> None:
    """With d_c = 16, voronoi_angle > θ_{1/e} = arctan(1/β) for β = 16."""
    theta_voronoi = sphere.voronoi_angle(d_c=16)
    theta_1_over_e = math.degrees(math.atan(1.0 / 16.0))
    assert theta_voronoi > theta_1_over_e, (
        f"Voronoi angle {theta_voronoi}° must exceed β=16 boundary {theta_1_over_e}°"
    )
    expected = math.degrees(math.atan(math.pi / math.sqrt(16)))
    assert abs(theta_voronoi - expected) < 1e-6