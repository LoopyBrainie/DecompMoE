## 1. ST-01 — Package Skeleton + Frozen MVP Config + Wire-Level Contracts

- [x] 1.1 Write `tests/test_config.py` with failing pytest cases: `test_mvp_locked_constants`, `test_mvp_is_frozen`, `test_total_param_estimate`, `test_active_flops_parity`, `test_canonical_name`
- [x] 1.2 Write `tests/test_contracts.py` with failing pytest cases: `test_router_contract_signatures`, `test_no_kv_cache_field`
- [x] 1.3 Implement `src/decompmoe/__init__.py` (version, `__all__`, `__canonical_name__`, `__alias__`)
- [x] 1.4 Implement `src/decompmoe/config.py` (`MVPConfig` frozen dataclass + `compute_total_and_active` + `flops_per_token`)
- [x] 1.5 Implement `src/decompmoe/contracts.py` (Protocol stubs for `GeometricRouter`, `TerritoryHolder`, `BlockAdapter`)
- [x] 1.6 Run `pytest tests/test_config.py tests/test_contracts.py -v` → all green before advancing

## 2. ST-02 — β Sigmoid + Bounded γ + Gradient Upper-Bound Checks

- [x] 2.1 ~~Write `tests/test_beta.py` with failing pytest cases: `test_beta_endpoints`, `test_beta_monotone`, `test_logit_range`, `test_grad_C_bound`, `test_grad_gamma_bound`, `test_beta_param_init_default`~~
- [x] 2.2 ~~Implement `src/decompmoe/beta.py` (`inverse_temperature`, `MAX_GRAD_PER_C`, `MAX_GRAD_PER_GAMMA`)~~
- [x] 2.3 ~~Run `pytest tests/test_beta.py -v` → all green before advancing~~

## 3. ST-03 — Spherical Normalization Primitive

- [x] 3.1 ~~Write `tests/test_sphere.py` with failing pytest cases: `test_unit_sphere_invar`, `test_near_zero_numerically_safe`, `test_double_normalize_idempotent`, `test_voronoi_angle_self_consistency`~~
- [x] 3.2 ~~Implement `src/decompmoe/sphere.py` (`spherical_l2_normalize`, `voronoi_angle`)~~
- [x] 3.3 ~~Run `pytest tests/test_sphere.py -v` → all green before advancing~~

## 4. ST-04 — C Extraction Four-Step Pipeline + Differentiability

- [x] 4.1 ~~Write `tests/test_extraction.py` with failing pytest cases: `test_pipeline_shape`, `test_aggregate_across_heads_awareness`, `test_complexity_budget`, `test_full_differentiability`, `test_no_surrogate_in_codebase`~~
- [x] 4.2 ~~Implement `src/decompmoe/extraction.py` (`extract_C` 4-step pure function)~~
- [x] 4.3 ~~Run `pytest tests/test_extraction.py -v` → all green before advancing~~

## 5. ST-05 — Centroid Four-Phase Lifecycle Driver

- [x] 5.1 ~~Write `tests/test_extraction_phase.py` with failing pytest cases: `test_phase_seeding_no_grad`, `test_phase_090_ema`, `test_phase_095_to_099_ema_coefficients`, `test_phase_4_projected_sgd`, `test_phase_transition_swaps_rule`, `test_dead_expert_protection`~~
- [x] 5.2 ~~Add `CentroidDriver` class + `Phase` enum to `src/decompmoe/extraction.py`~~
- [x] 5.3 ~~Run `pytest tests/test_extraction_phase.py -v` → all green before advancing~~

## 6. ST-06 — Isotropic Squared-Chord Distance + Logit Composition

- [x] 6.1 ~~Write `tests/test_distance.py` with failing pytest cases: `test_distance_range`, `test_distance_zero_at_align`, `test_distance_two_at_antipode`, `test_logit_zero_at_aligned`, `test_logit_no_w_i`, `test_logit_grad_safe`~~
- [x] 6.2 ~~Implement `src/decompmoe/distance.py` (`squared_chord`, `logit`)~~
- [x] 6.3 ~~Run `pytest tests/test_distance.py -v` → all green before advancing~~

## 7. ST-07 — Top-K Sparse Mask + Local Softmax Gating

- [x] 7.1 ~~Write `tests/test_gating.py` with failing pytest cases: `test_k_equals_two`, `test_neg_inf_sentinel_used`, `test_partition_of_unity`, `test_zero_grad_for_non_top_k`, `test_forward_formula_strictness`, `test_convex_combination_dtype_safe`~~
- [x] 7.2 ~~Implement `src/decompmoe/gating.py` (`topk_mask_with_neg_inf`, `local_softmax`)~~
- [x] 7.3 ~~Run `pytest tests/test_gating.py -v` → all green before advancing~~

## 8. ST-08 — SwiGLU Expert + No-Shared-Expert Invariant

