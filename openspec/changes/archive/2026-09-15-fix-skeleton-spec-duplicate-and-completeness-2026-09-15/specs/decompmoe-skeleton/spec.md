# Delta for `decompmoe-skeleton`

## MODIFIED Requirements

### Requirement: Eight Metrics And Classification — CG Type Guard

The package SHALL provide eight metric functions (`L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, `MCI`, `CG`) whose closed forms MUST match the master `wayfinder` Req 20 verbatim:

**Realtime Tier** (every step):
- `L_sep = (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form).
- `R_H = −(1 / ln N_e) · Σ_i f_i · ln f_i`, normalized entropy; `R_H ∈ [0, 1]`.
- `S_load = N_e · max_i f_i`; `1` at perfect uniformity, `N_e` at full collapse.
- `UR = (1 / N_e) · Σ_i I[f_i > 0]` over the most recent W = 100 steps.

**Offline Tier** (diagnostic runs):
- `SP_i = (1 / ‖T_i‖₁) · Σ_{t ∈ T_i} c_iᵀ C_t`; aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` (skip experts with empty `T_i`). `SP ∈ [-1, 1]`.
- `D_chord = (2 / (N_e(N_e−1))) · Σ_{i<j} √(2(1 − c_iᵀ c_j))` (mean spherical chord).
- `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / |T|) · Σ_{t} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`); **effective-dimensionality fraction**; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range). Uniform token distribution (each basis `e_j` equally represented in `T`) ⇒ `M = I/d_c` exactly ⇒ `MCI = 1.0`. Rank-1 token distribution (all `C_t = e_1`) ⇒ `M = e_1 e_1ᵀ` exactly ⇒ `MCI = 1/d_c`. The previous formula `(1/d_c) · Σ 1/λ̃²` was mathematically inconsistent with the declared range and MUST NOT appear. MCI takes **token signatures** as input (NOT centroids), per the definition.
- `CG = ‖∇_{W^{K, V, b}} L_total‖₂` (debug-only); non-negative; zero on zero gradient.

The four offline metric implementations MUST implement the closed forms above (and verify with the closed-form numerical Scenarios below — not the prior structural `!= torch.tensor(0.0)` assertion). The `OFFLINE` set in `metrics.__all__` MUST use the spec name `"D_chord"` (not the implementation alias `"D_c"`). The package SHALL expose `REALTIME = frozenset({"L_sep", "R_H", "S_load", "UR"})` and `OFFLINE = frozenset({"SP", "D_chord", "MCI", "CG"})`. `L_sep` from the metrics module SHALL be numerically equivalent to `L_sep` from the loss module under the same input. `R_H` SHALL lie in `[0, 1]` when fed a normalized probability distribution over `N_e` experts. (Matches master `wayfinder` Req 20 verbatim.)

#### Scenario: Metric classification

- **WHEN** `metrics.REALTIME ∪ metrics.OFFLINE` is computed
- **THEN** the union has cardinality exactly `8` and equals the eight metric names

#### Scenario: R_H bounded

- **WHEN** `R_H(p)` is called for any probability vector `p`
- **THEN** the result lies in `[0, 1]` within `1e-6`

#### Scenario: L_sep cross-module consistency

- **WHEN** `metrics.L_sep(c_centroids)` is compared to `loss.compute_L_sep(c_centroids)` under the same input
- **THEN** the two values are equal within `1e-6`

#### Scenario: SP closed-form on orthonormal-aligned inputs

- **WHEN** `SP(orthonormal_centroids, assignments, signatures)` is called with every assigned token's signature exactly aligned with its centroid (`C_t = c_{a(t)}` for all `t ∈ T_i`)
- **THEN** the aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` equals `1.0` within `abs=1e-6` (each `SP_i = c_i^T c_i = 1`)

#### Scenario: SP closed-form on 60° offset

- **WHEN** `SP` is called with every assigned token's signature at `60°` from its centroid (`c_i^T C_t = cos 60° = 0.5`)
- **THEN** the aggregated `SP` equals `0.5` within `abs=1e-6`

#### Scenario: SP closed-form on antipodal-aligned inputs

