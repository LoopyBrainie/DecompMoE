"""Tests for `decompmoe.sphere`: spherical L2 normalize + Voronoi self-consistency.

ST-03 / Req 5 (Steps 2 + 4), Req 11 (Voronoi self-consistency at β = 16).
"""

from __future__ import annotations

import inspect
import math

import pytest
import torch

from decompmoe import config
from decompmoe import extraction
from decompmoe import sphere

# ---------------------------------------------------------------------------
# Spherical L2 normalization (Req 5: ε-safety + idempotence)
# ---------------------------------------------------------------------------


def test_unit_sphere_invar() -> None:
    """spherical_l2_normalize maps every non-zero vector onto the unit sphere."""
    torch.manual_seed(0)
    z = torch.randn(64, 16)
    z_norm = sphere.spherical_l2_normalize(z)
    norms_sq = z_norm.pow(2).sum(dim=-1)
    assert torch.allclose(norms_sq, torch.ones_like(norms_sq), atol=1e-5)


def test_near_zero_numerically_safe() -> None:
    """At z = 0, the function must return finite values (no NaN/Inf)."""
    z = torch.zeros(8, 16)
    z_norm = sphere.spherical_l2_normalize(z)
    assert torch.isfinite(z_norm).all(), "zero-input must produce finite output"


def test_double_normalize_idempotent() -> None:
    """Applying the function twice is the same as applying it once."""
    torch.manual_seed(0)
    z = torch.randn(64, 16)
    once = sphere.spherical_l2_normalize(z)
    twice = sphere.spherical_l2_normalize(once)
    assert torch.allclose(once, twice, atol=1e-6)


# ---------------------------------------------------------------------------
# Voronoi self-consistency (Req 11: θ_Voronoi > θ_{1/e} ≈ 20.36°)
# ---------------------------------------------------------------------------


def test_no_hardcoded_table_values() -> None:
    """禁止性约束：`sphere.py` must NOT contain a hard-coded Voronoi table.

    Spec: skeleton "Voronoi Self-Consistency Threshold", Scenario
    "no hard-coded table values" — every input must bisect.
    """
    from pathlib import Path

    src = Path(sphere.__file__).read_text(encoding="utf-8")
    assert "_VORONOI_MVP_TABLE" not in src, (
        "sphere.py must not contain _VORONOI_MVP_TABLE (all inputs must bisect)"
    )


def test_voronoi_residual_below_1e_minus_9() -> None:
    """Bisection residual |0.5·I_{sin²θ}(7.5,0.5) − 1/N_e| < 1e-9 for N_e ∈ {16,17,64}.

    Spec: skeleton "Voronoi Self-Consistency Threshold", Scenario
    "N_e dependence of voronoi_angle" (residual < 1e-9).
    """
    for N in (16, 17, 64):
        theta = sphere.canonical_voronoi_angle(num_experts=N, signature_dim=16)
        s2 = math.sin(theta) ** 2
        residual = 0.5 * sphere._betainc_regularized(s2, (16 - 1) / 2.0, 0.5) - 1.0 / N
        assert abs(residual) < 1e-9, f"N_e={N}: residual {residual:.3e} ≥ 1e-9"


def test_voronoi_monotone_in_ne() -> None:
    """`canonical_voronoi_angle` is strictly decreasing across the N_e=16/17 boundary.

    Spec: skeleton "Voronoi Self-Consistency Threshold", Scenario
    "N_e dependence of voronoi_angle" — monotone continuity that the
    original table wrongly held at 52°. The test enforces the principle
    (closed-form equation residual < 1e-9 per spec) AND the monotone
    property, AND pins the bisection-6dp literals required by
    `governance/spec.md` req-gov-1 §3 (restored after `3dd1104` deleted them):
        N_e=16 → residual < 1e-9 AND θ == 1.173547 rad (abs=1e-6) AND θ_17 < θ_16
        N_e=17 → residual < 1e-9 AND θ == 1.165847 rad (abs=1e-6)
    """
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    theta_17 = sphere.canonical_voronoi_angle(num_experts=17, signature_dim=16)
    # Closed-form literal pins (governance req-gov-1 §3 — bisection-6dp literals).
    # These 6dp literals are the integrator's INDEPENDENT guard: they are
    # truncations of the canonical values, and at `abs=1e-6` they fail against
    # a defective integrator (measured 1.275e-6 at the pre-fix (16,16) output)
    # while passing against a conforming one (4.259e-7).
    #
    # The tolerance is NOT tightened, but the reason this comment used to give
    # was wrong and is corrected here. It claimed a 6dp literal carries
    # "truncation error up to 5e-7, so any bound below 1e-6 would fail on the
    # true value itself". A TRUNCATED 6dp literal's error is strictly below
    # 1e-6; 5e-7 is the round-half-up half-unit, not the truncation bound
    # (trunc6(0.9999999) = 0.999999 has error 9e-7, which exceeds 5e-7). So
    # 1e-6 is a defensible guard but NOT the minimum the 6dp display format
    # permits -- measured, abs=4.3e-7 already passes for 1.173547. Keeping
    # the wider guard is a stability choice, not a correctness limit.
    # (governance req-gov-1 obligation 3; measured on pytest 9.1.1, where
    # pytest.approx(expected, abs=T) has tolerance exactly T -- the rel default
    # is None, and the tolerance property returns before the max branch.)
    assert theta_16 == pytest.approx(1.173547, abs=1e-6), f"actual={theta_16}"
    assert theta_17 == pytest.approx(1.165847, abs=1e-6), f"actual={theta_17}"
    # Principle: each θ must solve the closed-form equation ½·I_{sin²θ}(7.5, ½) = 1/N_e
    # with residual < 1e-9 per `decompmoe-skeleton Req 6 Voronoi Self-Consistency Threshold (#req-6)`.
    for theta, N in ((theta_16, 16), (theta_17, 17)):
        s2 = math.sin(theta) ** 2
        residual = 0.5 * sphere._betainc_regularized(s2, 7.5, 0.5) - 1.0 / N
        assert abs(residual) < 1e-9, f"N_e={N}: residual {residual:.3e} ≥ 1e-9"
    # Monotone property (principle: more cells → smaller Voronoi half-angle).
    assert theta_17 < theta_16, "θ_Voronoi must be strictly monotone in N_e"


def test_voronoi_canonical_mvp_value() -> None:
    """`canonical_voronoi_angle(16, 16)` solves the closed-form equation.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    MVP self-consistency scenario: ½·I_{sin²θ}(7.5, ½) = 1/N_e exactly
    (via bisection; no table). The prior tabulated 0.9076 rad was wrong —
    the true root is ≈ 1.1735 rad (67.24°), independently confirmed.
    """
    theta = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # `decompmoe-skeleton Req 6 Voronoi Self-Consistency Threshold (#req-6)` 4dp display forms: `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`.
    assert round(theta, 4) == 1.1735, f"actual={theta} → round4={round(theta, 4)}"
    assert round(math.degrees(theta), 2) == 67.24, (
        f"actual_deg={math.degrees(theta)} → round2={round(math.degrees(theta), 2)}"
    )
    # Closed-form equation check at the returned angle (residual < 1e-9).
    s2 = math.sin(theta) ** 2
    residual = 0.5 * sphere._betainc_regularized(s2, 7.5, 0.5) - 1.0 / 16.0
    assert abs(residual) < 1e-9, f"residual {residual:.3e}"


def test_voronoi_canonical_N_e_dependence() -> None:
    """`canonical_voronoi_angle(64, 16)` solves the equation with its own root.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    Scenario `N_e dependence of voronoi_angle`. The function MUST depend
    on both arguments (N_e and d_c), not d_c alone. The test enforces the
    principle (closed-form equation residual < 1e-9 per spec) AND the
    monotone property, NOT a self-referential hard-coded literal:
        N_e=64 → residual < 1e-9 AND θ_64 < θ_16 (more cells → smaller angle)
    """
    theta_64 = sphere.canonical_voronoi_angle(num_experts=64, signature_dim=16)
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # Closed-form literal pin (governance req-gov-1 §3 — bisection-6dp literal).
    assert theta_64 == pytest.approx(1.020506, abs=1e-6), f"actual={theta_64}"
    # `decompmoe-skeleton Req 6 Voronoi Self-Consistency Threshold (#req-6)` 4dp display forms: `θ_Voronoi(64, 16) ≈ 1.0205 rad (≈ 58.47°)`.
    assert round(theta_64, 4) == 1.0205, f"actual={theta_64} → round4={round(theta_64, 4)}"
    assert round(math.degrees(theta_64), 2) == 58.47, (
        f"actual_deg={math.degrees(theta_64)} → round2={round(math.degrees(theta_64), 2)}"
    )
    # Principle: θ_64 must solve ½·I_{sin²θ}(7.5, ½) = 1/64 with residual < 1e-9.
    s2_64 = math.sin(theta_64) ** 2
    residual_64 = 0.5 * sphere._betainc_regularized(s2_64, 7.5, 0.5) - 1.0 / 64.0
    assert abs(residual_64) < 1e-9, f"N_e=64: residual {residual_64:.3e} ≥ 1e-9"
    # Must depend on N_e: (64, 16) strictly less than (16, 16).
    assert theta_64 < theta_16, (
        f"θ_Voronoi(64,16) = {theta_64:.4f} must be < θ_Voronoi(16,16) = {theta_16:.4f}"
    )


