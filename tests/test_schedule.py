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


def test_phase_step_frozen_names_phase_0_and_4_empty_set() -> None:
    """Spec (wayfinder Req 14 / openspec/specs/decompmoe-skeleton/spec.md
    req-13 "Five-Phase Schedule State Machine"):
    phase_step_frozen_names returns `set()` for phases 0 and 4. Phase 0 =
    SEEDING has no gradient channel at all (wayfinder `#req-6` (Req 6 C Extraction Differentiability And Centroid Lifecycle):
    "Spherical K-Means seeding (no gradient, no EMA)"; phase table
    wayfinder `#req-27` (Req 27 CentroidDriver Dual-Channel Architecture Contract): `| 0 | K-Means seeding |
    Frozen (requires_grad=False) | N/A |`), so the freeze-name set is
    vacuously empty — this is NOT "everything frozen", which would instead
    be the FULL name set. Phase 4 = PROJECTED_SGD has full AdamW unfreeze
    with `c_i` gradient-channel Active.

    This pins the empty-set contract verbatim. A refactor that returned a
    NON-EMPTY set for phase 0 (implying an active gradient channel that the
    spec does not grant Phase 0) or a non-empty set for phase 4 (claiming
    "freeze c_i during projected SGD") would silently violate the
    dual-channel contract — the explicit assertion on `set()` (NOT
    `frozenset()`, NOT `None`) closes the gap.
    """
    actual_0 = schedule.phase_step_frozen_names(0)
    actual_4 = schedule.phase_step_frozen_names(4)
    assert actual_0 == set(), (
        f'phase 0 frozen-name set MUST be empty per skeleton req-13 '
        f'"Five-Phase Schedule State Machine" '
        f"(Phase 0 SEEDING has no gradient channel; vacuously empty); got {actual_0!r}"
    )
    assert actual_4 == set(), (
        f'phase 4 frozen-name set MUST be empty per skeleton req-13 '
        f'"Five-Phase Schedule State Machine" '
        f"(full AdamW unfreeze with c_i gradient-channel Active); got {actual_4!r}"
    )


def test_phase3_b_ramp() -> None:
    """Phase 3 ramp pins at canonical + boundary positions (closed-form abs=1e-9 per req-gov-1 §2)."""
    assert schedule.phase_beta_max(phase=3, step=26_000) == pytest.approx(4.0, abs=1e-9)
    assert schedule.phase_beta_max(phase=3, step=55_999) == pytest.approx(15.9996, abs=1e-9)
    assert schedule.phase_beta_max(phase=3, step=41_000) == pytest.approx(10.0, abs=1e-9)


def test_phase4_b_dynamic_box() -> None:
    """Float closed-form → `pytest.approx(abs=...)` per `governance/spec.md`
    req-gov-1 §2, because `phase_beta_box` returns floats.

    Disclosing the cost: `1.0` and `32.0` are BOTH exactly representable in
    IEEE-754 (`0x1.0000000000000p+0`, `0x1.0000000000000p+5`), so obligation 2's
    "carries floating-point rounding" rationale does not literally bite. The
    migration is compliance-driven and very slightly weaker than `==`
    (effective tolerance `max(1e-12, 1e-12·32) = 3.2e-11` at 32.0); its purpose
    is to stop one file carrying two rules for equally-typed constants.
    """
    lo, hi = schedule.phase_beta_box(4)
    assert lo == pytest.approx(1.0, abs=1e-12), f"actual lo={lo}"
    assert hi == pytest.approx(32.0, abs=1e-12), f"actual hi={hi}"


def test_adam_momentum_reset_on_phase4_entry() -> None:
    assert schedule.should_reset_adam(3, 4) is True
    assert schedule.should_reset_adam(2, 4) is False
    assert schedule.should_reset_adam(3, 3) is False
    assert schedule.should_reset_adam(0, 4) is False


