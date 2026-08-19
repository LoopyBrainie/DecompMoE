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
    """compute_total_and_active(MVPConfig()) must agree with 452M / 100M within ±1%."""
    cfg = config.MVPConfig()
    total, active = config.compute_total_and_active(cfg)

    assert 448_000_000 <= total <= 456_000_000, (
        f"total {total} outside [448M, 456M] (expected ≈452M)"
    )
    assert 99_000_000 <= active <= 101_000_000, (
        f"active {active} outside [99M, 101M] (expected ≈100M)"
    )


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