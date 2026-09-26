# Spec Delta

## MODIFIED Requirements

### Requirement: Formal Symbols And Code Naming

The system MUST use formal symbol `Σ_i` (per-expert covariance), `P_i = Σ_i^{-1}` (precision matrix), and the subscript convention `(i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S)` for expert / layer / head / token — where the per-head index `h` enumerates the KV-head axis (per req-5 cross-head mean `z̄_t^l = (1/H_kv) · Σ_h C_t^{l,h}`), which at MVP equals the Q-head count `H` because `H_kv = H = 8` (GQA degenerates to MHA at MVP scale per req-11 L211); when true GQA is later enabled (`H_kv < H`), the convention remains `h ∈ 1..H_kv` (the KV-head axis is the gating-relevant axis). Under per-layer head-aggregation, head subscript `h` MUST be elided and symbols MUST collapse to per-layer `C_t^l`, `c_i^l`, `Σ_i^l`, `P_i^l`. Code identifiers MUST map to: `GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding`, `territory_collapse`. **Note:** `territory_seeding` is the canonical API contract name for the Phase 0 K-Means initialization pathway. Its implementation is **deferred to the training-time caller** per req-6 Phase 0 sub-clause; the function exists as a thin contract placeholder that raises `NotImplementedError` with a verbatim pointer to req-6 Phase 0 (see the deferred-contract Requirement anchored below this one). Drivers and inference-time callers MUST NOT invoke this function at inference time.

**Source:** `wayfinder/tickets/A1-1.md`, `wayfinder/tickets/A2-2.md`

#### Scenario: Notation is unambiguous
- **WHEN** a formula appears in a spec, design, or doc
- **THEN** the formula uses the locked subscripts and matches the code-identifier mapping table

### Requirement: C Extraction Differentiability And Centroid Lifecycle

The system MUST compute the extraction in a fully differentiable manner (the D-path, no Straight-Through Estimator). The per-expert territory centroids `c_i^l` MUST evolve through a five-phase dual-channel lifecycle, strictly separating two orthogonal update channels:

**Driver Channel (CentroidDriver, gradient-free)**: responsible for centroid updates under explicit, deterministic rules.
- **Phase 0** — Spherical K-Means seeding (no gradient, no EMA): `c_i^(t+1) = KMeans(C)` initialization. **Phase 0 K-Means implementation is deferred to the training-time caller** (MVP scope per `CLAUDE.md §7 "Out of Scope"` — training execution out-of-scope). The canonical contract name in the codebase is `territory_seeding(C_batch, N_e, *, d_c)` (per req-2 "Formal Symbols And Code Naming" identifier map), which currently raises `NotImplementedError` with a verbatim pointer to this clause. Drivers and inference-time callers MUST NOT call `territory_seeding` at inference time; `CentroidDriver.step` Phase 0 (`Phase.SEEDING`) returns the input centroids detached as a no-op (see `src/decompmoe/extraction.py:119-120`).
- **Phase 1** — Masked Spherical EMA at `α = 0.90` (`c_i^(t+1) = Normalize(0.90·c_i^(t) + 0.10·m_i^(t))`); driver channel Active; this is the "Fast Adapt (Warmup)" stage.
- **Phase 2** — Masked Spherical EMA at `α = 0.95` (`c_i^(t+1) = Normalize(0.95·c_i^(t) + 0.05·m_i^(t))`); driver channel Active; "Coarse Align" stage.
- **Phase 3** — Masked Spherical EMA at `α = 0.99` (`c_i^(t+1) = Normalize(0.99·c_i^(t) + 0.01·m_i^(t))`); driver channel Active; "High-Inertia Annealing (Pre-SGD)" stage.
- **Phase 4** — Projected SGD + L2 re-projection (`c_i^(t+1) = c_i^(t) − η·grad_c_i L_routing`, then `c_i^(t+1) ← c_i^(t+1) / ‖c_i^(t+1)‖₂`); driver channel Active and under gradient descent.

**Gradient Channel (AdamW optimizer)**: governs `c_i.requires_grad` and across-P AdamW registration. Phase 0–3 the gradient channel is **Frozen** (`c_i.requires_grad = False`, `c_i` NOT in AdamW parameter group). Phase 4 the gradient channel is **Active** (`c_i.requires_grad = True`, `c_i` IS in AdamW parameter group). Freezing the gradient channel MUST NOT propagate to the driver channel — Phase 1–3 driver channel remains Active even when the gradient channel is Frozen.

**Empty-Cell Invariant (Invariant 1)**: If for any expert `i` the assigned token count in the current batch `n_i = |T_i| = Σ_t I[i ∈ Top-k(C_t)]` is zero, the per-expert mean MUST default to the previous centroid: `m_i^(t) ≡ c_i^(t−1)`, which yields `c_i^(t+1) = c_i^(t)`. The implementation MUST NOT use `assignment_mask.sum().clamp_min(1e-9)` style normalization; such normalization introduces direction randomization on empty cells and breaks Dead Expert Resurrection.

**Spherical Re-projection Invariant (Invariant 2)**: After every driver-channel update, the centroid MUST satisfy `‖c_i^(t+1)‖₂ ≡ 1.0`. If the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse), the implementation MUST fall back to the previous centroid `c_i^(t+1) = c_i^(t)` to prevent NaN and preserve the geometric boundedness of `logit = β·(C^T c − 1) ∈ [−2β, 0]`.

