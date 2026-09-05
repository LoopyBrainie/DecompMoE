# decompmoe-skeleton Specification (delta)

## MODIFIED Requirements

### Requirement: Beta Parameterization Operational Domain

The package SHALL provide `inverse_temperature(gamma) -> Tensor` implementing the **parameterization-space** form `β = β_min + (β_max − β_min) · σ(γ)` with `β_min == 0.1` and `β_max == 32`. The package SHALL additionally provide `phase4_inverse_temperature(gamma_p) -> Tensor` implementing the **operational-domain** form `β^eff = 1 + 31 · σ(γ')` used in Phase 4 (the parameterization-space floor `0.1` and the operational-domain floor `1.0` are intentionally decoupled — the latter prevents routing resonance at runtime, the former keeps `σ'(γ)` non-degenerate in the cold-start region). The package SHALL provide `gamma_reset_for_phase4(beta_p3) -> float` implementing `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))`; the worked example `gamma_reset_for_phase4(16.0) ≈ −0.0645385...` MUST hold within `abs=1e-4`. The package SHALL provide `beta_effective(gamma, phase, step, *, cfg) -> Tensor` returning `1.0` for `phase == 1`, `Clamp(inverse_temperature(gamma), 1.0, phase_beta_max(phase, step))` for `phase ∈ {2, 3}` (where `phase_beta_max(phase, step)` is the **time-varying** schedule ramp under the **pinned** linear-interpolation convention `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive: Phase 2 range `[6_000, 26_000)` ramp `1.0 → 4.0` (so `phase_beta_max(2, 6_000) = 1.0` exact at boundary start, `phase_beta_max(2, 16_000) = 2.5` exact at midpoint, `phase_beta_max(2, 25_999) = 1 + 3·19_999/20_000 = 3.99985`); Phase 3 range `[26_000, 56_000)` ramp `4.0 → 16.0` (so `phase_beta_max(3, 26_000) = 4.0` exact at boundary start = `box(3).lo`, `phase_beta_max(3, 41_000) = 4 + 12·15_000/30_000 = 10.0` exact at midpoint, `phase_beta_max(3, 55_999) = 4 + 12·29_999/30_000 = 15.9996`). `phase_beta_max` is **distinct** from the static `phase_beta_box(phase).hi` and the `step` parameter is required), and `phase4_inverse_temperature(gamma_p)` for `phase == 4`. The module SHALL export `MAX_GRAD_PER_C: Final[float] = 32.0` (operational-domain worst case, all domains) and `MAX_GRAD_PER_GAMMA: Final[float] = 15.95` (**parameterization-space** worst case `0.5 · (β_max − β_min)`; the **operational-domain Phase 4** worst case is `0.5 · 31 = 15.5` at `γ' = 0` (canonical export per `src/decompmoe/beta.py:39` `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`); the two constants live in different domains and MUST NOT be conflated). (Matches master `wayfinder` Req 7 / Req 24 verbatim.)

#### Scenario: Parameterization endpoints
- **WHEN** `inverse_temperature(gamma)` is called with `gamma ∈ {-50, 0, 50}`
- **THEN** the result is `≈ 0.1` / `16.05` (midpoint) / `≈ 32.0` respectively within `1e-3`

#### Scenario: gamma reset for phase 4 boundary continuity
- **WHEN** `gamma_reset_for_phase4(16.0)` is called
- **THEN** the result equals `ln(15/16) ≈ −0.0645385...` within `abs=1e-4`

#### Scenario: beta_effective is continuous at Phase 3 → 4 boundary
- **WHEN** `beta_effective(gamma_p=ln(15/16), phase=4, step=56_000)` is called
- **THEN** the result equals `1 + 31 · σ(ln(15/16)) = 16.0` exactly (continuity with Phase 3's terminal `β_max`)

#### Scenario: closed-form MAX_GRAD_PER_GAMMA_PHASE4 derivation matches code
- **WHEN** the spec text states the operational-domain Phase 4 worst case as `0.5 · 31 = 15.5` at `γ' = 0`
- **THEN** the closed-form product `0.5 · 31` evaluates to `15.5` exactly (within `abs=1e-9`), matching `src/decompmoe/beta.py:39` `MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`; the previous erroneous derivation `0.5 · 31 · 2 = 15.5` (literal product `31`) is removed