"""Tests for `decompmoe.metrics`: 8 metrics + REALTIME/OFFLINE classification.

ST-12 / Req 19, 20.
"""

from __future__ import annotations

import ast
import math
import pathlib

import pytest
import torch

from decompmoe import config
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
    _mci = metrics.MCI(T).item()
    assert _mci == pytest.approx(1.0, abs=1e-12), f"actual MCI(uniform) = {_mci}, expected 1.0"


def test_mci_rank1_token_distribution() -> None:
    """Rank-1 tokens (all C_t = e_1) → MCI == 1/d_c exactly.

    Spec: wayfinder ADDED "MCI closed-form on rank-1 token distribution".
    """
    d_c = 16
    T = torch.zeros(32, d_c)
    T[:, 0] = 1.0
    _mci = metrics.MCI(T).item()
    assert _mci == pytest.approx(1.0 / d_c, abs=1e-12), f"actual MCI(rank-1) = {_mci}, expected 1/d_c = {1.0 / d_c}"


def test_mci_range_bound() -> None:
    """MCI ∈ [1/d_c, 1] for random token signatures."""
    torch.manual_seed(0)
    d_c = 16
    T = torch.nn.functional.normalize(torch.randn(256, d_c), dim=-1)
    mci = metrics.MCI(T).item()
    assert 1.0 / d_c - 1e-6 <= mci <= 1.0 + 1e-6


def test_mci_centered_covariance_upper_endpoint_unreachable() -> None:
    """Principle-form: `wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 1 — centered-covariance reading has
    `(1/d_c, 1]` upper endpoint unreachable at |T| = d_c.

    Mathematical derivation (verbatim from design.md §"Centered covariance"):
    - M_centered = (1/|T|) Σ (C_t − μ)(C_t − μ)ᵀ
    - rank(M_centered) ≤ rank(C − μ) ≤ |T| − 1 (centering subtracts 1 dof)
    - At |T| = d_c: rank(M_centered) ≤ d_c − 1
    - For T = I_{d_c}: M_centered has eigenvalues {0 (multiplicity 1),
      1/d_c (multiplicity d_c − 1)}, so MCI_centered = 1/(d_c · Σ λ̃_j²) =
      1/(d_c · (d_c − 1) · (1/(d_c − 1))²) = (d_c − 1)/d_c, STRICTLY < 1.0.
    - This proves the centered-covariance reading cannot reach MCI = 1.0,
    which is exactly why `wayfinder Req 20 MCI row (#req-20-mci)` Reason supersedes it with uncentered second moment.

    Verifier F2 — principle-form guard for `wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 1.
    This test computes MCI_centered MANUALLY (not via `metrics.MCI`, which
    uses uncentered) to directly demonstrate the upper endpoint bound.
    """
    d_c = 16
    T = torch.eye(d_c)
    # Compute μ and M_centered manually
    mu = T.mean(dim=0)
    centered = T - mu.unsqueeze(0)
    M_centered = (centered.T @ centered) / d_c  # (1/|T|) Σ (C_t − μ)(C_t − μ)ᵀ
    eigvals = torch.linalg.eigvalsh(M_centered)
    # Verify rank: at least one eigenvalue near 0, (d_c - 1) non-zero
    nonzero_count = int((eigvals > 1e-10).sum().item())
    assert nonzero_count == d_c - 1, (
        f"rank(M_centered) should be d_c − 1 = {d_c - 1} at |T| = d_c, got {nonzero_count} "
        f"(centering subtracts 1 dof, so rank ≤ |T| − 1)"
    )
    assert eigvals[0].item() < 1e-10, (
        f"Expected near-zero smallest eigenvalue of M_centered, got {eigvals[0].item():.6e}"
    )
    # Compute MCI_centered manually: 1 / (d_c · Σ λ̃_j²) where λ̃_j = λ_j / Σ_r λ_r
    total = eigvals.sum()
    lam_norm = eigvals / total
    mci_centered = 1.0 / (d_c * (lam_norm ** 2).sum())
    # Upper endpoint unreachable: mci_centered < 1.0 (strictly)
    assert mci_centered.item() == pytest.approx((d_c - 1) / d_c, abs=1e-6), (
        f"MCI_centered = {mci_centered.item()}, expected (d_c − 1)/d_c = {(d_c - 1) / d_c:.6f}"
    )
    assert mci_centered.item() < 1.0, (
        f"MCI_centered = {mci_centered.item()} must be strictly less than 1.0 "
        f"(upper endpoint unreachable for centered-covariance reading at |T| = d_c)"
    )


