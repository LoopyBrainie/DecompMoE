## ADDED Requirements

### Requirement: No decompmoe-skeleton spec changes required for cycle-12 finding 1 closure

The system SHALL NOT modify any `decompmoe-skeleton` spec Requirement as part of cycle-12 finding 1 closure. The cycle-12 finding 1 (ticket A8-2 L70 centered-covariance + L74 CV/convex-hull vs spec L408 uncentered second moment) is **purely a wayfinder spec scope concern** — but `decompmoe-skeleton` **does** own a verbatim mirror of the wayfinder Req 20 closed-form definitions (see below), so this Requirement serves as an explicit declaration that the existing mirror is already aligned and no new mirror / no new behavior is being introduced by this change.

**Why no decompmoe-skeleton changes are needed**:

- `decompmoe-skeleton` Requirement `<a id="req-22">` ("Eight Metrics And Classification — CG Type Guard", `openspec/specs/decompmoe-skeleton/spec.md` L500-518) **verbatim mirrors** `wayfinder` Req 20 closed-forms:
  - L504 enumerates `L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, `MCI`, `CG` (all 8 metric names from wayfinder L396-409)
  - L500-518 each closed-form matches wayfinder L389-L407 verbatim (post-229016fe drift)
  - L515 explicitly mirrors the `MCI` row from `wayfinder/spec.md` L408, including the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (lower bound `1/d_c` on `S^{d_c−1}` makes `< 0.05` health target unreachable), the centered-covariance supersede reasoning (`(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations
- `decompmoe-skeleton` Requirement `<a id="req-22">` also defines `MCI closed-form on uniform token distribution` (L560-563, abs=1e-12) and `MCI closed-form on rank-1 token distribution` (L565-568, abs=1e-12) Scenarios — these mirror wayfinder L445-447 + L449-451 Scenarios verbatim
- cycle-12 finding 1 is specifically about `MCI` (an eight-metric row in `wayfinder` spec.md L408), implemented in `src/decompmoe/metrics.py` per `wayfinder` spec — `decompmoe-skeleton` mirrors the closed-form but does not own a separate MCI definition; both capabilities use the same uncentered second moment reading
- The `(historical, ...)` supersede annotations appended to ticket `A8-2.md` L70 + L74 in this change apply to ticket lineage only; they do NOT modify the `decompmoe-skeleton` Req-22 mirror of the L408 closed-form (the mirror is already aligned with the canonical uncentered second moment reading)

**Source:** `wayfinder/tickets/A8-2.md` (cycle-12 finding 1 evidence — wayfinder spec.md L408 owns the MCI closed-form; decompmoe-skeleton L502-568 is a verbatim mirror and is already aligned)

#### Scenario: decompmoe-skeleton mirror of wayfinder Req 20 MCI closed-form is already aligned

- **WHEN** `openspec/specs/decompmoe-skeleton/spec.md` Req 22 (L500-518) is read for the `MCI` closed-form
- **THEN** the text at L515 verbatim contains the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (`replaces CV (whose lower bound 1/d_c on S^{d_c−1} made the original < 0.05 health target unreachable — see wayfinder/tickets/A8-2.md)`), the centered-covariance supersede reasoning (`The centered-covariance reading has its (1/d_c, 1] upper endpoint unreachable at |T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations — all mirroring wayfinder spec.md L408 verbatim
- **AND** L560-563 `MCI closed-form on uniform token distribution` and L565-568 `MCI closed-form on rank-1 token distribution` Scenarios use `abs=1e-12` (mirroring wayfinder L445/L449 Scenarios) — both endpoints of the declared `[1/d_c, 1]` range are guarded
- **AND** no `decompmoe-skeleton` Requirement is listed in the "Affected code / Affected Requirements" sections of `proposal.md` for this change (the mirror is unchanged)
- **AND** the `decompmoe-skeleton` spec.md anchor coverage remains unchanged (existing anchors per archived changes `2026-09-15-fix-skeleton-spec-duplicate-and-completeness-2026-09-15` + `2026-09-16-fill-skeleton-spec-leading-anchor-gaps` are not affected by this change)