- [x] 8.1 ~~Write `tests/test_experts.py` with failing pytest cases: `test_swiglu_formula`, `test_expert_param_count`, `test_no_c_injection`, `test_expert_pool_no_shared_branch`, `test_no_custom_kernel`, `test_isomorphic_to_llama_ffn`~~
- [x] 8.2 ~~Implement `src/decompmoe/experts.py` (`SwiGLUExpert`, `ExpertPool`)~~
- [x] 8.3 ~~Run `pytest tests/test_experts.py -v` → all green before advancing~~

## 9. ST-09 — Loss Composition `L_CE + α·L_lb + λ(t)·L_sep`

- [x] 9.1 ~~Write `tests/test_loss.py` with failing pytest cases: `test_load_balance_alpha_fixed`, `test_lb_uses_detached_fractions`, `test_lambda_zero_phase_1_2`, `test_lambda_cosine_ramp_phase_3`, `test_lambda_fixed_phase_4`, `test_sep_formula`, `test_token_vs_expert_C_notation`~~
- [x] 9.2 ~~Implement `src/decompmoe/loss.py` (`L_total`, `LossParts`, `compute_L_sep`)~~
- [x] 9.3 ~~Run `pytest tests/test_loss.py -v` → all green before advancing~~

## 10. ST-10 — Numerical Safeguards (5 Predicates + Helpers)

- [x] 10.1 ~~Write `tests/test_safeguards.py` with failing pytest cases: `test_clip_grad_norm_threshold`, `test_nan_ladder`, `test_resurrection_trigger_window`, `test_resurrection_perturb_distribution`, `test_beta_saturation_warning_at_30_4`, `test_beta_saturation_global_lr_halve_at_28_8`, `test_loss_spike_defense_phase3plus`, `test_step_ordering`~~
- [x] 10.2 ~~Implement `src/decompmoe/safeguards.py` (5 helpers + `STEP_ORDER` constant)~~
- [x] 10.3 ~~Run `pytest tests/test_safeguards.py -v` → all green before advancing~~

## 11. ST-11 — Five-Phase Scheduler + Three-Layer Hybrid Trigger

- [x] 11.1 ~~Write `tests/test_schedule.py` with failing pytest cases: `test_phase_ratios_pure_function`, `test_phase_id_at_boundary`, `test_phase1_freeze_router`, `test_phase2_freeze_experts`, `test_phase3_b_ramp`, `test_phase4_b_dynamic_box`, `test_adam_momentum_reset_on_phase4_entry`, `test_advisory_signals_read_only`~~
- [x] 11.2 ~~Implement `src/decompmoe/schedule.py` (`phase_id`, `phase_step_frozen_names`, `should_reset_adam`, `advisory_signals`)~~
- [x] 11.3 ~~Run `pytest tests/test_schedule.py -v` → all green before advancing~~

## 12. ST-12 — Eight Metrics + Six Viz Module Protocol Stubs

- [x] 12.1 ~~Write `tests/test_metrics.py` with failing pytest cases: `test_sep_formula_matches_loss`, `test_R_H_partition_of_unity_input`, `test_S_load_zero_at_uniform`, `test_four_realtime_four_offline_classification`, `test_active_flops_parity_per_arch`~~
- [x] 12.2 ~~Write `tests/test_viz_protocols.py` with failing pytest cases: `test_viz_modules_complete`, `test_viz_stack_pinned`, `test_PCA_camera_angles_fixed`~~
- [x] 12.3 ~~Implement `src/decompmoe/metrics.py` (8 metric functions + `flops_per_token` + `REALTIME` / `OFFLINE` frozensets)~~
- [x] 12.4 ~~Implement `src/decompmoe/viz.py` (6 Protocol stubs + `IMPLEMENTATION_STACK` frozenset)~~
- [x] 12.5 ~~Run `pytest tests/test_metrics.py tests/test_viz_protocols.py -v` → all green before advancing~~

## 13. Final Verification Gates

- [x] 13.1 `pytest tests/ -v` → all 14 test files green
- [x] 13.2 `openspec validate --strict` → zero errors
- [x] 13.3 Hard-constraint grep: no `StraightThroughEstimator` / `w_i.*logit` / `shared.*expert` matches in `src/decompmoe/`（仅 docstring 注释陈述约束本身，非违规使用）
- [x] 13.4 Hard-constraint grep: no `cpp_extension` / `triton` / custom-CUDA imports in `src/decompmoe/`（仅 `extraction.py:14` 注释陈述约束本身）
- [x] 13.5 Run `openspec archive add-decompoe-skeleton-with-tdd-tests --yes` to close the change — 实际通过 manual recovery at `d3a71c4`（`chore(openspec): archive code-level apply changes`），与 precedent `f45a42c` 同模式

---

## 完成度口径（2026-09-03 @c6294f9，post-archive cleanup）

本文件原表声称 **22** 条 checkbox，实际计数 **46**（§1: 6 + §2-§11: 10×3=30 + §12: 5 + §13: 5）。两类语义：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行（0d87e32 + commit chain）** | 46 | §1 全 6（0d87e32）+ §2-§12 全 38（commit chain）+ §13.1-13.5 全 5（验证 + manual archive） |
| **其中 U2 retroactive verify** | 5 | §13.1-13.5（pytest / validate / grep / archive CLI — 全部事后复跑 PASS） |
| 合计 | 46 | |

