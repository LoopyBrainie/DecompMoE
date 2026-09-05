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

# Dead-expert resurrection parameters (wayfinder Req 13 / archived spec).
# Threshold is parameterized by N_e (= 1/(2·N_e)); at MVP N_e=16 this
# evaluates to 1/32. Previously hardcoded to 1/128 (N_e=64 legacy).
DEAD_EXPERT_CONSEC_STEPS: Final[int] = 200
RESURRECTION_RATE_LIMIT_STEPS: Final[int] = 1000


def _dead_expert_threshold(N_e: int) -> float:
    """Return the dead-expert threshold `1 / (2·N_e)` for the given N_e."""
    return 1.0 / (2.0 * N_e)


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
    *,
    N_e: int,
    consec: int = DEAD_EXPERT_CONSEC_STEPS,
    rate_limit_steps: int = RESURRECTION_RATE_LIMIT_STEPS,
    threshold: float | None = None,
) -> set[int]:
    """Return set of expert indices that need resurrection (rate-limited).

    An expert `i` qualifies when `f_i < threshold` for `consec` consecutive
    steps. Rate limit: at most one resurrection event per `rate_limit_steps`.

    Spec (wayfinder Req 13): the threshold is parameterized by N_e as
    `1 / (2·N_e)`; at MVP N_e=16 this evaluates to 1/32. Pass an explicit
    `threshold` to override (e.g. for testing the rate-limit edge cases
    without changing N_e).
    """
    if threshold is None:
        threshold = _dead_expert_threshold(N_e)
    if current_step - last_resurrection_step < rate_limit_steps:
        return set()
    if len(f_history) < consec:
        return set()
    recent = f_history[-consec:]
    flagged = set()
    for i in range(N_e):
        if all(snap[i] < threshold for snap in recent):
            flagged.add(i)
    return flagged


def resurrection_perturb_distribution(
    f_per_expert: Tensor,
    target_idx: int,
    eps_std: float = 0.05,
    *,
    dim: int | None = None,
) -> Tensor:
    """Per-expert clone perturbation: `ε ~ N(0, eps_std²·I)`.

    Spec (wayfinder ADDED "Resurrection Perturbation Per-Expert Contract"):
    returns a SINGLE-expert tensor of shape `(d_c,)` or `(d_model·d_ffn,)`
    — NOT a per-expert `(N_e,)` tensor. `target_idx` selects the expert
    being resurrected (kept for contract compatibility); `dim` MUST be
    passed explicitly (signature `(d_c,)` at MVP). No default — passing
    `dim=None` raises `TypeError` to prevent silent use of
    `f_per_expert.shape[-1] == N_e` (which would violate the per-expert
    contract by returning an `(N_e,)` perturbation).
    """
    del target_idx  # contract signature only; perturbation is one vector
    if dim is None:
        raise TypeError(
            "resurrection_perturb_distribution requires explicit `dim` "
            "(spec Req 28: shape (d_c,) or (d_model·d_ffn,) per single "
            "expert — not the implicit (N_e,) derived from "
            "`f_per_expert.shape[-1]`)."
        )
    if not isinstance(dim, int):
        dim = int(dim)
    return torch.randn(dim) * eps_std


RESURRECTION_BETA_DECAY: Final[float] = 0.85


def apply_resurrection_beta_decay(β_per_expert: Tensor, j_star: int, i: int) -> Tensor:
    """Same-event β mutation on resurrection (returns a NEW tensor).

    Spec: β_i ← 0.85·β_{j*} AND β_{j*} ← 0.85·β_{j*} as part of the same
    event. The donor value is read BEFORE either write (immutability:
    input tensor is never mutated).
    """
    donor = β_per_expert[j_star].item()
    if not isinstance(donor, float):
        donor = float(donor)
    out = β_per_expert.clone()
    out[j_star] = RESURRECTION_BETA_DECAY * donor
    out[i] = RESURRECTION_BETA_DECAY * donor
    return out


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
    "DEAD_EXPERT_CONSEC_STEPS",
    "RESURRECTION_RATE_LIMIT_STEPS",
    "LOSS_SPIKE_RATIO",
    "LOSS_SPIKE_LR_SCALE",
    "clip_global_grad_norm_",
    "nan_ladder",
    "should_resurrect",
    "resurrection_perturb_distribution",
    "apply_resurrection_beta_decay",
    "beta_saturation_warning",
    "beta_saturation_global_halve",
    "loss_spike_defense",
]