def test_advisory_signals_read_only() -> None:
    """`advisory_signals` returns its arguments verbatim (pass-through stub).

    Left as bare `==` ON PURPOSE. `advisory_signals` is a keyword-only
    pass-through: it returns `R_H`/`S_load`/`R_beta_sat`/`L_sep_WB` unchanged
    (`src/decompmoe/schedule.py`), so this asserts an identity, not a
    spec-anchored closed-form value. Migrating it to `pytest.approx` would
    apply req-gov-1 §2 to a claim obligation 2 does not scope — the same
    misclassification that made ``tests/test_gating.py::test_zero_grad_for_non_top_k`` exempt in this change.

    Consequence, recorded honestly: the spec numbers this nominally guards
    are NOT guarded by this test. `wayfinder/spec.md` req-15 Layer 2 declares
    `WB = 0.0476` and a `> 2.0` severe-clustering threshold; neither appears
    anywhere in `src/` or `tests/`. req-15 Layer 2 is unimplemented and is
    registered as a hand-off in this change's proposal.
    """
    assert schedule.phase_id(5_000) == 1
    advisory = schedule.advisory_signals(
        R_H=0.99,
        S_load=0.99,
        R_beta_sat=0.99,
        L_sep_WB=0.99,
    )
    assert advisory["R_H"] == 0.99, f"actual={advisory['R_H']}"
    assert schedule.phase_id(5_000) == 1


# ---------------------------------------------------------------------------
# Task 3.3 — schedule-time functions (skeleton "Beta Parameterization
# Operational Domain"): gamma_reset_for_phase4 / phase_beta_max /
# beta_effective; phase_beta_box(2) == (1.0, 4.0)
# ---------------------------------------------------------------------------


def test_phase_beta_box_phase2_exact() -> None:
    """phase_beta_box(2) == (1.0, 4.0) exact — must NOT fall through to default.

    Float closed-form → `pytest.approx(abs=...)` per `governance/spec.md`
    req-gov-1 §2. Disclosing the cost: `1.0` and `4.0` are both exactly
    representable (`0x1.0p+0`, `0x1.0p+2`), so this is compliance-driven and
    marginally weaker than `==`; it is done to keep one rule per file.
    """
    lo, hi = schedule.phase_beta_box(2)
    assert lo == pytest.approx(1.0, abs=1e-12), f"actual lo={lo}"
    assert hi == pytest.approx(4.0, abs=1e-12), f"actual hi={hi}"


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
    # Boundary witness (Phase 2 last in-phase step, exclusive end) — symmetric
    # to the Phase-3 boundary witness in test_beta_effective_phase_4_continuity.
    assert schedule.phase_beta_max(2, 25_999) == pytest.approx(3.99985, abs=1e-9)


def test_gamma_reset_for_phase4_boundary_continuity() -> None:
    """gamma_reset_for_phase4(16.0) == ln(15/16); inverse recovers 16.0.

    Spec: skeleton "Beta Parameterization Operational Domain" — the γ reset
    at phase-4 entry places β^eff exactly at the phase-3 exit value 16.0.
    """
    g_reset = schedule.gamma_reset_for_phase4(16.0)
    assert g_reset == pytest.approx(math.log(15.0 / 16.0), abs=1e-4)
    # Spec req-26 ("Operational Domain γ' Reset Closed-Form Worked Example")
    # literal pin: `gamma_reset_for_phase4(16.0) ≈ -0.06454`, stated at 5-decimal
    # display precision. The assertion above re-derives the formula
    # (math.log(15/16)) and would pass for any implementation of the same
    # expression; this pins the spec's own 5-decimal value so a formula
    # regression surfaces directly.
    # Pinned by exact rounding at its own display precision, NOT by a widened
    # tolerance: the half-unit of a 5-decimal literal is 5e-6, and the previous
    # abs=1e-4 was 20x that — it accepted a reset wrong by 9e-5 outright.
    assert round(g_reset, 5) == -0.06454, (
        f"actual={g_reset}; round(gamma_reset_for_phase4(16.0), 5) must equal -0.06454"
    )
    beta_eff = beta.phase4_inverse_temperature(g_reset)
    assert beta_eff == pytest.approx(16.0, abs=1e-6), (
        f"actual={float(beta_eff)}; β^eff at phase-4 entry must equal 16.0"
    )