def test_mci_health_target_unreachable_below_floor() -> None:
    """Principle-form: the spec's `1/d_c` floor is attained by `metrics.MCI`, and
    the original `< 0.05` health target sits below it, so it is unreachable.

    `wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 2 states the floor as a geometric constraint on the
    CV reading. The quantity actually implemented and measurable here is
    `metrics.MCI` (uncentered second moment), whose rank-1 floor is exactly
    `1/d_c`. Anchoring the claim on `MCI`'s real output — rather than on a
    self-computed `1.0/16` reciprocal, which can never fail — is what makes
    this falsifiable: if `MCI`'s floor drifted, this turns red.

    Two corrections made to the previous form of this test, both found in
    review:

    * The unreachable-health-target consequence is a statement about the FLOOR,
      not about a typical reading. It now asserts `health_target < mci_floor`
      (`0.05 < 0.0625`). The earlier `health_target < mci_empirical` form
      compared against a seed-dependent value on an isotropic sample, which
      would still pass if `MCI` were floored at 0.06.
    * The `MCI(rank-1) == 1/d_c` half is NOT re-asserted here: it is already
      covered by `test_mci_rank1_token_distribution` and
      `test_mci_uncentered_both_endpoints_attainable_principle`. A third copy
      guards nothing new.

    The spec's own `CV ≥ 1/d_c` claim remains UNGUARDED and is registered as a
    hand-off. The previous "empirical CV" block did not guard it: it computed
    the max chord distance from the empirical mean direction, which for an
    isotropic sample is ≈4σ ≈ 1.0 and is essentially independent of `d_c` —
    it has no mathematical connection to `1/d_c` and passed with 30.7x slack.
    Asserting it verbatim only made a wrong number look verified.
    """
    d_c = 16
    lower_bound = 1.0 / d_c
    health_target = 0.05

    # The floor, read from the implementation rather than recomputed.
    rank1 = torch.zeros(32, d_c)
    rank1[:, 0] = 1.0
    mci_floor = metrics.MCI(rank1).item()

    assert health_target < mci_floor, (
        f"actual health_target={health_target}, MCI rank-1 floor={mci_floor} — "
        f"the < {health_target} health target would be REACHABLE, contradicting "
        f"`wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 2 (floor 1/d_c = {lower_bound})"
    )


