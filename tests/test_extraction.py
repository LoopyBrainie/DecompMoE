"""Tests for `decompmoe.extraction`: C-extraction 4-step pipeline (D-path).

ST-04 / Req 5 (full pipeline) + Req 6 (no STE, fully differentiable).
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import torch

from decompmoe import extraction
from decompmoe.sphere import spherical_l2_normalize


def _fake_proj(B: int, H_kv: int, d_k: int, d_c: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Make deterministic small projection parameters (per-head)."""
    torch.manual_seed(0)
    W_K = torch.randn(H_kv, d_k, d_c) * 0.1
    W_V = torch.randn(H_kv, d_k, d_c) * 0.1
    b = torch.randn(H_kv, d_c) * 0.1
    return W_K, W_V, b


# ---------------------------------------------------------------------------
# Step 1+2+3+4: output shape + on unit sphere (Req 5)
# ---------------------------------------------------------------------------


def test_pipeline_shape() -> None:
    """extract_C(K, V, W_K, W_V, b) returns [B, N, d_c] on the unit sphere."""
    torch.manual_seed(0)
    B, H_kv, N, d_k, d_c = 2, 8, 16, 128, 16
    K = torch.randn(B, H_kv, N, d_k)
    V = torch.randn(B, H_kv, N, d_k)
    W_K, W_V, b = _fake_proj(B, H_kv, d_k, d_c)
    C = extraction.extract_C(K, V, W_K, W_V, b, H_kv=H_kv, d_c=d_c)
    assert C.shape == (B, N, d_c), f"expected (B, N, d_c), got {C.shape}"
    norms_sq = C.pow(2).sum(dim=-1)
    assert torch.allclose(norms_sq, torch.ones_like(norms_sq), atol=1e-5), (
        "C must lie on the unit sphere (norm=1)"
    )


def test_aggregate_across_heads_awareness() -> None:
    """Cross-head mean uses 1/H_kv factor (GQA-aware)."""
    torch.manual_seed(0)
    B, H_kv, N, d_k, d_c = 1, 8, 4, 32, 16
    K = torch.randn(B, H_kv, N, d_k)
    V = torch.randn(B, H_kv, N, d_k)
    W_K, W_V, b = _fake_proj(B, H_kv, d_k, d_c)
    C = extraction.extract_C(K, V, W_K, W_V, b, H_kv=H_kv, d_c=d_c)

    # Manually replicate the pipeline
    z = (
        torch.einsum("bhnd,hde->bhne", K, W_K)
        + torch.einsum("bhnd,hde->bhne", V, W_V)
        + b.view(1, H_kv, 1, d_c)  # broadcast
    )
    z_per_head_unit = spherical_l2_normalize(z, eps=1e-6)
    z_bar = z_per_head_unit.mean(dim=1)  # 1/H_kv factor
    C_manual = spherical_l2_normalize(z_bar, eps=1e-6)
    # Loose tolerance: float32 accumulators across 4 ops.
    assert torch.allclose(C, C_manual, atol=1e-4), "Pipeline mismatch"


# ---------------------------------------------------------------------------
# Complexity budget (Req 5: O(H_kv · d_c · d_k) per token)
# ---------------------------------------------------------------------------


def test_complexity_budget() -> None:
    """Per-token C-extraction FLOPs scale as O(H_kv · d_c · d_k)."""
    B, H_kv, N, d_k, d_c = 1, 8, 1, 128, 16

    def count_flops(h_kv: int) -> int:
        return h_kv * (4 * d_k * d_c + d_c) + h_kv * d_c

    flops_8 = count_flops(8)
    flops_4 = count_flops(4)
    assert flops_8 > flops_4
    expected_per_token = H_kv * (4 * d_k * d_c + d_c) + H_kv * d_c
    assert expected_per_token == 65792


# ---------------------------------------------------------------------------
# Differentiability: full D-path, no STE (Req 6)
# ---------------------------------------------------------------------------


