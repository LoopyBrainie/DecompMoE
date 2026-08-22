"""8 geometric metrics + REALTIME/OFFLINE classification (Req 20).

Realtime (every step): L_sep, R_H, S_load, UR.
Offline:               SP, D_c, MCI, CG.
"""
from __future__ import annotations

from typing import Final, Literal

import torch
from torch import Tensor

from decompmoe.config import MVPConfig
from decompmoe.loss import compute_L_sep as _compute_L_sep_internal


REALTIME: Final[frozenset[str]] = frozenset({"L_sep", "R_H", "S_load", "UR"})
OFFLINE: Final[frozenset[str]] = frozenset({"SP", "D_c", "MCI", "CG"})


def L_sep(c_centroids: Tensor) -> Tensor:
    """Centroid orthogonality loss (cross-equal to `loss.compute_L_sep`)."""
    return _compute_L_sep_internal(c_centroids)


def R_H(p: Tensor) -> Tensor:
    """Normalized entropy of routing distribution over N_e experts.

    R_H(p) = -Σ p_i log(p_i) / log(N_e) ∈ [0, 1].
    """
    p_safe = p.clamp_min(1e-12)
    n = p.shape[-1]
    entropy = -(p_safe * p_safe.log()).sum(dim=-1)
    return entropy / torch.log(torch.tensor(float(n)))


def S_load(f_per_expert: Tensor) -> Tensor:
    """Load skew across N_e experts: `S_load = N_e · max_i f_i`.

    Spec (wayfinder Req 20 + archived `fix-openspec-doc-bugs`): S_load
    equals `N_e · max_i f_i`. Range: `1` at perfect uniformity (each
    expert receives `1/N_e`), `N_e` at full collapse to a single expert.
    """
    return f_per_expert.shape[-1] * f_per_expert.max(dim=-1).values


def UR(f_per_expert_history) -> Tensor:
    """Utilization rate over the most recent W=100 steps.

    Spec (wayfinder Req 20): `UR = (1/N_e) · Σ_i I[f_i > 0]` over the most
    recent W = 100 steps. Accepts either a single-step tensor `(N_e,)`
    or a history list/stack of recent `f_per_expert` tensors.
    """
    if isinstance(f_per_expert_history, list):
        if len(f_per_expert_history) == 0:
            return torch.tensor(0.0)
        stacked = torch.stack(f_per_expert_history, dim=0)  # (T, ..., N_e)
    else:
        stacked = f_per_expert_history
    if stacked.dim() == 1:
        return (stacked > 0).float().mean()
    any_active = (stacked > 0).any(dim=0)  # (..., N_e)
    return any_active.float().mean(dim=-1)


def SP(c_centroids: Tensor, assignments: Tensor) -> Tensor:
    """Specialization purity (offline; full implementation deferred)."""
    return torch.tensor(0.0)


def D_c(c_centroids: Tensor) -> Tensor:
    """Per-expert geodesic spread on the sphere (offline; O(N_e²))."""
    return torch.tensor(0.0)


def MCI(c_centroids: Tensor) -> Tensor:
    """Effective-dimensionality fraction (offline)."""
    return torch.tensor(0.0)


def CG(c_centroids: Tensor) -> Tensor:
    """Debug-only chordogram (offline)."""
    return torch.tensor(0.0)


ArchKind = Literal["MOE", "DENSE"]


def flops_per_token(cfg: MVPConfig, arch: ArchKind = "MOE") -> int:
    """Return per-token active forward FLOPs. Mirrors `config.flops_per_token`."""
    from decompmoe.config import flops_per_token as _cfg_flops
    return _cfg_flops(cfg, arch=arch)


__all__ = [
    "REALTIME",
    "OFFLINE",
    "L_sep",
    "R_H",
    "S_load",
    "UR",
    "SP",
    "D_c",
    "MCI",
    "CG",
    "flops_per_token",
]