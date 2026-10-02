# Spec Delta — `decompmoe-skeleton`

## MODIFIED Requirements

<a id="req-1"></a>

### Requirement: Canonical Package And Version Identifier

The package SHALL expose `decompmoe.__canonical_name__ == "DecompMoE"`, `decompmoe.__alias__ == "GeoMoE"`, and `decompmoe.__version__` as a `str` matching PEP 440 semantics. The package SHALL expose a stable `__all__` listing every public symbol introduced by this skeleton. **De-duplication rule (normative):** "every public symbol" means the **de-duplicated union** of the `__all__` entries declared by the 13 submodules — a name declared in more than one submodule counts **once**. At MVP that union is exactly **75** names; together with the 3 package dunders (`__version__`, `__canonical_name__`, `__alias__`) the package-level `__all__` therefore has **78** entries. The **only** cross-module name collision at MVP is `flops_per_token`, declared in both `config` and `metrics` (the `metrics` definition is a passthrough wrapper that mirrors `config.flops_per_token`); the package-level `__all__` MUST bind that name to the `config` definition, and the `metrics` definition MUST remain reachable as `decompmoe.metrics.flops_per_token`. **MUST NOT:** summing the 13 per-module counts without de-duplication yields **76** and is not the expected total. The alias SHALL NOT appear as a code identifier anywhere in the package (only in design prose / docstrings).

#### Scenario: Name resolution
- **WHEN** `decompmoe.__canonical_name__` is accessed
- **THEN** it returns the literal string `"DecompMoE"`

#### Scenario: Alias preserved
- **WHEN** `decompmoe.__alias__` is accessed
- **THEN** it returns the literal string `"GeoMoE"` for documentation continuity


<a id="req-7"></a>
### Requirement: C Extraction Four-Step Pipeline

The package SHALL provide `extract_C(K, V, proj_W_K, proj_W_V, proj_b, *, H_kv, d_c, eps=1e-6) -> Tensor` implementing the spec's exact four-step pipeline: (1) per-head projection `z^{l,h} = W_K^{l,h} · k^{l,h} + W_V^{l,h} · v^{l,h} + b^{l,h}`; (2) per-head spherical projection; (3) cross-head mean with `1/H_kv` factor; (4) final spherical projection. The pipeline SHALL be fully differentiable (D-path, no Straight-Through Estimator; no `.detach()` between intermediate tensors).

#### Scenario: Output shape on unit sphere
- **WHEN** `K ∈ R^{B × H_kv × N × d_k}` and `V ∈ R^{B × H_kv × N × d_k}` are fed in
- **THEN** `C ∈ R^{B × N × d_c}` and `‖C_t‖₂ = 1` for every token (within `1e-5`), **provided the degenerate regime is excluded** — i.e. provided every per-head projection `z^{l,h}` satisfies `‖z^{l,h}‖₂ ≥ ε` with `ε = 1e-6` (req-19). This precondition is normative, not a caveat: the pipeline's spherical-projection steps divide by `max(‖·‖₂, ε)`, so a projection in the sub-epsilon regime `0 < ‖z^{l,h}‖₂ < ε` yields `‖C_t‖₂ < 1` rather than 1. This Scenario previously asserted unit norm **unconditionally**, which contradicted this same spec's req-19 Scenario, which states that `0 < ‖z‖₂ < ε` produces a sub-unit norm on first application. The assertion is now conditioned on the same threshold req-19 uses.

#### Scenario: Fully differentiable
- **WHEN** `torch.autograd.gradcheck` is run on `extract_C` with random `K`, `V` and the projection parameters
- **THEN** the gradient check passes with ATOL `1e-5` and no NaN

#### Scenario: Per-token MAC closed form
- **WHEN** the per-token operation count of `extract_C` is computed under the pinned **MAC** convention (1 MAC = 1 multiply + 1 accumulate; FLOPs = 2·MACs)
- **THEN** per-token MACs equal `H_kv · (2 · d_k · d_c + d_c) + H_kv · d_c + H_kv · d_c + d_c` — i.e. (i) per-head K/V/bias projection: `H_kv · (2 · d_k · d_c + d_c)` MACs, (ii) per-head L2-normalization (numerator/denominator ops only; sqrt counts as 0 MAC): `H_kv · d_c` MACs, (iii) cross-head mean with the `1/H_kv` factor (step 3 of the pipeline: a `H_kv`-long accumulation and rescale, i.e. `H_kv` multiply-accumulates over `d_c` values each): `H_kv · d_c` MACs, (iv) final L2-normalization: `d_c` MACs. At MVP (`H_kv=8, d_k=128, d_c=16`) this evaluates to `8·4112 + 8·16 + 8·16 + 16 = 32_896 + 128 + 128 + 16 = 33_168` per-token MACs exactly (within `abs=1`). Tests MUST assert the closed form (or its MVP specialization), NOT a profiler-derived op count.

#### Scenario: Cross-head awareness
- **WHEN** `H_kv = 8` GQA input is processed
- **THEN** the cross-head mean uses the `1/H_kv` factor (mathematical equivalence to a manual `mean(..., dim=1)`)


<a id="req-18"></a>

### Requirement: Centroid Four-Phase Lifecycle Driver — Phase-4 SGD Step Extension

