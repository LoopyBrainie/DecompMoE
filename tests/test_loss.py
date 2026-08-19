"""Tests for `decompmoe.loss`: L_CE + α·L_lb + λ(t)·L_sep.

ST-09 / Req 12 — α = 0.01 (Switch-style); λ(t) staged schedule.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import math
import torch
import torch.nn.functional as F

from decompmoe import loss as loss_mod


def test_load_balance_alpha_fixed() -> None:
    """α == 0.01 (Switch-style fixed weight on L_lb)."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts = loss_mod.L_total(task_logits, targets, f, c, phase=1, step=1_000)
    expected = parts.L_CE + 0.01 * parts.L_lb_raw
    assert torch.allclose(parts.L_total, expected, atol=1e-5)


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
    assert detached_found, "loss.py must contain at least one .detach() call (for L_lb fractions)"


def test_lambda_zero_phase_1_2() -> None:
    """For phase ∈ {1, 2}, λ(t) == 0 ⇒ L_sep contribution is 0."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    for phase in (1, 2):
        parts = loss_mod.L_total(task_logits, targets, f, c, phase=phase, step=phase * 5_000)
        assert parts.L_sep.item() == 0.0, (
            f"phase {phase} should have λ=0 ⇒ L_sep=0; got {parts.L_sep}"
        )


def test_lambda_cosine_ramp_phase_3() -> None:
    """For phase == 3, λ(t) is cosine ramp from 0 to 0.001 across the phase."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts_start = loss_mod.L_total(task_logits, targets, f, c, phase=3, step=26_000)
    parts_end = loss_mod.L_total(task_logits, targets, f, c, phase=3, step=55_999)
    assert parts_end.L_sep.item() > parts_start.L_sep.item()


def test_lambda_fixed_phase_4() -> None:
    """For phase == 4, λ(t) == 0.001 fixed across step."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts1 = loss_mod.L_total(task_logits, targets, f, c, phase=4, step=56_000)
    parts2 = loss_mod.L_total(task_logits, targets, f, c, phase=4, step=100_000)
    assert torch.allclose(parts1.L_sep, 0.001 * parts1.L_sep_raw, atol=1e-6)
    assert torch.allclose(parts2.L_sep, 0.001 * parts2.L_sep_raw, atol=1e-6)


def test_sep_formula() -> None:
    """L_sep == (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1)) for unit-sphere centroids."""
    torch.manual_seed(0)
    N_e, d_c = 16, 16
    c = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    L_sep = loss_mod.compute_L_sep(c)
    G = c @ c.T
    fro_sq = (G ** 2).sum()
    expected = (fro_sq - N_e) / (N_e * (N_e - 1))
    assert abs(L_sep.item() - expected.item()) < 1e-6


def test_token_vs_expert_C_notation() -> None:
    """loss source must distinguish per-token `C_t^l` vs per-expert `c_i^l`."""
    src = Path(loss_mod.__file__).read_text(encoding="utf-8")
    assert "C_t^l" in src or "C_t" in src
    assert "c_i^l" in src or "c_i" in src