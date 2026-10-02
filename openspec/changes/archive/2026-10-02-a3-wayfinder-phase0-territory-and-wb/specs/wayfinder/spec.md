# Spec Delta — `wayfinder`

## MODIFIED Requirements

<a id="req-2"></a>

### Requirement: Formal Symbols And Code Naming

The system MUST use formal symbol `Σ_i` (per-expert covariance), `P_i = Σ_i^{-1}` (precision matrix), and the subscript convention `(i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S)` for expert / layer / head / token — where the per-head index `h` enumerates the KV-head axis (per req-5 cross-head mean `z̄_t^l = (1/H_kv) · Σ_h C_t^{l,h}`), which at MVP equals the Q-head count `H` because `H_kv = H = 8` (GQA degenerates to MHA at MVP scale per req-11 L211); when true GQA is later enabled (`H_kv < H`), the convention remains `h ∈ 1..H_kv` (the KV-head axis is the gating-relevant axis). Under per-layer head-aggregation, head subscript `h` MUST be elided and symbols MUST collapse to per-layer `C_t^l`, `c_i^l`, `Σ_i^l`, `P_i^l`. Code identifiers MUST map to: `GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding`, `territory_collapse`. **Note:** `territory_seeding` is the canonical API contract name for the Phase 0 K-Means initialization pathway. Its implementation is **deferred to the training-time caller** per req-6 Phase 0 sub-clause; the function exists as a thin contract placeholder that raises `NotImplementedError` with a verbatim pointer to req-6 Phase 0 (see the deferred-contract Requirement anchored below this one). Drivers and inference-time callers MUST NOT invoke this function. **Note:** `territory_collapse` (expert territory collapse detection) is likewise **deferred to the training-time caller** at MVP; it is NOT a MUST-level code identifier at MVP, requires NO placeholder function, and is declared spec-only by the deferred-contract Requirement anchored below this one (see also the source Open Question in archive `2026-09-23-07-fix-spec-territory-seeding-phase-0`).

**Source:** `wayfinder/tickets/A1-1.md`, `wayfinder/tickets/A2-2.md`

#### Scenario: Notation is unambiguous
- **WHEN** a formula appears in a spec, design, or doc
- **THEN** the formula uses the locked subscripts and matches the code-identifier mapping table


<a id="req-15"></a>

### Requirement: Hybrid Three-Layer Phase Triggers

The system MUST combine three trigger layers: (Layer 1) Time-Driven hard cut at the 1 K / 6 K / 26 K / 56 K / 100 K boundaries; (Layer 2) State-Driven Advisory signals — normalized entropy `R_H`, load skew `S_load`, β saturation ratio `R_β-sat`, and overlap index `L_sep / WB` (where `WB = 0.0476` is the natural baseline of the soft orthogonality loss, defined in `wayfinder/tickets/A6b-2.md` L52 and L89–L92 as the per-expert orthogonality baseline that the advisory ratio normalizes against; a ratio `> 2.0` indicates severe centroid clustering / territory overlap). **Deferral note (Layer 2):** the two concrete Layer 2 thresholds `WB = 0.0476` and the `> 2.0` severe-clustering ratio are **advisory-only and unimplemented in the MVP skeleton** — `advisory_signals()` is a pure passthrough that returns its four keyword arguments unchanged, and neither threshold appears as an executable literal in `src/decompmoe/` or `tests/`. The deferral is registered as a hand-off in the change that introduced Layer 2 and recorded in `tests/test_schedule.py::test_advisory_signals_read_only`; it is stated here so the spec body is no longer the only place lacking the annotation) — read-only and advisory only (never auto-trigger a transition); (Layer 3) Hard Cutoff at 100 K steps. Real-time monitoring of `D_c` (per-expert geodesic spread) MUST be excluded;` `D_c` remains an offline metric due to its `O(N_e²)` cost and unstable threshold.

**Source:** `wayfinder/tickets/A6b-2.md`

#### Scenario: Advisory signals not to auto-trigger
- **WHEN** an advisory signal crosses any threshold before its corresponding time-driven boundary
- **THEN** the system logs the advisory but does NOT advance the phase


<a id="req-23"></a>

### Requirement: Spherical Re-Projection And Zero-Vector Invariant

**Phase scope.** The norm invariant of this Requirement is asserted for **Phase 1–4** only (1–3 EMA and 4 Projected SGD). **Phase 0 (K-Means seeding) is explicitly excluded**: its driver is a no-op that returns the input centroids unchanged, so it performs no driver-channel update for this Requirement to constrain, and the `‖c_i‖₂ ≈ 1.0` precondition for Phase 0 is the caller's obligation per `decompmoe-skeleton` req-18. This narrowing resolves a peer-spec contradiction in which this Requirement asserted the invariant for "any Phase (including 0)" while req-18 assigned Phase 0 normalization to the caller against a no-op driver. After every driver-channel update in Phase 1–4, the centroid MUST satisfy `‖c_i^(t+1)‖₂ ≡ 1.0` (within `1e-7` FP tolerance). If the unnormalized candidate `u_i` satisfies `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse from the spherical EMA), the implementation MUST fall back to the previous centroid `c_i^(t+1) = c_i^(t)` to prevent NaN propagation and preserve the geometric boundedness of `logit = β · (C^T c − 1) ∈ [−2β, 0]`. The hard guarantee `‖c_i‖₂ = 1` is required by Req 7 (`d ∈ [0, 2]`, `‖∂logit/∂C‖ ≤ β_max = 32`).