def test_beta_effective_phase_4_continuity() -> None:
    """β^eff at phase-4 entry == 16.0 exact; limit-continuity witness at
    phase-3 exit: phase_beta_max(3, 55_999) ≈ 15.9996.

    Spec: skeleton "Beta Parameterization Operational Domain" — the reset γ
    places β^eff exactly on the phase-3 ramp's limiting value; the linear
    convention with exclusive end gives the witness value
    4 + 12·(55_999−26_000)/(56_000−26_000) ≈ 15.9996.
    """
    g_reset = schedule.gamma_reset_for_phase4(beta_p3=16.0)
    assert schedule.beta_effective(g_reset, 4, 56_000).item() == pytest.approx(
        16.0, abs=1e-6
    )
    # Limit-continuity witness (exclusive end ⇒ last in-phase step).
    # Pinned by exact rounding at its own 4-decimal display precision: the
    # half-unit of a 4-dp literal is 5e-5, and the previous abs=1e-4 was
    # 2x that — the same over-wide form governance req-gov-1 already rejected
    # for the Voronoi `versine` literals.
    beta_max_last = schedule.phase_beta_max(3, 55_999)
    assert round(beta_max_last, 4) == 15.9996, (
        f"actual={beta_max_last}; round(phase_beta_max(3, 55_999), 4) must equal 15.9996"
    )
    # Spec req-29 "β^eff Phase 3 → 4 Continuity Closed-Form" literal bound pin:
    # |β_max(Phase 3, 55_999) − β^eff(Phase 4, 56_000)| < 5e-4.
    # Both endpoints are asserted above; this pins the *bound itself*, which was
    # previously unguarded (the two values could each drift and the claim would
    # silently become false).
    delta = abs(
        schedule.phase_beta_max(3, 55_999) - schedule.beta_effective(g_reset, 4, 56_000).item()
    )
    assert delta < 5e-4, (
        f"actual={delta} (spec req-29 requires "
        f"|β_max(3,55_999) − β^eff(4,56_000)| < 5e-4)"
    )


# ---------------------------------------------------------------------------
# Bug #1 + #2 — spec req-24 "Beta Parameterization Space vs Operational Domain"
# per-phase formula enforcement
# ---------------------------------------------------------------------------


def test_beta_effective_phase_1_fixed_one() -> None:
    """Phase 1 β^eff == 1.0 for ANY γ (wayfinder req-24 per-phase formula)."""
    import torch as _t

    _t.manual_seed(0)
    for gamma, step in [(0.0, 1_000), (-3.5, 3_000), (5.0, 5_999), (100.0, 100)]:
        v = schedule.beta_effective(gamma, phase=1, step=step).item()
        assert v == pytest.approx(1.0, abs=1e-9), (
            f"phase=1, γ={gamma}, step={step}: β^eff={v}, spec requires exactly 1.0"
        )


def test_beta_effective_phase_2_3_use_inverse_temperature() -> None:
    """Phase 2/3 use β^param(γ)=0.1+31.9·σ(γ) (NOT 1+31·σ(γ)).

    Trigger: γ=-5 saturates the clamp at the lower bound → β^eff must be 1.0.
    With the (wrong) phase-4 formula 1+31·σ(-5)≈1.208, this test fails.
    """
    v = float(schedule.beta_effective(-5.0, phase=2, step=16_000).item())
    # β^param(-5)=0.1+31.9·σ(-5)≈0.314 → Clamp(0.314, 1.0, 4.0) = 1.0
    assert v == pytest.approx(1.0, abs=1e-6), (
        f"phase=2, γ=-5: β^eff={v}, spec Clamp(β^param(-5), 1.0, 4.0) = 1.0"
    )
    v3 = float(schedule.beta_effective(-5.0, phase=3, step=41_000).item())
    # phase 3 cap at step 41_000 = 4 + 12·(41_000-26_000)/30_000 ≈ 10.0
    # lower-clamp still 1.0
    assert v3 == pytest.approx(1.0, abs=1e-6)


