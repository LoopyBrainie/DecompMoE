"""Tests for `decompmoe.loss`: L_CE + α·L_lb + λ(t)·L_sep.

ST-09 / Req 12 — α = 0.01 (Switch-style); λ(t) staged schedule.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import torch

from decompmoe import loss as loss_mod


def test_load_balance_alpha_fixed() -> None:
    """α == 0.01 (Switch-style) AND closed forms: uniform f = P = 1/16 →
    L_lb_raw == 1.0 and L_lb == 0.01 exact.

    Spec: skeleton "Loss Composition With Staged Lambda", Scenarios
    "L_lb closed form on uniform routing" + "Alpha pinned to 0.01":
    L_lb_raw = N_e · Σ_i f_i·P_i = 16 · 16 · (1/16)² = 1.0.
    """
    torch.manual_seed(0)
    B, N, V, N_e = 1, 1, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.full((B, N, N_e), 1.0 / N_e)
    p = torch.full((B, N, N_e), 1.0 / N_e)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts = loss_mod.L_total(task_logits, targets, f, p, c, phase=1, step=1_000)
    assert parts.L_lb_raw.item() == pytest.approx(1.0, abs=1e-6), (
        f"actual={parts.L_lb_raw.item()}; L_lb_raw(uniform) expected 1.0"
    )
    assert parts.L_lb.item() == pytest.approx(0.01, abs=1e-8), (
        f"actual={parts.L_lb.item()}; L_lb = α · 1.0 must equal 0.01"
    )


def test_lb_gradient_flows_through_P_i() -> None:
    """`∂L_lb/∂P_i ≠ 0` AND `∂L_lb/∂f_i ≡ 0` (wayfinder Req 12 invariant).

    Spec: skeleton "Loss Composition With Staged Lambda" Scenario
    `L_lb gradient flows through P_i only`. Verifies the spec-mandated
    double-factor closed form `L_lb = α · N_e · Σ f.detach() · P`:
      - P_i path is differentiable (gradient flows back into logit chain)
      - f_i path is blocked by `.detach()`

    Closed-form guard: under uniform routing `f = P = 1/N_e`, the spec
    closed form gives
      - `L_lb_raw = N_e · Σ (1/N_e) · (1/N_e) = 1.0`
      - `L_lb = α · L_lb_raw = 0.01 · 1.0 = 0.01` (`α = 0.01` Switch-style)
      - `∂L_lb / ∂P[b,n,i] = α · N_e · f_det_i / (B·N)`
        = `0.01 · 16 · (1/16) / (1·4) = 0.0025` for the chosen (B=1, N=4) setup.
        (Each entry is constant per i; the `α`, `N_e`, and `(B·N)` scaling
        factors are all essential — dropping α would silently raise the
        gradient to 0.25, dropping N_e would silently reduce it to α/(BN),
        and the per-(B,N) entry aggregation is what brings the per-(b,n,i)
        gradient below the per-i gradient.)
    This guards against silent zero-grad regressions and against any future
    refactor that drops either the `α` Switch-style weight or the `N_e`
    scaling factor or weakens the `f.detach()` barrier.
    """
    torch.manual_seed(0)
    B, N, N_e = 1, 4, 16  # MVP N_e=16 per CLAUDE.md §5 MVP hyperparameters
    f_uniform = torch.nn.Parameter(torch.full((B, N, N_e), 1.0 / N_e))
    p_uniform = torch.nn.Parameter(torch.full((B, N, N_e), 1.0 / N_e))
    task_logits = torch.randn(B, N, 32)
    targets = torch.randint(0, 32, (B, N))
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts = loss_mod.L_total(task_logits, targets, f_uniform, p_uniform, c, phase=1, step=1_000)
    # Closed-form guard on the forward value (spec Req 11: α=0.01 pinned).
    assert parts.L_lb.item() == pytest.approx(0.01, abs=1e-6), (
        f"actual={parts.L_lb.item()}; expected α · 1.0 = 0.01 per "
        f"spec closed form α · N_e · Σ (1/N_e) · (1/N_e)"
    )
    grad_p = torch.autograd.grad(parts.L_lb, p_uniform, retain_graph=True)[0]
    # f MUST be detached inside L_total (spec contract); if f were used in the
    # autograd graph, ∂L_lb/∂f would be a non-None tensor (zero or nonzero).
    # The spec-mandated behavior: grad_f is exactly None (= f not in graph).
    # If a future change routes f through the graph (even if grad is numerically
    # zero), this assertion catches it.
    grad_f = torch.autograd.grad(parts.L_lb, f_uniform, retain_graph=True, allow_unused=True)[0]
    assert grad_f is None, (
        "∂L_lb/∂f_i must be detached (f not in graph); "
        f"got grad_f with shape {tuple(grad_f.shape) if grad_f is not None else 'None'}"
    )
    # Closed-form guard on ∂L_lb/∂P[b,n,i]: under uniform routing, every entry
    # equals `α · N_e · f_det_i / (B·N) = 0.01 · 16 · (1/16) / 4 = 0.0025`.
    expected_grad = 0.01 * N_e * (1.0 / N_e) / (B * N)  # = α / (B·N) = 0.0025
    assert torch.isfinite(grad_p).all()
    assert torch.allclose(grad_p, torch.full_like(grad_p, expected_grad), atol=1e-6), (
        f"∂L_lb/∂P[b,n,i] under uniform f=P=1/{N_e} must equal "
        f"α · N_e · f_det_i / (B·N) = {expected_grad} element-wise; "
        f"got min={grad_p.min().item():.3e}, max={grad_p.max().item():.3e}"
    )


def test_lb_uses_detached_fractions() -> None:
    """L_lb must use `f_per_expert.detach()` specifically — AST scan checks
    the variable name AND the call, not any generic `.detach()` occurrence.

    Per CLAUDE.md §6 第 8 条: a test named "uses detached fractions" must
    fail if the SPECIFIC contract `f_det = f_per_expert.detach()` is missing
    or replaced with something semantically equivalent-but-different.
    """
    import ast as _ast

    src = inspect.getsource(loss_mod)
    tree = _ast.parse(src)

    # 1. Find any Assign where the target is `f_det` and RHS is
    #    `f_per_expert.detach()` — SPECIFIC contract.
    specific_detach = False
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, _ast.Name) and tgt.id == "f_det":
                    rhs = node.value
                    if (
                        isinstance(rhs, _ast.Call)
                        and isinstance(rhs.func, _ast.Attribute)
                        and rhs.func.attr == "detach"
                        and isinstance(rhs.func.value, _ast.Name)
                        and rhs.func.value.id == "f_per_expert"
                    ):
                        specific_detach = True
    assert specific_detach, (
        "loss.py must contain `f_det = f_per_expert.detach()` for L_lb"
    )

    # 2. The L_lb computation must reference `f_det` (the detached alias),
    #    NOT the raw `f_per_expert`. Slice the source to assert presence.
    #    (Implementation may compute L_lb anywhere; we check that f_det
    #    appears as a name binding/use after the assignment.)
    src_loss_block = src[src.index("f_det") :] if "f_det" in src else ""
    assert "f_det" in src_loss_block and "f_det.mean" in src_loss_block, (
        "L_lb must consume `f_det` (not raw f_per_expert)"
    )


def test_lambda_zero_phase_1_2() -> None:
    """For phase ∈ {1, 2}, λ(t) == 0 ⇒ L_sep contribution is 0."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    p = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    for phase in (1, 2):
        parts = loss_mod.L_total(
            task_logits, targets, f, p, c, phase=phase, step=phase * 5_000
        )
        assert parts.L_sep.item() == pytest.approx(0.0, abs=1e-12), (
            f"actual={parts.L_sep.item()}; phase {phase} should have λ=0 ⇒ L_sep=0"
        )


