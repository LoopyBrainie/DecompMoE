"""Tests for `decompmoe.metrics`: 8 metrics + REALTIME/OFFLINE classification.

ST-12 / Req 19, 20.
"""

from __future__ import annotations

import math

import pytest
import torch

from decompmoe import loss as loss_mod
from decompmoe import metrics


def test_sep_formula_matches_loss() -> None:
    """metrics.L_sep(c) ≡ loss.compute_L_sep(c) under the same input."""
    torch.manual_seed(0)
    c = torch.nn.functional.normalize(torch.randn(16, 16), dim=-1)
    L_metrics = metrics.L_sep(c)
    L_loss = loss_mod.compute_L_sep(c)
    assert abs(L_metrics.item() - L_loss.item()) < 1e-6


def test_R_H_partition_of_unity_input() -> None:
    """R_H(p) lies in [0, 1] for any probability vector p."""
    torch.manual_seed(0)
    for N_e in (4, 16, 64):
        p = torch.softmax(torch.randn(N_e), dim=-1)
        r = metrics.R_H(p)
        assert 0.0 <= r.item() <= 1.0, f"R_H out of [0,1]: {r.item()}"


def test_S_load_closed_form_mvp() -> None:
    """S_load(f) = N_e · max_i f_i (wayfinder Req 20 closed form).

    Spec: S_load is `N_e · max_i f_i`, ranging from 1 at perfect
    uniformity to N_e at full collapse. The previous implementation
    used `‖f − 1/N‖₂` which violated the spec closed form.
    """
    N_e = 16
    # Uniform → S_load = 16 · (1/16) = 1.0
    f_uniform = torch.full((N_e,), 1.0 / N_e)
    assert abs(metrics.S_load(f_uniform).item() - 1.0) < 1e-6, (
        f"S_load(uniform) = {metrics.S_load(f_uniform).item()}, expected 1.0"
    )
    # Collapse (half on expert 0, half on expert 1) → S_load = 16 · 0.5 = 8.0
    f_collapsed = torch.zeros(N_e)
    f_collapsed[0] = 0.5
    f_collapsed[1] = 0.5
    assert abs(metrics.S_load(f_collapsed).item() - 8.0) < 1e-6, (
        f"S_load(half-collapse) = {metrics.S_load(f_collapsed).item()}, expected 8.0"
    )
    # Full collapse → S_load = 16 · 1 = 16.0
    f_full = torch.zeros(N_e)
    f_full[0] = 1.0
    assert abs(metrics.S_load(f_full).item() - 16.0) < 1e-6


def test_four_realtime_four_offline_classification() -> None:
    """REALTIME ∪ OFFLINE == 8 metric names; REALTIME has 4, OFFLINE has 4."""
    assert len(metrics.REALTIME) == 4
    assert len(metrics.OFFLINE) == 4
    assert {"L_sep", "R_H", "S_load", "UR"} == metrics.REALTIME
    assert frozenset({"SP", "D_chord", "MCI", "CG"}) == metrics.OFFLINE
    assert {
        "L_sep",
        "R_H",
        "S_load",
        "UR",
        "SP",
        "D_chord",
        "MCI",
        "CG",
    } == metrics.REALTIME | metrics.OFFLINE


def test_active_flops_parity_per_arch() -> None:
    """flops_per_token(MOE) == flops_per_token(DENSE)."""
    from decompmoe.config import MVPConfig

    cfg = MVPConfig()
    moe = metrics.flops_per_token(cfg, arch="MOE")
    dense = metrics.flops_per_token(cfg, arch="DENSE")
    assert moe == dense


# ---------------------------------------------------------------------------
# Task 3.4 — offline closed forms (wayfinder ADDED Requirements)
# ---------------------------------------------------------------------------


def test_offline_uses_d_chord_name() -> None:
    """OFFLINE frozenset uses `D_chord` (renamed from D_c)."""
    assert frozenset({"SP", "D_chord", "MCI", "CG"}) == metrics.OFFLINE


