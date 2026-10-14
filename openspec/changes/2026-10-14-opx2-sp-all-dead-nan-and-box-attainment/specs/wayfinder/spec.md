# Spec Delta

## MODIFIED Requirements

<a id="req-20"></a>

### Requirement: Eight Geometric Quantification Metrics

The system MUST report eight metrics in two classes, each with a precise closed-form definition.

**Realtime Tier (computed every step)**
| Metric | Definition | Range / Notes |
|---|---|---|
| `L_sep` | `L_sep = (‖C^T C‖_F² − N_e) / (N_e · (N_e − 1))` (Frobenius form; equivalent `(2/(N_e(N_e−1))) · Σ_{i<j} (c_i^T c_j)²`) | References Req 12; positive scalar |
| `R_H` | `R_H = −(1 / ln N_e) · Σ_{i=1}^{N_e} f_i · ln f_i` | `f_i` = per-expert normalized routing fraction; `R_H ∈ [0, 1]` (1 = uniform, 0 = degenerate). **Windowing deferred**: this row's earlier text said `f_i` is taken "over a sliding window", but no window length is stated anywhere in the spec and `R_H(p)` takes a single distribution, so the window remains unimplemented by design rather than by omission — the same treatment `wayfinder` req-15 gives its Layer-2 deferral |
| `S_load` | `S_load = N_e · max_{1 ≤ i ≤ N_e} f_i` | `1` at perfect uniformity, `N_e` at full collapse to a single expert. Evaluated on a **single step**; like `R_H` it carries no window parameter, and unlike `UR` it never claimed one |
| `UR` | `UR = (1 / N_e) · Σ_{i=1}^{N_e} I[f_i > 0]` over the most recent W = 100 steps, where the indicator is evaluated on the **union** of the experts selected by any of those steps (not averaged per step) | fraction of experts actually selected at least once in the window; `UR = 1.0` under fully uniform routing and `UR = 1/N_e` when the window routes exclusively to a single expert |

**Offline Tier (computed during diagnostic runs, NOT every step)**
| Metric | Definition | Range / Notes |
|---|---|---|
| `SP_i` | `SP_i = (1 / ‖T_i‖₁) · Σ_{t ∈ T_i} c_i^T C_t`; aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` (skip experts with empty `T_i`) | `T_i` = set of tokens routed to expert `i`. If `‖T_i‖₁ = 0`, `SP_i` is excluded; SP MUST NOT be reported as `0` |
| `D_chord` | `D_chord = (2 / (N_e(N_e−1))) · Σ_{i<j} √(2(1 − c_i^T c_j))` | mean spherical chord between off-diagonal centroid pairs; note: `D_chord = √(2 · versine)` |
<a id="req-20-mci"></a>
| `MCI` | `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / \|T\|) · Σ_{t ∈ T} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`) | effective-dimensionality fraction; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `\|T\| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range); `MCI = 1.0` when `M` is proportional to identity (uniform token-distribution across the `d_c` basis), `MCI = 1/d_c` when `M` is rank-1 |
| `CG` | `CG = ‖∇_{W^{K, V, b}} L_total‖₂` | debug-only stability probe; non-negative; MUST NOT enter quality acceptance |

