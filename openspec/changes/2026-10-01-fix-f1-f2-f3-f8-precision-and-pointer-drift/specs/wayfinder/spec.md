# Spec Delta — `wayfinder`

## MODIFIED Requirements

<a id="req-7"></a>

### Requirement: Isotropic Squared-Chord Distance And Bounded Beta

The system MUST measure distance between `C_t^l` and `c_i^l` using the isotropic squared-chord distance `d(C, c_i) = 1 − C^T c_i ∈ [0, 2]`. The system MUST parameterize the inverse-temperature using the **parameterization-space** form `β^param(γ) = β_min + (β_max − β_min) · Sigmoid(γ)` with `β_min = 0.1` and `β_max = 32`. The corresponding logit MUST be `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The system MUST bound `‖∂logit/∂C‖₂` and `‖∂logit/∂c_i‖₂` by ` ≤ β_max = 32`, and `|∂logit/∂γ_i|` by ` ≤ 0.5(β_max − β_min) = 15.95`, as hard numerical-stability guarantees derived from ticket A4-1.

**Operational-domain override (Invariant 3)**: per-phase effective β MUST be:
- **Phase 1**: `β^eff = 1.0` (fixed, regardless of `γ`).
- **Phase 2–3**: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase-driven schedule (`1.0 → 4.0` in Phase 2, `4.0 → 16.0` in Phase 3).
- **Phase 4**: `β^eff = 1.0 + 31.0 · Sigmoid(γ')` — continuous reparameterization. On entering Phase 4, `γ` MUST be reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum MUST be reset for `γ` (per A6b-1).

`β_min = 0.1` exists to keep `σ'(γ)` non-degenerate in the parameterization space (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.02845`, verified at 50-digit mpmath precision `σ'(−3.5) = 0.0284530238797355598396878271273`). The operational-domain floor `1.0` in Phase 4 is independent and exists to prevent routing resonance.

Per-expert scalar weights `w_i` MUST NOT appear in the logit; the mixing weight for top-k routing IS the softmax probability `p_i` (per A4-2 and CLAUDE.md §6). `w_i` MUST NOT appear in any stage, in any formulation, in any reserved form.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A4-2.md`, `wayfinder/tickets/A6b-1.md`

#### Scenario: Distance is bounded and gradient-safe
- **WHEN** any `(C, c_i)` pair on the unit sphere is fed into the gating function
- **THEN** the distance lies in `[0, 2]` and the per-component gradient magnitude stays below or equal to `β_max = 32`

#### Scenario: w_i is absent from the logit
- **WHEN** the logit is computed for gating
- **THEN** no learnable per-expert scalar weight `w_i` participates in `logit = β(C^T c − 1)`; mixing weights are exactly the softmax probabilities `p_i`

#### Scenario: σ'(−3.5) narrative precision matches 50-digit mpmath within 4 significant figures (narrative form)
- **WHEN** `σ'(γ) = σ(γ) · (1 − σ(γ))` is evaluated at `γ = −3.5`
- **THEN** the narrative value `σ'(−3.5) ≈ 0.02845` matches the 50-digit mpmath value `0.0284530238797355598396878271273` rounded to 4 significant figures (round-half-up at 5dp or truncate-then-format, both yield `0.02845`); the 5-sig-fig truncation would yield `0.028453`, NOT displayed; the discrepancy is intentional — narrative precision is 4 sig figs to align with `β_0 ≈ 1.035` (4 sig fig) closed-form style elsewhere in this Requirement (per Decision 4 of change `01-fix-ticket-stale-numerical-4file-batch` proposal); this is the "healthy gradient" health-check anchor for the cold-start region `γ_init ≈ −3.5`

#### Scenario: MVPConfig.beta_initial default derives from spec closed-form β_min + (β_max−β_min)·σ(γ_init), NOT self-referential literal
- **WHEN** `MVPConfig().beta_initial` is asserted against a pytest.approx value
- **THEN** the expected value MUST be derived from the spec closed form `β_min + (β_max − β_min) · Sigmoid(γ_init)` with `β_min = 0.1`, `β_max = 32`, `γ_init = −3.5` (i.e., `0.1 + 31.9·σ(−3.5) ≈ 1.035060`, narrative `≈ 1.035` per L130); the assertion MUST NOT degenerate to a self-referential comparison against a hard-coded literal that equals `MVPConfig.beta_initial` (which would always pass regardless of whether `inverse_temperature` actually evaluates the closed form)
- **AND** the tolerance MUST be `abs=1e-3` to cover both the narrative 4-sig-fig truncation (`1.035060 → 1.035` diff = `6e-5`) AND any closed-form computation noise from the `inverse_temperature` implementation

#### Scenario: σ'(−3.5) is guarded by a 50-digit mpmath pytest assertion (durable across archive of `.audit/`)
- **WHEN** `σ'(γ) = σ(γ) · (1 − σ(γ))` is evaluated at `γ = −3.5` in `tests/test_beta.py`
- **THEN** there MUST exist a pytest assertion `σ'(−3.5) == pytest.approx(0.0284530238797355598396878271273, abs=1e-30)` that nails the mpmath closed form. The literal MUST be a transcription of the closed form accurate to at least 31 decimal places, because `abs=1e-30` is only satisfiable at that depth: the 31-dp transcription above differs from the closed form by `3.93e-34`, whereas a 20-dp truncation (`0.02845302387973555984`) differs by `3.12e-22` — `3.12e8 ×` the mandated tolerance, so the requirement would be unsatisfiable as previously written
- **AND** both operands of that assertion MUST be compared in `mpmath.mpf` precision; neither side may be routed through `float()`. float64 resolution at this magnitude is `≈6.3e-18`, eleven orders of magnitude coarser than `abs=1e-30`, so a float64-cast comparison makes the tolerance inert and the 钉值零容差 guarantee non-existent even when the test reports green
- **AND** a paired assertion `round(σ'(−3.5), 5) == 0.02845` that nails the L130 narrative 4-sig-fig precision disclosure at its own 4-sig-fig display precision. A 4-sig-fig display literal MUST NOT be pinned by a tolerance wider than its half-unit `5e-6`; the previous `abs=1e-5` was exactly `2 ×` that half-unit, the same defect class `governance` req-gov-1 already rejected for the Voronoi `versine` literals
- **AND** this test MUST be retained after archive of `.audit/audit-verification/` (i.e., it lives in the durable `tests/` tree, not in the drop-on-archive audit tree)

#### Scenario: Source field lists all three referenced tickets
- **WHEN** the `**Source:**` field of this Requirement is enumerated
- **THEN** it contains three backtick-wrapped ticket references `` `wayfinder/tickets/A4-1.md` ``, `` `wayfinder/tickets/A4-2.md` ``, `` `wayfinder/tickets/A6b-1.md` `` (A4-1 is the **主反链** and MUST appear first per lint req-34 paren-depth-aware code-span atomic split; A4-2 covers the `w_i` 剔除 narrative at the requirement's last paragraph; A6b-1 covers the AdamW momentum reset narrative at the Phase 4 bullet)

<a id="req-26"></a>

### Requirement: Operational Domain γ' Reset Closed-Form Worked Example

On entering Phase 4, the system MUST reset `γ` to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so that `β^eff` is continuous at the Phase 3 → 4 boundary. The worked example for `β_{p3} = 16.0` MUST evaluate to `γ' = ln(15/16) ≈ −0.0645385...`. AdamW momentum for `γ` MUST be reset on the same boundary. The closed form is pinned: `gamma_reset_for_phase4(16.0) ≈ −0.06454`, stated at 5-decimal display precision and therefore guarded by the exact rounding assertion `round(gamma_reset_for_phase4(16.0), 5) == -0.06454`. A 5-decimal display literal MUST NOT be pinned by a tolerance wider than its own half-unit `5e-6`; the previous `abs=1e-4` was `20 ×` that half-unit and admitted any γ-reset wrong by up to `0.15%` relative, which `governance` req-gov-1 obligation 2 forbids under either the display-literal or the float-closed-form reading. (References Req 7 Invariant 3 / Req 24.)

**Source:** `wayfinder/tickets/A4-1.md` (historical, γ parameterization origin: `β_min + (β_max−β_min)·σ(γ)`), `wayfinder/tickets/A6b-2.md` (historical, phase-boundary optimizer state policy); change `fix-math-consistency-audit-2026-08` design.md (Decision 2 — closed-form `γ' = ln((β_{p3}−1)/(32−β_{p3}))` added by this change)

#### Scenario: gamma reset is a real root of the boundary continuity equation

- **WHEN** the schedule enters Phase 4 with `β_{p3} = 16.0`
- **THEN** `γ' = ln((16 − 1) / (32 − 16)) = ln(15/16) ≈ −0.0645385...` and the resulting `β^eff(Phase 4, t=0) = 1 + 31 · σ(γ') = 16.0` exactly (continuity at the boundary)

<a id="req-28"></a>

### Requirement: Resurrection Perturbation Per-Expert Contract

The Dead Expert Splitting Resurrection pathway (Req 13) MUST perturb the **single cloned expert** (centroid and/or expert weights) — not the per-expert routing frequency vector `f_per_expert`. The perturbation API `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)` MUST accept `f_per_expert` as the leading positional argument with **shape `(..., N_e)`** — the trailing axis MUST equal `N_e` and leading dims are arbitrary (canonical call sites pass `(N_e,)`, `(T, N_e)`, or `(B, N, N_e)` matching the per-expert routing-frequency convention used by `decompmoe.loss` and `decompmoe.metrics`). Layer 1 shape enforcement (primitive-side, at this primitive): `f_per_expert.ndim ≥ 1` so the primitive cannot silently receive a 0-D scalar. Layer 2 wrapper-side enforcement (trailing-axis = `cfg.N_e` pair-check, enforced at the canonical call site `resurrect_expert`) is described in Req 32. `target_idx` is a positional integer identifying the dead expert slot, `eps_std=0.05` is a positional-or-keyword Gaussian perturbation scale, and `dim` is a **keyword-only** parameter sourcing the per-expert dimensionality (centroid `d_c` or expert-weight `d_model · d_ffn`). `dim=None` MUST raise `TypeError` (explicit `dim` is required so the return-shape contract is enforced at the call site). The returned tensor MUST have leading dimension `dim` — corresponding to a single expert slot — NOT the `(N_e,)` shape of `f_per_expert`. The β double-write semantic (`β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`) is defined in Req 13; this primitive does not mutate `β_per_expert` — that mutation is the wrapper's responsibility. (References Req 13.)

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-math-consistency-audit-2026-08` design.md (Decision 4 — per-expert perturbation contract); signature mirrors the `resurrection_perturb_distribution` function in `src/decompmoe/safeguards.py` at commit `263ac19 feat(safeguards): per-expert resurrection perturb shape + same-event beta decay` (Layer 1 primitive-side `ndim ≥ 1` guard inside that function)

#### Scenario: perturbation output shape matches a single expert slot
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called (explicit `dim` required; `dim=None` raises `TypeError`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

<a id="req-32"></a>

### Requirement: Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper

The Dead Expert Splitting Resurrection pathway (Req 13) MUST perturb the **single cloned expert** (centroid and/or expert weights) — not the per-expert routing frequency vector `f_per_expert`. The perturbation API `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)` MUST accept `f_per_expert` as the leading positional argument with **shape `(..., N_e)`** — the trailing axis MUST equal `N_e` and leading dims are arbitrary (canonical call sites pass `(N_e,)`, `(T, N_e)`, or `(B, N, N_e)`). Layer 2 shape enforcement (wrapper-side, at this wrapper): `f_per_expert.shape[-1] == cfg.N_e` pair-check. The vacuous self-check `f_per_expert.shape[-1] == β_per_expert.shape[0]` (which is identically true given `f_per_expert = β_per_expert.detach()` inside this wrapper, where `shape[-1] == shape[0]`) was an earlier draft and was corrected by commit `0b2202e` to anchor on the spec-defined `cfg.N_e`. Layer 1 primitive-side enforcement (`ndim ≥ 1`) is described in Req 28. `target_idx` is a positional integer, `eps_std=0.05` is a positional-or-keyword perturbation scale, and `dim` is a **keyword-only** parameter sourcing the per-expert dimensionality. `dim=None` MUST raise `TypeError`. The returned tensor MUST have leading dimension `dim` — corresponding to a single expert slot — NOT the `(N_e,)` shape of `f_per_expert`. The β double-write semantic (`β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`) is defined in Req 13; this wrapper additionally guarantees same-call-stack execution (see wrapper contract paragraph below). (References Req 13.)

**The canonical single-event API is `resurrect_expert(i, j_star, β_per_expert, cfg) -> tuple[Tensor, Tensor]`** which returns `(c_perturbed, β_per_expert_new)` and guarantees that the centroid perturbation and the β double-write happen in the **same Python call stack** — no `yield` / `await` / background-task scheduling between the two operations. Callers MUST use `resurrect_expert` for the resurrection pathway; the two primitives `resurrection_perturb_distribution` and `apply_resurrection_beta_decay` remain available for low-level composition but their separate invocation does NOT satisfy the "same resurrection event" contract above. The wrapper signature takes `cfg: MVPConfig` so the per-expert dimensionality `cfg.d_c` is sourced from the canonical config rather than re-derived from `β_per_expert.shape` (which would conflate centroid dimension with the `N_e` routing dimension — the very bug the per-expert contract exists to prevent).

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
- **WHEN** `resurrect_expert(i=3, j_star=0, β_per_expert, cfg)` is called with `β_per_expert.detach()` (the wrapper's internal `f_per_expert = β_per_expert.detach()`) whose trailing axis length `!= cfg.N_e` (the canonical N_e sourced from `cfg.MVPConfig`, **NOT** `β_per_expert.shape[0]` — the latter would be a vacuous self-check given `f_per_expert = β_per_expert.detach()`, where `shape[-1] == shape[0]` identically)
- **THEN** the wrapper raises `ValueError` (Layer 2 guard: trailing-axis = N_e pair-check, anchored on `cfg.N_e`)

#### Scenario: same-event beta decay
- **WHEN** `resurrect_expert(i, j_star, β_per_expert, cfg)` is called with any valid `MVPConfig cfg`, valid expert indices `i` and `j_star` (`0 ≤ i, j_star < N_e`, `i ≠ j_star`), and a valid `β_per_expert ∈ R^{N_e}` (positive finite values)
- **THEN** the returned `c_perturbed` is the output of `resurrection_perturb_distribution(β_per_expert.detach(), j_star, eps_std=0.05, dim=cfg.d_c)` and the returned `β_per_expert_new` is the output of `apply_resurrection_beta_decay(β_per_expert, j_star, i)`, with both calls executed in the **same call stack** (no `await` / `yield` / `spawn` between them — verifiable by inspecting the wrapper's linear code path which is a synchronous function composition)
- **AND** `β_per_expert_new[i] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (donor value is read from `β_per_expert[j_star]` BEFORE either write, per the immutability clause; this matches the canonical pattern in `apply_resurrection_beta_decay`)
- **AND** `β_per_expert_new[j_star] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (the donor's own β is also decayed by the same factor)
- **AND** `c_perturbed.shape == (cfg.d_c,)` (single-expert slot shape, consistent with the perturbation output shape scenario above)
- **AND** `β_per_expert_new is not β_per_expert` (immutability: the input tensor is never mutated in-place; `apply_resurrection_beta_decay` clones internally)