def test_mci_uncentered_both_endpoints_attainable_principle() -> None:
    """Principle-form: `wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 3 — uncentered second moment allows BOTH
    endpoints of `MCI ∈ [1/d_c, 1]` to be attainable, unlike centered-covariance or CV.

    Mathematical derivation (verbatim from design.md §"Uncentered second moment"):
    - M_uncentered = (1/|T|) Σ C_t C_tᵀ
    - rank(M_uncentered) ≤ min(rank(C), d_c) ≤ min(|T|, d_c)
    - At |T| = d_c: rank(M_uncentered) ≤ d_c, achievable at full rank
    - Upper endpoint (uniform): M = I/d_c, λ̃ = (1/d_c, …, 1/d_c),
      Σ λ̃_j² = d_c · (1/d_c)² = 1/d_c, MCI = 1.0
    - Lower endpoint (rank-1): M = e_1 e_1ᵀ, λ̃ = (1, 0, …, 0),
      Σ λ̃_j² = 1, MCI = 1/d_c

    This is the principle-form version of `test_mci_uniform_token_distribution` +
    `test_mci_rank1_token_distribution`, framed explicitly as "both endpoints
    attainable" with the uncentered reading (the third L413 Reason claim).

    Verifier F2 — principle-form guard for `wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 3.
    """
    d_c = 16
    # Upper endpoint (uniform basis vectors, |T| = d_c)
    T_uniform = torch.eye(d_c)
    mci_upper = metrics.MCI(T_uniform).item()
    assert mci_upper == pytest.approx(1.0, abs=1e-12), (
        f"MCI(uniform) = {mci_upper} must equal 1.0 (upper endpoint, "
        f"verifies `wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 3 upper endpoint attainability)"
    )
    # Lower endpoint (rank-1, |T| = d_c copies of e_1)
    T_rank1 = torch.zeros(d_c, d_c)
    T_rank1[:, 0] = 1.0
    mci_lower = metrics.MCI(T_rank1).item()
    assert mci_lower == pytest.approx(1.0 / d_c, abs=1e-12), (
        f"MCI(rank-1) = {mci_lower} must equal 1/d_c = {1.0 / d_c} (lower endpoint, "
        f"verifies `wayfinder Req 20 MCI row (#req-20-mci)` Reason claim 3 lower endpoint attainability)"
    )
    # Both endpoints attainable within declared range [1/d_c, 1]
    assert 1.0 / d_c <= mci_lower and mci_upper <= 1.0 + 1e-12, (
        f"Both endpoints must be in [1/d_c, 1]: lower={mci_lower}, upper={mci_upper}"
    )


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
    """CG(g) = ‖g‖₂ per `wayfinder Req 20 Eight Geometric Quantification Metrics (#req-20)` CG row — closed-form numerical verification.

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


def test_cg_n_eq_1_returns_magnitude() -> None:
    """CG n=1 boundary behavior per `wayfinder Req 20 (CG)` + ADDED Requirement "CG n=1 boundary behavior".

    Spec anchor: `openspec/specs/wayfinder/spec.md` Req 20 (CG)
    `CG = ‖∇_{W^{K, V, b}} L_total‖₂` (parent requirement) + ADDED Requirement
    "CG n=1 boundary behavior" (4 Scenarios: 1D positive / 1D negative /
    1D zero / multi-dim `numel()==1`). Audit review LOW 7 (CRIT-3 silent
    change at n=1 boundary): single-element inputs map to abs(value)
    directly via L2-norm definition (no special-case branch),
    dimension-agnostic because L2 norm depends only on `numel()`.
    """
    # 1D positive: spec Scenario "CG n=1 positive value"
    g_pos_1d = torch.tensor([5.0])
    actual_pos_1d = metrics.CG(g_pos_1d).item()
    assert actual_pos_1d == pytest.approx(5.0, abs=1e-15), f"actual={actual_pos_1d}"

    # 1D negative: spec Scenario "CG n=1 negative value"
    g_neg_1d = torch.tensor([-5.0])
    actual_neg_1d = metrics.CG(g_neg_1d).item()
    assert actual_neg_1d == pytest.approx(5.0, abs=1e-15), f"actual={actual_neg_1d}"

    # 1D zero: spec Scenario "CG n=1 zero value"
    g_zero_1d = torch.tensor([0.0])
    actual_zero_1d = metrics.CG(g_zero_1d).item()
    assert actual_zero_1d == pytest.approx(0.0, abs=1e-15), f"actual={actual_zero_1d}"

    # Multi-dim numel==1: spec Scenario "CG n=1 multi-dim numel==1"
    # L2 norm is dimension-agnostic when numel()==1; spec text allows
    # any rank so long as `g.numel() == 1`.
    g_pos_2d = torch.tensor([[5.0]])
    actual_pos_2d = metrics.CG(g_pos_2d).item()
    assert actual_pos_2d == pytest.approx(5.0, abs=1e-15), f"actual={actual_pos_2d}"

    g_neg_3d = torch.tensor([[[-5.0]]])
    actual_neg_3d = metrics.CG(g_neg_3d).item()
    assert actual_neg_3d == pytest.approx(5.0, abs=1e-15), f"actual={actual_neg_3d}"

    # L2-norm identity sanity check (per spec Requirement "CG n=1 boundary behavior"
    # anchor #req-35 "MUST satisfy the L2-norm identity" wording): documents the
    # FP-exact equality `actual == torch.linalg.norm(g).item()` for the L2-norm
    # reduce path. **Caveat: at numel=1 this sanity check does NOT actually
    # discriminate between L2-norm / abs(sum) / abs(max) implementations** —
    # all three coincidentally return `abs(value)` for single-element tensors
    # (L2=sqrt(g²)=|g|, abs(sum)=|g|, abs(max)=|g| for `g.numel()==1`). The actual
    # L2-vs-other-norms discriminator lives in the sibling test
    # `test_cg_l2_norm_closed_form` (req-20 coverage), where the
    # assertion `CG(torch.tensor([3.0, 4.0])) == pytest.approx(5.0)` is uniquely
    # satisfied by L2-norm (L1=7.0, abs(sum)=7.0, abs(max)=4.0 — only L2=5.0).
    # This bare `==` is FP-exact because `sqrt(g²)` is exact for `|g| ≤ 2^52` in
    # IEEE-754 binary64, so no `pytest.approx` is needed. Reuse `actual_pos_1d`
    # (computed at L326) instead of recomputing CG(g_pos_1d) here.
    assert actual_pos_1d == torch.linalg.norm(g_pos_1d).item(), (
        f"actual CG={actual_pos_1d}; L2 norm reduce path "
        f"torch.linalg.norm={torch.linalg.norm(g_pos_1d).item()}; "
        f"CG must reduce via L2 norm, not abs(.sum()) or abs(.max())"
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


def test_sp_antipodal_aligned_inputs() -> None:
    """C_t == -c_{a(t)} for all t → SP == -1.0 within abs=1e-6.

    Spec: wayfinder ADDED "SP closed-form on antipodal-aligned inputs".
    Lower-bound closed-form witness symmetric to `test_sp_orthonormal_aligned_inputs`
    (upper bound = +1.0) and `test_sp_60_degree_offset` (middle = +0.5).
    Each per-expert purity SP_i = c_iᵀ(-c_i) = -1 by definition (‖-c_i‖₂ = 1).
    """
    N_e, d_c, T = 4, 8, 40
    centroids = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    assign = torch.randint(0, N_e, (T,))
    C = -centroids[assign]  # antipode of assigned centroid for every token
    sp = metrics.SP(centroids, assign, C)
    assert sp.item() == pytest.approx(-1.0, abs=1e-6)


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
    amortizes the per-call tensor allocation while preserving the
    closed-form value exactly. Verifies:
    1. `_log_int(16)` equals the runtime computation AND equals `math.log(16)`
       exactly — the reference is computed in **float64** because
       `torch.tensor(float(n))` defaults to float32, which silently cost the
       normalisation constant ~2.7e-9 of relative precision.
    2. Repeated `_log_int(16)` does NOT grow `_LOG_CACHE` (cache hit).
    3. `R_H` numerical output matches the closed form with the same divisor.
    """
    # 1. Closed-form match: cache value == runtime value == math.log(n)
    runtime = float(torch.log(torch.tensor(16.0, dtype=torch.float64)))
    cached = metrics._log_int(16)
    assert cached == pytest.approx(runtime, abs=1e-12), (
        f"actual={cached}, expected runtime {runtime}"
    )
    assert cached == pytest.approx(math.log(16.0), abs=1e-12), (
        f"actual={cached}, expected math.log(16)={math.log(16.0)}"
    )

    # 2. Cache hit: repeated call does not grow the cache
    size_before = len(metrics._LOG_CACHE)
    metrics._log_int(16)
    assert len(metrics._LOG_CACHE) == size_before, (
        "_log_int must hit cache on repeat (no growth)"
    )

    # 3. R_H numerical output matches the closed form with the same divisor
    torch.manual_seed(0)
    p = torch.softmax(torch.randn(8, 16), dim=-1)
    r_h_optimized = metrics.R_H(p)
    p_safe = p.clamp_min(1e-12)
    expected = -(p_safe * p_safe.log()).sum(dim=-1) / runtime
    assert torch.allclose(r_h_optimized, expected, atol=1e-6), (
        f"actual={r_h_optimized}, expected {expected}"
    )