def test_mci_uniform_token_distribution() -> None:
    """Uniform token distribution (each e_j repeated k times) → MCI == 1.0.

    Spec: wayfinder ADDED "MCI closed-form on uniform token distribution",
    abs=1e-12. Input is token signatures, uncentered second moment.
    """
    d_c, k = 16, 2
    T = torch.stack([torch.eye(d_c)[j] for j in range(d_c) for _ in range(k)])
    assert metrics.MCI(T).item() == pytest.approx(1.0, abs=1e-12)


def test_mci_rank1_token_distribution() -> None:
    """Rank-1 tokens (all C_t = e_1) → MCI == 1/d_c exactly.

    Spec: wayfinder ADDED "MCI closed-form on rank-1 token distribution".
    """
    d_c = 16
    T = torch.zeros(32, d_c)
    T[:, 0] = 1.0
    assert metrics.MCI(T).item() == pytest.approx(1.0 / d_c, abs=1e-12)


def test_mci_range_bound() -> None:
    """MCI ∈ [1/d_c, 1] for random token signatures."""
    torch.manual_seed(0)
    d_c = 16
    T = torch.nn.functional.normalize(torch.randn(256, d_c), dim=-1)
    mci = metrics.MCI(T).item()
    assert 1.0 / d_c - 1e-6 <= mci <= 1.0 + 1e-6


def test_cg_zero_gradient_invariance() -> None:
    """CG(zero_grad) == 0.0 exact within abs=1e-12."""
    g = torch.zeros(16)
    assert metrics.CG(g).item() == pytest.approx(0.0, abs=1e-12)


def test_cg_positive_homogeneity() -> None:
    """|CG(2g) − 2·CG(g)| < 1e-6."""
    torch.manual_seed(0)
    g = torch.randn(16)
    diff = abs(metrics.CG(2 * g).item() - 2 * metrics.CG(g).item())
    assert diff < 1e-6


def test_cg_l2_norm_closed_form() -> None:
    """CG(g) = ‖g‖₂ per spec Req 20 L394 — closed-form numerical verification.

    Audit finding CRIT-3: previous implementation `mean pairwise |g_i − g_j|`
    failed this closed-form test. Known-vector inputs verify L2 directly:
    - CG([3, 4]) == 5.0 (Pythagorean)
    - CG([1, 2, 3]) == √14 ≈ 3.7417
    - CG(zeros) == 0.0 (zero-gradient invariant)
    """
    import math

    g_2d = torch.tensor([3.0, 4.0])
    assert metrics.CG(g_2d).item() == pytest.approx(5.0, abs=1e-6)

    g_3d = torch.tensor([1.0, 2.0, 3.0])
    assert metrics.CG(g_3d).item() == pytest.approx(math.sqrt(14.0), abs=1e-6)

    g_zero = torch.zeros(8)
    assert metrics.CG(g_zero).item() == pytest.approx(0.0, abs=1e-12)

    torch.manual_seed(0)
    g_rand = torch.randn(16)
    assert metrics.CG(g_rand).item() == pytest.approx(
        torch.linalg.norm(g_rand).item(), abs=1e-6
    )


def test_sp_orthonormal_aligned_inputs() -> None:
    """C_t == c_{a(t)} for all t → SP == 1.0 within abs=1e-6."""
    N_e, d_c, T = 4, 8, 40
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    assign = torch.randint(0, N_e, (T,))
    C = centroids[assign]
    sp = metrics.SP(
        centroids, assign, C
    )  # spec: SP(centroids, assignments, signatures)
    assert sp.item() == pytest.approx(1.0, abs=1e-6)


def test_sp_60_degree_offset() -> None:
    """c_i^T C_t == cos 60° = 0.5 → SP == 0.5 within abs=1e-6."""
    d_c, T = 8, 10
    c0 = torch.nn.functional.normalize(torch.randn(d_c), dim=-1)
    # Rotate c0 by 60° in the plane spanned by c0 and an orthogonal vector u.
    r = torch.randn(d_c)
    u = torch.nn.functional.normalize(r - (r @ c0) * c0, dim=-1)
    C_t = math.cos(math.pi / 3) * c0 + math.sin(math.pi / 3) * u
    assignments = torch.zeros(T, dtype=torch.long)
    # One expert only; SP averages per-token alignment with assigned centroid.
    sp = metrics.SP(c0.unsqueeze(0), assignments, C_t.expand(T, d_c).contiguous())
    assert sp.item() == pytest.approx(0.5, abs=1e-6)


