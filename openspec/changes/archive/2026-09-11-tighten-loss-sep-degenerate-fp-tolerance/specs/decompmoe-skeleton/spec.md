## MODIFIED Requirements

### Requirement: Loss Composition With Staged Lambda

The package SHALL provide `L_total(task_logits, targets, f_per_expert, p_per_expert, c_centroids, phase, step, *, cfg) -> LossParts` returning a dataclass with `.L_CE`, `.L_lb`, `.L_sep`, `.L_total` fields. The constants SHALL be: `α = 0.01` (Switch-style fixed weight on `L_lb`), `λ(t)` schedule = `0` for `phase ∈ {1, 2}`, cosine ramp `0 → 0.001` during `phase == 3`, and `0.001` fixed for `phase == 4`. The `L_lb` closed form MUST be `L_lb = N_e · Σ_i f_i.detach() · P_i`, where `P_i = (1/T) · Σ_t p_i(C_t)` is the per-expert differentiable soft routing probability; gradient MUST flow through `P_i` and be blocked through `f_i.detach()`. The previous "verified by source grep" acceptance is incorrect (permits any expression containing `.detach()`); it MUST be replaced by the testable invariant `∂L_lb / ∂P_i ≠ 0` AND `∂L_lb / ∂f_i ≡ 0`. `L_sep` SHALL equal `(‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1))` (canonical Frobenius form); the `Σ_{i<j}` equivalent form MUST use factor `2/(N_e(N_e − 1))` — the factor `1/(N_e(N_e − 1))` is INCORRECT and MUST NOT appear. (Matches master `wayfinder` Req 12 verbatim.)

#### Scenario: Alpha pinned to 0.01
- **WHEN** `L_total(...)` is evaluated with uniform `f = P = 1/N_e`
- **THEN** `L_lb_raw = N_e · Σ (1/N_e) · (1/N_e) = 1.0` exactly and the `L_lb` contribution equals `0.01 · 1.0 = 0.01` exactly regardless of phase

#### Scenario: Lambda zero in phases 1 and 2
- **WHEN** `phase ∈ {1, 2}`
- **THEN** the `L_sep` contribution equals `0.0` within `abs=1e-12` (i.e. `λ(t) == 0`)

#### Scenario: Lambda cosine ramp endpoints in phase 3
- **WHEN** `phase == 3` and `step ∈ {26_000, 41_000, 55_999}` (phase boundary, midpoint, near-end)
- **THEN** `λ(26_000) == 0.0` (cosine starts at `0`) AND `λ(41_000) ≈ 5e-4` (cosine midpoint, `0.5 · (1 − cos(π/2)) · 0.001`) AND `λ(55_999) ≈ 0.001` (cosine reaches asymptote)

#### Scenario: Lambda fixed in phase 4
- **WHEN** `phase == 4`
- **THEN** `λ(t) == 0.001` constant across `step`

#### Scenario: L_sep closed form
- **WHEN** `c_centroids ∈ R^{N_e × d_c}` is on the unit sphere AND forms an orthogonal basis (e.g. `c = I_d` truncated to `N_e` rows when `N_e = d_c`)
- **THEN** `L_sep == (‖CᵀC‖_F² − N_e) / (N_e · (N_e − 1)) == 0.0` exactly (within `abs=1e-12`)

#### Scenario: L_lb gradient flows through P_i only
- **WHEN** `L_lb` is back-propagated
- **THEN** `∂L_lb / ∂P_i ≠ 0` (differentiable through `P_i`) and `∂L_lb / ∂f_i ≡ 0` (blocked by `.detach()`)
