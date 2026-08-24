"""Tests for `decompmoe.experts`: SwiGLU expert + ExpertPool.

ST-08 / Req 9 (Standard SwiGLU) + Req 10 (no shared expert).
"""

from __future__ import annotations

import inspect
from pathlib import Path

import torch

from decompmoe import experts
from decompmoe.config import MVPConfig


def test_swiglu_formula() -> None:
    torch.manual_seed(0)
    cfg = MVPConfig()
    expert = experts.SwiGLUExpert(cfg)
    x = torch.randn(4, cfg.d_model)
    y = expert(x)
    silu = torch.nn.functional.silu(x @ expert.W_g.T)
    out_ref = (silu * (x @ expert.W_u.T)) @ expert.W_d.T
    assert torch.allclose(y, out_ref, atol=1e-5)


def test_expert_param_count() -> None:
    cfg = MVPConfig()
    expert = experts.SwiGLUExpert(cfg)
    n_params = sum(p.numel() for p in expert.parameters())
    expected = 3 * cfg.d_model * cfg.d_ffn
    assert n_params == expected, f"expected {expected}, got {n_params}"


def test_no_c_injection() -> None:
    sig = inspect.signature(experts.SwiGLUExpert.forward)
    param_names = set(sig.parameters.keys())
    assert param_names == {"self", "x"}, (
        f"SwiGLUExpert.forward must take only (self, x); got {param_names}"
    )


def test_expert_pool_no_shared_branch() -> None:
    cfg = MVPConfig()
    pool = experts.ExpertPool(cfg)
    assert hasattr(pool, "experts")
    assert not hasattr(pool, "shared"), (
        "ExpertPool must NOT expose a `shared` attribute (A5-2 invariant)"
    )
    assert not hasattr(pool, "shared_expert")
    assert len(pool.experts) == cfg.N_e


def test_no_custom_kernel() -> None:
    src = Path(experts.__file__).read_text(encoding="utf-8")
    assert "cpp_extension" not in src, (
        "experts.py must not import torch.utils.cpp_extension (Req 9 / 18)"
    )
    assert "triton" not in src.lower()


def test_isomorphic_to_llama_ffn() -> None:
    torch.manual_seed(0)
    cfg = MVPConfig()
    expert = experts.SwiGLUExpert(cfg)
    x = torch.randn(2, cfg.d_model)
    y = expert(x)
    ref_lin_g = torch.nn.Linear(cfg.d_model, cfg.d_ffn, bias=False)
    ref_lin_u = torch.nn.Linear(cfg.d_model, cfg.d_ffn, bias=False)
    ref_lin_d = torch.nn.Linear(cfg.d_ffn, cfg.d_model, bias=False)
    with torch.no_grad():
        ref_lin_g.weight.copy_(expert.W_g)
        ref_lin_u.weight.copy_(expert.W_u)
        ref_lin_d.weight.copy_(expert.W_d)
    y_ref = ref_lin_d(torch.nn.functional.silu(ref_lin_g(x)) * ref_lin_u(x))
    assert torch.allclose(y, y_ref, atol=1e-5)


# ---------------------------------------------------------------------------
# Task 3.5 / 3.14 — ExpertPool is an nn.Module with ModuleList (spec:
# skeleton "Standard SwiGLU Expert With No Shared Branch")
# ---------------------------------------------------------------------------


def test_expert_pool_is_nn_module() -> None:
    """ExpertPool(MVPConfig()) is nn.Module with experts: nn.ModuleList."""
    pool = experts.ExpertPool(MVPConfig())
    assert isinstance(pool, torch.nn.Module)
    assert isinstance(pool.experts, torch.nn.ModuleList)


def test_expert_pool_param_count() -> None:
    """sum(p.numel()) == N_e · 3 · d_model · d_ffn == 100_663_296 exact."""
    cfg = MVPConfig()
    pool = experts.ExpertPool(cfg)
    total = sum(p.numel() for p in pool.parameters())
    expected = cfg.N_e * 3 * cfg.d_model * cfg.d_ffn
    assert total == expected
    assert total == 100_663_296


def test_expert_pool_source_contains_modulelist() -> None:
    """禁止性约束：`inspect.getsource(ExpertPool)` mentions nn.Module + nn.ModuleList."""
    src = inspect.getsource(experts.ExpertPool)
    assert "nn.Module" in src
    assert "nn.ModuleList" in src
