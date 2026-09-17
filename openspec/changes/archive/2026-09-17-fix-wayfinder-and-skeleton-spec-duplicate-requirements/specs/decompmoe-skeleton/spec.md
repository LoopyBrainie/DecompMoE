# Delta for `decompmoe-skeleton`

## REMOVED Requirements

### Requirement: Frozen MVP Hyperparameter Set
**Reason**: Replaced by ADDED Req "Frozen MVP Hyperparameter Set — D1 Geometric-Only Fields" at L536, which is the authoritative source for geometric-only hyperparameters (`d_c`, `θ_Voronoi`, `θ_{1/e}`) after `04fd653`. The original Req (L20) duplicated the master `wayfinder` Req "4070 MVP Hyperparameter Set" verbatim — keeping it as a separate skeleton entry created two independent edit surfaces for the same frozen numbers.

**Migration**: All references to "Frozen MVP Hyperparameter Set" in skeleton must resolve to L536 ADDED. The master `wayfinder/spec.md` Req "4070 MVP Hyperparameter Set" (L184) remains the source of truth for the full MVP hyperparameter set (d_model, N_e, k, d_ffn, L, β_min, β_max, d_c); skeleton L536 ADDED is the slice that the package-level code (`src/decompmoe/config.py`) actually consumes.

### Requirement: Spherical L2 Normalization
**Reason**: Replaced by ADDED Req "Spherical L2 Normalization — max(…z…, ε) Formula" at L489, which pins the exact degenerate-input formula `z / max(‖z‖₂, ε)` with `ε = 1e-12`. The original Req (L94) described only the conceptual normalization, leaving the degenerate case to implementation discretion — which historically caused zero-division on all-zero centroid inputs.

**Migration**: Any code-level reference to "Spherical L2 Normalization" must resolve to L489 ADDED. The Scenarios under L94 are kept as orphan content under L489 ADDED since the underlying math invariant `‖z‖₂ > 0 ⇒ output ‖·‖₂ = 1` is identical.

### Requirement: Centroid Four-Phase Lifecycle Driver
**Reason**: Replaced by ADDED Req "Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension" at L454, which extends the original 4-phase driver with the Phase-4 projected-SGD step (`c_i^(t+1) = c_i^(t) − η·grad_c_i L_routing`, then re-projection). The original Req (L145) stopped at Phase 3 (EMA 0.99), leaving Phase 4 unspecified in skeleton — which was the root cause of the Phase-4 implementation ambiguity surfaced in `fix-math-consistency-audit-2026-08`.

**Migration**: `CentroidDriver.step()` implementation (in skeleton terms: any 4-phase centroid driver module) MUST be written against L454 ADDED's full 5-phase signature `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The master `wayfinder/spec.md` Req "C Extraction Differentiability And Centroid Lifecycle" (L78) remains the source of truth for the lifecycle math invariants; skeleton L454 ADDED is the slice the package-level driver code consumes.

### Requirement: Eight Metrics And Classification
**Reason**: Replaced by ADDED Req "Eight Metrics And Classification — CG Type Guard" at L562, which adds the explicit `CG (centroid–gradient) projection` type guard scenarios (`CG` MUST return a `Tensor` with shape `(N_e, d_c)`, not `(N_e,)`; a missing `.detach()` MUST raise `TypeError` at the metric boundary). The original Req (L307) listed the 8 metrics but did not pin the CG type contract, which led to silent shape drift when centroid gradients were projected to `f_per_expert`-shaped tensors by mistake.

**Migration**: Any code reference to "Eight Metrics And Classification" must resolve to L562 ADDED. The 8 metric identities (SP, D_chord, MCI, CG, S_load, UR, R_H, L_sep) and their definitions are unchanged — only the CG type guard is new.

### Requirement: Beta Parameterization Operational Domain
**Reason**: Replaced by ADDED Req "Beta Parameterization Operational Domain — D1 Module-Level Constants" at L510, which removes the `cfg: MVPConfig` keyword-only argument from the `beta_effective(gamma, phase, step, *, cfg) -> Tensor` signature, leaving `beta_effective(gamma, phase, step) -> Tensor` (3 positional args). The original Req (L432) threaded `cfg` through `beta_effective` to source `β_min` / `β_max`, but `fix-math-consistency-audit-2026-08` Decision 1 concluded those constants belong as module-level `Final[float]` in `decompmoe/beta.py` — not in `MVPConfig` — to avoid indirection cost and to keep the call site focused on schedule / phase decision. The Scenarios at L436 / L440 / L444 are retained as orphan Scenarios under L510 ADDED since they reference the same math invariants.

**Migration**: `beta_effective` callers MUST use the 3-positional-arg signature `beta_effective(gamma, phase, step) -> Tensor`. Any code passing `cfg=...` to `beta_effective` is non-conforming and SHOULD be updated as part of this change (no callers exist today — see `Impact` section of `proposal.md`).