def test_sp_skips_empty_experts() -> None:
    """SP averages over non-empty experts only (‖T_i‖₁ > 0), not zeros."""
    N_e, d_c, T = 4, 8, 20
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    assign = torch.zeros(T, dtype=torch.long)  # experts 1..3 empty
    C = centroids[assign]  # perfectly aligned → SP == 1.0, not diluted by empties
    sp = metrics.SP(centroids, assign, C)
    assert sp.item() == pytest.approx(1.0, abs=1e-6)


def test_sp_range_containment() -> None:
    """−1 − 1e-6 ≤ SP ≤ 1 + 1e-6 (containment, NOT point equality)."""
    torch.manual_seed(0)
    N_e, d_c, T = 4, 8, 50
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    assign = torch.randint(0, N_e, (T,))
    C = torch.nn.functional.normalize(torch.randn(T, d_c), dim=-1)
    sp = metrics.SP(centroids, assign, C).item()
    assert -1.0 - 1e-6 <= sp <= 1.0 + 1e-6


def test_d_chord_orthonormal_basis() -> None:
    """D_chord over an orthonormal basis == √2 exact within abs=1e-6."""
    d_c = 16
    B = torch.eye(d_c)
    val = metrics.D_chord(B).item()
    assert val == pytest.approx(math.sqrt(2.0), abs=1e-6)


def test_d_chord_versine_relationship() -> None:
    """D_chord(c_i, c_j) = √(2·versine θ) with versine θ = 1 − cos θ holds."""
    torch.manual_seed(0)
    a = torch.nn.functional.normalize(torch.randn(16), dim=-1)
    b = torch.nn.functional.normalize(torch.randn(16), dim=-1)
    expected = math.sqrt(2.0 * (1.0 - float(a @ b)))
    val2 = metrics.D_chord(torch.stack([a, b])).item()
    assert val2 == pytest.approx(expected, abs=1e-6)


def test_log_int_cache_matches_runtime_and_amortizes() -> None:
    """`_log_int(n)` cached value must equal runtime log(float(n)) (Pi finding M2).

    Spec: R_H divides by `log(N_e)` (frozen N_e=16 in MVP). The cache
    amortizes the per-call `torch.tensor(float(n))` allocation while
    preserving the closed-form value exactly. Verifies:
    1. `_log_int(16)` equals runtime `float(torch.log(torch.tensor(16.0)))`.
    2. Repeated `_log_int(16)` does NOT grow `_LOG_CACHE` (cache hit).
    3. `R_H` numerical output is unchanged after the optimization.
    """
    # 1. Closed-form match: cache value == runtime value
    runtime = float(torch.log(torch.tensor(16.0)))
    cached = metrics._log_int(16)
    assert cached == pytest.approx(runtime, abs=1e-12), (
        f"_log_int(16) = {cached} ≠ runtime {runtime}"
    )

    # 2. Cache hit: repeated call does not grow the cache
    size_before = len(metrics._LOG_CACHE)
    metrics._log_int(16)
    assert len(metrics._LOG_CACHE) == size_before, (
        "_log_int must hit cache on repeat (no growth)"
    )

    # 3. R_H numerical output unchanged after the optimization
    torch.manual_seed(0)
    p = torch.softmax(torch.randn(8, 16), dim=-1)
    r_h_optimized = metrics.R_H(p)
    p_safe = p.clamp_min(1e-12)
    expected = -(p_safe * p_safe.log()).sum(dim=-1) / runtime
    assert torch.allclose(r_h_optimized, expected, atol=1e-6), (
        f"R_H after cache optimization diverged from runtime: "
        f"{r_h_optimized} vs {expected}"
    )