def test_beta_effective_phase_2_3_cap_binding() -> None:
    """Phase 3 cap-binding (γ=0, mid-phase): β^eff == phase_beta_max value.

    β^param(0) = 0.1+31.9·0.5 = 16.05
    cap at step 41_000 = 4 + 12·(41_000-26_000)/30_000 = 10.0
    ⇒ Clamp(16.05, 1.0, 10.0) = 10.0
    """
    v = float(schedule.beta_effective(0.0, phase=3, step=41_000).item())
    cap = schedule.phase_beta_max(3, 41_000)
    assert v == pytest.approx(float(cap), abs=1e-6), (
        f"γ=0 phase=3 step=41k: β^eff={v}, expected cap={cap}"
    )


# =====================================================================
# Req 24 γ-reset contract — change 2026-10-04-phase2-gamma-reset-ramp-closure
# =====================================================================


def test_gamma_reset_for_phase2_is_zero() -> None:
    """`gamma_reset_for_phase2()` is exactly `0.0`.

    Float closed form -> `pytest.approx(..., abs=...)` per governance req-gov-1
    §2; `abs=0` is forbidden. `1e-12` is the established tolerance for an
    exactly-representable constant in this repo (see the AC-44 default-budget
    assertions), not a widened one.
    """
    g = schedule.gamma_reset_for_phase2()
    assert g == pytest.approx(0.0, abs=1e-12), (
        f"actual={g!r}; gamma_reset_for_phase2() must be 0.0 "
        "(Req 24 Phase-2 entry gamma reset Scenario)"
    )


def test_saturation_margin_holds_in_float32_frame() -> None:
    """`β^param(0) > phase_beta_max(3, 55_999)` in the float32 operational frame.

    This test and `test_beta_effective_saturated_branch_is_bit_exact_with_float32_cap`
    are BOTH non-vacuous, but for different properties — do not read either as
    redundant:

    - The **bit-exact** test is the one that pins the *composition*: it calls
      `beta_effective` and therefore goes RED if the upper clamp is removed
      (with no clamp the function returns `β^param = 16.05`, which is not
      bit-equal to the cap `15.9996`). Verified by mutation.
    - This test pins the *inequality* — that the binding side is the clamp's
      UPPER bound. It never calls `beta_effective`, so on its own it would
      still hold for an implementation that applied no clamp at all. Its job is
      to make the direction of the inequality explicit and to keep the margin
      off the knife-edge, which is what lets the bit-exact test's
      "saturated branch" reading be sound rather than assumed.

        exact arithmetic:  β^param(0) = 0.1 + 31.9·σ(0) = 16.05
                          cap supremum  = phase_beta_max(3, 55_999) = 15.9996
                          margin         = 16.05 − 15.9996 = 0.0504
        float32 frame:    16.0499992      >   15.9996004    (margin 0.0503988)

    Both the strict inequality and the saturation identity are asserted with NO
    tolerance, in the frame the implementation actually runs in —
    `torch.as_tensor(<python float>)` adopts the torch default float dtype,
    so the clamp's `max` scalar is cast to float32 before it saturates. The
    float64 spec frame's 0.0504 is stated above as documentation; the
    representation offset between frames is measured in the Req 24 Scenario
    and is explicitly NOT used as a test tolerance.
    """
    import torch as _t

    _t.manual_seed(0)
    beta_param_f32 = beta.inverse_temperature(_t.as_tensor(0.0))
    cap_sup_f64 = schedule.phase_beta_max(3, 55_999)
    cap_sup_f32 = _t.tensor(cap_sup_f64, dtype=_t.float32)

    # Strict inequality, float32 frame, no tolerance.
    assert float(beta_param_f32) > float(cap_sup_f32), (
        f"actual β^param={float(beta_param_f32)} vs actual cap={float(cap_sup_f32)}; "
        "the upper clamp must saturate for the whole of Phase 3"
    )
    # The cap is computed in float64, so ITS 4-decimal display literal is pinned
    # by exact rounding at its own precision (governance req-gov-1 §2 exception;
    # the same pinning the Phase-4 continuity test already uses for this value).
    assert round(cap_sup_f64, 4) == 15.9996, (
        f"actual={cap_sup_f64}; round(phase_beta_max(3, 55_999), 4) must equal 15.9996"
    )
    # The float32 margin is not a knife-edge either. Documented magnitude, not a
    # pinned literal: a bare comparison, no tolerance.
    margin_f32 = float(beta_param_f32) - float(cap_sup_f32)
    assert margin_f32 > 0.05, (
        f"actual={margin_f32}; the float32 saturation margin should stay "
        "comfortably above 5e-2 (exact-arithmetic value 0.0504)"
    )


