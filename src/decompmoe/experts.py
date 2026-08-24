"""Standard SwiGLU experts (Req 9) + ExpertPool with no shared branch (Req 10).

Each `SwiGLUExpert` is a Llama-style SwiGLU FFN:
    Expert_i(x) = (SiLU(x W_i^g) ⊙ x W_i^u) W_i^d
parameterized by 3 · d_model · d_ffn learnable weights, with no C-derived
injection (the geometric routing chain does not touch the expert body).

`ExpertPool` is a thin container for the N_e experts — it has NO shared
expert slot (A5-2 decision; CLAUDE.md §6 hard constraint).
"""

from __future__ import annotations

import torch
from torch import Tensor, nn

from decompmoe.config import MVPConfig


class SwiGLUExpert(nn.Module):
    """Standard SwiGLU FFN: `(SiLU(x W^g) ⊙ x W^u) W^d`.

    Weights follow `nn.Linear` convention: W_g, W_u ∈ R^{d_ffn × d_model},
    W_d ∈ R^{d_model × d_ffn}. Forward: `((silu(x @ W_g.T) ⊙ x @ W_u.T)) @ W_d.T`.
    """

    def __init__(self, cfg: MVPConfig) -> None:
        super().__init__()
        self.W_g = nn.Parameter(torch.empty(cfg.d_ffn, cfg.d_model))
        self.W_u = nn.Parameter(torch.empty(cfg.d_ffn, cfg.d_model))
        self.W_d = nn.Parameter(torch.empty(cfg.d_model, cfg.d_ffn))
        nn.init.normal_(self.W_g, std=0.02)
        nn.init.normal_(self.W_u, std=0.02)
        nn.init.normal_(self.W_d, std=0.02)

    def forward(self, x: Tensor) -> Tensor:
        return (
            torch.nn.functional.silu(x @ self.W_g.T) * (x @ self.W_u.T)
        ) @ self.W_d.T


class ExpertPool(nn.Module):
    """Container of N_e SwiGLU experts. NO shared expert slot (A5-2).

    An `nn.Module` with `experts: nn.ModuleList[SwiGLUExpert]` so that
    `pool.parameters()` aggregates all N_e experts (spec: skeleton
    "Standard SwiGLU Expert With No Shared Branch": param total ==
    N_e · 3 · d_model · d_ffn == 100_663_296 exact at MVP).
    """

    def __init__(self, cfg: MVPConfig) -> None:
        super().__init__()
        self.experts = nn.ModuleList([SwiGLUExpert(cfg) for _ in range(cfg.N_e)])

    def __len__(self) -> int:
        return len(self.experts)


__all__ = ["SwiGLUExpert", "ExpertPool"]
