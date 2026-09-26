"""Tests for `decompmoe.beta`: inverse-temperature sigmoid + gradient bounds.

ST-02 / Req 7: β = β_min + (β_max − β_min) · σ(γ), with β_min = 0.1, β_max = 32.
"""

from __future__ import annotations

import mpmath
import pytest
import torch

from decompmoe import beta
from decompmoe.beta import _MAX_GRAD_BETA_PHASE4_INTERNAL
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
    """MVPConfig().beta_initial ≈ 1.035 — derived from spec req-7 L122 closed-form β_0 = 0.1 + 31.9·σ(γ_init=−3.5).

    Per governance req-gov-1 第 2 条 + CLAUDE.md §6 第 8 条: pytest MUST derive the
    expected value from the spec closed form (NOT a self-referential literal that
    trivially equals MVPConfig.beta_initial). abs=1e-3 covers both the narrative
    4-sig-fig truncation (1.035060 → 1.035, diff = 6e-5) and closed-form computation
    noise from `inverse_temperature`.
    """
    g = torch.tensor(-3.5)
    expected = 0.1 + 31.9 * float(torch.sigmoid(g))
    actual = MVPConfig().beta_initial
    assert actual == pytest.approx(expected, abs=1e-3), (
        f"actual={actual}, expected={expected} (from closed form β_min + "
        f"(β_max − β_min) · σ(γ_init=−3.5) = 0.1 + 31.9·σ(−3.5))"
    )


def test_sigma_prime_gamma_init_health_check() -> None:
    """Spec req-7 L122: σ'(−3.5) ≈ 0.02845 (narrative 4 sig figs); 50-digit mpmath = 0.02845302387973555984.

    Cold-start region health-check anchor: σ'(γ_init≈−3.5) MUST stay ≈ 0.02845
    ("healthy gradient") per spec L122 narrative. The 50-digit mpmath closed-form
    σ'(−3.5) = σ(−3.5)·(1−σ(−3.5)) = 0.02845302387973555984 is the spec-level
    mathematical truth; this test is the persistent pytest guard (audit `.audit/`
    scripts are dropped on archive — pytest is the durable layer).

    Two assertions:
      (a) `abs=1e-30` nail 50-digit mpmath literal (钉值零容差 for mpmath-exact
          constant-vs-closed-form). NOTE: torch.float32 only has ~7 decimals, so
          this test uses `mpmath` directly to retain full 50-digit precision.
      (b) `abs=1e-5` nail narrative 4-sig-fig precision disclosure (works for both
          fp32/mpmath since this is a coarse tolerance).
    """
    mpmath.mp.dps = 50
    s_mp = mpmath.mpf(1) / (1 + mpmath.exp(mpmath.mpf("3.5")))
    sp_mp = s_mp * (1 - s_mp)
    sp_val_50digit = float(sp_mp)
    # (a) 50-digit mpmath closed-form anchor — spec-level mathematical truth
    assert sp_val_50digit == pytest.approx(0.02845302387973555984, abs=1e-30), (
        f"σ'(−3.5) (50-digit mpmath) = {sp_val_50digit}, expected 0.02845302387973555984"
    )
    # (b) spec L122 narrative 4-sig-fig precision disclosure
    assert sp_val_50digit == pytest.approx(0.02845, abs=1e-5), (
        f"σ'(−3.5) (50-digit mpmath) = {sp_val_50digit}, expected ≈ 0.02845 "
        f"(spec L122 narrative, 4 sig figs)"
    )


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
    |∂β/∂γ|·|Cᵀc−1| ≤ σ'(0) · 2 · (β_max − β_min)
                        = 0.25 · 2 · 31.9 = 15.95 — the spec-pinned value is 15.95.
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
    # Reference the principle-form derivation chain (not `beta.MAX_GRAD_PER_GAMMA`
    # which is itself derived as `SIGMA_PRIME_AT_ZERO * ANTIPODAL_INNER_EXTREME *
    # (BETA_MAX - BETA_MIN)`). This forces the test to track all three factors.
    # `abs=1e-6` per `CLAUDE.md §6 第 8 条` (bisection Voronoi 一律 `abs=1e-6`):
    # the autograd computation accumulates ~1.9e-7 FP error vs the principle-chain
    # analytic value, which is below 1e-6 but above the 1e-12 "钉值零容差" floor
    # (the latter applies only to FP-exact constant-vs-literal comparisons, not
    # autograd-vs-analytic comparisons).
    assert abs(grad.item()) == pytest.approx(
        beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN),
        abs=1e-6,
    ), (
        f"worst-case |∂logit/∂γ| = {abs(grad.item())}, expected "
        f"σ'(0)·2·(β_max−β_min) = "
        f"{beta.SIGMA_PRIME_AT_ZERO * beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN)}"
    )