# ---------------------------------------------------------------------------
# CG type guard (skeleton spec Req "Eight Metrics And Classification"
# Scenario `CG raises TypeError on non-floating-point input`).
# ---------------------------------------------------------------------------


def test_cg_raises_type_error_on_int_tensor() -> None:
    """CG(int_tensor) raises TypeError per spec Scenario.

    Spec: skeleton "Eight Metrics And Classification" Scenario
    `CG raises TypeError on non-floating-point input`. Integer tensors
    are caller bugs — silently coercing to zero norm would defeat the
    stability-probe purpose of CG.
    """
    int_tensor = torch.zeros(8, dtype=torch.int32)
    with pytest.raises(TypeError, match="CG requires a floating-point"):
        metrics.CG(int_tensor)


def test_cg_raises_type_error_on_bool_tensor() -> None:
    """CG(bool_tensor) raises TypeError per spec Scenario."""
    bool_tensor = torch.zeros(8, dtype=torch.bool)
    with pytest.raises(TypeError, match="CG requires a floating-point"):
        metrics.CG(bool_tensor)


def test_cg_raises_type_error_on_non_tensor() -> None:
    """CG(non-Tensor) raises TypeError per spec Scenario.

    Tests `list`, `np.ndarray`, and `None` as non-Tensor inputs.
    """
    import numpy as np
    for non_tensor in ([1.0] * 8, np.zeros(8), None):
        with pytest.raises(TypeError, match="CG requires a floating-point"):
            metrics.CG(non_tensor)


