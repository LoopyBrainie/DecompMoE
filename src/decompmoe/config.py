"""Frozen 4070 MVP hyperparameters + total/active parameter estimator.

This module materializes Req 1, Req 2, Req 11, and Req 19 of
`openspec/specs/wayfinder/spec.md`:

    - `MVPConfig` is a `frozen=True` dataclass whose fields are the locked
      geometric constants for the 4070 8 GB MVP.
    - `compute_total_and_active(cfg)` returns `(total_params, active_params_per_token)`
      using the agreed accounting: total = embedding + L × (attention + experts);
      active = embedding + L × (attention + k × expert_params).
    - `flops_per_token(cfg, arch)` returns the per-token active FLOPs for the
      MoE MVP and for a Dense baseline of `d_ffn_dense=4096`. The two values
      are equal under the agreed accounting (1:1 FLOPs parity per Req 11 / 19).

The module is import-side-effect-free: no torch device calls, no autograd
state, no global registries.
"""

from __future__ import annotations

import dataclasses
from typing import Literal

# ---------------------------------------------------------------------------
# Frozen MVP configuration dataclass (Req 11)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class MVPConfig:
    """Locked 4070 8 GB MVP hyperparameter set.

    Every field is frozen at construction time. Mutation raises
    `dataclasses.FrozenInstanceError` (asserted by `test_mvp_is_frozen`).

    The dataclass only carries GEOMETRY constants (model shape). Algorithmic
    constants (β_min, β_max, α, λ_max, etc.) live with their usage site —
    see design.md D1.
    """

    d_model: int = 1024
    N_e: int = 16
    k: int = 2
    d_ffn: int = 2048
    L: int = 4
    d_ffn_dense: int = 4096
    d_c: int = 16
    H_kv: int = 8
    d_k: int = 128
    # Initial inverse-temperature β₀ = 1.0 — proxy for γ₀ ≈ −3.5 (the exact
    # γ₀ is pending a spec-level backfill change, tracked as `★ TODO` in the
    # plan §ST-02). Stored here so downstream code can read the canonical
    # default without reaching into the `beta` module.
    beta_initial: float = 1.0
    # Embedding table size — required to reconcile 452M total. With vocab=32K
    # and d_model=1024, embedding contributes 32M, leaving 420M for the
    # transformer stack (matches Req 11 within ±1%).
    vocab_size: int = 32000


# ---------------------------------------------------------------------------
# Total / active parameter estimator (Req 11: ≈452M / ≈100M)
# ---------------------------------------------------------------------------


def _attention_params_per_layer(cfg: MVPConfig) -> int:
    """Q/K/V/O projections per layer (dense d_model × d_model)."""
    return 4 * cfg.d_model * cfg.d_model


def _expert_params(cfg: MVPConfig) -> int:
    """Parameters of one SwiGLU expert: 3 × d_model × d_ffn."""
    return 3 * cfg.d_model * cfg.d_ffn


def _router_params_per_layer(cfg: MVPConfig) -> int:
    """Per-layer router: per-head W_K, W_V (each d_k × d_c), bias d_c."""
    per_head = 2 * cfg.d_k * cfg.d_c + cfg.d_c
    return cfg.H_kv * per_head


def compute_total_and_active(cfg: MVPConfig) -> tuple[int, int]:
    """Return `(total_params, active_params_per_token)`.

    Accounting:
        total   = embedding + L × (attention_per_layer
                                    + N_e × expert_params
                                    + router_per_layer)
        active  = embedding + L × (attention_per_layer
                                    + k × expert_params
                                    + router_per_layer)

    With `MVPConfig()` (vocab=32K, d_model=1024, L=4, N_e=16, k=2):
        total ≈ 451M (within ±1% of 452M, target 448M–456M)
        active ≈ 99M (within ±1% of 100M, target 99M–101M)
    """
    embedding = cfg.vocab_size * cfg.d_model
    attn = _attention_params_per_layer(cfg)
    expert = _expert_params(cfg)
    router = _router_params_per_layer(cfg)

    total = embedding + cfg.L * (attn + cfg.N_e * expert + router)
    active = embedding + cfg.L * (attn + cfg.k * expert + router)
    return total, active


# ---------------------------------------------------------------------------
# FLOPs parity (Req 11 / Req 19: MoE active FLOPs == Dense FLOPs)
# ---------------------------------------------------------------------------


ArchKind = Literal["MOE", "DENSE"]


def _flops_dense(cfg: MVPConfig) -> int:
    """Dense forward FLOPs per token, summed across L layers.

    Accounting per layer:
        attention (Q/K/V/O projections): 4 × 2 × d_model × d_model  (MAC = 2 FLOPs)
        FFN:                              3 × 2 × d_model × d_ffn_dense
                                          (SwiGLU has 3 matrices: g, u, d)
    """
    attn = 4 * 2 * cfg.d_model * cfg.d_model
    ffn = 3 * 2 * cfg.d_model * cfg.d_ffn_dense
    return cfg.L * (attn + ffn)


def _flops_moe(cfg: MVPConfig) -> int:
    """MoE active forward FLOPs per token.

    Same attention as dense; FFN is k × (3 × 2 × d_model × d_ffn).
    Each routed token uses exactly `k` expert FFNs; SwiGLU counts its
    3 matrices (g, u, d) — NOT 2 (fix-math-consistency-audit-2026-08).
    """
    attn = 4 * 2 * cfg.d_model * cfg.d_model
    ffn = cfg.k * 3 * 2 * cfg.d_model * cfg.d_ffn
    return cfg.L * (attn + ffn)


def flops_per_token(cfg: MVPConfig, arch: ArchKind = "MOE") -> int:
    """Return per-token active forward FLOPs for the given architecture.

    With `MVPConfig()`:
        MoE   = L × (4·2·d_model² + k·3·2·d_model·d_ffn)
        Dense = L × (4·2·d_model² + 3·2·d_model·d_ffn_dense)
    """
    if arch == "DENSE":
        return _flops_dense(cfg)
    if arch == "MOE":
        return _flops_moe(cfg)
    raise ValueError(f"Unknown arch={arch!r}; expected 'MOE' or 'DENSE'")


__all__ = [
    "MVPConfig",
    "compute_total_and_active",
    "flops_per_token",
    "ArchKind",
]