def test_canonical_voronoi_angle_not_arctan_shortcut() -> None:
    """`canonical_voronoi_angle` is the root of its defining equation, not `arctan(pi/sqrt(d_c))`.

    The closed form under test is specified by decompmoe-skeleton Req 6
    Voronoi Self-Consistency Threshold (`#req-6`); the guard for the forbidden
    substitution is the Scenario "Voronoi closed form is not the arctan
    shortcut" in decompmoe-skeleton Req 16 Centroid Driver Semantic Invariants
    (`#req-16`), which is where Req 15's two grep-scoped invariants were
    re-homed when they were removed from that Requirement.

    A short-lived token `arctan(pi/sqrt(d_c))` was moved out of grep scope
    without being replaced by a named guard, so nothing named the forbidden
    form: the 6dp literal pins discriminate against it (measured `5.078e-01`
    error at `N_e=16`) but never asserted its absence. This test closes that
    gap on three independent axes:

      1. the 6dp closed-form literal (float closed form, `abs=1e-6`);
      2. the defining-equation residual in the impl-internal frame
         (`x` first into `_betainc_regularized`; a residual near `0.44` means
         the argument order is wrong, not that the integrator is broken);
      3. the substitution itself — the shortcut misses by at least `1e5`
         tolerances, and the implementation's own source contains no
         inverse-trigonometric call at all.

    Axis 3 is the one that fails if someone edits `canonical_voronoi_angle` to
    return the shortcut: axes 1 and 2 would both catch it, but only after the
    value silently changed; the source check catches the substitution itself.
    """
    TOL = 1e-6
    N_E, D_C = 16, 16

    # --- 1. closed-form literal (governance req-gov-1 obl. 3, float closed form)
    theta = sphere.canonical_voronoi_angle(num_experts=N_E, signature_dim=D_C)
    assert theta == pytest.approx(1.173547, abs=TOL), f"actual={theta!r}"

    # --- 2. defining-equation residual, impl-internal frame -------------------
    # `0.5 * I_{sin^2(theta)}((d_c-1)/2, 0.5) == 1/N_e`; `_betainc_regularized`
    # takes (x, a, b), so the substitution `sin^2(theta)` MUST be first.
    residual = 0.5 * sphere._betainc_regularized(
        math.sin(theta) ** 2, (D_C - 1) / 2.0, 0.5
    ) - 1.0 / N_E
    assert abs(residual) < 1e-9, f"actual={residual!r} at theta={theta!r}"

    # --- 3. the forbidden substitution --------------------------------------
    shortcut = math.atan(math.pi / math.sqrt(D_C))
    assert theta != pytest.approx(shortcut, abs=TOL), (
        f"arctan(pi/sqrt(d_c)) substitution adopted as the closed form: "
        f"actual={theta!r} == {shortcut!r}"
    )
    error = abs(theta - shortcut)
    tolerances = error / TOL
    assert error >= 1e5 * TOL, (
        f"shortcut must miss by >= 1e5 tolerances of abs={TOL}; "
        f"actual error={error!r} ({tolerances:.1f} tolerances)"
    )
    # Measured, not merely bounded: the margin is ~5.1e5 tolerances at N_e=16.
    assert tolerances == pytest.approx(507_773.2, rel=1e-3), f"actual={tolerances!r}"

    # --- 3b. the implementation itself must not contain the shortcut ---------
    # `canonical_voronoi_angle` solves by bisection on the defining equation;
    # an inverse-trigonometric call anywhere in its body means the bisection
    # was bypassed, whatever the value happens to be.
    source = inspect.getsource(sphere.canonical_voronoi_angle)
    banned = [tok for tok in ("atan", "arctan", "acos", "asin", "sqrt") if tok in source]
    assert not banned, (
        f"canonical_voronoi_angle must solve by bisection on the defining "
        f"equation; found inverse-trig/radical token(s) {banned} in its source"
    )


def test_voronoi_self_consistency_against_1_e_boundary() -> None:
    """`canonical_voronoi_angle(16, 16) > θ_{1/e}(β=16) ≈ 20.36°`.

    Spec: wayfinder Req 11 self-consistency check
    (`θ_Voronoi(N_e=16, d_c=16) > θ_{1/e}(β=16) = arccos(15/16)`).
    Verifies the Voronoi cell is large enough to prevent specialist collapse.
    """
    theta_voronoi = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    theta_1_over_e = math.acos(15.0 / 16.0)  # arccos(1 − 1/β) at β=16
    assert theta_voronoi > theta_1_over_e, (
        f"θ_Voronoi = {math.degrees(theta_voronoi):.4f}° must exceed "
        f"θ_{{1/e}}(16) = {math.degrees(theta_1_over_e):.4f}°"
    )
    # wayfinder Req 11 4070 MVP Hyperparameter Set (`#req-11`) literal: `arccos(15/16) ≈ 20.36°` (float closed form → abs=1e-2 deg).
    assert math.degrees(theta_1_over_e) == pytest.approx(20.36, abs=1e-2), (
        f"actual={math.degrees(theta_1_over_e)}"
    )


def test_ct_decode_footprint_is_dtype_dependent() -> None:
    """wayfinder Req 16 Prefill And Decode Share The Same Algorithm (`#req-16`): Decode SRAM footprint of `C_t` is `16 floats = 64 bytes`
    per layer per token at `d_c = 16`.

    The spec states `16 floats` without naming an element type, so `64` bytes
    holds only for 4-byte floats. `extract_C` is dtype-TRANSPARENT: the output
    dtype follows the input dtype. This test therefore pins the property the
    spec actually implies and that any implementation must preserve:

      * footprint is `d_c * element_size()` of the tensor `extract_C` returns,
        not a hard-coded `d_c * 4`;
      * halving the input element type halves the footprint (32 bytes).

    The earlier form of this test fed float32 and asserted `dtype ==
    torch.float32`, which is true of every float32 torch pipeline and therefore
    could not fail for the scenario it described. Asserting transparency across
    dtypes does fail if `extract_C` ever starts casting.

    An earlier revision of this change pinned `float32` into the spec as a
    normative MUST. That pin was withdrawn: no spec statement establishes a
    compute dtype for `C_t`, and it contradicted req-18's BF16 regime
    (`W_proj ≈ 64 KB in BF16`). Deriving the element type is a hand-off.
    """
    cfg = config.MVPConfig()
    torch.manual_seed(0)
    B, N = 1, 1

    def _run(dtype: torch.dtype) -> torch.Tensor:
        K = torch.randn(B, cfg.H_kv, N, cfg.d_k, dtype=dtype)
        V = torch.randn(B, cfg.H_kv, N, cfg.d_k, dtype=dtype)
        W_K = torch.randn(cfg.H_kv, cfg.d_k, cfg.d_c, dtype=dtype) * 0.1
        W_V = torch.randn(cfg.H_kv, cfg.d_k, cfg.d_c, dtype=dtype) * 0.1
        b = torch.randn(cfg.H_kv, cfg.d_c, dtype=dtype) * 0.01
        return extraction.extract_C(
            K, V, W_K, W_V, b, H_kv=cfg.H_kv, d_c=cfg.d_c
        )

    # float32 reference: the 64-byte figure in the spec.
    C = _run(torch.float32)
    assert C.shape[-1] == cfg.d_c, f"actual C.shape={tuple(C.shape)}"
    bytes_fp32 = C.shape[-1] * C.element_size()
    assert bytes_fp32 == 64, f"actual={bytes_fp32}"
    assert C.element_size() == pytest.approx(4.0, abs=1e-12), (
        f"actual element_size={C.element_size()}"
    )

    # Dtype transparency: half-precision inputs stay half-precision, so the
    # footprint halves. This is what makes the spec's unqualified "64 bytes"
    # conditional, and it is a claim about the implementation, not a constant.
    C16 = _run(torch.float16)
    assert C16.dtype == torch.float16, (
        f"actual={C16.dtype} — extract_C is no longer dtype-transparent; the "
        f"Decode footprint would no longer follow the router compute dtype"
    )
    assert C16.shape[-1] * C16.element_size() == 32, (
        f"actual={C16.shape[-1] * C16.element_size()}"
    )
    Cbf = _run(torch.bfloat16)
    assert Cbf.dtype == torch.bfloat16, f"actual={Cbf.dtype}"
    assert Cbf.shape[-1] * Cbf.element_size() == 32, (
        f"actual={Cbf.shape[-1] * Cbf.element_size()}"
    )


_VORONOI_MC_5SIGMA_DEG = 7.31e-5
"""`5σ` of the Monte-Carlo mean returned by `voronoi_angle` at
`VORONOI_AREA_SAMPLES = 1_000_000`, at MVP (`d_c=16`, `N_e=16`).

The derivation MUST respect the exact constraint `Σ_i A_i ≡ 1`: each probe
is assigned to exactly one `argmax` owner, so `Σ_i n_i = M` identically and
`Σ_i ε_i ≡ 0` for `ε_i := A_i − 1/N_e`. The first-order term of
`θ̂ − G⁻¹(1/N_e)` therefore cancels EXACTLY, and the leading fluctuation is
second order, `(1/(2N_e))·g''·Σ_i ε_i²` with `g'' = [G⁻¹]'' = −G''/G'³`:

    G'(θ₀)   = 0.4884333     (θ₀ = canonical(16, 16) = 1.1735474259 rad)
    g''      = −24.6236
    Var(Σ ε_i²) ≈ 2·N_e·(A(1−A)/M)²        ⇒ spread scales as 1/M, not 1/√M
    SE       = |g''|·A(1−A)·√2 / (2·√N_e·M) = 1.461e-5 deg

Cross-checked empirically: the SD over 8 probe seeds at fixed `M` measures
`1.353e-5 deg` (spread `4.20e-5 deg`), i.e. the closed form and the sampler
agree to ~8%.

An earlier revision derived `5σ = 0.0355 deg` by treating the `N_e` cell
areas as independent. That ignores `Σ A_i ≡ 1` and is `486×` too large.

Derived per `openspec/specs/governance/spec.md` req-gov-1 obligation 7
(statistical-tolerance form): a gap smaller than this MUST NOT be read as
a real equal-area deviation.
"""