def test_beta_effective_saturated_branch_is_bit_exact_with_float32_cap() -> None:
    """Req 24: at the Phase-2 entry γ reset, `β^eff` is bit-identical to the
    float32 rendering of `phase_beta_max`, over the pinned phase grid.

    Guard form is `torch.equal` — bit-exact, **no tolerance, cannot be flaky**.
    `beta_effective` computes `Clamp(β^param_f32, 1.0, cap)`, and the clamp's
    `max` scalar is cast to float32, so the saturated branch returns exactly
    `float32(cap)`. The exact-arithmetic identity `β^eff ≡ phase_beta_max`
    holds by construction; this assertion pins its float32 realisation.

    A `pytest.approx(phase_beta_max(...), abs=1e-9)` in the float64 frame would
    be unsatisfiable by construction (the impl is float32) and would look
    stricter while being weaker. See the Req 24 Scenario for the frame
    declaration and the measured float64 offset.
    """
    import torch as _t

    _t.manual_seed(0)
    gamma_reset = schedule.gamma_reset_for_phase2()
    for phase, step in (
        (2, 6_000),
        (2, 13_000),
        (2, 25_999),
        (3, 26_000),
        (3, 41_000),
        (3, 55_999),
    ):
        got = schedule.beta_effective(gamma_reset, phase=phase, step=step)
        cap_f32 = _t.tensor(schedule.phase_beta_max(phase, step), dtype=_t.float32)
        assert _t.equal(got, cap_f32), (
            f"actual={float(got)} actual float32_cap={float(cap_f32)} "
            f"(phase={phase}, step={step}); the saturated branch must be bit-exact"
        )


