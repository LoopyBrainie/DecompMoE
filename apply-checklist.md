# Apply Checklist — `fix-math-consistency-audit-2026-08-apply`

> **Bootstrap doc** for the downstream code-only change. Not part of any commit — copy / paste / reference when scaffolding `fix-math-consistency-audit-2026-08-apply`.
>
> **Spec source of truth**: `openspec/specs/wayfinder/spec.md` (master, post-archive) and `openspec/specs/decompmoe-skeleton/spec.md` (master, post-archive). The spec drives the tests; tests do NOT derive from the implementation's output (this is the failure mode the audit fixed).

---

## TDD workflow (per task)

For each item below, the next session should follow this exact sequence — this is the failure-prevention pattern that the audit found missing in the prior 95/95 green tests:

1. **Read the spec anchor**: open the spec file at the Requirement + Scenario listed in the task. Confirm the closed-form expected value (or invariant) is the spec-stated constant, not the implementation's output.
2. **Write the test FIRST**: in the listed test file, add a new test or rewrite an existing one with the spec's closed-form constant (e.g. `pytest.approx(33_554_432, abs=0)`). At this point, the test MUST fail (no implementation yet).
3. **Implement the fix**: in the listed source file, make the minimum change to satisfy the test (per spec).
4. **Re-run the test**: it MUST now pass.
5. **Run the full suite**: `uv run pytest tests/` — MUST have zero regressions vs the previous 95-pass baseline (target: 95 + new tests).
6. **Commit test + impl together** as one logical change.

Do NOT skip step 1 — the spec is the single source of truth, not the code.

---

## Code items (8 tasks)

### Apply task 3.1 — `src/decompmoe/sphere.py`

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, Requirement "Voronoi Self-Consistency Threshold", Scenario "no hard-coded table values" + Scenario "MVP self-consistency" + Scenario "N_e dependence of voronoi_angle" (residual `< 1e-9`)
- **Action**: delete `_VORONOI_MVP_TABLE` constant and its hit branch in `canonical_voronoi_angle()`. Every input must bisect.
- **Verify**: `grep -F "_VORONOI_MVP_TABLE" src/decompmoe/sphere.py` → 0 hits (禁止性约束：常量不复现 — 见 CLAUDE.md §3 grep 适用范围)
- **New tests** (3 项 — 既有禁止性 grep 又有数值验证):
  - `tests/test_sphere.py::test_no_hardcoded_table_values` — source-grep asserting `_VORONOI_MVP_TABLE` is absent (禁止性约束)
  - `tests/test_sphere.py::test_voronoi_residual_below_1e_minus_9` — `|0.5 · I_{sin²θ}(7.5, 0.5) − 1/N_e| < 1e-9` for `N_e ∈ {16, 17, 64}` (the residual from MVP Scenario)
  - `tests/test_sphere.py::test_voronoi_monotone_in_ne` — assert `canonical_voronoi_angle(N_e=16) ≈ 1.1736 rad`, `canonical_voronoi_angle(N_e=17) ≈ 1.1663 rad` (monotone-continuity across the N_e=16/17 boundary that the original table wrongly held at 52°); `pytest.approx(value, abs=1e-4)` for each. **DO NOT hard-code the implementation's exact bisection output** as the expected value — these constants come from independent root-finding of `½·I_{sin²θ}((d_c−1)/2, 1/2) = 1/N_e`, NOT from `canonical_voronoi_angle()`.

---

### Apply task 3.2 — `src/decompmoe/config.py`

- **Spec anchor**: `openspec/specs/wayfinder/spec.md`, Requirement "4070 MVP Hyperparameter Set", Scenario "Closed-form parameter totals"
  - Per-layer `33_554_432`, total `134_217_728` exact
