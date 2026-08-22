"""Tests for `decompmoe.extraction.CentroidDriver` and `Phase` enum.

ST-05 / Req 6 — 4-phase centroid lifecycle driver.
"""
from __future__ import annotations

import torch

from decompmoe.extraction import CentroidDriver, Phase


def test_phase_enum_integers() -> None:
    """Phase enum integer codes must match spec (A3-2)."""
    assert int(Phase.SEEDING) == 0
    assert int(Phase.EMA_090) == 1
    assert int(Phase.EMA_095) == 2
    assert int(Phase.EMA_099) == 3
    assert int(Phase.PROJECTED_SGD) == 4


def test_phase_seeding_no_grad() -> None:
    """Phase 0 (SEEDING) must NOT register gradient on centroids."""
    centroids = torch.nn.Parameter(torch.randn(16, 16))
    X = torch.randn(64, 16)
    out = CentroidDriver(Phase.SEEDING).step(centroids, X)
    # SEEDING returns a detached tensor — no grad_fn, no requires_grad
    assert not out.requires_grad, "SEEDING output must not require grad"
    assert out.grad_fn is None, "SEEDING output must have no grad_fn"
    # And consequently: no gradient can flow back into centroids
    assert centroids.grad is None, "SEEDING must not propagate gradient into centroids"


def test_phase_090_ema() -> None:
    """Phase 1 (EMA_090): `c_i^(t+1) = Normalize(0.90·c_i + 0.10·m_i) / ‖·‖₂`.

    Spec: skeleton "Centroid Four-Phase Lifecycle Driver" Phase 1 + Invariant 2
    (spherical re-projection). Without F.normalize after EMA combination,
    ``‖c_i‖₂`` drifts from 1.0 and breaks ``logit ∈ [−2β, 0]`` boundedness.
    """
    torch.manual_seed(0)
    centroids = torch.randn(4, 8)
    X = torch.randn(100, 8)
    out = CentroidDriver(Phase.EMA_090).step(centroids, X)
    expected = torch.nn.functional.normalize(
        0.90 * centroids + 0.10 * X.mean(dim=0).unsqueeze(0).expand_as(centroids),
        dim=-1,
    )
    assert torch.allclose(out, expected, atol=1e-5)
    norms = out.norm(dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-6)


def test_phase_095_to_099_ema_coefficients() -> None:
    """Phase 2 (α=0.95) and Phase 3 (α=0.99) apply distinct smoothing + re-project."""
    torch.manual_seed(0)
    centroids = torch.randn(4, 8)
    X = torch.randn(100, 8)
    out_095 = CentroidDriver(Phase.EMA_095).step(centroids, X)
    out_099 = CentroidDriver(Phase.EMA_099).step(centroids, X)
    expected_095 = torch.nn.functional.normalize(
        0.95 * centroids + 0.05 * X.mean(dim=0).unsqueeze(0).expand_as(centroids),
        dim=-1,
    )
    expected_099 = torch.nn.functional.normalize(
        0.99 * centroids + 0.01 * X.mean(dim=0).unsqueeze(0).expand_as(centroids),
        dim=-1,
    )
    assert torch.allclose(out_095, expected_095, atol=1e-5)
    assert torch.allclose(out_099, expected_099, atol=1e-5)
    assert torch.allclose(out_095.norm(dim=-1), torch.ones(4), atol=1e-6)
    assert torch.allclose(out_099.norm(dim=-1), torch.ones(4), atol=1e-6)


def test_phase_4_projected_sgd() -> None:
    """Phase 4 retracts centroids to the unit sphere."""
    torch.manual_seed(0)
    centroids = torch.randn(4, 8) * 5.0
    out = CentroidDriver(Phase.PROJECTED_SGD).step(centroids, torch.zeros(1, 8))
    norms = out.norm(dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5), (
        f"Phase 4 must produce unit-norm centroids; got norms {norms}"
    )


def test_phase_transition_swaps_rule() -> None:
    """Transitioning from EMA_090 to EMA_099 changes the α value, not the math."""
    torch.manual_seed(0)
    centroids = torch.randn(4, 8)
    X = torch.randn(50, 8)
    mean = X.mean(dim=0).unsqueeze(0).expand_as(centroids)
    out_090 = CentroidDriver(Phase.EMA_090).step(centroids, X)
    out_099 = CentroidDriver(Phase.EMA_099).step(centroids, X)
    assert not torch.allclose(out_090, out_099)
    expected_090 = torch.nn.functional.normalize(0.90 * centroids + 0.10 * mean, dim=-1)
    expected_099 = torch.nn.functional.normalize(0.99 * centroids + 0.01 * mean, dim=-1)
    assert torch.allclose(out_090, expected_090, atol=1e-5)
    assert torch.allclose(out_099, expected_099, atol=1e-5)


def test_dead_expert_protection_signature() -> None:
    """`CentroidDriver` and `Phase` are the canonical API surface for ST-05."""
    import decompmoe.extraction as ext_module
    assert hasattr(ext_module, "CentroidDriver")
    assert hasattr(ext_module, "Phase")