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
# Sigmoid derivative extreme: σ'(0) = max σ(γ)·(1 − σ(γ)) over γ ∈ ℝ.
# Canonical name for grep-testability against future sigmoid retunes
# (per `CLAUDE.md §6 第 8 条`: formula must reflect mathematical principle).
SIGMA_PRIME_AT_ZERO: Final[float] = 0.25
# Antipodal inner-product extreme: |Cᵀc − 1| = 2 when c = −C (worst case
# on the unit sphere). Canonical name for grep-testability against future
# inner-product extreme retunes.
ANTIPODAL_INNER_EXTREME: Final[float] = 2.0
# |∂logit/∂γ| ≤ σ'(0) · |Cᵀc − 1|_max · (β_max − β_min)
#               = 0.25 · 2 · 31.9 = 15.95 (per Req 7 / A4-1)
# Domain: PARAMETERIZATION-space worst case (full sigmoid domain γ ∈ ℝ).
MAX_GRAD_PER_GAMMA: Final[float] = SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME * (BETA_MAX - BETA_MIN)
# Operational-domain Phase 4 β-gradient worst case (NO inner-product factor):
#   β^eff(γ') = 1 + 31·σ(γ') ⇒ |∂β^eff/∂γ'| = 31·σ'(γ') ≤ 31·σ'(0) = 31·0.25 = 7.75.
# This bounds ONLY the β-as-function-of-γ' gradient; for the logit gradient
# (`logit = β · (Cᵀc − 1)`), the inner-product factor |Cᵀc − 1|_max = 2
# multiplies this and yields the bound below.
# INTERNAL intermediate value (NOT in `__all__`): kept here so the derivation
# chain `31·σ'(0)·2 = 15.5` below stays traceable without re-deriving in callers.
# Skeleton ADDED "Beta Parameterization Operational Domain" only requires
# exporting `MAX_GRAD_PER_GAMMA_PHASE4` (the bound with inner factor).
_MAX_GRAD_BETA_PHASE4_INTERNAL: Final[float] = 31.0 * SIGMA_PRIME_AT_ZERO  # = 7.75
# Operational-domain Phase 4 logit-gradient worst case (WITH inner factor):
#   |∂logit/∂γ'| = |∂β/∂γ'| · |Cᵀc − 1| ≤ 7.75 · 2 = 15.5
# attained at γ' = 0 (max σ') and antipodal (Cᵀc = −1 ⇒ inner = −2).
# Derivation chain (per L42-45 above): reuses `_MAX_GRAD_BETA_PHASE4_INTERNAL`
# so a retune of the internal constant propagates through to the exported
# bound without silent divergence.
MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = ANTIPODAL_INNER_EXTREME * _MAX_GRAD_BETA_PHASE4_INTERNAL  # = 7.75·2 = 15.5


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


# Phase 2–3 operational-domain gradient, derivation only — deliberately NOT
# exported (change `2026-10-04-phase2-gamma-reset-ramp-closure` design.md
# Decision 4: no new bound is introduced by this change).
#
# Where the clamp is NOT saturated, the schedule-layer formula
#     β^eff = Clamp(β^param(γ), 1.0, β_max(t)),  β^param(γ) = 0.1 + 31.9·σ(γ)
# gives
#     |∂β^eff/∂γ| = 31.9 · σ'(γ) ≤ 31.9 · σ'(0) = 31.9 · 0.25 = 7.975
# and, on the logit side, multiplying by the inner-product worst case
# |Cᵀc − 1|_max = 2 returns
#     |∂logit/∂γ| ≤ 2 · 7.975 = 15.95
# which is exactly the bound Req 7 already pins as MAX_GRAD_PER_GAMMA. So the
# Phase 2–3 non-saturated segment introduces NO new gradient ceiling; it
# reuses the existing parameterization-space bound.
#
# Under the Req 24 γ-reset contract this segment is never reached in the
# operational path: `gamma_reset_for_phase2()` places β^param above every
# Phase-2/3 cap, so the upper clamp saturates and ∂β^eff/∂γ ≡ 0 there. The
# bound above documents the segment for callers that evaluate the formula at
# a caller-chosen γ (i.e. `beta_effective`, whose semantics this change
# leaves untouched).
#
# Do not conflate the three Phase-4/parameterization-space quantities:
#   7.75  = 31·σ'(0)      upper bound at γ' = 0        (exported, MAX_GRAD_PER_GAMMA_PHASE4 / 2)
#   240/31 ≈ 7.7419355    slope at the reset point γ' = ln(15/16)
#   0.9077 = 31.9·σ'(−3.5) parameterization-space slope at γ_init (not operational)


__all__ = [
    "BETA_MIN",
    "BETA_MAX",
    "MAX_GRAD_PER_C",
    "MAX_GRAD_PER_GAMMA",
    "MAX_GRAD_PER_GAMMA_PHASE4",
    "inverse_temperature",
    "phase4_inverse_temperature",
]
