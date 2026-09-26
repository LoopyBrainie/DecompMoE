## ADDED Requirements

### Requirement: Isotropic Squared-Chord Distance And Bounded Beta — σ' Precision Refinement And Source Field Closure

The system MUST measure distance between `C_t^l` and `c_i^l` using the isotropic squared-chord distance `d(C, c_i) = 1 − C^T c_i ∈ [0, 2]`. The system MUST parameterize the inverse-temperature using the **parameterization-space** form `β^param(γ) = β_min + (β_max − β_min) · Sigmoid(γ)` with `β_min = 0.1` and `β_max = 32`. The corresponding logit MUST be `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The system MUST bound `‖∂logit/∂C‖₂` and `‖∂logit/∂c_i‖₂` by ` ≤ β_max = 32`, and `|∂logit/∂γ_i|` by ` ≤ 0.5(β_max − β_min) = 15.95`, as hard numerical-stability guarantees derived from ticket A4-1.

**Operational-domain override (Invariant 3)**: per-phase effective β MUST be:
- **Phase 1**: `β^eff = 1.0` (fixed, regardless of `γ`).
- **Phase 2–3**: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase-driven schedule (`1.0 → 4.0` in Phase 2, `4.0 → 16.0` in Phase 3).
- **Phase 4**: `β^eff = 1.0 + 31.0 · Sigmoid(γ')` — continuous reparameterization. On entering Phase 4, `γ` MUST be reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum MUST be reset for `γ` (per A6b-1).

`β_min = 0.1` exists to keep `σ'(γ)` non-degenerate in the parameterization space (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.02845`, verified at 50-digit mpmath precision `σ'(−3.5) = 0.02845302387973555984`). The operational-domain floor `1.0` in Phase 4 is independent and exists to prevent routing resonance.

Per-expert scalar weights `w_i` MUST NOT appear in the logit; the mixing weight for top-k routing IS the softmax probability `p_i` (per A4-2 and CLAUDE.md §6). `w_i` MUST NOT appear in any stage, in any formulation, in any reserved form.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A4-2.md`, `wayfinder/tickets/A6b-1.md`

#### Scenario: Closed-form β_0 initial parameterization at γ_init = −3.5

- **WHEN** `β^param(γ_init = −3.5)` is evaluated via the closed form `0.1 + 31.9 · Sigmoid(−3.5)`
- **THEN** `β_0 ≈ 1.035` within `abs=1e-3` (the narrative `≈ 1.035` matches the 50-digit mpmath value `1.0350601609682665718` truncated at 4 significant figures; `MVPConfig.beta_initial = 1.035` stores this narrative概略作为 Phase 1 宽门控探索的默认值 per ticket A4-1 L58 historical trace)

#### Scenario: σ'(−3.5) healthy gradient

- **WHEN** `σ'(γ)` is evaluated at `γ = −3.5` where `σ'(γ) = σ(γ) · (1 − σ(γ))`
- **THEN** `σ'(−3.5) ≈ 0.02845` within `abs=1e-4` (the narrative `≈ 0.02845` matches the 50-digit mpmath value `0.02845302387973555984` truncated at 5 significant figures; this is the "healthy gradient" health-check anchor for the cold-start region `γ_init ≈ −3.5`)

#### Scenario: Source field lists all three referenced tickets

- **WHEN** the `**Source:**` field of this Requirement is enumerated
- **THEN** it contains three backtick-wrapped ticket references `\`wayfinder/tickets/A4-1.md\``, `\`wayfinder/tickets/A4-2.md\``, `\`wayfinder/tickets/A6b-1.md\`` (A4-1 is the **主反链** and MUST appear first per lint req-34 paren-depth-aware code-span atomic split; A4-2 covers the w_i 剔除 narrative at L124; A6b-1 covers the AdamW momentum reset narrative at L120)

#### Scenario: Ticket A4-1 L58 historical supersede annotation preserved

- **WHEN** `wayfinder/tickets/A4-1.md` L58 is read for the `β_0 ≈ 1.0` historical estimate
- **THEN** the line preserves the original `γ_init ≈ -3.5 → β_0 ≈ 1.0` (Phase 1 宽门控探索) text AND a subsequent annotation `(historical, β_0 ≈ 1.0 estimate; superseded by spec req-7 L122 closed-form β_0 = 1.035060 via change fix-math-consistency-audit-2026-08 Decision 1)` follows immediately (the original stale数字 is retained for ticket lineage traceability; supersede annotation tells future readers that the数字 is historical, not current spec truth)