def _dup_centroids(d_c: int, copies: int) -> torch.Tensor:
    """`copies` exact duplicates of `e_1` plus `e_2 .. e_{d_c+1-copies}`.

    Duplicated sites are never the `argmax` owner, so this fixture also
    exercises the `area == 0` branch of `_cap_radius`.
    """
    eye = torch.eye(d_c)
    return torch.cat([eye[0:1].repeat(copies, 1), eye[1 : d_c + 1 - copies]], dim=0)


def _antipodal_cluster_centroids(d_c: int, spread: float) -> torch.Tensor:
    """An antipodal pair `±e_1` plus `d_c − 2` sites squeezed near `e_1`.

    No RNG: fully deterministic, so the measured gap is reproducible.
    """
    eye = torch.eye(d_c)
    tail = torch.cat(
        [spread * eye[2:d_c], torch.zeros(1, d_c)], dim=0
    )[: d_c - 2]
    tail = tail + 0.05 * eye[0:1].repeat(d_c - 2, 1)
    return torch.nn.functional.normalize(
        torch.cat([eye[0:1], -eye[0:1], tail], dim=0), dim=-1
    )


def _great_circle_centroids(n: int, d_c: int) -> torch.Tensor:
    """`n` equally spaced sites on one great circle of `S^{d_c − 1}`.

    Degenerate as a point set (it spans 2 of `d_c` dimensions) yet exactly
    equal-area: the cells are lunes, whose areas are proportional to their
    longitude spans.
    """
    ring = torch.zeros(n, d_c)
    for i in range(n):
        angle = 2.0 * math.pi * i / n
        ring[i, 0] = math.cos(angle)
        ring[i, 1] = math.sin(angle)
    return ring


def _cap_area_d2_closed_form(theta: float, d_c: int) -> float:
    """Analytic `G''(θ)` of the spherical cap-area function.

    From `G(θ) = ½·I_{sin²θ}((d_c−1)/2, ½)`:

        G'(θ)  = sin^(d_c−2)(θ) / B((d_c−1)/2, ½)
        G''(θ) = (d_c−2)·sin^(d_c−3)(θ)·cos(θ) / B((d_c−1)/2, ½)

    This is the ONLY trustworthy way to read the curvature. Do NOT replace it
    with a finite difference of `sphere._cap_area`: that helper integrates
    with a single 8-point Gauss–Legendre panel and no subdivision, and its
    numerical second difference develops a spurious sign change near
    `82°`–`88°` that has nothing to do with the shape of `G`.
    """
    a = (d_c - 1) / 2.0
    return (
        (d_c - 2)
        * math.sin(theta) ** (d_c - 3)
        * math.cos(theta)
        / math.gamma(a)
        / math.gamma(0.5)
        * math.gamma(a + 0.5)
    )


def test_voronoi_measurement_layer() -> None:
    """`voronoi_angle(centroids)` is COMMENSURABLE with the closed form.

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    measurement layer, which describes the function as computing the
    realised half-angle from an actual centroid tensor.

    This is the regression the superseded implementation could not catch.
    It averaged the chord over ALL `i<j` pairs and then fed the chord into
    the slot that expects a versine, so on this fixture it returned
    `113.9589°` against a canonical `67.2394°` — `0.8154 rad` away, which
    the old `abs(theta - canonical) < pi/2` bound happily admitted. The
    measurement layer now returns the mean per-cell equivalent-cap radius,
    which is commensurable with `canonical_voronoi_angle` by construction.

    The bound below is a COMMENSURABILITY bound, not a one-sidedness bound and
    not the estimator's noise floor. The true gap on this fixture is 0.0399°,
    which is ~2730x the estimator's `1.461e-5°` standard error — a real
    deviation, because this fixture's cells are genuinely not equal-area,
    just small in absolute terms. A 5σ bound would therefore be the wrong
    threshold (it rejects a real signal); the `0.2°` bound below instead
    states the property this test exists to protect, that the two quantities
    now live in the same neighbourhood. `0.2°` is 5x the true gap and 1.2x
    the estimator's `5σ = 7.31e-5°` x 2700, so it has ample headroom while
    still rejecting the superseded statistic. For direction-only checks see
    `test_voronoi_angle_one_sided_gap`.
    """
    torch.manual_seed(0)
    N_e, d_c = 16, 16
    # Generate a Fibonacci-sphere point set on S^2 and embed it in R^{d_c}.
    # NOTE: only the first 3 dimensions are populated, so this fixture has
    # effective rank 3 of d_c — it is an S^2 embedded in R^16, NOT a
    # distribution on S^{d_c - 1}. Its cells are therefore NOT equal-area,
    # which is exactly what makes the residual gap below non-zero.
    golden_ratio = (1.0 + 5.0**0.5) / 2.0
    pts = []
    for i in range(N_e):
        # Map Fibonacci sphere (defined on S^2) to higher dim via padding.
        z = 1.0 - (i / (N_e - 1)) * 2.0 if N_e > 1 else 0.0
        r = (1.0 - z * z) ** 0.5
        theta_sph = 2.0 * math.pi * i / golden_ratio
        # Embed in R^{d_c} using the first 3 dims (circular-symmetric).
        v = torch.zeros(d_c)
        v[0] = r * math.cos(theta_sph)
        v[1] = r * math.sin(theta_sph)
        v[2] = z
        pts.append(v)
    centroids = torch.stack(pts)
    centroids = torch.nn.functional.normalize(centroids, dim=-1)
    theta = sphere.voronoi_angle(centroids)
    assert 0.0 < theta < math.pi, f"voronoi_angle = {theta} rad must be in (0, π)"
    canonical = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    # Commensurability: the realised measure sits within 0.2 deg of the
    # equal-area ideal (true gap 0.0399 deg, so 5x headroom). The superseded
    # all-pairs statistic was 0.8154 rad (46.72 deg) away here — 234x this
    # bound, and it slipped past the previous, 5x looser 1.0 deg threshold
    # only because the looser bound was never actually applied to it.
    bound = math.radians(0.2)
    assert abs(theta - canonical) < bound, (
        f"realized θ̂ = {math.degrees(theta):.4f}° is {math.degrees(abs(theta - canonical)):.4f}° "
        f"from canonical {math.degrees(canonical):.4f}°, exceeding the 0.2° "
        f"commensurability bound; actual_delta_rad={abs(theta - canonical):.3e}"
    )


def test_voronoi_angle_known_answer_crosspolytope() -> None:
    """Known-answer witness for `voronoi_angle` — pins the exact value it returns.

    Input: the 32 crosspolytope vertices `±e_i` on S^15. Its 32 spherical
    facets are all congruent, so this is an **exactly equal-area** partition —
    the mathematical ideal a Voronoi-based measure is supposed to recognise.
    On it the superseded implementation and the closed form separated by
    53.12°:

        superseded `arccos(1 − mean_pairwise_chord)`   115.6651°
        its inversion defect, `arccos(1 − c²/2)`        91.5415°
        canonical_voronoi_angle(32, 16)                 62.5445°

    The measurement layer is now commensurable with the closed form, so the
    crosspolytope — the one configuration whose cells are exactly equal-area
    — returns the canonical angle. The tolerance is the estimator's own
    `5σ` (req-gov-1 obligation 7), not a closed-form `abs=1e-6`; the
    measured gap is 6.5e-5°.

    The second assertion is the regression guard that the old witness value
    made impossible: neither superseded output may come back.
    """
    torch.manual_seed(0)
    d_c = 16
    crosspolytope = torch.cat([torch.eye(d_c), -torch.eye(d_c)], dim=0)
    assert crosspolytope.shape == (32, d_c)

    theta = sphere.voronoi_angle(crosspolytope)
    assert math.degrees(theta) == pytest.approx(62.5444, abs=1e-3), (
        f"actual={math.degrees(theta)} deg — voronoi_angle's output on the "
        f"crosspolytope changed; if the formula was fixed on purpose, update "
        f"this witness together with the sphere.py docstring"
    )
    canonical = sphere.canonical_voronoi_angle(32, d_c)
    assert abs(theta - canonical) < math.radians(1e-3), (
        f"actual_delta_deg={math.degrees(abs(theta - canonical))} — the "
        f"crosspolytope is exactly equal-area, so the measurement must land "
        f"on the canonical angle"
    )
    # Regression guard: the two superseded outputs must not reappear. The
    # margins below are 20x and 5x their own numbers.
    for superseded, why in ((115.6651, "chord fed into the versine slot"), (91.5415, "all-pairs averaging")):
        assert abs(math.degrees(theta) - superseded) > 1.0, (
            f"actual={math.degrees(theta)} deg is back within 1 deg of the "
            f"superseded {superseded} deg value ({why})"
        )


