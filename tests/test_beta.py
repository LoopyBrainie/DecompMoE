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
    """Worst case hits the bound EXACTLY: orthogonal e_1, e_2 at β=β_max →
    ‖∂logit/∂C‖₂ == 32.0 within abs=1e-4.

    Spec: wayfinder ADDED "Closed-Form Gradient Bound Worst Case":
    logit = β·(Cᵀc − 1), ∂logit/∂C = β·c (for unit-norm C path); with
    C = e_1, c = e_2 orthogonal and β = 32, the norm is exactly β_max.
    """
    d_c = 16
    C = torch.nn.Parameter(torch.zeros(d_c))
    with torch.no_grad():
        C[0] = 1.0  # C = e_1
    c_unit = torch.zeros(d_c)
    with torch.no_grad():
        c_unit[1] = 1.0  # c = e_2 (orthogonal)
    inner = ((C / C.norm()) * c_unit).sum()
    logit = beta.MAX_GRAD_PER_C * (inner - 1.0)
    grad = torch.autograd.grad(logit, C)[0]
    # d/dC [β·(C/‖C‖·e_2)] at C = e_1: β · e_2/‖C‖ = β·e_2 ⇒ norm == 32
    grad_norm = grad.norm().item()
    assert grad_norm == pytest.approx(32.0, abs=1e-4), (
        f"worst-case ‖∂logit/∂C‖₂ = {grad_norm}, expected exactly 32.0"
    )


def test_grad_gamma_bound() -> None:
    """Worst case: γ = 0, c = −e_1 → |∂logit/∂γ| == 15.95 within abs=1e-3.

    Spec: wayfinder ADDED "Closed-Form Gradient Bound Worst Case":
    |dσ/dγ| ≤ 0.25 at γ=0; |Cᵀc − 1| maximal (= 2) when c = −C.
    0.5·31.9·0.25·... closed form: 0.5·(β_max−β_min)·0.5·2 = 15.95 only via
    |∂β/∂γ|·|Cᵀc−1| ≤ 0.5·31.9·0.5·2 — the spec-pinned value is 15.95.
    """
    torch.manual_seed(0)
    d_c = 16
    gamma = torch.nn.Parameter(torch.tensor(0.0))
    C_unit = torch.zeros(d_c)
    with torch.no_grad():
        C_unit[0] = 1.0  # C = e_1
    c_unit = -C_unit.clone()  # c = −e_1 (antipodal, worst case)
    inner = (C_unit * c_unit).sum()
    logit = beta.inverse_temperature(gamma) * (inner - 1.0)
    grad = torch.autograd.grad(logit, gamma)[0]
    expected = beta.MAX_GRAD_PER_GAMMA
    assert abs(grad.item()) == pytest.approx(expected, abs=1e-3), (
        f"worst-case |∂logit/∂γ| = {abs(grad.item())}, expected {expected}"
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


def test_max_grad_per_gamma_phase4() -> None:
    """Operational-domain Phase 4 worst case: γ' = 0, c = −C (antipodal) →
    |∂logit/∂γ'| == 15.5 within abs=1e-3.

    Spec: skeleton ADDED "Beta Parameterization Operational Domain":
    logit = β · (Cᵀc − 1); β^eff(γ') = 1 + 31·σ(γ') ⇒
    max |∂logit/∂γ'| = 31·σ'(0)·|Cᵀc − 1|_max = 31·0.25·2 = 15.5.
    (For β-only gradient bound see `test_max_grad_beta_phase4` below.)
    """
    gamma_p = torch.nn.Parameter(torch.tensor(0.0))
    C_unit = torch.zeros(16)
    with torch.no_grad():
        C_unit[0] = 1.0
    c_unit = -C_unit.clone()  # c = −C (antipodal worst case: Cᵀc − 1 = −2)
    logit = beta.phase4_inverse_temperature(gamma_p) * ((C_unit * c_unit).sum() - 1.0)
    grad = torch.autograd.grad(logit, gamma_p)[0]
    assert abs(grad.item()) == pytest.approx(
        beta.MAX_GRAD_PER_GAMMA_PHASE4, abs=1e-3
    ), (
        f"Phase-4 worst case |∂logit/∂γ'| = {abs(grad.item())}, "
        f"expected {beta.MAX_GRAD_PER_GAMMA_PHASE4}"
    )


def test_max_grad_beta_phase4() -> None:
    """Operational-domain Phase 4 β-only gradient bound: |∂β^eff/∂γ'| == 7.75
    within abs=1e-3.

    Spec: β^eff(γ') = 1 + 31·σ(γ'); σ'(γ') = σ(γ')(1−σ(γ')) with
    max σ'(0) = 0.25; thus max |∂β^eff/∂γ'| = 31·0.25 = 7.75.
    (Distinct from MAX_GRAD_PER_GAMMA_PHASE4 = 15.5 which multiplies in
    the inner-product factor |Cᵀc − 1|_max = 2.)
    """
    gamma_p = torch.nn.Parameter(torch.tensor(0.0))
    beta_only = beta.phase4_inverse_temperature(gamma_p)
    grad = torch.autograd.grad(beta_only, gamma_p)[0]
    assert abs(grad.item()) == pytest.approx(
        beta.MAX_GRAD_BETA_PHASE4, abs=1e-3
    ), (
        f"Phase-4 worst case |∂β^eff/∂γ'| = {abs(grad.item())}, "
        f"expected {beta.MAX_GRAD_BETA_PHASE4}"
    )