def test_phase_beta_max_saturation_holds_across_the_whole_ramp_windows() -> None:
    """The Req 24 Scenario claims saturation for the WHOLE of Phase 2 ∪ Phase 3.

    The 6-point pinned grid only samples 6 steps, so it cannot see a defect
    *between* the samples. A sawtooth perturbation of `phase_beta_max`'s
    progress term that happens to preserve all 6 grid points leaves the grid
    test fully green. This test sweeps every step in both windows (stride 1) and
    pins the two properties the whole-phase claim actually rests on:

      1. `phase_beta_max` is **monotone non-decreasing in `step`** within each
         ramp window — this is what makes "the cap supremum is attained at the
         window's last step" a valid reduction rather than an assumption;
      2. `β^param(0)` is **strictly above the cap at every single step**, which
         is the substantive normative claim, in the float32 frame.

    Runtime is dominated by 50_000 pure-Python calls; measured well under a
    second.
    """
    import torch as _t

    _t.manual_seed(0)
    beta_param_f32 = float(beta.inverse_temperature(_t.as_tensor(0.0)))
    boundaries = schedule.phase_boundaries(100_000)  # (1000, 6000, 26000, 56000, 100000)

    for phase, lo_step, hi_step_exclusive in ((2, boundaries[1], boundaries[2]),
                                              (3, boundaries[2], boundaries[3])):
        prev_cap = float("-inf")
        first_violation = None
        non_monotone = None
        for step in range(lo_step, hi_step_exclusive):
            cap = float(_t.tensor(schedule.phase_beta_max(phase, step), dtype=_t.float32))
            if cap < prev_cap and non_monotone is None:
                non_monotone = (step, prev_cap, cap)
            if beta_param_f32 <= cap and first_violation is None:
                first_violation = (step, beta_param_f32, cap)
            prev_cap = cap
        assert non_monotone is None, (
            f"actual first non-monotone step={non_monotone!r} (phase={phase}); "
            "phase_beta_max must be monotone non-decreasing in step"
        )
        assert first_violation is None, (
            f"actual first unsaturated step={first_violation!r} (phase={phase}); "
            "beta^param(0) must strictly exceed the cap at EVERY step"
        )
        # The window's last IN-WINDOW step really is the attained cap supremum.
        # Note the ranges are END-EXCLUSIVE, so the box hi is approached but
        # not attained inside the window: Phase 2 tops out at
        # 1.0 + 3.0·(19999/20000) = 3.99985 (not 4.0), Phase 3 at
        # 4.0 + 12.0·(29999/30000) = 15.9996.
        if phase == 2:
            assert round(prev_cap, 4) == 3.9999, (
                f"actual={prev_cap}; the attained Phase 2 cap supremum must be "
                f"3.9999 (last in-window step={hi_step_exclusive - 1})"
            )
        else:
            assert round(prev_cap, 4) == 15.9996, (
                f"actual={prev_cap}; the attained Phase 3 cap supremum must be "
                f"15.9996 (last in-window step={hi_step_exclusive - 1})"
            )


def test_beta_effective_returns_leaf_tensor_in_every_phase() -> None:
    """Req 24: `beta_effective` MUST keep taking `gamma_p: float` and returning
    a leaf tensor — the differentiable primitives stay in `decompmoe.beta`.

    Guards the last AND-clause of the Req 24 gradient Scenario. Without this, a
    future refactor that "fixes" `beta_effective` to be differentiable would
    contradict both the spec text and the `schedule.py` docstring with nothing
    objecting. Phase 2/3 is incidentally covered by the value comparisons in
    other tests, but Phase 4 has **no** clamp and so no value-based tripwire;
    this is the only assertion that covers it.

    The second half also pins the silent part: handing in a `requires_grad=True`
    Tensor does not raise and does not propagate the graph. `float(gamma_p)`
    detaches it, so the caller gets a leaf without being told.
    """
    import torch as _t

    _t.manual_seed(0)

    for phase, step in ((1, 3_000), (2, 6_000), (3, 26_000), (4, 56_000)):
        out = schedule.beta_effective(0.0, phase=phase, step=step)
        assert out.requires_grad is False, (
            f"actual requires_grad={out.requires_grad} (phase={phase}, step={step}); "
            "beta_effective is a schedule-layer float helper, non-differentiable by design"
        )
        assert out.grad_fn is None, (
            f"actual grad_fn={out.grad_fn!r} (phase={phase}, step={step}); "
            "beta_effective MUST return a leaf tensor"
        )
        assert out.is_leaf, (
            f"actual is_leaf={out.is_leaf} (phase={phase}, step={step})"
        )

    # A Tensor input must be silently detached, not honoured and not rejected.
    # Phase 4 is the load-bearing case: it has no clamp, so a naive
    # implementation would happily thread the graph straight through. Phase 1
    # is the other edge — a constant, so a graph could not survive it either.
    for phase, step in ((1, 3_000), (2, 6_000), (3, 26_000), (4, 56_000)):
        grad_tensor = _t.tensor(0.0, requires_grad=True)
        out = schedule.beta_effective(grad_tensor, phase=phase, step=step)  # type: ignore[arg-type]
        assert out.grad_fn is None, (
            f"actual grad_fn={out.grad_fn!r} (phase={phase}, step={step}); "
            "passing a Tensor MUST NOT open a gradient path"
        )
        assert out.is_leaf, (
            f"actual is_leaf={out.is_leaf} (phase={phase}, step={step})"
        )
        assert grad_tensor.grad is None, (
            f"actual grad={grad_tensor.grad!r} (phase={phase}, step={step}); "
            "beta_effective MUST NOT populate .grad"
        )