- **Action**: FFN coefficient `2 * 2` → `3 * 2` at lines 122 and 133 (the FLOPs formula must count SwiGLU's 3 matrices, not 2). DO NOT change attention `4 * 2 * d²` at lines 121/132 — that 4 is correct (Q/K/V/O).
- **Verify**: `grep -F "3 * 2" src/decompmoe/config.py` → ≥ 2 hits
- **New test**: `tests/test_config.py::test_flops_per_layer_exact_33554432` and `test_flops_total_exact_134217728` — assert the absolute values

---

### Apply task 3.3 — `src/decompmoe/schedule.py`

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, Requirement "Beta Parameterization Operational Domain"
  - `gamma_reset_for_phase4(16.0) == ln(15/16) ≈ −0.0645385` within `abs=1e-4`
  - `beta_effective(gamma, phase, step, *, cfg)` uses `phase_beta_max(phase, step)` (NOT `phase_beta_box(phase).hi`)
  - Pinned linear convention: `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)` with `phase_end` exclusive (Phase 2 range `[6_000, 26_000)`, Phase 3 range `[26_000, 56_000)`)
  - `phase_beta_box(2) == (1.0, 4.0)` exact
- **Action**: add the **three schedule-time functions** (`gamma_reset_for_phase4`, `phase_beta_max`, `beta_effective`). Fix `phase_beta_box(2)` (currently falls through to default `(1.0, 32.0)`). **`phase4_inverse_temperature` lives in `beta.py` (3.8)**, not here — β parameterization primitives belong with `inverse_temperature`.
- **Verify**: `grep -E "gamma_reset_for_phase4|phase_beta_max|beta_effective" src/decompmoe/schedule.py` → ≥ 3 hits (note: `grep -F` with `\|` is broken; use `grep -E`); separately `grep -F "phase4_inverse_temperature" src/decompmoe/beta.py` → ≥ 1 hit (3.8 verify)
- **New tests**: `tests/test_schedule.py::test_phase_beta_box_phase2_exact`, `test_phase_beta_max_is_time_varying` (exact-value pins at `(2, 6_000) = 1.0`, `(2, 16_000) = 2.5`, `(3, 26_000) = 4.0`, `(3, 41_000) = 10.0`, all within `abs=1e-9`), `test_gamma_reset_for_phase4_boundary_continuity` (`gamma_reset_for_phase4(16.0) ≈ −0.0645385`, `phase4_inverse_temperature(gamma_reset_for_phase4(16.0)) ≈ 16.0`)

---

### Apply task 3.4 — `src/decompmoe/metrics.py` (MOST COMPLEX)

- **Spec anchors** (multiple Requirements in `openspec/specs/decompmoe-skeleton/spec.md`):
  - Requirement "Eight Metrics And Classification" — Offline Tier definitions
  - ADDED Requirements in wayfinder master: "MCI closed-form on uniform token distribution" + "MCI closed-form on rank-1 token distribution" + "CG zero-gradient invariance" + "CG positive homogeneity" + "SP closed-form on orthonormal-aligned inputs" + "SP closed-form on 60° offset" + "SP range bound" + "D_chord closed-form on orthonormal basis"
- **Critical spec details to implement**:
  - `MCI(token_signatures)` — input is **token signatures**, NOT centroids
  - `MCI = 1 / (d_c · Σ_{j=1}^{d_c} λ̃_j²)` where `λ_j` are eigenvalues of the **uncentered** second moment `M = (1/|T|) · Σ_{t ∈ T} C_t C_tᵀ` of routed-token signatures
  - `λ̃_j = λ_j / Σ_r λ_r`
  - Uniform token distribution (`|T| = d_c·k`, each `e_j` repeated `k` times) → `MCI == 1.0` exactly
  - Rank-1 (all `C_t = e_1`) → `MCI == 1/d_c` exactly
  - `MCI ∈ [1/d_c, 1]` (closed range)
  - `CG(zero_grad) == 0.0` exact
  - `CG(2·g) == 2·CG(g)` (positive homogeneity, |·| < 1e-6)
  - `SP = mean({SP_i : ‖T_i‖₁ > 0})` (skip empty experts, NOT report 0)
  - `SP(C_t = c_{a(t)} for all t) == 1.0`
  - `SP(60° offset, c_i^T C_t = 0.5) == 0.5`
  - `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6` (containment)
  - `D_chord(orthonormal basis) == √2` exact within `abs=1e-6`
  - `D_chord = √(2 · versine)` relationship holds
  - `metrics.OFFLINE = frozenset({"SP", "D_chord", "MCI", "CG"})` (note: rename `D_c` → `D_chord`)
- **Action**: replace `return torch.tensor(0.0)` stubs in `SP`, `D_c` (rename), `MCI`, `CG` with the closed-form implementations per spec.
- **Verify**: `grep -F "torch.tensor(0.0)" src/decompmoe/metrics.py` → 0 hits; `grep -F "D_chord" src/decompmoe/metrics.py` → ≥ 2 hits
- **New tests**: 8 closed-form tests (see spec anchors)

---

### Apply task 3.5 — `src/decompmoe/experts.py`

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, Requirement "Standard SwiGLU Expert With No Shared Branch"
  - `ExpertPool(MVPConfig())` MUST be `nn.Module` with `experts: nn.ModuleList[SwiGLUExpert]`
  - `sum(p.numel() for p in pool.parameters()) == N_e · 3 · d_model · d_ffn == 100_663_296` exact
- **Action**: change `class ExpertPool:` to `class ExpertPool(nn.Module):`, `self.experts = [...]` to `self.experts = nn.ModuleList([...])`, add `super().__init__()`.
- **Verify**: `inspect.getsource(ExpertPool)` contains both `nn.Module` and `nn.ModuleList`
- **New tests**: `tests/test_experts.py::test_expert_pool_is_nn_module` (asserts `isinstance(pool, nn.Module)` + `isinstance(pool.experts, nn.ModuleList)`), `test_expert_pool_param_count == 100_663_296`

---

### Apply task 3.6 — `src/decompmoe/extraction.py`

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, Requirement "Centroid Driver Semantic Invariants", invariant #4 (Near-zero candidate fallback for Phase 4)
  - Phase 4 step applies `torch.where(‖c‖ < 1e-9, prev_c, normalize(c))` like EMA branch (lines 139-142)
- **Action**: extend `CentroidDriver.step()` Phase 4 branch (line 144-145) with the same `torch.where` guard pattern.
- **Verify**: `test_near_zero_candidate_fallback_phase4` passes (new test in `tests/test_extraction.py`)
- **New test**: `tests/test_extraction.py::test_near_zero_candidate_fallback_phase4` — feed `centroids` with `‖c‖₂ < 1e-9`, verify output preserves prev + no NaN

---

### Apply task 3.7 — `src/decompmoe/safeguards.py`

- **Spec anchor**: `openspec/specs/wayfinder/spec.md`, ADDED Requirement "Resurrection Perturbation Per-Expert Contract"
  - `resurrection_perturb_distribution(target_idx, *, eps_std=0.05)` returns shape `(d_c,)` or `(d_model·d_ffn,)` (single expert), NOT `(N_e,)`
  - `β_i ← 0.85·β_{j*}` and `β_{j*} ← 0.85·β_{j*}` mutation as part of the same event
- **Action**: stop using `target_idx` as unused param; return single-expert-shape tensor; add β decay mutation
- **Verify**: output shape `(d_c,)` or `(d_model·d_ffn,)`; not `(N_e,)`. Mutation visible via state inspection.
- **New test**: `tests/test_safeguards.py::test_resurrection_perturbation_shape_per_expert` + `test_resurrection_beta_decay`

---

### Apply task 3.8 — `src/decompmoe/beta.py`

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, ADDED Requirement "Beta Parameterization Operational Domain" (already in master)
  - `phase4_inverse_temperature(gamma_p) = 1 + 31 · σ(gamma_p)` (operational-domain form, distinct from `inverse_temperature`)
  - `MAX_GRAD_PER_GAMMA = 15.95` with **explicit domain label** (parameterization-space worst case)
  - Add `MAX_GRAD_PER_GAMMA_PHASE4 = 15.5` (operational-domain Phase 4 worst case)
- **Action**: add `phase4_inverse_temperature` function; document `MAX_GRAD_PER_GAMMA` domain in module docstring or comment; add Phase 4 constant.
- **Verify**: `grep -F "phase4_inverse_temperature" src/decompmoe/beta.py` → ≥ 1 hit

---

## Test rewrites (5 tasks, all reference closed-form constants from the spec)

### Apply task 3.9 — `tests/test_loss.py`

- **Spec anchors** (`openspec/specs/decompmoe-skeleton/spec.md`):
  - "Loss Composition With Staged Lambda" → "L_sep closed form" + "Alpha pinned to 0.01" + "Lambda cosine ramp endpoints in phase 3"
- **Rewrites**:
  - `test_sep_formula`: orthogonal basis → `L_sep == 0.0` within `abs=1e-12`
  - `test_load_balance_alpha_fixed`: uniform `f = P = 1/16` → `L_lb_raw == 1.0`; `L_lb == 0.01` exact
  - `test_lambda_cosine_ramp_phase_3`: 3 step values exact — `λ(26_000) == 0.0`, `λ(41_000) ≈ 5e-4`, `λ(55_999) ≈ 0.001`

---

### Apply task 3.10 — `tests/test_beta.py`

- **Spec anchor**: `openspec/specs/wayfinder/spec.md`, ADDED Requirement "Closed-Form Gradient Bound Worst Case"
- **Rewrites** (tightest possible closed form):
  - `test_grad_C_bound`: orthogonal unit vectors `C = e_1, c = e_2, β = β_max = 32` → `‖∂logit/∂C‖₂ == 32.0` within `abs=1e-4`
  - `test_grad_gamma_bound`: `γ = 0, c = −e_1` → `|∂logit/∂γ| == 15.95` within `abs=1e-3`
- **New**: `test_max_grad_per_gamma_phase4`: `γ' = 0, c = −C` → `|∂β^eff/∂γ'| == 15.5` within `abs=1e-3` (operational-domain Phase 4 worst case)

---

### Apply task 3.11 — `tests/test_extraction.py`

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, Requirement "C Extraction Four-Step Pipeline", Scenario "Per-token MAC closed form" (pinned convention: 1 MAC = 1 multiply + 1 accumulate; FLOPs = 2·MACs)
- **Closed form**: per-token MACs = `H_kv · (2 · d_k · d_c + d_c) + H_kv · d_c + d_c`. At MVP (`H_kv=8, d_k=128, d_c=16`): `8·4112 + 8·16 + 16 = 32_896 + 128 + 16 = 33_040` per-token MACs exactly (NOT `33_056` — that was an arithmetic slip; NOT `65_792` — that's the prior test's FLOPs convention counting bias term not doubled). Scaling: `O(H_kv · d_k · d_c)`.
- **Rewrite** `test_complexity_budget`:
  - Compute the closed form from `cfg.H_kv`, `cfg.d_k`, `cfg.d_c`: `expected = H_kv*(2*d_k*d_c + d_c) + H_kv*d_c + d_c`
  - `pytest.approx(expected, abs=1)` for `cfg == MVPConfig()`
  - Assert `expected == 33_040` exactly when run against the MVP constants
  - DO NOT instrument via `torch.profiler` — profiler counts are backend-dependent and will not reproduce a hand-derived constant
  - Add a scaling test: doubling `d_c` should double the linear-in-`d_c` terms (sanity check the closed form, not the implementation)

---

### Apply task 3.12 — `tests/test_gating.py`

- **Spec anchor**: `openspec/specs/wayfinder/spec.md`, ADDED Requirement "Forward Formula Numerical Verification (Routing Layer)"
- **Rewrite** `test_forward_formula_strictness`: NOT source-grep. Numerical verify with stub `ExpertPool`:
  - Stub experts: `experts[i](x) = E_i` (fixed per expert)
  - Assert `x_out == x + Σ_{i ∈ I_k} p_i · E_i` within `abs=1e-6`

---

### Apply task 3.13 — `tests/test_config.py`

- **Spec anchor**: `openspec/specs/wayfinder/spec.md`, Requirement "4070 MVP Hyperparameter Set" — "Closed-form parameter totals"
- **Rewrite** `test_total_param_estimate`: assert exact `total == 452_329_984`, `active == 100_008_448` (NOT ≤ ±1% interval). Also assert `P_router/layer = 32_896` exact (the router term that was previously misclassified as rounding).

---

### Apply task 3.14 — `tests/test_experts.py` (new tests)

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, Requirement "Standard SwiGLU Expert With No Shared Branch"
- **New tests**:
  - `test_expert_pool_is_nn_module`: `isinstance(ExpertPool(MVPConfig()), nn.Module)` AND `isinstance(pool.experts, nn.ModuleList)`
  - `test_expert_pool_param_count`: `sum(p.numel() for p in ExpertPool(MVPConfig()).parameters()) == 100_663_296` exact

---

### Apply task 3.15 — `tests/test_extraction.py` (new test)

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, Requirement "Centroid Driver Semantic Invariants", invariant #4
- **New test** `test_near_zero_candidate_fallback_phase4`: feed Phase 4 driver with `‖c‖₂ < 1e-9`, verify output preserves prev + no NaN

---

### Apply task 3.16 — `tests/test_schedule.py` (new tests)

- **Spec anchor**: `openspec/specs/decompmoe-skeleton/spec.md`, ADDED Requirement "Beta Parameterization Operational Domain"
- **New tests**:
  - `test_phase_beta_box_phase2 == (1.0, 4.0)`
  - `test_phase_beta_max_is_time_varying`: at exact-value boundaries — `phase_beta_max(2, 6_000) == 1.0`, `phase_beta_max(2, 16_000) == 2.5`, `phase_beta_max(3, 26_000) == 4.0`, `phase_beta_max(3, 41_000) == 10.0`, all within `abs=1e-9`
  - `test_beta_effective_phase_4_continuity`: `beta_effective(gamma_p=ln(15/16), phase=4, step=56_000) == 16.0` exact within `1e-6`; also assert `phase_beta_max(3, 55_999) ≈ 15.9996` (the limit-continuity witness)

---

### Apply task 3.17 — `tests/test_metrics.py` (new tests)

- **Spec anchors** (multiple ADDED Requirements in wayfinder master):
  - "MCI closed-form on uniform token distribution": `|T| = d_c·k` with each `e_j` repeated `k` times → `MCI == 1.0` exact within `abs=1e-12`
  - "MCI closed-form on rank-1 token distribution": all `C_t = e_1` → `MCI == 1/d_c` exact within `abs=1e-12`
  - "CG zero-gradient invariance": `CG(zero_grad) == 0.0` exact within `abs=1e-12`
  - "CG positive homogeneity": `|CG(2g) − 2·CG(g)| < 1e-6`
  - "SP closed-form on orthonormal-aligned inputs": `C_t = c_{a(t)} for all t` → `SP == 1.0` within `abs=1e-6`
  - "SP closed-form on 60° offset": `c_i^T C_t = cos 60° = 0.5` → `SP == 0.5` within `abs=1e-6`
  - "SP range bound": `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6` (containment, NOT `abs=1e-6` ambiguity)

---

## Acceptance criteria (apply change archive gate)

- `uv run pytest tests/` → 95 baseline preserved (rewrites replace existing tests, do NOT add count) + ~15 new closed-form / residual / continuity tests ≈ ≥ 110 passed, 0 failed. **DO NOT double-count rewrites** as new tests — they keep the count, not grow it. The only growth comes from §3.1 (3 new), §3.2 (2 new), §3.3 (3 new), §3.4 (8 closed-form), §3.5 (2 new), §3.6 (1 new), §3.7 (2 new), §3.14-§3.17 (~6 new across 4 files). All new tests must derive their expected values from the spec closed form or independent root-finding (NOT from the implementation's output).
- New §4 grep checks pass (post-apply):
  - `grep -F "torch.tensor(0.0)" src/decompmoe/metrics.py` → 0 hits
  - `grep -F "_VORONOI_MVP_TABLE" src/decompmoe/sphere.py` → 0 hits
  - `inspect.getsource(ExpertPool)` contains `nn.ModuleList`
  - `isinstance(ExpertPool(MVPConfig()), nn.Module) == True`
  - `phase_beta_box(2) == (1.0, 4.0)` exact
  - `phase_beta_max(3, 55_999) ≈ 15.9996` (limit-continuity witness)
  - `compute_total_and_active(MVPConfig()) == (452_329_984, 100_008_448)` exact
  - `flops_per_token(MVPConfig(), "MOE") == 134_217_728` exact
- Independent post-archive consistency check (per `CLAUDE.md §3`): for each Req carrying a concrete number, manually substitute the equation and compare to spec claim. Should pass cleanly with all corrections applied.

---

## Out of scope (deferred to future changes)

- **m1** `halve_lr` → `decay_lr` rename (cosmetic)
- **m2** `spherical_l2_normalize` `eps`-denominator bias (separate spec/code decision needed)
- **m3** wayfinder-vs-skeleton `phase_id(100_000)` boundary inconsistency (semantic decision needed)
- **m5** `viz.py` Protocol stub免责 (already declarative)

---

## Reference: 4-round review history

| Round | Commit | Findings | Key fix |
|---|---|---|---|
| 1 | `e09b893` | initial 13-finding delta | — |
| 2 | `9fe9dab` | review: 13/13 + 2 Majors + 4 Minors | MCI formula corrected; β ramp; CG invariants; Beta Param refile |
| 3 | `c06720c` | review: 7/7 + 2 Majors + 3 Minors | MCI covariance pinned (uncentered M); phase_beta_max convention pinned |
| 4 | `d9b9774` | review: 5/5 + 2 Majors + 3 Minors | MCI range `[1/d_c, 1]` closed; CV rationale split; limit-continuity wording |
| archive | `f45a42c` | — | delta applied to master specs |

(All four commits are in the review branch `review/fix-math-consistency-audit-2026-08`; the archived change is at `openspec/changes/archive/2026-08-23-fix-math-consistency-audit-2026-08/`.)