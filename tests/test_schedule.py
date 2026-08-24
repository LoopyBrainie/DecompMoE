"""Tests for `decompmoe.schedule`: 5-phase scheduler + 3-layer trigger.

ST-11 / Req 14, 15.
"""
from __future__ import annotations

import math

import pytest

from decompmoe import beta, schedule


def test_phase_ratios_pure_function() -> None:
    bounds = schedule.phase_boundaries(total_steps=100_000)
    assert bounds == (1_000, 6_000, 26_000, 56_000, 100_000)


def test_phase_id_at_boundary() -> None:
    assert schedule.phase_id(0) == 0
    assert schedule.phase_id(999) == 0
    assert schedule.phase_id(1_000) == 1
    assert schedule.phase_id(5_999) == 1
    assert schedule.phase_id(6_000) == 2
    assert schedule.phase_id(25_999) == 2
    assert schedule.phase_id(26_000) == 3
    assert schedule.phase_id(55_999) == 3
    assert schedule.phase_id(56_000) == 4
    assert schedule.phase_id(100_000) == 4


def test_phase1_freeze_router() -> None:
    assert schedule.phase_step_frozen_names(1) == {"c_i", "beta_i", "W_K", "W_V", "b"}


def test_phase2_freeze_experts() -> None:
    """Phase 2 freezes gradient channel for (c_i, beta_i), not experts.

    Spec (wayfinder Req 14): Phase 2 unfreezes W_K/W_V/b so they train
    under the driver-channel EMA at α=0.95; c_i, beta_i stay gradient-
    channel frozen. The previous (incorrect) implementation froze the
    experts W_g/W_u/W_d, which violated the dual-channel architecture
    contract.
    """
    assert schedule.phase_step_frozen_names(2) == {"c_i", "beta_i"}


def test_phase3_freeze() -> None:
    """Phase 3 freezes gradient channel for `c_i` only; beta_i unfrozen.

    Spec (wayfinder Req 14 + archived `fix-openspec-doc-bugs` Decision 4):
    in Phase 3 the routing continues via driver-channel Masked Spherical
    EMA at α = 0.99 with operational β ramping 4 → 16. The β_i parameter
    needs gradient-channel Active to update, so only c_i stays frozen.
    """
    assert schedule.phase_step_frozen_names(3) == {"c_i"}


def test_phase3_b_ramp() -> None:
    assert schedule.phase_beta(phase=3, step=26_000) == 4.0
    assert abs(schedule.phase_beta(phase=3, step=55_999) - 16.0) < 1e-5
    mid = schedule.phase_beta(phase=3, step=41_000)
    assert 9.0 < mid < 11.0


def test_phase4_b_dynamic_box() -> None:
    lo, hi = schedule.phase_beta_box(4)
    assert lo == 1.0
    assert hi == 32.0


def test_adam_momentum_reset_on_phase4_entry() -> None:
    assert schedule.should_reset_adam(3, 4) is True
    assert schedule.should_reset_adam(2, 4) is False
    assert schedule.should_reset_adam(3, 3) is False
    assert schedule.should_reset_adam(0, 4) is False


def test_advisory_signals_read_only() -> None:
    assert schedule.phase_id(5_000) == 1
    advisory = schedule.advisory_signals(
        R_H=0.99,
        S_load=0.99,
        R_beta_sat=0.99,
        L_sep_WB=0.99,
    )
    assert advisory["R_H"] == 0.99
    assert schedule.phase_id(5_000) == 1

# ---------------------------------------------------------------------------
# Task 3.3 — schedule-time functions (skeleton "Beta Parameterization
# Operational Domain"): gamma_reset_for_phase4 / phase_beta_max /
# beta_effective; phase_beta_box(2) == (1.0, 4.0)
# ---------------------------------------------------------------------------


def test_phase_beta_box_phase2_exact() -> None:
    """phase_beta_box(2) == (1.0, 4.0) exact — must NOT fall through to default."""
    assert schedule.phase_beta_box(2) == (1.0, 4.0)


def test_phase_beta_max_is_time_varying() -> None:
    """phase_beta_max pins the linear convention with exclusive phase end.

    Spec: phase_beta_max(phase, step) = box.lo + (box.hi − box.lo)
          · (step − phase_start) / (phase_end − phase_start),
    Phase 2 range [6_000, 26_000), Phase 3 range [26_000, 56_000).
    Exact-value pins within abs=1e-9.
    """
    assert schedule.phase_beta_max(2, 6_000) == pytest.approx(1.0, abs=1e-9)
    assert schedule.phase_beta_max(2, 16_000) == pytest.approx(2.5, abs=1e-9)
    assert schedule.phase_beta_max(3, 26_000) == pytest.approx(4.0, abs=1e-9)
    assert schedule.phase_beta_max(3, 41_000) == pytest.approx(10.0, abs=1e-9)


def test_gamma_reset_for_phase4_boundary_continuity() -> None:
    """gamma_reset_for_phase4(16.0) == ln(15/16); inverse recovers 16.0.

    Spec: skeleton "Beta Parameterization Operational Domain" — the γ reset
    at phase-4 entry places β^eff exactly at the phase-3 exit value 16.0.
    """
    g_reset = schedule.gamma_reset_for_phase4(16.0)
    assert g_reset == pytest.approx(math.log(15.0 / 16.0), abs=1e-4)
    assert beta.phase4_inverse_temperature(g_reset) == pytest.approx(16.0, abs=1e-6)
