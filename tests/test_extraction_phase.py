"""Tests for `decompmoe.extraction.CentroidDriver` and `Phase` enum.

ST-05 / Req 6 — 4-phase centroid lifecycle driver.
"""
from __future__ import annotations

import torch

from decompmoe.extraction import CentroidDriver, Phase


def _one_hot_mask(n_tokens: int, n_experts: int) -> torch.Tensor:
    """Deterministic `(T, N_e)` one-hot soft assignment: token `t` -> expert `t % N_e`.

    AC-17: `mask` is a required positional argument (spec skeleton req-18), so
    every test below supplies one. The one-hot form is deliberate -- it lets
    each assertion derive the expected `m_i` by plain boolean indexing
    (`X[mask[:, e] > 0].mean(dim=0)`), which shares no code path with the
    driver's `(mask.T @ X) / n_i` weighted sum and so is a real check rather
    than a restatement.
    """
    idx = torch.arange(n_tokens) % n_experts
    mask = torch.zeros(n_tokens, n_experts)
    mask[torch.arange(n_tokens), idx] = 1.0
    return mask



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
    out = CentroidDriver(Phase.SEEDING).step(
        centroids, X, _one_hot_mask(X.shape[0], centroids.shape[0])
    )
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
    N_e = centroids.shape[0]
    mask = _one_hot_mask(X.shape[0], N_e)
    out = CentroidDriver(Phase.EMA_090).step(centroids, X, mask)
    # AC-17: m_i is the per-expert masked mean, derived here by boolean
    # indexing. The pre-A-3 expectation used `X.mean(dim=0)` broadcast to
    # every centroid -- the exact substitution req-18 forbids.
    m = torch.stack([X[mask[:, e] > 0].mean(dim=0) for e in range(N_e)])
    expected = torch.nn.functional.normalize(0.90 * centroids + 0.10 * m, dim=-1)
    assert torch.allclose(out, expected, atol=1e-5), (
        f"actual max abs delta = {(out - expected).abs().max().item()!r}"
    )
    assert not torch.allclose(out[0], out[1], atol=1e-6), (
        f"actual=EMA output collapsed to a single point (territory collapse); "
        f"max|out[0]-out[1]| = "
        f"{(out[0] - out[1]).abs().max().item()!r}"
    )
    norms = out.norm(dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-6), (
        f"actual=norms {norms.tolist()!r} (req-18 Invariant 2 wants all 1.0)"
    )


def test_dense_mask_makes_the_weighting_and_division_load_bearing() -> None:
    """A DENSE mask with unequal column totals exercises both parts of `m_i`.

    The one-hot fixture elsewhere makes `m_i` a plain subset mean, so a driver
    that mishandled the weights could still agree. Here the rows are normalised
    to sum to 1 (each token spreads its weight across experts) and the column
    totals are deliberately unequal, so (a) the weighted sum and (b) the
    division by `n_i` are both load-bearing.
    """
    torch.manual_seed(0)
    centroids = torch.randn(4, 8)
    X = torch.randn(30, 8)
    N_e = centroids.shape[0]
    # Every entry >= 1 so every column total `n_i` exceeds 1, which makes the
    # driver's `n_i.clamp_min(1.0)` guard a no-op and the expectation the plain
    # masked mean. (With `n_i` below 1 the clamp silently changes the result;
    # that behaviour is a separate question from the axis/weighting semantics
    # this test is about.)
    mask = torch.rand(30, N_e) + 1.0
    col_totals = mask.sum(dim=0)
    assert bool((col_totals > 1.0).all()), (
        f"actual=n_i must all exceed 1 for this fixture; got {col_totals.tolist()}"
    )
    assert not torch.allclose(
        col_totals, col_totals[0].expand_as(col_totals), atol=1e-6
    ), "actual=column totals are equal; the division by n_i is not load-bearing"

    out = CentroidDriver(Phase.EMA_090).step(centroids, X, mask)
    # m_i = sum_t mask[t, i] * X[t] / sum_t mask[t, i] -- the spec's formula,
    # evaluated with an explicit loop rather than the driver's matmul.
    m = torch.stack([
        (mask[:, e].unsqueeze(-1) * X).sum(dim=0) / mask[:, e].sum()
        for e in range(N_e)
    ])
    expected = torch.nn.functional.normalize(0.90 * centroids + 0.10 * m, dim=-1)
    assert torch.allclose(out, expected, atol=1e-5), (
        f"actual max abs delta = {(out - expected).abs().max().item()!r}"
    )
    # Skipping the division would give a different answer.
    undivided = mask.t() @ X
    assert not torch.allclose(m, undivided, atol=1e-6), (
        f"actual=the n_i division is not load-bearing for this fixture "
        f"(max|diff| = {(m - undivided).abs().max().item()!r})"
    )


