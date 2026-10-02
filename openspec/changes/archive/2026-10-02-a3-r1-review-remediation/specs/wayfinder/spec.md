# Spec Delta — `wayfinder`

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
| `MCI` | `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)`, with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1 / \|T\|) · Σ_{t ∈ T} C_t C_tᵀ` over the routed-token signature set `T`, and `λ̃_j = λ_j / Σ_r λ_r` (normalized eigenvalue of `M`) | effective-dimensionality fraction; replaces CV (whose lower bound `1/d_c` on `S^{d_c−1}` made the original `< 0.05` health target unreachable — see `wayfinder/tickets/A8-2.md`). The centered-covariance reading has its `(1/d_c, 1]` upper endpoint unreachable at `\|T\| = d_c`; this Requirement uses the **uncentered** second moment so that both endpoints of the declared range are attainable. `MCI ∈ [1/d_c, 1]` (closed range); `MCI = 1.0` when `M` is proportional to identity (uniform token-distribution across the `d_c` basis), `MCI = 1/d_c` when `M` is rank-1 |
| `CG` | `CG = ‖∇_{W^{K, V, b}} L_total‖₂` | debug-only stability probe; non-negative; MUST NOT enter quality acceptance |

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


<a id="req-28"></a>

### Requirement: Resurrection Perturbation Per-Expert Contract

The Dead Expert Splitting Resurrection pathway (Req 13) MUST perturb the **single cloned expert** (centroid and/or expert weights) — not the per-expert routing frequency vector `f_per_expert`. The perturbation API `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)` MUST accept `f_per_expert` as the leading positional argument with **shape `(..., N_e)`** — the trailing axis MUST equal `N_e` and leading dims are arbitrary (canonical call sites pass `(N_e,)`, `(T, N_e)`, or `(B, N, N_e)` matching the per-expert routing-frequency convention used by `decompmoe.loss` and `decompmoe.metrics`). Layer 1 shape enforcement (primitive-side, at this primitive): `f_per_expert.ndim ≥ 1` so the primitive cannot silently receive a 0-D scalar. Layer 2 wrapper-side enforcement (trailing-axis = `cfg.N_e` pair-check, enforced at the canonical call site `resurrect_expert`) is described in Req 32. `target_idx` is a positional integer naming the expert slot the perturbation is attributed to, and the primitive MUST NOT consume it (it does not select which expert to perturb — the caller's `target_idx` value carries no behavioural meaning); the canonical wrapper in req-32 passes the **donor** `j_star`, because the perturbed quantity is the donor's centroid per req-13's "clones `j*`", while `i` remains the dead expert whose slot is being repaired. `eps_std=0.05` is a positional-or-keyword Gaussian perturbation scale, and `dim` is a **keyword-only** parameter sourcing the per-expert dimensionality (centroid `d_c` or expert-weight `d_model · d_ffn`). `dim=None` MUST raise `TypeError` (explicit `dim` is required so the return-shape contract is enforced at the call site). The returned tensor MUST have leading dimension `dim` — corresponding to a single expert slot — NOT the `(N_e,)` shape of `f_per_expert`. The β double-write semantic (`β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`) is defined in Req 13; this primitive does not mutate `β_per_expert` — that mutation is the wrapper's responsibility. (References Req 13.)

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-math-consistency-audit-2026-08` design.md (Decision 4 — per-expert perturbation contract); signature mirrors the `resurrection_perturb_distribution` function in `src/decompmoe/safeguards.py` at commit `263ac19 feat(safeguards): per-expert resurrection perturb shape + same-event beta decay` (Layer 1 primitive-side `ndim ≥ 1` guard inside that function)

