"""Tests for `decompmoe.distance`: squared-chord + logit composition.

ST-06 / Req 7 — distance d(C, c_i) = 1 − Cᵀc_i ∈ [0, 2]; logit = β·(Cᵀc − 1).
"""
from __future__ import annotations

import inspect
from pathlib import Path

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
    assert d.min().item() >= -1e-5, f"d_min = {d.min().item()} < 0"
    assert d.max().item() <= 2.0 + 1e-5, f"d_max = {d.max().item()} > 2"


def test_distance_zero_at_align() -> None:
    """d(c_i, c_i) == 0."""
    torch.manual_seed(0)
    c = torch.nn.functional.normalize(torch.randn(16), dim=-1)
    d = distance.squared_chord(c, c)
    assert abs(d.item()) < 1e-5, f"d(c, c) = {d.item()} ≠ 0"


def test_distance_two_at_antipode() -> None:
    """d(c, −c) == 2 (d_c = 2)."""
    c = torch.tensor([1.0, 0.0])
    c_neg = torch.tensor([-1.0, 0.0])
    d = distance.squared_chord(c, c_neg)
    assert abs(d.item() - 2.0) < 1e-5, f"d(c, -c) = {d.item()} ≠ 2"


def test_logit_zero_at_aligned() -> None:
    """logit(c_i, c_i, β) == 0."""
    torch.manual_seed(0)
    c = torch.nn.functional.normalize(torch.randn(16), dim=-1)
    out = distance.logit(c, c, beta=4.0)
    assert abs(out.item()) < 1e-5, f"logit(c, c) = {out.item()} ≠ 0"


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


def test_logit_grad_safe() -> None:
    """‖∂logit/∂C‖₂ ≤ β_max (gradient bound per Req 7 / A4-1)."""
    from decompmoe.beta import MAX_GRAD_PER_C

    torch.manual_seed(0)
    d_c = 16
    C = torch.nn.Parameter(torch.randn(d_c))
    c = torch.nn.functional.normalize(torch.randn(d_c), dim=-1)
    out = distance.logit(C / C.norm(), c, beta=MAX_GRAD_PER_C)
    grad = torch.autograd.grad(out, C, create_graph=False)[0]
    assert grad.norm().item() <= MAX_GRAD_PER_C + 1e-3