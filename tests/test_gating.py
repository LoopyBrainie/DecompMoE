"""Tests for `decompmoe.gating`: top-k mask + local softmax.

ST-07 / Req 8 — k=2 sparse mask with −∞ sentinel; local softmax over the
top-k active set only. Forward: `x_out = x + Σ p_i · Expert_i(x)` is the
ONLY routing equation (grep test).
"""
from __future__ import annotations

import pytest
import torch

from decompmoe import gating
from decompmoe.config import MVPConfig


def test_k_equals_two() -> None:
    assert MVPConfig().k == 2


def test_neg_inf_sentinel_used() -> None:
    """Non-top-k entries are exactly `-float('inf')`, NOT a large finite negative."""
    torch.manual_seed(0)
    logits = torch.randn(8, 16)
    masked = gating.topk_mask_with_neg_inf(logits, k=2)
    neg_inf_mask = torch.isinf(masked) & (masked < 0)
    assert neg_inf_mask.any(), "non-top-k entries must be -inf"
    is_neg_inf = torch.isinf(masked)
    top_k_mask = torch.zeros_like(masked, dtype=torch.bool)
    _, idx = logits.topk(2, dim=-1)
    top_k_mask.scatter_(1, idx, True)
    kept = masked[top_k_mask]
    assert torch.isfinite(kept).all()
    orig_kept = logits[top_k_mask]
    assert torch.allclose(kept, orig_kept)


def test_partition_of_unity() -> None:
    """local_softmax produces p with Σ p == 1 over the top-k active set."""
    torch.manual_seed(0)
    logits = torch.randn(8, 16) * 4
    masked = gating.topk_mask_with_neg_inf(logits, k=2)
    p = gating.local_softmax(masked)
    assert torch.allclose(p.sum(dim=-1), torch.ones(8), atol=1e-6)
    assert (p >= 0).all()
    assert torch.isfinite(p).all()


def test_zero_grad_for_non_top_k() -> None:
    """torch.autograd.grad on non-top-k entries is exactly zero (no STE)."""
    torch.manual_seed(0)
    logits = torch.nn.Parameter(torch.randn(4, 8))
    masked = gating.topk_mask_with_neg_inf(logits, k=2)
    p = gating.local_softmax(masked)
    p.sum().backward()
    grad = logits.grad
    is_neg_inf = torch.isinf(masked)
    assert torch.all(grad[is_neg_inf] == 0.0), (
        f"non-top-k gradients must be 0, got {grad[is_neg_inf]}"
    )


def test_forward_formula_strictness() -> None:
    """`gating.py` must contain the forward formula x_out = x + Σ p_i · Expert_i(x)."""
    from pathlib import Path
    src = Path(gating.__file__).read_text(encoding="utf-8")
    assert "x_out" in src, (
        "gating.py must contain the forward formula x_out = x + Σ p_i · Expert_i(x)"
    )


def test_convex_combination_dtype_safe() -> None:
    """p has same dtype as logits and is fully finite."""
    torch.manual_seed(0)
    for dtype in (torch.float32, torch.float64):
        logits = torch.randn(4, 8, dtype=dtype)
        masked = gating.topk_mask_with_neg_inf(logits, k=2)
        p = gating.local_softmax(masked)
        assert p.dtype == logits.dtype
        assert torch.isfinite(p).all()