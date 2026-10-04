"""Tests for `decompmoe.distance`: squared-chord + logit composition.

ST-06 / Req 7 — distance d(C, c_i) = 1 − Cᵀc_i ∈ [0, 2]; logit = β·(Cᵀc − 1).
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import torch

from decompmoe import distance


def test_distance_range() -> None:
    """d(C, c_i) ∈ [0, 2] for C, c_i on the unit sphere (1000-sample property test)."""
    torch.manual_seed(0)
    d_c = 16
    N = 1000
    C = torch.randn(N, d_c)
    c = torch.randn(d_c)
    C_unit = torch.nn.functional.normalize(C, dim=-1)
    c_unit = torch.nn.functional.normalize(c, dim=-1)
    d = distance.squared_chord(C_unit, c_unit)
    assert d.min().item() >= -1e-5, f"actual={d.min().item()} < 0"
    assert d.max().item() <= 2.0 + 1e-5, f"actual={d.max().item()} > 2"


def test_distance_zero_at_align() -> None:
    """d(c_i, c_i) == 0."""
    torch.manual_seed(0)
    c = torch.nn.functional.normalize(torch.randn(16), dim=-1)
    d = distance.squared_chord(c, c)
    assert d.item() == pytest.approx(0.0, abs=1e-5), f"actual={d.item()}"


def test_distance_two_at_antipode() -> None:
    """d(c, −c) == 2 (d_c = 2)."""
    c = torch.tensor([1.0, 0.0])
    c_neg = torch.tensor([-1.0, 0.0])
    d = distance.squared_chord(c, c_neg)
    assert d.item() == pytest.approx(2.0, abs=1e-5), f"actual={d.item()}"


def test_logit_zero_at_aligned() -> None:
    """logit(c_i, c_i, β) == 0."""
    torch.manual_seed(0)
    c = torch.nn.functional.normalize(torch.randn(16), dim=-1)
    out = distance.logit(c, c, beta=4.0)
    assert out.item() == pytest.approx(0.0, abs=1e-5), f"actual={out.item()}"


def test_logit_no_w_i() -> None:
    """logit signature MUST NOT contain a parameter named w_i (A4-2 invariant).

    The signature-level check is the canonical hard invariant. Docstrings may
    reference `w_i` for design context (A4-2 rationale); the executable body
    uses AST-based extraction to verify no `w_i` symbol participates.
    """
    import ast as _ast
    sig = inspect.signature(distance.logit)
    param_names = set(sig.parameters.keys())
    assert "w_i" not in param_names, (
        f"distance.logit must not have a 'w_i' parameter (got {param_names})"
    )
    # AST parse: collect all Name references in the function body; assert no `w_i`.
    src = inspect.getsource(distance.logit)
    tree = _ast.parse(src)
    fn = tree.body[0]
    for node in _ast.walk(fn):
        if isinstance(node, _ast.Name) and node.id == "w_i":
            raise AssertionError(
                "distance.logit body uses 'w_i' as a name (A4-2 / CLAUDE.md §6)"
            )


def test_logit_grad_norm_equals_beta_on_the_sphere() -> None:
    """‖∂logit/∂C‖₂ == β for unit C and unit c — the bound is attained, not slack.

    Closed form: `logit = β·(Cᵀc − 1)` is linear in `C`, so `∂logit/∂C = βc`
    exactly and `‖∂logit/∂C‖₂ = β·‖c‖₂ = β`. `C` enters the chain directly, so
    the differentiation MUST be taken on the sphere point itself — feeding
    `C / ‖C‖` into `logit` would differentiate the *composition* with the
    projection (whose Jacobian is `β·(I − ûûᵀ)·c`, norm ≤ β but typically
    ~β/3), which is a different quantity from the one the spec bounds.

    The declared worst case (`β = β_max`, orthogonal unit `C` and `c`) is
    pinned separately with the orthogonal construction in
    `tests/test_beta.py::test_grad_C_bound`; this test covers the *general*
    unit-sphere case that the Scenario only samples at one point. Tolerance is
    the spec Scenario's own `abs=1e-4` (float32 autograd round-off on the
    32-magnitude product measures ~3.8e-6).
    """
    from decompmoe.beta import MAX_GRAD_PER_C

    torch.manual_seed(0)
    d_c = 16
    for _ in range(5):
        C = torch.nn.Parameter(
            torch.nn.functional.normalize(torch.randn(d_c), dim=-1)
        )
        c = torch.nn.functional.normalize(torch.randn(d_c), dim=-1)
        out = distance.logit(C, c, beta=MAX_GRAD_PER_C)
        grad_norm = torch.autograd.grad(out, C, create_graph=False)[0].norm().item()
        assert grad_norm == pytest.approx(MAX_GRAD_PER_C, abs=1e-4), (
            f"actual={grad_norm}, expected β=MAX_GRAD_PER_C={MAX_GRAD_PER_C} "
            f"for unit C and unit c"
        )
