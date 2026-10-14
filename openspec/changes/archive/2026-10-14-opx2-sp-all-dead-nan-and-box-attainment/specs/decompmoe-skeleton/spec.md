# Spec Delta

## MODIFIED Requirements

<a id="req-22"></a>

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