**Source:** `wayfinder/tickets/A3-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: Spherical norm is strictly one in Phase 1-4
- **WHEN** the driver channel completes a step in **Phase 1–4** (1–3 EMA or 4 Projected SGD; Phase 0 K-Means is out of scope for this Requirement — see the Phase scope note above)
- **THEN** `max_i |‖c_i‖₂ − 1.0| < 1e-7` over all experts

#### Scenario: Near-zero candidate falls back
- **WHEN** the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹`
- **THEN** the post-step `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears in the centroid tensor


## ADDED Requirements

<a id="req-38"></a>

### Requirement: Territory Collapse Deferred Contract

The canonical API contract name `territory_collapse` (per req-2 "Formal Symbols And Code Naming" identifier map) denotes the detection of expert territory collapse, i.e. the condition in which two or more centroids `c_i` coincide so that the per-expert covariance sum degenerates. In the MVP scope (training execution out-of-scope per `CLAUDE.md` §7 "Out of Scope"), this identifier's implementation is **deferred to the training-time caller** and the codebase MUST NOT be required to expose a `territory_collapse` symbol. Unlike `territory_seeding` (see the deferred-contract Requirement anchored below req-2), this contract is **specification-only**: no placeholder function is mandated, because the MVP has no closed form for the collapse statistic and a placeholder would assert a signature whose semantics are not derived. `req-2`'s identifier map therefore lists `territory_collapse` as a **deferred, non-MUST-at-MVP** name rather than a MUST-level code identifier, which resolves the dangling-MUST gap where the name appeared in the spec but neither in `src/` nor in `tests/`. Drivers and inference-time callers MUST NOT reference `territory_collapse` at MVP. A subsequent OpenSpec change that activates it MUST first derive the collapse statistic's closed form, then update this Requirement's body and emit a superseding change adding the implementation contract — this Requirement remains as the historical anchor for the deferred state.

**Source:** `wayfinder/tickets/A1-1.md`

#### Scenario: territory_collapse is spec-only at MVP
- **WHEN** the `wayfinder` req-2 identifier map is compared against the codebase surface (`src/decompmoe/*.py` and `tests/*.py`)
- **THEN** the six MUST-level identifiers `GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding` each resolve to at least one definition or reference, while `territory_collapse` is declared deferred by this Requirement and is **not** required to resolve
- **AND** this absence is recorded in the spec rather than being an undocumented gap

#### Scenario: lineage is traceable
- **WHEN** the provenance of the `territory_collapse` identifier is traced
- **THEN** `wayfinder/tickets/A1-1.md` contains the identifier in its symbol-naming mapping table, and A1-1 is already the `req-2` Source back-link — i.e. the deferral is anchored to real ticket lineage, not to an invented reference