- **WHEN** `SP(centroids, assignments, signatures)` is called with every assigned token's signature equal to the antipode of its assigned centroid (`C_t = −c_{a(t)}` for all `t ∈ T_i`)
- **THEN** the aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` equals `−1.0` within `abs=1e-6` (each `SP_i = c_iᵀ (−c_i) = −1`)

#### Scenario: SP range bound

- **WHEN** `SP(any_centroids, any_assignments, any_signatures)` is called
- **THEN** `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6`

#### Scenario: D_chord closed-form on orthonormal basis

- **WHEN** `D_chord(c_centroids)` is called with `centroids ∈ R^{N_e × d_c}` forming an orthonormal subset
- **THEN** the result equals `sqrt(2)` within `abs=1e-6`

#### Scenario: MCI closed-form on uniform token distribution

- **WHEN** `MCI(token_signatures)` is called with `|T| = d_c · k` signatures, each `e_j ∈ R^{d_c}` (the `d_c` standard basis vectors) represented exactly `k` times (so the uncentered second moment `M = (1/|T|) · Σ_t C_t C_tᵀ = I/d_c` exactly)
- **THEN** the result equals `1.0` exactly within `abs=1e-12`

#### Scenario: MCI closed-form on rank-1 token distribution

- **WHEN** `MCI(token_signatures)` is called with all `|T|` signatures equal to the same unit vector `e_1` (so `M = e_1 e_1ᵀ` is rank-1)
- **THEN** the result equals `1/d_c` exactly within `abs=1e-12`

#### Scenario: CG zero-gradient invariance

- **WHEN** `CG(zero_grad)` is called with all-zero input gradient
- **THEN** the result equals `0.0` exactly within `abs=1e-12`

#### Scenario: CG positive homogeneity

- **WHEN** `CG(g)` and `CG(2·g)` are both evaluated for any non-zero gradient `g`
- **THEN** `|CG(2·g) − 2·CG(g)| < 1e-6`

#### Scenario: CG raises TypeError on non-floating-point input

- **WHEN** `CG(grad)` is called with `grad` not being a `torch.Tensor` (e.g. `list`, `np.ndarray`, `None`)
- **THEN** it raises `TypeError` referencing the closed form `CG = ‖∇_{W^{K, V, b}} L_total‖₂` (the gradient of a learnable parameter is necessarily a Tensor; non-Tensor inputs are a caller bug)
- **AND WHEN** `CG(grad)` is called with `grad` being a `torch.Tensor` of non-floating-point dtype (`int`, `bool`, etc.)
- **THEN** it raises `TypeError` (the `CG` definition is the `ℓ₂` norm of a learnable-parameter gradient — non-floating-point tensors cannot be such a gradient)

## Structural Cleanup (apply-step direct edit, not a delta requirement)

Three orphan `#### Scenario:` blocks currently sit between req-13 ("Centroid Driver Invariant Test Scenarios", L331-347) and req-14 ("Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension", L365-396) in `openspec/specs/decompmoe-skeleton/spec.md`. These scenarios — "Parameterization endpoints" / "gamma reset for phase 4 boundary continuity" / "beta_effective is continuous at Phase 3 → 4 boundary" — are **verbatim duplicates** of the same three scenarios under req-3 ("Beta Parameterization Operational Domain — D1 Module-Level Constants") at L427-440 in the same file. They have NO `### Requirement:` parent (the previous fix `2026-09-10-fix-wayfinder-and-skeleton-spec-duplicate-requirements` deliberately retained them as orphan Scenarios pending this follow-up cleanup).

**Why this isn't expressed as a delta requirement**: the spec-driven delta format (`ADDED Requirements` / `MODIFIED Requirements` / `REMOVED Requirements`) operates on whole `### Requirement:` blocks with the `Reason` + `Migration` fields. There is no schema entry for "REMOVED Scenario not under any Requirement". The orphan Scenarios removal is a structural edit on the main spec file (delete 14 lines at L347-360) without changing any Requirement body — analogous to deleting a stray comment block.

**Apply-step action**: the apply workflow MUST delete the `---` separator at L347, the three `#### Scenario:` blocks at L349-352 / L353-355 / L357-360, and the `---` separator at L361-362 (14 lines total), as a single Edit operation on `openspec/specs/decompmoe-skeleton/spec.md`. After deletion, `grep -n '^### Requirement:' openspec/specs/decompmoe-skeleton/spec.md` MUST show no orphan `#### Scenario:` blocks between req-13 (formerly L331) and req-14 (formerly L365). The deleted content is preserved verbatim at L427-440 under req-3, so no spec coverage is lost.

**Acceptance check**: `python scripts/lint_no_source_field_drift.py` exit=0 (no change since no `**Source:**` field is added or removed); `openspec validate fix-skeleton-spec-duplicate-and-completeness-2026-09-15 --strict` pass; the orphan Scenarios text no longer appears in the main spec between req-13 and req-14.