def test_voronoi_angle_equal_area_witness_equal_area_configurations() -> None:
    """Exactly equal-area cell sets return exactly the canonical angle.

    Three independent constructions of an equal-area tessellation, all of
    which must satisfy `θ̂ ≈ canonical` within the estimator's `5σ`:

        `N_e=32` crosspolytope `±e_i` on S^15 — congruent facets
        `N_e=16` equally spaced on one great circle — congruent lunes
        `N_e=8`  equally spaced on one great circle — congruent lunes

    The great-circle cases matter because the point set is degenerate (it
    spans 2 of 16 dimensions) while the tessellation is still exactly
    equal-area, so this separates "the sites look spread out" from "the
    cells are equal-area" — the distinction a Voronoi measure must track.

    Tolerance `abs=1e-3` degrees is `13.7x` the derived `5σ = 7.31e-5 deg`
    and `23.8x` the measured cross-seed spread (`4.20e-5 deg`, 8 seeds), per
    req-gov-1 obligation 7. Measured gaps: 6.5e-5 / 1.0e-4 / 0.0 deg
    respectively.
    """
    torch.manual_seed(0)
    d_c = 16
    cases = (
        ("crosspolytope32", torch.cat([torch.eye(d_c), -torch.eye(d_c)], dim=0)),
        ("greatcircle16", _great_circle_centroids(16, d_c)),
        ("greatcircle8", _great_circle_centroids(8, d_c)),
    )
    for name, centroids in cases:
        N_e = centroids.shape[0]
        theta = sphere.voronoi_angle(centroids)
        canonical = sphere.canonical_voronoi_angle(N_e, d_c)
        assert math.degrees(theta) == pytest.approx(62.5444 if N_e == 32 else math.degrees(canonical), abs=1e-3), (
            f"actual={math.degrees(theta)} deg for {name} — an exactly "
            f"equal-area tessellation must reproduce the canonical angle"
        )
        assert abs(theta - canonical) < math.radians(1e-3), (
            f"actual_delta_deg={math.degrees(abs(theta - canonical))} for {name}"
        )


def test_voronoi_angle_not_degenerate_mean_area_form() -> None:
    """`voronoi_angle` MUST NOT be `G⁻¹(mean_i A_i)` — that form is a constant.

    Spherical Voronoi cell areas always sum to 1, so `mean_i A_i ≡ 1/N_e`
    for EVERY centroid set and `G⁻¹(mean_i A_i)` returns
    `canonical_voronoi_angle` unconditionally. Such an implementation
    reports perfect equal-area coverage for any input, including obviously
    broken ones, and is therefore useless as a self-consistency measure.

    Both fixtures below are wildly non-equal-area. Measured per-cell θ̂ vs
    the degenerate form: 40.3868° vs 67.2394° (26.85° apart) and 64.7660°
    vs 67.2394° (2.47° apart). The `1.0°` threshold is below the smaller
    separation and ~1.4e4x the estimator's `5σ = 7.31e-5°`.
    """
    torch.manual_seed(0)
    d_c = 16
    cases = (
        ("dup8_of_e1", _dup_centroids(d_c, 8), 1.0),
        ("antipodal_pair_plus_14", _antipodal_cluster_centroids(d_c, 0.02), 1.0),
    )
    for name, centroids, min_separation_deg in cases:
        N_e = centroids.shape[0]
        theta = sphere.voronoi_angle(centroids)
        canonical = sphere.canonical_voronoi_angle(N_e, d_c)
        separation_deg = math.degrees(canonical - theta)
        assert separation_deg > min_separation_deg, (
            f"actual_separation_deg={separation_deg} for {name} — the "
            f"degenerate G^-1(mean area) form returns the canonical angle for "
            f"every input and would give exactly 0 here"
        )


def test_voronoi_angle_one_sided_gap() -> None:
    """`canonical − θ̂ ≥ 0`: the equal-area deviation is one-sided.

    Under the precondition of `voronoi_angle`'s docstring — every cell smaller
    than a hemisphere, `∀i: A_i < 0.5`, which holds because `G` is strictly
    convex on all of `(0, π/2)` — `G⁻¹` is concave on the matching area
    interval `(0, 0.5)`, and Jensen gives `θ̂ ≤ G⁻¹(mean A) = canonical` with
    equality iff the cells are equal-area. Past a hemisphere the reflected
    branch takes over and the inequality is observed behaviour, not a
    theorem, so it is guarded here as a direction check.

    Fixtures are chosen so the true gap is tens of thousands of σ, which is
    what makes a strict `≥ 0` meaningful: a sign flip would be visible.
    Measured gaps: 26.8525°, 11.3372°, 2.4734° — i.e. `3.7e5σ`, `1.6e5σ`
    and `3.4e4σ` of `5σ = 7.31e-5°`. (An earlier revision quoted 756σ / 319σ
    / 70σ against a `5σ` of `0.0355°` that was `486×` too large.)
    """
    torch.manual_seed(0)
    d_c = 16
    cases = (
        ("dup8_of_e1", _dup_centroids(d_c, 8)),
        ("dup4_of_e1", _dup_centroids(d_c, 4)),
        ("antipodal_pair_plus_14", _antipodal_cluster_centroids(d_c, 0.02)),
    )
    for name, centroids in cases:
        N_e = centroids.shape[0]
        theta = sphere.voronoi_angle(centroids)
        canonical = sphere.canonical_voronoi_angle(N_e, d_c)
        gap_deg = math.degrees(canonical - theta)
        assert gap_deg >= 0.0, (
            f"actual_gap_deg={gap_deg} for {name} — the deviation "
            f"canonical − θ̂ must be one-sided and non-negative"
        )


def test_voronoi_angle_precondition_is_area_below_half() -> None:
    """The Jensen precondition of `voronoi_angle` is `∀i: A_i < 0.5`.

    `G(θ) = ½·I_{sin²θ}((d_c−1)/2, ½)` is STRICTLY CONVEX on all of
    `(0, π/2)`, so `G⁻¹` is concave on the whole matching area interval
    `(0, 0.5)` and the one-sided bound needs no per-`d_c` angle threshold.
    An earlier revision of this file asserted a `θ_conv(d_c)` convexity
    boundary at `81.3148° / 82.6036° / 83.7313°`, measured by central-
    differencing `sphere._cap_area`. Those numbers are an ARTEFACT of that
    helper's single-panel 8-point Gauss–Legendre quadrature, not a property
    of `G`; the assertions below are the regression guard against the claim
    returning.
    """
    # (1) G'' > 0 across the WHOLE open interval, at every pinned d_c.
    for d_c in (8, 16, 32):
        for deg in (0.5, 30.0, 60.0, 81.3148, 82.6036, 83.7313, 88.0, 89.5):
            g2 = _cap_area_d2_closed_form(math.radians(deg), d_c)
            assert g2 > 0.0, (
                f"actual_G''={g2} at {deg} deg, d_c={d_c}; G is strictly "
                f"convex on (0, pi/2) so this must be positive"
            )

    # (2) The retired per-d_c boundaries are NOT sign changes: the true G''
    # stays positive a full degree above each of them.
    for d_c, retired in ((8, 81.3148), (16, 82.6036), (32, 83.7313)):
        for deg in (retired + 1.0, retired + 5.0):
            g2 = _cap_area_d2_closed_form(math.radians(deg), d_c)
            assert g2 > 0.0, (
                f"actual_G''={g2} at {deg} deg, d_c={d_c}; the retired "
                f"theta_conv={retired} was a quadrature artefact, not a "
                f"convexity boundary"
            )

    # (3) The stated precondition actually holds for the equal-area witnesses.
    # Margin is 0.5/A = N_e/2, so the tightest case here is N_e=8 at 4.0x.
    d_c = 16
    for N_e in (8, 16, 32):
        canonical = sphere.canonical_voronoi_angle(N_e, d_c)
        A = sphere._cap_area(canonical, d_c)
        assert A == pytest.approx(1.0 / N_e, abs=1e-12), (
            f"actual_A={A} for N_e={N_e}; by definition canonical is the "
            f"cap whose area fraction is 1/N_e"
        )
        assert A < 0.5, (
            f"actual_A={A} for N_e={N_e}; the Jensen precondition is A < 0.5"
        )
        assert 0.5 / A == pytest.approx(N_e / 2.0, rel=1e-9), (
            f"actual_margin={0.5 / A} for N_e={N_e}; the margin to the "
            f"hemisphere ceiling is exactly N_e/2 at the equal-area ideal"
        )


def test_voronoi_angle_rejects_non_unit_centroids() -> None:
    """`centroids` MUST be unit-norm; otherwise the tessellation is silent-wrong.

    The owner of a probe is `argmax_i (p̂ · c_i)`. That selects the nearest
    site BY ANGLE only when every `‖c_i‖₂ = 1`; otherwise the inner product
    is scaled by `‖c_i‖₂`, so a far-but-long site can outrank a near-but-short
    one and the realised tessellation silently differs from the caller's
    intent. Rejecting beats absorbing.
    """
    d_c = 16
    good = _great_circle_centroids(8, d_c)

    scaled = good * 2.0
    with pytest.raises(ValueError, match="unit-norm"):
        sphere.voronoi_angle(scaled)

    mixed = good.clone()
    mixed[3] = mixed[3] * 1.5
    with pytest.raises(ValueError, match="unit-norm"):
        sphere.voronoi_angle(mixed)

    with pytest.raises(ValueError, match="row 3"):
        sphere.voronoi_angle(mixed)

    # The message must name the offending row so the caller can find it.
    with pytest.raises(ValueError) as exc:
        sphere.voronoi_angle(mixed)
    assert "row 3" in str(exc.value), f"actual_message={str(exc.value)}"


def test_voronoi_angle_honours_centroid_dtype() -> None:
    """`float64` centroids MUST work — a `float32`-only matmul is a regression.

    The superseded implementation paired `centroids @ centroids.T`, so both
    sides shared a dtype and a `float64` tensor worked. Rewriting the owner
    as `probes @ centroids.T` broke that, because the probe block is generated
    at the default `float32`: `RuntimeError: expected m1 and m2 to have the
    same dtype`. The probes are now cast to `centroids.dtype`, and the two
    dtypes MUST agree numerically.
    """
    d_c = 16
    centroids32 = _great_circle_centroids(8, d_c)
    centroids64 = centroids32.to(torch.float64)
    assert centroids64.dtype == torch.float64

    theta32 = sphere.voronoi_angle(centroids32)
    theta64 = sphere.voronoi_angle(centroids64)
    assert math.degrees(theta64) == pytest.approx(
        math.degrees(theta32), abs=1e-6
    ), (
        f"actual_float64={math.degrees(theta64)} deg vs "
        f"actual_float32={math.degrees(theta32)} deg; the dtype cast must not "
        f"change the result beyond float32 resolution"
    )


