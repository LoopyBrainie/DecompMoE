"""Tests for `decompmoe.contracts`: wire-level Protocol stubs.

ST-01 / Req 3, 4, 16, 17, 18 — wire-level contracts only, no executable bodies.

Written FIRST (TDD Red). GREEN step implements `decompmoe.contracts`.
"""
from __future__ import annotations

import inspect

from decompmoe import contracts


def _declared_members(proto: type) -> set[str]:
    """Return the names declared on a Protocol's `__annotations__` / methods.

    `typing.get_type_hints()` does NOT include method annotations by default
    for `Protocol` classes — they live in `__annotations__` but are filtered
    by `get_type_hints`. We collect via `__dict__` + `__annotations__` to
    cover both attribute slots and method signatures.
    """
    names: set[str] = set()
    for klass in proto.__mro__:
        names.update(klass.__dict__.keys())
        if hasattr(klass, "__annotations__"):
            names.update(klass.__annotations__.keys())
    # Strip dunder / inherited noise
    return {n for n in names if not n.startswith("__")}


# ---------------------------------------------------------------------------
# GeometricRouter: required methods present (Req 3, 4, 16, 17, 18)
# ---------------------------------------------------------------------------


def test_router_contract_signatures() -> None:
    """GeometricRouter must declare extract_C, gating_logits, route."""
    members = _declared_members(contracts.GeometricRouter)
    assert "extract_C" in members, (
        f"GeometricRouter must declare extract_C(K, V) -> Tensor (got {members})"
    )
    assert "gating_logits" in members, (
        f"GeometricRouter must declare gating_logits(C) -> Tensor (got {members})"
    )
    assert "route" in members, (
        f"GeometricRouter must declare route(x, logits) -> Tensor (got {members})"
    )


def test_router_protocol_origin() -> None:
    """GeometricRouter must be a typing.Protocol (structural typing)."""
    for proto in (contracts.GeometricRouter, contracts.TerritoryHolder, contracts.BlockAdapter):
        assert isinstance(proto, type), f"{proto.__name__} must be a class"
        # Protocol classes expose _is_protocol=True (CPython 3.8+)
        assert getattr(proto, "_is_protocol", False) is True, (
            f"{proto.__name__} must be a typing.Protocol"
        )


def test_no_kv_cache_field() -> None:
    """GeometricRouter must NOT expose kv_cache_c (Req 16 forbids C_t in KV cache)."""
    members = _declared_members(contracts.GeometricRouter)
    assert "kv_cache_c" not in members, (
        f"GeometricRouter must not declare kv_cache_c (got {members})"
    )
    assert not hasattr(contracts.GeometricRouter, "kv_cache_c"), (
        "GeometricRouter Protocol has no kv_cache_c attribute"
    )


# ---------------------------------------------------------------------------
# TerritoryHolder: required methods present (Req 4)
# ---------------------------------------------------------------------------


def test_territory_holder_signatures() -> None:
    """TerritoryHolder must declare territory_volume, active_territories, coverage_balance_loss."""
    members = _declared_members(contracts.TerritoryHolder)
    assert "territory_volume" in members
    assert "active_territories" in members
    assert "coverage_balance_loss" in members


# ---------------------------------------------------------------------------
# BlockAdapter: required methods present (Req 3: Post-FFN mount point)
# ---------------------------------------------------------------------------


def test_block_adapter_signatures() -> None:
    """BlockAdapter must declare forward_residual."""
    members = _declared_members(contracts.BlockAdapter)
    assert "forward_residual" in members


# ---------------------------------------------------------------------------
# Hard-constraint: no w_i in any router signature (Req 7 / A4-2)
# ---------------------------------------------------------------------------


def test_no_w_i_in_router_signatures() -> None:
    """GeometricRouter must not have any parameter named w_i (A4-2 invariant)."""
    for method_name in ("extract_C", "gating_logits", "route"):
        method = getattr(contracts.GeometricRouter, method_name, None)
        assert method is not None, f"GeometricRouter.{method_name} must exist"
        sig = inspect.signature(method)
        param_names = set(sig.parameters.keys())
        assert "w_i" not in param_names, (
            f"GeometricRouter.{method_name} must not have a 'w_i' parameter"
        )