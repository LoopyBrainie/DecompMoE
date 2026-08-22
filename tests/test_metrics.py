"""Tests for `decompmoe.metrics`: 8 metrics + REALTIME/OFFLINE classification.

ST-12 / Req 19, 20.
"""
from __future__ import annotations

import torch

from decompmoe import metrics
from decompmoe import loss as loss_mod


def test_sep_formula_matches_loss() -> None:
    """metrics.L_sep(c) ≡ loss.compute_L_sep(c) under the same input."""
    torch.manual_seed(0)
    c = torch.nn.functional.normalize(torch.randn(16, 16), dim=-1)
    L_metrics = metrics.L_sep(c)
    L_loss = loss_mod.compute_L_sep(c)
    assert abs(L_metrics.item() - L_loss.item()) < 1e-6


def test_R_H_partition_of_unity_input() -> None:
    """R_H(p) lies in [0, 1] for any probability vector p."""
    torch.manual_seed(0)
    for N_e in (4, 16, 64):
        p = torch.softmax(torch.randn(N_e), dim=-1)
        r = metrics.R_H(p)
        assert 0.0 <= r.item() <= 1.0, f"R_H out of [0,1]: {r.item()}"


def test_S_load_closed_form_mvp() -> None:
    """S_load(f) = N_e · max_i f_i (wayfinder Req 20 closed form).

    Spec: S_load is `N_e · max_i f_i`, ranging from 1 at perfect
    uniformity to N_e at full collapse. The previous implementation
    used `‖f − 1/N‖₂` which violated the spec closed form.
    """
    N_e = 16
    # Uniform → S_load = 16 · (1/16) = 1.0
    f_uniform = torch.full((N_e,), 1.0 / N_e)
    assert abs(metrics.S_load(f_uniform).item() - 1.0) < 1e-6, (
        f"S_load(uniform) = {metrics.S_load(f_uniform).item()}, expected 1.0"
    )
    # Collapse (half on expert 0, half on expert 1) → S_load = 16 · 0.5 = 8.0
    f_collapsed = torch.zeros(N_e)
    f_collapsed[0] = 0.5
    f_collapsed[1] = 0.5
    assert abs(metrics.S_load(f_collapsed).item() - 8.0) < 1e-6, (
        f"S_load(half-collapse) = {metrics.S_load(f_collapsed).item()}, expected 8.0"
    )
    # Full collapse → S_load = 16 · 1 = 16.0
    f_full = torch.zeros(N_e)
    f_full[0] = 1.0
    assert abs(metrics.S_load(f_full).item() - 16.0) < 1e-6


def test_four_realtime_four_offline_classification() -> None:
    """REALTIME ∪ OFFLINE == 8 metric names; REALTIME has 4, OFFLINE has 4."""
    assert len(metrics.REALTIME) == 4
    assert len(metrics.OFFLINE) == 4
    assert metrics.REALTIME == {"L_sep", "R_H", "S_load", "UR"}
    assert metrics.OFFLINE == {"SP", "D_c", "MCI", "CG"}
    assert metrics.REALTIME | metrics.OFFLINE == {
        "L_sep", "R_H", "S_load", "UR", "SP", "D_c", "MCI", "CG"
    }


def test_active_flops_parity_per_arch() -> None:
    """flops_per_token(MOE) == flops_per_token(DENSE)."""
    from decompmoe.config import MVPConfig

    cfg = MVPConfig()
    moe = metrics.flops_per_token(cfg, arch="MOE")
    dense = metrics.flops_per_token(cfg, arch="DENSE")
    assert moe == dense