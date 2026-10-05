"""5-phase time-driven schedule + 3-layer hybrid trigger (Req 14, 15).

Phase boundaries (Req 14 / A6b-1) for total_steps = 100_000:
    Phase 0 (SEEDING):       step ∈ [0,     999]
    Phase 1 (router freeze):  step ∈ [1K,   5_999]
    Phase 2 (expert freeze):  step ∈ [6K,  25_999]
    Phase 3 (β ramp 4→16):    step ∈ [26K, 55_999]
    Phase 4 (projected SGD):  step ∈ [56K,100_000]

Schedule-time β parameterization functions (skeleton "Beta Parameterization
Operational Domain"):
    - `gamma_reset_for_phase2()` — γ reset at phase-2 entry (constant 0.0).
    - `gamma_reset_for_phase4(beta_p3)` — γ reset at phase-4 entry.
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

from decompmoe.beta import BETA_MAX

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
    """Return the (lo, hi) dynamic box for β in the given phase.

    For MVP (Phase 1–4) the spec only pins boxes for Phase 2 `(1.0, 4.0)`
    and Phase 3 `(4.0, 16.0)`. The `return (1.0, 32.0)` fallback applies
    to phases the spec does not constrain (Phase 0 K-Means seeding, Phase 1
    `β^eff = 1.0` fixed, Phase 4 continuous reparameterization without a
    box clamp, and any future phase ≥ 5). MVP training flow does not hit
    this fallback; tests pin the static fallback for Phase 4
    (see `tests/test_schedule.py::test_phase4_b_dynamic_box`).
    """
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


def gamma_reset_for_phase2() -> float:
    """γ reset value placed at Phase-2 entry: exactly `0.0`.

    Rationale (Spec Req 24 "Phase-2 entry γ reset places β^param in the
    cap-saturated region" Scenario, per change
    `2026-10-04-phase2-gamma-reset-ramp-closure` design.md Decision 3):

        β^param(γ) = 0.1 + 31.9·σ(γ)
        β^param(0) = 0.1 + 31.9·0.5 = 16.05
        sup{phase_beta_max(3, step)} = phase_beta_max(3, 55_999) = 15.9996

    so `β^param(0) > cap(t)` across all of Phase 2 ∪ Phase 3 with margin
    `16.05 − 15.9996 = 5.04e-2`. The upper clamp therefore saturates for
    the whole of Phases 2–3 and `β^eff(step) ≡ phase_beta_max(phase, step)`
    pointwise — which is how Req 14's operational ramp `1.0 → 4.0` (Phase 2)
    and `4.0 → 16.0` (Phase 3) is delivered deterministically, by the
    schedule cap rather than by the value of `β^param`.

    Why `0.0` and not something closer to the saturation boundary: the exact
    threshold is `γ* = logit(0.49841943…) = −0.006319770250253427`, whose
    margin is `≈ 0` **by construction** — it is the boundary, not a safe
    operating point. The rounded literal `−0.006318` does saturate, but only
    by `1.41e-5` in exact arithmetic, so `0.0`'s margin of `5.04e-2` is
    `≈ 3574×` larger. (Note `logit(0.498420) = −0.006320021…` overshoots past
    `γ*` and does **not** saturate at all — margin `−2.0e-6`.) `γ = 0` is
    additionally the fixed point
    of decoupled weight decay, so in Phase 3 — where `phase_step_frozen_names(3)`
    is `{"c_i"}` and `beta_i` is therefore unfrozen — the weight-decay term
    drives an already-zero `γ` to zero and no extra momentum reset is needed.

    Structurally parallel to `gamma_reset_for_phase4`, which returns a
    closed-form value for the same reason (boundary continuity). This one is
    a constant because the saturation target is constant.
    """
    return 0.0


def gamma_reset_for_phase4(beta_p3: float = 16.0) -> float:
    """γ reset value placing β^eff exactly at the phase-3 exit value.

    Spec (skeleton "Beta Parameterization Operational Domain"): at phase-4
    entry the γ parameter is reset so that
    `phase4_inverse_temperature(γ_reset) == β_p3` (= 16.0 at MVP).
    Closed form: `γ_reset = ln(β_p3 − 1) − ln(β_max − β_p3)` where
    `β_max = 32` is the algorithmic ceiling (per `decompmoe.beta.BETA_MAX`,
    not MVPConfig);
    at β_p3 = 16 this evaluates to ln(15/16) ≈ −0.0645385.
    """
    return math.log(beta_p3 - 1.0) - math.log(BETA_MAX - beta_p3)


def beta_effective(
    gamma_p: float,
    phase: int,
    step: int,
    total_steps: int = _DEFAULT_TOTAL,
) -> Tensor:
    """Operational β^eff (per-phase formulas of wayfinder Req 24 Beta
    Parameterization Space vs Operational Domain (`#req-24`)).

    Spec declarations:
      Phase 1: β^eff = 1.0 (fixed, regardless of γ)              — Req 24 Phase 1 row
      Phase 2-3: Clamp(β^param(γ), 1.0, β_max(t))               — Req 24 Phase 2-3 row
                 where β^param(γ) = 0.1 + 31.9 · σ(γ)
      Phase 4:  β^eff = 1 + 31 · σ(γ')                          — Req 24 Phase 4 row
                 (γ' = γ_reset_for_phase4(β_p3)); no clamp.

    Signature is 3 positional args plus a defaulted `total_steps`, so that
    `total_steps` reaches `phase_beta_max` below. There is no dead `cfg` param
    (the constants β_min / β_max / 31 / 31.9 are module-level in
    `decompmoe.beta`).

    Contract (per change `2026-10-04-phase2-gamma-reset-ramp-closure`
    design.md Decision 2): this is a **schedule-layer helper** and is
    **non-differentiable by design**. `gamma_p: float` is converted with
    `torch.as_tensor` and the result is read back through `float(... .item())`,
    so the returned tensor is always a leaf with `requires_grad=False` and
    `grad_fn=None` — in every phase, Phase 4 included. A γ gradient path
    therefore cannot be obtained by calling this function with a Tensor; the
    differentiable primitives are `inverse_temperature` and
    `phase4_inverse_temperature` in `decompmoe.beta`, which the caller
    composes with the box. The caller-γ-free operational path is obtained by
    composing the same two primitives with the per-phase γ reset, i.e.
    `beta_effective(gamma_reset_for_phase2(), phase, step)` in Phase 2-3.

    Precision frame: `torch.as_tensor(<python float>)` adopts the torch
    default floating dtype, so the returned value is rounded to that dtype
    while `phase_beta_max` below computes in Python-float (float64)
    precision. The two agree exactly only for caps that are representable in
    both. Callers comparing against `phase_beta_max` must state which frame
    they are asserting in (see governance req-gov-1 obligation 4 on residual
    frame disambiguation).
    """
    from decompmoe.beta import (
        inverse_temperature,
        phase4_inverse_temperature,
    )

    if phase == 1:
        # Req 24 Phase 1 row: fixed 1.0 (γ-independent exploration phase).
        return torch.tensor(1.0)
    if phase in (2, 3):
        # Req 24 Phase 2-3 row: Clamp(β^param(γ), 1.0, β_max(t))
        beta_raw = inverse_temperature(torch.as_tensor(float(gamma_p)))
        cap = phase_beta_max(phase, step, total_steps)
        return torch.tensor(float(beta_raw.clamp(min=1.0, max=cap).item()))
    if phase == 4:
        # Req 24 Phase 4 row: 1 + 31 · σ(γ'); the γ' reset already places this
        # at β_p3 on entry, so no further clamp needed (spec does not
        # request one for Phase 4).
        beta_raw = phase4_inverse_temperature(torch.as_tensor(float(gamma_p)))
        return torch.tensor(float(beta_raw.item()))
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
    "gamma_reset_for_phase2",
    "gamma_reset_for_phase4",
    "beta_effective",
    "should_reset_adam",
    "advisory_signals",
]