def test_lambda_cosine_ramp_phase_3() -> None:
    """Phase-3 λ(t) cosine ramp pinned at 3 exact step values.

    Spec: skeleton "Loss Composition With Staged Lambda", Scenario
    "Lambda cosine ramp endpoints in phase 3": λ(26_000) == 0.0,
    λ(41_000) ≈ 5e-4, λ(55_999) ≈ 0.001. λ(t) is verified directly against
    the cosine closed form, so no L_sep_raw reference scaling is needed.
    """
    lam_start = loss_mod._lambda_at(3, 26_000)
    lam_mid = loss_mod._lambda_at(3, 41_000)
    lam_end = loss_mod._lambda_at(3, 55_999)
    assert lam_start == pytest.approx(0.0, abs=1e-12), (
        f"actual={lam_start}; λ(26_000) should be 0 at the phase-3 ramp start"
    )
    assert lam_mid == pytest.approx(5e-4, abs=1e-6), (
        f"actual={lam_mid}; λ(41_000) expected 5e-4"
    )
    assert lam_end == pytest.approx(0.001, abs=1e-6), (
        f"actual={lam_end}; λ(55_999) expected 0.001"
    )


def test_lambda_fixed_phase_4() -> None:
    """For phase == 4, λ(t) == 0.001 fixed across step."""
    torch.manual_seed(0)
    B, N, V, N_e = 2, 4, 100, 16
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    p = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, 16), dim=-1)
    parts1 = loss_mod.L_total(task_logits, targets, f, p, c, phase=4, step=56_000)
    parts2 = loss_mod.L_total(task_logits, targets, f, p, c, phase=4, step=100_000)
    assert torch.allclose(parts1.L_sep, 0.001 * parts1.L_sep_raw, atol=1e-6), (
        f"actual={parts1.L_sep.item()} vs 0.001 * L_sep_raw="
        f"{parts1.L_sep_raw.item()} at step 56_000"
    )
    assert torch.allclose(parts2.L_sep, 0.001 * parts2.L_sep_raw, atol=1e-6), (
        f"actual={parts2.L_sep.item()} vs 0.001 * L_sep_raw="
        f"{parts2.L_sep_raw.item()} at step 100_000"
    )