def test_voronoi_angle_reflected_cap_branch_n_e_2() -> None:
    """The `theta > pi/2` branch of the cap-area function is reachable and used.

    `_cap_area` has two branches; the small-cap one saturates at
    `G(pi/2) = 0.5`, so any cell holding more than half the sphere is only
    invertible through the reflected branch. `N_e = 2` is the case that
    reaches it — the bisector leaves each site with slightly more or less
    than half depending on the probe draw, so at least one cell exceeds 0.5.

    Two sites 20° apart are symmetric, so the two cells are near-equal and
    the mean lands on `canonical(2, 16) = 90.0°` exactly. That symmetry is
    precisely why the returned value CANNOT discriminate the branch — the
    degenerate `G⁻¹(mean_i A_i)` form returns the same `90.0°` here — so the
    branch guard below spies on `_cap_radius` and asserts that an area above
    the `G(π/2) = 0.5` ceiling was actually inverted, and that the radius it
    produced exceeded `π/2`.
    """
    d_c = 16
    b = torch.zeros(d_c)
    b[0] = math.cos(math.radians(20.0))
    b[1] = math.sin(math.radians(20.0))
    centroids = torch.stack([torch.eye(d_c)[0], b])

    generator = torch.Generator().manual_seed(sphere.VORONOI_AREA_SEED)
    probes = torch.nn.functional.normalize(
        torch.randn(sphere.VORONOI_AREA_SAMPLES, d_c, generator=generator), dim=-1
    )
    areas = torch.bincount(
        (probes @ centroids.T).argmax(dim=1), minlength=2
    ).to(torch.float64) / sphere.VORONOI_AREA_SAMPLES
    assert float(areas.max()) > 0.5, (
        f"actual_max_area={float(areas.max())} — this fixture is supposed to "
        f"drive one cell past the small-cap branch's G(pi/2) = 0.5 ceiling"
    )
    assert sphere._cap_area(math.pi, d_c) == pytest.approx(1.0, abs=1e-12), (
        f"actual={sphere._cap_area(math.pi, d_c)} — the reflected branch must "
        f"reach 1.0 at theta = pi"
    )

    # Spy on the public call path: record every (area, radius) pair inverted.
    seen: list[tuple[float, float]] = []
    real = sphere._cap_radius

    def _recording(area: float, dc: int) -> float:
        r = real(area, dc)
        seen.append((area, r))
        return r

    sphere._cap_radius = _recording
    try:
        theta = sphere.voronoi_angle(centroids)
    finally:
        sphere._cap_radius = real

    over = [(a, r) for a, r in seen if a > 0.5]
    assert over, (
        f"seen_areas={[a for a, _ in seen]} — no cell exceeded 0.5, so the "
        f"reflected branch was never exercised through voronoi_angle"
    )
    for a, r in over:
        assert r > math.pi / 2, (
            f"actual_radius={r} rad for area={a} (>0.5); the reflected branch "
            f"must invert past pi/2, the small-cap branch saturates at 0.5"
        )
    assert 0.0 < theta < math.pi, f"actual={theta} rad must be in (0, π)"


def test_voronoi_impl_output_within_1e6_of_exact_root() -> None:
    """Spec req-11: the impl bisection output stays within `1e-6 rad` of the
    exact equation root at both MVP `(N_e, d_c)` pairs, and the gap is a genuine
    non-zero quantity.

    Measured bias: `8.4878023e-7 rad` at `(16, 16)` and `8.7898467e-9 rad` at
    `(64, 16)`.

    The guard is deliberately a TWO-SIDED BOUND, not an equality against those
    measured values: the bias is a property of `sphere._betainc_regularized`'s
    quadrature, so pinning it exactly would turn any future accuracy
    *improvement* into a test failure. What the spec actually promises is the
    magnitude bound, plus that the impl output is not the exact root by
    coincidence (hence the strict `0 <` lower side).
    """
    import mpmath

    mpmath.mp.dps = 50

    def exact_root(n_e: int, d_c: int):
        def f(th):
            return (mpmath.mpf(0.5)
                    * mpmath.betainc(mpmath.mpf(d_c - 1) / 2, mpmath.mpf(0.5),
                                    0, mpmath.sin(th) ** 2, regularized=True)
                    - mpmath.mpf(1) / n_e)

        lo, hi = mpmath.mpf("0.3"), mpmath.mpf("1.55")
        assert f(lo) < 0 < f(hi), f"bracket failed: f(lo)={f(lo)}, f(hi)={f(hi)}"
        for _ in range(400):
            mid = (lo + hi) / 2
            if f(mid) > 0:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2

    for n_e in (16, 64):
        theta_impl = mpmath.mpf(
            sphere.canonical_voronoi_angle(num_experts=n_e, signature_dim=16)
        )
        bias = abs(theta_impl - exact_root(n_e, 16))
        assert 0 < bias < mpmath.mpf("1e-6"), f"actual={float(bias)}"

def test_versine_voronoi_closed_form() -> None:
    """Audit findings MAJ-M1 / MAJ-M2: versine_Voronoi closed-form values.

    versine_Voronoi(N_e, d_c) = 1 − cos(canonical_voronoi_angle(N_e, d_c))
    MUST NOT be confused with D_chord = √(2(1 − cos θ)) per `wayfinder Req 7 Isotropic Squared-Chord Distance And Bounded Beta (#req-7)`.
    The test enforces the versine principle via the bisection residual
    < 1e-9 on the underlying angle, the spec's 4dp `versine` literals
    (`0.6131` / `0.4771`, `decompmoe-skeleton Req 6 Voronoi Self-Consistency Threshold (#req-6)`-L237), and the identity assertions on
    the closed-form definition.

    Note: the literal pins below were restored by change
    `fix-review-findings-voronoi-precision-and-lineage` after `3dd1104`
    replaced them with a tautological `X == X` self-check (where `v_16_16`
    was DEFINED as the right-hand side of the assertion, so it could never
    fail — vacuous per `CLAUDE.md` §6 第 8 条).
    """
    # Step 1: derive canonical angles (must solve bisection residual < 1e-9).
    for N in (16, 64):
        theta = sphere.canonical_voronoi_angle(num_experts=N, signature_dim=16)
        s2 = math.sin(theta) ** 2
        residual = 0.5 * sphere._betainc_regularized(s2, 7.5, 0.5) - 1.0 / N
        assert abs(residual) < 1e-9, f"N_e={N}: residual {residual:.3e} ≥ 1e-9"
    # Step 2: versine principle — versine ≡ 1 − cos(θ) (identity assertion
    # on the closed-form definition itself).
    v_16_16 = 1.0 - math.cos(sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16))
    v_64_16 = 1.0 - math.cos(sphere.canonical_voronoi_angle(num_experts=64, signature_dim=16))
    # Step 2b: `wayfinder` `#req-10` (Territory Seeding Deferred Contract) 4dp `versine` literal pins. A
    # 4-decimal spec display value is guarded by EXACT `round(v, 4) == literal`,
    # per `decompmoe-skeleton` req-6 (same rule as `round(θ, 4) == 1.1735`),
    # NOT by a widened `pytest.approx` tolerance.
    assert round(v_16_16, 4) == 0.6131, f"actual={v_16_16}"
    assert round(v_64_16, 4) == 0.4771, f"actual={v_64_16}"
    # Step 2c: the deviation the `round()` decision rests on. `governance`
    # req-gov-1's bisection-Voronoi Scenario states both deviations, so per
    # CLAUDE.md §6 they are pinned numerically here rather than only described
    # in prose. Quoted to 6 significant figures with a matching `abs=1e-10`
    # (the 6th significant figure of a ~1e-5 quantity sits at the 1e-10 place).
    # The load-bearing spec claim is the strict bound below, not the digits.
    dev_16_16 = abs(v_16_16 - 0.6131)
    dev_64_16 = abs(v_64_16 - 0.4771)
    # These two deviations are functions of theta, so they move when the
    # integrator is corrected (change 2026-10-02-fix-canonical-literal-
    # residual-frame-and-dead-guard). The 4dp literals and the strict 5e-5
    # half-unit bound below are what the spec actually pins; these digits
    # only document where each value sits inside that bound.
    assert dev_16_16 == pytest.approx(1.70583e-5, abs=1e-10), f"actual={dev_16_16!r}"
    assert dev_64_16 == pytest.approx(3.40146e-5, abs=1e-10), f"actual={dev_64_16!r}"
    assert dev_16_16 < 5e-5 and dev_64_16 < 5e-5, (
        f"both deviations MUST be strictly below the 4dp half-unit 5e-5, "
        f"which is what makes round(v, 4) a decision on the display form; "
        f"actual=({dev_16_16:.6e}, {dev_64_16:.6e})"
    )
    # Step 3: versine MUST NOT be chord distance (per `wayfinder` `#req-10`
    # definitional layer, which forbids conflating versine with D_chord).
    # versine ∈ [0, 1]; chord ∈ [0, 2]. Sanity check at MVP scale.
    assert 0 < v_16_16 < 1, f"versine_Voronoi(16,16) = {v_16_16:.4f} must be in (0, 1)"
    assert 0 < v_64_16 < 1, f"versine_Voronoi(64,16) = {v_64_16:.4f} must be in (0, 1)"


