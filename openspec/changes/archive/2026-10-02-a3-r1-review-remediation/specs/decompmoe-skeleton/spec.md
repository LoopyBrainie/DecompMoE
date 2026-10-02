# Spec Delta — `decompmoe-skeleton`

## MODIFIED Requirements

<a id="req-7"></a>
### Requirement: C Extraction Four-Step Pipeline

The package SHALL provide `extract_C(K, V, proj_W_K, proj_W_V, proj_b, *, H_kv, d_c, eps=1e-6) -> Tensor` implementing the spec's exact four-step pipeline: (1) per-head projection `z^{l,h} = W_K^{l,h} · k^{l,h} + W_V^{l,h} · v^{l,h} + b^{l,h}`; (2) per-head spherical projection; (3) cross-head mean with `1/H_kv` factor; (4) final spherical projection. The pipeline SHALL be fully differentiable (D-path, no Straight-Through Estimator; no `.detach()` between intermediate tensors).

#### Scenario: Output shape on unit sphere
- **WHEN** `K ∈ R^{B × H_kv × N × d_k}` and `V ∈ R^{B × H_kv × N × d_k}` are fed in
- **THEN** `C ∈ R^{B × N × d_c}` and `‖C_t‖₂ = 1` for every token (within `1e-5`), **provided the degenerate regime is excluded** — i.e. provided the **cross-head mean** `z̄_t^l = (1/H_kv) · Σ_h ẑ^{l,h}` satisfies `‖z̄_t^l‖₂ ≥ ε` with `ε = 1e-6` (req-19). This precondition is normative, not a caveat, and it MUST be stated on the **mean** rather than on the per-head terms: step 4 divides by `max(‖z̄‖₂, ε)`, so the quantity that decides the output norm is `‖z̄‖₂`, not any individual `‖z^{l,h}‖₂`. Conditioning on the per-head norms is **insufficient** — at `H_kv = 8` with four heads projecting to `+e₀` and four to `−e₀` (all `‖z^{l,h}‖₂ = 1.0`, so the per-head form of this precondition is satisfied) the mean is exactly `0` and `extract_C` returns `‖C_t‖₂ = 0.0`, violating this Scenario's own `‖C_t‖₂ = 1` bound. The per-head sub-epsilon regime `0 < ‖z^{l,h}‖₂ < ε` named in req-19 remains a separate, sufficient-to-violate case, and is subsumed by the mean form. This Scenario previously asserted unit norm **unconditionally**, which contradicted req-19; an earlier revision of this same correction conditioned on the per-head norms and was still falsifiable, which is why the condition is now on `z̄`.

#### Scenario: Fully differentiable
- **WHEN** `torch.autograd.gradcheck` is run on `extract_C` with random `K`, `V` and the projection parameters
- **THEN** the gradient check passes with ATOL `1e-5` and no NaN

#### Scenario: Per-token MAC closed form
- **WHEN** the per-token operation count of `extract_C` is computed under the pinned **MAC** convention (1 MAC = 1 multiply + 1 accumulate; FLOPs = 2·MACs)
- **THEN** per-token MACs equal `H_kv · (2 · d_k · d_c + d_c) + H_kv · d_c + H_kv · d_c + d_c` — i.e. (i) per-head K/V/bias projection: `H_kv · (2 · d_k · d_c + d_c)` MACs, (ii) per-head L2-normalization (numerator/denominator ops only; sqrt counts as 0 MAC): `H_kv · d_c` MACs, (iii) cross-head mean with the `1/H_kv` factor (step 3 of the pipeline: a `H_kv`-long accumulation and rescale, i.e. `H_kv` multiply-accumulates over `d_c` values each): `H_kv · d_c` MACs, (iv) final L2-normalization: `d_c` MACs. At MVP (`H_kv=8, d_k=128, d_c=16`) this evaluates to `8·4112 + 8·16 + 8·16 + 16 = 32_896 + 128 + 128 + 16 = 33_168` per-token MACs exactly (within `abs=1`). Tests MUST assert the closed form (or its MVP specialization), NOT a profiler-derived op count.

#### Scenario: Cross-head awareness
- **WHEN** `H_kv = 8` GQA input is processed
- **THEN** the cross-head mean uses the `1/H_kv` factor (mathematical equivalence to a manual `mean(..., dim=1)`)
