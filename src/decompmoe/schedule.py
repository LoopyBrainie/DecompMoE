"""5-phase time-driven schedule + 3-layer hybrid trigger (Req 14, 15).

Phase boundaries (Req 14 / A6b-1) for total_steps = 100_000:
    Phase 0 (SEEDING):       step ∈ [0,     999]
    Phase 1 (router freeze):  step ∈ [1K,   5_999]
    Phase 2 (expert freeze):  step ∈ [6K,  25_999]
    Phase 3 (β ramp 4→16):    step ∈ [26K, 55_999]
    Phase 4 (projected SGD):  step ∈ [56K,100_000]

Schedule-time β parameterization functions (skeleton "Beta Parameterization
Operational Domain"):
    - `gamma_reset_for_phase4(β_exit)` — γ reset at phase-4 entry.
    - `phase_beta_max(phase, step)` — time-varying operational box hi.
    - `beta_effective(γ_p, phase, step)` — clamped operational β^eff.

3-layer hybrid trigger (Req 15 / A6b-2):
    Layer 1: time-driven hard cut at the boundaries.
    Layer 2: state-driven advisory signals (read-only).
    Layer 3: hard cutoff at 100_000 steps.
"""

from __future__ import annotations

import math
from typing import Final

import torch
from torch import Tensor

_DEFAULT_TOTAL: Final[int] = 100_000
_PHASE_RATIOS: Final[tuple[float, ...]] = (0.01, 0.05, 0.20, 0.30, 0.44)


def phase_boundaries(total_steps: int = _DEFAULT_TOTAL) -> tuple[int, ...]:
    """Return phase boundary timestamps for `total_steps`."""
    cumul = 0.0
    out: list[int] = []
    for ratio in _PHASE_RATIOS:
        cumul += ratio
        raw = cumul * total_steps
        if not math.isfinite(raw):
            raise ValueError(
                f"non-finite boundary: ratio={ratio}, total_steps={total_steps}"
            )
        try:
            out.append(int(round(raw)))
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"invalid boundary value: {raw!r}") from exc
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
    if phase == 2:
        return (1.0, 4.0)
    if phase == 3:
        return (4.0, 16.0)
    return (1.0, 32.0)


def phase_beta_max(phase: int, step: int, total_steps: int = _DEFAULT_TOTAL) -> float:
    """Time-varying β upper bound within a phase's dynamic box.

    Pinned linear convention (skeleton "Beta Parameterization Operational
    Domain"):

        phase_beta_max(phase, step) = box(phase).lo
            + (box(phase).hi − box(phase).lo) · (step − phase_start)
              / (phase_end − phase_start)

    with `phase_end` EXCLUSIVE: Phase 2 range [6_000, 26_000),
    Phase 3 range [26_000, 56_000). Other phases return the static box hi.
    """
    bounds = phase_boundaries(total_steps)
    lo, hi = phase_beta_box(phase)
    if phase == 2:
        t_start, t_end = bounds[1], bounds[2]
    elif phase == 3:
        t_start, t_end = bounds[2], bounds[3]
    else:
        return hi
    progress = max(0.0, min(1.0, (step - t_start) / (t_end - t_start)))
    return lo + (hi - lo) * progress


def gamma_reset_for_phase4(beta_exit: float = 16.0) -> float:
    """γ reset value placing β^eff exactly at the phase-3 exit value.

    Spec (skeleton "Beta Parameterization Operational Domain"): at phase-4
    entry the γ parameter is reset so that
    `phase4_inverse_temperature(γ_reset) == β_exit` (= 16.0 at MVP).
    Closed form: `γ_reset = ln(β_exit − 1) − ln(32 − β_exit)`;
    at β_exit = 16 this evaluates to ln(15/16) ≈ −0.0645385.
    """
    return math.log(beta_exit - 1.0) - math.log(31.0 + 1.0 - beta_exit)


def beta_effective(
    gamma_p: float,
    phase: int,
    step: int,
) -> Tensor:
    """Operational β^eff (spec Req 24 per-phase formulas, wayfinder L491-507).

    Spec declarations:
      Phase 1: β^eff = 1.0 (fixed, regardless of γ)              — line 495
      Phase 2-3: Clamp(β^param(γ), 1.0, β_max(t))               — line 496
                 where β^param(γ) = 0.1 + 31.9 · σ(γ)
      Phase 4:  β^eff = 1 + 31 · σ(γ')                          — line 497
                 (γ' = γ_reset_for_phase4(β_exit)); no clamp.

    Signature is exactly 3 args: no dead `cfg` param (the constants
    β_min / β_max / 31 / 31.9 are module-level in `decompmoe.beta`).
    """
    from decompmoe.beta import (
        inverse_temperature,
        phase4_inverse_temperature,
    )

    if phase == 1:
        # Spec line 495: fixed 1.0 (γ-independent exploration phase).
        return torch.tensor(1.0)
    if phase in (2, 3):
        # Spec line 496: Clamp(β^param(γ), 1.0, β_max(t))
        try:
            beta_raw = inverse_temperature(torch.as_tensor(float(gamma_p)))
            cap = phase_beta_max(phase, step)
            return torch.tensor(float(beta_raw.clamp(min=1.0, max=cap).item()))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid (gamma_p, phase, step): "
                             f"{gamma_p!r}, {phase}, {step}") from exc
    if phase == 4:
        # Spec line 497: 1 + 31 · σ(γ'); the γ' reset already places this
        # at β_exit on entry, so no further clamp needed (spec does not
        # request one for Phase 4).
        try:
            beta_raw = phase4_inverse_temperature(torch.as_tensor(float(gamma_p)))
            return torch.tensor(float(beta_raw.item()))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid gamma_p={gamma_p!r} in phase 4") from exc
    raise ValueError(f"unknown phase: {phase}")


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
    "phase_beta_max",
    "gamma_reset_for_phase4",
    "beta_effective",
    "should_reset_adam",
    "advisory_signals",
]