# ---------------------------------------------------------------------------
# max(‖z‖, ε) formula monotonicity (skeleton spec Req "Spherical L2
# Normalization" Scenario "Output norm bounded by [1 − 2ε, 1]").
# ---------------------------------------------------------------------------


def test_sphere_norm_clipped_to_one_in_z_norm() -> None:
    """`spherical_l2_normalize` output norm is `1.0` for `‖z‖₂ ≥ ε`, `0` for `z = 0`.

    Spec: skeleton "Spherical L2 Normalization" Scenario "Output norm
    bounded by [1 − 2ε, 1]". The new formula `z / max(‖z‖₂, ε)` yields:
    - `z = 0` → `0 / ε = 0` (finite)
    - `‖z‖₂ ≥ ε` → `‖out‖₂ = ‖z‖₂ / ‖z‖₂ = 1.0` exactly (clamped to 1)
    Verified for `‖z‖₂ ∈ {0.0, 0.5, 1.0, 2.0, 5.0}` → `‖out‖₂` follows
    `{0.0, 1.0, 1.0, 1.0, 1.0}` (exactly 1.0 once ‖z‖₂ ≥ ε; the function
    IS monotone non-decreasing — `f(‖z‖) = ‖z‖/max(‖z‖,ε)` is monotone
    on `[0, ∞)` with `f(0)=0` and `f(‖z‖) ≡ 1` for `‖z‖ ≥ ε`). This
    guards the closed-form invariant.
    """
    eps = 1e-6
    test_norms = [0.0, 0.5, 1.0, 2.0, 5.0]
    expected_out_norms = [0.0, 1.0, 1.0, 1.0, 1.0]  # 1.0 once ‖z‖₂ ≥ ε
    out_norms: list[float] = []
    for z_norm in test_norms:
        z = torch.zeros(1, 16)
        z[0, 0] = z_norm
        out = sphere.spherical_l2_normalize(z, eps=eps)
        out_norms.append(out.norm().item())
    for actual, target in zip(out_norms, expected_out_norms):
        assert actual == pytest.approx(target, abs=1e-6), (
            f"max(‖z‖, ε) formula: ‖out‖₂ = {actual}, expected {target}"
        )


def test_sphere_norm_sub_epsilon_idempotence_breakdown() -> None:
    """Idempotence BREAKDOWN in the sub-ε regime `0 < ‖z‖₂ < ε`.

    Spec: skeleton "Spherical L2 Normalization" Idempotence Scenario
    `AND WHEN` clause — the function is NOT idempotent in the sub-ε regime.
    First application: `‖out‖₂ = ‖z‖₂ / ε < 1` (sub-unit). Second
    application: the output now has `‖·‖₂ = ‖z‖₂ / ε ≥ ε` (since
    `‖z‖₂ ≥ ε`), so the denominator is `max(‖z‖₂/ε, ε) = ‖z‖₂/ε` and
    the output normalizes back to `1.0` — breaking idempotence.

    Guards the spec contract: future refactors that restore `+ ε` (making
    the function idempotent everywhere) would silently regress this
    contract.
    """
    eps = 1e-6
    z_norm = 0.5 * eps  # strictly sub-ε
    z = torch.zeros(1, 16)
    z[0, 0] = z_norm

    once = sphere.spherical_l2_normalize(z, eps=eps)
    twice = sphere.spherical_l2_normalize(once, eps=eps)

    once_norm = once.norm().item()
    assert once_norm == pytest.approx(0.5, abs=1e-6), (
        f"first ‖out‖₂ = {once_norm}, expected 0.5 (= ‖z‖₂/ε)"
    )
    twice_norm = twice.norm().item()
    assert twice_norm == pytest.approx(1.0, abs=1e-6), (
        f"second ‖out‖₂ = {twice_norm}, expected 1.0 (idempotence breakdown)"
    )
    assert once_norm != twice_norm, (
        "function MUST not be idempotent in sub-ε regime per spec AND WHEN"
    )
# ---------------------------------------------------------------------------
# d_c = 2 affine degeneration
# (Req 6 Scenario: `d_c = 2 affine degeneration`)
#
# Exactly: `G(θ) = θ/π` on `(0, π/2]`, so `G'' ≡ 0`, `G` is affine, and the
# strict-convexity premise of the one-sidedness bound degenerates to an
# identity — the bound is no longer a theorem there.
#
# HISTORY. This test used to pin a TWO-SIDED DEVIATION BAND of 3.63%–6.52%,
# on the diagnosis that at `d_c = 2` the integrand `u^(a−1)` has
# `a = (d_c−1)/2 = ½`, i.e. `u^(−1/2)` — a square-root singularity at the
# single panel's LEFT endpoint, the mirror image of its `x → 1` failure.
# That diagnosis was correct and the defect is now GONE: the `t = sin²φ`
# substitution gives integrand `2·sin^(2a−1)φ·cos^(2b−1)φ`, and at `d_c = 2`
# the exponent is `2a−1 = 0` — the singularity is removed EXACTLY, not
# approximated away. The adaptive 8/16-point rule is belt-and-braces on top.
#
# WHAT SURVIVES is not a quadrature residual but an ARGUMENT-conditioning
# gap. The implementation evaluates `G` at `x = sin²θ`; that `x` carries an
# absolute float64 error ~1.1e-16, which `1 − x` inherits in full near
# `θ → π/2`, and `G`'s sensitivity to `x` there is `~1/(2·sqrt(1−x))`. So
# comparing `G(sin²θ)` against `θ/π` amplifies the rounding of `sin²θ` by
# `1/sqrt(1−x)`, while comparing against exact `G` AT THE SAME FLOAT x` does
# not. Hence two separate assertions below:
#   (b1) the integrator's own accuracy, measured at the argument it consumed
#        — FLAT at ≤ 3.3e-16 across the whole sweep;
#   (b2) the cross-parameterization band — grows to 7.60e-11 at 89.99999°.
# Same rationale as the impl-vs-true test higher up in this file.
# ---------------------------------------------------------------------------


def test_cap_area_dc2_affine_degeneration() -> None:
    """`G(θ) = θ/π` exactly at d_c = 2; the impl now attains it to 3.2e-16."""
    import mpmath

    mpmath.mp.dps = 50

    # The identity is exact in real arithmetic, but mpmath can only CONFIRM it
    # to its working precision, so these are float closed forms and get a
    # tolerance tied to `dps` — not a bare `==`. At dps=50 the two sides agree
    # to ~50 significant digits and differ only in the last ulp, so a bare `==`
    # would fail for a reason that has nothing to do with the mathematics.
    tol = mpmath.mpf(10) ** (-(mpmath.mp.dps - 5))  # 1e-45

    # (a) the exact identity, established WITHOUT the implementation
    for deg in (1.0, 5.0, 20.0, 37.0, 60.0, 89.0):
        th = mpmath.radians(mpmath.mpf(deg))
        exact = mpmath.mpf(0.5) * mpmath.betainc(
            mpmath.mpf(1) / 2,
            mpmath.mpf(1) / 2,
            0,
            mpmath.sin(th) ** 2,
            regularized=True,
        )
        want = th / mpmath.pi
        assert abs(exact - want) < tol, (
            f"actual_I={mpmath.nstr(exact, 20)} at {deg} deg; for d_c=2 the "
            f"identity is exactly theta/pi = {mpmath.nstr(want, 20)}"
        )

    # (a2) hence G(θ) = 1/N_e solves to θ = π/N_e
    for n_e in (2, 4, 8, 16, 32):
        th = mpmath.pi / n_e
        g = mpmath.mpf(0.5) * mpmath.betainc(
            mpmath.mpf(1) / 2,
            mpmath.mpf(1) / 2,
            0,
            mpmath.sin(th) ** 2,
            regularized=True,
        )
        assert abs(g - mpmath.mpf(1) / n_e) < tol, (
            f"actual_G(pi/{n_e})={mpmath.nstr(g, 20)}; at d_c=2 the exact root "
            f"of G(θ)=1/{n_e} is θ=π/{n_e}"
        )

    # (b) the sweep both residuals below are measured over. It reaches 89°
    #     and then keeps going, because the cross-parameterization residual
    #     (b2) is monotone in 1/sqrt(1-x) and only shows its structure near
    #     the degenerate end.
    sweep = (1.0, 20.0, 37.0, 60.0, 81.34, 89.0, 89.9, 89.999, 89.99999)

    # (b1) the INTEGRATOR's accuracy, measured at the identical float argument
    # the implementation actually consumed. This is what the `t = sin^2(phi)`
    # substitution plus adaptive subdivision are responsible for, and it is
    # FLAT: every point of the sweep, including 89.99999 deg, lands within
    # 3.3e-16 of exact `G` at that same `x` — i.e. at the float64 noise floor.
    for deg in sweep:
        th = math.radians(deg)
        x = math.sin(th) ** 2
        impl = sphere._cap_area(th, 2)
        exact_at_x = mpmath.mpf(0.5) * mpmath.betainc(
            mpmath.mpf(1) / 2,
            mpmath.mpf(1) / 2,
            0,
            mpmath.mpf(x),
            regularized=True,
        )
        dev = abs(mpmath.mpf(impl) - exact_at_x)
        assert dev < mpmath.mpf("1e-14"), (
            f"actual_abs_dev_at_same_x={mpmath.nstr(dev, 6)} at {deg} deg "
            f"(impl={impl!r}, x={x!r}); the adaptive quadrature must stay below "
            f"1e-14 at the argument it actually consumed (measured max 3.3e-16)"
        )

    # (b2) the CROSS-PARAMETERIZATION band: `G` evaluated at `x = sin²θ`
    # versus `θ/π` evaluated at `θ`. The two are the same number in exact
    # arithmetic, but see the block comment: in float64 the gap is the
    # rounding of `sin²θ` amplified by `1/sqrt(1-x)`, not a quadrature
    # residual. Pre-fix this band was 3.63%–6.52% (the `u^(-1/2)` endpoint
    # singularity); what is left is the conditioning floor, 7.60e-11 at the
    # last sweep point.
    for deg in sweep:
        th = math.radians(deg)
        impl = sphere._cap_area(th, 2)
        want = th / math.pi
        rel = abs(impl - want) / want
        assert 0.0 <= rel <= 8e-11, (
            f"actual_rel_dev={rel:.6e} at {deg} deg (impl={impl!r}, "
            f"closed_form={want!r}); what remains of the deviation is the "
            f"float64 conditioning of x = sin^2(theta) amplified by "
            f"1/sqrt(1-x), bounded at 8e-11 over the open interval (0, 90) "
            f"deg. Exceeding it means either the quadrature regressed — in "
            f"which case (b1) above fails first — or the 1/sqrt(1-x) "
            f"conditioning account of this residual is wrong"
        )

    # (b3) the canonical angle against the exact root `theta = pi / N_e`.
    # N_e = 2 is deliberately EXCLUDED, for the same reason as before: it
    # targets area exactly 0.5, so bisection lands on the `x >= 1.0`
    # early-return plateau at pi/2 (see the F9 test below) rather than on a
    # quadrature result.
    #
    # The disclosed structure is now a BISECTION limit rather than a
    # quadrature one. The ABSOLUTE deviation is flat at ~4.46e-14 — the
    # `break < 1e-13` convergence test in `canonical_voronoi_angle` — so the
    # RELATIVE deviation is exactly proportional to N_e, because
    # `rel = abs_dev / (pi / N_e) = abs_dev * N_e / pi`. The pre-fix
    # "monotone increasing, supremum 5.3994% as N_e -> infinity" claim came
    # from a quadrature error that grew with the target area; that error is
    # gone, and the surviving mathematical statement is the proportionality.
    rels = []
    for n_e in (4, 8, 16, 32, 64):
        got = sphere.canonical_voronoi_angle(n_e, 2)
        want = math.pi / n_e
        abs_dev = abs(got - want)
        rels.append((n_e, abs_dev / want))
        assert abs_dev < 1e-13, (
            f"actual_abs_dev={abs_dev!r} for N_e={n_e} (impl={got!r}, "
            f"exact={want!r}); bisection converges on an ABSOLUTE theta "
            f"tolerance (`break < 1e-13`), so this bound must hold for every "
            f"N_e and must NOT be allowed to grow with N_e"
        )
    # rel / N_e = abs_dev / pi is therefore invariant in N_e. The absolute
    # deviation is not bit-constant — it is 4.4631e-14 for N_e <= 16 and
    # 4.4645e-14 for N_e >= 32, a spread of one ulp of the deviation — so
    # the invariant is pinned to that spread rather than to a single value.
    for n_e, rel in rels:
        ratio = rel / n_e
        assert ratio == pytest.approx(1.4208e-14, abs=1e-17), (
            f"actual_rel_over_n_e={ratio!r} for N_e={n_e} (rel={rel!r}); the "
            f"absolute deviation is bisection-limited and constant to one ulp, "
            f"so rel_dev / N_e = abs_dev / pi MUST be the same number for every "
            f"N_e. If this drifts, either the bisection tolerance changed or "
            f"the deviation is no longer purely bisection-limited"
        )
