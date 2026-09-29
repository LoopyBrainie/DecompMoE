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
    - `voronoi_angle(centroids)` does NOT measure a Voronoi half-angle. It
      computes `arccos(1 − mean_pairwise_chord)`, which (a) applies a wrong
      inverse to the chord (the correct inversion is `arccos(1 − c²/2)`) and
      (b) averages over all centroid pairs rather than the nearest neighbours
      that define a Voronoi cell. See its own docstring for measurements and
      for the required fix. Offline use only — NEVER in the training hot path.

Both functions are pure: no autograd state, no global registries, no hidden
parameters.
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
# Voronoi self-consistency (wayfinder Req 11)
# ---------------------------------------------------------------------------


def canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float:
    """Closed-form Voronoi half-angle on S^{signature_dim − 1}.

    Solves ½ · I_{sin² θ}((d_c − 1)/2, 1/2) = 1 / N_e for θ ∈ (0, π/2)
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

    Returns the angle in radians (multiply by 180/π for degrees).
    """
    if num_experts < 2:
        raise ValueError(f"num_experts must be ≥ 2; got {num_experts}")
    if signature_dim < 2:
        raise ValueError(f"signature_dim must be ≥ 2; got {signature_dim}")
    target = 1.0 / num_experts
    a = (signature_dim - 1) / 2.0
    b = 0.5

    def f(theta: float) -> float:
        s2 = math.sin(theta) ** 2
        return 0.5 * _betainc_regularized(s2, a, b) - target

    lo, hi = 0.0, math.pi / 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13:
            break
    return 0.5 * (lo + hi)


def voronoi_angle(centroids: Tensor) -> float:
    """Centroid-spread angle from a realized centroid tensor — NOT a Voronoi angle.

    Computes the mean pairwise spherical chord length
    `c = mean_{i<j} √(2(1 − cᵢᵀcⱼ))` over ALL pairs, then returns
    `arccos(1 − c)`. Offline use only.

    THIS FUNCTION HAS TWO DEFECTS. Neither is fixed here: both change its
    output, and `CLAUDE.md` §6 forbids changing DecompMoE behaviour outside an
    OpenSpec change that derives the replacement.

    1. Wrong inverse. A chord satisfies `chord = √(2 · versine)` where
       `versine = 1 − cos θ`. The correct inverse is therefore
       `θ = arccos(1 − c²/2)`, which reproduces the true angle exactly. This
       function instead feeds the CHORD LENGTH into the slot that expects a
       VERSINE, computing `arccos(1 − c)`. Measured inversion error
       (averaging held exact by a regular simplex, so only the inversion is
       at fault):

           true    10.0000°  ->  34.3416°   (+24.3416)
           true    45.0000°  ->  76.4300°   (+31.4300)
           true    60.0000°  ->  90.0000°   (+30.0000)
           true   120.0000°  -> 137.0586°   (+17.0586)
           true   150.0000°  -> 158.7253°   ( +8.7253)

       i.e. the output is inflated by +8.7° to +31.4° over the whole range,
       peaking near 45°.

    2. Wrong averaging. The mean runs over all `i < j` pairs, while a Voronoi
       cell half-angle is set by the NEAREST neighbours. The two are not
       commensurable, so this quantity does not converge to
       `canonical_voronoi_angle` for any centroid set.

    Combined effect, measured at the crosspolytope ideal (the 32 vertices
    `±e_i` on S^15, an exactly equal-area partition): this function returns
    115.665°, the correct-inversion value is 91.542°, and
    `canonical_voronoi_angle(32, 16)` is 62.544°. The inversion accounts for
    45.4% of the impl-to-canonical gap; the averaging accounts for the rest.

    Callers must NOT treat `abs(this − canonical) < bound` as evidence of
    equal-area coverage. The correct formalization of a realized Voronoi
    half-angle is the nearest-neighbour inradius
    `θ = mean_i min_{j≠i} angle(c_i, c_j) / 2`; for crosspolytope(32) that is
    45.000°, still not equal to the canonical 62.544° — the gap there is the
    spec/implementation mismatch registered as a hand-off in change
    `2026-09-28-fix-b1-b3-b6-b8-b9-test-protocol-guard-fidelity`.
    """
    if centroids.dim() != 2:
        raise ValueError(
            f"centroids must be 2-D (N_e × d_c); got shape {tuple(centroids.shape)}"
        )
    N_e = centroids.shape[0]
    if N_e < 2:
        raise ValueError(f"need at least 2 centroids; got N_e={N_e}")
    sims = centroids @ centroids.T  # (N_e, N_e) on [-1, 1]
    iu = torch.triu_indices(N_e, N_e, offset=1)
    pair_sims = sims[iu[0], iu[1]]
    pair_chord = torch.sqrt(2.0 * (1.0 - pair_sims).clamp_min(0.0))
    mean_chord = pair_chord.mean().item()
    arg = max(-1.0, min(1.0, 1.0 - mean_chord))
    try:
        return float(math.acos(arg))
    except ValueError as exc:  # defensive: clamp already bounds arg to [-1, 1]
        raise ValueError(f"acos domain violation: arg={arg}") from exc


__all__ = [
    "spherical_l2_normalize",
    "canonical_voronoi_angle",
    "voronoi_angle",
]