def test_sep_raw_wired_into_l_total() -> None:
    """`L_total` MUST actually compose `L_sep = λ(t)·compute_L_sep(c)`.

    Spec req-12: `L_sep = (‖CᵀC‖_F² − N_e) / (N_e·(N_e−1))` and
    `L_total = L_CE + α·L_lb + λ(t)·L_sep`.

    Wiring guard: the closed forms above are only reachable by calling
    `compute_L_sep` directly, and `test_lambda_fixed_phase_4` compares
    `L_sep` against `L_sep_raw` *from the same `LossParts`* — so both stay
    self-consistent even if the call site were rewired to a stub (e.g.
    `L_sep_raw = torch.zeros(())`) or if `L_total` dropped the separation
    term. Here `L_sep_raw` is re-derived **independently from `c`** so a
    zero-stub fails, and the final assertion pins the 3-term composition.
    """
    torch.manual_seed(7)
    B, N, V = 2, 4, 100
    N_e, d_c = 8, 4
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    p = torch.softmax(torch.randn(B, N, N_e), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)

    parts = loss_mod.L_total(task_logits, targets, f, p, c, phase=4, step=56_000)

    # Independent re-derivation of the spec closed form (NOT compute_L_sep).
    G = c @ c.T
    expected_sep_raw = float(((G * G).sum() - N_e) / (N_e * (N_e - 1)))
    assert expected_sep_raw > 0.0, (
        f"test setup is degenerate: expected_sep_raw={expected_sep_raw} must be > 0"
    )
    assert parts.L_sep_raw.item() == pytest.approx(expected_sep_raw, abs=1e-9), (
        f"actual={parts.L_sep_raw.item()}; L_total must expose the spec "
        f"L_sep closed form {expected_sep_raw} re-derived from c"
    )

    lam = loss_mod._lambda_at(4, 56_000)
    assert parts.L_sep.item() == pytest.approx(lam * expected_sep_raw, abs=1e-9), (
        f"actual={parts.L_sep.item()}; expected λ={lam} * L_sep_raw="
        f"{expected_sep_raw}"
    )

    expected_total = parts.L_CE.item() + parts.L_lb.item() + parts.L_sep.item()
    assert parts.L_total.item() == pytest.approx(expected_total, abs=1e-6), (
        f"actual={parts.L_total.item()}; L_total must equal "
        f"L_CE({parts.L_CE.item()}) + L_lb({parts.L_lb.item()}) + "
        f"L_sep({parts.L_sep.item()})"
    )


