"""Tests for `decompmoe.sphere`: spherical L2 normalize + Voronoi self-consistency.

ST-03 / Req 5 (Steps 2 + 4), Req 11 (Voronoi self-consistency at β = 16).
"""

from __future__ import annotations

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
        N_e=16 → residual < 1e-9 AND θ == 1.173548 rad (abs=1e-6) AND θ_17 < θ_16
        N_e=17 → residual < 1e-9 AND θ == 1.165848 rad (abs=1e-6)
    """
    theta_16 = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    theta_17 = sphere.canonical_voronoi_angle(num_experts=17, signature_dim=16)
    # Closed-form literal pins (governance req-gov-1 §3 — bisection-6dp literals).
    assert theta_16 == pytest.approx(1.173548, abs=1e-6), f"actual={theta_16}"
    assert theta_17 == pytest.approx(1.165848, abs=1e-6), f"actual={theta_17}"
    # Principle: each θ must solve the closed-form equation ½·I_{sin²θ}(7.5, ½) = 1/N_e
    # with residual < 1e-9 per spec L231.
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
    # Spec L236 4dp display forms: `θ_Voronoi(16, 16) ≈ 67.24° (≈ 1.1735 rad)`.
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
    # Spec L237 4dp display forms: `θ_Voronoi(64, 16) ≈ 1.0205 rad (≈ 58.47°)`.
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
    # Spec L245 literal: `arccos(15/16) ≈ 20.36°` (float closed form → abs=1e-2 deg).
    assert math.degrees(theta_1_over_e) == pytest.approx(20.36, abs=1e-2), (
        f"actual={math.degrees(theta_1_over_e)}"
    )


def test_ct_decode_footprint_is_dtype_dependent() -> None:
    """Spec L370 (req-16): Decode SRAM footprint of `C_t` is `16 floats = 64 bytes`
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


def test_voronoi_measurement_layer() -> None:
    """`voronoi_angle(centroids)` returns a centroid-spread statistic in (0, π).

    Spec: wayfinder Req 11 + skeleton "Voronoi Self-Consistency Threshold"
    measurement layer, which describes the function as computing "the realized
    half-angle from an actual centroid tensor".

    The implementation is NOT commensurable with `canonical_voronoi_angle`:
    it averages over all centroid pairs, whereas a Voronoi half-angle is set
    by the nearest neighbours. Measured at the exactly-equal-area crosspolytope
    ideal, the two differ by 84.9% (see `voronoi_angle` docstring in
    sphere.py). This test therefore guards only that the function returns a
    sane magnitude on a real centroid tensor; it does NOT certify that any
    distribution is close to the equal-area ideal. Resolving that spec/implementation
    mismatch is deferred to a dedicated change (see `design.md` Decision 4).
    """
    torch.manual_seed(0)
    N_e, d_c = 16, 16
    # Generate a Fibonacci-sphere point set on S^2 and embed it in R^{d_c}.
    # NOTE: only the first 3 dimensions are populated, so this fixture has
    # effective rank 3 of d_c — it is an S^2 embedded in R^16, NOT a
    # distribution on S^{d_c - 1}. It therefore cannot exercise Voronoi
    # geometry on the canonical sphere. See `design.md` Decision 4.
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
    # Returned angle must be in (0, π).
    assert 0.0 < theta < math.pi, f"voronoi_angle = {theta} rad must be in (0, π)"
    # Deviation from the canonical angle. The π/2 bound below is NOT a theorem
    # about Voronoi cells — see the `voronoi_angle` docstring in sphere.py: the
    # statistic it returns averages over ALL pairs, while a Voronoi half-angle
    # is set by the nearest neighbours, so no such bound exists. The bound here
    # is a loose smoke check that the function returns a sane magnitude, and
    # the delta it tolerates is large precisely because the two quantities are
    # not commensurable (measured delta for this fixture: 8.15e-1 rad).
    canonical = sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16)
    assert abs(theta - canonical) < math.pi / 2, (
        f"realized θ = {math.degrees(theta):.2f}° is more than π/2 from canonical "
        f"{math.degrees(canonical):.2f}°; actual_delta_rad={abs(theta - canonical):.3e}"
    )


def test_voronoi_angle_known_answer_crosspolytope() -> None:
    """Known-answer witness for `voronoi_angle` — pins the exact value it returns.

    The `π/2` bound in `test_voronoi_measurement_layer` tolerates a 0.815 rad
    deviation, so it cannot detect a change in this function's output at all.
    This test pins the output instead.

    Input: the 32 crosspolytope vertices `±e_i` on S^15. Its 32 spherical
    facets are all congruent, so this is an **exactly equal-area** partition —
    the mathematical ideal a Voronoi-based measure is supposed to recognise.
    On it the three quantities separate cleanly:

        this function                        115.6651°
        with the correct inverse arccos(1−c²/2)   91.5415°
        canonical_voronoi_angle(32, 16)            62.5445°

    The middle row is not asserted by this function (it computes the first row);
    it is the value a corrected inversion would produce, and the difference
    quantifies the inversion defect documented in `sphere.voronoi_angle`.

    Pinning 115.6651° makes any change to the formula — fixing the inversion,
    switching to a nearest-neighbour inradius, or plain regression — turn this
    red, so the eventual fix has to update this witness deliberately rather
    than drift silently.
    """
    torch.manual_seed(0)
    d_c = 16
    crosspolytope = torch.cat([torch.eye(d_c), -torch.eye(d_c)], dim=0)
    assert crosspolytope.shape == (32, d_c)

    theta = sphere.voronoi_angle(crosspolytope)
    assert math.degrees(theta) == pytest.approx(115.6651, abs=1e-4), (
        f"actual={math.degrees(theta)} deg — voronoi_angle's output on the "
        f"crosspolytope changed; if the formula was fixed on purpose, update "
        f"this witness together with the sphere.py docstring"
    )
    # And it is NOT the canonical angle, by a wide margin — the reason this
    # function must not be used as an equal-area coverage check.
    canonical = sphere.canonical_voronoi_angle(32, d_c)
    assert abs(theta - canonical) == pytest.approx(
        math.radians(53.1206), abs=1e-3
    ), f"actual_delta_deg={math.degrees(abs(theta - canonical))}"


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
    MUST NOT be confused with D_chord = √(2(1 − cos θ)) per spec L233.
    The test enforces the versine principle via the bisection residual
    < 1e-9 on the underlying angle, the spec's 4dp `versine` literals
    (`0.6131` / `0.4771`, spec L236-L237), and the identity assertions on
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
    # Step 2b: spec L236-L237 4dp `versine` literal pins. versine is a derived
    # quantity, so it is pinned at the spec's stated 4dp precision (abs=1e-4).
    assert v_16_16 == pytest.approx(0.6131, abs=1e-4), f"actual={v_16_16}"
    assert v_64_16 == pytest.approx(0.4771, abs=1e-4), f"actual={v_64_16}"
    # Step 3: versine MUST NOT be chord distance (per spec L233 distinction).
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