#### Scenario: perturbation output shape matches a single expert slot
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called (explicit `dim` required; `dim=None` raises `TypeError`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

<a id="req-32"></a>

### Requirement: Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper

The Dead Expert Splitting Resurrection pathway (Req 13) MUST perturb the **single cloned expert** (centroid and/or expert weights) — not the per-expert routing frequency vector `f_per_expert`. The perturbation API `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)` MUST accept `f_per_expert` as the leading positional argument with **shape `(..., N_e)`** — the trailing axis MUST equal `N_e` and leading dims are arbitrary (canonical call sites pass `(N_e,)`, `(T, N_e)`, or `(B, N, N_e)`). Layer 2 shape enforcement (wrapper-side, at this wrapper): `f_per_expert.shape[-1] == cfg.N_e` pair-check. The vacuous self-check `f_per_expert.shape[-1] == β_per_expert.shape[0]` (which is identically true given `f_per_expert = β_per_expert.detach()` inside this wrapper, where `shape[-1] == shape[0]`) was an earlier draft and was corrected by commit `0b2202e` to anchor on the spec-defined `cfg.N_e`. Layer 1 primitive-side enforcement (`ndim ≥ 1`) is described in Req 28. `target_idx` is a positional integer, `eps_std=0.05` is a positional-or-keyword perturbation scale, and `dim` is a **keyword-only** parameter sourcing the per-expert dimensionality. `dim=None` MUST raise `TypeError`. The returned tensor MUST have leading dimension `dim` — corresponding to a single expert slot — NOT the `(N_e,)` shape of `f_per_expert`. The β double-write semantic (`β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`) is defined in Req 13; this wrapper additionally guarantees same-call-stack execution (see wrapper contract paragraph below). (References Req 13.)

**The canonical single-event API is `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg) -> tuple[Tensor, Tensor]`** which returns `(c_perturbed, β_per_expert_new)` and guarantees that the centroid perturbation and the β double-write happen in the **same Python call stack** — no `yield` / `await` / background-task scheduling between the two operations. Callers MUST use `resurrect_expert` for the resurrection pathway; the two primitives `resurrection_perturb_distribution` and `apply_resurrection_beta_decay` remain available for low-level composition but their separate invocation does NOT satisfy the "same resurrection event" contract above. The wrapper signature takes `cfg: MVPConfig` so the per-expert dimensionality `cfg.d_c` is sourced from the canonical config rather than re-derived from `β_per_expert.shape` (which would conflate centroid dimension with the `N_e` routing dimension — the very bug the per-expert contract exists to prevent). It additionally takes `c_centroids: Tensor` of shape `(N_e, d_c)` as a **required per-call argument**, because Req 28's "perturb the single cloned expert" is unsatisfiable without it: neither `MVPConfig` nor `β_per_expert` carries a centroid, and a per-call parameter is the correct home for it because the donor differs on every resurrection event, whereas `MVPConfig` is a frozen configuration singleton. **The clone source is row `j_star` (the donor), not row `i`** — `i` is the dead expert whose own centroid is exactly the degenerate quantity the resurrection exists to replace, and this matches the β double-write, which likewise reads its pre-write value from `β_per_expert[j_star]`. A wrapper that cloned row `i` would be a no-op dressed as a resurrection.

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-math-consistency-audit-2026-08` design.md (Decision 4 — per-expert perturbation contract); signature mirrors the `resurrect_expert` function in `src/decompmoe/safeguards.py` at commit `263ac19 feat(safeguards): per-expert resurrection perturb shape + same-event beta decay` (Layer 2 wrapper-side anchor `cfg.N_e` per commit `0b2202e fix(safeguards): replace vacuous β-length self-check with cfg.N_e meaningful guard` at the `cfg.N_e` guard inside `resurrect_expert`)

#### Scenario: perturbation accepts 1-D (N_e,) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (N_e,)` (e.g. `(16,)` at MVP)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation accepts batched (B, N, N_e) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (B, N, N_e)` (e.g. `(4, 3, 16)` at MVP — matches `loss.L_lb` hot-path shape per `src/decompmoe/loss.py:88`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation accepts history-stacked (T, ..., N_e) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (T, ..., N_e)` (e.g. `(100, N_e)` history stacked by `metrics.UR` per `src/decompmoe/metrics.py:83`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation rejects 0-D scalar f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert=(), target_idx=3, dim=16)` is called with `f_per_expert.ndim == 0`
- **THEN** the primitive raises `ValueError` (Layer 1 guard: ndim ≥ 1)

#### Scenario: wrapper pair-checks f_per_expert trailing axis vs cfg.N_e
- **WHEN** `resurrect_expert(i=3, j_star=0, β_per_expert, c_centroids, cfg)` is called with `β_per_expert.detach()` (the wrapper's internal `f_per_expert = β_per_expert.detach()`) whose trailing axis length `!= cfg.N_e` (the canonical N_e sourced from `cfg.MVPConfig`, **NOT** `β_per_expert.shape[0]` — the latter would be a vacuous self-check given `f_per_expert = β_per_expert.detach()`, where `shape[-1] == shape[0]` identically)
- **THEN** the wrapper raises `ValueError` (Layer 2 guard: trailing-axis = N_e pair-check, anchored on `cfg.N_e`)

#### Scenario: same-event beta decay
- **WHEN** `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg)` is called with any valid `MVPConfig cfg` and a `c_centroids` of shape `(N_e, d_c)` with unit-norm rows, valid expert indices `i` and `j_star` (`0 ≤ i, j_star < N_e`, `i ≠ j_star`), and a valid `β_per_expert ∈ R^{N_e}` (positive finite values)
- **THEN** the returned `c_perturbed` is `L2Normalize(c_centroids[j_star] + ε)` where `ε` is the output of `resurrection_perturb_distribution(β_per_expert.detach(), j_star, eps_std=0.05, dim=cfg.d_c)`, and the returned `β_per_expert_new` is the output of `apply_resurrection_beta_decay(β_per_expert, j_star, i)`, with both calls executed in the **same call stack** (no `await` / `yield` / `spawn` between them — verifiable by inspecting the wrapper's linear code path which is a synchronous function composition)
- **AND** `β_per_expert_new[i] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (donor value is read from `β_per_expert[j_star]` BEFORE either write, per the immutability clause; this matches the canonical pattern in `apply_resurrection_beta_decay`)
- **AND** `β_per_expert_new[j_star] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (the donor's own β is also decayed by the same factor)
- **AND** `c_perturbed.shape == (cfg.d_c,)` (single-expert slot shape, consistent with the perturbation output shape scenario above)
- **AND** `‖c_perturbed‖₂ == 1.0` within `abs=1e-6` — the resurrection MUST return a point on the unit sphere `S^{d_c−1}`. This is the invariant the bare-ε behaviour broke: `ε ~ N(0, eps_std²·I)` has RMS norm `eps_std·sqrt(d_c) = 0.2` at `d_c = 16, eps_std = 0.05`, so assigning it to `c_i` violated the sphere constraint before any other invariant could be checked. The **mean** norm is strictly smaller and has the exact closed form `E‖ε‖₂ = eps_std · √2 · Γ((d_c+1)/2) / Γ(d_c/2) = 0.196901` at these values (the `eps_std·sqrt(d_c)` figure is the RMS, i.e. `√(E‖ε‖₂²)`, and overstates the mean by 1.58% at `d_c = 16`; measured 0.196838 over 200 000 samples). This is a **float** closed form and MUST be pinned with `pytest.approx(0.196901, abs=1e-3)` against a Monte-Carlo mean, not with the RMS literal. This is a **float** closed form and MUST be pinned with `pytest.approx(1.0, abs=1e-6)`, never with a bare `==`
- **AND** `cos(c_perturbed, c_centroids[j_star]) > 0` — the returned point is a perturbation **of the donor**, not an independent random direction. Measured over 200 000 samples at `d_c = 16, eps_std = 0.05` the mean cosine is `0.981666` and the mean angle `10.8054°`; the bare-ε behaviour gave `−0.000289` and `90.0177°`, i.e. an 8.33× angle gap and a vector that was orthogonal to the donor
- **AND** `β_per_expert_new is not β_per_expert` (immutability: the input tensor is never mutated in-place; `apply_resurrection_beta_decay` clones internally)

#### Scenario: clone source is the donor row, not the dead expert
- **WHEN** `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg)` is called with `i != j_star` and `c_centroids` of shape `(N_e, d_c)` with unit-norm rows
- **THEN** the clone is taken from `c_centroids[j_star]` (the donor) and NOT from `c_centroids[i]`; with `eps_std → 0` the returned `c_perturbed` converges to `c_centroids[j_star]`
- **AND** an implementation that cloned row `i` MUST be rejected: `i` is the dead expert, so its centroid is the degenerate quantity the resurrection is meant to replace, and cloning it would return a perturbed copy of the very state being repaired
