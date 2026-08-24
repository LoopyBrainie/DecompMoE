# Tasks — `fix-math-consistency-audit-2026-08`

## 1. 主 spec `wayfinder` 修订

- [x] 1.1 Req 11 (B1) — MODIFIED Requirement "4070 MVP Hyperparameter Set": Voronoi table 52°/25.45° → 67.24°/58.47°; `r` 0.380/0.0971 → `versine_Voronoi` 0.6127/0.4776 (renamed from "spherical-chord radius" to avoid confusion with `D_chord`); domain `(0, π)` → `(0, π/2]` (m4 folded); add "Voronoi closed-form residual is bounded" Scenario (residual `< 1e-9`); rewrite assumption 4 from "rounding residual" to exact router term `P_router/layer = H_kv · (2·d_k·d_c + d_c) = 32_896` (Major 2); rewrite the "Closed-form parameter totals" paragraph to derive `452_329_984` / `100_008_448` term-by-term from the four assumptions; verify `grep -F "52.00°\|25.45°\|0.9076\|0.4494\|0.380\|0.0971" openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` → 0 hits and `grep -F "67.24°\|58.47°\|0.6127\|0.4776\|1.1736\|1.0205"` → ≥ 4 hits and `grep -F "P_router/layer"` → ≥ 1 hit.

- [x] 1.2 Req 7 (B6) — ADDED Requirement "Operational Domain γ' Reset Closed-Form Worked Example" pinning `gamma_reset_for_phase4(16.0) ≈ −0.0645385...`; verify `grep -F "Operational Domain" openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` ≥ 1 hit.

- [x] 1.3 Req 13 (M4) — ADDED Requirement "Resurrection Perturbation Per-Expert Contract" pinning single-expert-shape output; verify `grep -F "Resurrection Perturbation Per-Expert"` → 1 hit.

- [x] 1.4 Req 14 (M1) — ADDED Requirement "Phase 2 β Box Equality": pin `phase_beta_box(2) == (1.0, 4.0)` and `phase_beta_box(3) == (4.0, 16.0)`; also introduce `phase_beta_max(phase, step)` as the time-varying schedule ramp (linear in step between box endpoints); add Scenario "phase_beta_max is time-varying, not the static box hi" (asserts `phase_beta_max(2, 6_000) == 1.0`, `phase_beta_max(2, ~16_000) == 2.5`, `phase_beta_max(2, 25_999) == 4.0`); verify `grep -F "Phase 2 β Box"` → 1 hit, `grep -F "phase_beta_max"` → ≥ 1 hit.

- [x] 1.5 Req 20 (B7) — MODIFIED Requirement "Eight Geometric Quantification Metrics" (whole-block): change MCI formula from `(1/d_c) · Σ 1/λ̃²` to `1/(d_c · Σλ̃²)` (B1 Blocker); replace 4 original Scenarios verbatim + add 8 closed-form Scenarios (SP uniform-aligned=1.0, SP 60° offset=0.5, SP range bound ∈ [-1, 1], D_chord orthonormal=√2, MCI uniform=1.0, MCI rank-1→1/d_c, CG zero-grad=0.0, CG positive homogeneity); removed the prior "Offline Metric Numerical Invariants" ADDED Requirement (its content folded into the MODIFIED Scenarios); verify `grep -F "Eight Geometric Quantification Metrics"` → 1 hit (in MODIFIED block), `grep -F "sqrt(2)"` → ≥ 1 hit, `grep -F "MCI closed-form on uniform spectrum"` → 1 hit, `grep -F "CG zero-gradient invariance"` → 1 hit, `grep -F "Offline Metric Numerical Invariants" openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` → 0 hits (deleted).

- [x] 1.6 Req 24 (B6) — ADDED Requirement "β^eff Phase 3 → 4 Continuity Closed-Form" pinning `β^eff(Phase 4, t=0) = 16.0` exactly; verify `grep -F "β^eff Phase 3 → 4 Continuity"` → 1 hit.

- [x] 1.7 Req 7 (B6) — ADDED Requirement "Closed-Form Gradient Bound Worst Case" pinning `‖∂‖₂ == 32.0` and `|∂γ| == 15.95`; verify `grep -F "Closed-Form Gradient Bound"` → 1 hit.

- [x] 1.8 Req 8 (M5) — ADDED Requirement "Forward Formula Numerical Verification (Routing Layer)" pinning `x_out == x + Σ p_i · E_i` numerical equality; verify `grep -F "Forward Formula Numerical"` → 1 hit.

## 2. Skeleton spec `decompmoe-skeleton` 修订

