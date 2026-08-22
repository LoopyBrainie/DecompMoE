# Proposal — `fix-math-consistency-audit-2026-08`

## Why

Mathematical audit of `LoopyBrainie/DecompMoE @ dev (d3a71c4)` on 2026-08-22 found **7 Blocker + 6 Major** discrepancies in the spec × code × pytest triangle. Spec is internally inconsistent (`wayfinder/spec.md:188-190` lists Voronoi MVP table values that fail its own equation by 14.7× / 38000×), code deviates from spec formalization (FLOPs misses SwiGLU's third projection; β operational domain unimplemented; 4 of 8 metrics are `torch.tensor(0.0)` placeholders; `ExpertPool` not `nn.Module`), and 8 pytest tests are tautological (assert `SUT ≡ reimplementation of SUT`, hard-code implementation constants, or use loose bounds that pass under wrong formulas). 95/95 tests pass — under spec/code drift — because the green tests do not exercise the spec.

This change revises the **spec** to be self-consistent and to declare closed-form invariants for every testable formula. Code/test rewrites are explicitly handed off to a downstream `fix-math-consistency-audit-2026-08-apply` change (mirrors the `fix-openspec-doc-bugs` → `fix-openspec-doc-bugs-apply` precedent).

## What Changes

- **B1** — wayfinder Req 11 Voronoi table: replace `θ(16,16) ≈ 52.00° (0.9076 rad)` / `θ(64,16) ≈ 25.45° (0.4494 rad)` with the spec's own equation's root `θ(16,16) ≈ 67.24° (1.1736 rad)` / `θ(64,16) ≈ 58.47° (1.0205 rad)`; replace `r(16,16) ≈ 0.380` / `r(64,16) ≈ 0.0971` with `0.6127 / 0.4776`; replace the unique-θ domain `(0, π)` with `(0, π/2]` (the equation is symmetric about `π/2`; the half-cap interpretation requires `θ ≤ π/2`). The 52° figure is an *unverified estimate* from `A5-3.md:62-67` ("16 个点在 S^15 上的等距划分上界") and is not a separately defined concept; no dual-definition is preserved.
- **B2 / B3** — skeleton spec's `Voronoi Self-Consistency Threshold` Requirement: replace the ≈ 52.00° / ≈ 25.45° Scenario expected values with the equation's actual roots; add a residual Scenario asserting `|½ · I_{sin²θ}((d_c − 1)/2, 1/2) − 1/N_e| < 1e-9` after substitution. The hard-coded `_VORONOI_MVP_TABLE` in `src/decompmoe/sphere.py` is handed off to apply.
- **B4 / B5** — skeleton spec's `Active FLOPs Parity Against Dense Baseline`: add absolute-value Scenarios pinning `33_554_432` per-layer and `134_217_728` total (`L = 4`); parity becomes a derived assertion. Formula text already correct (`k·6·d_model·d_ffn^Expert`); code `2·2 = 4` coefficient is handed off to apply.
- **B6** — strengthen wayfinder Req 7 Invariant 3 and Req 24 with the worked numerical example `γ'(β_{p3}=16.0) = ln(15/16) ≈ −0.0645` and the closed-form `β^eff(Phase 4, t=0) ≡ 16.0` (continuity at Phase 3 → 4 boundary). Spec text already contains the formula; the implementation (`beta_effective`, `gamma_reset_for_phase4` in `schedule.py`) is handed off to apply.
- **B7** — wayfinder Req 20 **MODIFIED** with corrected MCI formula + 8 closed-form Scenarios (original spec had `(1/d_c) · Σ 1/λ̃²` which is mathematically inconsistent with the declared `(1/d_c, 1]` range; corrected to `1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)` with `λ_j` the eigenvalues of the **uncentered** second moment `M = (1/|T|) · Σ_t C_t C_tᵀ` of the routed-token signature set). The Scenarios pin: `SP(orthonormal-aligned) = 1.0` (with precondition `C_t = c_{a(t)}`); `SP(60° offset) = 0.5`; `SP ∈ [-1, 1]` (cosine kernel range); `D_chord(orthonormal basis) = √2`; `MCI(token signatures covering orthonormal basis equally) = 1.0` exact; `MCI(rank-1 token distribution) = 1/d_c` exact; `CG(zero gradient) = 0.0` exact; `CG(2·g) = 2·CG(g)` (positive homogeneity). The placeholder `torch.tensor(0.0)` returns in `metrics.py` are handed off to apply.
- **M1** — wayfinder Req 14 already specifies `β_max(t) ∈ [1.0, 4.0]` for Phase 2; add a Scenario asserting `phase_beta_box(2) == (1.0, 4.0)`. Code `phase_beta_box(2)` falls through to default in `schedule.py` and is handed off to apply.
- **M2** — skeleton spec's `Standard SwiGLU Expert With No Shared Branch`: add a Scenario asserting `ExpertPool(MVPConfig())` is an `nn.Module`, exposes `nn.ModuleList`, and `sum(p.numel() for p in pool.parameters()) == N_e · 3 · d_model · d_ffn == 100_663_296` exactly. Code `class ExpertPool:` (plain object) is handed off to apply.
- **M3** — skeleton spec's `Centroid Driver Semantic Invariants`: extend the **Near-zero candidate fallback** invariant to cover all active phases (the current wording covers EMA; Phase 4 `PROJECTED_SGD` currently has `centroids / ‖centroids‖.clamp_min(eps)` with no `torch.where(prev, ...)` guard). Add a `test_near_zero_candidate_fallback_phase4` Scenario. Code fix in `extraction.py` is handed off to apply.
- **M4** — wayfinder Req 13 already specifies the resurrection semantics (`β_i ← 0.85·β_{j*}`, perturb clone with `N(0, 0.05² I)`); the actual code in `safeguards.resurrection_perturb_distribution` ignores `target_idx` and returns a whole-vector `randn_like`. Strengthen the spec Scenario with an explicit per-expert-shape assertion on the perturbation contract. Apply phase corrects `safeguards.py`.
- **M5** — add spec-level closed-form Scenarios pinning the constants that the tautological tests should assert (orthogonal basis → `L_sep == 0`; uniform `f = P = 1/N_e` → `L_lb_raw == 1`; `λ(41_000) ≈ 5e-4`; worst-case gradient bounds; forward-formula numerical verification; total params `452_329_984`, active `100_008_448`). Apply phase rewrites the 8 tests.
- **M6** — wayfinder Req 24's `γ_init ≈ −3.5` example currently produces `β_0 ≈ 1.035`, but skeleton `MVPConfig.beta_initial = 1.0` does not match. Decision: **update `beta_initial = 1.0` text in skeleton spec to read `beta_initial == 1.0` as a deliberate floor (the operational-domain floor matches)** and add a closed-form Scenario asserting `β_min == 0.1` for the parameterization space and `β^eff == 1.0` for the Phase-1 operational domain — i.e. the two domains are intentionally decoupled. No spec/code contradiction remains.

## Capabilities

### New Capabilities

None. No new capability paths; the change is entirely within the existing two capabilities.

### Modified Capabilities

- `wayfinder`: Voronoi table values + domain (Req 11); new closed-form Scenarios for `γ'` reset worked example (Req 7 Invariant 3), Phase 2 β box (Req 14), resurrection perturbation contract (Req 13), offline metrics invariants (Req 20), `β^eff(Phase 4, t=0) ≡ 16.0` continuity (Req 24). Net: 1 MODIFIED Requirement (Req 11) + multiple ADDED Scenarios across Reqs 7 / 13 / 14 / 20 / 24.
- `decompmoe-skeleton`: Voronoi closed-form contract + residual Scenario; ExpertPool `nn.Module` + 100_663_296 param count Scenario; Phase 4 near-zero fallback Scenario; `β^eff` and `L_sep` / `L_lb` / `λ(t)` closed-form Scenarios; FLOPs absolute-value Scenarios; param count exact equality Scenarios. Net: 4 MODIFIED Requirements (Voronoi, FLOPs, SwiGLU Expert, Loss Composition) + 1 MODIFIED (Total And Active Parameter Estimator) + multiple ADDED Scenarios.

## Impact

**Spec layer** (this change): `openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` and `openspec/changes/fix-math-consistency-audit-2026-08/specs/decompmoe-skeleton/spec.md`. After archive, the merged specs contain the corrected Voronoi table, explicit closed-form invariants, and the ExpertPool `nn.Module` contract.

**Code layer** (downstream — explicitly out of scope for this change, handed off to `fix-math-consistency-audit-2026-08-apply`):
- `src/decompmoe/sphere.py` — delete `_VORONOI_MVP_TABLE` and the table-hit branch (`canonical_voronoi_angle(16,16)` must bisect like every other input).
- `src/decompmoe/config.py` — fix FFN coefficient from `2 * 2` to `3 * 2` (note: attention term `4 * 2 * d²` at lines 121/132 is correct for Q/K/V/O; only FFN is wrong).
- `src/decompmoe/schedule.py` — implement `beta_effective(gamma, phase, step)` and `gamma_reset_for_phase4(beta_p3)`; fix `phase_beta_box(2)` to return `(1.0, 4.0)`.
- `src/decompmoe/metrics.py` — replace `return torch.tensor(0.0)` stubs in `SP`, `D_c` (rename to `D_chord`), `MCI`, `CG` with closed-form implementations; **MCI MUST use `1 / (d_c · Σλ̃²)`** with `λ̃` from the **uncentered** second moment `M = (1/|T|) · Σ_t C_t C_tᵀ` of routed-token signatures (NOT `(1/d_c) · Σ 1/λ̃²` which is mathematically inconsistent with the declared range, NOT centered `Cov` whose upper endpoint is unreachable at `|T| = d_c`); **MCI takes `token_signatures` as input** (NOT `c_centroids` — MCI measures spread of routed-token distribution, not of centroid positions); **CG** MUST satisfy zero-grad invariance + positive homogeneity; **SP** MUST aggregate as `mean({SP_i : ‖T_i‖₁ > 0})` (skip empty experts, do NOT report 0); align `metrics.OFFLINE = frozenset({"SP", "D_chord", "MCI", "CG"})`.
- `src/decompmoe/experts.py` — `class ExpertPool(nn.Module):` + `self.experts = nn.ModuleList([...])`.
- `src/decompmoe/extraction.py` — Phase 4 step applies `torch.where(‖c‖ < 1e-9, prev_c, normalize(c))` like EMA branch.
- `src/decompmoe/safeguards.py` — `resurrection_perturb_distribution(f, target_idx, eps_std)` returns per-expert-shape perturbation; add `β_i ← 0.85·β_{j*}` mutation in the resurrection flow.
- `src/decompmoe/beta.py` — add `phase4_inverse_temperature(gamma_p) = 1 + 31 · torch.sigmoid(gamma_p)`.

**Test layer** (downstream — 8 tautological tests rewritten + ~6 new tests):
- `tests/test_loss.py` — `test_sep_formula`, `test_load_balance_alpha_fixed`, `test_lambda_cosine_ramp_phase_3`.
- `tests/test_beta.py` — `test_grad_C_bound`, `test_grad_gamma_bound`.
- `tests/test_extraction.py` — `test_complexity_budget`.
- `tests/test_gating.py` — `test_forward_formula_strictness`.
- `tests/test_config.py` — `test_total_param_estimate`.
- New tests for `expert_pool_param_count`, `phase_4_near_zero_fallback`, `phase_beta_box_phase2`, `beta_effective_phase_4_continuity`.

## Downstream Hand-off（不在本 change 范围）

All code/test edits above are handed off to a future `fix-math-consistency-audit-2026-08-apply` change (mirrors `fix-openspec-doc-bugs` → `fix-openspec-doc-bugs-apply`). The apply change's `tasks.md` will list these as `~~(已移交下游)~~` strike-through prefix entries; its `proposal.md` will declare `Modified Capabilities: 无` (no spec changes) and reference this change as the source of truth.

The post-archive independent self-consistency check (CLAUDE.md §3) is the apply change's responsibility: for each Req carrying a concrete number, manually substitute into the equation by hand and compare to spec claim — catches any future B1/B4/B6/B7-style regressions at archive time.

## Out of Scope（明确不动）

- **m1** — `nan_ladder` action name `halve_lr` (rename to `decay_lr` to match the actual `÷10` coefficient): purely cosmetic naming; deferred to a future change if needed.
- **m2** — `spherical_l2_normalize` `eps`-denominator bias: produces `‖z‖/(‖z‖+eps) < 1` rather than `1`. The existing `atol=1e-5` test passes by accident. Affects only the "zero-vector safe" Scenario (which currently asserts `z/eps`); tightening would change the Scenario's expected value. Deferred — needs separate spec/code decision.
- **m3** — wayfinder Req 14 spec marks 100 K as the END boundary; skeleton spec currently has `phase_id(100_000) → 4` (i.e. 100 K is in Phase 4, not END). Two-spec boundary inconsistency. Resolution requires either adding `phase_id(100_000) → 5` (END sentinel) or relaxing skeleton spec. Deferred — semantic boundary needs product-side decision.
- **m5** — `viz.py` Protocol stubs are explicitly out of numerical scope; skeleton spec already declares them as Protocol-only. No change needed.
- All `m1`-`m5` Minor items are excluded from this change's spec; they remain open for a future change that explicitly owns them.