<a id="req-20-source"></a>
**Source:** `wayfinder/tickets/A8-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 8), change `fix-math-consistency-audit-2026-08` design.md (Decision 5)

#### Scenario: Realtime vs offline classification
- **WHEN** metrics are reported
- **THEN** `L_sep`, `R_H`, `S_load`, `UR` are available every step; `SP`, `D_chord`, `MCI`, `CG` are computed offline

#### Scenario: L_sep Frobenius consistency
- **WHEN** `L_sep` from the metrics module is compared to `L_sep` from the loss module under the same `c_centroids`
- **THEN** the two values are equal within `1e-6`

#### Scenario: Dead-expert SP is undefined
- **WHEN** an expert `i` has `‖T_i‖₁ = 0` in the current offline window
- **THEN** `SP_i` is reported as `undefined` (e.g. `NaN` with a `dead=True` flag, or omitted), NOT as `0.0`; the aggregated `SP` excludes this expert

#### Scenario: R_H is bounded
- **WHEN** `R_H(p)` is computed for any probability vector `p` over `N_e` experts
- **THEN** `R_H ∈ [0, 1]` within `1e-6`

#### Scenario: SP closed-form on orthonormal-aligned inputs
- **WHEN** `SP(orthonormal_centroids, assignments, signatures)` is called with every assigned token's signature exactly aligned with its centroid (`C_t = c_{a(t)}` for all `t ∈ T_i`)
- **THEN** the aggregated `SP = mean({SP_i : ‖T_i‖₁ > 0})` equals `1.0` within `abs=1e-6` (each `SP_i = c_i^T c_i = 1`)

#### Scenario: SP closed-form on 60° offset
- **WHEN** `SP` is called with every assigned token's signature at `60°` from its centroid (`c_i^T C_t = cos 60° = 0.5` for all `t ∈ T_i`)
- **THEN** the aggregated `SP` equals `0.5` within `abs=1e-6`

#### Scenario: SP range bound
- **WHEN** `SP(any_centroids, any_assignments, any_signatures)` is called
- **THEN** `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6` (cosine-kernel range, exact up to FP error; SP negative when most signatures lie on the antipodal side of their centroid)

#### Scenario: D_chord closed-form on orthonormal basis
- **WHEN** `D_chord(c_centroids)` is called with `centroids ∈ R^{N_e × d_c}` forming an orthonormal subset (e.g. first `d_c` rows of `I_{d_c}` when `N_e = d_c`)
- **THEN** the result equals `sqrt(2)` within `abs=1e-6` (mean of `√(2·1)` over `c_i^T c_j = 0` pairs)

#### Scenario: MCI closed-form on uniform token distribution
- **WHEN** `MCI(token_signatures)` is called with `|T| = d_c · k` signatures, each `e_j ∈ R^{d_c}` (the `d_c` standard basis vectors) represented exactly `k` times (so the uncentered second moment `M = (1/|T|) · Σ_t C_t C_tᵀ = I/d_c` exactly)
- **THEN** the result equals `1.0` exactly within `abs=1e-12` (every dimension equally active ⇒ `Σλ̃² = 1/d_c` ⇒ `MCI = 1/(d_c · 1/d_c) = 1.0`)

#### Scenario: MCI closed-form on rank-1 token distribution
- **WHEN** `MCI(token_signatures)` is called with all `|T|` signatures equal to the same unit vector `e_1` (so `M = e_1 e_1ᵀ` is rank-1 with eigenvalues `{1, 0, ..., 0}`)
- **THEN** the result equals `1/d_c` exactly within `abs=1e-12` (one dimension active ⇒ `Σλ̃² = 1` ⇒ `MCI = 1/d_c` — the lower endpoint of the declared `[1/d_c, 1]` range, attained)

#### Scenario: CG zero-gradient invariance
- **WHEN** `CG(zero_grad)` is called with all-zero input gradient
- **THEN** the result equals `0.0` exactly within `abs=1e-12` (L2 norm of the zero vector is zero)

#### Scenario: CG positive homogeneity
- **WHEN** `CG(g)` and `CG(2·g)` are both evaluated for any non-zero gradient `g`
- **THEN** `|CG(2·g) − 2·CG(g)| < 1e-6` (L2 norm is positively homogeneous of degree 1)

#### Scenario: UR window, axis semantics and closed form
- **WHEN** `UR(f_per_expert)` is called with a history of `T` per-expert routing
  vectors, given either as a list of `T` tensors of shape `(N_e,)` or as a single
  tensor of shape `(T, N_e)`
- **THEN** only the most recent `W = 100` entries of the **time axis** are reduced
  (list index for the list form, axis 0 for the tensor form), so a 200-step history
  and its trailing 100 steps MUST give the same value; and the reduction is the
  **union** over the window, i.e. `UR = (1 / N_e) · |{i : f_{t,i} > 0 for some t in
  the window}|` — **not** the mean of the per-step fractions. Rationale: the
  indicator is indexed by expert alone and the row's gloss is a fraction *of
  experts*; averaging per step would make the same expression two different
  quantities for `T = 1` versus `T > 1`.
- **AND** for a single step `f ∈ R^{N_e}` (the `T = 1` special case) `UR` equals
  the number of strictly-positive entries divided by `N_e`; with exactly 3 of
  `N_e = 16` experts active this is `3/16 = 0.1875` (float closed form, MUST be
  pinned with `pytest.approx(3/16, abs=1e-9)`)
- **AND** an input whose active-expert set is constant across the window MUST NOT
  distinguish the two aggregations — with 8 single-expert steps cycling over 4
  distinct experts the union reading gives `4/16 = 0.25` while the per-step-mean
  reading gives `1/16 = 0.0625`; the difference is observable only when the active
  set varies **within** the window

#### Scenario: UR rejects inputs with no time axis
- **WHEN** `UR` is called with a 0-dim tensor, or with a tensor of `ndim ≥ 3` such
  as the `(B, N, N_e)` batched routing tensor that req-28 lists as canonical for
  `f_per_expert`
- **THEN** it raises `ValueError` naming the required shapes. A `(B, N, N_e)` input
  has **no** step axis — each `B × N` element is a token, not a step — so reducing
  its axis 0 would silently drop whole batch rows rather than truncate a history.
  Callers MUST reduce over tokens first and pass `(T, N_e)`

#### Scenario: req-20 is the single canonical source for the MCI closed form

- **WHEN** `MCI(token_signatures)` is implemented per `#req-20-mci`
- **THEN** the implementation uses `M = (1/|T|) · Σ C_t C_t^T` uncentered second moment (NOT centered covariance, NOT convex hull radius), with eigenvalues `λ_j` extracted from `M`, normalized to `λ̃_j = λ_j / Σ_r λ_r`, and the result is `1 / (d_c · Σ λ̃_j²)`
- **AND** the result lies in `MCI ∈ [1/d_c, 1]` closed range with both endpoints attainable, guarded by the two `MCI closed-form` Scenarios above at `abs=1e-12`
- **AND** no other Requirement restates this closed form: a Requirement that points at this one MUST reference `#req-20-mci` rather than a line number or a verbatim copy, so that editing this Requirement cannot invalidate a pointer elsewhere


