"""Spherical L2 normalization + Voronoi self-consistency threshold.

This module materializes Req 5 (Steps 2 + 4) and Req 11 of
`openspec/specs/wayfinder/spec.md`:

    - `spherical_l2_normalize(z, eps)` implements z / (‖z‖₂ + ε).
    - `voronoi_angle(d_c)` returns arctan(π / √d_c), the closed-form bound on
      the per-layer Voronoi cell angle for uniform-spread centroids on the
      unit sphere S^{d_c−1}.

Both functions are pure: no autograd state, no global registries, no hidden
parameters.
"""
from __future__ import annotations

import math

import torch
from torch import Tensor


# ---------------------------------------------------------------------------
# Spherical L2 normalization (Req 5)
# ---------------------------------------------------------------------------


def spherical_l2_normalize(z: Tensor, eps: float = 1e-6) -> Tensor:
    """Return `z / (‖z‖₂ + eps)` along the last dimension.

    Safe at `z = 0`: the +ε in the denominator prevents NaN. Output norm is
    approximately 1 for inputs with ‖z‖₂ >> eps.

    Default eps = 1e-6 matches ticket A3-1.
    """
    norm = torch.linalg.norm(z, dim=-1, keepdim=True)
    return z / (norm + eps)


# ---------------------------------------------------------------------------
# Voronoi self-consistency (Req 11)
# ---------------------------------------------------------------------------


def voronoi_angle(d_c: int) -> float:
    """Closed-form Voronoi cell angle bound for uniform centroids on S^{d_c−1}.

    Returns `arctan(π / √d_c)` in degrees.

    For d_c = 16: θ_Voronoi ≈ 38.16° — strictly greater than the
    β = 16 boundary `θ_{1/e} = arctan(1/16) ≈ 3.58°`.
    """
    return math.degrees(math.atan(math.pi / math.sqrt(d_c)))


__all__ = [
    "spherical_l2_normalize",
    "voronoi_angle",
]