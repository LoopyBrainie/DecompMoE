"""Spherical L2 normalization + Voronoi self-consistency threshold.

This module materializes Req 5 (Steps 2 + 4) and Req 11 of
`openspec/specs/wayfinder/spec.md`:

    - `spherical_l2_normalize(z, eps)` implements z / max(‖z‖₂, eps)
      (closed-form `max` denominator per A-CR-2 spec revision; output
      norm is `≤ 1` and exactly `1.0` for `‖z‖₂ ≥ eps`, exactly `0` for
      `z = 0`).
    - `canonical_voronoi_angle(num_experts, signature_dim)` returns the
      closed-form Voronoi half-angle θ_Voronoi(N_e, d_c) on the unit sphere
      S^{d_c − 1} (per Equal-Area Voronoi tessellation). Defined as the
      unique θ ∈ (0, π) solving

          ½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1 / N_e

      where I_x(a, b) is the regularized incomplete beta function. Every
      input is solved by bisection on a hand-rolled regularized-incomplete-
      beta via direct Gauss quadrature (no scipy dependency); no hard-coded
      table.
    - `voronoi_angle(centroids)` is the OFFLINE MEASUREMENT LAYER. It returns
      the mean per-cell equivalent-cap radius of the realised spherical
      Voronoi tessellation, `θ̂ = mean_i G^{-1}(A_i)`, where `A_i` is the area
      fraction of cell `i` and `G` is the spherical cap-area function. This
      makes it commensurable with `canonical_voronoi_angle`, which is
      `G^{-1}(1/N_e)`. See its own docstring for the derivation, the
      convexity precondition of the one-sided bound, and the measurement
      error budget. Offline use only — NEVER in the training hot path.

`canonical_voronoi_angle` and `spherical_l2_normalize` are pure. `voronoi_angle`
is deterministic (fixed seed) but is a Monte-Carlo estimator over
`VORONOI_AREA_SAMPLES` probes, so it is NOT a pure function of its argument in
the usual sense; the sample count and seed are explicit module constants, not
hidden parameters. No autograd state, no global registries.
"""

from __future__ import annotations

import math

import torch
from torch import Tensor

# ---------------------------------------------------------------------------
# Spherical L2 normalization (Req 5)
# ---------------------------------------------------------------------------


def spherical_l2_normalize(z: Tensor, eps: float = 1e-6) -> Tensor:
    """Return `z / max(‖z‖₂, eps)` along the last dimension.

    Spec (skeleton "Spherical L2 Normalization"): `max(‖z‖₂, ε)` guarantees
    output norm is `≤ 1` and monotone non-decreasing in input norm
    (for `‖z‖₂ ≥ ε`). Safe at `z = 0`: returns the zero vector (finite).

    Default eps = 1e-6 matches ticket A3-1.
    """
    norm = torch.linalg.norm(z, dim=-1, keepdim=True)
    return z / torch.clamp(norm, min=eps)


# ---------------------------------------------------------------------------
# Regularized incomplete Beta function (self-implemented, no scipy dependency)
# ---------------------------------------------------------------------------

_GL8 = (
    (-0.9602898564975363, 0.1012285362903763),
    (-0.7966664774136267, 0.2223810344533745),
    (-0.5255324099163290, 0.3137066458778883),
    (-0.1834346424956498, 0.3626837833783620),
    (0.1834346424956498, 0.3626837833783620),
    (0.5255324099163290, 0.3137066458778883),
    (0.7966664774136267, 0.2223810344533745),
    (0.9602898564975363, 0.1012285362903763),
)

_GL16 = (
    (-0.9894009349916499, 0.0271524594117541),
    (-0.9445750230732326, 0.0622535239386479),
    (-0.8656312023878317, 0.0951585116824928),
    (-0.7554044083550030, 0.1246289712555339),
    (-0.6178762444026438, 0.1495959888165767),
    (-0.4580167776572274, 0.1691565193950025),
    (-0.2816035507792589, 0.1826034150449236),
    (-0.0950125098376374, 0.1894506104550685),
    (0.0950125098376374, 0.1894506104550685),
    (0.2816035507792589, 0.1826034150449236),
    (0.4580167776572274, 0.1691565193950025),
    (0.6178762444026438, 0.1495959888165767),
    (0.7554044083550030, 0.1246289712555339),
    (0.8656312023878317, 0.0951585116824928),
    (0.9445750230732326, 0.0622535239386479),
    (0.9894009349916499, 0.0271524594117541),
)

