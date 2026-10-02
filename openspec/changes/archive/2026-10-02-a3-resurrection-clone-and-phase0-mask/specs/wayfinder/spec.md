# Spec Delta — `wayfinder`

## MODIFIED Requirements

<a id="req-32"></a>

### Requirement: Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper

The Dead Expert Splitting Resurrection pathway (Req 13) MUST perturb the **single cloned expert** (centroid and/or expert weights) — not the per-expert routing frequency vector `f_per_expert`. The perturbation API `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)` MUST accept `f_per_expert` as the leading positional argument with **shape `(..., N_e)`** — the trailing axis MUST equal `N_e` and leading dims are arbitrary (canonical call sites pass `(N_e,)`, `(T, N_e)`, or `(B, N, N_e)`). Layer 2 shape enforcement (wrapper-side, at this wrapper): `f_per_expert.shape[-1] == cfg.N_e` pair-check. The vacuous self-check `f_per_expert.shape[-1] == β_per_expert.shape[0]` (which is identically true given `f_per_expert = β_per_expert.detach()` inside this wrapper, where `shape[-1] == shape[0]`) was an earlier draft and was corrected by commit `0b2202e` to anchor on the spec-defined `cfg.N_e`. Layer 1 primitive-side enforcement (`ndim ≥ 1`) is described in Req 28. `target_idx` is a positional integer, `eps_std=0.05` is a positional-or-keyword perturbation scale, and `dim` is a **keyword-only** parameter sourcing the per-expert dimensionality. `dim=None` MUST raise `TypeError`. The returned tensor MUST have leading dimension `dim` — corresponding to a single expert slot — NOT the `(N_e,)` shape of `f_per_expert`. The β double-write semantic (`β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`) is defined in Req 13; this wrapper additionally guarantees same-call-stack execution (see wrapper contract paragraph below). (References Req 13.)