The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask, *, grad=None, eta=1e-2) -> Tensor` method MUST apply, per phase. **`mask` is a REQUIRED positional parameter and MUST NOT be given a default value:** per-expert masked means `m_i` are undefined without it, and a defaulted `mask=None` invites an implementation to substitute a whole-batch mean for `m_i`, which silently broadcasts one mean to every centroid and collapses all territories to a single point. An implementation MUST reject a missing `mask` rather than substitute one.

- Phase 0 (SEEDING): `c_i ← c_i.detach()` (driver is a no-op returning the input centroids detached from the autograd graph); `c_i.requires_grad = False`. Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds. **The caller MUST supply Phase 0 seeds already satisfying `‖c_i‖₂ ≡ 1.0`** — this is a normative obligation on the caller, not a description of the driver's behaviour, and the driver MUST NOT normalise, project, or otherwise repair Phase 0 inputs. This elevation is the deliberate half of a paired correction: `wayfinder` req-23 previously asserted the spherical-norm invariant for "any Phase (including 0 K-Means)" while simultaneously declaring this driver a no-op, giving two peer specs mutually exclusive MUSTs for the same quantity. `wayfinder` req-23 has since been narrowed to **Phase 1–4**; this Requirement is the corresponding owner of the Phase 0 obligation, and the two MUSTs are no longer in conflict.
- Phase 1 (EMA_090): `c_i ← Normalize(0.90 · c_i + 0.10 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 2 (EMA_095): `c_i ← Normalize(0.95 · c_i + 0.05 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 3 (EMA_099): `c_i ← Normalize(0.99 · c_i + 0.01 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 4 (PROJECTED_SGD): When `grad is not None`: `candidate_i = c_i − eta · grad_i`; then `c_i^(t+1) = candidate_i / ‖candidate_i‖₂`. When `grad is None`: `c_i^(t+1) = c_i / ‖c_i‖₂` (L2 retraction of the input only). Both branches apply the Invariant #4 guard pattern: when `‖candidate_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)` (no `clamp_min(ε)` denominator; the same `torch.where(use_old, prev, normalize(...))` pattern used in EMA). Driver Active, gradient channel Active.

The `m_i` is the masked-mean over tokens assigned to expert `i`. The driver MUST enforce the empty-cell invariant: if `n_i = |T_i| = 0`, then `m_i ≡ c_i^(t−1)` (no `clamp_min(ε)` denominator). The driver MUST enforce the spherical re-projection invariant: `‖c_i^(t+1)‖₂ ≡ 1.0` after every step; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)`. The driver MAY call `decompmoe.safeguards.should_resurrect(f_history, current_step, last_resurrection_step, *, N_e, consec=DEAD_EXPERT_CONSEC_STEPS, rate_limit_steps=RESURRECTION_RATE_LIMIT_STEPS, threshold=None) -> set[int]` for dead-expert detection; the function itself lives in `safeguards.py` and is *called* from the driver (the driver MUST NOT define a same-named helper). When `threshold=None` is passed, the implementation derives the effective threshold via the private helper `_dead_expert_threshold(N_e) = 1/(2·N_e)`; at MVP `N_e = 16` this yields `1/32`. The dead-expert rule is parameterized by `N_e`, not hardcoded `1/128`. The constants `DEAD_EXPERT_CONSEC_STEPS = 200` and `RESURRECTION_RATE_LIMIT_STEPS = 1000` are `Final[int]` module-level constants (see `src/decompmoe/safeguards.py:30-31`); the spec references the constant identifiers rather than literal values to ensure the spec stays in lock-step with the code if these constants are retuned.

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold parameterization `1/(2·N_e)`); signature mirrors `src/decompmoe/safeguards.py:71-80` at commit `d3689a1`.

The `step` signature `(*, grad=None, eta=1e-2)` REPLACES the legacy `(centroids, X, mask, eps=1e-6)` contract: the `eps` parameter is removed (no longer used by any active phase); the `grad` keyword is REQUIRED for the projected SGD step (no positional gradient argument); the `eta` keyword defaults to `1e-2` (conservative; spec does not pin a specific value beyond the linear convention); when `grad is None` the P4 branch is the identity L2 retraction (no SGD step applied — this is the backward-compatible fallback for callers that do not provide a gradient). Callers that previously passed `eps=1e-6` will need to remove the kwarg (breaking change; no in-repo callers pass `eps`).

#### Scenario: Phase-4 SGD-1-step closed form

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called with `centroids ∈ R^{N_e × d_c}` (unit-norm rows), `grad ∈ R^{N_e × d_c}` with `‖grad_i‖₂ = 0.05` for all `i`, and `eta = 1e-2`
- **THEN** for every expert `i` where `‖centroids[i] − eta · grad[i]‖₂ ≥ 1e-9`: `c_i^(t+1) == (centroids[i] − eta · grad[i]) / ‖centroids[i] − eta · grad[i]‖₂` within `abs=1e-7` (closed-form SGD step followed by L2 retraction)
- **AND** for every expert `i`: `‖c_i^(t+1)‖₂ == 1.0` within `abs=1e-7` (spherical re-projection invariant holds after the full P4 path, including the SGD step)

#### Scenario: Phase-4 SGD with near-zero candidate falls back to c_i^(t)

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask, grad=grad, eta=eta)` is called and for some expert `i` the post-SGD candidate `‖centroids[i] − eta · grad[i]‖₂ < 1e-9` (e.g. `centroids[i] = +grad[i] / ‖grad[i]‖₂` and `eta · ‖grad[i]‖₂ = 1`)
- **THEN** `c_i^(t+1) == c_i^(t)` element-wise (Invariant #4 fallback applies to the full P4 path, not only to the EMA branches) and no NaN appears in the centroid tensor

#### Scenario: Phase-4 with `grad=None` preserves the legacy L2-retraction semantics

- **WHEN** `CentroidDriver(PROJECTED_SGD).step(centroids, X, mask)` is called with the default `grad=None` and `eta=1e-2`
- **THEN** `c_i^(t+1) == centroids[i] / ‖centroids[i]‖₂` element-wise within `abs=1e-7` (the legacy P4 behavior — L2 retraction of the input — is preserved exactly when no gradient is provided; this is the backward-compatibility contract for callers predating the SGD step addition)

---

