# Spec Delta: wayfinder

## MODIFIED Requirements

### Requirement: Naming And Alias Convention

The system MUST adopt **DecompMoE** as the canonical project name and MUST adopt **GeoMoE** as a documented alias (per CLAUDE.md §1 project-level amendment; GeoMoE was never previously a canonical name — it is a deliberate alias upgrade, not a downgrade). The alias MUST appear only in design prose and never as a code identifier.

**Source:** `wayfinder/tickets/A0-1.md`

#### Scenario: Canonical reference resolution
- **WHEN** any artifact, doc, or code comment refers to the project
- **THEN** the reference uses "DecompMoE" as the primary name, with "GeoMoE" only as a secondary alias inside design prose

### Requirement: Formal Symbols And Code Naming

The system MUST use formal symbol `Σ_i` (per-expert covariance), `P_i = Σ_i^{-1}` (precision matrix), and the subscript convention `(i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S)` for expert / layer / head / token — where the per-head index `h` enumerates the KV-head axis (per req-5 cross-head mean `z̄_t^l = (1/H_kv) · Σ_h C_t^{l,h}`), which at MVP equals the Q-head count `H` because `H_kv = H = 8` (GQA degenerates to MHA at MVP scale per req-11 L211); when true GQA is later enabled (`H_kv < H`), the convention remains `h ∈ 1..H_kv` (the KV-head axis is the gating-relevant axis). Under per-layer head-aggregation, head subscript `h` MUST be elided and symbols MUST collapse to per-layer `C_t^l`, `c_i^l`, `Σ_i^l`, `P_i^l`. Code identifiers MUST map to: `GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding`, `territory_collapse`.

**Source:** `wayfinder/tickets/A1-1.md`, `wayfinder/tickets/A2-2.md`

#### Scenario: Notation is unambiguous
- **WHEN** a formula appears in a spec, design, or doc
- **THEN** the formula uses the locked subscripts (with the `h ∈ 1..H_kv` domain declared per NAR-2) and matches the code-identifier mapping table