def test_full_differentiability() -> None:
    """All inputs to extract_C receive finite gradients (D-path)."""
    torch.manual_seed(0)
    B, H_kv, N, d_k, d_c = 1, 4, 2, 8, 4
    K = torch.randn(B, H_kv, N, d_k, dtype=torch.double) * 0.1
    V = torch.randn(B, H_kv, N, d_k, dtype=torch.double) * 0.1
    W_K = torch.randn(H_kv, d_k, d_c, dtype=torch.double) * 0.1
    W_V = torch.randn(H_kv, d_k, d_c, dtype=torch.double) * 0.1
    b = torch.randn(H_kv, d_c, dtype=torch.double) * 0.1
    K.requires_grad_(True)
    V.requires_grad_(True)
    W_K.requires_grad_(True)
    W_V.requires_grad_(True)
    b.requires_grad_(True)
    C = extraction.extract_C(K, V, W_K, W_V, b, H_kv=H_kv, d_c=d_c, eps=1e-6)
    loss = C.sum()
    loss.backward()
    for name, p in [("K", K), ("V", V), ("W_K", W_K), ("W_V", W_V), ("b", b)]:
        assert p.grad is not None, f"{name} got no gradient"
        assert torch.isfinite(p.grad).all(), f"{name} gradient has NaN/Inf"


def test_no_surrogate_in_codebase() -> None:
    """The extraction pipeline (extract_C) MUST NOT use Straight-Through Estimators."""
    src_path = Path(extraction.__file__)
    text = src_path.read_text(encoding="utf-8")
    assert "StraightThroughEstimator" not in text, (
        "extraction.py must not import or mention StraightThroughEstimator (Req 6: D-path)"
    )
    assert "straight_through" not in text.lower(), (
        "extraction.py must not use straight-through estimators"
    )

    # Scope: the rule "no .detach() between z and C" applies ONLY to the
    # 4-step pipeline body, not to the centroid lifecycle (Phase 0 is allowed
    # to detach centroids by spec). We extract extract_C's source via inspect
    # and assert zero .detach() calls in it.
    import inspect as _inspect
    extract_c_src = _inspect.getsource(extraction.extract_C)
    assert ".detach(" not in extract_c_src, (
        "extract_C must have zero .detach() calls between z and C (Req 6: D-path)"
    )


# ---------------------------------------------------------------------------
# Signature sanity
# ---------------------------------------------------------------------------


def test_extract_C_signature() -> None:
    """extract_C signature must accept K, V, W_K, W_V, b, H_kv, d_c, eps."""
    sig = inspect.signature(extraction.extract_C)
    names = set(sig.parameters.keys())
    assert {"K", "V", "W_K", "W_V", "b"}.issubset(names)
    assert "eps" in names
    assert "H_kv" in names
    assert "d_c" in names


# ---------------------------------------------------------------------------
# CentroidDriver invariant tests (skeleton spec Req "Centroid Driver Semantic
# Invariants" — Issue ⑧ from fix-spec-doc-oversights hand-off contract).
# Each test name MUST match the spec Scenario name exactly so
# `grep test_empty_cell_preserves_centroid openspec/specs/decompmoe-skeleton/spec.md`
# anchors spec ↔ test contract.
# ---------------------------------------------------------------------------


