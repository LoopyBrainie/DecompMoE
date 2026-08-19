"""Loss composition `L_CE + α·L_lb + λ(t)·L_sep` (Req 12).

Notation (A1-1):
    - `C_t^l` is per-token, per-layer territory signature (shape [..., d_c]).
    - `c_i^l` is per-expert, per-layer centroid (shape [N_e, d_c]).

Constants:
    - `ALPHA = 0.01` (Switch-style fixed weight on L_lb).
    - `LAMBDA_MAX = 0.001` (the saturation value of the cosine ramp).

L_lb uses `f_per_expert.detach()` so that load-balancing regularization does
not propagate gradient into the central task loss / router gradients (A4-2).

λ(t) staged schedule (Req 12, A6a-1):
    - Phase 1, 2:  λ = 0  (centroid-only training)
    - Phase 3:     λ(t) = cosine ramp 0 → 0.001 across the phase
    - Phase 4:     λ = 0.001 fixed
"""
from __future__ import annotations

import dataclasses
import math
from typing import Final

import torch
import torch.nn.functional as F
from torch import Tensor


ALPHA: Final[float] = 0.01
LAMBDA_MAX: Final[float] = 0.001

_PHASE_BOUNDS: Final[tuple[int, ...]] = (1_000, 6_000, 26_000, 56_000, 100_000)


@dataclasses.dataclass
class LossParts:
    """Decomposition of the total loss into its components."""

    L_CE: Tensor
    L_lb_raw: Tensor
    L_sep_raw: Tensor
    L_lb: Tensor
    L_sep: Tensor
    L_total: Tensor


def compute_L_sep(c_centroids: Tensor) -> Tensor:
    """L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1)).

    `c_centroids` is the per-expert centroid matrix, shape (N_e, d_c).
    Equivalent reformulation: `(1/(N_e(N_e−1))) · Σ_{i<j} (c_iᵀc_j)²`.
    """
    G = c_centroids @ c_centroids.T  # (N_e, N_e)
    N_e = G.shape[0]
    fro_sq = (G * G).sum()
    return (fro_sq - N_e) / (N_e * (N_e - 1))


def _lambda_at(phase: int, step: int) -> float:
    """Staged λ(t) schedule (Req 12)."""
    if phase in (1, 2):
        return 0.0
    if phase == 3:
        t_start = _PHASE_BOUNDS[2]  # 26_000
        t_end = _PHASE_BOUNDS[3]    # 56_000
        progress = max(0.0, min(1.0, (step - t_start) / (t_end - t_start)))
        return 0.5 * (1.0 - math.cos(math.pi * progress)) * LAMBDA_MAX
    if phase == 4:
        return LAMBDA_MAX
    return 0.0


def L_total(
    task_logits: Tensor,
    targets: Tensor,
    f_per_expert: Tensor,
    c_centroids: Tensor,
    phase: int,
    step: int,
) -> LossParts:
    """Total loss: `L_CE + α·L_lb + λ(t)·L_sep`.

    Args:
        task_logits: (B, N, V) — task vocabulary logits.
        targets:     (B, N)    — token targets.
        f_per_expert: (B, N, N_e) — gating fractions (will be detached for L_lb).
        c_centroids: (N_e, d_c)  — per-expert centroids.
        phase:       int (0..4) — current schedule phase.
        step:        int — global training step.

    Returns:
        LossParts dataclass with each component.
    """
    L_CE = F.cross_entropy(
        task_logits.reshape(-1, task_logits.shape[-1]),
        targets.reshape(-1),
    )

    # L_lb (Switch-style: N_e · Σ f_i · log f_i, using detached fractions)
    f_det = f_per_expert.detach()
    f_mean = f_det.mean(dim=(0, 1))  # (N_e,)
    L_lb_raw = (f_mean * f_mean.log()).sum() * f_per_expert.shape[-1]
    L_lb = ALPHA * L_lb_raw

    L_sep_raw = compute_L_sep(c_centroids)
    lam = _lambda_at(phase, step)
    L_sep = lam * L_sep_raw

    L_total_t = L_CE + L_lb + L_sep
    return LossParts(
        L_CE=L_CE,
        L_lb_raw=L_lb_raw,
        L_sep_raw=L_sep_raw,
        L_lb=L_lb,
        L_sep=L_sep,
        L_total=L_total_t,
    )


__all__ = ["ALPHA", "LAMBDA_MAX", "LossParts", "compute_L_sep", "L_total"]