# Spec Delta

## MODIFIED Requirements

### Requirement: Operational Domain γ' Reset Closed-Form Worked Example

On entering Phase 4, the system MUST reset `γ` to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so that `β^eff` is continuous at the Phase 3 → 4 boundary. The worked example for `β_{p3} = 16.0` MUST evaluate to `γ' = ln(15/16) ≈ −0.0645385...`. AdamW momentum for `γ` MUST be reset on the same boundary. The closed form is pinned: `gamma_reset_for_phase4(16.0) ≈ −0.06454` within `abs=1e-4`. (References Req 7 Invariant 3 / Req 24.)

**Source:** `wayfinder/tickets/A4-1.md` (historical, γ parameterization origin: `β_min + (β_max−β_min)·σ(γ)`), `wayfinder/tickets/A6b-2.md` (historical, phase-boundary optimizer state policy); change `fix-math-consistency-audit-2026-08` design.md (Decision 2 — closed-form `γ' = ln((β_{p3}−1)/(32−β_{p3}))` added by this change)

#### Scenario: gamma reset is a real root of the boundary continuity equation

- **WHEN** the schedule enters Phase 4 with `β_{p3} = 16.0`
- **THEN** `γ' = ln((16 − 1) / (32 − 16)) = ln(15/16) ≈ −0.0645385...` and the resulting `β^eff(Phase 4, t=0) = 1 + 31 · σ(γ') = 16.0` exactly (continuity at the boundary)

### Requirement: Beta Parameterization Space vs Operational Domain

The system MUST maintain a clean separation between two domains: the **parameterization space** (`β^param(γ) = 0.1 + 31.9 · σ(γ)`, theoretical interval `[0.1, 32]`) and the **operational domain** (per-phase effective `β^eff`). `β_min = 0.1` exists in parameterization space to keep `σ'(γ)` non-degenerate in the cold-start region (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.02845`, verified at 50-digit mpmath precision `σ'(−3.5) = 0.02845302387973555984`; lowering the floor to `1.0` (i.e., switching to the counterfactual parameterization `β = 1.0 + 31.0 · σ(γ)`) would require `γ_init ≈ −6.785`, with `σ'(−6.785) ≈ 1.128e-3`, a 25× gradient starvation). The operational floor `1.0` is independent and exists to prevent routing resonance at runtime. Per-phase effective `β^eff`:

- Phase 1: `β^eff = 1.0` (fixed, regardless of `γ`).
- Phase 2–3: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase schedule (`1.0 → 4.0` Phase 2, `4.0 → 16.0` Phase 3).
- Phase 4: `β^eff = 1 + 31.0 · σ(γ')` — continuous reparameterization. On Phase 4 entry, `γ` is reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum for `γ` is reset. This avoids the hard-clamp gradient-zero trap at the `[1.0, 32.0]` box boundary.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A6b-1.md`

#### Scenario: Parameterization floor preserves cold-start gradient

- **WHEN** `γ` is initialized to `γ_init ≈ −3.5`
- **THEN** `β_0 ≈ 1.035` and `σ'(γ_init) ≥ 0.02` (healthy gradient in the cold-start region)

#### Scenario: Phase 3 → 4 transition is continuous

- **WHEN** Phase 4 is entered at `β_{p3} = 16.0`
- **THEN** `γ' = ln(15/16) ≈ −0.0645385...` is set, AdamW momentum for `γ` is reset, and `β^eff(Phase 4, t=0) = 16.0` exactly (continuity)