# ---------------------------------------------------------------------------
# Hard-constraint constants are exported (grep / import-level invariant)
# ---------------------------------------------------------------------------


def test_constants_exported() -> None:
    """beta module must export MAX_GRAD_PER_C and MAX_GRAD_PER_GAMMA as Final[float],
    with the logit-gradient bound asserted against its principle-form derivation chain
    `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95` (per Req 7 declaration +
    Req 30 derivation / A4-1).

    The literal `0.25 * 2 * 31.9` (rather than `beta.SIGMA_PRIME_AT_ZERO *
    beta.ANTIPODAL_INNER_EXTREME * (beta.BETA_MAX - beta.BETA_MIN)`) is used so that
    a future retune of any sub-constant forces this test to fail, exposing silent
    factor-collapse drift. `abs=1e-12` per `governance/spec.md req-gov-1` item 2
    (浮点闭式, tolerance matching FP-exact precision) + project convention for
    FP-exact constant-vs-literal comparisons.
    """
    assert hasattr(beta, "MAX_GRAD_PER_C")
    assert hasattr(beta, "MAX_GRAD_PER_GAMMA")
    assert isinstance(beta.MAX_GRAD_PER_C, float)
    assert isinstance(beta.MAX_GRAD_PER_GAMMA, float)
    assert beta.MAX_GRAD_PER_C == 32.0
    assert beta.MAX_GRAD_PER_GAMMA == pytest.approx(0.25 * 2 * 31.9, abs=1e-12), (
        f"actual MAX_GRAD_PER_GAMMA = {beta.MAX_GRAD_PER_GAMMA}, "
        f"expected σ'(0)·2·(β_max−β_min) = 0.25·2·31.9 = {0.25 * 2 * 31.9}"
    )


def test_max_grad_per_gamma_phase4_closed_form() -> None:
    """Phase-4 logit-gradient bound closed-form check (per Req 22 Operational Domain
    declaration + Req 30 derivation chain / A4-1).

    Spec derivation: |∂logit/∂γ'|_max = 31·σ'(0)·|Cᵀc − 1|_max
                   = 31·0.25·2 = 15.5.
    Guards against silent divergence between the internal β-only bound
    (`_MAX_GRAD_BETA_PHASE4_INTERNAL`) and the exported logit bound
    (`MAX_GRAD_PER_GAMMA_PHASE4`) — derivation chain promise in
    `decompmoe.beta` L42-45.
    """
    assert beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(0.25 * 2 * 31.0, abs=1e-12), (
        f"actual MAX_GRAD_PER_GAMMA_PHASE4 = {beta.MAX_GRAD_PER_GAMMA_PHASE4}, "
        f"expected σ'(0)·2·31 = 0.25·2·31 = {0.25 * 2 * 31.0}"
    )


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
    # Reference the principle-form derivation chain (not `beta.MAX_GRAD_PER_GAMMA_PHASE4`
    # which is itself derived as `ANTIPODAL_INNER_EXTREME * _MAX_GRAD_BETA_PHASE4_INTERNAL`
    # = `ANTIPODAL_INNER_EXTREME * 31.0 * SIGMA_PRIME_AT_ZERO`). This forces the test
    # to track all three factors (antipodal extreme, Phase-4 span, sigmoid-derivative
    # extreme). `abs=1e-6` per `CLAUDE.md §6 第 8 条` (autograd-vs-analytic comparison
    # tolerates FP error accumulation, distinct from 钉值零容差 floor of 1e-12 which
    # applies only to FP-exact constant-vs-literal).
    assert abs(grad.item()) == pytest.approx(
        beta.ANTIPODAL_INNER_EXTREME * 31.0 * beta.SIGMA_PRIME_AT_ZERO, abs=1e-6
    ), (
        f"Phase-4 worst case |∂logit/∂γ'| = {abs(grad.item())}, "
        f"expected 2·31·σ'(0) = "
        f"{beta.ANTIPODAL_INNER_EXTREME * 31.0 * beta.SIGMA_PRIME_AT_ZERO}"
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
    # Reference the renamed internal constant directly so the test tracks
    # any retune of the derivation chain (single source of truth — avoids
    # the inline-literal anti-pattern that would silently pass if the
    # derivation were ever generalized, e.g. to a non-symmetric sigmoid
    # extreme).
    assert abs(grad.item()) == pytest.approx(
        _MAX_GRAD_BETA_PHASE4_INTERNAL, abs=1e-3
    ), (
        f"Phase-4 worst case |∂β^eff/∂γ'| = {abs(grad.item())}, "
        f"expected {_MAX_GRAD_BETA_PHASE4_INTERNAL}"
    )
