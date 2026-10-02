"""Loss composition `L_CE + α·L_lb + λ(t)·L_sep` (Req 12).

Notation (A1-1):
    - `C_t^l` is per-token, per-layer territory signature (shape [..., d_c]).
    - `c_i^l` is per-expert, per-layer centroid (shape [N_e, d_c]).

Closed-form spec contract (wayfinder Req 12 + archived
`fix-openspec-doc-bugs` + `fix-spec-doc-oversights`):
    - α = 0.01 (Switch-style fixed weight on L_lb)
    - L_lb = N_e · Σ_i f_i.detach() · P_i
      where P_i = (1/T) · Σ_t p_i(C_t)
      gradient MUST flow through P_i (back into logit → (C, c_i, β))
      and be BLOCKED through f_i.detach()
    - L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))  (canonical Frobenius)
    - λ(t): phase 1–2 = 0, phase 3 = cosine ramp 0 → 0.001, phase 4 = 0.001
"""
from __future__ import annotations

import dataclasses
import math
from typing import Final

import torch
import torch.nn.functional as F
from torch import Tensor

from decompmoe.schedule import _DEFAULT_TOTAL, phase_boundaries


ALPHA: Final[float] = 0.01
LAMBDA_MAX: Final[float] = 0.001


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
    Equivalent reformulation: `(2/(N_e(N_e−1))) · Σ_{i<j} (c_iᵀc_j)²`.
    """
    G = c_centroids @ c_centroids.T  # (N_e, N_e)
    N_e = G.shape[0]
    fro_sq = (G * G).sum()
    return (fro_sq - N_e) / (N_e * (N_e - 1))


def _lambda_at(phase: int, step: int, total_steps: int = _DEFAULT_TOTAL) -> float:
    """Staged λ(t) schedule (Req 12).

    `total_steps` is honoured the same way `schedule.phase_id` and
    `schedule.phase_beta_max` honour it, so a non-100K run does not ramp λ over
    the 100K window while every other consumer rescales.
    """
    if phase in (1, 2):
        return 0.0
    if phase == 3:
        bounds = phase_boundaries(total_steps)
        t_start = bounds[2]
        t_end = bounds[3]
        progress = max(0.0, min(1.0, (step - t_start) / (t_end - t_start)))
        return 0.5 * (1.0 - math.cos(math.pi * progress)) * LAMBDA_MAX
    if phase == 4:
        return LAMBDA_MAX
    return 0.0


def L_total(
    task_logits: Tensor,
    targets: Tensor,
    f_per_expert: Tensor,
    p_per_expert: Tensor,
    c_centroids: Tensor,
    phase: int,
    step: int,
    *,
    cfg=None,
    total_steps: int = _DEFAULT_TOTAL,
) -> LossParts:
    """Total loss: `L_CE + α·L_lb + λ(t)·L_sep`.

    Args:
        task_logits:    (B, N, V) — task vocabulary logits.
        targets:        (B, N)    — token targets.
        f_per_expert:   (B, N, N_e) — hard routing fraction per expert
                        (averaged over batch). Detached for L_lb.
        p_per_expert:   (B, N, N_e) — soft routing probability per expert
                        (per-token differentiable). Required for the
                        spec-mandated L_lb closed form (f.detach · P).
        c_centroids:    (N_e, d_c) — per-expert centroids.
        phase:          int (0..4) — current schedule phase.
        step:           int — global training step.
        cfg:            optional MVPConfig. Supplies the spec-mandated
                        `N_e` in the `L_lb` closed form
                        (`L_lb = N_e · Σ_i f_i.detach() · P_i`); when
                        omitted, `N_e` falls back to the routing-tensor
                        width `f_per_expert.shape[-1]`.
        total_steps:    total training-step budget. Threaded into the λ(t)
                        schedule exactly as `schedule.phase_id` and
                        `schedule.phase_beta_max` consume it, so a non-100K
                        run rescales λ and the phase boundaries together.

    Returns:
        LossParts dataclass with each component.
    """
    L_CE = F.cross_entropy(
        task_logits.reshape(-1, task_logits.shape[-1]),
        targets.reshape(-1),
    )

    # L_lb closed form (wayfinder Req 12 + archived spec):
    #   L_lb = N_e · Σ_i f_i.detach() · P_i
    # where P_i = (1/T) · Σ_t p_i(C_t) (mean over tokens of the per-expert
    # soft probability). We average over (B, N) too to match the scalar
    # L_CE convention.
    f_det = f_per_expert.detach()
    P_mean = p_per_expert.mean(dim=(0, 1))  # (N_e,)
    # `N_e` in the spec closed form is the model-wide constant, so it is read
    # from cfg whenever the caller supplies one; the routing-tensor width is
    # only the cfg-free fallback (they coincide under the `N_e` invariant).
    N_e = cfg.N_e if cfg is not None else f_per_expert.shape[-1]
    L_lb_raw = (f_det.mean(dim=(0, 1)) * P_mean).sum() * N_e
    L_lb = ALPHA * L_lb_raw

    L_sep_raw = compute_L_sep(c_centroids)
    lam = _lambda_at(phase, step, total_steps)
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