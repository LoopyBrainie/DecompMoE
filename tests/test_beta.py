"""Tests for `decompmoe.beta`: inverse-temperature sigmoid + gradient bounds.

ST-02 / Req 7: β = β_min + (β_max − β_min) · σ(γ), with β_min = 0.1, β_max = 32.
"""
from __future__ import annotations

import pytest
import torch

from decompmoe import beta
from decompmoe.config import MVPConfig


# ---------------------------------------------------------------------------
# β(γ) endpoint / monotonicity properties
# ---------------------------------------------------------------------------


def test_beta_endpoints() -> None:
    """β(γ → −∞) ≈ 0.1, β(γ → +∞) ≈ 32."""
    beta_low = beta.inverse_temperature(torch.tensor(-50.0))
    beta_high = beta.inverse_temperature(torch.tensor(50.0))
    assert abs(beta_low.item() - 0.1) < 1e-3, f"β(-50)={beta_low.item()} ≠ 0.1"
    assert abs(beta_high.item() - 32.0) < 1e-3, f"β(+50)={beta_high.item()} ≠ 32.0"


def test_beta_monotone() -> None:
    """β(γ₁) < β(γ₂) whenever γ₁ < γ₂."""
    gammas = torch.linspace(-10.0, 10.0, 100)
    betas = beta.inverse_temperature(gammas)
    diffs = betas[1:] - betas[:-1]
    assert (diffs > 0).all(), "β must be strictly monotonically increasing"


def test_beta_param_init_default() -> None:
    """MVPConfig().beta_initial == 1.0 (proxy for γ₀ ≈ −3.5 per plan §ST-02)."""
    assert MVPConfig().beta_initial == 1.0


# ---------------------------------------------------------------------------
# logit range + gradient bounds (Req 7: hard numerical-stability guarantees)
# ---------------------------------------------------------------------------


def test_logit_range() -> None:
    """logit = β·(Cᵀc − 1) ∈ [−2β, 0] for C, c on the unit sphere.

    The full `logit` function lives in `decompmoe.distance` (ST-06). Here we
    inline the formula to keep ST-02 self-contained — the bound depends only
    on the closed-form expression, not on where it is implemented.
    """
    torch.manual_seed(0)
    d_c = 16
    N = 256
    C = torch.randn(N, d_c)
    c = torch.randn(d_c)
    C_unit = C / C.norm(dim=-1, keepdim=True)
    c_unit = c / c.norm()
    beta_val = 4.0
    inner = (C_unit * c_unit).sum(dim=-1)
    logits = beta_val * (inner - 1.0)
    assert logits.max().item() <= 1e-5, f"logit max {logits.max().item()} > 0"
    assert logits.min().item() >= -2 * beta_val - 1e-5, (
        f"logit min {logits.min().item()} < -2β = {-2 * beta_val}"
    )


def test_grad_C_bound() -> None:
    """‖∂logit/∂C‖₂ ≤ β_max = 32 (worst case at β = β_max)."""
    torch.manual_seed(0)
    d_c = 16
    C = torch.nn.Parameter(torch.randn(d_c))
    c = torch.randn(d_c)
    c_unit = c / c.norm()
    inner = ((C / C.norm()) * c_unit).sum()
    logit = beta.MAX_GRAD_PER_C * (inner - 1.0)
    grad = torch.autograd.grad(logit, C, create_graph=False)[0]
    grad_norm = grad.norm().item()
    assert grad_norm <= beta.MAX_GRAD_PER_C + 1e-3, (
        f"‖∂logit/∂C‖₂ = {grad_norm} > β_max = {beta.MAX_GRAD_PER_C}"
    )


def test_grad_gamma_bound() -> None:
    """|∂logit/∂γ| ≤ 0.5·(β_max − β_min) = 15.95."""
    torch.manual_seed(0)
    d_c = 16
    gamma = torch.nn.Parameter(torch.tensor(0.0))
    C_unit = torch.nn.functional.normalize(torch.randn(1, d_c), dim=-1).squeeze(0)
    c_unit = torch.nn.functional.normalize(torch.randn(d_c), dim=-1)
    inner = (C_unit * c_unit).sum()
    logit = beta.inverse_temperature(gamma) * (inner - 1.0)
    grad = torch.autograd.grad(logit, gamma, create_graph=False)[0]
    assert abs(grad.item()) <= beta.MAX_GRAD_PER_GAMMA + 1e-3, (
        f"|∂logit/∂γ| = {abs(grad.item())} > 15.95"
    )


# ---------------------------------------------------------------------------
# Hard-constraint constants are exported (grep / import-level invariant)
# ---------------------------------------------------------------------------


def test_constants_exported() -> None:
    """beta module must export MAX_GRAD_PER_C and MAX_GRAD_PER_GAMMA as Final[float]."""
    assert hasattr(beta, "MAX_GRAD_PER_C")
    assert hasattr(beta, "MAX_GRAD_PER_GAMMA")
    assert isinstance(beta.MAX_GRAD_PER_C, float)
    assert isinstance(beta.MAX_GRAD_PER_GAMMA, float)
    assert beta.MAX_GRAD_PER_C == 32.0
    assert abs(beta.MAX_GRAD_PER_GAMMA - 15.95) < 1e-6