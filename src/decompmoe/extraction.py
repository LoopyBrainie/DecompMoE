"""C-extraction 4-step pipeline + 4-phase centroid lifecycle driver.

This module materializes Req 5 (full pipeline) + Req 6 (no STE, fully
differentiable; centroid lifecycle: Phase 0 k-means → Phases 1–3 EMA →
Phase 4 projected SGD).

`extract_C` is the per-frame, stateless signature of the geometric routing
chain (Req 17): `(K, V) → C ∈ R^{B × N × d_c}`, no KV-cache side effect.

`CentroidDriver` exposes the four-phase centroid update rule (k-means →
0.90 → 0.95 → 0.99 → projected SGD).

The module is import-side-effect-free: no autograd state, no global
registries, no `torch.utils.cpp_extension` / `triton` imports (Req 9/18).
"""
from __future__ import annotations

from enum import IntEnum
from typing import Final

import torch
from torch import Tensor

from decompmoe.sphere import spherical_l2_normalize


# ---------------------------------------------------------------------------
# 4-step C extraction pipeline (Req 5)
# ---------------------------------------------------------------------------


def extract_C(
    K: Tensor,
    V: Tensor,
    W_K: Tensor,
    W_V: Tensor,
    b: Tensor,
    *,
    H_kv: int,
    d_c: int,
    eps: float = 1e-6,
) -> Tensor:
    """Stateless C extraction from (K, V) following the spec's 4-step pipeline.

    Step 1 — per-head projection:
        z^{l,h} = W_K^{l,h} · k_t^{l,h} + W_V^{l,h} · v_t^{l,h} + b^{l,h}
    Step 2 — per-head spherical projection (ε-safety).
    Step 3 — cross-head mean with `1/H_kv` factor.
    Step 4 — final spherical projection (ε-safety).

    Differentiability: every step contributes a finite gradient; no
    Straight-Through Estimator is inserted between `z` and `C` (Req 6).
    """
    z = torch.einsum("bhnd,hde->bhne", K, W_K) + torch.einsum(
        "bhnd,hde->bhne", V, W_V
    )
    z = z + b.view(1, H_kv, 1, d_c)

    # Step 2: per-head spherical projection.
    z_unit = spherical_l2_normalize(z, eps=eps)

    # Step 3: cross-head mean (1/H_kv factor built in by `mean`).
    z_bar = z_unit.mean(dim=1)  # (B, N, d_c)

    # Step 4: final spherical projection.
    C = spherical_l2_normalize(z_bar, eps=eps)
    return C


# ---------------------------------------------------------------------------
# Centroid 4-phase lifecycle (Req 6)
# ---------------------------------------------------------------------------


class Phase(IntEnum):
    """Centroid lifecycle phase (Req 6 / A3-2)."""

    SEEDING = 0           # spherical k-means (no gradient)
    EMA_090 = 1           # α = 0.90
    EMA_095 = 2           # α = 0.95
    EMA_099 = 3           # α = 0.99
    PROJECTED_SGD = 4     # L2 retraction after SGD step


_EMA_ALPHA: Final[dict[int, float]] = {
    int(Phase.EMA_090): 0.90,
    int(Phase.EMA_095): 0.95,
    int(Phase.EMA_099): 0.99,
}


class CentroidDriver:
    """Per-layer centroid lifecycle driver."""

    def __init__(self, phase: Phase) -> None:
        self.phase = phase

    def step(
        self,
        centroids: Tensor,
        X: Tensor,
        mask: Tensor | None = None,
        eps: float = 1e-6,
    ) -> Tensor:
        """Apply the centroid update rule for `self.phase`.

        Phase 0 (SEEDING):        no-op (returns centroids detached — actual
                                  k-means is owned by training-time caller).
        Phase 1–3 (EMA_xxx):      centroids ← α · centroids + (1 − α) · mean(X|mask)
        Phase 4 (PROJECTED_SGD):  L2 retraction: centroids / ‖centroids‖₂
        """
        if self.phase == Phase.SEEDING:
            return centroids.detach()

        if int(self.phase) in _EMA_ALPHA:
            alpha = _EMA_ALPHA[int(self.phase)]
            if mask is None:
                mean = X.mean(dim=0)
                if mean.dim() == 1:
                    mean = mean.unsqueeze(0).expand_as(centroids)
            else:
                # mask: (T, N_e) — soft assignment per token.
                # Empty-cell invariant (skeleton spec "Centroid Driver Semantic
                # Invariants" + Invariant 1): when n_i = 0, m_i must default
                # to the previous centroid c_i^(t-1) — NOT a direction-randomized
                # 0/clamp_min(eps). `safe_n.clamp_min(1.0)` is used solely to
                # guard the division against 0/0 NaN; the actual `mean` is
                # selected via torch.where.
                weights = mask
                n_i = weights.sum(dim=0)
                weighted = weights.T @ X  # zero when n_i = 0
                safe_n = n_i.clamp_min(1.0)
                mean_n = weighted / safe_n.unsqueeze(-1)
                mean = torch.where(n_i.unsqueeze(-1) > 0, mean_n, centroids)
            # Spherical re-projection invariant (Invariant 2): every EMA step
            # MUST enforce ‖c_i^(t+1)‖₂ ≡ 1.0. Near-zero candidate fallback
            # (‖candidate‖₂ < 1e-9): preserve the previous centroid to
            # prevent NaN and maintain spherical boundedness.
            candidate = alpha * centroids + (1.0 - alpha) * mean
            norm = candidate.norm(dim=-1, keepdim=True)
            use_old = norm < 1e-9
            return torch.where(use_old, centroids, torch.nn.functional.normalize(candidate, dim=-1))

        if self.phase == Phase.PROJECTED_SGD:
            return centroids / centroids.norm(dim=-1, keepdim=True).clamp_min(eps)

        raise ValueError(f"Unknown phase={self.phase!r}")


__all__ = [
    "extract_C",
    "Phase",
    "CentroidDriver",
]