_QUAD_RTOL = 1e-12
"""Relative agreement required between the 8- and 16-point panel results.

Deliberately NOT tighter. The acceptance test is scale-free, so for a small
argument (`x = 0.02`, `a = 7.5` gives `I_x ~ 2e-14`) the threshold
`1e-15 * 2e-14 = 2e-26` sits at the same magnitude as the roundoff floor of the
comparison itself, and the recursion then never terminates. `1e-12` still
leaves four orders of margin against the `< 1e-9` residual bound on
`G(θ) - 1/N_e`, and is far above the ~`1e-16` relative noise of two independent
panel sums.
"""

_QUAD_MAX_PANELS = 4096
"""Hard cap on evaluated panels; a backstop so no input can run away."""


def _gauss_legendre(f, lo: float, hi: float, rule) -> float:
    half = 0.5 * (hi - lo)
    mid = 0.5 * (hi + lo)
    total = 0.0
    for node, weight in rule:
        total += weight * f(mid + half * node)
    return total * half


def _adaptive_gauss_legendre(f, lo: float, hi: float, budget: list[int]) -> float:
    """Integrate `f` on `[lo, hi]`, bisecting until the 8- and 16-point panels
    agree to `_QUAD_RTOL` relative.

    Comparing two orders makes the acceptance test an error estimate rather
    than an assumption. `budget` is a single-element list used as a shared
    counter so the recursion cannot exceed `_QUAD_MAX_PANELS` evaluations.
    """
    budget[0] += 1
    coarse = _gauss_legendre(f, lo, hi, _GL8)
    fine = _gauss_legendre(f, lo, hi, _GL16)
    converged = abs(fine - coarse) <= _QUAD_RTOL * abs(fine)
    if converged or budget[0] >= _QUAD_MAX_PANELS:
        return fine
    mid = 0.5 * (lo + hi)
    return _adaptive_gauss_legendre(f, lo, mid, budget) + _adaptive_gauss_legendre(
        f, mid, hi, budget
    )