def test_gamma_gradient_exists_only_from_phase_4() -> None:
    """Req 24: the gamma gradient path opens at Phase 4, not before.

    Composition is inlined here on purpose — no new production API. The
    primitives are `beta.inverse_temperature` (parameterisation space) and
    `beta.phase4_inverse_temperature` (Phase-4 operational domain); the
    schedule layer only supplies the box.

    Phase 2-3 (evaluated at the reset gamma, where the clamp saturates):
        ∂β^eff/∂γ = 0   (integer closed form -> bare `==`)
    Phase 4 (at the reset point gamma' = ln(15/16), no clamp):
        ∂β^eff/∂γ' = 31·σ'(γ') and σ(γ') = 15/31, so
        σ'(γ') = (15/31)(16/31) = 240/961 and
        ∂β^eff/∂γ' = 31·240/961 = 240/31 = 7.7419354838709677...

    Do NOT conflate with `7.75` (= 31·σ'(0), the γ' = 0 upper bound) or with
    `0.9077` (= 31.9·σ'(−3.5), a parameterisation-space quantity at γ_init).
    """
    import torch as _t

    _t.manual_seed(0)

    # --- Phase 2 / 3: upper-clamp saturation -> exactly zero gradient -------
    for phase, step in ((2, 6_000), (2, 25_999), (3, 26_000), (3, 55_999)):
        g = _t.tensor(schedule.gamma_reset_for_phase2(), requires_grad=True)
        beta_eff = beta.inverse_temperature(g).clamp(
            min=1.0, max=schedule.phase_beta_max(phase, step)
        )
        # grad_fn present AND grad == 0 together prove the zero comes from
        # clamp saturation, not from a severed autograd graph.
        assert beta_eff.grad_fn is not None, (
            f"actual grad_fn={beta_eff.grad_fn!r} (phase={phase} step={step}); "
            "composition severed the autograd graph"
        )
        beta_eff.backward()
        assert g.grad == 0, (
            f"actual={g.grad} (phase={phase}, step={step}); "
            "Req 24 requires ∂β^eff/∂γ ≡ 0 while the upper clamp saturates"
        )

    # --- Phase 4: no clamp -> the path exists and has the closed-form slope --
    g4 = _t.tensor(schedule.gamma_reset_for_phase4(16.0), requires_grad=True)
    beta_eff4 = beta.phase4_inverse_temperature(g4)
    assert beta_eff4.grad_fn is not None, (
        f"actual grad_fn={beta_eff4.grad_fn!r}; "
        "Phase-4 path must be differentiable (no clamp applies)"
    )
    beta_eff4.backward()
    # This single assertion already discriminates the three gradient quantities:
    # 240/31 = 7.7419355... is ~8.06e-3 away from 7.75 (the γ'=0 upper bound),
    # which is 8x the abs=1e-6 tolerance, and ~6.8 away from 0.9077 (the
    # parameterisation-space value at γ_init). An explicit `!= 7.75` assertion
    # was removed as tautological -- it is fully implied by this one and could
    # never fail. The distinction it documented is real and is kept as the
    # comment above and in the Req 24 Scenario's non-conflation clause.
    assert g4.grad == pytest.approx(240 / 31, abs=1e-6), (
        f"actual={g4.grad}; ∂β^eff/∂γ' at γ'=ln(15/16) is 31·σ'(γ') = 240/31, "
        f"which must be distinguishable from the γ'=0 bound 7.75 and from 0.9077"
    )