#### Scenario: all-dead window makes the aggregated SP undefined
- **WHEN** EVERY expert `i` has `‖T_i‖₁ = 0` in the current offline window, so the surviving set `{SP_i : ‖T_i‖₁ > 0}` is empty (`mean(∅)` is undefined)
- **THEN** the aggregated `SP` is reported as `undefined` — encoded as `NaN` — and MUST NOT be reported as `0.0`

#### Scenario: a live measurement of exactly 0.0 exists, so 0.0 is not available as a sentinel
- **WHEN** per-token alignment terms `c_i^T C_t` cancel exactly within each live expert (e.g. `+0.6` and `−0.6` in equal number, which IEEE-754 evaluates to exactly `0.0`), and every expert is live
- **THEN** the aggregated `SP` is exactly `0.0` — a legitimate, bit-exact measurement — which is precisely why `0.0` MUST NOT double as the all-dead sentinel

#### Scenario: all-dead sentinel is distinguishable from a live zero
- **WHEN** the aggregated `SP` of an all-dead window is bit-compared (`torch.equal`) against a live window whose per-token alignment terms cancel exactly, so that the live aggregated `SP` is exactly `0.0`
- **THEN** the two results MUST NOT compare equal: the all-dead result MUST be `NaN`, never a `0.0` sentinel

#### Scenario: an empty signature set takes the same undefined path
- **WHEN** the offline signature set itself is empty (`|T| = 0`), so every per-expert token count `n_i` is `0`
- **THEN** the aggregated `SP` is `NaN` under the same contract as the all-dead case above, NOT `0.0`

#### Scenario: the SP range bound is asserted only for finite results
- **WHEN** `SP(any_centroids, any_assignments, any_signatures)` returns a finite value
- **THEN** `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6` holds; and when the same call returns the `NaN` sentinel (every expert dead) the range assertion is NOT applicable and MUST NOT be read as violated — the `NaN` sentinel lies, by convention, OUTSIDE the declared range `SP ∈ [-1, 1]`, and MUST NOT participate in any downstream aggregation or comparison

