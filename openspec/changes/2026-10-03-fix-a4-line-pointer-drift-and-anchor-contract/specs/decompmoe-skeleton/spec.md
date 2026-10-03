# Spec Delta — `decompmoe-skeleton`

## MODIFIED Requirements

<a id="req-16"></a>

### Requirement: Centroid Driver Semantic Invariants

The package's `CentroidDriver` SHALL enforce four semantic invariants that **cannot be verified by literal-token grep alone** (data-flow analysis, runtime observation, and arithmetic comparison are required). These are the **semantic counterpart** to Requirement "Hard-Constraint Grep Invariants" and are the landing site for the two invariants that req-15 removed from grep scope:

1. **Empty-cell fallback**: `CentroidDriver.step(centroids, X, mask)` with `n_i = |T_i| = 0` MUST preserve `c_i^(t+1) == c_i^(t)` element-wise (no direction randomization). The driver MUST NOT use `.clamp_min(ε)` as a denominator in the empty-cell branch. Verified by `test_empty_cell_preserves_centroid`.

2. **Spherical re-projection (driver output invariant)**: After every `CentroidDriver.step(...)` call across all four active phases, `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`. Verified by `test_spherical_norm_is_strictly_one`.

3. **Near-zero candidate fallback (EMA phases 1–3)**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse) during Phases 1–3 EMA, `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears. Verified by `test_near_zero_candidate_fallback`.

4. **Near-zero candidate fallback (Phase 4 PROJECTED_SGD)**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` during Phase 4 projected SGD, the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears (the same `torch.where(use_old, prev, normalize(...))` guard pattern used in EMA must apply to Phase 4 — `centroids / ‖centroids‖.clamp_min(eps)` does NOT satisfy this invariant). Verified by `test_near_zero_candidate_fallback_phase4`.

#### Scenario: Semantic invariants are enforced by the named test scenarios
- **WHEN** the four named test scenarios (`test_empty_cell_preserves_centroid`, `test_spherical_norm_is_strictly_one`, `test_near_zero_candidate_fallback`, `test_near_zero_candidate_fallback_phase4`) all pass
- **THEN** the empty-cell fallback, spherical re-projection, and near-zero candidate fallback invariants hold for `CentroidDriver` across all four active phases


#### Scenario: Voronoi closed form is not the arctan shortcut

- **WHEN** `canonical_voronoi_angle(N_e, d_c)` is evaluated at the MVP point `(N_e = 16, d_c = 16)`
- **THEN** it returns the root of the defining equation `½ · I_{sin²θ}((d_c − 1)/2, 1/2) = 1/N_e`, which is `1.173547425920 rad` (`67.239315°`) at `d_c = 16` — **NOT** the forbidden token `arctan(pi / sqrt(d_c))`, which evaluates to `0.665773750028 rad` (`38.146026°`) at the same point and MUST NOT be the implementation's closed form
- **AND** the returned value MUST satisfy `pytest.approx(1.173547, abs=1e-6)` (the 6dp spec literal, per governance req-gov-1 obligation 3) with the actual value embedded in the failure message as `f"actual={...}"`
- **AND** a substitution of the forbidden token MUST move the result outside that tolerance by at least `1e5` times (measured: `5.078e-01` absolute error at `N_e = 16`, i.e. `507_773×` the `abs=1e-6` tolerance), so the guard discriminates rather than merely passing
- **AND** the residual frame is named: `|½·I_{sin²θ}(7.5, 1/2) − 1/16| < 1e-9` measured against the implementation-internal reference `src/decompmoe/sphere.py::_betainc_regularized`
- **AND** this Scenario is the guard that Requirement "Hard-Constraint Grep Invariants" refers to when it states the removed invariants are enforced here; the referenced name MUST be `test_canonical_voronoi_angle_not_arctan_shortcut`

<a id="req-18"></a>

### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension

The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask, *, grad=None, eta=1e-2) -> Tensor` method MUST apply, per phase. **`mask` is a REQUIRED positional parameter and MUST NOT be given a default value:** per-expert masked means `m_i` are undefined without it, and a defaulted `mask=None` invites an implementation to substitute a whole-batch mean for `m_i`, which silently broadcasts one mean to every centroid and collapses all territories to a single point. An implementation MUST reject a missing `mask` rather than substitute one.

- Phase 0 (SEEDING): `c_i ← c_i.detach()` (driver is a no-op returning the input centroids detached from the autograd graph); `c_i.requires_grad = False`. Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds. **The caller MUST supply Phase 0 seeds already satisfying `‖c_i‖₂ ≡ 1.0`** — this is a normative obligation on the caller, not a description of the driver's behaviour, and the driver MUST NOT normalise, project, or otherwise repair Phase 0 inputs. This elevation is the deliberate half of a paired correction: `wayfinder` req-23 previously asserted the spherical-norm invariant for "any Phase (including 0 K-Means)" while simultaneously declaring this driver a no-op, giving two peer specs mutually exclusive MUSTs for the same quantity. `wayfinder` req-23 has since been narrowed to **Phase 1–4**; this Requirement is the corresponding owner of the Phase 0 obligation, and the two MUSTs are no longer in conflict.
- Phase 1 (EMA_090): `c_i ← Normalize(0.90 · c_i + 0.10 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 2 (EMA_095): `c_i ← Normalize(0.95 · c_i + 0.05 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 3 (EMA_099): `c_i ← Normalize(0.99 · c_i + 0.01 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 4 (PROJECTED_SGD): When `grad is not None`: `candidate_i = c_i − eta · grad_i`; then `c_i^(t+1) = candidate_i / ‖candidate_i‖₂`. When `grad is None`: `c_i^(t+1) = c_i / ‖c_i‖₂` (L2 retraction of the input only). Both branches apply the Invariant #4 guard pattern: when `‖candidate_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)` (no `clamp_min(ε)` denominator; the same `torch.where(use_old, prev, normalize(...))` pattern used in EMA). Driver Active, gradient channel Active.

The `m_i` is the masked-mean over tokens assigned to expert `i`. The driver MUST enforce the empty-cell invariant: if `n_i = |T_i| = 0`, then `m_i ≡ c_i^(t−1)` (no `clamp_min(ε)` denominator). The driver MUST enforce the spherical re-projection invariant: `‖c_i^(t+1)‖₂ ≡ 1.0` after every step; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)`. The driver MAY call `decompmoe.safeguards.should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]` for dead-expert detection; the function itself lives in `safeguards.py` and is *called* from the driver (the driver MUST NOT define a same-named helper). When `threshold=None` is passed, the implementation derives the effective threshold via the private helper `_dead_expert_threshold(N_e) = 1/(2·N_e)`; at MVP `N_e = 16` this yields `1/32`. The dead-expert rule is parameterized by `N_e`, not hardcoded `1/128`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200` and `RESURRECTION_RATE_LIMIT_STEPS = 1000` are `Final[int]` module-level constants (see `src/decompmoe/safeguards.py:30-31`); the spec references the constant identifiers rather than literal values to ensure the spec stays in lock-step with the code if these constants are retuned.

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `safeguards.py::clip_global_grad_norm_` as of commit `d3689a1`.

The `step` signature `(*, grad=None, eta=1e-2)` REPLACES the legacy `(centroids, X, mask, eps=1e-6)` contract: the `eps` parameter is removed (no longer used by any active phase); the `grad` keyword is REQUIRED for the projected SGD step (no positional gradient argument); the `eta` keyword defaults to `1e-2` (conservative; spec does not pin a specific value beyond the linear convention); when `grad is None` the P4 branch is the identity L2 retraction (no SGD step applied — this is the backward-compatible fallback for callers that do not provide a gradient). Callers that previously passed `eps=1e-6` will need to remove the kwarg (breaking change; no in-repo callers pass `eps`).