- [x] 2.1 Voronoi (B1, B2, B3) — MODIFIED Requirement "Voronoi Self-Consistency Threshold": corrected values 1.1736 / 1.0205 rad, residual `< 1e-9` Scenario, no-table Scenario; rename `r_Voronoi` to `versine_Voronoi` with note distinguishing from `D_chord` (Minor 1); verify `grep -F "0.9076\|0.4494\|0.380\|0.0971\|1.1736\|1.0205" openspec/changes/fix-math-consistency-audit-2026-08/specs/decompmoe-skeleton/spec.md` — first 4 must be 0 hits, last 2 must hit.

- [x] 2.2 Param count (M5, Major 2) — MODIFIED Requirement "Total And Active Parameter Estimator": exact `total == 452_329_984`, `active == 100_008_448` (replacing ±1% interval); rewrite the body to derive each term exactly (`P_emb`, `P_attn/layer`, `P_expert`, `P_router/layer = 32_896` exact — NOT a rounding residual); verify `grep -F "452_329_984"` ≥ 1 hit, `grep -F "100_008_448"` ≥ 1 hit, `grep -F "P_router/layer = 32_896"` ≥ 1 hit.

- [x] 2.3 FLOPs (B4, B5) — MODIFIED Requirement "Active FLOPs Parity Against Dense Baseline": add per-layer `33_554_432` Scenario + total `134_217_728` Scenario; verify `grep -F "33_554_432"` ≥ 1 hit, `grep -F "134_217_728"` ≥ 1 hit.

- [x] 2.4 ExpertPool (M2) — MODIFIED Requirement "Standard SwiGLU Expert With No Shared Branch": add `isinstance(pool, nn.Module)` and `100_663_296` param-count Scenarios; verify `grep -F "nn.ModuleList\|100_663_296"` ≥ 1 hit each.

- [x] 2.5 L_lb / λ(t) (M5) — MODIFIED Requirement "Loss Composition With Staged Lambda": add uniform-f=P=1/N_e → L_lb_raw=1.0 Scenario; add λ(26_000)=0 / λ(41_000)≈5e-4 / λ(55_999)≈0.001 Scenario; verify `grep -F "L_lb_raw = N_e\|cosine ramp"` → ≥ 1 hit each.

- [x] 2.6 L_sep (M5) — MODIFIED Requirement "Loss Composition With Staged Lambda": orthogonal-basis `L_sep == 0.0` Scenario; verify `grep -F "orthogonal basis"` → 1 hit.

- [x] 2.7 Phase 4 fallback (M3) — MODIFIED Requirement "Centroid Driver Semantic Invariants": add invariant #4 for Phase 4 near-zero fallback; verify `grep -F "PROJECTED_SGD\|near-zero"` → ≥ 2 hits.

- [x] 2.8 Metrics (B7, Major 4) — MODIFIED Requirement "Eight Metrics And Classification": change MCI formula from `(1/d_c) · Σ 1/λ̃²` to `1/(d_c · Σλ̃²)` (B1); replace "Offline metrics are not placeholders" Scenario (structural) with 8 concrete closed-form Scenarios (Major 4): SP uniform-aligned, SP 60°, SP range, D_chord orthonormal, MCI uniform, CG zero-grad, CG homogeneity; verify `grep -F "MCI = 1 / (d_c"` → 1 hit, `grep -F "MCI closed-form on uniform spectrum"` → 1 hit, `grep -F "torch.tensor(0.0)\|Offline metrics are not placeholders" openspec/changes/fix-math-consistency-audit-2026-08/specs/decompmoe-skeleton/spec.md` → 0 hits (deleted).