def test_square_mask_detects_a_swapped_expert_axis() -> None:
    """With `T == N_e` a driver that swapped the mask axes would give a number.

    For a rectangular mask a swapped-axis driver raises a shape error, so the
    bug can only hide in the square case -- which is exactly the case this
    fixture covers. `m` reads `mask[:, e]` (experts on axis 1, per the spec's
    `(T, N_e)`); the swapped reading takes `mask[e, :]` (experts on axis 0).
    """
    torch.manual_seed(0)
    N_e, d_c, T = 4, 8, 4
    centroids = torch.randn(N_e, d_c)
    X = torch.randn(T, d_c)
    mask = torch.rand(T, N_e) + 1.0   # every n_i exceeds 1 -> clamp_min is a no-op
    assert bool((mask.sum(dim=0) > 1.0).all()), (
        f"actual=n_i={mask.sum(dim=0).tolist()} must all exceed 1 for this fixture"
    )

    out = CentroidDriver(Phase.EMA_090).step(centroids, X, mask)
    m = (mask.t() @ X) / mask.sum(dim=0).unsqueeze(-1)         # experts on axis 1
    m_swapped = (mask @ X) / mask.sum(dim=1).unsqueeze(-1)    # experts on axis 0
    assert not torch.allclose(m, m_swapped, atol=1e-6), (
        f"actual=the two axis readings coincide "
        f"(max|diff| = {(m - m_swapped).abs().max().item()!r}); "
        f"this fixture cannot distinguish them"
    )
    expected = torch.nn.functional.normalize(0.90 * centroids + 0.10 * m, dim=-1)
    expected_swapped = torch.nn.functional.normalize(
        0.90 * centroids + 0.10 * m_swapped, dim=-1
    )
    assert torch.allclose(out, expected, atol=1e-5), (
        f"actual max abs delta = {(out - expected).abs().max().item()!r} "
        f"(expert axis is axis 1 per the spec's (T, N_e) layout)"
    )
    assert not torch.allclose(out, expected_swapped, atol=1e-5), (
        f"actual=the driver agrees with the SWAPPED expert axis; "
        f"max|diff| = {(out - expected_swapped).abs().max().item()!r}"
    )