#### Scenario: Phase-4 SGD-1-step closed form

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called with `centroids ∈ R^{N_e × d_c}` (unit-norm rows), `grad ∈ R^{N_e × d_c}` with `‖grad_i‖₂ = 0.05` for all `i`, and `eta = 1e-2`
- **THEN** for every expert `i` where `‖centroids[i] − eta · grad[i]‖₂ ≥ 1e-9`: `c_i^(t+1) == (centroids[i] − eta · grad[i]) / ‖centroids[i] − eta · grad[i]‖₂` within `abs=1e-7` (closed-form SGD step followed by L2 retraction)
- **AND** for every expert `i`: `‖c_i^(t+1)‖₂ == 1.0` within `abs=1e-7` (spherical re-projection invariant holds after the full P4 path, including the SGD step)

#### Scenario: Phase-4 SGD with near-zero candidate falls back to c_i^(t)

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called and for some expert `i` the post-SGD candidate `‖centroids[i] − eta · grad[i]‖₂ < 1e-9` (e.g. `centroids[i] = +grad[i] / ‖grad[i]‖₂` and `eta · ‖grad[i]‖₂ = 1`)
- **THEN** `c_i^(t+1) == c_i^(t)` element-wise (Invariant #4 fallback applies to the full P4 path, not only to the EMA branches) and no NaN appears in the centroid tensor

#### Scenario: Phase-4 with `grad=None` preserves the legacy L2-retraction semantics

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask)` is called with the default `grad=None` and `eta=1e-2`
- **THEN** `c_i^(t+1) == centroids[i] / ‖centroids[i]‖₂` element-wise within `abs=1e-7` (the legacy P4 behavior — L2 retraction of the input — is preserved exactly when no gradient is provided; this is the backward-compatibility contract for callers predating the SGD step addition)

---


<a id="req-21"></a>

### Requirement: Frozen MVP Hyperparameter Set — D1 Geometric-Only Fields

The package SHALL provide a `MVPConfig` frozen dataclass whose locked constants equal: `d_model == 1024`, `N_e == 16`, `k == 2`, `d_ffn == 2048`, `L == 4`, `d_ffn_dense == 4096`, `d_c == 16`, `H_kv == 8`, `d_k == 128`, `β_initial ≈ 1.035` (per wayfinder `Req 7` "Isotropic Squared-Chord Distance And Bounded Beta" (`#req-7`) closed-form `β_0 = 0.1 + 31.9·σ(γ_init)` with `γ_init ≈ −3.5`; 50-digit mpmath `β_0 = 1.0350601609682665718`). Attempting to mutate any field SHALL raise `dataclasses.FrozenInstanceError`. A factory function `MVPConfig()` SHALL return an instance with all default values.

**MVPConfig carries only GEOMETRIC constants** (model shape: `d_model`, `N_e`, `k`, `d_ffn`, `L`, `d_ffn_dense`, `d_c`, `H_kv`, `d_k`, `vocab_size`) **plus the specific initial value `β_initial ≈ 1.035`** (narrative 4-sig-fig; wayfinder `Req 7` "Isotropic Squared-Chord Distance And Bounded Beta" (`#req-7`) closed-form anchor). The algorithmic range constants `β_min = 0.1` and `β_max = 32` live as module-level `Final[float]` in `decompmoe/beta.py` (NOT in MVPConfig), per `design.md` Decision 1: "Algorithmic constants live with their usage site". MVPConfig does not carry `β_min` or `β_max` fields, and the canonical sources for those constants are `decompmoe.beta.BETA_MIN` and `decompmoe.beta.BETA_MAX`.

**Source:** `wayfinder/tickets/A4-1.md`, change `fix-math-consistency-audit-2026-08` design.md (Decision 1)

#### Scenario: Field defaults locked