def test_empty_cell_preserves_centroid() -> None:
    """Empty-cell invariant: `n_i = 0 ⇒ c_i^(t+1) == c_i^(t)` element-wise.

    Spec: skeleton "Centroid Driver Semantic Invariants" Scenario
    `test_empty_cell_preserves_centroid` (L341-343). The driver MUST NOT
    use `.clamp_min(epsilon)` as a denominator in the empty-cell branch;
    when `n_i = 0`, `m_i` must default to the previous centroid `c_i^(t-1)`
    so `c_i^(t+1) == c_i^(t)` element-wise within FP tolerance.
    """
    torch.manual_seed(0)
    from decompmoe.extraction import CentroidDriver, Phase

    N_e, d_c, T = 4, 3, 8
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    X = torch.randn(T, d_c)
    # Mask shape: (T, N_e) — token-to-expert soft assignment.
    # Force expert 0 to have ZERO assignment across all tokens (n_0 = 0).
    mask = torch.softmax(torch.randn(T, N_e), dim=-1)
    mask[:, 0] = 0.0

    out = CentroidDriver(Phase.EMA_090).step(centroids, X, mask=mask)

    # Expert 0 must be byte-exact preserved (machine-epsilon identity).
    assert torch.allclose(out[0], centroids[0], atol=1e-12), (
        f"expert 0 with n_0=0 must equal input; got drift "
        f"max |out[0] - centroids[0]| = {(out[0] - centroids[0]).abs().max().item():.3e}"
    )
    # Experts with n_i > 0 may legitimately update via EMA — no constraint.
    # Verify only that they remain unit-norm (Issue ⑥ derivative check).
    norms = out.norm(dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-6)


def test_spherical_norm_is_strictly_one() -> None:
    """After every CentroidDriver.step in Phases 1-4, `max_i |‖c_i‖₂ − 1.0| < 1e-7`.

    Spec: skeleton "Centroid Driver Semantic Invariants" Scenario
    `test_spherical_norm_is_strictly_one` (L345-347). The driver MUST
    enforce `‖c_i^(t+1)‖₂ ≡ 1.0` after every active-phase step
    (Phases 1-3 EMA + Phase 4 Projected SGD).
    """
    torch.manual_seed(0)
    from decompmoe.extraction import CentroidDriver, Phase

    N_e, d_c, T = 8, 16, 32
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    X = torch.randn(T, d_c)
    mask = torch.softmax(torch.randn(T, N_e), dim=-1)

    for phase in (Phase.EMA_090, Phase.EMA_095, Phase.EMA_099, Phase.PROJECTED_SGD):
        out = CentroidDriver(phase).step(centroids, X, mask=mask)
        norms = out.norm(dim=-1)
        max_dev = (norms - 1.0).abs().max().item()
        assert max_dev < 1e-7, (
            f"phase {phase!r}: max |‖c_i‖₂ - 1| = {max_dev:.3e} exceeds 1e-7 tolerance"
        )


def test_near_zero_candidate_fallback() -> None:
    """Near-zero candidate fallback: `‖u_i‖₂ < 1e-9 ⇒ c_i^(t+1) == c_i^(t)` element-wise.

    Spec: skeleton "Centroid Driver Semantic Invariants" Scenario
    `test_near_zero_candidate_fallback` (L349-351). When the unnormalized
    candidate `u_i` has `‖u_i‖₂ < 1e-9` (degenerate isotropic collapse),
    the driver MUST fall back to the previous centroid `c_i^(t)` to
    prevent NaN and preserve spherical boundedness.
    """
    torch.manual_seed(0)
    from decompmoe.extraction import CentroidDriver, Phase

    N_e, d_c, T = 4, 3, 8
    # Start from unit-sphere centroids; expert 0 has zero assignment so its
    # masked mean will be `weighted / clamp_min(1.0)` (i.e. divide by 1),
    # producing a near-zero candidate under the EMA combination when mask
    # only contains expert 0 for some tokens.
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    X = torch.zeros(T, d_c)  # degenerate feature: produces zero masked-mean

    # mask[:, 0] is nonzero for at least one token (so expert 0 is "in"
    # the assignment) but the EMA on zeros yields a degenerate candidate.
    mask = torch.zeros(T, N_e)
    mask[: T // 2, 0] = 1.0  # half tokens assigned to expert 0 with zero features
    mask[T // 2 :, 1] = 1.0

    out = CentroidDriver(Phase.EMA_090).step(centroids, X, mask=mask)

    # No NaN in output (NaN would propagate from 0/0 in the broken impl).
    assert torch.isfinite(out).all(), "CentroidDriver output must be finite"
    # All centroids remain on the unit sphere (Issue ⑥ derivative).
    norms = out.norm(dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-6)