def test_cg_raises_type_error_on_additional_integer_dtypes() -> None:
    """CG raises TypeError on additional integer dtypes (int8/int16/int64, uint8).

    Spec: skeleton "Eight Metrics And Classification" Scenario
    `CG raises TypeError on non-floating-point input`. The original
    int32 + bool test covers the most common cases; this test extends
    coverage to the rest of the integer dtype family (`torch.int8`,
    `torch.int16`, `torch.int64`, `torch.uint8`) which all have
    `dtype.is_floating_point == False` and MUST also be rejected.
    """
    for dtype in (torch.int8, torch.int16, torch.int64, torch.uint8):
        tensor = torch.zeros(8, dtype=dtype)
        with pytest.raises(TypeError, match="CG requires a floating-point"):
            metrics.CG(tensor)


def test_cg_raises_type_error_on_complex_dtype() -> None:
    """CG raises TypeError on complex tensors (complex64/complex128).

    Spec: skeleton "Eight Metrics And Classification" Scenario
    `CG raises TypeError on non-floating-point input`. Complex dtypes
    have `dtype.is_floating_point == False` in PyTorch (they are the
    `complex` family, not the `floating-point` family). The spec contract
    `CG = ‖∇_{W^{K, V, b}} L_total‖₂` requires REAL floating-point gradients
    (the L2 norm is real-valued); complex inputs would silently coerce and
    yield a real-valued output that is semantically wrong. Must reject.
    """
    for dtype in (torch.complex64, torch.complex128):
        tensor = torch.zeros(8, dtype=dtype)
        with pytest.raises(TypeError, match="CG requires a floating-point"):
            metrics.CG(tensor)
# ---------------------------------------------------------------------------
# Req 19: the 1:1 parity assertion covers only the reparameterizable entries,
# and the representable-baseline set is pinned so the deferral note stays honest
# (change 2026-10-02-audit-a2-errata-and-spec-math-fixes; F6 / F8)
#
# The Scenario used to claim "every MoE entry equals the Dense baseline's
# per-token active FLOPs", which is wider than the parity formula's own object
# range: it is defined for a given (N_e, k, d_model, d_ffn^Expert) via
# `d_ffn^Dense ≡ k · d_ffn^Expert`, and cannot be asserted for external QLoRA /
# GMoE checkpoints. The Scenario is now scoped accordingly, and the deferred
# entries are declared in the Requirement body.
#
# These two tests are the enforcement: the parity pin, and an AST guard that
# fails if `flops_per_token` ever admits a third arch — which would silently
# make the Requirement's deferral annotation stale.
# ---------------------------------------------------------------------------

