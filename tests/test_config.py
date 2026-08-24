"""Tests for `decompmoe.config`: MVPConfig + compute_total_and_active + flops_per_token.

ST-01 / Req 1, 2, 11, 19 (form factor / FLOPs parity).

These tests are written FIRST (TDD Red) — they intentionally fail at import time
because `decompmoe.config` does not exist yet. The GREEN step implements the
module to make these pass.
"""
from __future__ import annotations

import dataclasses

import pytest

import decompmoe
from decompmoe import config

# ---------------------------------------------------------------------------
# MVPConfig field defaults (Req 11: 4070 MVP hyperparameters)
# ---------------------------------------------------------------------------


def test_mvp_locked_constants() -> None:
    """MVPConfig() must return the locked 4070 MVP hyperparameter set."""
    cfg = config.MVPConfig()
    assert cfg.d_model == 1024
    assert cfg.N_e == 16
    assert cfg.k == 2
    assert cfg.d_ffn == 2048
    assert cfg.L == 4
    # Extended geometry constants required by extraction/distance
    assert cfg.d_ffn_dense == 4096
    assert cfg.d_c == 16
    assert cfg.H_kv == 8
    assert cfg.d_k == 128


def test_mvp_is_frozen() -> None:
    """Mutating any field of MVPConfig must raise FrozenInstanceError."""
    cfg = config.MVPConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.d_model = 2048  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.N_e = 32  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Total / active parameter estimator (Req 11: 452M / 100M)
# ---------------------------------------------------------------------------


def test_total_param_estimate() -> None:
    """compute_total_and_active returns the spec EXACT totals.

    Spec: wayfinder "4070 MVP Hyperparameter Set", Scenario
    "Closed-form parameter totals": total == 452_329_984,
    active == 100_008_448, P_router/layer == 32_896 exact (the router term
    previously misclassified as rounding).
    """
    cfg = config.MVPConfig()
    total, active = config.compute_total_and_active(cfg)

    assert total == 452_329_984, f"total {total} != 452_329_984"
    assert active == 100_008_448, f"active {active} != 100_008_448"
    # Router per layer: H_kv · (2·d_k·d_c + d_c) = 8 · (2·128·16 + 16) = 32_896
    assert config._router_params_per_layer(cfg) == 32_896


def test_flops_per_layer_exact_33554432() -> None:
    """Per-layer MoE FLOPs == 33_554_432 exact.

    Spec: wayfinder "4070 MVP Hyperparameter Set", Scenario
    "Closed-form parameter totals": L × (4·2·d_model² + k·3·2·d_model·d_ffn)
    with SwiGLU counting 3 matrices (g, u, d).
    """
    cfg = config.MVPConfig()
    per_layer = 4 * 2 * cfg.d_model**2 + cfg.k * 3 * 2 * cfg.d_model * cfg.d_ffn
    assert config.flops_per_token(cfg, "MOE") == cfg.L * per_layer
    assert per_layer * 4 == 134_217_728
    assert per_layer == 33_554_432


def test_flops_total_exact_134217728() -> None:
    """Total MoE active FLOPs per token == 134_217_728 exact (spec closed form)."""
    assert config.flops_per_token(config.MVPConfig(), "MOE") == 134_217_728


def test_active_flops_parity() -> None:
    """flops_per_token(MOE_MVP) must equal flops_per_token(DENSE_4096) within the agreed accounting."""
    cfg = config.MVPConfig()
    moe_flops = config.flops_per_token(cfg, arch="MOE")
    dense_flops = config.flops_per_token(cfg, arch="DENSE")

    # Strict parity per Req 11 / Req 19
    assert moe_flops == dense_flops, (
        f"MoE active FLOPs ({moe_flops}) must equal Dense 4096 FLOPs ({dense_flops})"
    )


# ---------------------------------------------------------------------------
# Package-level canonical name (Req 1: Naming And Alias Convention)
# ---------------------------------------------------------------------------


def test_canonical_name() -> None:
    """`decompmoe.__canonical_name__` must be the literal string "DecompMoE"."""
    assert decompmoe.__canonical_name__ == "DecompMoE"


def test_alias_preserved() -> None:
    """`decompmoe.__alias__` must be the literal string "GeoMoE" for documentation continuity."""
    assert decompmoe.__alias__ == "GeoMoE"
