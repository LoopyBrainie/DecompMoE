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
    # f MUST be detached inside L_total (spec contract); if f were used in the
    # autograd graph, ∂L_lb/∂f would be a non-None tensor (zero or nonzero).
    # The spec-mandated behavior: grad_f is exactly None (= f not in graph).
    # If a future change routes f through the graph (even if grad is numerically
    # zero), this assertion catches it.
    grad_f = torch.autograd.grad(parts.L_lb, f, retain_graph=True, allow_unused=True)[0]
    assert grad_f is None, (
        "∂L_lb/∂f_i must be detached (f not in graph); "
        f"got grad_f with shape {tuple(grad_f.shape) if grad_f is not None else 'None'}"
    )
    # ∂L_lb/∂P_i ≠ 0 (gradient flows).
    assert torch.isfinite(grad_p).all()
    assert grad_p.abs().max().item() > 1e-12, (
        f"∂L_lb/∂P_i should be nonzero; got max |grad| = {grad_p.abs().max().item():.3e}"
    )


def test_lb_uses_detached_fractions() -> None:
    """L_lb must use `f_per_expert.detach()` specifically — AST scan checks
    the variable name AND the call, not any generic `.detach()` occurrence.

    Per CLAUDE.md §6 第 8 条: a test named "uses detached fractions" must
    fail if the SPECIFIC contract `f_det = f_per_expert.detach()` is missing
    or replaced with something semantically equivalent-but-different.
    """
    import ast as _ast

    src = inspect.getsource(loss_mod)
    tree = _ast.parse(src)

    # 1. Find any Assign where the target is `f_det` and RHS is
    #    `f_per_expert.detach()` — SPECIFIC contract.
    specific_detach = False
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, _ast.Name) and tgt.id == "f_det":
                    rhs = node.value
                    if (
                        isinstance(rhs, _ast.Call)
                        and isinstance(rhs.func, _ast.Attribute)
                        and rhs.func.attr == "detach"
                        and isinstance(rhs.func.value, _ast.Name)
                        and rhs.func.value.id == "f_per_expert"
                    ):
                        specific_detach = True
    assert specific_detach, (
        "loss.py must contain `f_det = f_per_expert.detach()` for L_lb"
    )

    # 2. The L_lb computation must reference `f_det` (the detached alias),
    #    NOT the raw `f_per_expert`. Slice the source to assert presence.
    #    (Implementation may compute L_lb anywhere; we check that f_det
    #    appears as a name binding/use after the assignment.)
    src_loss_block = src[src.index("f_det"):] if "f_det" in src else ""
    assert "f_det" in src_loss_block and "f_det.mean" in src_loss_block, (
        "L_lb must consume `f_det` (not raw f_per_expert)"
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


def test_sep_formula_orthonormal_degenerate() -> None:
    """Orthonormal basis → L_sep == 0.0 (DEGENERATE boundary case).

    Spec: skeleton "Loss Composition With Staged Lambda", Scenario
    "L_sep closed form degenerate boundary": for an orthonormal centroid
    set, ‖CᵀC‖_F² == N_e exactly, so the numerator vanishes identically.
    """
    N_e, d_c = 16, 16
    c = torch.eye(N_e, d_c)
    L_sep = loss_mod.compute_L_sep(c)
    assert L_sep.item() == pytest.approx(0.0, abs=1e-12), (
        f"L_sep(orthonormal basis) = {L_sep.item()}, expected 0"
    )


def test_sep_formula_non_degenerate() -> None:
    """Non-degenerate L_sep must match spec closed form exactly (abs=1e-9).

    Spec: L_sep = (‖CᵀC‖_F² − N_e) / (N_e·(N_e−1)). For non-orthogonal
    centroids, the implementation must compute this value — a degenerate
    `compute_L_sep = torch.zeros_like` would fail. Test with N_e=8, d_c=4
    so columns must overlap (rank-constrained).
    """
    torch.manual_seed(42)
    N_e, d_c = 8, 4
    c = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    G = c @ c.T
    fro_sq = (G * G).sum()
    expected = (fro_sq - N_e) / (N_e * (N_e - 1))
    actual = loss_mod.compute_L_sep(c)
    assert actual.item() > 0, "L_sep must be > 0 for non-orthogonal centroids"
    assert actual.item() == pytest.approx(float(expected), abs=1e-9), (
        f"L_sep mismatch: got {actual.item()}, expected {float(expected)}"
    )

    # Sanity: pair-wise reformulation is mathematically equivalent but
    # may differ in floating point summation order (~1e-8). Tolerance
    # abs=1e-6 captures the equivalence without false-failing on order.
    pair_sum = 0.0
    for i in range(N_e):
        for j in range(i + 1, N_e):
            pair_sum += float(G[i, j]) ** 2
    expected_pairs = (2.0 / (N_e * (N_e - 1))) * pair_sum
    assert actual.item() == pytest.approx(expected_pairs, abs=1e-6), (
        f"L_sep pair-wise form mismatch: got {actual.item()}, "
        f"expected {expected_pairs}"
    )


def test_token_vs_expert_C_notation() -> None:
    """loss source must distinguish per-token `C_t^l` vs per-expert `c_i^l`."""
    src = Path(loss_mod.__file__).read_text(encoding="utf-8")
    assert "C_t^l" in src or "C_t" in src
    assert "c_i^l" in src or "c_i" in src
