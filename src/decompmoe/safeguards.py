"""Numerical safeguards (Req 13) — 5 helpers + STEP_ORDER constant.

Standard training step:
    STEP_ORDER = ('backward', 'clip_grad_norm', 'optimizer_step', 'l2_norm')

Five safeguards (A6a-2):
    1. Global gradient clipping at threshold 1.0.
    2. NaN detection & escalation ladder (1 → skip, 3 → halve_lr, 10 → halt).
    3. Dead-expert splitting/resurrection (rate-limited to 1 per 1000 steps).
    4. β saturation guard (warning at 30.4 = 0.95·β_max; LR halve at 28.8 = 0.90·β_max).
    5. Loss spike defense (LR × 0.8 when phase ≥ 3 and L_task > 2.5·EMA(L_task)).
"""
from __future__ import annotations

from typing import Final, Literal

import torch
from torch import Tensor

from decompmoe.beta import BETA_MAX


# Saturation thresholds (Req 13 / A6a-2)
BETA_SATURATION_WARN: Final[float] = 0.95 * BETA_MAX  # 30.4
BETA_SATURATION_HALVE: Final[float] = 0.90 * BETA_MAX  # 28.8

# Dead-expert resurrection parameters (A6a-2)
DEAD_EXPERT_FRACTION: Final[float] = 1.0 / 128.0
DEAD_EXPERT_CONSEC_STEPS: Final[int] = 200
RESURRECTION_RATE_LIMIT_STEPS: Final[int] = 1000

# Loss-spike defense (A6a-2)
LOSS_SPIKE_RATIO: Final[float] = 2.5
LOSS_SPIKE_LR_SCALE: Final[float] = 0.8

STEP_ORDER: Final[tuple[str, ...]] = (
    "backward",
    "clip_grad_norm",
    "optimizer_step",
    "l2_norm",
)


NaNAction = Literal["skip", "halve_lr", "halt"]


def clip_global_grad_norm_(params, max_norm: float = 1.0) -> float:
    """Clip gradients in-place to global L2 norm ≤ `max_norm`. Returns the pre-clip norm."""
    pre_norm = torch.nn.utils.clip_grad_norm_(params, max_norm=max_norm)
    return float(pre_norm.item() if pre_norm.dim() == 0 else pre_norm)


def nan_ladder(consecutive_nan: int) -> tuple[NaNAction, float, bool]:
    """NaN escalation ladder per A6a-2."""
    if consecutive_nan >= 10:
        return ("halt", 1.0, True)
    if consecutive_nan >= 3:
        return ("halve_lr", 0.1, False)
    if consecutive_nan >= 1:
        return ("skip", 1.0, False)
    return ("skip", 1.0, False)


def should_resurrect(
    f_history: list[list[float]],
    current_step: int,
    last_resurrection_step: int,
    consec: int = DEAD_EXPERT_CONSEC_STEPS,
    rate_limit_steps: int = RESURRECTION_RATE_LIMIT_STEPS,
    threshold: float = DEAD_EXPERT_FRACTION,
) -> set[int]:
    """Return set of expert indices that need resurrection (rate-limited).

    An expert `i` qualifies when `f_i < threshold` for `consec` consecutive
    steps. Rate limit: at most one resurrection event per `rate_limit_steps`.
    """
    if current_step - last_resurrection_step < rate_limit_steps:
        return set()
    if len(f_history) < consec:
        return set()
    recent = f_history[-consec:]
    N_e = len(recent[0])
    flagged = set()
    for i in range(N_e):
        if all(snap[i] < threshold for snap in recent):
            flagged.add(i)
    return flagged


def resurrection_perturb_distribution(
    f_per_expert: Tensor, target_idx: int, eps_std: float = 0.05
) -> Tensor:
    """Perturbation contract: `ε ~ N(0, eps_std²·I)` for the cloned expert."""
    return torch.randn_like(f_per_expert) * eps_std


def beta_saturation_warning(β_per_expert: Tensor) -> bool:
    """True iff any single `β_i > 30.4` (95% of β_max)."""
    return bool((β_per_expert > BETA_SATURATION_WARN).any().item())


def beta_saturation_global_halve(β_per_expert: Tensor) -> bool:
    """True iff more than 50% of `β_i > 28.8` (90% of β_max)."""
    n = β_per_expert.numel()
    return bool((β_per_expert > BETA_SATURATION_HALVE).sum().item() > n / 2)


def loss_spike_defense(
    L_task: float, L_task_ema: float, phase: int, ratio: float = LOSS_SPIKE_RATIO
) -> bool:
    """True iff phase ≥ 3 and `L_task > ratio · L_task_ema`."""
    if phase < 3:
        return False
    return L_task > ratio * L_task_ema


__all__ = [
    "STEP_ORDER",
    "BETA_SATURATION_WARN",
    "BETA_SATURATION_HALVE",
    "DEAD_EXPERT_FRACTION",
    "DEAD_EXPERT_CONSEC_STEPS",
    "RESURRECTION_RATE_LIMIT_STEPS",
    "LOSS_SPIKE_RATIO",
    "LOSS_SPIKE_LR_SCALE",
    "clip_global_grad_norm_",
    "nan_ladder",
    "should_resurrect",
    "resurrection_perturb_distribution",
    "beta_saturation_warning",
    "beta_saturation_global_halve",
    "loss_spike_defense",
]