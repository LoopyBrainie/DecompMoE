"""Tests for `decompmoe.gating`: top-k mask + local softmax.

ST-07 / Req 8 — k=2 sparse mask with −∞ sentinel; local softmax over the
top-k active set only. Forward: `x_out = x + Σ p_i · Expert_i(x)` is the
ONLY routing equation (grep test).
"""

from __future__ import annotations

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
    assert grad is not None
    is_neg_inf = torch.isinf(masked)
    assert torch.all(grad[is_neg_inf] == 0.0), (
        f"non-top-k gradients must be 0, got {grad[is_neg_inf]}"
    )


def test_forward_formula_strictness() -> None:
    """Real-routing path: compose MUST use gating functions; verify against
    an independently-derived closed form (NOT a re-implementation).

    Spec Req 31 "Forward Formula Numerical Verification": given stub
    experts[i](x) = E_i (fixed per expert), the routing layer's x_out must
    equal x + Σ_{i ∈ I_k} p_i · E_i within abs=1e-6. This test exercises
    the actual `gating.topk_mask_with_neg_inf` + `gating.local_softmax`
    path and compares against an INDEPENDENT derivation of the closed form
    (using `torch.softmax` and `topk` directly, NOT `gating.local_softmax`).
    """
    torch.manual_seed(0)
    N_e, d_model, k = 16, 8, 2
    x = torch.randn(d_model)
    logits = torch.randn(N_e)
    fixed_outputs = torch.randn(N_e, d_model)

    # ---- LEFT side: actual routing path (calls gating module) ----
    def compose_routing(
        x_in: torch.Tensor, logits_in: torch.Tensor, E: torch.Tensor
    ) -> torch.Tensor:
        masked = gating.topk_mask_with_neg_inf(logits_in.unsqueeze(0), k=k)
        p = gating.local_softmax(masked).squeeze(0)  # (N_e,)
        return x_in + torch.einsum("i,id->d", p, E)

    x_out = compose_routing(x, logits, fixed_outputs)

    # ---- RIGHT side: independently derived closed form ----
    # Uses `torch.softmax` (NOT gating.local_softmax) so a bug in
    # local_softmax would break this side.
    topk_vals, topk_idx = logits.topk(k)
    p_topk = torch.softmax(topk_vals, dim=-1)
    expected = x.clone()
    for j in range(k):
        i = topk_idx[j]
        expected = expected + p_topk[j] * fixed_outputs[i]

    assert torch.allclose(x_out, expected, atol=1e-6), (
        f"routing mismatch: max diff = {(x_out - expected).abs().max().item():.3e}"
    )
    # Sanity: non-top-k p_i must be exactly 0 (via the actual gating path).
    masked = gating.topk_mask_with_neg_inf(logits.unsqueeze(0), k=k)
    p = gating.local_softmax(masked).squeeze(0)
    active = masked.squeeze(0) > float("-inf")
    assert (p[~active] == 0).all(), "non-top-k p must be 0 (gating output)"


def test_convex_combination_dtype_safe() -> None:
    """p has same dtype as logits and is fully finite."""
    torch.manual_seed(0)
    for dtype in (torch.float32, torch.float64):
        logits = torch.randn(4, 8, dtype=dtype)
        masked = gating.topk_mask_with_neg_inf(logits, k=2)
        p = gating.local_softmax(masked)
        assert p.dtype == logits.dtype
        assert torch.isfinite(p).all()