## Post-Archive Execution Record（2026-09-03 @c6294f9）

> §1 ST-01（Package Skeleton + Frozen MVP Config + Wire-Level Contracts）由 `0d87e32` 直接执行；§2-§13 ST-02~ST-13 由后续 commit chain 执行（部分与 `2026-09-01-fix-math-consistency-audit-2026-08-apply` 的 task 3.X 重叠）。

| Task | Commit | 证据（grep 可验） |
|---|---|---|
| §1.1-1.6（ST-01） | `0d87e32` | `feat(skeleton): implement DecompMoE MVP skeleton + 85 TDD tests`；建立 `src/decompmoe/{__init__,config,contracts}.py` + `tests/test_{config,contracts}.py` |
| §2.1-2.3（ST-02 β） | `0d87e32` + `1fd7f59` | `0d87e32` 初版 β.py + `test_beta.py`；`1fd7f59` 加 `phase4_inverse_temperature` + `MAX_GRAD_PER_GAMMA_PHASE4 = 15.5` |
| §3.1-3.3（ST-03 sphere） | `0d87e32` + `c919b3d` + `af91717` | `0d87e32` 初版；`c919b3d` 删 `_VORONOI_MVP_TABLE`；`af91717` `canonical_voronoi_angle` via Beta inversion |
| §4.1-4.3（ST-04 extraction） | `0d87e32` + `a56a599` | `0d87e32` 初版 `extract_C`；`a56a599` 加 Issues ⑥⑦⑧（empty-cell + EMA normalize + 3 invariant tests） |
| §5.1-5.3（ST-05 CentroidDriver） | `0d87e32` + `a56a599` | 同上；`a56a599` 加 EMA `F.normalize` 与 near-zero fallback（`CentroidDriver.step` 重写） |
| §6.1-6.3（ST-06 distance） | `0d87e32` | 初版 `squared_chord` + `logit = β·(Cᵀc − 1)`，无 `w_i`（A4-2 硬约束） |
| §7.1-7.3（ST-07 gating） | `0d87e32` | 初版 `topk_mask_with_neg_inf` + `local_softmax` |
| §8.1-8.3（ST-08 experts） | `0d87e32` + `ad60f0f` | `0d87e32` 初版 `SwiGLUExpert`；`ad60f0f` `ExpertPool(nn.Module) + nn.ModuleList`，参数 100_663_296 exact |
| §9.1-9.3（ST-09 loss） | `0d87e32` + `35fdad7` | `0d87e32` 初版；`35fdad7` 重写 `L_lb = N_e·Σ f_i.detach()·P_i` + gradient flow test |
| §10.1-10.3（ST-10 safeguards） | `0d87e32` + `d3689a1` | `0d87e32` 初版 5 safeguards；`d3689a1` `should_resurrect` 参数化 `1/(2·N_e)` |
| §11.1-11.3（ST-11 schedule） | `0d87e32` + `702b0f3` + `1fd7f59` | `0d87e32` 初版；`702b0f3` Phase 2/3 freeze sets；`1fd7f59` `phase_beta_max` time-varying + `gamma_reset_for_phase4` |
| §12.1-12.5（ST-12 metrics + viz） | `0d87e32` + `1002a99` + `6c97a90` | `0d87e32` 初版 8 metrics + 6 viz protocols；`1002a99` `S_load` closed form；`6c97a90` SP/D_chord/MCI/CG 闭式 |
| §13.1（pytest 全量） | U2 retroactive | post-archive `uv run pytest tests/` 全绿（最新基线 ≥ 132 passed at `9987707`） |
| §13.2（openspec validate） | U2 retroactive | post-cleanup `openspec validate --archived` → 9/9 PASS（本次 cleanup 后） |
| §13.3（硬约束 grep：w_i / shared expert） | U2 retroactive | `grep -rE 'StraightThroughEstimator\|shared.*expert\|w_i.*logit\|w_i)\|\\*\s\*w_i\|w_i\s*=' src/decompmoe/` → 仅 `contracts.py` docstring 注释陈述约束（`w_i is reserved for post-aggregation mixing; never in logit`）+ `experts.py` docstring 注释（`NO shared expert slot`）；无违规使用 |
| §13.4（硬约束 grep：triton / custom kernel） | U2 retroactive | `grep -rE '^(import\|from)\s+(triton\|cpp_extension\|torch\.utils\.cpp_extension)' src/decompmoe/` → 0 hits；仅 `extraction.py:14` 注释陈述约束本身 |
| §13.5（archive CLI） | manual recovery at `d3a71c4` | `chore(openspec): archive code-level apply changes for fix-spec-doc-oversights + fix-openspec-doc-bugs`；与 precedent `f45a42c` 同模式（CLI 在 Windows 不可用 → manual `Move-Item`） |