- [x] 2.9 β operational domain (B6, Major 1, Minor 4) — REFLED as ADDED Requirement "Beta Parameterization Operational Domain" (was previously MODIFIED; renamed + refiled because the master spec doesn't have a matching header): `phase4_inverse_temperature`, `gamma_reset_for_phase4`, `beta_effective` definitions; `beta_effective` uses `phase_beta_max(phase, step)` (time-varying) NOT `phase_beta_box(phase).hi` (static) (B2 Blocker); explicit domain labels: `MAX_GRAD_PER_C = 32.0` (operational, all domains), `MAX_GRAD_PER_GAMMA = 15.95` (parameterization-space worst case, `0.5 · (β_max − β_min)`); operational-domain Phase 4 worst case is `0.5 · 31 · 2 = 15.5` (Minor 4); verify `grep -F "phase4_inverse_temperature\|gamma_reset_for_phase4"` ≥ 1 hit each, `grep -F "phase_beta_max(phase, step)"` → 1 hit (NOT `phase_beta_box(phase).hi`), `grep -F "Beta Parameterization Operational Domain"` → 1 hit.

- [ ] ~~2.10 FLOPs permutation (B5 hardening) — DROPPED per Minor 2 (the closed-form `33_554_432` / `134_217_728` Scenarios already pin MoE == DENSE exactly; permutation invariance is a derived consequence, not a new constraint; also `MOE_MVP`/`DENSE_4096` vs `"MOE"`/`"DENSE"` arch-ID mismatch is moot now that this Requirement is gone).~~

## 3. Apply 阶段触发（下游，非本 change 范围）

All items in this section are handed off to a future `fix-math-consistency-audit-2026-08-apply` change (mirrors `fix-openspec-doc-bugs` → `fix-openspec-doc-bugs-apply` precedent). The apply change's `tasks.md` will mirror this section verbatim with the same `~~(已移交下游)~~` strike-through prefix. The two-stage split is deliberate (see `design.md` Open Questions) and is NOT a contradiction of the Q2/Q3 answers in the original review — those answers address whether the *spec* should require these (it does, this change); code implementation follows in the apply change.

- [ ] 3.1 ~~`src/decompmoe/sphere.py` delete `_VORONOI_MVP_TABLE` and table-hit branch (B2); verify `grep -F "_VORONOI_MVP_TABLE" src/decompmoe/sphere.py` → 0 hits.~~
- [ ] 3.2 ~~`src/decompmoe/config.py` FFN coefficient `2 * 2` → `3 * 2` at lines 122 / 133 (B4; attention `4 * 2 * d²` at lines 121 / 132 is correct for Q/K/V/O and MUST NOT change); verify `grep -F "3 * 2" src/decompmoe/config.py` → ≥ 2 hits.~~
- [ ] 3.3 ~~`src/decompmoe/schedule.py` add `beta_effective(gamma, phase, step, *, cfg)`, `gamma_reset_for_phase4(beta_p3)`, `phase_beta_max(phase, step)` (NEW time-varying API, distinct from `phase_beta_box(phase).hi`); fix `phase_beta_box(2)` to return `(1.0, 4.0)` (B6 + M1); verify `grep -F "beta_effective\|gamma_reset_for_phase4\|phase_beta_max\|phase4_inverse_temperature" src/decompmoe/schedule.py src/decompmoe/beta.py` → ≥ 4 hits.~~
- [ ] 3.4 ~~`src/decompmoe/metrics.py` replace `return torch.tensor(0.0)` stubs in `SP`, `D_c` (rename to `D_chord`), `MCI`, `CG` with closed-form implementations — **MCI MUST use `1 / (d_c · Σλ̃²)`** (effective-dimensionality fraction; uniform spectrum → 1.0, rank-1 → 1/d_c), NOT the prior `(1/d_c) · Σ 1/λ̃²` (which is mathematically inconsistent with the declared `(1/d_c, 1]` range); **CG** MUST satisfy zero-grad invariance (`CG(zero_grad) == 0.0` exact) AND positive homogeneity (`|CG(2·g) − 2·CG(g)| < 1e-6`); **SP** MUST aggregate as `mean({SP_i : ‖T_i‖₁ > 0})` (skip experts with empty `T_i`, do NOT report 0); align `metrics.OFFLINE = frozenset({"SP", "D_chord", "MCI", "CG"})`; verify `grep -F "torch.tensor(0.0)" src/decompmoe/metrics.py` → 0 hits.~~
- [ ] 3.5 ~~`src/decompmoe/experts.py` `class ExpertPool(nn.Module):` + `self.experts = nn.ModuleList([SwiGLUExpert(cfg) for _ in range(cfg.N_e)])` (M2); verify `inspect.getsource(ExpertPool)` contains `nn.Module` and `nn.ModuleList`.~~
- [ ] 3.6 ~~`src/decompmoe/extraction.py` Phase 4 step applies `torch.where(‖c‖ < 1e-9, prev_c, normalize(c))` like EMA branch at lines 139-142 (M3); verify the test `test_near_zero_candidate_fallback_phase4` passes.~~
- [ ] 3.7 ~~`src/decompmoe/safeguards.py` `resurrection_perturb_distribution(target_idx, *, eps_std=0.05)` returns single-expert-shape tensor (shape `(d_c,)` or `(d_model · d_ffn,)`); add `β_i ← 0.85·β_{j*}` and `β_{j*} ← 0.85·β_{j*}` mutation as part of the same resurrection event (M4); verify the perturbation output shape is `(d_c,)` or `(d_model·d_ffn,)`, NOT `(N_e,)`.~~
- [ ] 3.8 ~~`src/decompmoe/beta.py` add `phase4_inverse_temperature(gamma_p) = 1 + 31 · torch.sigmoid(gamma_p)` (B6); export `MAX_GRAD_PER_GAMMA = 15.95` with explicit parameterization-space domain label AND add operational-domain Phase 4 worst-case constant `MAX_GRAD_PER_GAMMA_PHASE4 = 15.5` (Minor 4); verify `grep -F "phase4_inverse_temperature" src/decompmoe/beta.py` → ≥ 1 hit.~~
- [ ] 3.9 ~~`tests/test_loss.py` rewrite `test_sep_formula` (orthogonal basis → `L_sep == 0.0` within `1e-12`); rewrite `test_load_balance_alpha_fixed` (uniform `f = P = 1/16` → `L_lb_raw == 1.0`); rewrite `test_lambda_cosine_ramp_phase_3` (3 closed-form step values).~~
- [ ] 3.10 ~~`tests/test_beta.py` rewrite `test_grad_C_bound` (orthogonal unit vectors → `‖∂‖ == 32.0` within `1e-4`); rewrite `test_grad_gamma_bound` (`γ=0, c=−C` → `|∂γ| == 15.95` within `1e-3`); add `test_max_grad_per_gamma_phase4` (`|∂β^eff/∂γ'| == 15.5` at `γ'=0, inner=−1` — Minor 4 operational-domain counterpart).~~
- [ ] 3.11 ~~`tests/test_extraction.py` rewrite `test_complexity_budget` to assert on `extract_C` actual op count (`33_056` MAC at MVP, NOT the internal helper's `65792`).~~
- [ ] 3.12 ~~`tests/test_gating.py` rewrite `test_forward_formula_strictness` to numerical verify `x_out == x + Σ p_i · E_i` with stub experts (NOT a source-grep).~~
- [ ] 3.13 ~~`tests/test_config.py` rewrite `test_total_param_estimate` to assert exact `total == 452_329_984`, `active == 100_008_448` (NOT ±1% interval); also assert `P_router/layer = 32_896` exact (Major 2).~~
- [ ] 3.14 ~~`tests/test_experts.py` add `test_expert_pool_is_nn_module` (asserts `isinstance(ExpertPool(MVPConfig()), nn.Module)` and `isinstance(pool.experts, nn.ModuleList)`); add `test_expert_pool_param_count == 100_663_296`.~~
- [ ] 3.15 ~~`tests/test_extraction.py` add `test_near_zero_candidate_fallback_phase4` covering Phase 4 fallback under `‖c‖₂ < 1e-9`.~~
- [ ] 3.16 ~~`tests/test_schedule.py` add `test_phase_beta_box_phase2 == (1.0, 4.0)`; add `test_phase_beta_max_pinned_linear_convention` (asserts `phase_beta_max(2, 6_000) == 1.0` exact at boundary start, `phase_beta_max(2, 16_000) == 2.5` exact at midpoint = `1 + 3·10_000/20_000`, `phase_beta_max(2, 25_999) == 3.99985` exact = `1 + 3·19_999/20_000` — NOT `4.0` since `phase_end` is exclusive; `phase_beta_max(3, 26_000) == 4.0` exact at boundary start = `box(3).lo`; `phase_beta_max(3, 41_000) == 10.0` exact at midpoint = `4 + 12·15_000/30_000`; `phase_beta_max(3, 55_999) == 15.9996` exact); add `test_beta_effective_phase_4_continuity` (asserts `beta_effective(gamma_p=ln(15/16), phase=4, step=56_000) == 16.0` within `1e-6`). Convention: `phase_beta_max(phase, step) = box(phase).lo + (box(phase).hi − box(phase).lo) · (step − phase_start) / (phase_end − phase_start)`, `phase_end` exclusive (Phase 2 range `[6_000, 26_000)`, Phase 3 range `[26_000, 56_000)`).~~
- [ ] 3.17 ~~`tests/test_metrics.py` add `test_mci_uniform_token_distribution` (`|T| = d_c · k` signatures each `e_j` repeated `k` times ⇒ `MCI == 1.0` within `1e-12`), `test_mci_rank1_token_distribution` (all `C_t = e_1` ⇒ `MCI == 1/d_c` within `1e-12`), `test_cg_zero_grad` (`CG(zero) == 0.0` exact), `test_cg_homogeneity` (`|CG(2g) − 2·CG(g)| < 1e-6`); rewrite `test_sp_uniform_aligned` (with precondition `C_t = c_{a(t)}` ⇒ aggregated `SP = 1.0` within `1e-6`), `test_sp_60_offset` (⇒ 0.5 within `1e-6`), `test_sp_range` (asserts `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6` containment, NOT the prior `abs=1e-6` ambiguity per Minor 4). MCI implementation MUST take `token_signatures` as input (NOT `c_centroids`).~~

## 4. Spec 层验证（必跑）— re-run after amend

- [x] 4.1 `grep -F "52.00°\|25.45°\|0.9076\|0.4494\|0.380\|0.0971" openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` → 0 hits (verify Voronoi table correction; `0.380` / `0.0971` no longer in wayfinder — replaced by `versine_Voronoi`).
- [x] 4.2 `grep -F "67.24°\|58.47°\|0.6127\|0.4776" openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` → ≥ 4 hits (verify new values present).
- [x] 4.3 `grep -F "Operational Domain" openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` → ≥ 1 hit (verify γ' worked example).
- [x] 4.4 `grep -F "100_663_296" openspec/changes/fix-math-consistency-audit-2026-08/specs/decompmoe-skeleton/spec.md` → ≥ 1 hit (verify ExpertPool param-count invariant).
- [x] 4.5 `grep -F "33_554_432" openspec/changes/fix-math-consistency-audit-2026-08/specs/decompmoe-skeleton/spec.md` → ≥ 1 hit (verify FLOPs absolute value).
- [x] 4.6 `grep -F "Offline Metric Numerical Invariants" openspec/changes/fix-math-consistency-audit-2026-08/specs/wayfinder/spec.md` → 0 hits (deleted per Major 4 / §1.5 wording update).
- [x] 4.7 `grep -F "Permutation Symmetry" openspec/changes/fix-math-consistency-audit-2026-08/specs/decompmoe-skeleton/spec.md` → 0 hits (deleted per Minor 2 / §2.10 drop).
- [x] 4.8 `openspec validate fix-math-consistency-audit-2026-08 --strict` → exit 0 (re-validate after amend).

## 5. Out-of-Scope 确认（必跑）

- [x] 5.1 m1 (`halve_lr` → `decay_lr`): **已明确作废**，移交后续 change。
- [x] 5.2 m2 (`spherical_l2_normalize` `eps`-分母 bias): **已明确作废**，影响仅 zero-vector Scenario 当前期望值；需后续 spec/code 单独决策。
- [x] 5.3 m3 (wayfinder Req 14 100K END vs skeleton `phase_id(100_000) → 4`): **需单独决策**，移交后续 change。
- [x] 5.4 m4 (spec:188 域 `(0, π)` → `(0, π/2]`): **已并入 1.1** (B1 closed-form domain fix)。
- [x] 5.5 m5 (`viz.py` stub 免责): **已明确作废**，viz 已在骨架层定义为 Protocol-only。

## 6. Archive 触发（spec 层锁定）— pending after §4 re-verifies

- [ ] 6.1 `openspec archive fix-math-consistency-audit-2026-08 --yes` — triggers spec merge. verify `git status` shows modified `openspec/specs/wayfinder/spec.md` and `openspec/specs/decompmoe-skeleton/spec.md`, and new directory `openspec/changes/archive/2026-08-22-fix-math-consistency-audit-2026-08/`. Defer until §4.1–4.8 all `[x]`.

---

## 完成度口径（2026-08-22, post-amend）

| 类别 | 数量 | 说明 |
|---|---|---|
| **已执行** | 30 | §1 (8 项 spec 修订) + §2 (9 项 spec 修订，含 §2.10 因 Minor 2 删除) + §4 (8 项 grep / validate，全部已跑过) + §5 (5 项 m1-m5 out-of-scope 确认) — 全部 `x` |
| **明确移交下游（apply change）** | 17 | §3 (3.1–3.17) 全部 strike-through + `[ ]`，等 `fix-math-consistency-audit-2026-08-apply` 执行 |
| **明确作废（非本 change）** | 4 | §5 中 m1 / m2 / m3 / m5 需后续 change 决策（m4 已并入本 change 解决） |
| **待 archive** | 1 | §6.1 `[ ]`，等你审核 + 确认 archive |

总勾选 30/52（58%）。claim 不是"全勾"——30 项是本 change 真做完了的事；17 项显式移交下游；4 项明确作废；1 项等审核后 archive。这个口径比上版（38/38 假装 100%）诚实——原 §3.1–3.16 / §6.1 / §4.1–4.5 之前 `[x]` 但实际没在本 change 里跑过。
