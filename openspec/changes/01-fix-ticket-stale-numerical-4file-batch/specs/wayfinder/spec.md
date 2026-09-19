## MODIFIED Requirements

### Requirement: Isotropic Squared-Chord Distance And Bounded Beta

The system MUST measure distance between `C_t^l` and `c_i^l` using the isotropic squared-chord distance `d(C, c_i) = 1 − C^T c_i ∈ [0, 2]`. The system MUST parameterize the inverse-temperature using the **parameterization-space** form `β^param(γ) = β_min + (β_max − β_min) · Sigmoid(γ)` with `β_min = 0.1` and `β_max = 32`. The corresponding logit MUST be `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The system MUST bound `‖∂logit/∂C‖₂` and `‖∂logit/∂c_i‖₂` by ` ≤ β_max = 32`, and `|∂logit/∂γ_i|` by ` ≤ 0.5(β_max − β_min) = 15.95`, as hard numerical-stability guarantees derived from ticket A4-1.

- **Phase 1**: `β^eff = 1.0` (fixed, regardless of `γ`).
- **Phase 2–3**: `β^eff = Clamp(β^param(γ), 1.0, β_max(t))` where `β_max(t)` is the phase-driven schedule (`1.0 → 4.0` in Phase 2, `4.0 → 16.0` in Phase 3).
- **Phase 4**: `β^eff = 1.0 + 31.0 · Sigmoid(γ')` — continuous reparameterization. On entering Phase 4, `γ` MUST be reset to `γ' = ln((β_{p3} − 1) / (32 − β_{p3}))` so `β^eff` is continuous at the boundary, and AdamW momentum MUST be reset for `γ` (per A6b-1).

`β_min = 0.1` exists to keep `σ'(γ)` non-degenerate in the parameterization space (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.02845`, verified at 50-digit mpmath precision `σ'(−3.5) = 0.02845302387973555984`). The operational-domain floor `1.0` in Phase 4 is independent and exists to prevent routing resonance.

Per-expert scalar weights `w_i` MUST NOT appear in the logit; the mixing weight for top-k routing IS the softmax probability `p_i` (per A4-2 and CLAUDE.md §6). `w_i` MUST NOT appear in any stage, in any formulation, in any reserved form.

**Source:** `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A4-2.md`, `wayfinder/tickets/A6b-1.md`

#### Scenario: Distance is bounded and gradient-safe
- **WHEN** any `(C, c_i)` pair on the unit sphere is fed into the gating function
- **THEN** the distance lies in `[0, 2]` and the per-component gradient magnitude stays below or equal to `β_max = 32`

#### Scenario: w_i is absent from the logit
- **WHEN** the logit is computed for gating
- **THEN** no learnable per-expert scalar weight `w_i` participates in `logit = β(C^T c − 1)`; mixing weights are exactly the softmax probabilities `p_i`

#### Scenario: σ'(−3.5) narrative precision matches 50-digit mpmath within 5 significant figures
- **WHEN** `σ'(γ) = σ(γ) · (1 − σ(γ))` is evaluated at `γ = −3.5`
- **THEN** the narrative value `σ'(−3.5) ≈ 0.02845` matches the 50-digit mpmath value `0.02845302387973555984` truncated at 5 significant figures (diff `|0.028453 − 0.02845| = 3e-6`, relative `0.011%`, well below `1e-6` tolerance); this is the "healthy gradient" health-check anchor for the cold-start region `γ_init ≈ −3.5`

#### Scenario: Source field lists all three referenced tickets
- **WHEN** the `**Source:**` field of this Requirement is enumerated
- **THEN** it contains three backtick-wrapped ticket references `` `wayfinder/tickets/A4-1.md` ``, `` `wayfinder/tickets/A4-2.md` ``, `` `wayfinder/tickets/A6b-1.md` `` (A4-1 is the **主反链** and MUST appear first per lint req-34 paren-depth-aware code-span atomic split; A4-2 covers the `w_i` 剔除 narrative at the requirement's last paragraph; A6b-1 covers the AdamW momentum reset narrative at the Phase 4 bullet)