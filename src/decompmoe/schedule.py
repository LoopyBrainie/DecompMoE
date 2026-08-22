"""5-phase time-driven schedule + 3-layer hybrid trigger (Req 14, 15).

Phase boundaries (Req 14 / A6b-1) for total_steps = 100_000:
    Phase 0 (SEEDING):       step ∈ [0,     999]
    Phase 1 (router freeze):  step ∈ [1K,   5_999]
    Phase 2 (expert freeze):  step ∈ [6K,  25_999]
    Phase 3 (β ramp 4→16):    step ∈ [26K, 55_999]
    Phase 4 (projected SGD):  step ∈ [56K,100_000]

3-layer hybrid trigger (Req 15 / A6b-2):
    Layer 1: time-driven hard cut at the boundaries.
    Layer 2: state-driven advisory signals (read-only).
    Layer 3: hard cutoff at 100_000 steps.
"""
from __future__ import annotations

from typing import Final

_DEFAULT_TOTAL: Final[int] = 100_000
_PHASE_RATIOS: Final[tuple[float, ...]] = (0.01, 0.05, 0.20, 0.30, 0.44)


def phase_boundaries(total_steps: int = _DEFAULT_TOTAL) -> tuple[int, ...]:
    """Return phase boundary timestamps for `total_steps`."""
    cumul = 0.0
    out: list[int] = []
    for ratio in _PHASE_RATIOS:
        cumul += ratio
        out.append(int(round(cumul * total_steps)))
    return tuple(out)


def phase_id(step: int, total_steps: int = _DEFAULT_TOTAL) -> int:
    """Return phase id for the given global step."""
    bounds = phase_boundaries(total_steps)
    if step < bounds[0]:
        return 0
    for i in range(1, len(bounds)):
        if step < bounds[i]:
            return i
    return len(bounds) - 1


def phase_step_frozen_names(phase: int) -> set[str]:
    """Return the set of **gradient-channel** parameter-name suffixes to freeze per phase.

    Spec (wayfinder Req 14 + archived `fix-openspec-doc-bugs`): the
    frozen set freezes the gradient channel (AdamW) — the driver channel
    (CentroidDriver) remains Active and executes Masked Spherical EMA in
    Phases 1-3 regardless. Phase 2 freezes gradient for `(c_i, beta_i)`
    only — `W_K/W_V/b` are unfrozen so they can train under the driver-
    channel EMA at α = 0.95. Phase 3 freezes gradient for `(c_i)` only —
    `beta_i` is unfrozen so it can ramp via AdamW.
    """
    if phase == 1:
        return {"c_i", "beta_i", "W_K", "W_V", "b"}
    if phase == 2:
        return {"c_i", "beta_i"}
    if phase == 3:
        return {"c_i"}
    return set()


def phase_beta_box(phase: int) -> tuple[float, float]:
    """Return the (lo, hi) dynamic box for β in the given phase."""
    if phase == 3:
        return (4.0, 16.0)
    return (1.0, 32.0)


def phase_beta(phase: int, step: int, total_steps: int = _DEFAULT_TOTAL) -> float:
    """Return β value for (phase, step)."""
    bounds = phase_boundaries(total_steps)
    if phase == 1:
        return 1.0
    if phase == 2:
        t_start, t_end = bounds[1], bounds[2]
        span = t_end - t_start - 1
        progress = max(0.0, min(1.0, (step - t_start) / span)) if span > 0 else 0.0
        return 1.0 + 3.0 * progress
    if phase == 3:
        t_start, t_end = bounds[2], bounds[3]
        span = t_end - t_start - 1
        progress = max(0.0, min(1.0, (step - t_start) / span)) if span > 0 else 0.0
        return 4.0 + 12.0 * progress
    return 16.0


def should_reset_adam(prev_phase: int, next_phase: int) -> bool:
    """Return True iff `prev_phase == 3 and next_phase == 4`."""
    return prev_phase == 3 and next_phase == 4


def advisory_signals(
    *,
    R_H: float,
    S_load: float,
    R_beta_sat: float,
    L_sep_WB: float,
) -> dict[str, float]:
    """Layer-2 advisory signals (read-only; never triggers phase transitions)."""
    return {
        "R_H": R_H,
        "S_load": S_load,
        "R_beta_sat": R_beta_sat,
        "L_sep_WB": L_sep_WB,
    }


__all__ = [
    "phase_boundaries",
    "phase_id",
    "phase_step_frozen_names",
    "phase_beta_box",
    "phase_beta",
    "should_reset_adam",
    "advisory_signals",
]