def test_lb_N_e_comes_from_cfg_not_tensor_width() -> None:
    """The spec's `N_e` multiplier MUST come from `cfg.N_e` when supplied.

    Spec req-12 closed form: `L_lb = N_e · Σ_i f_i.detach() · P_i`, where
    `N_e` is the model-wide constant. The call site therefore has to read the
    authoritative configured value rather than inferring `N_e` from the
    routing tensor's last dimension.

    The two are deliberately made inconsistent here (tensor width 8 vs
    `cfg.N_e = 4`) because that is the *only* way to tell the two sources
    apart; under a correct call they coincide by the `N_e` invariant, and a
    test using matching widths would pass under either implementation.
    """
    torch.manual_seed(11)
    B, N, V = 2, 4, 100
    width = 8
    task_logits = torch.randn(B, N, V)
    targets = torch.randint(0, V, (B, N))
    f = torch.softmax(torch.randn(B, N, width), dim=-1)
    p = torch.softmax(torch.randn(B, N, width), dim=-1)
    c = torch.nn.functional.normalize(torch.randn(width, 4), dim=-1)

    from decompmoe.config import MVPConfig

    cfg = MVPConfig(N_e=4)
    parts = loss_mod.L_total(
        task_logits, targets, f, p, c, phase=1, step=1_000, cfg=cfg
    )

    expected = float(
        (f.detach().mean(dim=(0, 1)) * p.mean(dim=(0, 1))).sum() * cfg.N_e
    )
    assert parts.L_lb_raw.item() == pytest.approx(expected, abs=1e-6), (
        f"actual={parts.L_lb_raw.item()}; expected cfg.N_e={cfg.N_e} scaling "
        f"→ {expected} (tensor width would give "
        f"{expected / cfg.N_e * width})"
    )


def test_sep_formula_orthonormal_degenerate() -> None:
    """Orthonormal basis → L_sep == 0.0 (DEGENERATE boundary case).

    Spec: skeleton "Loss Composition With Staged Lambda", Scenario
    "L_sep closed form degenerate boundary": for an orthonormal centroid
    set, ‖CᵀC‖_F² == N_e exactly, so the numerator vanishes identically.
    """
    N_e, d_c = 16, 16
    c = torch.eye(N_e, d_c)
    L_sep = loss_mod.compute_L_sep(c)
    assert L_sep.item() == pytest.approx(0.0, abs=1e-12), (
        f"actual={L_sep.item()}; L_sep(orthonormal basis) expected 0"
    )


def test_sep_formula_non_degenerate() -> None:
    """Non-degenerate L_sep must match spec closed form exactly (abs=1e-9).

    Spec: L_sep = (‖CᵀC‖_F² − N_e) / (N_e·(N_e−1)). For non-orthogonal
    centroids, the implementation must compute this value — a degenerate
    `compute_L_sep = torch.zeros_like` would fail. Test with N_e=8, d_c=4
    so columns must overlap (rank-constrained).
    """
    torch.manual_seed(42)
    N_e, d_c = 8, 4
    c = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    G = c @ c.T
    fro_sq = (G * G).sum()
    expected = (fro_sq - N_e) / (N_e * (N_e - 1))
    actual = loss_mod.compute_L_sep(c)
    assert actual.item() > 0, "L_sep must be > 0 for non-orthogonal centroids"
    assert actual.item() == pytest.approx(float(expected), abs=1e-9), (
        f"actual={actual.item()}; L_sep expected {float(expected)}"
    )

    # Sanity: pair-wise reformulation is mathematically equivalent but
    # may differ in floating point summation order (~1e-8). Tolerance
    # abs=1e-6 captures the equivalence without false-failing on order.
    pair_sum = 0.0
    for i in range(N_e):
        for j in range(i + 1, N_e):
            pair_sum += float(G[i, j]) ** 2
    expected_pairs = (2.0 / (N_e * (N_e - 1))) * pair_sum
    assert actual.item() == pytest.approx(expected_pairs, abs=1e-6), (
        f"actual={actual.item()}; L_sep pair-wise form expected {expected_pairs}"
    )


def test_token_vs_expert_C_notation() -> None:
    """loss source must distinguish per-token `C_t^l` vs per-expert `c_i^l`."""
    src = Path(loss_mod.__file__).read_text(encoding="utf-8")
    assert "C_t^l" in src or "C_t" in src
    assert "c_i^l" in src or "c_i" in src
