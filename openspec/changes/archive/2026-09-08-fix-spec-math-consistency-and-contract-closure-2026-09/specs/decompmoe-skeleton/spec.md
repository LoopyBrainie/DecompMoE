## ADDED Requirements

### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension

The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask, *, grad=None, eta=1e-2) -> Tensor` method MUST apply, per phase:

- Phase 0 (SEEDING): `c_i ← c_i.detach()` (driver is a no-op returning the input centroids detached from the autograd graph); `c_i.requires_grad = False`. Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds (the `‖c_i‖₂ ≡ 1.0` invariant for Phase 0 is the caller's responsibility, not the driver's).
- Phase 1 (EMA_090): `c_i ← Normalize(0.90 · c_i + 0.10 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 2 (EMA_095): `c_i ← Normalize(0.95 · c_i + 0.05 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 3 (EMA_099): `c_i ← Normalize(0.99 · c_i + 0.01 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 4 (PROJECTED_SGD): When `grad is not None`: `candidate_i = c_i − eta · grad_i`; then `c_i^(t+1) = candidate_i / ‖candidate_i‖₂`. When `grad is None`: `c_i^(t+1) = c_i / ‖c_i‖₂` (L2 retraction of the input only). Both branches apply the Invariant #4 guard pattern: when `‖candidate_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)` (no `clamp_min(ε)` denominator; the same `torch.where(use_old, prev, normalize(...))` pattern used in EMA). Driver Active, gradient channel Active.

The `m_i` is the masked-mean over tokens assigned to expert `i`. The driver MUST enforce the empty-cell invariant: if `n_i = |T_i| = 0`, then `m_i ≡ c_i^(t−1)` (no `clamp_min(ε)` denominator). The driver MUST enforce the spherical re-projection invariant: `‖c_i^(t+1)‖₂ ≡ 1.0` after every step; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)`. The driver SHALL expose a `should_resurrect(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/(2·N_e), consec=200) -> set[int]` helper that flags expert indices whose mask-fraction `f_i` was below `1/(2·N_e)` for `200` consecutive steps (rate-limited to once per `1000`-step window). At MVP `N_e = 16`, `1/(2·N_e) = 1/32`; the rule is parameterized by `N_e`, not a hardcoded `1/128`.

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

### Requirement: Spherical L2 Normalization — max(…z…, ε) Formula

The package SHALL provide `spherical_l2_normalize(z, eps=1e-6) -> Tensor` returning `z / max(‖z‖₂, eps)` along the last dimension. The default `eps` SHALL equal `1e-6`. The function SHALL be safe at `z = 0` (no NaN / Inf in output; returns the zero vector).

#### Scenario: Output norm equals 1.0 for `‖z‖₂ ≥ ε` (and 0 for `z = 0`)

- **WHEN** `spherical_l2_normalize(z)` is called for any `z` with `‖z‖₂ ≥ ε` (which subsumes the prior `‖z‖₂ ≥ 1 − ε` regime — the formula's relevant threshold is `ε`, not `1 − ε`)
- **THEN** the result's `pow(2).sum(-1) == 1.0` exactly (the `max(‖z‖₂, ε)` denominator equals `‖z‖₂` for `‖z‖₂ ≥ ε`, so `‖out‖₂ = ‖z‖₂ / ‖z‖₂ = 1` exactly; the formula attains `1.0` strictly across this entire regime — the prior `[1 − 2ε, 1]` interval bound from the OLD `+ ε` formula is obsolete)

#### Scenario: Idempotence

- **WHEN** the function is applied twice in succession with input satisfying either `z = 0` (output is `0`) or `‖z‖₂ ≥ ε` (output norm is `1`)
- **THEN** the second application leaves the output unchanged (since for `z = 0` the output is `0` and the second `0 / max(0, ε) = 0` is the identity; for `‖z‖₂ ≥ ε` the first output has norm `1`, so the second `max(1, ε) = 1` denominator gives the identity map)
- **AND WHEN** the input is in the degenerate regime `0 < ‖z‖₂ < ε`
- **THEN** the first application yields `‖out‖₂ = ‖z‖₂ / ε < 1` (sub-unit norm), and the second application normalizes to norm `1` (NOT idempotent in this regime)

---

### Requirement: Beta Parameterization Operational Domain — D1 Module-Level Constants

The package SHALL provide `inverse_temperature(gamma) -> Tensor` implementing the **parameterization-space** form `β = β_min + (β_max − β_min) · σ(γ)` with `β_min == 0.1` and `β_max == 32`. The package SHALL additionally provide `phase4_inverse_temperature(gamma_p) -> Tensor` implementing the **operational-domain** form `β^eff = 1 + 31 · σ(γ')` used in Phase 4 (the parameterization-space floor `0.1` and the operational-domain floor `1.0` are intentionally decoupled — the latter prevents routing resonance at runtime, the former keeps `σ'(γ)` non-degenerate in the cold-start region). The package SHALL provide `gamma_reset_for_phase4(beta_p3) -> float` implementing `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`; the worked example `gamma_reset_for_phase4(16.0) ≈ −0.0645385...` MUST hold within `abs=1e-4`. The package SHALL provide `beta_effective(gamma, phase, step) -> Tensor` returning `1.0` for `phase == 1`, `Clamp(inverse_temperature(gamma), 1.0, phase_beta_max(phase, step))` for `phase ∈ {2, 3}` (where `phase_beta_max(phase, step)` is the **time-varying** schedule ramp under the **pinned** linear-interpolation convention `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive: Phase 2 range `[6_000, 26_000)` ramp `1.0 → 4.0` (so `phase_beta_max(2, 6_000) = 1.0` exact at boundary start, `phase_beta_max(2, 16_000) = 2.5` exact at midpoint, `phase_beta_max(2, 25_999) = 1 + 3·19_999/20_000 = 3.99985`); Phase 3 range `[26_000, 56_000)` ramp `4.0 → 16.0` (so `phase_beta_max(3, 26_000) = 4.0` exact at boundary start = `box(3).lo`, `phase_beta_max(3, 41_000) = 4 + 12·15_000/30_000 = 10.0` exact at midpoint, `phase_beta_max(3, 55_999) = 4 + 12·29_999/30_000 = 15.9996`). `phase_beta_max` is **distinct** from the static `phase_beta_box(phase).hi` and the `step` parameter is required), and `phase4_inverse_temperature(gamma_p)` for `phase == 4`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` (operational-domain worst case, all domains) and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (**parameterization-space** worst case derived as `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95`, where `σ'(0) = 0.25` is the sigmoid derivative at `γ = 0` and the inner-product factor `|Cᵀc − 1|_max = 2` is the antipodal extreme; the **operational-domain Phase 4** worst case is `σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` at `γ' = 0` (canonical export per `src/decompmoe/beta.py:46` `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`); the two constants live in different domains and MUST NOT be conflated).

**`beta_effective` signature is exactly 3 positional args `(gamma, phase, step)`** — there is no `cfg` keyword-only parameter. Per `design.md` Decision 1, the algorithmic constants `β_min = 0.1` and `β_max = 32` live as module-level `Final[float]` in `decompmoe/beta.py` (not in MVPConfig and not threaded through `cfg`). The signature intentionally avoids `cfg` to keep the call site focused on the schedule / phase decision and to avoid the indirection cost of looking up constants that are already canonically placed. The three constants `31` (Phase 4 span), `31.9` (parameterization span), and `1.0` (Phase 4 floor) likewise live in `decompmoe/beta.py`.

#### Scenario: Parameterization endpoints

- **WHEN** `inverse_temperature(gamma)` is called with `gamma ∈ {-50, 0, 50}`
- **THEN** the result is `≈ 0.1` / `16.05` (midpoint) / `≈ 32.0` respectively within `1e-3`

#### Scenario: gamma reset for phase 4 boundary continuity

- **WHEN** `gamma_reset_for_phase4(16.0)` is called
- **THEN** the result equals `ln(15/16) ≈ −0.0645385...` within `abs=1e-4`

#### Scenario: beta_effective is continuous at Phase 3 → 4 boundary

- **WHEN** `beta_effective(gamma_p=ln(15/16), phase=4, step=56_000)` is called
- **THEN** the result equals `1 + 31 · σ(ln(15/16)) = 16.0` exactly (continuity with Phase 3's terminal `β_max`)

---

### Requirement: Frozen MVP Hyperparameter Set — D1 Geometric-Only Fields

The package SHALL provide a `MVPConfig` frozen dataclass whose locked constants equal: `d_model == 1024`, `N_e == 16`, `k == 2`, `d_ffn == 2048`, `L == 4`, `d_ffn_dense == 4096`, `d_c == 16`, `H_kv == 8`, `d_k == 128`, `β_initial == 1.0`. Attempting to mutate any field SHALL raise `dataclasses.FrozenInstanceError`. A factory function `MVPConfig()` SHALL return an instance with all default values.

**MVPConfig carries only GEOMETRIC constants** (model shape: `d_model`, `N_e`, `k`, `d_ffn`, `L`, `d_ffn_dense`, `d_c`, `H_kv`, `d_k`, `vocab_size`) **plus the specific initial value `β_initial = 1.0`**. The algorithmic range constants `β_min = 0.1` and `β_max = 32` live as module-level `Final[float]` in `decompmoe/beta.py` (NOT in MVPConfig), per `design.md` Decision 1: "Algorithmic constants live with their usage site". MVPConfig does not carry `β_min` or `β_max` fields, and the canonical sources for those constants are `decompmoe.beta.BETA_MIN` and `decompmoe.beta.BETA_MAX`.

#### Scenario: Field defaults locked

- **WHEN** `MVPConfig()` is constructed
- **THEN** `cfg.d_model == 1024 and cfg.N_e == 16 and cfg.k == 2 and cfg.d_ffn == 2048 and cfg.L == 4`

#### Scenario: Mutation rejected

- **WHEN** any field is assigned after construction
- **THEN** `dataclasses.FrozenInstanceError` is raised

#### Scenario: MVPConfig field set is exactly the geometric constants plus β_initial

- **WHEN** the set of dataclass field names on `MVPConfig` is enumerated via `[f.name for f in dataclasses.fields(MVPConfig)]`
- **THEN** the set equals exactly `{'d_model', 'N_e', 'k', 'd_ffn', 'L', 'd_ffn_dense', 'd_c', 'H_kv', 'd_k', 'beta_initial', 'vocab_size'}` (11 fields; **`β_min` and `β_max` are NOT MVPConfig fields**; they live as `Final[float]` in `decompmoe/beta.py`)

---

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
- `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / |T|) · Σ_{t ∈ T} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`); **effective-dimensionality fraction**; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range). Uniform token distribution (each basis `e_j` equally represented in `T`) ⇒ `M = I/d_c` exactly ⇒ `MCI = 1.0`. Rank-1 token distribution (all `C_t = e_1`) ⇒ `M = e_1 e_1ᵀ` exactly ⇒ `MCI = 1/d_c`. The previous formula `(1/d_c) · Σ 1/λ̃²` was mathematically inconsistent with the declared range and MUST NOT appear. MCI takes **token signatures** as input (NOT centroids), per the definition.
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
- **THEN** it raises `TypeError` (the gradient of a float-parameterized loss MUST be floating-point; integer / boolean tensors are caller bugs that would silently coerce to zero norm and defeat the stability-probe purpose)