# ---------------------------------------------------------------------------
# F9 / F10 — the two `src/decompmoe/sphere.py` docstring disclosures
# (change 2026-10-02-audit-a2-errata-and-spec-math-fixes; E15 / E8)
#
# BOTH defects these two tests used to pin are GONE; they are now
# REGRESSION GUARDS against the defects returning. The tests were kept rather
# than deleted precisely because a deleted test discloses nothing.
#
# F9: `canonical_voronoi_angle` — used to jump `7.87e-02` across `pi/2`.
#     Cause: `sin(pi/2)**2` is EXACTLY 1.0 in float64, so `_betainc_regularized`'s
#     `x >= 1.0` early return fired and `_cap_area(pi/2, d_c)` returned 0.5 by
#     construction, while the quadrature approached the same value from below
#     at the OLD single-panel rate. The exact `G` is continuous there, with a
#     true step of `1.5190e-07` at this probe. The step is now the true step.
#     The `x >= 1.0` early return is still the load-bearing path and is still
#     pinned by the bare `==` on `at_pi2 == 0.5` — what changed is that it
#     now AGREES with the quadrature instead of contradicting it.
#
# F10: `_betainc_regularized` — used to escalate by >5 orders of magnitude
#     as `x -> 1`, because `b = 1/2` put an integrable `(1 − t)^(−1/2)`
#     singularity at the never-subdivided panel's RIGHT endpoint. The
#     `t = sin²φ` substitution makes `2b − 1 = 0`, removing it EXACTLY. The
#     error is now flat across the domain, so the "MVP point does not
#     characterize the domain" claim is replaced by a domain-wide BOUND.
# ---------------------------------------------------------------------------


def test_cap_area_pi_half_no_artificial_discontinuity() -> None:
    """F9 regression guard: the `7.870852e-02` step across `pi/2` must not return.

    The exact `G` is continuous at `pi/2`; at 50 decimal digits
    `G(pi/2) = 0.5` and the true step down to `pi/2 - 1e-7` is `1.5190e-07`.
    The implementation used to step `7.87e-02` there — `18.68%` of the left
    limit, an artefact of the never-subdivided single panel, not a property of
    the mathematics. It now reproduces the true step, so this test is the guard
    against the artefact's RETURN rather than a pin on the artefact's size.

    The argument reached from below is 90 ulps under `1.0`, NOT
    `math.nextafter(1.0, 0)`, and the two are deliberately kept distinct here:
    at 1 ulp the float `x` is a different number, so the true step — and the
    implementation's — is a different number too.
    """
    import mpmath

    mpmath.mp.dps = 50
    a_exact = (mpmath.mpf(16) - 1) / 2  # 15/2 = 7.5, the d_c = 16 exponent

    at_pi2 = sphere._cap_area(math.pi / 2, 16)
    assert at_pi2 == 0.5, (
        f"actual_cap_area_at_pi2={at_pi2!r}; the x >= 1.0 early return must make "
        f"this exactly 0.5 (bare == pins the early-return path itself)"
    )

    h = 1e-7
    just_below = sphere._cap_area(math.pi / 2 - h, 16)
    x_below = math.sin(math.pi / 2 - h) ** 2

    # The step, measured at the exact same float argument the implementation
    # consumed. Pinning the impl against exact `G` AT THAT x` is what makes
    # this a statement about the mathematics rather than about the output.
    exact_lo = mpmath.mpf(0.5) * mpmath.betainc(
        a_exact, mpmath.mpf(1) / 2, 0, mpmath.mpf(x_below), regularized=True
    )
    exact_at = mpmath.mpf(0.5) * mpmath.betainc(
        a_exact, mpmath.mpf(1) / 2, 0, mpmath.mpf(1.0), regularized=True
    )
    true_step = exact_at - exact_lo
    assert just_below == pytest.approx(float(exact_lo), abs=1e-12), (
        f"actual_cap_area_below={just_below!r}, exact={mpmath.nstr(exact_lo, 20)} "
        f"at x={x_below!r}; the quadrature must agree with exact G at the "
        f"argument it was given"
    )

    # The load-bearing regression guard. The pre-fix step was 7.870852e-02, so
    # 1e-5 sits 7870x below the defect and 66x above the surviving true step.
    jump = abs(at_pi2 - just_below)
    assert jump < 1e-5, (
        f"actual_jump={jump!r} across pi/2; the exact G is continuous there, so "
        f"any step above 1e-5 means the artificial 7.87e-02 discontinuity has "
        f"returned (true step at this probe is "
        f"{mpmath.nstr(true_step, 8)})"
    )
    # ...and it is not merely small, it IS the analytic step.
    assert jump == pytest.approx(float(true_step), abs=1e-12), (
        f"actual_jump={jump!r}, true_step={mpmath.nstr(true_step, 20)}; the step "
        f"must equal the exact G's step at the same float argument, not merely "
        f"fall under a threshold"
    )

    # A vanishing fraction of the left limit, not a rounding artefact. This is
    # the quantity that used to make any stencil straddling pi/2 meaningless.
    rel_jump = jump / just_below
    assert rel_jump < 1e-5, (
        f"actual_rel_jump={rel_jump!r}; disclosed pre-fix value was 0.1868 "
        f"(18.68% of the left limit), which is what forced callers to treat "
        f"pi/2 as non-differentiable"
    )

    ulps = (1.0 - x_below) / 2.0**-53
    assert ulps == pytest.approx(90.0, abs=1e-6), (
        f"actual_ulps={ulps!r} (x_below={x_below!r}); expected 90 ulps, and "
        f"specifically NOT math.nextafter(1.0, 0) — the two are different "
        f"arguments and therefore carry different true steps"
    )
    at_1ulp = sphere._cap_area(math.asin(math.sqrt(math.nextafter(1.0, 0.0))), 16)
    assert at_1ulp != just_below, (
        f"actual_1ulp={at_1ulp!r} equals actual_90ulp={just_below!r}; the 1-ulp "
        f"and 90-ulp neighbours are distinct arguments and MUST NOT be "
        f"conflated into one literal"
    )

    # `N_e = 2` targets area exactly 0.5, so bisection lands on the pi/2
    # plateau and returns the same constant for every signature dimension.
    # That constant is why its `d_c = 2` residual looks like a harmless
    # 6.71e-09: it is the distance to pi/2, not quadrature accuracy. This
    # behaviour is unchanged by the fix and stays pinned as such.
    plateau = {sphere.canonical_voronoi_angle(2, d_c) for d_c in (2, 4, 16, 64)}
    assert len(plateau) == 1, (
        f"actual_n_e2_angles={sorted(plateau)!r}; N_e=2 targets area 0.5, so "
        f"bisection must land on one shared pi/2 plateau value for every d_c"
    )
    plateau_angle = sphere.canonical_voronoi_angle(2, 16)
    assert plateau_angle == pytest.approx(math.pi / 2, abs=1e-7), (
        f"actual_n_e2_angle={plateau_angle!r}; the plateau must sit at pi/2"
    )
    # Relative to pi/2 the plateau is the `6.71e-09` the docstring quotes —
    # a bisection tolerance, not a quadrature residual.
    rel_to_pi2 = abs(plateau_angle - math.pi / 2) / (math.pi / 2)
    assert rel_to_pi2 == pytest.approx(6.71e-09, abs=1e-11), (
        f"actual_rel_to_pi2={rel_to_pi2!r}; disclosed 6.71e-09 for N_e=2, which "
        f"is the distance to the pi/2 plateau rather than quadrature accuracy"
    )


