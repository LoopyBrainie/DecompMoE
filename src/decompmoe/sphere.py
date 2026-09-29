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


def _betainc_regularized(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta function I_x(a, b) via Gauss–Legendre 8-point.

    Direct numerical integration of B(x; a, b) = ∫₀ˣ t^{a−1} (1−t)^{b−1} dt
    then normalized by B(a, b) = Γ(a)Γ(b)/Γ(a+b).

    A **single** 8-point Gauss–Legendre panel is applied on [0, x]; there is
    no subdivision. Accuracy is therefore parameter-dependent and NOT uniform
    across the declared domain: at the MVP point (`a = 7.5`, `b = 0.5`,
    `x = sin²θ ≈ 0.8503`) the absolute error against exact quadrature is
    `8.29e-07` (relative `6.63 ppm`). Callers MUST NOT assume a 1e-12-accurate
    regularized beta over all `signature_dim >= 2`; see
    `canonical_voronoi_angle` for the validated band. Pure stdlib
    (math.lgamma + math.exp).

    Per fix-openspec-doc-bugs-apply design.md Decision 1 + Risk 1 mitigation:
    avoids scipy dependency by direct Gauss–Legendre quadrature.
    """
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    # Transform [0, x] to [-1, 1]: t = x * (1 + u) / 2.
    half_x = x / 2.0
    # 8-point Gauss–Legendre nodes and weights on [-1, 1].
    nodes = [
        -0.9602898564975363,
        -0.7966664774136267,
        -0.5255324099163290,
        -0.1834346424956498,
        0.1834346424956498,
        0.5255324099163290,
        0.7966664774136267,
        0.9602898564975363,
    ]
    weights = [
        0.1012285362903763,
        0.2223810344533745,
        0.3137066458778883,
        0.3626837833783620,
        0.3626837833783620,
        0.3137066458778883,
        0.2223810344533745,
        0.1012285362903763,
    ]
    integral = 0.0
    for node, weight in zip(nodes, weights, strict=True):
        t = half_x * (1.0 + node)
        if t <= 0.0:
            continue
        # log(t) − log(1−t) formulation to avoid 0**negative.
        log_t = math.log(t) if t > 0 else -math.inf
        log_one_minus_t = math.log1p(-t) if t < 1 else -math.inf
        log_integrand = (a - 1.0) * log_t + (b - 1.0) * log_one_minus_t
        integral += weight * math.exp(log_integrand)
    integral *= half_x  # Jacobian of t = x·(1+u)/2 mapping
    incomplete = math.exp(math.log(max(integral, 1e-300)) - log_beta)
    return min(1.0, max(0.0, incomplete))


# ---------------------------------------------------------------------------
# Spherical cap area and its inverse (shared by the closed form and the
# measurement layer)
# ---------------------------------------------------------------------------

VORONOI_AREA_SAMPLES = 1_000_000
"""Monte-Carlo probe count used by `voronoi_angle` to estimate cell areas.

At the MVP point `(N_e=16, d_c=16)` this yields a standard error of the
returned mean of ≈ `0.0071°` (per-cell SD `0.0284°` at `dG/dθ = 0.488421`,
averaged over 16 cells), so `5σ ≈ 0.0355°`.
"""

VORONOI_AREA_SEED = 20260929
"""Fixed probe seed, so `voronoi_angle` is deterministic and pinnable.

Measured crosspolytope spread across seeds 0 / 1 / 20260929 / 42 at
`VORONOI_AREA_SAMPLES = 1_000_000` is `6.6e-5° .. 8.6e-5°` away from
`canonical_voronoi_angle(32, 16)`.
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

    Accuracy note: the impl-internal residual is always ~1e-15..1e-14
    because it is measured against `_betainc_regularized` itself. The TRUE
    closed-form residual is dominated by that helper's error and varies
    strongly with `signature_dim` — measured at `N_e = 16`:
    `d_c=2 → 3.35e-03`, `d_c=4 → 1.37e-05`, `d_c=6 → 2.21e-07`,
    `d_c=8 → 7.39e-09`, `d_c=16 → 4.15e-07`, `d_c=32 → 4.29e-05`.
    MVP is frozen at `d_c = 16` (`CLAUDE.md` §5); outside that the returned
    float is still a genuine root of the impl-internal equation, but its
    accuracy against the exact regularized incomplete beta is NOT bounded
    by the spec's `< 1e-9` claim.

    The body delegates to `_cap_radius(1 / N_e, d_c)`, which solves the same
    root: `1/N_e ≤ 0.5` places it in the small-cap branch, where
    `_cap_radius` reproduces this function's former `(0, π/2)` bisection to
    `0.00e+00` at `(16, 16)`, `(32, 16)` and `(64, 16)`.

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

    One-sidedness (Jensen). `G` is convex in θ on its first convex branch, so
    `G⁻¹` is concave on the matching area interval; if every `θ̂_i` lies in
    that branch then

        θ̂ = (1/N_e) Σ G⁻¹(A_i) ≤ G⁻¹((1/N_e) Σ A_i) = G⁻¹(1/N_e) = canonical

    with equality iff `A_1 = ⋯ = A_{N_e}`. The precondition is NOT vacuous
    and is NOT global: measured at `d_c = 16`, `G` is convex on `(0°, 81.9°)`,
    concave on `(82.8°, 90.0°)`, convex on `(90.9°, 97.2°)` and concave on
    `(98.1°, 179.1°)`. The MVP operating point `canonical(16, 16) = 67.24°`
    sits inside the first convex branch, and measured MVP cell areas
    (largest ≈ 0.077 vs `1/16 = 0.0625`) stay well inside it. Beyond that
    branch the inequality still held in every measured configuration
    (8 cases, cell radii out to `109.09°`) but that is OBSERVED BEHAVIOUR,
    NOT A THEOREM — it is guarded by
    `test_voronoi_angle_one_sided_gap`, not asserted as a closed form.

    Corrected inversion, for the record. The superseded implementation fed
    the mean pairwise CHORD `c = √(2·(1−cos θ))` into the slot that expects a
    VERSINE `1−cos θ`, computing `arccos(1 − c)` instead of `arccos(1 − c²/2)`
    — the chord magnitude was mistaken for the versine. That inflated the
    output over the sampled grid (10°/45°/60°/120°/150°) by
    `+24.3416° / +31.4300° / +30.0000° / +17.0586° / +8.7253°`; those are the
    min/max of THAT SAMPLE, not a global bound. A 1.8e6-point scan gives the
    true peak `+31.5868°` at `θ* = 2·arcsin(1/3) = 38.9420°` (derivation:
    `e(θ) = arccos(1 − 2sin(θ/2)) − θ`, `e′ = 0 ⟺ 3s² − 4s + 1 = 0 ⟺ s = 1/3`),
    and the error vanishes at BOTH ends (`e(180°) = 0`, `e(0.5°) = +7.07°`,
    `e(179°) = +0.29°`). The superseded implementation also averaged over all
    `i < j` pairs, which is not a Voronoi quantity at all: at the crosspolytope
    it returned `115.6651°` where the canonical answer is `62.5445°`.

    Measurement error. `VORONOI_AREA_SAMPLES = 1_000_000` probes give the
    returned mean a standard error of ≈ `0.0071°` at MVP (`5σ ≈ 0.0355°`).
    Do not read a gap smaller than that as a real deviation — use
    `test_voronoi_angle_equal_area_witness_crosspolytope` for the
    equal-area reference point, where the TRUE gap is `6.5e-5°`.
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

    generator = torch.Generator().manual_seed(VORONOI_AREA_SEED)
    probes = torch.nn.functional.normalize(
        torch.randn(VORONOI_AREA_SAMPLES, d_c, generator=generator), dim=-1
    )
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