**Source:** `wayfinder/tickets/A3-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 2)

#### Scenario: No STE in forward or backward
- **WHEN** gradients are back-propagated through the extraction
- **THEN** every step of the pipeline contributes a finite gradient; no surrogate (STE) is inserted between `z` and `C`

#### Scenario: Phase transition updates the centroid driver
- **WHEN** training crosses a phase boundary defined in the schedule
- **THEN** the driver-channel update rule switches (K-Means → EMA 0.90 → EMA 0.95 → EMA 0.99 → Projected SGD) without altering the extraction math; the gradient-channel `requires_grad` flag switches from `False` (Phases 0–3) to `True` (Phase 4) at the Phase 3 → Phase 4 boundary

#### Scenario: Empty-cell preserves centroid
- **WHEN** the driver channel receives a batch with `n_i = 0` for some expert `i`
- **THEN** `c_i^(t+1) == c_i^(t)` element-wise within FP tolerance (no direction randomization, no `.detach()` boundary leak)

#### Scenario: Spherical re-projection holds after every update
- **WHEN** the driver channel completes a step in any Phase
- **THEN** `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, `c_i^(t+1) == c_i^(t)` and no NaN is produced

#### Scenario: Phase 0 K-Means deferred to caller
- **WHEN** `territory_seeding(C_batch, N_e, *, d_c)` is called with `C_batch ∈ (S^{d_c-1})^T` (a batch of unit-sphere points — `‖C_batch[t]‖₂ ≡ 1.0` for all `t ∈ [1, T]`, with `T ≥ N_e`; spherical K-Means mathematical precondition per Phase 0 sub-clause "**Spherical** K-Means"), `N_e ∈ ℕ⁺` (positive integer), and `d_c ∈ ℕ⁺`
- **THEN** it raises `NotImplementedError` whose message contains the verbatim substring `"Phase 0"` and `"deferred to the training-time caller"` (linking back to this Requirement)
- **AND** the error message references spec req-2 (the identifier map) by its anchor string `"req-2"`
- **AND** drivers and inference-time callers MUST NOT invoke this function; `CentroidDriver(Phase.SEEDING).step(centroids, X, mask)` is the canonical no-op contract for the inference-time Phase 0 path

## ADDED Requirements

<a id="req-10"></a>

### Requirement: Territory Seeding Deferred Contract

The canonical API contract name `territory_seeding` (per req-2 "Formal Symbols And Code Naming" identifier map) for the Phase 0 Spherical K-Means initialization pathway `c_i^(t+1) = KMeans(C)` (per req-6 Phase 0 sub-clause) MUST be exposed by the codebase as a public function `territory_seeding(C_batch: Tensor, N_e: int, *, d_c: int) -> Tensor` whose signature **documents** the input batch shape `(T, d_c)` of unit-sphere points `C_batch ∈ (S^{d_c-1})^T` (spherical K-Means mathematical precondition), the per-expert count `N_e`, and the spec-level dimensionality `d_c` (keyword-only). The signature does NOT perform runtime shape or unit-sphere validation in MVP (deferred state); future active implementation MUST add `‖C_batch[t]‖₂ ≡ 1.0` precondition. In the MVP scope (training execution out-of-scope per `CLAUDE.md §7 "Out of Scope"`), the function body is a thin contract placeholder that unconditionally raises `NotImplementedError` with a message containing the verbatim substrings `"Phase 0"`, `"deferred to the training-time caller"`, `"req-2"`, and `"req-6"` so that future callers receive a self-locating error pointing to the deferred contract clauses. The function MUST be exported via `__all__` so `from decompmoe.extraction import territory_seeding` resolves without runtime side effects beyond the raise. Drivers and inference-time callers MUST NOT invoke this function; the canonical Phase 0 inference-time contract is `CentroidDriver(Phase.SEEDING).step(centroids, X, mask)` which returns the input centroids detached (no-op). Subsequent OpenSpec changes that switch `territory_seeding` from deferred to active (implementing the Spherical K-Means algorithm) MUST update this Requirement's body and emit a superseding OpenSpec change that adds a separate Requirement for the active implementation contract — this Requirement remains as the historical anchor for the deferred state.

**Source:** `wayfinder/tickets/A1-1.md`, `wayfinder/tickets/A3-2.md`, change `07-fix-spec-territory-seeding-phase-0` design.md (Decision 1)

#### Scenario: territory_seeding raises NotImplementedError with spec citations
- **WHEN** `territory_seeding(C_batch, N_e, *, d_c)` is called with `C_batch = torch.randn(64, 16)` then `C_batch = C_batch / C_batch.norm(dim=-1, keepdim=True)` (L2-normalized unit-sphere points per spherical K-Means precondition, `T = 64`), `N_e = 16`, and `d_c = 16`
- **THEN** it raises `NotImplementedError` matching the regex `r"Phase 0"`
- **AND** it raises `NotImplementedError` matching the regex `r"deferred to the training-time caller"`
- **AND** it raises `NotImplementedError` matching the regex `r"req-2"`
- **AND** it raises `NotImplementedError` matching the regex `r"req-6"`
- **AND** the function signature `inspect.signature(decompmoe.extraction.territory_seeding)` equals `(C_batch, N_e, *, d_c)` — keyword-only `d_c` enforced
- **AND** the type annotations of the signature match `C_batch: Tensor`, `N_e: int`, `d_c: int`, return `Tensor` (verbatim contract per this Requirement's body)

#### Scenario: territory_seeding is exported via __all__
- **WHEN** the module `decompmoe.extraction` is imported
- **THEN** `"territory_seeding" in decompmoe.extraction.__all__` evaluates to `True` (satisfies req-2 "Formal Symbols And Code Naming" identifier-map MUST-be-in-codebase contract)
- **AND** `from decompmoe.extraction import territory_seeding` resolves without ImportError, returning a callable matching the spec signature `territory_seeding(C_batch: Tensor, N_e: int, *, d_c: int) -> Tensor`