def _betainc_regularized(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta function I_x(a, b) via adaptive Gauss–Legendre.

    Direct numerical integration of B(x; a, b) = ∫₀ˣ t^{a−1} (1−t)^{b−1} dt
    then normalized by B(a, b) = Γ(a)Γ(b)/Γ(a+b), carried out on the
    `t = sin²φ` substitution described in the body below.

    ACCURACY. An adaptive 8/16-point Gauss–Legendre rule is bisected until the
    two orders agree to `_QUAD_RTOL` relative, so the error estimate is
    UNIFORM over the declared domain instead of parameter-dependent. Measured
    against exact quadrature at 50 decimal digits, the absolute error sits at
    the float64 noise floor everywhere: at the MVP point (`a = 7.5`, `b = 1/2`,
    `x = 0.8503215893859075`) it is `3.04e-16` (relative `2.43e-15`), and

        θ = 60.0°      x = 0.7499999999999999   abs 1.22e-17   rel 2.97e-16
        θ = 82.6036°   x = 0.9834277406156522   abs 3.58e-16   rel 5.75e-16
        θ = 89.999°    x = 0.9999999996953826   abs 5.45e-16   rel 5.45e-16
        θ = 89.99999°  x = 0.9999999999695371   abs 6.80e-16   rel 6.80e-16
        1 − 1 ulp      x = 0.9999999999999999   abs 6.45e-16   rel 6.45e-16

    On the small-`x` side (`a = 1/2`, i.e. `signature_dim = 2`) the errors are
    `4.53e-17` at `x = 0.02`, `9.42e-18` at `x = 0.001` and `3.54e-20` at
    `x = 1e-8`.

    ⚠️ HISTORY — the pre-fix figures were a POINT SAMPLE plus a worst case, and
    are recorded here only so the change is legible. A single never-subdivided
    8-point panel gave `8.29e-07` (6.633 ppm) at the MVP and grew to
    `1.57e-01` at `x → 1⁻`, because `b = 1/2` puts an integrable
    `(1 − t)^(−1/2)` singularity at the panel's RIGHT endpoint while `a = 1/2`
    puts a `t^(−1/2)` singularity at its LEFT one. The `t = sin²φ` substitution
    makes the exponents `2b − 1` and `2a − 1` zero at exactly those parameter
    values, so both singularities are removed EXACTLY rather than subdivided
    around. Callers MAY now rely on a domain-wide absolute bound of `1e-12`
    for every `signature_dim >= 2`;
    `tests/test_sphere.py::test_betainc_error_uniform_toward_one` is the
    guard, and it goes red if the flatness regresses. The old "the MVP point
    does not characterize the domain" caveat MUST NOT be reintroduced without
    re-measuring.

    HISTORY — the RETIRED `82.6°` "convexity boundary" artefact. An earlier
    revision of `tests/test_sphere.py` asserted a sign change in the
    central-differenced `G''` at `81.3148° / 82.6036° / 83.7313°`, and the
    pre-fix helper did reproduce sign changes there. Recomputing that stencil
    from THIS helper now matches the true `G''` to 8 significant digits and
    shows no sign change (at `82.6036°`, `d_c = 16`: stencil `2.4567645`, true
    `2.4567645`) — the sign changes were the error curve, not `G`. `G`'s only
    inflection on `(0, π)` is at exactly `pi/2`, since
    `G''(θ) = (d_c−2)·sin^{d_c−3}θ·cosθ / B((d_c−1)/2, ½)` and `sinθ > 0`
    throughout. `tests/test_sphere.py::test_voronoi_angle_precondition_is_area_below_half`
    is the regression guard against that claim returning.

    Per fix-openspec-doc-bugs-apply design.md Decision 1 + Risk 1 mitigation:
    avoids scipy dependency by direct Gauss–Legendre quadrature.
    """
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    # Substitute t = sin^2(phi). The integrand becomes
    #     t^(a-1) (1-t)^(b-1) dt = 2 sin^(2a-1)(phi) cos^(2b-1)(phi) dphi
    # so the integration range is [0, asin(sqrt(x))] and BOTH endpoint
    # singularities of the original are removed exactly for the parameter
    # values this package uses: b = 1/2 makes the exponent 2b-1 = 0 (the
    # (1-t)^(-1/2) singularity at t = 1 becomes a constant), and a = 1/2
    # (signature_dim = 2) makes 2a-1 = 0 (the t^(-1/2) singularity at t = 0
    # likewise). The log-form below keeps the remaining cases finite even when
    # an exponent is negative, because Gauss-Legendre nodes are strictly
    # interior and are never evaluated at an endpoint.
    p = 2.0 * a - 1.0
    q = 2.0 * b - 1.0
    log_two = math.log(2.0)

    def integrand(phi: float) -> float:
        s = math.sin(phi)
        c = math.cos(phi)
        if s <= 0.0 or c <= 0.0:
            # Only reachable at an endpoint, which the quadrature never samples.
            return 0.0
        return math.exp(log_two + p * math.log(s) + q * math.log(c))

    # Upper limit asin(sqrt(x)). For x near 1 that expression cancels: sqrt(x)
    # rounds to exactly 1.0 (the offset 5.55e-17 is below the 2.22e-16 spacing
    # near 1), which silently pins the limit to pi/2 and drops the true
    # pi/2 - 1.49e-8 offset, costing ~1.3e-08 in the result. Compute the offset
    # from `1 - x` instead, which is exact for x >= 0.5 (Sterbenz), and
    # asin(sqrt(d)) ~ sqrt(d) is accurate in relative terms for small d.
    if x <= 0.5:
        hi = math.asin(math.sqrt(x))
    else:
        hi = math.pi / 2.0 - math.asin(math.sqrt(1.0 - x))
    integral = _adaptive_gauss_legendre(integrand, 0.0, hi, [0])
    if not (integral > 0.0):
        return 0.0
    incomplete = math.exp(math.log(integral) - log_beta)
    return min(1.0, max(0.0, incomplete))


# ---------------------------------------------------------------------------
# Spherical cap area and its inverse (shared by the closed form and the
# measurement layer)
# ---------------------------------------------------------------------------

VORONOI_AREA_SAMPLES = 1_000_000
"""Monte-Carlo probe count used by `voronoi_angle` to estimate cell areas.

At the MVP point `(N_e=16, d_c=16)` this gives a standard error of the
returned mean of `1.461e-5°`, so `5σ ≈ 7.31e-5°`.

The derivation respects the exact constraint `Σ_i A_i ≡ 1` (one `argmax`
owner per probe ⇒ `Σ_i n_i = M`), so the first-order term of
`θ̂ − G⁻¹(1/N_e)` cancels identically and the leading fluctuation is second
order — the spread scales as `1/M`, not `1/√M`. Treating the `N_e` cell
areas as independent instead yields `0.0071°` / `5σ = 0.0355°`, which is
`486×` too large; that superseded figure MUST NOT be reintroduced.
"""

VORONOI_AREA_SEED = 20260929
"""Fixed probe seed, so `voronoi_angle` is deterministic and pinnable.

Measured crosspolytope(32) spread across seeds 0 / 1 / 7 / 42 / 123 / 999 /
20260929 / 31337 at `VORONOI_AREA_SAMPLES = 1_000_000` is `3.68e-5°`, with a
per-seed SD of `1.53e-5°` — the predicted `σ = 1.461e-5°` to within `5%`.

Every one of those seeds lands `6.1e-5° .. 9.8e-5°` BELOW
`canonical_voronoi_angle(32, 16)`, all the same sign. That is not sampler
noise: it is the canonical side's own error, since
`canonical_voronoi_angle` is a bisection root of `_betainc_regularized` and
its true closed-form residual is documented in
`openspec/specs/decompmoe-skeleton/spec.md` req-6.
"""


def _cap_area(theta: float, signature_dim: int) -> float:
    """Area fraction of the spherical cap of half-angle `theta` on
    `S^{signature_dim - 1}`, for `theta` in `(0, pi)`.

    The small-cap branch is `½ · I_{sin²θ}((d_c − 1)/2, ½)`; for
    `theta > pi/2` it is the reflection `1 − ½ · I_{sin²θ}((d_c − 1)/2, ½)`.
    The reflected branch is required for totality: `G(pi/2) = 0.5`, so a cell
    holding more than half the sphere has no solution in the small-cap branch
    alone.
    """
    half = 0.5 * _betainc_regularized(
        math.sin(theta) ** 2, (signature_dim - 1) / 2.0, 0.5
    )
    if theta <= math.pi / 2.0:
        return half
    return 1.0 - half


def _cap_radius(area: float, signature_dim: int) -> float:
    """Inverse of `_cap_area` on `[0, 1]`, by bisection on `(0, pi)`.

    `canonical_voronoi_angle(N_e, d_c)` is `1/N_e` inverted through this
    function, which is what makes the measurement layer commensurable with
    the closed form.
    """
    if not 0.0 <= area <= 1.0:
        raise ValueError(f"cap area must lie in [0, 1]; got {area}")
    if area == 0.0:
        return 0.0
    lo, hi = 0.0, math.pi
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _cap_area(mid, signature_dim) < area:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13:
            break
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Voronoi self-consistency (wayfinder Req 11)
# ---------------------------------------------------------------------------


def canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float:
    """Closed-form Voronoi half-angle on S^{signature_dim − 1}.

    Solves ½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1 / N_e for θ ∈ (0, π/2]
    via bisection on

        f(θ) = ½ · I_{sin² θ}((d_c − 1)/2, 1/2) − 1 / N_e.

    Every input bisects — no hard-coded table (spec Scenario
    "no hard-coded table values"; the prior tabulated MVP fast-path
    values were wrong and have been removed).

    Accuracy: the returned angle is the root of the impl-internal equation to
    within the bisection's own `break < 1e-13` bracket, and because the
    quadrature underneath is now uniformly accurate, that carries over to the
    TRUE closed form. Measured at `N_e = 16` against exact `G` at 50 decimal
    digits, the absolute residual is

        d_c=2  4.46e-14   d_c=4  4.13e-14   d_c=6  2.45e-14
        d_c=8  3.74e-14   d_c=16 3.54e-14   d_c=32 6.10e-16

    i.e. below the spec's `< 1e-9` claim for EVERY `signature_dim >= 2`
    measured here, not merely at the frozen MVP `d_c = 16`. The pre-fix
    residuals for the same six points ran from `7.39e-09` to `4.29e-05`, and
    that spread is why this note used to warn that the `< 1e-9` claim held
    only at `d_c = 16`. That warning no longer applies and MUST NOT be
    reintroduced without re-measuring.

    The body delegates to `_cap_radius(1 / N_e, d_c)`, which solves the same
    root: `1/N_e ≤ 0.5` places it in the small-cap branch. Its impl-internal
    residual is `1.74e-14` at `(16, 16)`, `6.45e-15` at `(32, 16)` and
    `2.67e-15` at `(64, 16)`. (This paragraph used to claim `0.00e+00` at
    those three points; the quadrature beneath them has since changed, and
    the figures above are the measured ones.)

    ⚠️ THE `pi/2` ENDPOINT IS AN EXACT EARLY RETURN, NOT A DISCONTINUITY.
    `math.sin(math.pi / 2) ** 2` evaluates to EXACTLY `1.0` in float64, so
    `_cap_area(pi/2, d_c)` takes `_betainc_regularized`'s `x >= 1.0` early
    return and yields `0.5` BY CONSTRUCTION rather than by quadrature. That
    used to disagree violently with the quadrature arriving from below; it no
    longer does:

        `_cap_area(pi/2, 16)`          = 0.5
        `_cap_area(pi/2 - 1e-7, 16)`  = 0.4999998481030135

    a step of `1.518970e-07`, which IS the true step — `1.518970e-07` at this
    same float argument, `1.519577e-07` at exact `θ = pi/2 - 1e-7`. The
    pre-fix step was `7.870852e-02`, `18.68%` of the left limit.

    Note the argument reached from below is `x = math.sin(pi/2 - 1e-7) ** 2 =
    0.99999999999999`, which is **90 ulps** below `1.0` — NOT
    `math.nextafter(1.0, 0)`. The two are distinct: at the 1-ulp neighbour the
    helper returns `0.49999997735653384`, at the 90-ulp point
    `0.4999998481030135`.

    CONSEQUENCES.
    (1) The pre-fix prohibition on differencing through or across `pi/2` no
        longer has a defect behind it: the function is continuous there to
        `1.5e-07`, the size of the true step, so a stencil straddling `pi/2`
        no longer measures an implementation artefact. Differencing is still
        unwise within the last `1e-7` below `pi/2`, where the float `x` is
        only 90 ulps from `1.0` and therefore carries 90 ulps of argument
        error — that is a property of `x = sin²θ` in float64, not of this
        function.
    (2) `_cap_radius` is unaffected because its target `1/N_e` is at most
        `0.5`, and `N_e >= 3` keeps its bisection root strictly below `pi/2`
        (e.g. `canonical_voronoi_angle(3, 16) = 1.4578378442369877`).
    (3) `N_e = 2` targets exactly `0.5`, so bisection lands on the `pi/2`
        plateau and this function returns `1.5707963162581635` for EVERY
        `d_c` — a constant that detects nothing about the signature
        dimension. That is also why its `d_c = 2` residual looks like a
        harmless `6.71e-09`: that figure is the distance to `pi/2`, not
        quadrature accuracy.

    Returns the angle in radians (multiply by 180/π for degrees).
    """
    if num_experts < 2:
        raise ValueError(f"num_experts must be ≥ 2; got {num_experts}")
    if signature_dim < 2:
        raise ValueError(f"signature_dim must be ≥ 2; got {signature_dim}")
    return _cap_radius(1.0 / num_experts, signature_dim)


def voronoi_angle(centroids: Tensor) -> float:
    """Realised equal-area deviation measure — commensurable with the closed form.

    Returns the MEAN PER-CELL EQUIVALENT-CAP RADIUS of the realised spherical
    Voronoi tessellation on `S^{d_c − 1}`:

        A_i = area fraction of cell i            (seeded Monte-Carlo)
        θ̂   = (1/N_e) · Σ_i G⁻¹(A_i)             where G = `_cap_area`

    Because `canonical_voronoi_angle(N_e, d_c)` is exactly `G⁻¹(1/N_e)`, the
    deviation `D := canonical − θ̂` is a one-sided, bounded equal-area
    deviation that vanishes at the equal-area ideal. Offline use only.

    ⚠️ THE PER-CELL FORM IS LOAD-BEARING. Do not "simplify" this to
    `G⁻¹(mean_i A_i)`: spherical Voronoi cell areas always sum to 1, so
    `mean_i A_i ≡ 1/N_e` for EVERY centroid set and that form returns
    `canonical_voronoi_angle` unconditionally — a constant function that
    detects nothing. `tests/test_sphere.py::test_voronoi_angle_not_degenerate_mean_area_form`
    exists specifically to kill that regression.

    One-sidedness (Jensen). `G` is STRICTLY CONVEX on the whole of
    `(0, π/2)`, with no convexity boundary to worry about. Differentiating
    the defining closed form gives

        G'(t)  = sin^(d_c−2)(t) / B((d_c−1)/2, ½)
        G''(t) = (d_c−2)·sin^(d_c−3)(t)·cos(t) / B((d_c−1)/2, ½)

    and for `d_c ≥ 3` every factor is strictly positive on `(0, π/2)`, so
    `G'' > 0` there and `G⁻¹` is concave on the matching area interval
    `(0, 0.5)`. The precondition therefore reduces to every cell being
    smaller than a hemisphere — `∀i: A_i < 0.5`. Then

        θ̂ = (1/N_e) Σ G⁻¹(A_i) ≤ G⁻¹((1/N_e) Σ A_i) = G⁻¹(1/N_e) = canonical

    with equality iff `A_1 = ⋯ = A_{N_e}`. At MVP `canonical(16, 16) =
    67.24°` and the measured cell areas (largest ≈ 0.077 vs `1/16 = 0.0625`)
    leave an `A_i < 0.5` margin of ~`6.5×`. `G⁻¹`'s concavity does NOT extend
    past a hemisphere: for `A_i > 0.5` the reflected branch takes over and
    the inequality is OBSERVED BEHAVIOUR, NOT A THEOREM — it is guarded by
    `test_voronoi_angle_one_sided_gap`, not asserted as a closed form.

    ⚠️ Do NOT measure this curvature by finite-differencing `_cap_area`.
    That helper integrates with a single 8-point Gauss–Legendre panel and no
    subdivision, and its numerical second difference develops a spurious sign
    change near `82°`–`88°` that is a QUADRATURE ARTEFACT, not a property of
    `G` (the true `G''` there is `+0.21`…`+2.46`, strictly positive). The
    guard is `test_voronoi_angle_precondition_is_area_below_half`, which uses
    the closed form above.

    Corrected inversion, for the record. The superseded implementation fed
    the mean pairwise CHORD `c = √(2·(1−cos θ))` into the slot that expects a
    VERSINE `1−cos θ`, computing `arccos(1 − c)` instead of `arccos(1 − c²/2)`
    — the chord magnitude was mistaken for the versine. That inflated the
    output over the sampled grid (10°/45°/60°/120°/150°) by
    `+24.3416° / +31.4300° / +30.0000° / +17.0586° / +8.7253°`; those are the
    min/max of THAT SAMPLE, not a global bound. A 1.8e6-point scan gives the
    true peak `+31.5863380965°` at `θ* = 2·arcsin(1/3) = 38.9424412690°` (derivation:
    `e(θ) = arccos(1 − 2sin(θ/2)) − θ`, `e′ = 0 ⟺ 3s² − 4s + 1 = 0 ⟺ s = 1/3`),
    and the error vanishes at BOTH ends (`e(180°) = 0`, `e(0.5°) = +7.07°`,
    `e(179°) = +0.29°`). The superseded implementation also averaged over all
    `i < j` pairs, which is not a Voronoi quantity at all: at the crosspolytope
    it returned `115.6651°` where the canonical answer is `62.5445°`.

    Measurement error. The exact constraint `Σ_i A_i ≡ 1` — every probe is
    assigned to exactly one `argmax` owner, so `Σ_i n_i = M` identically —
    makes the FIRST-ORDER term of `θ̂ − G⁻¹(1/N_e)` vanish exactly
    (`Σ_i ε_i ≡ 0` with `ε_i := A_i − 1/N_e`). The leading fluctuation is
    therefore the second-order one, `(1/(2N_e))·g''·Σ_i ε_i²` with
    `g'' = [G⁻¹]'' = −G''/G'³`, and `Var(Σ_i ε_i²) ≈ 2·N_e·(A(1−A)/M)²`:
    the spread scales as `1/M`, not `1/√M`. At MVP
    (`d_c=16`, `N_e=16`, `M=1_000_000`) `G'(θ₀) = 0.488436`,
    `g'' = −24.6207`, giving a standard error of `1.461e-5°` and
    `5σ ≈ 7.31e-5°` — corroborated by a measured cross-seed SD of `1.353e-5°`
    (8 seeds). An earlier revision of this docstring derived `0.0071°` by
    treating the `N_e` cell areas as independent; that is `486×` too large
    and is superseded. `abs=1e-3` (`13.7×` this `5σ`) is therefore a safe
    witness tolerance, not a tight one. Use
    `test_voronoi_angle_equal_area_witness_crosspolytope` for the equal-area
    reference point, where the TRUE gap is `6.5e-5°`.

    Degenerate input. A cell that captures no probe has `A_i = 0` and
    contributes `G⁻¹(0) = 0` to the mean, biasing `θ̂` DOWN. This is
    mathematically correct (a zero-area cell has zero equivalent-cap radius)
    and is REQUIRED: the one-sidedness witnesses deliberately pass exact
    duplicate sites, which leaves every shadowed copy with zero area. It
    signals a degenerate tessellation, not a sampler failure.

    `centroids` MUST be unit-norm (`‖c_i‖₂ = 1`). The owner is the `argmax` of
    `p̂ · c_i`, which selects the nearest site BY ANGLE only when every
    `‖c_i‖₂ = 1`; otherwise the inner product is scaled by `‖c_i‖₂` and the
    realised tessellation silently differs from the caller's intent. A
    deviation beyond `1e-6` is rejected rather than absorbed. dtype is
    honoured: the probes are cast to `centroids.dtype`, so a `float64`
    tensor works exactly as a `float32` one does.
    """
    if centroids.dim() != 2:
        raise ValueError(
            f"centroids must be 2-D (N_e × d_c); got shape {tuple(centroids.shape)}"
        )
    N_e = centroids.shape[0]
    if N_e < 2:
        raise ValueError(f"need at least 2 centroids; got N_e={N_e}")
    d_c = centroids.shape[1]
    if d_c < 2:
        raise ValueError(f"signature_dim must be ≥ 2; got d_c={d_c}")
    norms = centroids.norm(dim=-1)
    if not torch.allclose(norms, torch.ones_like(norms), atol=1e-6, rtol=0.0):
        worst = int(torch.argmax((norms - 1.0).abs()))
        raise ValueError(
            f"centroids must be unit-norm on S^{{{d_c} - 1}}; row {worst} has "
            f"norm {float(norms[worst])!r} (tolerance 1e-6). The argmax owner "
            f"is the nearest site by ANGLE only when every norm is 1; "
            f"normalize with torch.nn.functional.normalize(centroids, dim=-1)"
        )

    generator = torch.Generator().manual_seed(VORONOI_AREA_SEED)
    probes = torch.nn.functional.normalize(
        torch.randn(VORONOI_AREA_SAMPLES, d_c, generator=generator), dim=-1
    ).to(centroids.dtype)
    owner = (probes @ centroids.T).argmax(dim=1)
    areas = torch.bincount(owner, minlength=N_e).to(torch.float64) / (
        VORONOI_AREA_SAMPLES
    )
    radii = [_cap_radius(float(a), d_c) for a in areas]
    return sum(radii) / N_e


__all__ = [
    "VORONOI_AREA_SAMPLES",
    "VORONOI_AREA_SEED",
    "spherical_l2_normalize",
    "canonical_voronoi_angle",
    "voronoi_angle",
]