def test_empty_cell_falls_back_to_the_previous_centroid() -> None:
    """req-18 Invariant 1: when `n_i = 0`, `m_i` MUST be the previous `c_i^(t-1)`.

    A zero column would otherwise make the weighted sum `0/0`; the driver
    guards the division with `clamp_min(1.0)` and then selects via
    `torch.where`, so the fallback must be visible as "this expert did not
    move" rather than "this expert collapsed to zero".
    """
    torch.manual_seed(0)
    N_e, d_c = 4, 8
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    X = torch.randn(20, d_c)
    mask = torch.zeros(20, N_e)
    mask[:, 0] = 1.0                      # only expert 0 receives any token
    assert int(mask.sum(dim=0).max()) == 20, "actual=test fixture precondition"
    empty = [e for e in range(N_e) if float(mask[:, e].sum()) == 0.0]
    assert empty == [1, 2, 3], f"actual=expected experts 1,2,3 empty, got {empty}"

    out = CentroidDriver(Phase.EMA_090).step(centroids, X, mask)
    for e in empty:
        assert torch.allclose(out[e], centroids[e], atol=1e-6), (
            f"actual=expert {e} moved despite n_i = 0; "
            f"max|out - prev| = {(out[e] - centroids[e]).abs().max().item()!r} "
            f"(req-18 Invariant 1 requires the previous centroid)"
        )
    # expert 0 DID receive tokens, so it must have moved
    assert not torch.allclose(out[0], centroids[0], atol=1e-6), (
        "actual=expert 0 did not move despite receiving every token"
    )


def test_phase_095_to_099_ema_coefficients() -> None:
    """Phase 2 (α=0.95) and Phase 3 (α=0.99) apply distinct smoothing + re-project."""
    torch.manual_seed(0)
    centroids = torch.randn(4, 8)
    X = torch.randn(100, 8)
    N_e = centroids.shape[0]
    mask = _one_hot_mask(X.shape[0], N_e)
    out_095 = CentroidDriver(Phase.EMA_095).step(centroids, X, mask)
    out_099 = CentroidDriver(Phase.EMA_099).step(centroids, X, mask)
    m = torch.stack([X[mask[:, e] > 0].mean(dim=0) for e in range(N_e)])
    expected_095 = torch.nn.functional.normalize(0.95 * centroids + 0.05 * m, dim=-1)
    expected_099 = torch.nn.functional.normalize(0.99 * centroids + 0.01 * m, dim=-1)
    assert torch.allclose(out_095, expected_095, atol=1e-5)
    assert torch.allclose(out_099, expected_099, atol=1e-5)
    assert torch.allclose(out_095.norm(dim=-1), torch.ones(4), atol=1e-6)
    assert torch.allclose(out_099.norm(dim=-1), torch.ones(4), atol=1e-6)


def test_phase_4_projected_sgd() -> None:
    """Phase 4 retracts centroids to the unit sphere."""
    torch.manual_seed(0)
    centroids = torch.randn(4, 8) * 5.0
    out = CentroidDriver(Phase.PROJECTED_SGD).step(
        centroids, torch.zeros(1, 8), _one_hot_mask(1, centroids.shape[0])
    )
    norms = out.norm(dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5), (
        f"Phase 4 must produce unit-norm centroids; got norms {norms}"
    )


def test_phase_transition_swaps_rule() -> None:
    """Transitioning from EMA_090 to EMA_099 changes the α value, not the math."""
    torch.manual_seed(0)
    centroids = torch.randn(4, 8)
    X = torch.randn(50, 8)
    N_e = centroids.shape[0]
    mask = _one_hot_mask(X.shape[0], N_e)
    m = torch.stack([X[mask[:, e] > 0].mean(dim=0) for e in range(N_e)])
    out_090 = CentroidDriver(Phase.EMA_090).step(centroids, X, mask)
    out_099 = CentroidDriver(Phase.EMA_099).step(centroids, X, mask)
    assert not torch.allclose(out_090, out_099)
    expected_090 = torch.nn.functional.normalize(0.90 * centroids + 0.10 * m, dim=-1)
    expected_099 = torch.nn.functional.normalize(0.99 * centroids + 0.01 * m, dim=-1)
    assert torch.allclose(out_090, expected_090, atol=1e-5)
    assert torch.allclose(out_099, expected_099, atol=1e-5)


def test_dead_expert_protection_signature() -> None:
    """`CentroidDriver` and `Phase` are the canonical API surface for ST-05."""
    import decompmoe.extraction as ext_module
    assert hasattr(ext_module, "CentroidDriver")
    assert hasattr(ext_module, "Phase")