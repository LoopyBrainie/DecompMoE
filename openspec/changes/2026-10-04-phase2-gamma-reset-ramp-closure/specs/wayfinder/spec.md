# Spec Delta

## MODIFIED Requirements

### Requirement: Beta Parameterization Space vs Operational Domain

The system MUST maintain a clean separation between two domains: the **parameterization space** (`β^param(γ) = 0.1 + 31.9 · σ(γ)`, theoretical interval `[0.1, 32]`) and the **operational domain** (per-phase effective `β^eff`). `β_min = 0.1` exists in parameterization space to keep `σ'(γ)` non-degenerate in the cold-start region (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.02845`, verified at 50-digit mpmath precision `σ'(−3.5) = 0.0284530238797355598396878271273`; lowering the floor to `1.0` (i.e., switching to the counterfactual parameterization `β = 1.0 + 31.0 · σ(γ)`) would require `γ_init ≈ −6.7835`, with `σ'(-6.7835) ≈ 1.130e-3`, a 25× gradient starvation). The operational floor `1.0` is independent and exists to prevent routing resonance at runtime. Per-phase effective `β^eff`:

- Phase 1: `β^eff = 1.0` (fixed, regardless of `γ`).
- Phase 2–3: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase schedule (`1.0 → 4.0` Phase 2, `4.0 → 16.0` Phase 3).
- Phase 4: `β^eff = 1 + 31.0 · σ(γ')` — continuous reparameterization. On Phase 4 entry, `γ` is reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum for `γ` is reset. This avoids the hard-clamp gradient-zero trap at the `[1.0, 32.0]` box boundary.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A6b-1.md`, change `2026-09-28-fix-a2-a3-a4-residual-precision-claims` design.md (Decision 3 — counterfactual `γ_init` last-digit rounding correction; exact 50-digit mpmath value `−6.783545399795103364342` derived from `β_0 = 0.1 + 31.9·σ(−3.5) = 1.035060160968266571803`), change `2026-10-04-phase2-gamma-reset-ramp-closure` design.md (Decision 1 — Phase-2 entry γ reset and the Phase-2/3 gradient-path boundary; the two added Scenarios)

#### Scenario: Parameterization floor preserves cold-start gradient

- **WHEN** `γ` is initialized to `γ_init ≈ −3.5`
- **THEN** `β_0 ≈ 1.035` and `σ'(γ_init) ≥ 0.02` (healthy gradient in the cold-start region)

#### Scenario: Phase 3 → 4 transition is continuous

- **WHEN** Phase 4 is entered at `β_{p3} = 16.0`
- **THEN** `γ' = ln(15/16) ≈ −0.0645385...` is set, AdamW momentum for `γ` is reset, and `β^eff(Phase 4, t=0) = 16.0` exactly (continuity)

#### Scenario: Counterfactual β_min = 1.0 forces a 5-significant-figure γ_init

- **WHEN** the counterfactual parameterization `β = 1.0 + 31.0 · σ(γ)` is required to reproduce the same `β_0` as the adopted `β^param(γ) = 0.1 + 31.9 · σ(γ)` at `γ_init ≈ −3.5`
- **THEN** the required `γ_init` is `≈ −6.7835` (exact 50-digit mpmath value `−6.783545399795103364342`), NOT `−6.7836` — the latter back-substitutes to `β_0 = 1.0350582488933886469` instead of the spec's `β_0 = 1.035060160968266571803`
- **AND** the test guarding this claim MUST derive `β_0` independently from the adopted-path declaration `γ_init ≈ −3.5` and then invert it to the counterfactual `γ_init` (a cross-reconciliation of two separate spec declarations, not a re-statement of the asserted expression), and MUST assert the 5-sig literal form via `round(γ_full, 4) == -6.7835` so that a half-up rounding of the exact value to `-6.7836` fails the guard
- **AND** the guard tolerance MUST accommodate the rounding error of the 5-sig literal `−6.7835`, stated with its reference frame explicit rather than as a single unlabelled number: in **γ-space** the literal sits `4.54e-5` from the exact root (`|−6.7835 − (−6.783545399795103364342)| = 4.5399795e-5`), and it is this γ-space gap that the normative `abs=1e-4` tolerance bounds (`2.2×` the gap); the *same* discrepancy expressed in **β-space** is `|β(−6.7835) − β_0| = 1.5899599e-6`, consistent with the γ-gap times the local slope `|dβ/dγ| = 31 · σ'(−6.7835) = 0.0350220952386` (`4.5399795e-5 × 0.0350220952386 = 1.5899959e-6`, matching the exact β residual to `2.3e-5` relative). A tolerance near machine epsilon is NOT valid for a 5-significant-figure literal. (For contrast the rejected `−6.7836` literal has β-space residual `1.9120749e-6` at slope `0.0350186011251` — only `20%` larger than the `−6.7835` residual — while its γ-space gap is `5.46e-5` rather than `4.54e-5`. A β-space guard therefore does **not** separate the two literals: any `abs` that admits `1.5899599e-6` also admits `1.9120749e-6`, so the discriminating assertion is necessarily in γ-space — the `round(γ_full, 4) == -6.7835` guard above, which `−6.7836` fails by `1e-4`.)

#### Scenario: Phase-2 entry γ reset saturates the operational clamp (float32 frame)

- **WHEN** `β^eff` is evaluated at the Phase-2 entry γ reset value `gamma_reset_for_phase2() = 0.0`, for `phase ∈ {2, 3}` and `step` swept over the pinned phase grid
- **THEN** in the declared **float32 operational frame** — the frame the implementation runs in, because `torch.as_tensor(<python float>)` adopts the torch default float dtype and the clamp's `max` scalar is therefore cast to float32 before it saturates — the result MUST be **bit-identical** to `torch.tensor(phase_beta_max(phase, step), dtype=torch.float32)`. This is the saturated-branch identity: the clamp returns its upper bound, so the exact-arithmetic equality `β^eff ≡ phase_beta_max` holds by construction
- **AND** the reset value MUST keep that saturation **strict within the same frame**: `float32(β^param(0)) = 16.0499992 > float32(phase_beta_max(3, 55_999)) = 15.9996004`, i.e. margin `0.0503988` in the float32 frame (`0.0504` in exact arithmetic). The exact saturation threshold is `γ* = logit(0.49841943…) = −0.006319770250253427`, whose margin is `≈ 0` **by construction** — it is the boundary itself, not a safe operating point. The rounded literal `−0.006318` does saturate, but only by `1.41e-5` (exact arithmetic; `1.34e-5` in the float32 frame), so `0.0` is the boundary-robust choice by a factor of `≈ 3574` in exact arithmetic. Note that the *derivation* `logit(0.498420) = −0.006320021…` overshoots into a **negative** margin (`−2.0e-6`) and does not saturate at all: any γ at or below it violates this clause
- **AND** the offset between the float32 result and the float64-computed `phase_beta_max` is **representation error only**, measured max `4.10e-7` over the same sweep (≈ half-ulp at 16). It is **documentation, NOT a test tolerance**
- **AND** the equality MUST **NOT** be restated as a bare `==` against a float64-computed `phase_beta_max`: such a form is unsatisfiable by construction and, read as a guard, looks stricter while being weaker. This follows the `decompmoe-skeleton` req-19 display-form precedent (a "equals 1.0" claim degraded from exact equality to a provable bound, with an explicit prohibition on restating it as bare `==`) and governance req-gov-1 §2
- **AND** the lower clamp MUST NOT engage in Phase 2 — the prior behaviour pinned `β^eff` at `1.035` from step `6_233` onward (because `phase_step_frozen_names(2)` includes `beta_i`, so `γ` was frozen at `γ_init` and `β^param ≡ 1.035060`), which violated Req 14's `1.0 → 4.0` ramp; the arrival step of any `β^param`-driven traversal MUST NOT be relied upon, because it is not determined by this spec — it depends on `lr` and the weight-decay coefficient, neither of which is pinned

#### Scenario: The γ gradient path exists only from Phase 4 onward

- **WHEN** `γ` is a tensor with `requires_grad = True`, and `β^eff` is composed as the constant `1.0` for phase 1, as `Clamp(inverse_temperature(γ), 1.0, phase_beta_max(phase, step))` for phases 2–3, or as `phase4_inverse_temperature(γ)` for phase 4
- **THEN** `∂β^eff/∂γ ≡ 0` for phases 1–3 — Phase 1 is the constant function `1.0`, Phases 2–3 are upper-clamp saturation at `cap(t)`
- **AND** for Phase 4 at the reset point `γ' = ln(15/16)`, `σ(γ') = 15/31` and `σ'(γ') = (15/31)(16/31) = 240/961`, so `∂β^eff/∂γ' = 31 · σ'(γ') = 240/31 ≈ 7.7419355`
- **AND** the three gradient quantities MUST NOT be conflated: `7.75 = 31·σ'(0)` is the **upper bound at `γ' = 0`** (exported as `MAX_GRAD_PER_GAMMA_PHASE4 / 2`); `240/31` is the **slope at the reset point**; `0.9077 = 31.9·σ'(−3.5)` is a **parameterization-space** quantity at `γ_init` and is NOT an operational-domain value
- **AND** the schedule-layer helper `beta_effective` MUST keep taking `gamma_p: float` and returning a leaf tensor (`requires_grad = False`, `grad_fn = None`) — the differentiable primitives remain `inverse_temperature` and `phase4_inverse_temperature` in `decompmoe/beta.py`