def test_betainc_error_uniform_toward_one() -> None:
    """F10 regression guard: the `8.29e-07 -> 1.57e-01` escalation must not return.

    A single 8-point Gauss–Legendre panel is never subdivided, and `b = 1/2`
    places an integrable `(1 - t)^(-1/2)` singularity at the panel's RIGHT
    endpoint, so the absolute error used to grow by more than five orders of
    magnitude between the MVP point and `x -> 1`. The `t = sin^2(phi)`
    substitution makes the exponent `2b - 1 = 0`, removing that endpoint
    singularity EXACTLY rather than approximating it away, and the adaptive
    8/16-point rule covers what remains.

    The error is now FLAT across the declared domain, so the disclosure this
    test used to carry — "the MVP residual is a point sample, not a bound" —
    is replaced by the stronger claim it was warning about: there is now a
    domain-wide bound, and the load-bearing assertion is that the bound holds
    at EVERY point rather than at one sample.
    """
    import mpmath

    mpmath.mp.dps = 50
    a_exact = mpmath.mpf(7.5)
    b_exact = mpmath.mpf(1) / 2

    def measure(theta_rad: float) -> tuple[float, float]:
        x = math.sin(theta_rad) ** 2
        impl = sphere._betainc_regularized(x, 7.5, 0.5)
        truth = float(mpmath.betainc(a_exact, b_exact, 0, mpmath.mpf(x),
                                     regularized=True))
        return abs(impl - truth), abs(impl - truth) / truth

    # The domain-wide bound. Pre-fix this sweep spanned 8.29e-07 at the MVP
    # point up to 1.57e-01 at 89.999 deg; post-fix every point is at the
    # float64 noise floor, and the largest observed value is 1.5e-15.
    worst = 0.0
    for deg in (1.0, 20.0, 45.0, 60.0, 80.0, 89.0, 89.999, 89.99999):
        abs_err, _rel = measure(math.radians(deg))
        worst = max(worst, abs_err)
        assert abs_err < 1e-12, (
            f"actual_abs_err={abs_err!r} at {deg} deg; the domain-wide bound "
            f"for d_c = 16 (a = 7.5, b = 1/2) is 1e-12, and the pre-fix value "
            f"at 89.999 deg was 1.5736e-01"
        )
    assert worst < 1e-14, (
        f"actual_worst_abs_err={worst!r} over the sweep; measured max 1.5e-15, "
        f"so 1e-14 is a guard with three orders of margin"
    )

    # The specific point the old disclosure named: `x = 0.9999999996953826`
    # is 89.999 deg. Pre-fix the error there was 1.5736e-01 (15.74%).
    x_to_one = 0.9999999996953826
    one_impl = sphere._betainc_regularized(x_to_one, 7.5, 0.5)
    one_truth = float(
        mpmath.betainc(a_exact, b_exact, 0, mpmath.mpf(x_to_one), regularized=True)
    )
    one_abs = abs(one_impl - one_truth)
    one_rel = one_abs / one_truth
    assert one_abs < 1e-12, (
        f"actual_x_to_one_abs_err={one_abs!r} at x={x_to_one!r}; pre-fix this "
        f"was 1.5736e-01 (15.74% relative)"
    )

    mvp_abs, mvp_rel = measure(sphere.canonical_voronoi_angle(16, 16))
    assert mvp_abs < 1e-12, (
        f"actual_mvp_abs_err={mvp_abs!r}; pre-fix 8.2915e-07 (6.633 ppm)"
    )

    # The load-bearing claim is the ABSENCE of escalation. Pre-fix this was
    # `one_rel > 1000 * mvp_rel`; a single MVP sample could not stand in for
    # the domain, and the two ends could have been wrong in the same
    # direction with every other literal still passing. Now the error is at
    # the noise floor on both ends, so the ratio is order 1 — the assertion
    # is inverted to make a return of the escalation visible.
    assert one_rel < 10.0 * mvp_rel, (
        f"actual_ratio={one_rel / mvp_rel!r}; the pre-fix claim was that the "
        f"x->1 relative error exceeds 1000x the MVP one, so the domain could "
        f"not be summarized by the MVP sample. With both ends at the noise "
        f"floor the ratio must be O(1); a large value here means the "
        f"escalation has returned"
    )


# ---------------------------------------------------------------------------
# `spherical_l2_normalize`: the output-norm claim is a DIMENSION-DEPENDENT BOUND
# (change 2026-10-02-audit-a2-errata-and-spec-math-fixes; F2 / Req 19 Scenario
#  "Output norm is 1.0 up to a dimension-dependent rounding bound")
#
# The spec originally stated `pow(2).sum(-1) == 1.0` **exactly**. That identity
# holds in exact real arithmetic, but IEEE-754 rounding means `‖z‖/‖z‖` is not
# generally bit-equal to `1.0`: roughly half of all rows fail a bare `==`.
#
# Round 2 of the errata (change `2026-10-02-a2-round2-spec-math-fixes`) fixed a
# defect the first round introduced: the first round replaced the bare `==` with
# a UNIVERSAL `4*eps` bound, which is **false**. A length-`d` sum of squares
# carries relative error `gamma_{d-1} ~ d*u`, so the bound grows linearly with
# the last-dimension width. Measured against `4*eps` the ratio reaches 1.00x at
# `dim=512`, 1.12x at 1024, 1.75x at 4096 and 3.00x at 16384 (float64);
# float32 first exceeds at 4096. The governing claim is therefore
# `|pow(2).sum(-1) - 1| <= d*eps`, and `4*eps` survives only as the tight
# empirical envelope at the frozen MVP width `d_c = 16`.
#
# The first round's test swept only `{8, 16, 32, 128}` and so could not detect
# this. It now sweeps the widths at which the universal constant fails, which is
# the whole point: a bound test that only samples the regime where the bound is
# comfortable is not a bound test.
# ---------------------------------------------------------------------------


def test_spherical_l2_normalize_residual_dimension_dependent_bound() -> None:
    """`|pow(2).sum(-1) - 1| <= d*eps` for any width; `4*eps` only at MVP."""
    torch.manual_seed(0)

    eps64 = 2.220446049250313e-16
    eps32 = 1.1920928955078125e-07
    envelope64 = 4 * eps64
    envelope32 = 4 * eps32
    # integer/float closed forms: the 4-ulp MVP envelope is pinned at its own
    # value, bare `==`, because it is a claimed literal the spec quotes.
    assert envelope64 == 8.881784197001252e-16, f"actual={envelope64}"
    assert envelope32 == 4.768371582031250e-07, f"actual={envelope32}"

    # MVP width is the signature dim, frozen at 16 by CLAUDE.md section 5.
    mvp_dim = 16
    assert mvp_dim == 16, f"actual={mvp_dim}"

    # Widths chosen to straddle the point where a fixed 4-ulp constant stops
    # being valid, so the universal-constant failure is actually exercised.
    dims = (8, 16, 32, 128, 512, 1024, 4096)
    for dtype, eps, envelope in (
        (torch.float64, eps64, envelope64),
        (torch.float32, eps32, envelope32),
    ):
        worst_overall = 0.0
        worst_at = None
        worst_at_mvp = 0.0
        for dim in dims:
            worst = 0.0
            for _ in range(20):
                z = torch.randn(256, dim, dtype=dtype)
                out = sphere.spherical_l2_normalize(z)
                dev = float((out.pow(2).sum(-1) - 1.0).abs().max())
                if dev > worst:
                    worst = dev
            if dim == mvp_dim:
                worst_at_mvp = worst
            if worst > worst_overall:
                worst_overall, worst_at = worst, dim
            # THE governing claim: analytic, dimension-dependent, testable at
            # ANY width. A fixed constant cannot be written here.
            assert worst <= dim * eps, (
                f"actual_worst={worst:.6e} at dim={dim} for {dtype}; the "
                f"dimension-dependent bound is dim*eps = {dim * eps:.6e}. "
                f"The exact `== 1.0` equality is NOT attainable under IEEE-754"
            )
        # The 4-ulp envelope is a CLAIM only at the MVP width; scoped to it.
        assert worst_at_mvp <= envelope, (
            f"actual_worst_at_mvp_dim={worst_at_mvp:.6e} at dim={mvp_dim} for "
            f"{dtype}; the 4-ulp envelope quoted by the spec is {envelope:.6e}. "
            f"Note the overall worst over all swept widths is "
            f"{worst_overall:.6e} at dim={worst_at} — that is exactly why the "
            f"envelope MUST NOT be stated universally"
        )
