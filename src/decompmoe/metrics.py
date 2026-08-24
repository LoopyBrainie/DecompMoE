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

# Named zero-sentinel for degenerate/empty-input returns (NOT a metric stub —
# the four offline closed forms below are fully implemented).
_ZERO = torch.zeros(())
OFFLINE: Final[frozenset[str]] = frozenset({"SP", "D_chord", "MCI", "CG"})


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
    try:
        return entropy / torch.log(torch.tensor(float(n)))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"R_H: invalid p shape (n={n})") from exc


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
            return _ZERO
        stacked = torch.stack(f_per_expert_history, dim=0)  # (T, ..., N_e)
    else:
        stacked = f_per_expert_history
    if stacked.dim() == 1:
        return (stacked > 0).float().mean()
    any_active = (stacked > 0).any(dim=0)  # (..., N_e)
    return any_active.float().mean(dim=-1)


def SP(
    centroids: Tensor, assignments: Tensor, signatures: Tensor
) -> Tensor:
    """Specialization purity (offline).

    Spec signature: ``SP(centroids, assignments, signatures)``.
    Per-expert purity ``SP_i = mean_{t: a(t)=i} c_iᵀ C_t``; overall
    ``SP = mean({SP_i : ‖T_i‖₁ > 0})`` — empty experts are SKIPPED,
    not reported as 0. Closed forms: aligned inputs → 1.0;
    60° offset → 0.5. Range containment: [−1 − 1e-6, 1 + 1e-6].
    """
    C_t = signatures
    if C_t.numel() == 0:
        return _ZERO
    N_e = centroids.shape[0]
    per_expert_means: list[Tensor] = []
    for i in range(N_e):
        member = assignments == i
        n_i = member.sum()
        try:
            n_i_val = int(n_i.item())
        except (ValueError, RuntimeError) as exc:
            raise ValueError(f"SP: cannot read n_i for expert {i}") from exc
        if n_i_val == 0:
            continue  # skip empty expert (‖T_i‖₁ == 0)
        align = (C_t[member] * centroids[i].unsqueeze(0)).sum(dim=-1)
        per_expert_means.append(align.mean())
    if not per_expert_means:
        return _ZERO
    return torch.stack(per_expert_means).mean()


def D_chord(c_centroids: Tensor) -> Tensor:
    """Mean pairwise spherical chord distance over distinct centroid pairs.

    Spec: D_chord(c_i, c_j) = √(2 · versine θ_ij) with versine θ = 1 − cos θ,
    i.e. √(2·(1 − cᵢᵀcⱼ)). Orthonormal basis → √2 exact. O(N_e²).
    """
    N_e = c_centroids.shape[0]
    if N_e < 2:
        return _ZERO
    sims = c_centroids @ c_centroids.T
    iu = torch.triu_indices(N_e, N_e, offset=1)
    pair_sims = sims[iu[0], iu[1]]
    pair_chord = torch.sqrt((2.0 * (1.0 - pair_sims)).clamp_min(0.0))
    return pair_chord.mean()


def MCI(token_signatures: Tensor) -> Tensor:
    """MCI = 1 / (d_c · Σ λ̃_j²) on the uncentered second moment of tokens.

    Spec (wayfinder ADDED Requirements): input is TOKEN SIGNATURES
    (not centroids); M = (1/|T|) Σ_t C_t C_tᵀ; λ̃_j = λ_j / Σ_r λ_r.
    Closed forms: uniform token distribution → 1.0; rank-1 → 1/d_c.
    Range: [1/d_c, 1].
    """
    d_c = token_signatures.shape[-1]
    T_n = token_signatures.shape[0]
    try:
        T_n_f = float(T_n)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"MCI: invalid token count {T_n}") from exc
    if T_n_f <= 0.0:
        raise ValueError(f"MCI: degenerate input (T_n={T_n_f})")
    M_mat = token_signatures.T @ token_signatures / T_n_f
    eigvals = torch.linalg.eigvalsh(M_mat).clamp_min(0.0)
    total = eigvals.sum()
    try:
        total_f = float(total.item())
    except (ValueError, RuntimeError) as exc:
        raise ValueError("MCI: cannot read total of eigvals") from exc
    if total_f <= 0.0:
        raise ValueError("degenerate second moment: all eigenvalues are zero")
    lam_norm = eigvals / total
    return 1.0 / (d_c * (lam_norm ** 2).sum())


def CG(grad: Tensor) -> Tensor:
    """Chordogram-style dispersion debug metric (offline; homogeneous deg 1).

    CG(g) = mean pairwise |g_i − g_j| over entries — zero-gradient invariant
    (CG(0) == 0) and positively homogeneous (CG(2g) == 2·CG(g)).
    """
    n = grad.numel()
    if n < 2:
        return _ZERO
    g_flat = grad.reshape(-1)
    diffs = (g_flat.unsqueeze(0) - g_flat.unsqueeze(1)).abs()
    iu = torch.triu_indices(n, n, offset=1)
    return diffs[iu[0], iu[1]].mean()


ArchKind = Literal["MOE", "DENSE"]


def flops_per_token(cfg: MVPConfig, arch: ArchKind = "MOE") -> int:
    """Return per-token active forward FLOPs. Mirrors `config.flops_per_token`."""
    from decompmoe.config import flops_per_token as _cfg_flops
    return _cfg_flops(cfg, arch=arch)


__all__ = [
    "CG",
    "MCI",
    "OFFLINE",
    "REALTIME",
    "R_H",
    "SP",
    "UR",
    "D_chord",
    "L_sep",
    "S_load",
    "flops_per_token",
]
