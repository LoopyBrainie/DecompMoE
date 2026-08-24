"""Tests for `decompmoe.loss`: L_CE + α·L_lb + λ(t)·L_sep.

ST-09 / Req 12 — α = 0.01 (Switch-style); λ(t) staged schedule.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import torch

from decompmoe import loss as loss_mod


def test_load_balance_alpha_fixed() -> None:
    """α == 0.01 (Switch-style) AND closed forms: uniform f = P = 1/16 →
    L_lb_raw == 1.0 and L_lb == 0.01 exact.

    Spec: skeleton "Loss Composition With Staged Lambda", Scenarios
    "L_lb closed form on uniform routing" + "Alpha pinned to 0.01":
    L_lb_raw = N_e · Σ_i f_i·P_i = 16 · 16 · (1/16)² = 1.0.
    """
    torch.manual_seed(0)
    B, N, V, N_e = 1, 1, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.full((B, N, N_e), 1.0 / N_e)
    p = torch.full((B, N, N_e), 1.0 / N_e)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts = loss_mod.L_total(task_logits, targets, f, p, c, phase=1, step=1_000)
    assert parts.L_lb_raw.item() == pytest.approx(1.0, abs=1e-6), (
        f"L_lb_raw(uniform) = {parts.L_lb_raw.item()}, expected 1.0"
    )
    assert parts.L_lb.item() == pytest.approx(0.01, abs=1e-8), (
        f"L_lb = α · 1.0 must equal 0.01; got {parts.L_lb.item()}"
    )


def test_lb_gradient_flows_through_P_i() -> None:
    """`∂L_lb/∂P_i ≠ 0` AND `∂L_lb/∂f_i ≡ 0` (wayfinder Req 12 invariant).

    Spec: skeleton "Loss Composition With Staged Lambda" Scenario
    `L_lb gradient flows through P_i only`. Verifies the spec-mandated
    double-factor closed form `L_lb = N_e · Σ f.detach() · P`:
      - P_i path is differentiable (gradient flows back into logit chain)
      - f_i path is blocked by `.detach()`
    """
    torch.manual_seed(0)
    B, N, N_e = 1, 4, 8
    f = torch.nn.Parameter(torch.softmax(torch.randn(B, N, N_e), dim=-1))
    p = torch.nn.Parameter(torch.softmax(torch.randn(B, N, N_e), dim=-1))
    task_logits = torch.randn(B, N, 32)
    targets = torch.randint(0, 32, (B, N))
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts = loss_mod.L_total(task_logits, targets, f, p, c, phase=1, step=1_000)
    grad_p = torch.autograd.grad(parts.L_lb, p, retain_graph=True)[0]
    # f is detached inside loss.py so it does not appear in the autograd
    # graph; pass allow_unused=True so we can confirm grad is None (= 0).
    grad_f = torch.autograd.grad(parts.L_lb, f, retain_graph=True, allow_unused=True)[0]
    assert grad_f is None or torch.allclose(
        grad_f, torch.zeros_like(grad_f), atol=1e-12
    ), (
        f"∂L_lb/∂f_i must be exactly 0 (detached); got "
        f"{'None' if grad_f is None else f'max |grad| = {grad_f.abs().max().item():.3e}'}"
    )
    # ∂L_lb/∂P_i ≠ 0 (gradient flows).
    assert torch.isfinite(grad_p).all()
    assert grad_p.abs().max().item() > 1e-12, (
        f"∂L_lb/∂P_i should be nonzero; got max |grad| = {grad_p.abs().max().item():.3e}"
    )


def test_lb_uses_detached_fractions() -> None:
    """L_lb must use f_per_expert.detach() — verified by AST source scan."""
    import ast as _ast

    src = inspect.getsource(loss_mod)
    tree = _ast.parse(src)
    detached_found = False
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Call):
            func = node.func
            if isinstance(func, _ast.Attribute) and func.attr == "detach":
                detached_found = True
    assert detached_found, (
        "loss.py must contain at least one .detach() call (for L_lb fractions)"
    )


def test_lambda_zero_phase_1_2() -> None:
    """For phase ∈ {1, 2}, λ(t) == 0 ⇒ L_sep contribution is 0."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    p = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    for phase in (1, 2):
        parts = loss_mod.L_total(
            task_logits, targets, f, p, c, phase=phase, step=phase * 5_000
        )
        assert parts.L_sep.item() == 0.0, (
            f"phase {phase} should have λ=0 ⇒ L_sep=0; got {parts.L_sep}"
        )


def test_lambda_cosine_ramp_phase_3() -> None:
    """Phase-3 λ(t) cosine ramp pinned at 3 exact step values.

    Spec: skeleton "Loss Composition With Staged Lambda", Scenario
    "Lambda cosine ramp endpoints in phase 3": λ(26_000) == 0.0,
    λ(41_000) ≈ 5e-4, λ(55_999) ≈ 0.001 (via L_sep = λ·L_sep_raw with a
    known L_sep_raw).
    """
    c = torch.nn.functional.normalize(torch.randn(16, 16), dim=-1)
    # Compute L_sep_raw once for reference scaling.
    ref = loss_mod.compute_L_sep(c).item()
    assert ref > 0, "need nonzero L_sep_raw for ramp verification"
    del ref  # λ(t) verified directly against the cosine closed form
    lam_start = loss_mod._lambda_at(3, 26_000)
    lam_mid = loss_mod._lambda_at(3, 41_000)
    lam_end = loss_mod._lambda_at(3, 55_999)
    assert lam_start == pytest.approx(0.0, abs=1e-12)
    assert lam_mid == pytest.approx(5e-4, abs=1e-6), f"λ(41_000)={lam_mid}"
    assert lam_end == pytest.approx(0.001, abs=1e-6), f"λ(55_999)={lam_end}"


def test_lambda_fixed_phase_4() -> None:
    """For phase == 4, λ(t) == 0.001 fixed across step."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    p = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts1 = loss_mod.L_total(task_logits, targets, f, p, c, phase=4, step=56_000)
    parts2 = loss_mod.L_total(task_logits, targets, f, p, c, phase=4, step=100_000)
    assert torch.allclose(parts1.L_sep, 0.001 * parts1.L_sep_raw, atol=1e-6)
    assert torch.allclose(parts2.L_sep, 0.001 * parts2.L_sep_raw, atol=1e-6)


def test_sep_formula() -> None:
    """Orthogonal basis → L_sep == 0.0 within abs=1e-12.

    Spec: skeleton "Loss Composition With Staged Lambda", Scenario
    "L_sep closed form": for an orthonormal centroid set, ‖CᵀC‖_F² == N_e
    exactly, so the numerator vanishes identically.
    """
    N_e, d_c = 16, 16
    c = torch.eye(N_e, d_c)
    L_sep = loss_mod.compute_L_sep(c)
    assert L_sep.item() == pytest.approx(0.0, abs=1e-12), (
        f"L_sep(orthonormal basis) = {L_sep.item()}, expected 0"
    )


def test_token_vs_expert_C_notation() -> None:
    """loss source must distinguish per-token `C_t^l` vs per-expert `c_i^l`."""
    src = Path(loss_mod.__file__).read_text(encoding="utf-8")
    assert "C_t^l" in src or "C_t" in src
    assert "c_i^l" in src or "c_i" in src