#### Scenario: NaN is not clamped into the range
- **WHEN** the aggregated `SP` is `NaN` and a downstream step would clamp, average or threshold it
- **THEN** that step MUST NOT substitute `0.0` or any in-range value; the `NaN` MUST propagate unchanged or be filtered by an explicit caller decision

<a id="req-30"></a>

### Requirement: Closed-Form Gradient Bound Worst Case

The bound `‖∂logit/∂C‖₂ ≤ β_max = 32` in Req 7 is a **supremum over the closed range of `β`, not a value attained by any finite `γ`**. The exact derivative is `∂logit/∂C = β · c` — `logit = β · (C^T c − 1)` is linear in `C`, so the derivative carries NO `‖C‖` factor — whence `‖∂logit/∂C‖₂ = β · ‖c‖₂`, which is **independent of the angle between `c` and `C`**; `c ⟂ C` is one WITNESS, not a necessary condition and not "the" worst-case configuration. Because `β = 0.1 + 31.9 · σ(γ)` is strictly below `32` for every finite `γ` (in float64 `σ` reaches `1.0` only for `γ ≳ 36.7368`), `β_max = 32` MUST NOT be reported as attained by any finite configuration; it MUST be approached as `γ → ∞`. **The earlier form `∂logit/∂C = β · c / ‖C‖` is WRONG off the sphere**: it coincides with the exact derivative only on `‖C‖ = 1`, and returns `β · ‖c‖₂ / 2` where autograd returns `β · ‖c‖₂` at `‖C‖ = 2`. The bound `|∂logit/∂γ| ≤ 0.5 · (β_max − β_min) = 15.95` in Req 7 MUST be attained at `γ = 0, c = −C` (so `β = 16.05`, `inner = −1`, `(β_max − β_min) · σ'(γ) · (inner − 1) = 31.9 · 0.25 · (−2) = −15.95`). (References Req 7.)

**Source:** `wayfinder/tickets/A4-1.md` (historical, MAX_GRAD_PER_C = β_max = 32 bound declared in A4-1; worst-case attainability verification at orthogonal unit vectors added by `fix-math-consistency-audit-2026-08` Decision 6), change `fix-math-consistency-audit-2026-08` design.md (Decision 6), change `2026-10-14-opx2-sp-all-dead-nan-and-box-attainment` design.md (Decision D-3)

#### Scenario: gradient bound is tight at orthogonal unit vectors
- **WHEN** `logit = β_max · (C^T c − 1)` with `C = e_1`, `c = e_2`, `β = β_max`
- **THEN** `‖∂logit/∂C‖₂ == 32.0` within `abs=1e-4`

#### Scenario: the boundary value is the supremum, not any finite-gamma value
- **WHEN** the same expression is evaluated at the closed-range boundary `β = β_max = 32`, versus at any `β = 0.1 + 31.9 · σ(γ)` for a finite `γ`
- **THEN** at `β = β_max` the value is `32.0` (the boundary evaluation asserted above), while at every finite `γ` it is strictly `< 32.0`; `32.0` is the supremum, approached as `γ → ∞`, and MUST NOT be reported as attained by any finite `γ`

#### Scenario: the derivative carries no ‖C‖ factor and is angle-independent
- **WHEN** `logit = β · (C^T c − 1)` is differentiated with respect to `C`, sweeping the angle between `c` and `C` over `θ ∈ [0°, 180°]` at `‖C‖₂ = ‖c‖₂ = 1`, and additionally at `‖C‖₂ = 2` off the sphere
- **THEN** `‖∂logit/∂C‖₂ == β · ‖c‖₂` at every angle within `abs=1e-6` (orthogonality is not required), and at `‖C‖₂ = 2` the autograd value still equals `β · ‖c‖₂` — never `β · ‖c‖₂ / ‖C‖₂`

#### Scenario: gamma-gradient bound is tight at antipodal config
- **WHEN** `logit = inverse_temperature(γ=0) · (inner − 1)` with `C = e_1`, `c = −e_1`
- **THEN** `|∂logit/∂γ| == 15.95` within `abs=1e-3`