**The canonical single-event API is `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg) -> tuple[Tensor, Tensor]`** which returns `(c_perturbed, β_per_expert_new)` and guarantees that the centroid perturbation and the β double-write happen in the **same Python call stack** — no `yield` / `await` / background-task scheduling between the two operations. Callers MUST use `resurrect_expert` for the resurrection pathway; the two primitives `resurrection_perturb_distribution` and `apply_resurrection_beta_decay` remain available for low-level composition but their separate invocation does NOT satisfy the "same resurrection event" contract above. The wrapper signature takes `cfg: MVPConfig` so the per-expert dimensionality `cfg.d_c` is sourced from the canonical config rather than re-derived from `β_per_expert.shape` (which would conflate centroid dimension with the `N_e` routing dimension — the very bug the per-expert contract exists to prevent). It additionally takes `c_centroids: Tensor` of shape `(N_e, d_c)` as a **required per-call argument**, because Req 28's "perturb the single cloned expert" is unsatisfiable without it: neither `MVPConfig` nor `β_per_expert` carries a centroid, and a per-call parameter is the correct home for it because the donor differs on every resurrection event, whereas `MVPConfig` is a frozen configuration singleton. **The clone source is row `j_star` (the donor), not row `i`** — `i` is the dead expert whose own centroid is exactly the degenerate quantity the resurrection exists to replace, and this matches the β double-write, which likewise reads its pre-write value from `β_per_expert[j_star]`. A wrapper that cloned row `i` would be a no-op dressed as a resurrection.

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-math-consistency-audit-2026-08` design.md (Decision 4 — per-expert perturbation contract); signature mirrors the `resurrect_expert` function in `src/decompmoe/safeguards.py` at commit `263ac19 feat(safeguards): per-expert resurrection perturb shape + same-event beta decay` (Layer 2 wrapper-side anchor `cfg.N_e` per commit `0b2202e fix(safeguards): replace vacuous β-length self-check with cfg.N_e meaningful guard` at the `cfg.N_e` guard inside `resurrect_expert`)

#### Scenario: perturbation accepts 1-D (N_e,) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (N_e,)` (e.g. `(16,)` at MVP)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation accepts batched (B, N, N_e) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (B, N, N_e)` (e.g. `(4, 3, 16)` at MVP — matches `loss.L_lb` hot-path shape per `src/decompmoe/loss.py:88`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation accepts history-stacked (T, ..., N_e) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (T, ..., N_e)` (e.g. `(100, N_e)` history stacked by `metrics.UR` per `src/decompmoe/metrics.py:83`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation rejects 0-D scalar f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert=(), target_idx=3, dim=16)` is called with `f_per_expert.ndim == 0`
- **THEN** the primitive raises `ValueError` (Layer 1 guard: ndim ≥ 1)

#### Scenario: wrapper pair-checks f_per_expert trailing axis vs cfg.N_e
- **WHEN** `resurrect_expert(i=3, j_star=0, β_per_expert, cfg)` is called with `β_per_expert.detach()` (the wrapper's internal `f_per_expert = β_per_expert.detach()`) whose trailing axis length `!= cfg.N_e` (the canonical N_e sourced from `cfg.MVPConfig`, **NOT** `β_per_expert.shape[0]` — the latter would be a vacuous self-check given `f_per_expert = β_per_expert.detach()`, where `shape[-1] == shape[0]` identically)
- **THEN** the wrapper raises `ValueError` (Layer 2 guard: trailing-axis = N_e pair-check, anchored on `cfg.N_e`)

#### Scenario: same-event beta decay
- **WHEN** `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg)` is called with any valid `MVPConfig cfg` and a `c_centroids` of shape `(N_e, d_c)` with unit-norm rows, valid expert indices `i` and `j_star` (`0 ≤ i, j_star < N_e`, `i ≠ j_star`), and a valid `β_per_expert ∈ R^{N_e}` (positive finite values)
- **THEN** the returned `c_perturbed` is `L2Normalize(c_centroids[j_star] + ε)` where `ε` is the output of `resurrection_perturb_distribution(β_per_expert.detach(), j_star, eps_std=0.05, dim=cfg.d_c)`, and the returned `β_per_expert_new` is the output of `apply_resurrection_beta_decay(β_per_expert, j_star, i)`, with both calls executed in the **same call stack** (no `await` / `yield` / `spawn` between them — verifiable by inspecting the wrapper's linear code path which is a synchronous function composition)
- **AND** `β_per_expert_new[i] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (donor value is read from `β_per_expert[j_star]` BEFORE either write, per the immutability clause; this matches the canonical pattern in `apply_resurrection_beta_decay`)
- **AND** `β_per_expert_new[j_star] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (the donor's own β is also decayed by the same factor)
- **AND** `c_perturbed.shape == (cfg.d_c,)` (single-expert slot shape, consistent with the perturbation output shape scenario above)
- **AND** `‖c_perturbed‖₂ == 1.0` within `abs=1e-6` — the resurrection MUST return a point on the unit sphere `S^{d_c−1}`. This is the invariant the bare-ε behaviour broke: `ε ~ N(0, eps_std²·I)` has `E‖ε‖₂ ≈ eps_std·sqrt(d_c) ≈ 0.2` at `d_c = 16, eps_std = 0.05`, so assigning it to `c_i` violated the sphere constraint before any other invariant could be checked. This is a **float** closed form and MUST be pinned with `pytest.approx(1.0, abs=1e-6)`, never with a bare `==`
- **AND** `cos(c_perturbed, c_centroids[j_star]) > 0` — the returned point is a perturbation **of the donor**, not an independent random direction. Measured over 200 000 samples at `d_c = 16, eps_std = 0.05` the mean cosine is `0.981666` and the mean angle `10.8054°`; the bare-ε behaviour gave `−0.000289` and `90.0177°`, i.e. an 8.33× angle gap and a vector that was orthogonal to the donor
- **AND** `β_per_expert_new is not β_per_expert` (immutability: the input tensor is never mutated in-place; `apply_resurrection_beta_decay` clones internally)

#### Scenario: clone source is the donor row, not the dead expert
- **WHEN** `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg)` is called with `i != j_star` and `c_centroids` of shape `(N_e, d_c)` with unit-norm rows
- **THEN** the clone is taken from `c_centroids[j_star]` (the donor) and NOT from `c_centroids[i]`; with `eps_std → 0` the returned `c_perturbed` converges to `c_centroids[j_star]`
- **AND** an implementation that cloned row `i` MUST be rejected: `i` is the dead expert, so its centroid is the degenerate quantity the resurrection is meant to replace, and cloning it would return a perturbed copy of the very state being repaired

