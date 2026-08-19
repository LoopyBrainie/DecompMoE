"""Tests for `decompmoe.schedule`: 5-phase scheduler + 3-layer trigger.

ST-11 / Req 14, 15.
"""
from __future__ import annotations

from decompmoe import schedule


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
    assert schedule.phase_step_frozen_names(2) == {"W_g", "W_u", "W_d"}


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