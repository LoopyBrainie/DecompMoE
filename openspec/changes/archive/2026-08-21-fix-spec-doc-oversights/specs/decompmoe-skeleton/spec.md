## MODIFIED Requirements

### Requirement: Active FLOPs Parity Against Dense Baseline

The package SHALL provide `flops_per_token(cfg, arch) -> int` whose canonical per-token active-FLOPs formula is symmetric across MoE and Dense sides:
- **MoE** (per token, per layer): `FLOPs_MoE,core^(l) = 8 · d_model² + k · 6 · d_model · d_ffn^Expert` (attention Q/K/V/O + top-k SwiGLU expert FFNs).
- **Dense** (per token, per layer): `FLOPs_Dense,core^(l) = 8 · d_model² + 6 · d_model · d_ffn^Dense`.

The parity constraint `d_ffn^Dense ≡ k · d_ffn^Expert` MUST hold; at MVP this evaluates to `4096 = 2 · 2048` (exact 1:1). Explicit exclusions (symmetric on both sides, NOT in parity accounting): Attention `Q K^T` and `Attn · V` (sequence-length-dependent), and the output `lm_head`. Routing overhead is reported separately as `FLOPs_Routing^(l) = 4 · d_c · H_kv · d_k + 2 · N_e · d_c` (≈ 66_048 FLOPs/layer at MVP, ≈ 0.20% of active-core), within the `0.3%` allowance; it MUST NOT enter parity. (The previous figure `0.26%` was arithmetically inconsistent with the active-core definition in this paragraph; the corrected figure `0.20%` is `66_048 / 33_554_432 ≈ 0.001968`.)

#### Scenario: MoE vs dense 1:1
- **WHEN** `flops_per_token(cfg, MOE_MVP)` is compared to `flops_per_token(cfg, DENSE_4096)`
- **THEN** the two active-core values are equal (exact parity); routing overhead is reported as a separate line item

---

### Requirement: Centroid Four-Phase Lifecycle Driver

The package SHALL provide `CentroidDriver(phase: Phase) -> CentroidDriver` with `Phase ∈ {SEEDING=0, EMA_090=1, EMA_095=2, EMA_099=3, PROJECTED_SGD=4}`. The `step(centroids, X, mask) -> Tensor` method MUST apply, per phase:

- Phase 0 (SEEDING): `c_i ← c_i.detach()` (driver is a no-op returning the input centroids detached from the autograd graph); `c_i.requires_grad = False`. Driver is no-op; upstream spherical KMeans is assumed to have produced L2-normalized seeds (the `‖c_i‖₂ ≡ 1.0` invariant for Phase 0 is the caller's responsibility, not the driver's).
- Phase 1 (EMA_090): `c_i ← Normalize(0.90 · c_i + 0.10 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 2 (EMA_095): `c_i ← Normalize(0.95 · c_i + 0.05 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 3 (EMA_099): `c_i ← Normalize(0.99 · c_i + 0.01 · m_i) / ‖·‖₂`, driver Active, gradient channel Frozen.
- Phase 4 (PROJECTED_SGD): `c_i ← (c_i − η · ∇_{c_i} L_routing) / ‖·‖₂`, driver Active, gradient channel Active.

The `m_i` is the masked-mean over tokens assigned to expert `i`. The driver MUST enforce the empty-cell invariant: if `n_i = |T_i| = 0`, then `m_i ≡ c_i^(t−1)` (no `clamp_min(ε)` denominator). The driver MUST enforce the spherical re-projection invariant: `‖c_i^(t+1)‖₂ ≡ 1.0` after every step; on near-zero candidate `‖u_i‖₂ < 10⁻⁹`, fall back to `c_i^(t)`. The driver SHALL expose a `should_resurrect(f_per_expert, window_size, last_resurrection_step, current_step, *, threshold=1/(2·N_e), consec=200) -> set[int]` helper that flags expert indices whose mask-fraction `f_i` was below `1/(2·N_e)` for `200` consecutive steps (rate-limited to once per `1000`-step window). At MVP `N_e = 16`, `1/(2·N_e) = 1/32`; the rule is parameterized by `N_e`, not a hardcoded `1/128`.

#### Scenario: Phase-0 non-differentiable
- **WHEN** `CentroidDriver(SEEDING).step(...)` is called
- **THEN** no gradient is registered on the input `centroids` (`requires_grad` not propagated) and the output equals the input `centroids` element-wise

#### Scenario: Phase-1 EMA coefficient
- **WHEN** `CentroidDriver(EMA_090).step(centroids, X, mask)` is called with `n_i > 0` for all experts
- **THEN** `step` returns `Normalize(0.90 · centroids + 0.10 · masked_mean(X)) / ‖·‖₂` (within FP tolerance, post-normalization)

#### Scenario: Phase-4 re-projection
- **WHEN** `CentroidDriver(PROJECTED_SGD).step(...)` is called
- **THEN** the output `centroids` satisfy `‖c_i‖₂ = 1.0` within `1e-7` after retraction

#### Scenario: Phase-1 driver Active despite gradient Frozen
- **WHEN** `CentroidDriver(EMA_090).step(...)` is called and the gradient channel is Frozen for `c_i`
- **THEN** the driver still updates `c_i` per the EMA rule; `c_i.requires_grad` remains `False`; `c_i` is NOT in the AdamW parameter group

---

### Requirement: Hard-Constraint Grep Invariants

The package SHALL satisfy the following source-level invariants, asserted by **literal-token grep tests** (any invariant requiring data-flow / semantic analysis is NOT a grep invariant; see Requirement "Centroid Driver Semantic Invariants" for the semantic layer):
- NO occurrence of `StraightThroughEstimator` or `straight_through` in `src/decompmoe/`
- NO occurrence of `w_i` in the body of `distance.logit` (signature-level invariant already covered)
- NO occurrence of `shared` attribute in `ExpertPool`
- NO import of `torch.utils.cpp_extension` or `triton` in `experts.py`
- NO field `kv_cache_c` in `GeometricRouter` Protocol

(The two previously-listed invariants — `.clamp_min(ε)` empty-cell denominator and the literal `arctan(pi / sqrt(d_c))` token — are removed from this Requirement because they cannot be verified by literal grep alone: the former requires data-flow analysis (the `.clamp_min` call result must be checked to be a denominator), and the latter can be circumvented by a syntactically different but semantically equivalent expression. Both invariants are restated under Requirement "Centroid Driver Semantic Invariants" where they are enforced by the corresponding named test scenario.)

#### Scenario: Hard constraints hold
- **WHEN** the literal-token grep invariants above are evaluated against `src/decompmoe/`
- **THEN** all invariants pass

---

## ADDED Requirements

### Requirement: Centroid Driver Semantic Invariants

The package's `CentroidDriver` SHALL enforce three semantic invariants that **cannot be verified by literal-token grep alone** (data-flow analysis, runtime observation, and arithmetic comparison are required). These are the **semantic counterpart** to Requirement "Hard-Constraint Grep Invariants":

1. **Empty-cell fallback (formerly grep bullet 6)**: `CentroidDriver.step(centroids, X, mask)` with `n_i = |T_i| = 0` MUST preserve `c_i^(t+1) == c_i^(t)` element-wise (no direction randomization). The driver MUST NOT use `.clamp_min(ε)` as a denominator in the empty-cell branch. Verified by `test_empty_cell_preserves_centroid` (see Requirement "Centroid Driver Invariant Test Scenarios").

2. **Spherical re-projection (driver output invariant)**: After every `CentroidDriver.step(...)` call across all four active phases, `max_i |‖c_i‖₂ − 1.0| < 10⁻⁷`. Verified by `test_spherical_norm_is_strictly_one` (see Requirement "Centroid Driver Invariant Test Scenarios").

3. **Near-zero candidate fallback**: When the unnormalized candidate `u_i` has `‖u_i‖₂ < 10⁻⁹` (degenerate isotropic collapse), `c_i^(t+1) == c_i^(t)` element-wise and no NaN appears. Verified by `test_near_zero_candidate_fallback` (see Requirement "Centroid Driver Invariant Test Scenarios").

(Removed from the grep layer: the literal-token restriction `arctan(pi / sqrt(d_c))` is now enforced implicitly by the canonical Voronoi closed form contract in Requirement "Voronoi Self-Consistency Threshold"; grep-equivalent restrictions on the closed-form API name are added there if a future change requires them.)

#### Scenario: Semantic invariants are enforced by the named test scenarios
- **WHEN** the three named test scenarios (`test_empty_cell_preserves_centroid`, `test_spherical_norm_is_strictly_one`, `test_near_zero_candidate_fallback`) all pass
- **THEN** the empty-cell fallback, spherical re-projection, and near-zero candidate fallback invariants hold for `CentroidDriver`
