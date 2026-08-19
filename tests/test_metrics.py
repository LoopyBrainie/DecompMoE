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


def test_S_load_zero_at_uniform() -> None:
    """S_load(f_uniform) ≈ 0."""
    N_e = 16
    f_uniform = torch.full((N_e,), 1.0 / N_e)
    s = metrics.S_load(f_uniform)
    assert abs(s.item()) < 1e-5, f"S_load(uniform) = {s.item()}"


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