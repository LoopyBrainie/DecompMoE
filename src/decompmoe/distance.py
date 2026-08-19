"""Isotropic squared-chord distance + logit composition (Req 7).

This module materializes the geometric distance metric:
    d(C, c_i) = 1 − Cᵀc_i                ∈ [0, 2]
    logit(C, c_i, β) = β · (Cᵀc_i − 1)  ∈ [−2β, 0]

The `logit` function explicitly excludes a learnable per-expert scalar weight
`w_i` (A4-2 / CLAUDE.md §6 invariant).
"""
from __future__ import annotations

from torch import Tensor


def squared_chord(C: Tensor, c_i: Tensor) -> Tensor:
    """Isotropic squared-chord distance: d = 1 − Cᵀc_i.

    Inputs are expected to be unit-norm (callers should use `spherical_l2_normalize`
    if needed). Output range: [0, 2] for unit-norm inputs.
    """
    return 1.0 - (C * c_i).sum(dim=-1)


def logit(C: Tensor, c_i: Tensor, beta: float | Tensor) -> Tensor:
    """Geometric logit: β · (Cᵀc_i − 1).

    Output range: [−2β, 0] for unit-norm inputs.

    Note: `w_i` is intentionally absent — A4-2 decision; `w_i` is reserved
    for post-aggregation mixing decided elsewhere (Req 7).
    """
    inner = (C * c_i).sum(dim=-1)
    return beta * (inner - 1.0)


__all__ = ["squared_chord", "logit"]