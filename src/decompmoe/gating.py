"""Top-k sparse mask + local softmax gating (Req 8).

This module materializes the routing chain's gating function:
    1. `topk_mask_with_neg_inf(logits, k)`: keep top-k logits; mask the rest
       with -inf (NOT a large finite negative).
    2. `local_softmax(masked_logits)`: exponentiate over the non-(-inf) entries
       only; normalize so Σ p_i = 1 over the active set.

The forward equation is:
    x_out = x + Σ_{i ∈ I_k} p_i · Expert_i(x)
which is the ONLY routing equation in this module (asserted by grep test).
"""
from __future__ import annotations

import torch
from torch import Tensor

_NEG_INF: float = float("-inf")


def topk_mask_with_neg_inf(logits: Tensor, k: int) -> Tensor:
    """Mask all entries except the top-k per row with -inf."""
    topk_idx = logits.topk(k, dim=-1).indices  # (B, k)
    keep = torch.zeros_like(logits, dtype=torch.bool)
    keep.scatter_(-1, topk_idx, True)
    masked = torch.where(keep, logits, torch.full_like(logits, _NEG_INF))
    return masked


def local_softmax(masked_logits: Tensor) -> Tensor:
    """Local softmax over the non-(-inf) entries per row.

    Output: non-negative tensor of the same shape as `masked_logits`,
    with Σ p_i = 1 over the active set per row (and p_i = 0 for masked).
    """
    finite_max = torch.where(
        torch.isinf(masked_logits) & (masked_logits < 0),
        torch.full_like(masked_logits, float("-inf")),
        masked_logits,
    ).max(dim=-1, keepdim=True).values
    safe_max = torch.where(
        torch.isinf(finite_max), torch.zeros_like(finite_max), finite_max
    )
    shifted = masked_logits - safe_max
    exp_logits = torch.exp(shifted)
    exp_logits = torch.where(
        torch.isinf(masked_logits) & (masked_logits < 0),
        torch.zeros_like(exp_logits),
        exp_logits,
    )
    denom = exp_logits.sum(dim=-1, keepdim=True).clamp_min(1e-12)
    return exp_logits / denom


# The single canonical routing equation (asserted by `test_forward_formula_strictness`):
#
#     x_out = x + Σ_{i ∈ I_k} p_i · Expert_i(x)
#
# The actual routing computation lives in `experts.py` and downstream
# `GeometricRouter.route()` implementations; this module only emits `p`.


__all__ = ["topk_mask_with_neg_inf", "local_softmax"]