- **WHEN** `MVPConfig()` is constructed
- **THEN** `cfg.d_model == 1024 and cfg.N_e == 16 and cfg.k == 2 and cfg.d_ffn == 2048 and cfg.L == 4`

#### Scenario: Mutation rejected

- **WHEN** any field is assigned after construction
- **THEN** `dataclasses.FrozenInstanceError` is raised

#### Scenario: MVPConfig field set is exactly the geometric constants plus β_initial

- **WHEN** the set of dataclass field names on `MVPConfig` is enumerated via `[f.name for f in dataclasses.fields(MVPConfig)]`
- **THEN** the set equals exactly `{'d_model', 'N_e', 'k', 'd_ffn', 'L', 'd_ffn_dense', 'd_c', 'H_kv', 'd_k', 'beta_initial', 'vocab_size'}` (11 fields; **`β_min` and `β_max` are NOT MVPConfig fields**; they live as `Final[float]` in `decompmoe/beta.py`)

#### Scenario: MVPConfig.beta_initial default matches spec closed-form derivation

- **WHEN** `MVPConfig().beta_initial` is compared against `0.1 + 31.9·σ(γ_init=−3.5)` evaluated via `torch.sigmoid`
- **THEN** `abs(MVPConfig().beta_initial − closed_form_value) ≤ 1e-3` (covers narrative 4-sig-fig truncation to 1.035 from 50-digit 1.0350601609682665718)
- **AND** the test does NOT degenerate to a self-referential check (i.e., `MVPConfig().beta_initial ≈ literal_value`); the closed form MUST be derived from `β_min + (β_max−β_min)·σ(γ_init)` per wayfinder `#req-7` Sigmoid 闭式

---


<a id="req-23"></a>

### Requirement: No decompmoe-skeleton spec changes required for cycle-12 finding 1 closure

The system SHALL NOT modify any `decompmoe-skeleton` spec Requirement as part of cycle-12 finding 1 closure. The cycle-12 finding 1 (ticket A8-2 L70 centered-covariance + L74 CV/convex-hull vs spec L413 uncentered second moment) is **purely a wayfinder spec scope concern** — but `decompmoe-skeleton` **does** own a verbatim mirror of the wayfinder Req 20 closed-form definitions (see below), so this Requirement serves as an explicit declaration that the existing mirror is already aligned and no new mirror / no new behavior is being introduced by this change.

**Why no decompmoe-skeleton changes are needed**:

- `decompmoe-skeleton` Requirement `<a id="req-22">` ("Eight Metrics And Classification — CG Type Guard", `openspec/specs/decompmoe-skeleton/spec.md` L500-518) **verbatim mirrors** `wayfinder` Req 20 closed-forms:
  - The closed-form table enumerates `L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, `MCI`, `CG` — the same 8 metric names wayfinder `Req 20` "Eight Geometric Quantification Metrics" (`#req-20`) defines
  - Each closed-form matches the corresponding wayfinder `#req-20` row verbatim (post-229016fe + 09-22 line-drift correction)
  - L515 explicitly mirrors the `MCI` row from `wayfinder/spec.md` L413, including the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (lower bound `1/d_c` on `S^{d_c−1}` makes `< 0.05` health target unreachable), the centered-covariance supersede reasoning (`(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations
- `decompmoe-skeleton` Requirement `<a id="req-22">` also defines `MCI closed-form on uniform token distribution` and `MCI closed-form on rank-1 token distribution` Scenarios (both `abs=1e-12`) — these mirror the two corresponding Scenarios under wayfinder `#req-20` verbatim
- cycle-12 finding 1 is specifically about `MCI` (an eight-metric row in `wayfinder` spec.md L413), implemented in `src/decompmoe/metrics.py` per `wayfinder` spec — `decompmoe-skeleton` mirrors the closed-form but does not own a separate MCI definition; both capabilities use the same uncentered second moment reading
- The `(historical, ...)` supersede annotations appended to ticket `A8-2.md` L70 + L74 in this change apply to ticket lineage only; they do NOT modify the `decompmoe-skeleton` Req-22 mirror of the L413 closed-form (the mirror is already aligned with the canonical uncentered second moment reading)

**Source:** `wayfinder/tickets/A8-2.md` (cycle-12 finding 1 evidence — wayfinder `#req-20` owns the MCI closed-form; this capability's metric table is a verbatim mirror and is already flagged as a drift hazard)

#### Scenario: decompmoe-skeleton mirror of wayfinder Req 20 MCI closed-form is already aligned

- **WHEN** `openspec/specs/decompmoe-skeleton/spec.md` Req 22 (L500-518) is read for the `MCI` closed-form
- **THEN** the text at L515 verbatim contains the uncentered second moment definition (`M = (1/|T|) · Σ_{t} C_t C_tᵀ`), the CV supersede reasoning (`replaces CV (whose lower bound 1/d_c on S^{d_c−1} made the original < 0.05 health target unreachable — see wayfinder/tickets/A8-2.md)`), the centered-covariance supersede reasoning (`The centered-covariance reading has its (1/d_c, 1] upper endpoint unreachable at |T| = d_c`), the `MCI ∈ [1/d_c, 1]` range, and the uniform/rank-1 endpoint characterizations — all mirroring wayfinder spec.md L413 verbatim
- **AND** the `MCI closed-form on uniform token distribution` and `MCI closed-form on rank-1 token distribution` Scenarios use `abs=1e-12` (mirroring the two corresponding Scenarios under wayfinder `#req-20`) — both endpoints of the declared `[1/d_c, 1]` range are guarded
- **AND** no `decompmoe-skeleton` Requirement is listed in the "Affected code / Affected Requirements" sections of `proposal.md` for this change (the mirror is unchanged)
- **AND** the `decompmoe-skeleton` spec.md anchor coverage remains unchanged (existing anchors per archived changes `2026-09-15-fix-skeleton-spec-duplicate-and-completeness-2026-09-15` + `2026-09-16-fill-skeleton-spec-leading-anchor-gaps` are not affected by this change)

<a id="req-15"></a>

<a id="req-15"></a>

<a id="req-15"></a>

### Requirement: Hard-Constraint Grep Invariants

The package SHALL satisfy the following source-level invariants, asserted by **literal-token grep tests** (any invariant requiring data-flow / semantic analysis is NOT a grep invariant; see Requirement "Centroid Driver Semantic Invariants" for the semantic layer):
- NO occurrence of `StraightThroughEstimator` or `straight_through` in `src/decompmoe/`
- NO occurrence of `w_i` in the body of `distance.logit` (signature-level invariant already covered)
- NO occurrence of `shared` attribute in `ExpertPool`
- NO import of `torch.utils.cpp_extension` or `triton` in `experts.py`
- NO field `kv_cache_c` in `GeometricRouter` Protocol

(The two previously-listed invariants — `.clamp_min(ε)` empty-cell denominator and the literal `arctan(pi / sqrt(d_c))` token — are removed from this Requirement because they cannot be verified by literal grep alone: the former requires data-flow analysis (the `.clamp_min` call result must be checked to be a denominator), and the latter can be circumvented by a syntactically different but semantically equivalent expression. Both invariants are restated under decompmoe-skeleton Req 16 Centroid Driver Semantic Invariants (`#req-16`), each with its own named guard: the `.clamp_min(ε)` empty-cell denominator by Scenario "Semantic invariants are enforced by the named test scenarios" via `tests/test_schedule.py::test_empty_cell_preserves_centroid`, and the `arctan(pi / sqrt(d_c))` token by Scenario "Voronoi closed form is not the arctan shortcut" via `tests/test_sphere.py::test_canonical_voronoi_angle_not_arctan_shortcut`.)

#### Scenario: Hard constraints hold
- **WHEN** the literal-token grep invariants above are evaluated against `src/decompmoe/`
- **THEN** all invariants pass

