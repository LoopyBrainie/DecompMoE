"""Inverse-temperature sigmoid + bounded γ + gradient upper-bound constants.

This module materializes Req 7 of `openspec/specs/wayfinder/spec.md`:

    β = β_min + (β_max − β_min) · σ(γ)
    β_min = 0.1, β_max = 32
    logit = β · (Cᵀc − 1)

The gradient upper-bound constants are derived from ticket A4-1:
    ‖∂logit/∂C‖₂ ≤ β_max = 32
    |∂logit/∂γ_i| ≤ 0.5 · (β_max − β_min) = 15.95

These constants live here (not in `MVPConfig`) per design.md D1 — they are
algorithmic constants, not geometric constants, and a single canonical home
makes grep-tests easy.
"""
from __future__ import annotations

from typing import Final

import torch
from torch import Tensor


# ---------------------------------------------------------------------------
# Public constants (Final[float] per spec / plan §ST-02)
# ---------------------------------------------------------------------------


BETA_MIN: Final[float] = 0.1
BETA_MAX: Final[float] = 32.0
# ‖∂logit/∂C‖₂ ≤ β_max = 32 (per Req 7 / A4-1)
MAX_GRAD_PER_C: Final[float] = 32.0
# |∂logit/∂γ| ≤ 0.5 · (β_max − β_min) = 15.95 (per Req 7 / A4-1)
MAX_GRAD_PER_GAMMA: Final[float] = 0.5 * (BETA_MAX - BETA_MIN)


# ---------------------------------------------------------------------------
# Inverse-temperature sigmoid (Req 7: β = β_min + (β_max − β_min) · σ(γ))
# ---------------------------------------------------------------------------


def inverse_temperature(gamma: Tensor) -> Tensor:
    """Compute β = β_min + (β_max − β_min) · σ(γ).

    Differentiable w.r.t. `gamma` via `torch.sigmoid` (D-path).
    Output range: `(BETA_MIN, BETA_MAX)` for finite gamma.
    """
    return BETA_MIN + (BETA_MAX - BETA_MIN) * torch.sigmoid(gamma)


__all__ = [
    "BETA_MIN",
    "BETA_MAX",
    "MAX_GRAD_PER_C",
    "MAX_GRAD_PER_GAMMA",
    "inverse_temperature",
]