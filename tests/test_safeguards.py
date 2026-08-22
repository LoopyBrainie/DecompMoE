"""Tests for `decompmoe.safeguards`: 5 helpers + STEP_ORDER constant.

ST-10 / Req 13 — Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i).
"""
from __future__ import annotations

import torch
import torch.nn as nn

from decompmoe import safeguards


def test_clip_grad_norm_threshold() -> None:
    """When global ‖g‖₂ > 1.0, returns scaled grads to norm ≤ 1.0."""
    p = nn.Parameter(torch.randn(8) * 10.0)
    p.grad = torch.randn_like(p) * 5.0
    pre_norm = safeguards.clip_global_grad_norm_(p, max_norm=1.0)
    assert p.grad.norm().item() <= 1.0 + 1e-5
    assert pre_norm > 1.0


def test_nan_ladder() -> None:
    """nan_ladder(consecutive_nan) returns (action, lr_scale, halt) for (1, 3, 10)."""
    assert safeguards.nan_ladder(1) == ("skip", 1.0, False)
    assert safeguards.nan_ladder(3) == ("halve_lr", 0.1, False)
    assert safeguards.nan_ladder(10) == ("halt", 1.0, True)


def test_resurrection_trigger_window() -> None:
    """Within same 1000-step window, at most one resurrection event.

    Spec (wayfinder Req 13 + archived spec): `threshold = 1 / (2·N_e)`.
    MVP N_e=16 → threshold = 1/32. With `f_i = 1/256 < 1/32` for all
    experts and all 250 steps, the rule fires.
    """
    N_e = 16
    history = [[1 / 256] * N_e for _ in range(250)]
    res = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    res2 = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=0,
        N_e=N_e,
        consec=200,
    )
    assert len(res) > 0, "first call must flag at least one expert"
    assert len(res2) == 0, "second call within window must be rate-limited to empty"


def test_resurrection_threshold_mvp_value() -> None:
    """Threshold at MVP N_e=16 is `1/32`, NOT the legacy `1/128`.

    Spec: archived `fix-openspec-doc-bugs` corrects the hardcoded `1/128`
    to the parameterized `1/(2·N_e)` form. At MVP N_e=16 the threshold
    evaluates to 1/32 = 0.03125.
    """
    N_e = 16
    history = [[0.02] * N_e for _ in range(250)]  # f_i = 0.02 < 1/32 = 0.03125
    res = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res) > 0, "MVP threshold 1/32 must trigger resurrection at f_i=0.02"
    history2 = [[0.05] * N_e for _ in range(250)]  # 0.05 > 1/32
    res2 = safeguards.should_resurrect(
        history2,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res2) == 0, "f_i = 0.05 > 1/32 must NOT trigger resurrection"


def test_resurrection_threshold_N_e_64_legacy_value() -> None:
    """For N_e=64, `1/(2·N_e) = 1/128` — preserved as legacy value.

    Spec (archived `fix-openspec-doc-bugs` Decision 7): the previous
    hardcoded `1/128` was the `N_e=64` instantiation of the same
    `1/(2·N_e)` rule. Parameterizing by N_e restores both MVP (1/32)
    and legacy (1/128) thresholds from a single formula.
    """
    N_e = 64
    history = [[1 / 200] * N_e for _ in range(250)]  # 1/200 < 1/128 = 0.0078125
    res = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res) > 0, "N_e=64 threshold 1/128 must trigger at f_i=1/200"
    history2 = [[0.01] * N_e for _ in range(250)]  # 0.01 > 1/128
    res2 = safeguards.should_resurrect(
        history2,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res2) == 0, "f_i = 0.01 > 1/128 must NOT trigger"


def test_resurrection_perturb_distribution() -> None:
    """Perturbation contract: clone target j* = argmax f_j; perturbation ~ N(0, 0.05²·I)."""
    f = torch.zeros(16)
    f[3] = 0.5
    eps = safeguards.resurrection_perturb_distribution(f, target_idx=3, eps_std=0.05)
    assert eps.shape == f.shape
    # ε ~ N(0, 0.05²·I) ⇒ std ≈ 0.05 (loose tolerance)
    assert abs(eps.std().item() - 0.05) < 0.02


def test_beta_saturation_warning_at_30_4() -> None:
    """β_i > 30.4 (95% of β_max) triggers WARN."""
    β = torch.full((16,), 20.0)
    β[5] = 30.5
    assert safeguards.beta_saturation_warning(β) is True
    β_all_safe = torch.full((16,), 20.0)
    assert safeguards.beta_saturation_warning(β_all_safe) is False


def test_beta_saturation_global_lr_halve_at_28_8() -> None:
    """More than 50% of β_i > 28.8 (90% of β_max) triggers LR halve."""
    β = torch.full((16,), 30.0)
    assert safeguards.beta_saturation_global_halve(β) is True
    β_most_safe = torch.full((16,), 20.0)
    assert safeguards.beta_saturation_global_halve(β_most_safe) is False


def test_loss_spike_defense_phase3plus() -> None:
    """L_task > 2.5 · EMA(L_task) triggers LR × 0.8 ONLY when phase ≥ 3."""
    assert safeguards.loss_spike_defense(L_task=5.0, L_task_ema=1.0, phase=3) is True
    assert safeguards.loss_spike_defense(L_task=5.0, L_task_ema=1.0, phase=2) is False
    assert safeguards.loss_spike_defense(L_task=2.0, L_task_ema=2.0, phase=3) is False


def test_step_ordering() -> None:
    """STEP_ORDER must equal ('backward', 'clip_grad_norm', 'optimizer_step', 'l2_norm')."""
    assert safeguards.STEP_ORDER == (
        "backward",
        "clip_grad_norm",
        "optimizer_step",
        "l2_norm",
    )