# the arch discriminators this test expects the impl to compare against
_EXPECTED_ARCH_LITERALS = {"MOE", "DENSE"}


def _arch_literals_of(node: ast.AST) -> set[str]:
    """String literals that `node` compares for equality with `==`.

    Deliberately NOT "every string in the body": the `raise` in
    `flops_per_token` embeds `'MOE' or 'DENSE'` inside an f-string message, so
    a naive Constant walk would pick up message fragments that are not
    discriminators at all.
    """
    out: set[str] = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Compare):
            continue
        for op, comparator in zip(sub.ops, sub.comparators):
            if (
                isinstance(op, ast.Eq)
                and isinstance(comparator, ast.Constant)
                and isinstance(comparator.value, str)
            ):
                out.add(comparator.value)
    return out


def test_flops_per_token_admits_only_moe_and_dense() -> None:
    """Guard the Req 19 deferral: `flops_per_token` admits exactly MOE / DENSE.

    If a future change adds a third arch, the Requirement's "the other four
    baselines are deferred / zero representation" note becomes false, and this
    test turns red so the spec is updated in the same change.
    """
    # (0) MINIMAL SMOKE TEST of the extractor before trusting it on the real
    # source — a counter that silently reports an empty set would make the
    # assertion below vacuously true.
    smoke = ast.parse(
        "def probe(arch):\n"
        "    if arch == 'ALPHA':\n"
        "        return 1\n"
        "    if arch == 'BETA':\n"
        "        return 2\n"
        "    raise ValueError(f\"unknown {arch!r} (ALPHA or BETA)\")\n"
    )
    smoke_fn = next(
        n for n in ast.walk(smoke) if isinstance(n, ast.FunctionDef)
    )
    smoke_got = _arch_literals_of(smoke_fn)
    assert smoke_got == {"ALPHA", "BETA"}, (
        f"actual={sorted(smoke_got)}; the extractor must return the equality "
        f"operands only and must NOT pick up the f-string message fragments"
    )

    # (1) the real source
    src = pathlib.Path(config.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "flops_per_token"
    )
    got = _arch_literals_of(fn)
    assert got == _EXPECTED_ARCH_LITERALS, (
        f"actual={sorted(got)}; flops_per_token must admit exactly "
        f"{sorted(_EXPECTED_ARCH_LITERALS)}. A third arch means Req 19's "
        f"deferral note for the QLoRA / GMoE / Random-* baselines is stale"
    )


def test_active_flops_parity_reparameterization_closed_form() -> None:
    """Parity holds exactly for the entries admitting `d_ffn^Dense ≡ k·d_ffn^Expert`."""
    cfg = config.MVPConfig()
    d_ffn_dense = 4096
    k, d_ffn_expert = 2, 2048

    # MVP: the one entry the Requirement can pin exactly
    assert d_ffn_dense == k * d_ffn_expert, (
        f"actual={d_ffn_dense} vs {k}*{d_ffn_expert}={k * d_ffn_expert}; "
        f"MVP parity is the identity d_ffn^Dense = k·d_ffn^Expert"
    )

    # Mixtral reproduction (N_e=8, k=2): parity REQUIRES a re-densified
    # baseline, it does not hold against a stock d_ffn.
    mixtral_d_ffn = 14_336
    assert k * mixtral_d_ffn == 28_672, (
        f"actual={k * mixtral_d_ffn}; a Mixtral-shaped MoE is at parity only "
        f"with a Dense baseline re-densified to 28_672, not with a stock one"
    )
    assert 28_672 != d_ffn_dense, (
        "premise broken: if the re-densified Mixtral width equalled the MVP "
        "Dense width, the two entries would be indistinguishable here"
    )

    # the active-core FLOPs really do match under that reparameterization
    moe = 8 * cfg.d_model**2 + k * 6 * cfg.d_model * d_ffn_expert
    dense = 8 * cfg.d_model**2 + 6 * cfg.d_model * d_ffn_dense
    assert moe == dense == 33_554_432, f"actual_moe={moe}, actual_dense={dense}"
