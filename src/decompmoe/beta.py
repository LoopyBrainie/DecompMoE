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
# Domain: PARAMETERIZATION-space worst case (full sigmoid domain γ ∈ ℝ).
MAX_GRAD_PER_GAMMA: Final[float] = 0.5 * (BETA_MAX - BETA_MIN)
# Operational-domain Phase 4 worst case:
#   β^eff(γ') = 1 + 31·σ(γ') ⇒ |∂β^eff/∂γ'| ≤ 0.5·31 = 15.5 at γ' = 0.
MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0


# ---------------------------------------------------------------------------
# Inverse-temperature sigmoid (Req 7: β = β_min + (β_max − β_min) · σ(γ))
# ---------------------------------------------------------------------------


def inverse_temperature(gamma: Tensor) -> Tensor:
    """Compute β = β_min + (β_max − β_min) · σ(γ).

    Differentiable w.r.t. `gamma` via `torch.sigmoid` (D-path).
    Output range: `(BETA_MIN, BETA_MAX)` for finite gamma.
    """
    return BETA_MIN + (BETA_MAX - BETA_MIN) * torch.sigmoid(gamma)


def phase4_inverse_temperature(gamma_p: Tensor | float) -> Tensor:
    """Phase 4 operational-domain β: `1 + 31 · σ(γ_p)`.

    Distinct from `inverse_temperature`: the Phase 4 parameterization lives
    on the operational box [1, 32] (skeleton ADDED Requirement "Beta
    Parameterization Operational Domain"), not the full [β_min, β_max].
    At the reset point γ_p = ln(15/16): σ(γ_p) = 15/31 ⇒ β^eff = 16.0
    (boundary continuity with the Phase 3 exit value).
    """
    return 1.0 + 31.0 * torch.sigmoid(torch.as_tensor(gamma_p))


__all__ = [
    "BETA_MIN",
    "BETA_MAX",
    "MAX_GRAD_PER_C",
    "MAX_GRAD_PER_GAMMA",
    "MAX_GRAD_PER_GAMMA_PHASE4",
    "inverse_temperature",
    "phase4_inverse_temperature",
]
